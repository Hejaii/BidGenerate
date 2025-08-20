#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
招标文件文档提取器
使用通义千问API智能提取招标文件中要求提交的所有文档类型
"""

import json
import os
import sys
from typing import List, Dict, Any
import pdfplumber
from datetime import datetime
import time

from llm_client import LLMClient, DEFAULT_API_KEY

class DocumentExtractor:
    def __init__(self, llm: LLMClient | None = None):
        """初始化文档提取器"""
        self.llm = llm or LLMClient()
        
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        从PDF文件中提取文本内容，按页分割
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            包含页码和文本内容的字典列表
        """
        pages_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"正在处理PDF文件，共 {total_pages} 页...")
                
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if text and text.strip():
                        pages_data.append({
                            "page": page_num + 1,
                            "text": text.strip(),
                            "content_length": len(text)
                        })
                        
                        if (page_num + 1) % 10 == 0:
                            print(f"已处理 {page_num + 1}/{total_pages} 页")
                            
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
            api_response = self.llm.chat_json(messages)
        except Exception as e:
            print(f"第 {page_num} 页API调用失败: {e}")
            return []

        if "documents" in api_response and api_response["documents"]:
            documents = api_response["documents"]
            for doc in documents:
                doc["page"] = page_num
            return documents
        return []
    
    def extract_all_documents(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        从PDF中提取所有要求的文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            所有文档要求的列表
        """
        print("开始提取PDF文本内容...")
        pages_data = self.extract_text_from_pdf(pdf_path)
        
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
            
            # 添加延迟避免API限流
            time.sleep(1)
        
        return all_documents
    
    def deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对文档要求进行去重处理
        
        Args:
            documents: 原始文档列表
            
        Returns:
            去重后的文档列表
        """
        seen = set()
        unique_documents = []
        
        for doc in documents:
            # 使用文档名称和原始文本的组合作为去重依据
            key = (doc["name"].strip().lower(), doc["original_text"].strip()[:100])
            
            if key not in seen:
                seen.add(key)
                unique_documents.append(doc)
        
        return unique_documents
    
    def categorize_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        对文档进行分类
        
        Args:
            documents: 文档列表
            
        Returns:
            按类别分组的文档字典
        """
        categories = {
            "资格文件": [],
            "技术文件": [],
            "商务文件": [],
            "其他": []
        }
        
        for doc in documents:
            category = doc.get("category", "其他")
            
            # 标准化分类名称
            if "资格" in category or "资质" in category:
                category = "资格文件"
            elif "技术" in category:
                category = "技术文件"
            elif "商务" in category or "价格" in category or "报价" in category:
                category = "商务文件"
            else:
                category = "其他"
            
            doc["category"] = category
            categories[category].append(doc)
        
        return categories
    
    def generate_markdown(self, documents: List[Dict[str, Any]], categories: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        生成Markdown格式的文档清单
        
        Args:
            documents: 所有文档列表
            categories: 分类后的文档
            
        Returns:
            Markdown格式的字符串
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_content = f"""# 招标文件要求提交文档清单

> 生成时间：{timestamp}  
> 文档总数：{len(documents)} 项

## 📋 文档总览

本清单包含招标文件中明确要求投标人提交或附带的所有文档、材料、证明等。

---

## 📁 按类别分类

"""
        
        # 按类别输出
        for category, docs in categories.items():
            if docs:
                markdown_content += f"\n### {category} ({len(docs)} 项)\n\n"
                
                for i, doc in enumerate(docs, 1):
                    markdown_content += f"**{i}. {doc['name']}**\n"
                    markdown_content += f"- 页码：第 {doc['page']} 页\n"
                    markdown_content += f"- 原始要求：{doc['original_text']}\n\n"
        
        # 添加完整列表
        markdown_content += "\n---\n\n## 📄 完整文档列表\n\n"
        
        for i, doc in enumerate(documents, 1):
            markdown_content += f"**{i}. {doc['name']}**\n"
            markdown_content += f"- 页码：第 {doc['page']} 页\n"
            markdown_content += f"- 类别：{doc['category']}\n"
            markdown_content += f"- 原始要求：{doc['original_text']}\n\n"
        
        return markdown_content
    
    def save_results(self, documents: List[Dict[str, Any]], markdown_content: str, output_dir: str = "."):
        """
        保存提取结果
        
        Args:
            documents: 文档列表
            markdown_content: Markdown内容
            output_dir: 输出目录
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存Markdown文件
        markdown_file = os.path.join(output_dir, "required_documents.md")
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        # 保存JSON数据
        json_file = os.path.join(output_dir, f"extracted_documents_{timestamp}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "extraction_time": timestamp,
                "total_documents": len(documents),
                "documents": documents
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存：")
        print(f"- Markdown文件：{markdown_file}")
        print(f"- JSON数据：{json_file}")

def main():
    """主函数"""
    print("🔧 招标文件文档提取器")
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
    extractor = DocumentExtractor(llm)
    
    try:
        # 提取所有文档
        print("🚀 开始提取文档要求...")
        documents = extractor.extract_all_documents(pdf_path)
        
        if not documents:
            print("⚠️ 未识别到任何文档要求")
            return
        
        print(f"✅ 文档提取完成，共识别到 {len(documents)} 项要求")
        
        # 去重和分类
        print("🔄 正在进行去重和分类...")
        unique_documents = extractor.deduplicate_documents(documents)
        categories = extractor.categorize_documents(unique_documents)
        
        print(f"📊 去重后剩余 {len(unique_documents)} 项")
        for category, docs in categories.items():
            if docs:
                print(f"  - {category}: {len(docs)} 项")
        
        # 生成Markdown
        print("📝 正在生成Markdown文档...")
        markdown_content = extractor.generate_markdown(unique_documents, categories)
        
        # 保存结果
        extractor.save_results(unique_documents, markdown_content)
        
        print("\n🎉 文档提取任务完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

