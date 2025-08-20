#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能评分程序配置文件
"""

# 通义千问API配置（改为从环境变量读取，禁止硬编码）
import os
QIANWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QIANWEN_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 多个模型配置，按优先级排序
QIANWEN_MODELS = [
    "qwen-plus-2025-07-14",      # 最新版本，优先使用
    "qwen-plus-2025-04-28",      # 备选模型1
    "qwen-plus-2025-01-25",      # 备选模型2
    "qwen-plus-0112",            # 备选模型3
    "qwen-plus-1220",            # 备选模型4
    "qwen-plus-1127",            # 备选模型5
    "qwen-plus-1125",            # 备选模型6
    "qwen-plus-0919",            # 备选模型7
    "qwen-plus-0806",            # 备选模型8
    "qwen-plus-0723"             # 备选模型9
]

# 项目路径配置
PROJECT_ROOT = "/Users/leojiang/PycharmProjects/标书生成"
LIBRARY_ROOT = "/Users/leojiang/PycharmProjects/标书生成/litchi-smart-orchard-bid"

# 文件类型配置
SUPPORTED_FILE_EXTENSIONS = ['.txt', '.json']
REQUIREMENT_FILE_PREFIXES = [
    "03.招标文件_qualification_requirements_report",
    "03.招标文件_qualification_requirements_data"
]

# 评分配置
SCORING_DELAY_SECONDS = 3  # API请求间隔
API_TIMEOUT_SECONDS = 200   # API超时时间

# 关键词匹配配置
KEYWORD_MATCHING_RULES = {
    'iso9001': ['iso9001', 'iso 9001', '质量管理体系', '质量体系'],
    'iso14001': ['iso14001', 'iso 14001', '环境管理体系', '环境体系'],
    'iso45001': ['iso45001', 'iso 45001', '职业健康安全', 'ohsas'],
    'cma': ['cma', '计量认证', '计量资质'],
    'cnas': ['cnas', '实验室认可', '实验室资质'],
    '软件企业': ['软件企业', '软件企业认定', '软件认定'],
    '信息安全': ['信息安全', '安全开发', 'nsatp', '安全资质'],
    'iot': ['iot', '物联网', '智能硬件', '智能设备'],
    '科技奖': ['科技奖', '科技进步', '技术创新', '技术奖'],
    '项目经理': ['项目经理', 'pmp', '项目管理', '项目负责人'],
    '测试工程师': ['测试工程师', '软件测试', '测试', '测试人员'],
    '数据库': ['数据库', 'db', '数据库管理', '数据库工程师'],
    '大数据': ['大数据', '数据分析', 'bigdata', '数据工程师'],
    'it服务': ['it服务', '服务管理', 'it管理'],
    '智能集成': ['智能集成', '系统集成', '集成', '集成商'],
    '评估师': ['评估师', '评估', 'assessor', '评估人员'],
    '项目业绩': ['项目业绩', '类似项目', '业绩证明', '项目经验'],
    '技术方案': ['技术方案', '技术实现', '功能', '技术架构'],
    '测试方案': ['测试方案', '测试方法', '自动化测试', '测试策略'],
    '质量保证': ['质量保证', '质量控制', '质量', '质量管理'],
    '安全管理': ['安全管理', '安全文明', '安全', '安全体系'],
    '风险评估': ['风险评估', '风险管理', '风险', '风险控制'],
    '验收标准': ['验收标准', '验收', '标准', '验收规范'],
    '组织架构': ['组织架构', '团队', '人员配置', '组织'],
    '进度计划': ['进度计划', '工期', '时间安排', '计划'],
    '成本控制': ['成本控制', '预算', '成本', '费用控制']
}

# 文件类型映射
FILE_TYPE_MAPPING = {
    'company_qualification': '公司资质',
    'personnel_qualification': '人员资质', 
    'performance': '项目业绩',
    'technical_proposal': '技术方案',
    'test_plan': '测试方案',
    'management_plan': '管理方案',
    'other': '其他文件'
}

# 评分提示词模板
SCORING_PROMPT_TEMPLATE = """你是专业的投标文件评分专家。请根据招标要求对投标方提供的材料进行评分。

# 招标要求
- 要求类型: {requirement_type}
- 要求内容: {requirement_text}
- 要求概括: {requirement_summary}
- 满分: {max_score}分
- 重要性: {importance}

# 投标方材料
{library_content}

# 评分任务
请根据招标要求对投标方材料进行评分，要求：
1. 严格按照招标要求进行评分，不得主观臆断
2. 评分必须基于材料内容与要求的匹配程度
3. 如果材料完全满足要求，给满分
4. 如果材料部分满足要求，按满足程度给分
5. 如果材料不满足要求，给0分
6. 如果材料超出要求，最多给满分

# 输出格式
请严格按照以下JSON格式输出，不要包含其他文字：

{{
  "score": 实际得分（数字）,
  "max_score": 满分（数字）,
  "score_rate": 得分率（百分比，如85.5）,
  "evaluation": "详细评分说明，说明为什么给这个分数",
  "strengths": ["材料优势1", "材料优势2"],
  "weaknesses": ["材料不足1", "材料不足2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}

注意：只输出JSON，不要有任何其他文字。"""

# 报告配置
REPORT_TEMPLATE = {
    'title': '智能评分报告',
    'separator': '=' * 80,
    'sub_separator': '-' * 60,
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# Excel配置
EXCEL_SHEET_NAMES = {
    'scoring_results': '评分结果',
    'statistics': '统计信息'
}

EXCEL_COLUMNS = {
    'requirement_id': '要求编号',
    'requirement_summary': '要求概括',
    'requirement_type': '要求类型',
    'page_number': '页码',
    'importance': '重要性',
    'score': '得分',
    'max_score': '满分',
    'score_rate': '得分率(%)',
    'evaluation': '评分说明',
    'strengths': '优势',
    'weaknesses': '不足',
    'suggestions': '建议',
    'relevant_files': '相关文件'
}



