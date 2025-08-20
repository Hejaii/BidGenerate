#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版标文要求评分程序
根据PDF提取器总结的标文要求，在库中找到对应文件，使用通义千问API进行评分
"""

import os
import sys
import json
import time
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except ImportError:
    print("错误: 找不到配置文件 config.py")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("正在安装requests...")
    os.system("pip install requests")
    import requests


class EnhancedQianwenScorer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.API_KEY
        self.base_url = config.API_BASE_URL
        self.model = config.API_MODEL
        
        # 设置日志
        self._setup_logging()
        
        # 验证API密钥格式
        self.logger.info(f"正在验证API密钥: {self.api_key[:10]}...")
        if not self.api_key.startswith('sk-'):
            self.logger.error("API密钥格式不正确，应该以'sk-'开头")
            sys.exit(1)
        
        self.logger.info("API密钥格式验证通过")
        
    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 创建文件处理器
        log_file = os.path.join(config.OUTPUT_DIR, config.LOG_FILE)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(config.LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def score_requirement(self, requirement: Dict, project_files: List[Dict]) -> Dict:
        """使用通义千问API对单个要求进行评分"""
        
        # 构建评分提示词
        prompt = self._build_scoring_prompt(requirement, project_files)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'disable'
        }
        
        data = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "max_tokens": 1500,
                "top_p": 0.8
            }
        }
        
        # 重试机制
        for attempt in range(config.MAX_RETRIES):
            try:
                self.logger.info(f"发送API请求 (尝试 {attempt + 1}/{config.MAX_RETRIES})...")
                
                response = requests.post(
                    self.base_url, 
                    headers=headers, 
                    json=data, 
                    timeout=config.TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = self._extract_content_from_response(result)
                    
                    if content:
                        # 尝试解析JSON响应
                        try:
                            parsed = json.loads(content)
                            self.logger.info("API调用成功，解析响应完成")
                            return parsed
                        except json.JSONDecodeError:
                            self.logger.warning("API返回内容无法解析为JSON，使用默认评分")
                            return self._create_default_score(requirement)
                    else:
                        self.logger.warning("API响应格式异常，使用默认评分")
                        return self._create_default_score(requirement)
                else:
                    error_msg = f"API请求失败: {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f", {error_detail.get('message', '')}"
                    except:
                        error_msg += f", {response.text}"
                    
                    self.logger.warning(f"{error_msg} (尝试 {attempt + 1}/{config.MAX_RETRIES})")
                    
                    if attempt < config.MAX_RETRIES - 1:
                        self.logger.info(f"等待 {config.RETRY_DELAY} 秒后重试...")
                        time.sleep(config.RETRY_DELAY)
                    else:
                        self.logger.error("所有重试都失败了，使用默认评分")
                        return self._create_default_score(requirement)
                        
            except Exception as e:
                self.logger.error(f"API调用出错: {e} (尝试 {attempt + 1}/{config.MAX_RETRIES})")
                
                if attempt < config.MAX_RETRIES - 1:
                    self.logger.info(f"等待 {config.RETRY_DELAY} 秒后重试...")
                    time.sleep(config.RETRY_DELAY)
                else:
                    self.logger.error("所有重试都失败了，使用默认评分")
                    return self._create_default_score(requirement)
        
        return self._create_default_score(requirement)
    
    def _extract_content_from_response(self, result: Dict) -> Optional[str]:
        """从API响应中提取内容"""
        if 'output' in result:
            if 'choices' in result['output'] and len(result['output']['choices']) > 0:
                return result['output']['choices'][0]['message']['content']
            elif 'text' in result['output']:
                return result['output']['text']
        return None
    
    def _build_scoring_prompt(self, requirement: Dict, project_files: List[Dict]) -> str:
        """构建评分提示词"""
        
        category = requirement.get("category", "")
        requirement_text = requirement.get("requirement_text", "")
        score = requirement.get("score", 0)
        is_important = requirement.get("is_important", False)
        
        # 构建项目文件信息
        files_info = []
        for file_info in project_files:
            files_info.append(f"文件: {file_info['name']}")
            files_info.append(f"路径: {file_info['path']}")
            files_info.append(f"内容预览: {file_info['content_preview'][:200]}...")
            files_info.append("-" * 50)
        
        files_text = "\n".join(files_info)
        
        prompt = f"""你是"标书评分专家"。请根据招标文件中的要求，对照投标人的项目文件，对每个要求进行评分。

