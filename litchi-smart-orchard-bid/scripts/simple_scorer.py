#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版智能评分程序
根据PDF提取器总结的标文要求，在库中找到对应文件，使用通义千问API基于分数进行评分
"""

import os
import sys
import json
import time
import re
import pandas as pd
from typing import Dict, List
from pathlib import Path

# 导入配置
try:
    from scoring_config import *
except ImportError:
    print("错误: 找不到配置文件 scoring_config.py")
    sys.exit(1)

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


class SimpleScorer:
    def __init__(self):
        self.api_key = QIANWEN_API_KEY
        self.base_url = QIANWEN_BASE_URL
        self.library_root = Path(LIBRARY_ROOT)
        self.file_cache = {}
        self.scoring_results = []
        self._build_file_index()
    
    def _build_file_index(self):
        """构建文件索引"""
        print("正在构建文件索引...")
        
        # 索引所有markdown文件
        for file_path in self.library_root.rglob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 确定文件类型
                file_type = self._determine_file_type(file_path)
                
                self.file_cache[file_path.name] = {
                    'path': str(file_path),
                    'type': file_type,
                    'content': content
                }
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")
        
        print(f"文件索引构建完成，共索引 {len(self.file_cache)} 个文件")
    
    def _determine_file_type(self, file_path: Path) -> str:
        """确定文件类型"""
        path_str = str(file_path).lower()
        
        if 'company_qualifications' in path_str:
            return 'company_qualification'
        elif 'personnel' in path_str and 'profiles' in path_str:
            return 'personnel_qualification'
        elif 'performance' in path_str:
            return 'performance'
        elif 'package_a' in path_str:
            return 'technical_proposal'
        elif 'package_b' in path_str:
            return 'test_plan'
        elif 'package_c' in path_str:
            return 'management_plan'
        else:
            return 'other'
    
    def find_relevant_files(self, requirement: Dict) -> List[Dict]:
        """根据要求找到相关的文件"""
        requirement_text = requirement.get('requirement_text', '').lower()
        requirement_summary = requirement.get('requirement_summary', '').lower()
        
        relevant_files = []
        
        # 使用配置的关键词匹配规则
        for keyword, patterns in KEYWORD_MATCHING_RULES.items():
            for pattern in patterns:
                if pattern in requirement_text or pattern in requirement_summary:
                    # 查找包含关键词的文件
                    for file_name, file_info in self.file_cache.items():
                        if (keyword in file_name.lower() or 
                            any(p in file_info['content'].lower() for p in patterns)):
                            if file_info not in relevant_files:
                                relevant_files.append(file_info)
        
        # 如果没有找到相关文件，返回一些通用文件
        if not relevant_files:
            print(f"警告: 未找到与要求 '{requirement_summary}' 直接相关的文件")
            general_files = ['项目组织架构.md', '质量保证计划.md', '项目总结.md']
            for file_name in general_files:
                if file_name in self.file_cache:
                    relevant_files.append(self.file_cache[file_name])
        
        return relevant_files
    
    def score_requirement(self, requirement: Dict, library_content: str) -> Dict:
        """使用通义千问API对单个要求进行评分，支持模型自动切换"""
        
        # 使用配置的提示词模板
        prompt = SCORING_PROMPT_TEMPLATE.format(
            requirement_type=requirement.get('category', '未知'),
            requirement_text=requirement.get('requirement_text', ''),
            requirement_summary=requirement.get('requirement_summary', ''),
            max_score=requirement.get('score', 0),
            importance='重要' if requirement.get('is_important', False) else '一般',
            library_content=library_content
        )
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'disable'
        }
        
        # 尝试所有可用的模型
        for model_index, model_name in enumerate(QIANWEN_MODELS):
            print(f"  尝试模型 {model_index + 1}/{len(QIANWEN_MODELS)}: {model_name}")
            
            data = {
                "model": model_name,
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
                response = requests.post(self.base_url, headers=headers, json=data, timeout=API_TIMEOUT_SECONDS)
                
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
                            print(f"    API响应格式异常，尝试下一个模型")
                            continue
                    else:
                        print(f"    API响应格式异常，尝试下一个模型")
                        continue
                    
                    # 尝试解析JSON响应
                    try:
                        parsed = json.loads(content)
                        # 添加原始要求信息
                        parsed['requirement_text'] = requirement.get('requirement_text', '')
                        parsed['requirement_summary'] = requirement.get('requirement_summary', '')
                        parsed['requirement_type'] = requirement.get('category', '未知')
                        parsed['page_number'] = requirement.get('page_number', '')
                        parsed['is_important'] = requirement.get('is_important', False)
                        parsed['used_model'] = model_name  # 记录使用的模型
                        print(f"    模型 {model_name} 调用成功")
                        return parsed
                    except json.JSONDecodeError:
                        print(f"    模型 {model_name} 返回内容无法解析为JSON，尝试下一个模型")
                        continue
                        
                elif response.status_code == 400:
                    print(f"    模型 {model_name} 返回400错误，尝试下一个模型")
                    continue
                else:
                    print(f"    模型 {model_name} 请求失败: {response.status_code}，尝试下一个模型")
                    continue
                    
            except Exception as e:
                print(f"    模型 {model_name} 调用出错: {e}，尝试下一个模型")
                continue
        
        # 所有模型都失败了
        print(f"  所有模型都调用失败，使用默认评分")
        return self._create_default_score(requirement)
    
    def _create_default_score(self, requirement: Dict) -> Dict:
        """创建默认评分结果"""
        return {
            "score": 0,
            "max_score": requirement.get('score', 0),
            "score_rate": 0.0,
            "evaluation": "所有模型都调用失败，无法进行评分",
            "strengths": [],
            "weaknesses": ["系统评分失败"],
            "suggestions": ["请检查网络连接和API配置"],
            "requirement_text": requirement.get('requirement_text', ''),
            "requirement_summary": requirement.get('requirement_summary', ''),
            "requirement_type": requirement.get('category', '未知'),
            "page_number": requirement.get('page_number', ''),
            "is_important": requirement.get('is_important', False),
            "used_model": "无"  # 记录使用的模型
        }
    
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
            
            # 改进的文本解析逻辑
            lines = content.split('\n')
            current_requirement = {}
            in_requirement_block = False
            
            for line in lines:
                line = line.strip()
                
                # 检测要求块的开始
                if line.startswith('页码:'):
                    if current_requirement and 'requirement_summary' in current_requirement:
                        requirements.append(current_requirement)
                    current_requirement = {'page_number': line.split(':', 1)[1].strip()}
                    in_requirement_block = True
                    continue
                
                if not in_requirement_block:
                    continue
                
                # 解析各个字段
                if line.startswith('概括:'):
                    current_requirement['requirement_summary'] = line.split(':', 1)[1].strip()
                elif line.startswith('分数:'):
                    score_text = line.split(':', 1)[1].strip()
                    # 更灵活的分数提取
                    score_match = re.search(r'(\d+(?:\.\d+)?)分', score_text)
                    if score_match:
                        score_value = float(score_match.group(1))
                        current_requirement['score'] = score_value
                    else:
                        current_requirement['score'] = 0
                elif line.startswith('重要性:'):
                    importance_text = line.split(':', 1)[1].strip()
                    current_requirement['is_important'] = '重要' in importance_text
                elif line.startswith('原文:'):
                    requirement_text = line.split(':', 1)[1].strip()
                    # 如果原文太长，截取前200字符
                    if len(requirement_text) > 200:
                        requirement_text = requirement_text[:200] + "..."
                    current_requirement['requirement_text'] = requirement_text
                    
                    # 智能判断类别
                    if any(keyword in content.lower() for keyword in ['商务', '资格', '投标', '认证', '证书', '业绩']):
                        current_requirement['category'] = '商务要求'
                    else:
                        current_requirement['category'] = '技术要求'
                
                # 检测要求块的结束（分隔线）
                elif line.startswith('---') and len(line) >= 20:
                    in_requirement_block = False
            
            # 添加最后一个要求
            if current_requirement and 'requirement_summary' in current_requirement:
                requirements.append(current_requirement)
            
            # 去重处理（基于概括内容）
            seen_summaries = set()
            unique_requirements = []
            for req in requirements:
                summary = req.get('requirement_summary', '')
                if summary and summary not in seen_summaries:
                    seen_summaries.add(summary)
                    unique_requirements.append(req)
            
            print(f"解析完成: 原始要求 {len(requirements)} 条，去重后 {len(unique_requirements)} 条")
            return unique_requirements
                
        except Exception as e:
            print(f"解析文本文件失败: {e}")
            return []
    
    def score_all_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """对所有要求进行评分"""
        print(f"开始对 {len(requirements)} 个要求进行评分...")
        
        results = []
        
        for i, requirement in enumerate(requirements, 1):
            print(f"\n正在评分第 {i}/{len(requirements)} 个要求: {requirement.get('requirement_summary', '')}")
            
            # 找到相关文件
            relevant_files = self.find_relevant_files(requirement)
            
            if relevant_files:
                # 合并相关文件内容
                combined_content = "\n\n".join([f"文件: {f['path']}\n内容:\n{f['content']}" for f in relevant_files])
                
                # 使用API进行评分
                score_result = self.score_requirement(requirement, combined_content)
                
                # 添加文件信息
                score_result['relevant_files'] = [f['path'] for f in relevant_files]
                score_result['requirement_id'] = i
                
                results.append(score_result)
                
                print(f"评分完成: {score_result['score']}/{score_result['max_score']} 分")
                
                # 添加延迟避免API限制
                if i < len(requirements):
                    print(f"等待{SCORING_DELAY_SECONDS}秒后继续下一个要求...")
                    time.sleep(SCORING_DELAY_SECONDS)
            else:
                print(f"警告: 未找到相关文件，无法评分")
                # 创建默认评分结果
                default_result = self._create_default_score(requirement)
                default_result['relevant_files'] = []
                default_result['requirement_id'] = i
                results.append(default_result)
        
        self.scoring_results = results
        return results
    
    def enhance_scoring_results_with_llm(self) -> List[Dict]:
        """使用LLM增强评分结果，生成写作要点"""
        if not self.scoring_results:
            print("没有评分结果可增强")
            return []
        
        print(f"\n开始LLM增强流程，处理 {len(self.scoring_results)} 个评分结果...")
        
        enhanced_results = []
        
        for i, result in enumerate(self.scoring_results, 1):
            print(f"\n正在增强第 {i}/{len(self.scoring_results)} 个结果: {result.get('requirement_summary', '')}")
            
            # 调用LLM生成增强信息
            enhanced_info = self._generate_enhancement_with_llm(result)
            
            # 合并原始结果和增强信息
            enhanced_result = {**result, **enhanced_info}
            enhanced_results.append(enhanced_result)
            
            print(f"增强完成")
            
            # 添加延迟避免API限制
            if i < len(self.scoring_results):
                print(f"等待{SCORING_DELAY_SECONDS}秒后继续下一个...")
                time.sleep(SCORING_DELAY_SECONDS)
        
        self.enhanced_results = enhanced_results # 保存增强结果
        return enhanced_results
    
    def _generate_enhancement_with_llm(self, scoring_result: Dict) -> Dict:
        """使用LLM为单个评分结果生成增强信息"""
        
        prompt = f"""你是专业的投标文件写作顾问。请基于以下评分结果，生成结构化的写作要点增强信息。

