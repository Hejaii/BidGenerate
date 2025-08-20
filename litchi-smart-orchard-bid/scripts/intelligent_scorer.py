#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能评分程序
根据PDF提取器总结的标文要求，在库中找到对应文件，使用通义千问API基于分数进行评分
"""

import os
import sys
import json
import time
import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("正在安装requests...")
    os.system("pip install requests")
    import requests

try:
    import openpyxl
except ImportError:
    print("正在安装openpyxl...")
    os.system("pip install openpyxl")
    import openpyxl


class QianwenScorer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 验证API密钥
        if not self.api_key.startswith('sk-'):
            print("错误: API密钥格式不正确，应该以'sk-'开头")
            sys.exit(1)
        
        print("通义千问API初始化成功")
        
    def score_requirement(self, requirement: Dict, library_content: str, requirement_type: str) -> Dict:
        """使用通义千问API对单个要求进行评分"""
        
        prompt = f"""你是专业的投标文件评分专家。请根据招标要求对投标方提供的材料进行评分。

# 招标要求
- 要求类型: {requirement_type}
- 要求内容: {requirement.get('requirement_text', '')}
- 要求概括: {requirement.get('requirement_summary', '')}
- 满分: {requirement.get('score', 0)}分
- 重要性: {'重要' if requirement.get('is_important', False) else '一般'}

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

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'disable'
        }
        
        data = {
            "model": "qwen-plus-2025-07-28",
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
                "max_tokens": 1000,
                "top_p": 0.8
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=200)
            
            if response.status_code == 200:
                result = response.json()
                content = None
                
                # 解析API响应
                if 'output' in result:
                    if 'choices' in result['output'] and len(result['output']['choices']) > 0:
                        content = result['output']['choices'][0]['message']['content']
                    elif 'text' in result['output']:
                        content = result['output']['text']
                    else:
                        print(f"API响应格式异常: {result}")
                        return self._create_default_score(requirement)
                else:
                    print(f"API响应格式异常: {result}")
                    return self._create_default_score(requirement)
                
                # 尝试解析JSON响应
                try:
                    parsed = json.loads(content)
                    # 添加原始要求信息
                    parsed['requirement_text'] = requirement.get('requirement_text', '')
                    parsed['requirement_summary'] = requirement.get('requirement_summary', '')
                    parsed['requirement_type'] = requirement_type
                    parsed['page_number'] = requirement.get('page_number', '')
                    parsed['is_important'] = requirement.get('is_important', False)
                    return parsed
                except json.JSONDecodeError:
                    print("API返回内容无法解析为JSON")
                    return self._create_default_score(requirement)
            else:
                print(f"API请求失败: {response.status_code}")
                return self._create_default_score(requirement)
                
        except Exception as e:
            print(f"API调用出错: {e}")
            return self._create_default_score(requirement)
    
    def _create_default_score(self, requirement: Dict) -> Dict:
        """创建默认评分结果"""
        return {
            "score": 0,
            "max_score": requirement.get('score', 0),
            "score_rate": 0.0,
            "evaluation": "API调用失败，无法进行评分",
            "strengths": [],
            "weaknesses": ["系统评分失败"],
            "suggestions": ["请检查网络连接和API配置"],
            "requirement_text": requirement.get('requirement_text', ''),
            "requirement_summary": requirement.get('requirement_summary', ''),
            "requirement_type": "未知",
            "page_number": requirement.get('page_number', ''),
            "is_important": requirement.get('is_important', False)
        }


