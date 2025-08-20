#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟版标文要求评分程序
不依赖外部API，用于演示程序工作流程和测试功能
"""

import os
import sys
import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import random

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except ImportError:
    print("错误: 找不到配置文件 config.py")
    sys.exit(1)


class MockQianwenScorer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def score_requirement(self, requirement: Dict, project_files: List[Dict]) -> Dict:
        """模拟通义千问API对单个要求进行评分"""
        
        self.logger.info("使用模拟评分器进行评分...")
        
        # 模拟评分逻辑
        category = requirement.get("category", "")
        requirement_text = requirement.get("requirement_text", "")
        score = requirement.get("score", 0)
        is_important = requirement.get("is_important", False)
        
        # 基于文件匹配情况生成模拟评分
        if project_files:
            # 有相关文件，生成较好的评分
            base_score = random.uniform(0.7, 1.0)  # 70%-100%
            actual_score = int(score * base_score)
            score_percentage = (actual_score / score * 100) if score > 0 else 0
            
            if score_percentage >= 90:
                score_level = "优秀"
            elif score_percentage >= 80:
                score_level = "良好"
            elif score_percentage >= 70:
                score_level = "一般"
            else:
                score_level = "较差"
            
            # 生成模拟的评分理由
            scoring_reason = self._generate_scoring_reason(requirement, project_files, score_percentage)
            strengths = self._generate_strengths(project_files)
            weaknesses = self._generate_weaknesses(score_percentage)
            suggestions = self._generate_suggestions(score_percentage)
            matched_files = [f["name"] for f in project_files[:3]]
            overall_assessment = f"基本满足要求，得分率{score_percentage:.1f}%"
            
        else:
            # 没有相关文件，生成较差的评分
            actual_score = int(score * random.uniform(0.3, 0.6))  # 30%-60%
            score_percentage = (actual_score / score * 100) if score > 0 else 0
            score_level = "不满足"
            
            scoring_reason = "未找到相关项目文件，无法评估要求满足情况"
            strengths = []
            weaknesses = ["缺乏相关文件支撑", "无法验证要求满足情况"]
            suggestions = ["补充相关技术文档", "完善项目实施方案"]
            matched_files = []
            overall_assessment = "缺乏相关文件支撑，建议补充完善"
        
        return {
            "requirement_id": f"req_{hash(requirement.get('requirement_text', '')) % 10000}",
            "category": category,
            "requirement_text": requirement_text,
            "max_score": score,
            "actual_score": actual_score,
            "score_percentage": score_percentage,
            "score_level": score_level,
            "scoring_reason": scoring_reason,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": suggestions,
            "matched_files": matched_files,
            "overall_assessment": overall_assessment
        }
    
    def _generate_scoring_reason(self, requirement: Dict, project_files: List[Dict], score_percentage: float) -> str:
        """生成模拟的评分理由"""
        category = requirement.get("category", "")
        
        if score_percentage >= 90:
            return f"项目文件完全满足{category}要求，内容详细完整，方案可行性强"
        elif score_percentage >= 80:
            return f"项目文件基本满足{category}要求，内容较详细，方案基本可行"
        elif score_percentage >= 70:
            return f"项目文件部分满足{category}要求，内容一般，方案基本可行"
        else:
            return f"项目文件勉强满足{category}要求，内容简单，存在不足"
    
    def _generate_strengths(self, project_files: List[Dict]) -> List[str]:
        """生成模拟的优势分析"""
        strengths = []
        if project_files:
            strengths.append("相关文件齐全")
            strengths.append("内容结构清晰")
            if len(project_files) > 2:
                strengths.append("覆盖范围全面")
        return strengths
    
    def _generate_weaknesses(self, score_percentage: float) -> List[str]:
        """生成模拟的不足分析"""
        weaknesses = []
        if score_percentage < 90:
            weaknesses.append("部分内容需要进一步完善")
        if score_percentage < 80:
            weaknesses.append("技术细节描述不够详细")
        if score_percentage < 70:
            weaknesses.append("实施方案需要优化")
        return weaknesses
    
    def _generate_suggestions(self, score_percentage: float) -> List[str]:
        """生成模拟的改进建议"""
        suggestions = []
        if score_percentage < 90:
            suggestions.append("补充更多技术细节")
        if score_percentage < 80:
            suggestions.append("完善实施方案")
        if score_percentage < 70:
            suggestions.append("加强质量控制措施")
        return suggestions


class MockProjectFileAnalyzer:
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


class MockRequirementScorer:
    def __init__(self, project_root: str = None):
        self.project_root = project_root or config.PROJECT_ROOT
        
        self.mock_scorer = MockQianwenScorer()
        self.project_analyzer = MockProjectFileAnalyzer(self.project_root)
        self.scoring_results = []
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter(config.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
    
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
            score_result = self.mock_scorer.score_requirement(requirement, relevant_files)
            
            # 添加原始要求信息
            score_result["original_requirement"] = requirement
            
            self.scoring_results.append(score_result)
            
            # 模拟处理时间
            if i < len(requirements) - 1:
                self.logger.info("模拟处理中，等待1秒...")
                import time
                time.sleep(1)
        
        return self.scoring_results
    
    def generate_scoring_report(self) -> str:
        """生成评分报告"""
        if not self.scoring_results:
            return "没有评分结果可生成报告"
        
        lines = []
        lines.append("=== 标文要求评分报告 (模拟版) ===")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("注意: 这是模拟评分结果，仅用于演示程序功能\n")
        
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
        detailed_path = os.path.join(output_dir, f"mock_detailed_scoring_results_{timestamp}.json")
        with open(detailed_path, 'w', encoding='utf-8') as f:
            json.dump(self.scoring_results, f, ensure_ascii=False, indent=2)
        self.logger.info(f"详细评分结果已保存到: {detailed_path}")
        
        # 保存评分报告
        report_path = os.path.join(output_dir, f"mock_scoring_report_{timestamp}.txt")
        report = self.generate_scoring_report()
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.logger.info(f"评分报告已保存到: {report_path}")
        
        # 保存摘要结果
        summary_path = os.path.join(output_dir, f"mock_scoring_summary_{timestamp}.json")
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


def main():
    """主函数"""
    # 检查文件是否存在
    if not os.path.exists(config.REQUIREMENTS_FILE):
        print(f"错误: 找不到要求文件 {config.REQUIREMENTS_FILE}")
        return
    
    if not os.path.exists(config.PROJECT_ROOT):
        print(f"错误: 找不到项目目录 {config.PROJECT_ROOT}")
        return
    
    # 创建模拟评分器
    scorer = MockRequirementScorer()
    
    print("=== 模拟版标文要求评分程序 ===")
    print("注意: 这是模拟版本，不依赖外部API，仅用于演示程序功能")
    print(f"要求文件: {config.REQUIREMENTS_FILE}")
    print(f"项目目录: {config.PROJECT_ROOT}")
    print(f"输出目录: {config.OUTPUT_DIR}")
    print()
    
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
    
    print("\n模拟评分完成！")
    print("如需真实评分，请配置有效的通义千问API密钥")


if __name__ == "__main__":
    main()