# 招标要求信息
- 要求类别: {category}
- 要求内容: {requirement_text}
- 满分分值: {score}分
- 是否重要: {'是' if is_important else '否'}

# 投标人项目文件
{files_text}

# 评分任务
请根据以下标准对要求进行评分：

## 评分标准
- **优秀 (90-100%):** 完全满足要求，内容详细，方案先进，实施可行
- **良好 (80-89%):** 基本满足要求，内容较详细，方案合理，实施可行
- **一般 (70-79%):** 部分满足要求，内容一般，方案基本可行
- **较差 (60-69%):** 勉强满足要求，内容简单，方案存在不足
- **不满足 (0-59%):** 不满足要求，内容缺失，方案不可行

## 评分要求
1. 分析招标要求的具体内容
2. 在项目文件中找到对应的响应内容
3. 评估响应的完整性、准确性和可行性
4. 给出具体的评分和详细理由
5. 指出存在的不足和改进建议

请按照以下JSON格式输出评分结果：

{{
  "requirement_id": "要求标识",
  "category": "{category}",
  "requirement_text": "{requirement_text}",
  "max_score": {score},
  "actual_score": 实际得分,
  "score_percentage": 得分百分比,
  "score_level": "优秀/良好/一般/较差/不满足",
  "scoring_reason": "详细的评分理由",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "improvement_suggestions": ["改进建议1", "改进建议2"],
  "matched_files": ["匹配的文件1", "匹配的文件2"],
  "overall_assessment": "总体评价"
}}