class LibraryMatcher:
    def __init__(self, library_root: str):
        self.library_root = Path(library_root)
        self.file_cache = {}
        self._build_file_index()
    
    def _build_file_index(self):
        """构建文件索引"""
        print("正在构建文件索引...")
        
        # 公司资质文件
        company_qual_dir = self.library_root / "common" / "company_qualifications"
        if company_qual_dir.exists():
            for file_path in company_qual_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'company_qualification',
                    'content': self._read_file_content(file_path)
                }
        
        # 人员资质文件
        personnel_dir = self.library_root / "common" / "personnel" / "profiles"
        if personnel_dir.exists():
            for file_path in personnel_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'personnel_qualification',
                    'content': self._read_file_content(file_path)
                }
        
        # 项目业绩文件
        performance_dir = self.library_root / "common" / "performance"
        if performance_dir.exists():
            for file_path in performance_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'performance',
                    'content': self._read_file_content(file_path)
                }
        
        # 技术方案文件
        package_a_dir = self.library_root / "package_A"
        if package_a_dir.exists():
            for file_path in package_a_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'technical_proposal',
                    'content': self._read_file_content(file_path)
                }
        
        # 测试方案文件
        package_b_dir = self.library_root / "package_B"
        if package_b_dir.exists():
            for file_path in package_b_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'test_plan',
                    'content': self._read_file_content(file_path)
                }
        
        # 管理方案文件
        package_c_dir = self.library_root / "package_C"
        if package_c_dir.exists():
            for file_path in package_c_dir.glob("*.md"):
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': 'management_plan',
                    'content': self._read_file_content(file_path)
                }
        
        # 其他重要文件
        other_files = [
            "项目组织架构.md", "项目进度计划.md", "质量保证计划.md",
            "安全文明施工方案.md", "项目风险评估报告.md", "项目验收标准.md"
        ]
        
        for file_name in other_files:
            file_path = self.library_root / file_name
            if file_path.exists():
                self.file_cache[file_name] = {
                    'path': str(file_path),
                    'type': 'other',
                    'content': self._read_file_content(file_path)
                }
        
        print(f"文件索引构建完成，共索引 {len(self.file_cache)} 个文件")
    
    def _read_file_content(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return ""
    
    def find_relevant_files(self, requirement: Dict) -> List[Dict]:
        """根据要求找到相关的文件"""
        requirement_text = requirement.get('requirement_text', '').lower()
        requirement_summary = requirement.get('requirement_summary', '').lower()
        
        relevant_files = []
        
        # 关键词匹配规则
        keywords = {
            'iso9001': ['iso9001', 'iso 9001', '质量管理体系'],
            'iso14001': ['iso14001', 'iso 14001', '环境管理体系'],
            'iso45001': ['iso45001', 'iso 45001', '职业健康安全'],
            'cma': ['cma', '计量认证'],
            'cnas': ['cnas', '实验室认可'],
            '软件企业': ['软件企业', '软件企业认定'],
            '信息安全': ['信息安全', '安全开发', 'nsatp'],
            'iot': ['iot', '物联网', '智能硬件'],
            '科技奖': ['科技奖', '科技进步', '技术创新'],
            '项目经理': ['项目经理', 'pmp', '项目管理'],
            '测试工程师': ['测试工程师', '软件测试', '测试'],
            '数据库': ['数据库', 'db', '数据库管理'],
            '大数据': ['大数据', '数据分析', 'bigdata'],
            '信息安全': ['信息安全', '信息安全管理'],
            'it服务': ['it服务', '服务管理'],
            '智能集成': ['智能集成', '系统集成'],
            '评估师': ['评估师', '评估', 'assessor'],
            '项目业绩': ['项目业绩', '类似项目', '业绩证明'],
            '技术方案': ['技术方案', '技术实现', '功能'],
            '测试方案': ['测试方案', '测试方法', '自动化测试'],
            '质量保证': ['质量保证', '质量控制', '质量'],
            '安全管理': ['安全管理', '安全文明', '安全'],
            '风险评估': ['风险评估', '风险管理', '风险'],
            '验收标准': ['验收标准', '验收', '标准'],
            '组织架构': ['组织架构', '团队', '人员配置'],
            '进度计划': ['进度计划', '工期', '时间安排'],
            '成本控制': ['成本控制', '预算', '成本']
        }
        
        # 根据关键词匹配文件
        for keyword, patterns in keywords.items():
            for pattern in patterns:
                if pattern in requirement_text or pattern in requirement_summary:
                    # 查找包含关键词的文件
                    for file_name, file_info in self.file_cache.items():
                        if keyword in file_name.lower() or any(p in file_info['content'].lower() for p in patterns):
                            if file_info not in relevant_files:
                                relevant_files.append(file_info)
        
        # 如果没有找到相关文件，返回所有文件供参考
        if not relevant_files:
            print(f"警告: 未找到与要求 '{requirement_summary}' 直接相关的文件")
            # 返回一些通用文件
            general_files = ['项目组织架构.md', '质量保证计划.md', '项目总结.md']
            for file_name in general_files:
                if file_name in self.file_cache:
                    relevant_files.append(self.file_cache[file_name])
        
        return relevant_files


class IntelligentScorer:
    def __init__(self, api_key: str, library_root: str):
        self.scorer = QianwenScorer(api_key)
        self.matcher = LibraryMatcher(library_root)
        self.scoring_results = []
    
    def load_requirements(self, requirements_file: str) -> List[Dict]:
        """加载PDF提取器生成的要求文件"""
        print(f"正在加载要求文件: {requirements_file}")
        
        if requirements_file.endswith('.json'):
            # JSON格式
            with open(requirements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # 合并商务和技术要求
                    requirements = []
                    if 'business' in data:
                        for req in data['business']:
                            req['category'] = '商务要求'
                            requirements.append(req)
                    if 'technical' in data:
                        for req in data['technical']:
                            req['category'] = '技术要求'
                            requirements.append(req)
                    return requirements
                else:
                    return data
        elif requirements_file.endswith('.txt'):
            # 文本格式，尝试解析
            return self._parse_text_requirements(requirements_file)
        else:
            print(f"不支持的文件格式: {requirements_file}")
            return []
    
    def _parse_text_requirements(self, text_file: str) -> List[Dict]:
        """解析文本格式的要求文件"""
        requirements = []
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的文本解析逻辑
            lines = content.split('\n')
            current_requirement = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('页码:'):
                    if current_requirement:
                        requirements.append(current_requirement)
                    current_requirement = {'page_number': line.split(':', 1)[1].strip()}
                elif line.startswith('概括:'):
                    current_requirement['requirement_summary'] = line.split(':', 1)[1].strip()
                elif line.startswith('分数:'):
                    score_text = line.split(':', 1)[1].strip()
                    score_match = re.search(r'(\d+)分', score_text)
                    if score_match:
                        current_requirement['score'] = int(score_match.group(1))
                elif line.startswith('重要性:'):
                    importance_text = line.split(':', 1)[1].strip()
                    current_requirement['is_important'] = '重要' in importance_text
                elif line.startswith('原文:'):
                    current_requirement['requirement_text'] = line.split(':', 1)[1].strip()
                    # 判断类别
                    if '商务' in content or '资格' in content or '投标' in content:
                        current_requirement['category'] = '商务要求'
                    else:
                        current_requirement['category'] = '技术要求'
            
            if current_requirement:
                requirements.append(current_requirement)
                
        except Exception as e:
            print(f"解析文本文件失败: {e}")
        
        return requirements
    
    def score_all_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """对所有要求进行评分"""
        print(f"开始对 {len(requirements)} 个要求进行评分...")
        
        results = []
        
        for i, requirement in enumerate(requirements, 1):
            print(f"\n正在评分第 {i}/{len(requirements)} 个要求: {requirement.get('requirement_summary', '')}")
            
            # 找到相关文件
            relevant_files = self.matcher.find_relevant_files(requirement)
            
            if relevant_files:
                # 合并相关文件内容
                combined_content = "\n\n".join([f"文件: {f['path']}\n内容:\n{f['content']}" for f in relevant_files])
                
                # 使用API进行评分
                score_result = self.scorer.score_requirement(
                    requirement, 
                    combined_content, 
                    requirement.get('category', '未知')
                )
                
                # 添加文件信息
                score_result['relevant_files'] = [f['path'] for f in relevant_files]
                score_result['requirement_id'] = i
                
                results.append(score_result)
                
                print(f"评分完成: {score_result['score']}/{score_result['max_score']} 分")
                
                # 添加延迟避免API限制
                if i < len(requirements):
                    print("等待3秒后继续下一个要求...")
                    time.sleep(3)
            else:
                print(f"警告: 未找到相关文件，无法评分")
                # 创建默认评分结果
                default_result = self.scorer._create_default_score(requirement)
                default_result['relevant_files'] = []
                default_result['requirement_id'] = i
                results.append(default_result)
        
        self.scoring_results = results
        return results
    
    def generate_scoring_report(self, output_file: str = None) -> str:
        """生成评分报告"""
        if not self.scoring_results:
            return "没有评分结果可生成报告"
        
        # 计算统计信息
        total_score = sum(r['score'] for r in self.scoring_results)
        total_max_score = sum(r['max_score'] for r in self.scoring_results)
        overall_score_rate = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        # 按类别统计
        category_stats = {}
        for result in self.scoring_results:
            category = result.get('requirement_type', '未知')
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'total_score': 0, 'max_score': 0}
            category_stats[category]['count'] += 1
            category_stats[category]['total_score'] += result['score']
            category_stats[category]['max_score'] += result['max_score']
        
        # 生成报告
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("智能评分报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"总要求数: {len(self.scoring_results)}")
        report_lines.append(f"总得分: {total_score}")
        report_lines.append(f"总分: {total_max_score}")
        report_lines.append(f"总体得分率: {overall_score_rate:.2f}%")
        report_lines.append("")
        
        # 类别统计
        report_lines.append("类别统计:")
        report_lines.append("-" * 40)
        for category, stats in category_stats.items():
            if stats['max_score'] > 0:
                rate = (stats['total_score'] / stats['max_score'] * 100)
                report_lines.append(f"{category}: {stats['total_score']}/{stats['max_score']} ({rate:.2f}%) - {stats['count']}项")
        report_lines.append("")
        
        # 详细评分结果
        report_lines.append("详细评分结果:")
        report_lines.append("=" * 80)
        
        for result in self.scoring_results:
            report_lines.append(f"要求 {result['requirement_id']}: {result.get('requirement_summary', '')}")
            report_lines.append(f"类型: {result.get('requirement_type', '未知')}")
            report_lines.append(f"页码: {result.get('page_number', '未知')}")
            report_lines.append(f"重要性: {'重要' if result.get('is_important', False) else '一般'}")
            report_lines.append(f"得分: {result['score']}/{result['max_score']} ({result['score_rate']:.2f}%)")
            report_lines.append(f"评分说明: {result['evaluation']}")
            
            if result['strengths']:
                report_lines.append(f"优势: {', '.join(result['strengths'])}")
            if result['weaknesses']:
                report_lines.append(f"不足: {', '.join(result['weaknesses'])}")
            if result['suggestions']:
                report_lines.append(f"建议: {', '.join(result['suggestions'])}")
            
            if result['relevant_files']:
                report_lines.append(f"相关文件: {', '.join(result['relevant_files'])}")
            
            report_lines.append("-" * 60)
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # 保存报告
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"评分报告已保存到: {output_file}")
            except Exception as e:
                print(f"保存报告失败: {e}")
        
        return report
    
    def export_excel_report(self, output_file: str):
        """导出Excel格式的评分报告"""
        if not self.scoring_results:
            print("没有评分结果可导出")
            return
        
        try:
            # 准备数据
            data = []
            for result in self.scoring_results:
                data.append({
                    '要求编号': result['requirement_id'],
                    '要求概括': result.get('requirement_summary', ''),
                    '要求类型': result.get('requirement_type', ''),
                    '页码': result.get('page_number', ''),
                    '重要性': '重要' if result.get('is_important', False) else '一般',
                    '得分': result['score'],
                    '满分': result['max_score'],
                    '得分率(%)': result['score_rate'],
                    '评分说明': result['evaluation'],
                    '优势': '; '.join(result.get('strengths', [])),
                    '不足': '; '.join(result.get('weaknesses', [])),
                    '建议': '; '.join(result.get('suggestions', [])),
                    '相关文件': '; '.join(result.get('relevant_files', []))
                })
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 导出到Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='评分结果', index=False)
                
                # 添加统计信息
                stats_data = []
                total_score = sum(r['score'] for r in self.scoring_results)
                total_max_score = sum(r['max_score'] for r in self.scoring_results)
                overall_rate = (total_score / total_max_score * 100) if total_max_score > 0 else 0
                
                stats_data.append(['总要求数', len(self.scoring_results)])
                stats_data.append(['总得分', total_score])
                stats_data.append(['总分', total_max_score])
                stats_data.append(['总体得分率(%)', f"{overall_rate:.2f}"])
                
                stats_df = pd.DataFrame(stats_data, columns=['指标', '数值'])
                stats_df.to_excel(writer, sheet_name='统计信息', index=False)
            
            print(f"Excel评分报告已导出到: {output_file}")
            
        except Exception as e:
            print(f"导出Excel报告失败: {e}")


