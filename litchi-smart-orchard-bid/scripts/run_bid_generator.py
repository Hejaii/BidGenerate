#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标书生成主运行脚本
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from bid_generator import BidGenerator

def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bid_generation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_sample_requirements() -> list:
    """加载示例招标要求"""
    sample_requirements = [
        {
            "clause_id": "qualification_001",
            "text": "投标人应具备独立承担民事责任的能力，具有良好的商业信誉和健全的财务会计制度",
            "constraints": ["独立承担民事责任", "良好商业信誉", "健全财务会计制度"],
            "score_items": ["注册资本", "财务状况", "信用记录"],
            "forbidden": ["虚假信息", "夸大宣传"],
            "priority": "high"
        },
        {
            "clause_id": "technical_001", 
            "text": "投标人应具备智慧农业相关项目实施经验，并提供近3年类似项目业绩证明",
            "constraints": ["智慧农业经验", "近3年业绩", "项目证明"],
            "score_items": ["项目数量", "项目规模", "技术先进性"],
            "forbidden": ["虚构业绩", "过期证明"],
            "priority": "high"
        },
        {
            "clause_id": "personnel_001",
            "text": "项目团队应配备项目经理、技术负责人等关键岗位人员，具备相应资质证书",
            "constraints": ["项目经理", "技术负责人", "资质证书"],
            "score_items": ["人员资质", "项目经验", "团队配置"],
            "forbidden": ["无证上岗", "虚假资质"],
            "priority": "medium"
        }
    ]
    return sample_requirements

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="标书生成系统")
    parser.add_argument("--requirements", "-r", help="招标要求JSON文件路径")
    parser.add_argument("--output", "-o", default="bid_responses.json", help="输出文件路径")
    parser.add_argument("--industry", "-i", default="智慧农业", help="行业领域")
    parser.add_argument("--project", "-p", default="荔枝智慧果园项目", help="项目名称")
    parser.add_argument("--log-level", "-l", default="INFO", help="日志级别")
    parser.add_argument("--sample", "-s", action="store_true", help="使用示例招标要求")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # 检查环境变量
        if not os.getenv('DASHSCOPE_API_KEY'):
            logger.error("环境变量DASHSCOPE_API_KEY未设置")
            logger.info("请设置通义千问API密钥：export DASHSCOPE_API_KEY='你的dashscope密钥'")
            return 1
        
        # 初始化标书生成器
        logger.info("初始化标书生成器...")
        generator = BidGenerator()
        
        # 加载招标要求
        if args.sample:
            logger.info("使用示例招标要求")
            requirements = load_sample_requirements()
            # 保存示例要求到临时文件
            temp_file = "temp_requirements.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(requirements, f, ensure_ascii=False, indent=2)
            generator.requirements = requirements
        elif args.requirements:
            logger.info(f"从文件加载招标要求: {args.requirements}")
            generator.load_requirements(args.requirements)
        else:
            logger.error("请指定招标要求文件或使用--sample参数")
            return 1
        
        # 设置占位符
        placeholders = {
            "项目名称": args.project,
            "行业领域": args.industry,
            "响应时限小时": "24",
            "质保期": "2年",
            "服务地点": "项目现场",
            "公司名称": "智能科技有限公司",
            "成立时间": "2018年",
            "注册资本": "1000万元"
        }
        
        # 生成标书响应
        logger.info("开始生成标书响应...")
        results = generator.generate_bid_responses(
            industry=args.industry,
            project_name=args.project,
            placeholders=placeholders
        )
        
        # 保存结果
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"标书响应已保存到: {args.output}")
        
        # 显示摘要
        summary = results.get('summary', {})
        logger.info("生成摘要:")
        logger.info(f"  总条款数: {summary.get('total_clauses', 0)}")
        logger.info(f"  成功生成: {summary.get('success_count', 0)}")
        logger.info(f"  需人工确认: {summary.get('manual_review_count', 0)}")
        logger.info(f"  生成失败: {summary.get('error_count', 0)}")
        
        # 显示风险标识
        risk_flags = results.get('risk_flags', [])
        if risk_flags:
            logger.warning("发现以下风险标识:")
            for risk in risk_flags:
                logger.warning(f"  - {risk}")
        
        # 清理临时文件
        if args.sample and os.path.exists("temp_requirements.json"):
            os.remove("temp_requirements.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"标书生成失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