请确保输出的是有效的JSON格式，不要包含其他文字。"""

        return prompt
    
    def _create_default_score(self, requirement: Dict) -> Dict:
        """创建默认评分结果"""
        return {
            "requirement_id": f"req_{hash(requirement.get('requirement_text', '')) % 10000}",
            "category": requirement.get("category", ""),
            "requirement_text": requirement.get("requirement_text", ""),
            "max_score": requirement.get("score", 0),
            "actual_score": 0,
            "score_percentage": 0,
            "score_level": "不满足",
            "scoring_reason": "API调用失败，无法进行评分",
            "strengths": [],
            "weaknesses": ["无法获取评分结果"],
            "improvement_suggestions": ["请检查API配置和网络连接"],
            "matched_files": [],
            "overall_assessment": "评分失败"
        }


class EnhancedProjectFileAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.project_files = []
        self.logger = logging.getLogger(__name__)
        self._scan_project_files()
    
    def _scan_project_files(self):
        """扫描项目文件"""
        self.logger.info(f"正在扫描项目文件: {self.project_root}")
        
        # 扫描Markdown文件
        for file_path in self.project_root.rglob("*.md"):
            try:
                self._process_text_file(file_path, "markdown")
            except Exception as e:
                self.logger.error(f"读取文件失败 {file_path}: {e}")
        
        # 扫描其他文本文件
        for file_path in self.project_root.rglob("*.txt"):
            try:
                self._process_text_file(file_path, "text")
            except Exception as e:
                self.logger.error(f"读取文件失败 {file_path}: {e}")
        
        # 扫描其他类型的文件
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix not in ['.md', '.txt', '.py', '.sh']:
                try:
                    self._process_binary_file(file_path)
                except Exception as e:
                    self.logger.error(f"处理文件失败 {file_path}: {e}")
        
        self.logger.info(f"扫描完成，共找到 {len(self.project_files)} 个文件")
    
    def _process_text_file(self, file_path: Path, file_type: str):
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_info = {
            "name": file_path.name,
            "path": str(file_path.relative_to(self.project_root)),
            "full_path": str(file_path),
            "content": content,
            "content_preview": content[:500],
            "size": len(content),
            "type": file_type
        }
        
        self.project_files.append(file_info)
    
    def _process_binary_file(self, file_path: Path):
        """处理二进制文件"""
        file_info = {
            "name": file_path.name,
            "path": str(file_path.relative_to(self.project_root)),
            "full_path": str(file_path),
            "content": "",
            "content_preview": f"文件类型: {file_path.suffix}",
            "size": file_path.stat().st_size,
            "type": file_path.suffix
        }
        
        self.project_files.append(file_info)
    
    def find_relevant_files(self, requirement: Dict) -> List[Dict]:
        """根据要求找到相关的项目文件"""
        category = requirement.get("category", "")
        requirement_text = requirement.get("requirement_text", "")
        
        relevant_files = []
        
        # 根据要求类别和内容关键词匹配文件
        keywords = self._extract_keywords(requirement_text)
        
        for file_info in self.project_files:
            relevance_score = self._calculate_relevance(file_info, category, keywords)
            if relevance_score > config.RELEVANCE_THRESHOLD:
                file_info["relevance_score"] = relevance_score
                relevant_files.append(file_info)
        
        # 按相关性排序
        relevant_files.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant_files[:config.MAX_RELEVANT_FILES]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 技术相关关键词
        for keyword in config.TECH_KEYWORDS:
            if keyword in text:
                keywords.append(keyword)
        
        # 商务相关关键词
        for keyword in config.BUSINESS_KEYWORDS:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _calculate_relevance(self, file_info: Dict, category: str, keywords: List[str]) -> float:
        """计算文件与要求的相关性"""
        relevance_score = 0.0
        
        # 基于文件路径的相关性
        file_path = file_info["path"].lower()
        file_name = file_info["name"].lower()
        
        # 类别匹配
        if category == "技术要求" and any(tech in file_path for tech in ["技术", "系统", "软件", "硬件"]):
            relevance_score += 0.3
        elif category == "商务要求" and any(biz in file_path for biz in ["商务", "资质", "业绩", "管理"]):
            relevance_score += 0.3
        
        # 关键词匹配
        content = file_info["content"].lower()
        for keyword in keywords:
            if keyword in content:
                relevance_score += 0.2
            if keyword in file_name:
                relevance_score += 0.1
        
        # 文件类型权重
        if file_info["type"] in ["markdown", "text"]:
            relevance_score += 0.1
        
        return min(relevance_score, 1.0)


class EnhancedRequirementScorer:
    def __init__(self, api_key: str = None, project_root: str = None):
        self.api_key = api_key or config.API_KEY
        self.project_root = project_root or config.PROJECT_ROOT
        
        self.qianwen_scorer = EnhancedQianwenScorer(self.api_key)
        self.project_analyzer = EnhancedProjectFileAnalyzer(self.project_root)
        self.scoring_results = []
        self.logger = logging.getLogger(__name__)
    
    def load_requirements(self, requirements_file: str) -> List[Dict]:
        """加载标文要求"""
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析要求文件
            requirements = []
            
            # 查找要求块
            requirement_blocks = re.findall(r'页码: 第(\d+)页.*?概括: (.*?)\n.*?分数: (\d+)分.*?原文: (.*?)(?=\n-{40}|\n\n|$)', 
                                          content, re.DOTALL)
            
            for page_num, summary, score, text in requirement_blocks:
                # 判断类别
                category = "技术要求" if any(tech in text for tech in config.TECH_KEYWORDS) else "商务要求"
                
                requirement = {
                    "page_number": int(page_num),
                    "category": category,
                    "requirement_summary": summary.strip(),
                    "score": int(score),
                    "requirement_text": text.strip(),
                    "is_important": "▲" in text
                }
                
                requirements.append(requirement)
            
            self.logger.info(f"成功加载 {len(requirements)} 个要求")
            return requirements
            
        except Exception as e:
            self.logger.error(f"加载要求文件失败: {e}")
            return []
    
    def score_all_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """对所有要求进行评分"""
        self.logger.info(f"开始对 {len(requirements)} 个要求进行评分...")
        
        for i, requirement in enumerate(requirements):
            self.logger.info(f"\n正在评分第 {i+1}/{len(requirements)} 个要求...")
            self.logger.info(f"要求: {requirement.get('requirement_summary', '')[:50]}...")
            
            # 找到相关文件
            relevant_files = self.project_analyzer.find_relevant_files(requirement)
            self.logger.info(f"找到 {len(relevant_files)} 个相关文件")
            
            # 进行评分
            score_result = self.qianwen_scorer.score_requirement(requirement, relevant_files)
            
            # 添加原始要求信息
            score_result["original_requirement"] = requirement
            
            self.scoring_results.append(score_result)
            
            # 添加延迟避免API限制
            if i < len(requirements) - 1:
                self.logger.info(f"等待 {config.SCORING_DELAY} 秒后继续下一个要求...")
                time.sleep(config.SCORING_DELAY)
        
        return self.scoring_results
    
    def generate_scoring_report(self) -> str:
        """生成评分报告"""
        if not self.scoring_results:
            return "没有评分结果可生成报告"
        
        lines = []
        lines.append("=== 标文要求评分报告 ===\n")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 统计信息
        total_requirements = len(self.scoring_results)
        total_max_score = sum(r.get("max_score", 0) for r in self.scoring_results)
        total_actual_score = sum(r.get("actual_score", 0) for r in self.scoring_results)
        overall_score_percentage = (total_actual_score / total_max_score * 100) if total_max_score > 0 else 0
        
        lines.append(f"总要求数: {total_requirements}")
        lines.append(f"总满分: {total_max_score}分")
        lines.append(f"总得分: {total_actual_score}分")
        lines.append(f"总体得分率: {overall_score_percentage:.2f}%\n")
        
        # 按类别分组
        categories = {}
        for result in self.scoring_results:
            category = result.get("category", "未知")
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 输出每个类别的评分结果
        for category, results in categories.items():
            lines.append(f"=== {category} ===")
            lines.append(f"要求数量: {len(results)}")
            
            category_max_score = sum(r.get("max_score", 0) for r in results)
            category_actual_score = sum(r.get("actual_score", 0) for r in results)
            category_score_percentage = (category_actual_score / category_max_score * 100) if category_max_score > 0 else 0
            
            lines.append(f"满分: {category_max_score}分")
            lines.append(f"得分: {category_actual_score}分")
            lines.append(f"得分率: {category_score_percentage:.2f}%\n")
            
            # 详细评分结果
            for i, result in enumerate(results, 1):
                lines.append(f"--- 要求 {i} ---")
                lines.append(f"要求内容: {result.get('requirement_summary', '')}")
                lines.append(f"满分: {result.get('max_score', 0)}分")
                lines.append(f"得分: {result.get('actual_score', 0)}分")
                lines.append(f"得分率: {result.get('score_percentage', 0):.2f}%")
                lines.append(f"评分等级: {result.get('score_level', '')}")
                lines.append(f"评分理由: {result.get('scoring_reason', '')}")
                
                strengths = result.get('strengths', [])
                if strengths:
                    lines.append(f"优势: {', '.join(strengths)}")
                
                weaknesses = result.get('weaknesses', [])
                if weaknesses:
                    lines.append(f"不足: {', '.join(weaknesses)}")
                
                suggestions = result.get('improvement_suggestions', [])
                if suggestions:
                    lines.append(f"改进建议: {', '.join(suggestions)}")
                
                matched_files = result.get('matched_files', [])
                if matched_files:
                    lines.append(f"匹配文件: {', '.join(matched_files)}")
                
                lines.append(f"总体评价: {result.get('overall_assessment', '')}")
                lines.append("")
            
            lines.append("=" * 80)
            lines.append("")
        
        # 总结和建议
        lines.append("=== 总结与建议 ===")
        lines.append(f"总体表现: {'优秀' if overall_score_percentage >= 90 else '良好' if overall_score_percentage >= 80 else '一般' if overall_score_percentage >= 70 else '较差' if overall_score_percentage >= 60 else '不满足'}")
        
        if overall_score_percentage < 80:
            lines.append("\n主要改进方向:")
            # 分析主要不足
            all_weaknesses = []
            for result in self.scoring_results:
                all_weaknesses.extend(result.get('weaknesses', []))
            
            if all_weaknesses:
                # 统计常见不足
                weakness_count = {}
                for weakness in all_weaknesses:
                    weakness_count[weakness] = weakness_count.get(weakness, 0) + 1
                
                # 按频率排序
                sorted_weaknesses = sorted(weakness_count.items(), key=lambda x: x[1], reverse=True)
                for weakness, count in sorted_weaknesses[:5]:
                    lines.append(f"- {weakness} (出现{count}次)")
        
        return "\n".join(lines)
    
    def save_results(self, output_dir: str = None):
        """保存评分结果"""
        output_dir = output_dir or config.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存详细结果
        detailed_path = os.path.join(output_dir, f"detailed_scoring_results_{timestamp}.json")
        with open(detailed_path, 'w', encoding='utf-8') as f:
            json.dump(self.scoring_results, f, ensure_ascii=False, indent=2)
        self.logger.info(f"详细评分结果已保存到: {detailed_path}")
        
        # 保存评分报告
        report_path = os.path.join(output_dir, f"scoring_report_{timestamp}.txt")
        report = self.generate_scoring_report()
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.logger.info(f"评分报告已保存到: {report_path}")
        
        # 保存摘要结果
        summary_path = os.path.join(output_dir, f"scoring_summary_{timestamp}.json")
        summary = []
        for result in self.scoring_results:
            summary.append({
                "requirement_summary": result.get("requirement_summary", ""),
                "category": result.get("category", ""),
                "max_score": result.get("max_score", 0),
                "actual_score": result.get("actual_score", 0),
                "score_percentage": result.get("score_percentage", 0),
                "score_level": result.get("score_level", ""),
                "overall_assessment": result.get("overall_assessment", "")
            })
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        self.logger.info(f"评分摘要已保存到: {summary_path}")
        
        # 保存Excel格式（如果安装了pandas）
        try:
            import pandas as pd
            
            excel_path = os.path.join(output_dir, f"scoring_results_{timestamp}.xlsx")
            
            # 创建详细结果DataFrame
            detailed_df = pd.DataFrame(self.scoring_results)
            detailed_df = detailed_df.drop('original_requirement', axis=1, errors='ignore')
            
            # 创建摘要DataFrame
            summary_df = pd.DataFrame(summary)
            
            # 保存到Excel的不同sheet
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                detailed_df.to_excel(writer, sheet_name='详细结果', index=False)
                summary_df.to_excel(writer, sheet_name='评分摘要', index=False)
            
            self.logger.info(f"Excel格式结果已保存到: {excel_path}")
            
        except ImportError:
            self.logger.info("未安装pandas，跳过Excel格式输出")


def main():
    """主函数"""
    # 检查文件是否存在
    if not os.path.exists(config.REQUIREMENTS_FILE):
        print(f"错误: 找不到要求文件 {config.REQUIREMENTS_FILE}")
        return
    
    if not os.path.exists(config.PROJECT_ROOT):
        print(f"错误: 找不到项目目录 {config.PROJECT_ROOT}")
        return
    
    # 创建评分器
    scorer = EnhancedRequirementScorer()
    
    print("=== 增强版标文要求评分程序 ===")
    print(f"要求文件: {config.REQUIREMENTS_FILE}")
    print(f"项目目录: {config.PROJECT_ROOT}")
    print(f"输出目录: {config.OUTPUT_DIR}")
    
    # 加载要求
    requirements = scorer.load_requirements(config.REQUIREMENTS_FILE)
    if not requirements:
        print("没有找到可评分的要求，程序退出")
        return
    
    # 进行评分
    scoring_results = scorer.score_all_requirements(requirements)
    
    # 保存结果
    scorer.save_results()
    
    # 显示评分报告
    report = scorer.generate_scoring_report()
    print("\n" + report)
    
    print("\n评分完成！")


if __name__ == "__main__":
    main()