# 评分结果信息
- 要求概括: {scoring_result.get('requirement_summary', '')}
- 要求类型: {scoring_result.get('requirement_type', '')}
- 得分: {scoring_result['score']}/{scoring_result['max_score']}
- 得分率: {scoring_result.get('score_rate', 0):.2f}%
- 评分说明: {scoring_result.get('evaluation', '')}
- 优势: {', '.join(scoring_result.get('strengths', []))}
- 不足: {', '.join(scoring_result.get('weaknesses', []))}
- 建议: {', '.join(scoring_result.get('suggestions', []))}
- 相关文件: {', '.join(scoring_result.get('relevant_files', []))}

# 任务要求
请生成以下结构化信息，用于后续写作：
1. 要点清单：关键要点和注意事项
2. 证据锚点计划：需要提供的具体证据和材料
3. 缺失材料：当前缺少的关键材料
4. 风险提示：潜在风险和注意事项
5. 标签：分类标签和关键词
6. 写作参数模板：后续写作需要的具体参数

# 输出格式
请严格按照以下JSON格式输出，不要包含其他文字：

{{
  "key_points": ["要点1", "要点2", "要点3"],
  "evidence_plan": ["证据1", "证据2", "证据3"],
  "missing_materials": ["缺失材料1", "缺失材料2"],
  "risk_warnings": ["风险1", "风险2"],
  "tags": ["标签1", "标签2", "标签3"],
  "writing_params": {{
    "focus_areas": ["重点领域1", "重点领域2"],
    "required_docs": ["需要文档1", "需要文档2"],
    "quality_standards": ["质量标准1", "质量标准2"],
    "compliance_notes": "合规性说明",
    "action_items": ["行动项1", "行动项2"]
  }},
  "human_verification_needed": false,
  "verification_reason": ""
}}

