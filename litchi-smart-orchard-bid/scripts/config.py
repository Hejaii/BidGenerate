#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标文要求评分程序配置文件
"""

# API配置
API_KEY = "sk-fe0485c281964259b404907d483d3777"
API_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
API_MODEL = "qwen-plus-2025-07-14"

# 路径配置
PROJECT_ROOT = "/Users/leojiang/PycharmProjects/标书生成/litchi-smart-orchard-bid"
REQUIREMENTS_FILE = "/Users/leojiang/PycharmProjects/标书生成/03.招标文件_qualification_requirements_report_pages_76-90.txt"
OUTPUT_DIR = "/Users/leojiang/PycharmProjects/标书生成/scoring_results"

# 评分配置
SCORING_DELAY = 3  # API请求间隔（秒）
MAX_RELEVANT_FILES = 5  # 每个要求最多匹配的文件数
RELEVANCE_THRESHOLD = 0.3  # 文件相关性阈值

# 评分标准
SCORING_STANDARDS = {
    "优秀": (90, 100),
    "良好": (80, 89),
    "一般": (70, 79),
    "较差": (60, 69),
    "不满足": (0, 59)
}

# 关键词配置
TECH_KEYWORDS = [
    "技术", "系统", "软件", "硬件", "设备", "功能", "性能", 
    "架构", "集成", "测试", "开发", "部署", "维护", "升级",
    "接口", "协议", "数据", "算法", "模型", "平台", "服务"
]

BUSINESS_KEYWORDS = [
    "资质", "证书", "业绩", "经验", "团队", "管理", "质量", 
    "安全", "成本", "进度", "风险", "合同", "交付", "验收",
    "培训", "服务", "支持", "维护", "保修", "责任", "保险"
]

# 文件类型配置
SUPPORTED_FILE_TYPES = [".md", ".txt", ".doc", ".docx", ".pdf"]
TEXT_FILE_TYPES = [".md", ".txt"]
BINARY_FILE_TYPES = [".pdf", ".doc", ".docx"]

# 输出配置
OUTPUT_FORMATS = ["json", "txt", "csv", "excel"]
DEFAULT_OUTPUT_FORMAT = "json"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = "scoring.log"

# 错误处理配置
MAX_RETRIES = 3
RETRY_DELAY = 5
TIMEOUT = 200

# 性能配置
BATCH_SIZE = 5  # 批量处理大小
MAX_CONCURRENT_REQUESTS = 1  # 最大并发请求数
