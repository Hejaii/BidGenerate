#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF内容提取工具
支持提取招标文件的文本内容，并调用通义千问API智能分析商务部分和技术部分
"""

import os
import sys
import re
import json
import time
from typing import Dict, List, Tuple

try:
    import PyPDF2
except ImportError:
    print("正在安装PyPDF2...")
    os.system("pip install PyPDF2")
    import PyPDF2

try:
    import pdfplumber
except ImportError:
    print("正在安装pdfplumber...")
    os.system("pip install pdfplumber")
    import pdfplumber

try:
    import requests
except ImportError:
    print("正在安装requests...")
    os.system("pip install requests")
    import requests


class QianwenAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 使用正确的通义千问API端点
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 验证API密钥格式
        print(f"正在验证API密钥: {'*'*6 if self.api_key else '未提供'}")
        if not self.api_key or not self.api_key.startswith('sk-'):
            raise RuntimeError("未正确配置DashScope API密钥，请设置环境变量DASHSCOPE_API_KEY")
        
        if len(self.api_key) < 30:
            print("警告: API密钥长度可能不正确")
        
        print("API密钥格式验证通过")
        print(f"API端点: {self.base_url}")
        
    def extract_all_requirements(self, page_content: str, page_number: int) -> List[Dict]:
        """使用通义千问API提取页面中的所有要求"""
        # 限制内容长度，避免超出API限制，减少处理时间
        if len(page_content) > 1500:  # 从3000减少到1500
            page_content = page_content[:1500] + "..."
            
        prompt = f"""你是"要求抽取器"。仅基于输入文本进行抽取，不得臆测或引入外部知识。目标是：穷尽性抽取【商务要求】与【技术要求】（以及无法归类但像要求的"其他要求"），并给出可追溯的证据与定位提示。

请严格按照以下JSON格式输出，不要包含任何其他文字：

# 输入
- DOC: 原始文本（可包含或不包含页码/分段/表格/附件）。
- SCOPE: 作用范围描述（如"全文""第 X–Y 页""第 3 章至第 5 章"）。若为空则默认"全文"。
- ID_HINT: 可选，文档标识（如项目名/文件名），仅用于 meta 标注。
- PAGE_MARKER: 可选，页面分隔模式（如 "===Page {{n}}===" 或 "第{{n}}页"），若不存在则自动忽略。

# 任务
1) 识别并抽取所有"具备约束力或指令性"的句段，归类为【商务要求】或【技术要求】；无法判定时放入【其他要求】并注明原因。
2) 保留关键细节：数字/比例/阈值/时限/金额/介质/格式/型号/标准编号/模型或算法名/证书与材料名/责任主体/动作动词（必须/不得/应等）。
3) 为每条要求输出：原文近引、定位提示、强制性等级判断（Must/Should/May/Forbidden）、主题标签与去重后的唯一键。

# 判定规则（命中任一则视为"要求"）
- 动词/模态词（中）：必须/应/应当/须/需要/不得/禁止/不可/应由/确保/提供/提交/签订/配合/支持/具备/满足/实现/建立/备案/报告/监控/审计/留存/封存/加盖/密封/回执/验收/交付/保修/质保/处罚/违约/扣款/赔偿/上限/下限/不收取/免费等。
- 动词/模态词（英）：shall/ must/ should/ may/ shall not/ must not/ is required to/ is prohibited from/ provide/ submit/ comply/ certify/ deliver/ acceptance/ warranty/ penalty 等。
- 结构提示：带序号的条款/表格字段/清单/"不接受/不组织/仅限/至少/不低于/≥/≤/%/±/天/工作日/小时/份/套/份数/版本"等硬约束。

# 重要排除规则（以下内容不要抽取）
- 纯评分流程说明，如"评委对其进行综合评议"、"评分步骤包括"等
- 纯描述性内容，如"本项目采用综合评分法进行评审"
- 评委操作说明，如"评委对其进行综合评议"

# 重要：以下内容应该被识别为要求
- 功能要求、性能要求、技术参数要求
- 系统功能描述、技术指标要求
- 带分数的功能项、技术项
- 具体的功能实现要求、技术实现要求
- 商务资格要求、投标要求、合规要求
- 投标人资格条件、投标文件要求