注意：
- 只输出JSON，不要有任何其他文字
- 如果信息缺失无法确定，将 human_verification_needed 设为 true，并在 verification_reason 中说明原因
- 禁止臆造正文或事实，基于已有信息进行分析"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'disable'
        }
        
        # 尝试所有可用的模型
        for model_index, model_name in enumerate(QIANWEN_MODELS):
            print(f"  尝试模型 {model_index + 1}/{len(QIANWEN_MODELS)}: {model_name}")
            
            data = {
                "model": model_name,
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
            
            try:
                response = requests.post(self.base_url, headers=headers, json=data, timeout=API_TIMEOUT_SECONDS)
                
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
                            print(f"    API响应格式异常，尝试下一个模型")
                            continue
                    else:
                        print(f"    API响应格式异常，尝试下一个模型")
                        continue
                    
                    # 尝试解析JSON响应
                    try:
                        parsed = json.loads(content)
                        parsed['enhancement_model'] = model_name  # 记录使用的模型
                        print(f"    模型 {model_name} 增强成功")
                        return parsed
                    except json.JSONDecodeError:
                        print(f"    模型 {model_name} 返回内容无法解析为JSON，尝试下一个模型")
                        continue
                        
                elif response.status_code == 400:
                    print(f"    模型 {model_name} 返回400错误，尝试下一个模型")
                    continue
                else:
                    print(f"    模型 {model_name} 请求失败: {response.status_code}，尝试下一个模型")
                    continue
                    
            except Exception as e:
                print(f"    模型 {model_name} 调用出错: {e}，尝试下一个模型")
                continue
        
        # 所有模型都失败了，返回默认增强信息
        print(f"  所有模型都调用失败，使用默认增强信息")
        return self._create_default_enhancement(scoring_result)
    
    def _create_default_enhancement(self, scoring_result: Dict) -> Dict:
        """创建默认的增强信息"""
        return {
            "key_points": ["需人工确认：无法自动生成要点"],
            "evidence_plan": ["需人工确认：无法自动生成证据计划"],
            "missing_materials": ["需人工确认：无法自动识别缺失材料"],
            "risk_warnings": ["需人工确认：无法自动识别风险"],
            "tags": ["需人工确认", "LLM调用失败"],
            "writing_params": {
                "focus_areas": ["需人工确认"],
                "required_docs": ["需人工确认"],
                "quality_standards": ["需人工确认"],
                "compliance_notes": "需人工确认：LLM调用失败",
                "action_items": ["检查网络连接", "验证API配置"]
            },
            "human_verification_needed": True,
            "verification_reason": "LLM调用失败，无法自动生成增强信息",
            "enhancement_model": "无"
        }
    
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
        report_lines.append(REPORT_TEMPLATE['separator'])
        report_lines.append(REPORT_TEMPLATE['title'])
        report_lines.append(REPORT_TEMPLATE['separator'])
        report_lines.append(f"生成时间: {time.strftime(REPORT_TEMPLATE['date_format'])}")
        report_lines.append(f"总要求数: {len(self.scoring_results)}")
        report_lines.append(f"总得分: {total_score}")
        report_lines.append(f"总分: {total_max_score}")
        report_lines.append(f"总体得分率: {overall_score_rate:.2f}%")
        report_lines.append("")
        
        # 类别统计
        report_lines.append("类别统计:")
        report_lines.append(REPORT_TEMPLATE['sub_separator'])
        for category, stats in category_stats.items():
            if stats['max_score'] > 0:
                rate = (stats['total_score'] / stats['max_score'] * 100)
                report_lines.append(f"{category}: {stats['total_score']}/{stats['max_score']} ({rate:.2f}%) - {stats['count']}项")
        report_lines.append("")
        
        # 详细评分结果
        report_lines.append("详细评分结果:")
        report_lines.append(REPORT_TEMPLATE['separator'])
        
        for result in self.scoring_results:
            report_lines.append(f"要求 {result['requirement_id']}: {result.get('requirement_summary', '')}")
            report_lines.append(f"类型: {result.get('requirement_type', '未知')}")
            report_lines.append(f"页码: {result.get('page_number', '未知')}")
            report_lines.append(f"重要性: {'重要' if result.get('is_important', False) else '一般'}")
            report_lines.append(f"得分: {result['score']}/{result['max_score']} ({result['score_rate']:.2f}%)")
            report_lines.append(f"使用模型: {result.get('used_model', '未知')}")
            report_lines.append(f"评分说明: {result['evaluation']}")
            
            if result['strengths']:
                report_lines.append(f"优势: {', '.join(result['strengths'])}")
            if result['weaknesses']:
                report_lines.append(f"不足: {', '.join(result['weaknesses'])}")
            if result['suggestions']:
                report_lines.append(f"建议: {', '.join(result['suggestions'])}")
            
            if result['relevant_files']:
                report_lines.append(f"相关文件: {', '.join(result['relevant_files'])}")
            
            report_lines.append(REPORT_TEMPLATE['sub_separator'])
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
            # 准备基础评分数据
            basic_data = []
            for result in self.scoring_results:
                basic_data.append({
                    EXCEL_COLUMNS['requirement_id']: result['requirement_id'],
                    EXCEL_COLUMNS['requirement_summary']: result.get('requirement_summary', ''),
                    EXCEL_COLUMNS['requirement_type']: result.get('requirement_type', ''),
                    EXCEL_COLUMNS['page_number']: result.get('page_number', ''),
                    EXCEL_COLUMNS['importance']: '重要' if result.get('is_important', False) else '一般',
                    EXCEL_COLUMNS['score']: result['score'],
                    EXCEL_COLUMNS['max_score']: result['max_score'],
                    EXCEL_COLUMNS['score_rate']: result['score_rate'],
                    EXCEL_COLUMNS['evaluation']: result['evaluation'],
                    EXCEL_COLUMNS['strengths']: '; '.join(result.get('strengths', [])),
                    EXCEL_COLUMNS['weaknesses']: '; '.join(result.get('weaknesses', [])),
                    EXCEL_COLUMNS['suggestions']: '; '.join(result.get('suggestions', [])),
                    EXCEL_COLUMNS['relevant_files']: '; '.join(result.get('relevant_files', [])),
                    '使用模型': result.get('used_model', '未知')  # 添加使用的模型信息
                })
            
            # 准备增强版数据
            enhanced_data = []
            for result in self.scoring_results:
                # 检查是否有增强信息
                if hasattr(self, 'enhanced_results') and self.enhanced_results:
                    # 查找对应的增强结果
                    enhanced_result = next((er for er in self.enhanced_results if er['requirement_id'] == result['requirement_id']), None)
                    if enhanced_result:
                        enhanced_data.append({
                            '要求编号': result['requirement_id'],
                            '要求概括': result.get('requirement_summary', ''),
                            '要求类型': result.get('requirement_type', ''),
                            '得分': f"{result['score']}/{result['max_score']}",
                            '得分率(%)': f"{result.get('score_rate', 0):.2f}",
                            '要点清单': '; '.join(enhanced_result.get('key_points', [])),
                            '证据锚点计划': '; '.join(enhanced_result.get('evidence_plan', [])),
                            '缺失材料': '; '.join(enhanced_result.get('missing_materials', [])),
                            '风险提示': '; '.join(enhanced_result.get('risk_warnings', [])),
                            '标签': '; '.join(enhanced_result.get('tags', [])),
                            '重点领域': '; '.join(enhanced_result.get('writing_params', {}).get('focus_areas', [])),
                            '需要文档': '; '.join(enhanced_result.get('writing_params', {}).get('required_docs', [])),
                            '质量标准': '; '.join(enhanced_result.get('writing_params', {}).get('quality_standards', [])),
                            '合规性说明': enhanced_result.get('writing_params', {}).get('compliance_notes', ''),
                            '行动项': '; '.join(enhanced_result.get('writing_params', {}).get('action_items', [])),
                            '需人工确认': '是' if enhanced_result.get('human_verification_needed', False) else '否',
                            '确认原因': enhanced_result.get('verification_reason', ''),
                            '增强模型': enhanced_result.get('enhancement_model', '未知')
                        })
                    else:
                        # 没有增强信息的情况
                        enhanced_data.append({
                            '要求编号': result['requirement_id'],
                            '要求概括': result.get('requirement_summary', ''),
                            '要求类型': result.get('requirement_type', ''),
                            '得分': f"{result['score']}/{result['max_score']}",
                            '得分率(%)': f"{result.get('score_rate', 0):.2f}",
                            '要点清单': '未生成',
                            '证据锚点计划': '未生成',
                            '缺失材料': '未生成',
                            '风险提示': '未生成',
                            '标签': '未生成',
                            '重点领域': '未生成',
                            '需要文档': '未生成',
                            '质量标准': '未生成',
                            '合规性说明': '未生成',
                            '行动项': '未生成',
                            '需人工确认': '是',
                            '确认原因': 'LLM增强流程未执行',
                            '增强模型': '无'
                        })
                else:
                    # 增强流程未执行的情况
                    enhanced_data.append({
                        '要求编号': result['requirement_id'],
                        '要求概括': result.get('requirement_summary', ''),
                        '要求类型': result.get('requirement_type', ''),
                        '得分': f"{result['score']}/{result['max_score']}",
                        '得分率(%)': f"{result.get('score_rate', 0):.2f}",
                        '要点清单': '未生成',
                        '证据锚点计划': '未生成',
                        '缺失材料': '未生成',
                        '风险提示': '未生成',
                        '标签': '未生成',
                        '重点领域': '未生成',
                        '需要文档': '未生成',
                        '质量标准': '未生成',
                        '合规性说明': '未生成',
                        '行动项': '未生成',
                        '需人工确认': '是',
                        '确认原因': 'LLM增强流程未执行',
                        '增强模型': '无'
                    })
            
            # 创建DataFrame
            basic_df = pd.DataFrame(basic_data)
            enhanced_df = pd.DataFrame(enhanced_data)
            
            # 导出到Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 基础评分结果
                basic_df.to_excel(writer, sheet_name=EXCEL_SHEET_NAMES['scoring_results'], index=False)
                
                # 写作要点增强版
                enhanced_df.to_excel(writer, sheet_name='写作要点增强版', index=False)
                
                # 统计信息
                stats_data = []
                total_score = sum(r['score'] for r in self.scoring_results)
                total_max_score = sum(r['max_score'] for r in self.scoring_results)
                overall_rate = (total_score / total_max_score * 100) if total_max_score > 0 else 0
                
                stats_data.append(['总要求数', len(self.scoring_results)])
                stats_data.append(['总得分', total_score])
                stats_data.append(['总分', total_max_score])
                stats_data.append(['总体得分率(%)', f"{overall_rate:.2f}"])
                
                # 增强流程统计
                if hasattr(self, 'enhanced_results') and self.enhanced_results:
                    enhanced_count = len([r for r in self.enhanced_results if not r.get('human_verification_needed', True)])
                    stats_data.append(['成功增强数', enhanced_count])
                    stats_data.append(['需人工确认数', len(self.enhanced_results) - enhanced_count])
                else:
                    stats_data.append(['成功增强数', 0])
                    stats_data.append(['需人工确认数', 0])
                
                stats_df = pd.DataFrame(stats_data, columns=['指标', '数值'])
                stats_df.to_excel(writer, sheet_name=EXCEL_SHEET_NAMES['statistics'], index=False)
            
            print(f"Excel评分报告已导出到: {output_file}")
            print(f"包含工作表: {EXCEL_SHEET_NAMES['scoring_results']}, 写作要点增强版, {EXCEL_SHEET_NAMES['statistics']}")
            
        except Exception as e:
            print(f"导出Excel报告失败: {e}")


def main():
    """主函数"""
    # 检查项目目录是否存在
    if not os.path.exists(LIBRARY_ROOT):
        print(f"错误: 找不到项目目录 {LIBRARY_ROOT}")
        return
    
    # 查找要求文件，优先选择文本报告文件
    requirements_files = []
    
    # 先查找文本报告文件
    for file in os.listdir(PROJECT_ROOT):
        if file.startswith("03.招标文件_qualification_requirements_report") and file.endswith(".txt"):
            requirements_files.append(("文本报告", file))
    
    # 再查找JSON数据文件
    for file in os.listdir(PROJECT_ROOT):
        if file.startswith("03.招标文件_qualification_requirements_data") and file.endswith(".json"):
            requirements_files.append(("JSON数据", file))
    
    if not requirements_files:
        print("错误: 未找到要求文件，请先运行PDF提取器")
        return
    
    print("找到以下要求文件（推荐使用文本报告文件以获得完整要求）:")
    for i, (file_type, file) in enumerate(requirements_files, 1):
        print(f"{i}. [{file_type}] {file}")
    
    try:
        choice = int(input(f"\n请选择要分析的文件 (1-{len(requirements_files)}): ")) - 1
        if choice < 0 or choice >= len(requirements_files):
            print("选择无效")
            return
        
        selected_file_type, selected_file = requirements_files[choice]
        full_path = os.path.join(PROJECT_ROOT, selected_file)
        
        print(f"\n开始分析文件: [{selected_file_type}] {selected_file}")
        if selected_file_type == "JSON数据":
            print("注意: JSON数据文件可能不包含所有要求，建议使用文本报告文件")
        
    except (ValueError, KeyboardInterrupt):
        print("输入无效或用户取消")
        return
    
    # 创建智能评分器
    scorer = SimpleScorer()
    
    # 加载要求
    requirements = scorer.load_requirements(full_path)
    if not requirements:
        print("未加载到任何要求，程序退出")
        return
    
    print(f"成功加载 {len(requirements)} 个要求")
    
    # 进行评分
    scoring_results = scorer.score_all_requirements(requirements)
    
    # 增强评分结果
    enhanced_results = scorer.enhance_scoring_results_with_llm()
    
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