def main():
    """主函数"""
    # API密钥配置
    import os
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 项目根目录
    library_root = "/Users/leojiang/PycharmProjects/标书生成/litchi-smart-orchard-bid"
    
    # 检查目录是否存在
    if not os.path.exists(library_root):
        print(f"错误: 找不到项目目录 {library_root}")
        return
    
    # 查找要求文件
    requirements_files = []
    for file in os.listdir("/Users/leojiang/PycharmProjects/标书生成"):
        if file.startswith("03.招标文件_qualification_requirements_report") and file.endswith(".txt"):
            requirements_files.append(file)
        elif file.startswith("03.招标文件_qualification_requirements_data") and file.endswith(".json"):
            requirements_files.append(file)
    
    if not requirements_files:
        print("错误: 未找到要求文件，请先运行PDF提取器")
        return
    
    print("找到以下要求文件:")
    for i, file in enumerate(requirements_files, 1):
        print(f"{i}. {file}")
    
    try:
        choice = int(input(f"\n请选择要分析的文件 (1-{len(requirements_files)}): ")) - 1
        if choice < 0 or choice >= len(requirements_files):
            print("选择无效")
            return
        
        selected_file = requirements_files[choice]
        full_path = os.path.join("/Users/leojiang/PycharmProjects/标书生成", selected_file)
        
    except (ValueError, KeyboardInterrupt):
        print("输入无效或用户取消")
        return
    
    print(f"\n开始分析文件: {selected_file}")
    
    # 创建智能评分器
    scorer = IntelligentScorer(api_key, library_root)
    
    # 加载要求
    requirements = scorer.load_requirements(full_path)
    if not requirements:
        print("未加载到任何要求，程序退出")
        return
    
    print(f"成功加载 {len(requirements)} 个要求")
    
    # 进行评分
    scoring_results = scorer.score_all_requirements(requirements)
    
    # 生成报告
    print("\n正在生成评分报告...")
    
    # 文本报告
    report_file = full_path.replace('.txt', '_scoring_report.txt').replace('.json', '_scoring_report.txt')
    report = scorer.generate_scoring_report(report_file)
    
    # Excel报告
    excel_file = full_path.replace('.txt', '_scoring_report.xlsx').replace('.json', '_scoring_report.xlsx')
    scorer.export_excel_report(excel_file)
    
    print("\n评分完成！")
    print(f"文本报告: {report_file}")
    print(f"Excel报告: {excel_file}")


if __name__ == "__main__":
    main()