# 归类指引（通用，不依赖具体行业）
- 商务要求：资格/合规与证明材料；报价与计价；投标/递交/开标/评标流程与格式；有效期与保证金/履约保函/支付；交付周期/里程碑；验收与结算；保修/维护/SLA；保密/隐私/IP；变更/违约/处罚；费用与收费口径；联合体/分包/比例限制；政策优惠与认证（如小微、环保、节能等）。
- 技术要求：功能/性能/容量/并发/可用性/可靠性/兼容性/接口协议/数据格式；安全与访问控制/审计/加密/合规；部署/架构/环境/操作系统/中间件/数据库；标准规范与测试方法；文档/培训/交付件清单；可观测性/日志/监控；集成与互联；验收测试口径与度量。
- 其他要求：确认为要求但无法归入上面两类时使用，并给出"uncertain_reason"。

# 去重与合并
- 文义重复只保留信息最全的一条；相近条款合并但保留原始多处证据列表。
- 不猜测页码：若无法识别页码则 page 置为 null，并用 `loc_hint` 标出邻近标题/小节号或前后 10–30 字。

# 过程（模型内部执行，不在输出中呈现）
1) 结构化预处理：合并被换行/连字符断开的词；将表格行转成"字段：值"的句子；识别小节/标题/表格标题；抽取"页码/分段"标记（若有）。
2) 第一遍"要求检测"：按判定规则扫描 DOC，逐句标注候选，并记录证据位置。
3) 第二遍"归类与细化"：填充分类、modality（shall/must=Must；should=Should；may=May；shall not/must not=Forbidden）、tags、loc_hint。
4) 去重合并：同义/重复要求合并；证据位置累积到 evidence 列表（内部使用），输出里保留代表性一条。
5) 自适应检查：基于标题/关键词自动生成 `families_detected` 并对照候选，形成 `coverage_report`，标注可能缺漏的主题族。
6) 质量约束：仅输出 JSON；不可编造页码或标题；不可总结改写关键数字或标准编号；若文本不足以判断，坦诚置空并解释在 reason_uncertain。

# 约束
- 不输出除 JSON 以外的任何文字。
- 不做价值判断与建议；不引入外部知识。
- 当 SCOPE 限定时，仅在此范围内抽取；否则默认全文。
- 若输入存在多语言，按句分别判断并统一输出到同一 JSON。
- 分数识别必须准确，避免出现"每项3分，满分1.66"等不合理计算。

请分析以下招标文件第{page_number}页的内容：

页面内容：
{page_content}

请按照以下JSON格式输出，保持原有字段结构：

{{
  "requirements": [
    {{
      "category": "商务要求/技术要求",
      "requirement_text": "完整的要求内容",
      "score": 分数值（如果没有分数则写0）,
      "is_important": true/false（如果要求开头有▲符号则为true）,
      "requirement_summary": "不超过50字的概括"
    }}
  ]
}}

如果页面中没有商务或技术要求，请返回空数组。

重要：请严格按照JSON格式输出，不要包含任何其他文字、说明或解释。"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'disable'
        }
        
        # 使用LLMClient替代直接API调用
        from llm_client import LLMClient
        
        # 创建LLMClient实例，它会自动使用可用的模型
        llm_client = LLMClient()
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            # 使用LLMClient的chat方法
            content = llm_client.chat(messages, temperature=0.1, max_tokens=2000)  # 减少token数量，加快响应
            
            # 尝试解析JSON响应，处理可能的markdown代码块
            try:
                # 如果内容包含markdown代码块，提取其中的JSON
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_str = content[json_start:json_end].strip()
                        content = json_str
                elif '```' in content:
                    # 处理没有语言标识的代码块
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_str = content[json_start:json_end].strip()
                        content = json_str
                
                parsed = json.loads(content)
                
                # 处理不同的返回格式
                if isinstance(parsed, list):
                    # 如果直接返回列表
                    requirements = parsed
                elif isinstance(parsed, dict):
                    # 如果返回字典，提取requirements字段
                    requirements = parsed.get("requirements", [])
                else:
                    print(f"意外的返回格式: {type(parsed)}")
                    return []
                
                # 为每个要求添加页码信息
                for req in requirements:
                    req["page_number"] = page_number
                
                return requirements
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始内容: {content}")
                print("程序退出")
                sys.exit(1)
                
        except Exception as e:
            print(f"LLMClient调用失败: {e}")
            print("程序退出")
            sys.exit(1)
        
        print(f"使用LLMClient分析第{page_number}页内容...（请耐心等待，AI正在分析中）")


