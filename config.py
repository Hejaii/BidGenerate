#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

# 通义千问API配置
QIANWEN_CONFIG = {
    "api_base_url": "https://dashscope.aliyuncs.com/api/v1",
    "model": "qwen-plus-2025-07-14",
    "temperature": 0.1,
    "max_tokens": 2000,
    "timeout": 30
}

# PDF处理配置
PDF_CONFIG = {
    "input_file": "03.招标文件.pdf",
    "output_dir": ".",
    "batch_size": 10,  # 每批处理的页数
    "delay_between_pages": 1,  # 页面间延迟（秒）
}

# 文档分类配置
DOCUMENT_CATEGORIES = {
    "资格文件": ["资格", "资质", "证书", "认证", "许可", "执照"],
    "技术文件": ["技术", "方案", "设计", "图纸", "规范", "标准"],
    "商务文件": ["商务", "价格", "报价", "合同", "协议", "财务"],
    "其他": []
}

# 输出文件配置
OUTPUT_CONFIG = {
    "markdown_file": "required_documents.md",
    "json_file_prefix": "extracted_documents_",
    "encoding": "utf-8"
}

