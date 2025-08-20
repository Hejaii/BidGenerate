#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标书生成引擎
整合通义千问API调用和知识库管理，实现完整的标书生成流程
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from dashscope_client import DashScopeClient
from knowledge_base_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

class BidGenerator:
    """标书生成引擎"""
    
    def __init__(self, kb_root: str = "litchi-smart-orchard-bid"):
        self.dashscope_client = DashScopeClient()
        self.kb_manager = KnowledgeBaseManager(kb_root)
        self.requirements: List[Dict[str, Any]] = []
        self.generated_responses: Dict[str, Dict[str, Any]] = {}
        
        # 加载知识库
        self.kb_manager.load_knowledge_base()
        logger.info("标书生成引擎初始化完成")
    
    def load_requirements(self, requirements_file: str) -> None:
        """加载招标要求"""
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                self.requirements = json.load(f)
            logger.info(f"加载了 {len(self.requirements)} 个招标条款")
        except Exception as e:
            logger.error(f"加载招标要求失败: {e}")
            raise
    
    def generate_bid_responses(self, 
                             industry: str = "智慧农业",
                             project_name: str = "荔枝智慧果园项目",
                             placeholders: Dict[str, str] = None) -> Dict[str, Any]:
        """生成标书响应"""
        if not self.requirements:
            raise ValueError("请先加载招标要求")
        
        placeholders = placeholders or {}
        # 添加默认占位符
        default_placeholders = {
            "项目名称": project_name,
            "行业领域": industry,
            "响应时限小时": "24",
            "质保期": "2年",
            "服务地点": "项目现场"
        }
        placeholders.update(default_placeholders)
        
        logger.info(f"开始生成标书响应，项目：{project_name}")
        
        all_responses = []
        evidence_map = {}
        risk_flags = []
        
        for i, requirement in enumerate(self.requirements):
            logger.info(f"处理条款 {i+1}/{len(self.requirements)}: {requirement.get('clause_id', f'clause_{i}')}")
            
            try:
                response = self._generate_single_clause_response(requirement, placeholders)
                all_responses.append(response)
                
                # 收集证据映射
                if 'evidence_map' in response:
                    evidence_map.update(response['evidence_map'])
                
                # 收集风险标识
                if 'risk_flags' in response:
                    risk_flags.extend(response['risk_flags'])
                
                # 避免API调用过于频繁
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"生成条款响应失败: {e}")
                # 生成错误响应
                error_response = self._generate_error_response(requirement, str(e))
                all_responses.append(error_response)
        
        # 生成最终结果
        result = {
            "project_info": {
                "name": project_name,
                "industry": industry,
                "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_clauses": len(self.requirements)
            },
            "responses": all_responses,
            "evidence_map": evidence_map,
            "risk_flags": list(set(risk_flags)),  # 去重
            "summary": {
                "success_count": len([r for r in all_responses if r.get('status') == 'success']),
                "manual_review_count": len([r for r in all_responses if r.get('status') == 'manual_review_required']),
                "error_count": len([r for r in all_responses if r.get('status') == 'error'])
            }
        }
        
        logger.info("标书响应生成完成")
        return result
    
    def _generate_single_clause_response(self, 
                                       requirement: Dict[str, Any], 
                                       placeholders: Dict[str, str]) -> Dict[str, Any]:
        """生成单个条款响应"""
        clause_id = requirement.get('clause_id', 'unknown')
        clause_text = requirement.get('text', '')
        constraints = requirement.get('constraints', [])
        score_items = requirement.get('score_items', [])
        forbidden = requirement.get('forbidden', [])
        priority = requirement.get('priority', 'normal')
        
        try:
            # 步骤1：候选素材检索
            relevant_chunks = self._retrieve_relevant_materials(clause_text, constraints)
            
            # 步骤2：提取要点
            key_points = self._extract_key_points(clause_text, constraints, score_items, relevant_chunks)
            
            # 步骤3：获取模板片段
            template_fragments = self._get_template_fragments(requirement, relevant_chunks)
            
            # 步骤4：生成响应段落
            response = self.dashscope_client.generate_clause_response(
                clause_text=clause_text,
                constraints=constraints,
                score_items=score_items,
                forbidden=forbidden,
                evidence_summaries=[chunk.content[:200] for chunk in relevant_chunks[:5]],
                template_fragments=template_fragments,
                placeholders=placeholders
            )
            
            # 步骤5：处理占位符替换
            if 'draft' in response:
                response['draft'] = self._replace_placeholders(response['draft'], placeholders)
            
            # 步骤6：添加元数据
            response.update({
                "clause_id": clause_id,
                "priority": priority,
                "status": "success",
                "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "relevant_chunks_count": len(relevant_chunks),
                "key_points": key_points
            })
            
            return response
            
        except Exception as e:
            logger.error(f"生成条款 {clause_id} 响应失败: {e}")
            return self._generate_error_response(requirement, str(e))
    
    def _retrieve_relevant_materials(self, 
                                   clause_text: str, 
                                   constraints: List[str]) -> List[Any]:
        """检索相关材料"""
        # 构建查询
        query = clause_text + " " + " ".join(constraints)
        
        # 使用知识库管理器搜索
        relevant_chunks = self.kb_manager.search_relevant_chunks(query, top_k=10)
        
        # 如果有向量化结果，使用通义千问进行重排序
        if relevant_chunks and len(relevant_chunks) > 5:
            try:
                chunk_texts = [chunk.content for chunk in relevant_chunks]
                reranked_results = self.dashscope_client.rerank_documents(
                    query, chunk_texts, top_k=5
                )
                
                # 根据重排序结果重新组织chunks
                reranked_chunks = []
                for result in reranked_results:
                    index = result.get('index', 0)
                    if index < len(relevant_chunks):
                        reranked_chunks.append(relevant_chunks[index])
                
                if reranked_chunks:
                    relevant_chunks = reranked_chunks
                    
            except Exception as e:
                logger.warning(f"重排序失败，使用原始搜索结果: {e}")
        
        return relevant_chunks
    
    def _extract_key_points(self, 
                           clause_text: str,
                           constraints: List[str],
                           score_items: List[str],
                           relevant_chunks: List[Any]) -> List[str]:
        """提取关键要点"""
        try:
            evidence_summaries = [chunk.content[:200] for chunk in relevant_chunks[:3]]
            
            key_points = self.dashscope_client.extract_key_points(
                clause_text, constraints, score_items, evidence_summaries
            )
            
            return key_points if key_points else []
            
        except Exception as e:
            logger.warning(f"提取要点失败: {e}")
            return []
    
    def _get_template_fragments(self, 
                               requirement: Dict[str, Any], 
                               relevant_chunks: List[Any]) -> List[str]:
        """获取模板片段"""
        # 根据条款类型和关键词获取模板
        doc_type = self._determine_doc_type(requirement)
        keywords = self._extract_keywords(requirement)
        
        template_fragments = self.kb_manager.get_template_fragments(doc_type, keywords)
        
        # 如果没有找到相关模板，返回通用模板
        if not template_fragments:
            template_fragments = [
                "我公司具备相关资质和经验，能够满足招标要求。",
                "我们将严格按照招标文件要求执行，确保项目质量。",
                "我公司拥有专业的技术团队和丰富的项目经验。"
            ]
        
        return template_fragments
    
    def _determine_doc_type(self, requirement: Dict[str, Any]) -> str:
        """确定文档类型"""
        clause_text = requirement.get('text', '').lower()
        
        if any(word in clause_text for word in ['资格', '资质', '证书', '认证']):
            return "qualification"
        elif any(word in clause_text for word in ['业绩', '项目', '案例', '经验']):
            return "performance"
        elif any(word in clause_text for word in ['人员', '团队', '简历']):
            return "personnel"
        elif any(word in clause_text for word in ['技术', '方案', '设计']):
            return "technical"
        elif any(word in clause_text for word in ['商务', '价格', '报价']):
            return "business"
        elif any(word in clause_text for word in ['管理', '组织', '计划']):
            return "management"
        else:
            return "technical"  # 默认为技术类型
    
    def _extract_keywords(self, requirement: Dict[str, Any]) -> List[str]:
        """提取关键词"""
        keywords = []
        clause_text = requirement.get('text', '')
        
        # 简单的关键词提取
        important_words = ['技术', '方案', '设计', '实施', '管理', '服务', '质量', '安全']
        for word in important_words:
            if word in clause_text:
                keywords.append(word)
        
        return keywords
    
    def _replace_placeholders(self, text: str, placeholders: Dict[str, str]) -> str:
        """替换占位符"""
        for key, value in placeholders.items():
            placeholder = f"{{{{{key}}}}}"
            text = text.replace(placeholder, value)
        
        return text
    
    def _generate_error_response(self, requirement: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """生成错误响应"""
        return {
            "clause_id": requirement.get('clause_id', 'unknown'),
            "status": "error",
            "error_message": error_msg,
            "draft": f"关于{requirement.get('text', '该条款')}的响应内容生成失败，需要人工处理。",
            "evidence_map": {},
            "risk_flags": ["内容生成失败，需要人工确认"],
            "deviation": "无法自动生成，需要人工处理",
            "generation_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def export_results(self, output_file: str) -> None:
        """导出结果到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.generated_responses, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已导出到: {output_file}")
        except Exception as e:
            logger.error(f"导出结果失败: {e}")
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """获取生成摘要"""
        if not self.generated_responses:
            return {"message": "尚未生成任何响应"}
        
        total = len(self.generated_responses)
        success = len([r for r in self.generated_responses.values() if r.get('status') == 'success'])
        manual_review = len([r for r in self.generated_responses.values() if r.get('status') == 'manual_review_required'])
        errors = len([r for r in self.generated_responses.values() if r.get('status') == 'error'])
        
        return {
            "total_clauses": total,
            "success_count": success,
            "manual_review_count": manual_review,
            "error_count": errors,
            "success_rate": f"{(success/total)*100:.1f}%" if total > 0 else "0%"
        }