class PDFExtractor:
    def __init__(self, pdf_path: str, api_key: str = None):
        self.pdf_path = pdf_path
        self.text_content = ""
        self.pages_content = []
        self.qianwen_api = QianwenAPI(api_key) if api_key else None
        self.page_start_number = 1  # 当前缓存内容对应的起始绝对页码（1-based）

    def extract_with_pypdf2(self, start_page: int = None, end_page: int = None) -> str:
        """使用PyPDF2提取PDF文本，可选页码范围（1-based，含端点）"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                total_pages = len(pdf_reader.pages)
                s = max(1, start_page) if start_page else 1
                e = min(total_pages, end_page) if end_page else total_pages
                self.page_start_number = s
                for page_idx in range(s - 1, e):
                    page = pdf_reader.pages[page_idx]
                    page_text = page.extract_text() or ""
                    text += f"\n--- 第{page_idx + 1}页 ---\n"
                    text += page_text
                    self.pages_content.append(page_text)
                
                return text
        except Exception as e:
            print(f"PyPDF2提取失败: {e}")
            return ""

    def extract_with_pdfplumber(self, start_page: int = None, end_page: int = None) -> str:
        """使用pdfplumber提取PDF文本（通常效果更好），可选页码范围（1-based，含端点）"""
        try:
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                s = max(1, start_page) if start_page else 1
                e = min(total_pages, end_page) if end_page else total_pages
                self.page_start_number = s
                for page_idx in range(s - 1, e):
                    page = pdf.pages[page_idx]
                    page_text = page.extract_text() or ""
                    if page_text is not None:
                        text += f"\n--- 第{page_idx + 1}页 ---\n"
                        text += page_text
                        self.pages_content.append(page_text)
                
                return text
        except Exception as e:
            print(f"pdfplumber提取失败: {e}")
            return ""

    def extract_text(self, start_page: int = None, end_page: int = None) -> str:
        """提取PDF文本内容，可选页码范围（1-based，含端点）"""
        print(f"正在提取PDF文件: {self.pdf_path}")
        # 每次提取前重置缓存
        self.text_content = ""
        self.pages_content = []

        # 先尝试pdfplumber，通常效果更好
        self.text_content = self.extract_with_pdfplumber(start_page=start_page, end_page=end_page)
        
        # 如果pdfplumber失败，尝试PyPDF2
        if not self.text_content.strip():
            print("pdfplumber提取结果为空，尝试PyPDF2...")
            self.text_content = self.extract_with_pypdf2(start_page=start_page, end_page=end_page)
        
        if not self.text_content.strip():
            print("警告: 无法提取到文本内容，可能是扫描版PDF")
            return ""
        
        print(f"成功提取 {len(self.pages_content)} 页内容")
        return self.text_content

    def analyze_company_qualification_requirements(self, start_page: int = None, end_page: int = None) -> Dict[str, List[Dict]]:
        """直接分析PDF中的公司资质类要求"""
        print("开始分析PDF中的公司资质类要求...")
        
        # 直接提取PDF文本内容
        if start_page or end_page:
            self.extract_text(start_page=start_page, end_page=end_page)
        elif not self.pages_content:
            self.extract_text()

        results: Dict[str, List[Dict]] = {"business": [], "technical": []}

        if not self.pages_content:
            print("未获取到可分析的文本内容")
            return results

        if not self.qianwen_api:
            raise RuntimeError("未配置API密钥，无法进行分析。请通过DASHSCOPE_API_KEY提供")

        total_found = 0
        for page_index, page_text in enumerate(self.pages_content, start=1):
            abs_page_num = self.page_start_number + page_index - 1
            
            # 使用API直接提取该页面的所有要求
            requirements = self.qianwen_api.extract_all_requirements(page_text or "", abs_page_num)
            
            for req in requirements:
                category = req.get("category", "")
                if category == "商务要求":
                    bucket = "business"
                elif category == "技术要求":
                    bucket = "technical"
                else:
                    continue  # 跳过非资质要求
                
                results[bucket].append(req)
                total_found += 1
            
            # 在每次API请求后添加间隔，避免触发频率限制
            if page_index < len(self.pages_content):
                print(f"等待2秒后继续下一页分析...")
                time.sleep(2)

        print(f"公司资质类要求识别完成，共计 {total_found} 条（商务 {len(results['business'])}，技术 {len(results['technical'])}）")
        return results

    def generate_qualification_report(self, start_page: int = None, end_page: int = None) -> str:
        """基于PDF直接分析的公司资质类要求报告（只含商务/技术资质）。"""
        # 如果还没有分析过，先进行分析
        if not hasattr(self, '_cached_results') or not self._cached_results:
            self._cached_results = self.analyze_company_qualification_requirements(start_page=start_page, end_page=end_page)
        
        data = self._cached_results

        lines: List[str] = []
        lines.append("=== 公司资质类要求报告 ===\n")
        
        # 添加页码范围信息
        if start_page and end_page:
            if start_page == end_page:
                lines.append(f"分析范围: 第 {start_page} 页\n")
            else:
                lines.append(f"分析范围: 第 {start_page} 页到第 {end_page} 页\n")
        else:
            lines.append("分析范围: 全部页面\n")
            
        total = len(data.get("business", [])) + len(data.get("technical", []))
        lines.append(f"总计: {total} 条\n")

        lines.append(f"商务资质要求 ({len(data.get('business', []))} 条):")
        lines.append("-" * 80)
        for item in data.get("business", []):
            lines.append(f"页码: 第{item.get('page_number', '未知')}页")
            lines.append(f"概括: {item.get('requirement_summary', '')}")
            lines.append(f"分数: {item.get('score', 0)}分  重要性: {'重要' if item.get('is_important', False) else '一般'}")
            lines.append(f"原文: {item.get('requirement_text', '')[:200]}...")
            lines.append("-" * 40)

        lines.append("")
        lines.append(f"技术资质要求 ({len(data.get('technical', []))} 条):")
        lines.append("-" * 80)
        for item in data.get("technical", []):
            lines.append(f"页码: 第{item.get('page_number', '未知')}页")
            lines.append(f"概括: {item.get('requirement_summary', '')}")
            lines.append(f"分数: {item.get('score', 0)}分  重要性: {'重要' if item.get('is_important', False) else '一般'}")
            lines.append(f"原文: {item.get('requirement_text', '')[:200]}...")
            lines.append("-" * 40)

        return "\n".join(lines)


def main():
    """无交互入口：使用环境变量与命令行参数，禁止硬编码。"""
    import argparse
    parser = argparse.ArgumentParser(description="PDF公司资质类要求分析")
    parser.add_argument("--pdf", required=True, help="输入PDF文件路径")
    parser.add_argument("--out-prefix", default=None, help="输出前缀（默认与PDF同名）")
    parser.add_argument("--start", type=int, default=None, help="起始页(1-based)")
    parser.add_argument("--end", type=int, default=None, help="结束页(1-based)")
    args = parser.parse_args()

    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("未设置DASHSCOPE_API_KEY环境变量")

    pdf_file = args.pdf
    if not os.path.exists(pdf_file):
        raise FileNotFoundError(f"找不到PDF文件 {pdf_file}")

    extractor = PDFExtractor(pdf_file, api_key)
    results = extractor.analyze_company_qualification_requirements(start_page=args.start, end_page=args.end)
    report = extractor.generate_qualification_report(start_page=args.start, end_page=args.end)

    prefix = args.out_prefix or pdf_file.rsplit('.pdf', 1)[0]
    page_suffix = ""
    if args.start and args.end:
        if args.start == args.end:
            page_suffix = f"_page_{args.start}"
        else:
            page_suffix = f"_pages_{args.start}-{args.end}"

    report_path = f"{prefix}_qualification_requirements_report{page_suffix}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    json_path = f"{prefix}_qualification_requirements_data{page_suffix}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"已输出: {report_path}\n已输出: {json_path}")


if __name__ == "__main__":
    main()
