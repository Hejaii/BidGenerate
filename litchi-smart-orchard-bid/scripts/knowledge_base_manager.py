#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管理模块
负责文档切块、向量化和检索
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class DocumentChunk:
    """文档块"""
    
    def __init__(self, content: str, source_file: str, chunk_id: str, 
                 page_info: str = "", metadata: Dict[str, Any] = None):
        self.content = content
        self.source_file = source_file
        self.chunk_id = chunk_id
        self.page_info = page_info
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source_file": self.source_file,
            "chunk_id": self.chunk_id,
            "page_info": self.page_info,
            "metadata": self.metadata
        }

class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, kb_root: str = "litchi-smart-orchard-bid"):
        self.kb_root = Path(kb_root)
        self.chunks: List[DocumentChunk] = []
        self.chunk_embeddings: Dict[str, List[float]] = {}
        self.chunk_index: Dict[str, DocumentChunk] = {}
        
        # 文档类型映射
        self.doc_type_patterns = {
            "qualification": ["资格", "资质", "证书", "认证", "许可", "执照", "CMA", "CNAS", "ISO"],
            "performance": ["业绩", "项目", "案例", "经验", "成果"],
            "personnel": ["人员", "团队", "简历", "证书", "资格"],
            "technical": ["技术", "方案", "设计", "图纸", "规范", "标准"],
            "business": ["商务", "价格", "报价", "合同", "协议", "财务"],
            "management": ["管理", "组织", "计划", "风险", "质量", "安全"]
        }
    
    def load_knowledge_base(self) -> None:
        """加载知识库"""
        logger.info("开始加载知识库...")
        
        # 遍历知识库目录
        for file_path in self.kb_root.rglob("*.md"):
            if file_path.is_file():
                self._process_markdown_file(file_path)
        
        for file_path in self.kb_root.rglob("*.txt"):
            if file_path.is_file():
                self._process_text_file(file_path)
        
        logger.info(f"知识库加载完成，共加载 {len(self.chunks)} 个文档块")
    
    def _process_markdown_file(self, file_path: Path) -> None:
        """处理Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按标题分割文档
            chunks = self._split_by_headers(content)
            
            for i, chunk_content in enumerate(chunks):
                if len(chunk_content.strip()) < 50:  # 过滤过短的内容
                    continue
                
                chunk_id = f"{file_path.stem}_{i:03d}"
                chunk = DocumentChunk(
                    content=chunk_content.strip(),
                    source_file=str(file_path.relative_to(self.kb_root)),
                    chunk_id=chunk_id,
                    metadata={
                        "file_type": "markdown",
                        "doc_type": self._classify_document(chunk_content),
                        "word_count": len(chunk_content.split())
                    }
                )
                
                self.chunks.append(chunk)
                self.chunk_index[chunk_id] = chunk
                
        except Exception as e:
            logger.error(f"处理Markdown文件失败 {file_path}: {e}")
    
    def _process_text_file(self, file_path: Path) -> None:
        """处理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按段落分割
            paragraphs = content.split('\n\n')
            
            for i, para in enumerate(paragraphs):
                if len(para.strip()) < 50:
                    continue
                
                chunk_id = f"{file_path.stem}_{i:03d}"
                chunk = DocumentChunk(
                    content=para.strip(),
                    source_file=str(file_path.relative_to(self.kb_root)),
                    chunk_id=chunk_id,
                    metadata={
                        "file_type": "text",
                        "doc_type": self._classify_document(para),
                        "word_count": len(para.split())
                    }
                )
                
                self.chunks.append(chunk)
                self.chunk_index[chunk_id] = chunk
                
        except Exception as e:
            logger.error(f"处理文本文件失败 {file_path}: {e}")
    
    def _split_by_headers(self, content: str) -> List[str]:
        """按标题分割Markdown文档"""
        # 分割标题行
        header_pattern = r'^#{1,6}\s+.+$'
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            if re.match(header_pattern, line):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _classify_document(self, content: str) -> str:
        """分类文档类型"""
        content_lower = content.lower()
        
        for doc_type, patterns in self.doc_type_patterns.items():
            for pattern in patterns:
                if pattern.lower() in content_lower:
                    return doc_type
        
        return "other"
    
    def search_relevant_chunks(self, query: str, top_k: int = 10) -> List[DocumentChunk]:
        """搜索相关文档块"""
        # 简单的关键词匹配搜索
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for chunk in self.chunks:
            chunk_words = set(chunk.content.lower().split())
            if query_words & chunk_words:
                score = len(query_words & chunk_words) / len(query_words)
                scored_chunks.append((score, chunk))
        
        # 按评分排序
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        return [chunk for score, chunk in scored_chunks[:top_k]]
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """根据ID获取文档块"""
        return self.chunk_index.get(chunk_id)
    
    def get_chunks_by_type(self, doc_type: str) -> List[DocumentChunk]:
        """根据类型获取文档块"""
        return [chunk for chunk in self.chunks if chunk.metadata.get('doc_type') == doc_type]
    
    def get_evidence_summaries(self, chunk_ids: List[str]) -> List[str]:
        """获取证据摘要"""
        summaries = []
        for chunk_id in chunk_ids:
            chunk = self.get_chunk_by_id(chunk_id)
            if chunk:
                # 生成摘要（取前100个字符）
                summary = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                summaries.append(f"[{chunk_id}] {summary}")
        
        return summaries
    
    def get_template_fragments(self, doc_type: str, keywords: List[str] = None) -> List[str]:
        """获取模板片段"""
        relevant_chunks = self.get_chunks_by_type(doc_type)
        
        if keywords:
            # 按关键词过滤
            filtered_chunks = []
            for chunk in relevant_chunks:
                content_lower = chunk.content.lower()
                if any(keyword.lower() in content_lower for keyword in keywords):
                    filtered_chunks.append(chunk)
            relevant_chunks = filtered_chunks
        
        # 返回内容片段
        return [chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content 
                for chunk in relevant_chunks[:5]]
    
    def export_chunks_info(self) -> Dict[str, Any]:
        """导出文档块信息"""
        return {
            "total_chunks": len(self.chunks),
            "chunks_by_type": {
                doc_type: len(self.get_chunks_by_type(doc_type))
                for doc_type in set(chunk.metadata.get('doc_type') for chunk in self.chunks)
            },
            "sample_chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "source_file": chunk.source_file,
                    "doc_type": chunk.metadata.get('doc_type'),
                    "word_count": chunk.metadata.get('word_count'),
                    "preview": chunk.content[:100] + "..."
                }
                for chunk in self.chunks[:10]
            ]
        }
