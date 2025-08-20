#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义千问API客户端
负责与DashScope API的所有交互
"""

import os
import json
import requests
import time
from typing import List, Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashScopeClient:
    """通义千问API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("环境变量DASHSCOPE_API_KEY未设置")
        
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.embedding_model = os.getenv('QW_EMBEDDING_MODEL', 'text-embedding-v1')
        self.llm_model = os.getenv('QW_MODEL_NAME', 'qwen-plus')
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本向量化结果"""
        try:
            url = f"{self.base_url}/embeddings"
            payload = {
                "model": self.embedding_model,
                "input": texts
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item['embedding'] for item in result['data']]
            return embeddings
            
        except Exception as e:
            logger.error(f"获取向量化失败: {e}")
            raise
    
    def rerank_documents(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """重排序文档"""
        try:
            url = f"{self.base_url}/rerank"
            payload = {
                "model": "rerank-v1",
                "query": query,
                "documents": documents,
                "top_k": top_k
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['results']
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 如果重排序失败，返回简单的相似度排序
            return self._fallback_rerank(query, documents, top_k)
    
    def _fallback_rerank(self, query: str, documents: List[str], top_k: int) -> List[Dict[str, Any]]:
        """简单的回退重排序"""
        results = []
        for i, doc in enumerate(documents):
            # 简单的关键词匹配评分
            score = 0
            query_words = set(query.lower().split())
            doc_words = set(doc.lower().split())
            if query_words & doc_words:
                score = len(query_words & doc_words) / len(query_words)
            
            results.append({
                "index": i,
                "document": doc,
                "relevance_score": score
            })
        
        # 按评分排序
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:top_k]
    
    def generate_clause_response(self, 
                               clause_text: str,
                               constraints: List[str],
                               score_items: List[str],
                               forbidden: List[str],
                               evidence_summaries: List[str],
                               template_fragments: List[str],
                               placeholders: Dict[str, str]) -> Dict[str, Any]:
        """生成条款响应段落"""
        try:
            url = f"{self.base_url}/chat/completions"
            
            # 构建提示词
            prompt = self._build_clause_prompt(
                clause_text, constraints, score_items, forbidden, 
                evidence_summaries, template_fragments, placeholders
            )
            
            payload = {
                "model": self.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是专业的标书撰写专家，负责根据招标要求和公司资质生成符合要求的投标响应。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 解析返回内容
            return self._parse_clause_response(content)
            
        except Exception as e:
            logger.error(f"生成条款响应失败: {e}")
            return self._generate_fallback_response(clause_text, constraints)
    
    def _build_clause_prompt(self, 
                            clause_text: str,
                            constraints: List[str],
                            score_items: List[str],
                            forbidden: List[str],
                            evidence_summaries: List[str],
                            template_fragments: List[str],
                            placeholders: Dict[str, str]) -> str:
        """构建条款生成提示词"""
        
        prompt = f"""
请根据以下信息生成标书条款响应：

招标条款：{clause_text}

硬性约束：
{chr(10).join([f"- {c}" for c in constraints])}

评分项目：
{chr(10).join([f"- {s}" for s in score_items])}

禁止内容：
{chr(10).join([f"- {f}" for f in forbidden])}

可用证据摘要：
{chr(10).join([f"- {e}" for e in evidence_summaries])}

模板片段：
{chr(10).join([f"- {t}" for t in template_fragments])}

占位符映射：
{chr(10).join([f"- {k}: {v}" for k, v in placeholders.items()])}

要求：
1. 生成300-500字的专业响应段落
2. 每个关键主张必须包含证据锚点〔证据#ID〕
3. 严格避免使用禁止词汇
4. 覆盖所有约束条件和评分项目
5. 使用提供的模板片段和占位符
6. 输出格式：JSON，包含draft（正文）、evidence_map（证据映射）、risk_flags（风险标识）

请以JSON格式返回结果。
"""
        return prompt
    
    def _parse_clause_response(self, content: str) -> Dict[str, Any]:
        """解析条款响应内容"""
        try:
            # 尝试提取JSON部分
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            elif '{' in content and '}' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
            else:
                raise ValueError("未找到有效的JSON内容")
            
            result = json.loads(json_str)
            return result
            
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return self._generate_fallback_response("", [])
    
    def _generate_fallback_response(self, clause_text: str, constraints: List[str]) -> Dict[str, Any]:
        """生成回退响应"""
        return {
            "draft": f"关于{clause_text}的响应内容需要人工确认。",
            "evidence_map": {},
            "risk_flags": ["需要人工确认具体内容"],
            "deviation": "无法自动生成，需要人工处理",
            "status": "manual_review_required"
        }
    
    def extract_key_points(self, 
                          clause_text: str,
                          constraints: List[str],
                          score_items: List[str],
                          evidence_summaries: List[str]) -> List[str]:
        """提取条款要点"""
        try:
            url = f"{self.base_url}/chat/completions"
            
            prompt = f"""
请分析以下招标条款，提取关键要点：

条款：{clause_text}
约束：{chr(10).join(constraints)}
评分项：{chr(10).join(score_items)}
证据：{chr(10).join(evidence_summaries)}

请提取5-8个关键要点，每个要点应该是：
1. 可核查的
2. 可量化的
3. 有明确证据支撑的

以JSON数组格式返回要点列表。
"""
            
            payload = {
                "model": self.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是招标文件分析专家，负责提取关键要点。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 解析要点
            try:
                if '[' in content and ']' in content:
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    json_str = content[json_start:json_end]
                    points = json.loads(json_str)
                    return points if isinstance(points, list) else []
                else:
                    return []
            except:
                return []
                
        except Exception as e:
            logger.error(f"提取要点失败: {e}")
            return []
