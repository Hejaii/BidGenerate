#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本的招标文件文档提取器
只处理前3页来验证修复是否成功
"""

import json
import os
import sys
from typing import List, Dict, Any
import pdfplumber
from datetime import datetime
import time

from llm_client import LLMClient, DEFAULT_API_KEY

class TestDocumentExtractor:
    def __init__(self, llm: LLMClient | None = None):
        """初始化文档提取器"""
        self.llm = llm or LLMClient()
        
    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        从PDF文件中提取文本内容，按页分割（测试版本只处理前几页）
        
        Args:
            pdf_path: PDF文件路径
            max_pages: 最大处理页数（测试用）
            
        Returns:
            包含页码和文本内容的字典列表
        """
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = min(len(pdf.pages), max_pages)
                print(f"正在处理PDF文件，测试版本只处理前 {total_pages} 页...")
                
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if text and text.strip():
                        pages_data.append({
                            "page": page_num + 1,
                            "text": text.strip(),
                            "content_length": len(text)
                        })
                        
                        print(f"已处理第 {page_num + 1} 页")
                            
        except Exception as e:
            print(f"PDF处理错误: {e}")
            return []
            
        return pages_data
    
    def analyze_page_content(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分析单页内容，识别文档要求
        
        Args:
            page_data: 页面数据字典
            
        Returns:
            识别出的文档要求列表
        """
        page_num = page_data["page"]
        text = page_data["text"]
        
        # 构建发送给通义千问的提示词
        prompt = f"""
请仔细分析以下招标文件页面内容，识别出所有要求投标人提交或附带的文档、材料、证明等。

页面内容：
{text}

请按照以下JSON格式返回结果，如果识别到要求提交的文档，请提取：
1. 文档名称（具体要提交什么文件）
2. 原始要求语句（完整的句子）
3. 文档类型分类（资格文件/技术文件/商务文件/其他）

如果页面中没有相关要求，请返回空列表。

返回格式：
{{
    "documents": [
        {{
            "name": "文档名称",
            "original_text": "原始要求语句",
            "category": "文档类型分类"
        }}
    ]
}}

请确保返回的是有效的JSON格式。
"""
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的招标文件分析专家，擅长识别和提取招标文件中要求投标人提交的各种文档和材料。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            print(f"正在调用通义千问API分析第 {page_num} 页...")
            api_response = self.llm.chat_json(messages)
            print(f"第 {page_num} 页API调用成功")
            return api_response.get("documents", [])
        except Exception as e:
            print(f"第 {page_num} 页API调用失败: {e}")
            return []
    
    def test_extraction(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        测试文档提取功能
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文档列表
        """
        print("开始测试PDF文本内容提取...")
        pages_data = self.extract_text_from_pdf(pdf_path, max_pages=3)
        
        if not pages_data:
            print("PDF文本提取失败")
            return []
        
        print(f"文本提取完成，共 {len(pages_data)} 页")
        print("开始使用通义千问API分析每页内容...")
        
        all_documents = []
        
        for i, page_data in enumerate(pages_data):
            print(f"正在分析第 {page_data['page']} 页 ({i+1}/{len(pages_data)})...")
            
            documents = self.analyze_page_content(page_data)
            if documents:
                all_documents.extend(documents)
                print(f"第 {page_data['page']} 页识别到 {len(documents)} 个文档要求")
            else:
                print(f"第 {page_data['page']} 页未识别到文档要求")
            
            # 添加延迟避免API限流
            time.sleep(1)
        
        return all_documents

def main():
    """主函数"""
    print("🔧 测试版招标文件文档提取器")
    print("=" * 50)
    
    # 检查API密钥
    api_key = os.getenv("QIANWEN_API_KEY", DEFAULT_API_KEY)
    llm = LLMClient(api_key=api_key)
    
    # 检查PDF文件
    pdf_path = "03.招标文件.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ 错误：PDF文件不存在：{pdf_path}")
        sys.exit(1)
    
    # 创建提取器
    extractor = TestDocumentExtractor(llm)
    
    try:
        # 测试提取功能
        print("🚀 开始测试文档提取功能...")
        documents = extractor.test_extraction(pdf_path)
        
        if not documents:
            print("⚠️ 未识别到任何文档要求")
        else:
            print(f"✅ 测试完成，共识别到 {len(documents)} 项要求")
            for doc in documents:
                print(f"  - {doc['name']} ({doc['category']})")
        
        print("\n🎉 测试完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

