#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用cache中的内容生成PDF - 修复版本
"""

import json
from pathlib import Path
import subprocess
import logging
import re

def load_cache_content():
    """加载cache中的内容"""
    cache_file = "build_test_current/cache/ea77395a1ae0fe44de82925f16558b630159268ac89a144eaf30f849f64bab8d.json"
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取cache文件失败: {e}")
        return None

def clean_cache_content(cache_content):
    """清理cache内容，移除Markdown标记"""
    # 移除Markdown标题标记
    content = re.sub(r'^#+\s*', '', cache_content, flags=re.MULTILINE)
    
    # 移除Markdown粗体标记
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    
    # 移除Markdown列表标记
    content = re.sub(r'^\s*[-*]\s*', '', content, flags=re.MULTILINE)
    
    # 移除多余的空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    return content

def create_content_from_cache(cache_content):
    """基于cache内容创建标书内容"""
    # 清理cache内容
    clean_content = clean_cache_content(cache_content)
    
    content = f"""# 智能化荔枝果园管理系统项目投标文件

## 投标函

**致：** 海南省农业农村厅

**项目名称：** 智能化荔枝果园管理系统项目  
**项目编号：** HHNNSHBB-2023100066  
**标包名称：** A包：智能化荔枝果园管理系统构建项目  
**标包编号：** HHNNSHBB-20233100066-A  

我方已仔细研究了上述项目的招标文件，愿意按照招标文件的要求承担上述项目的建设任务，并承诺：

1. 我方完全理解并接受招标文件的全部内容，愿意按照招标文件的要求提供所有服务
2. 我方承诺在投标有效期内不修改、不撤销投标文件
3. 我方承诺中标后按照招标文件的要求与采购人签订合同
4. 我方承诺按照招标文件的要求提供所有必要的技术支持和售后服务

**投标人（盖章）：** 中电科国海信通科技（海南）有限公司  
**法定代表人（签字）：** 张三  
**投标日期：** 2025年8月15日  

---

## 一、法定代表人身份证明

**投标人名称：** 中电科国海信通科技（海南）有限公司  
**法定代表人：** 张三  
**身份证号码：** 460100199001011234  
**职务：** 董事长兼总经理  
**联系电话：** 0898-12345678  
**联系地址：** 海南省海口市美兰区国兴大道123号  

**法定代表人身份证复印件（加盖公章）**

---

## 二、法定代表人授权委托书

**委托人：** 中电科国海信通科技（海南）有限公司  
**法定代表人：** 张三  
**受托人：** 李四  
**职务：** 技术总监  
**身份证号码：** 460100198502023456  

**授权范围：** 代表本公司参加"智能化荔枝果园管理系统项目"的投标活动，包括但不限于：投标文件的编制、递交、开标、评标、合同谈判、合同签署等一切与投标相关的事宜。

**授权期限：** 自本授权委托书签署之日起至本项目招标活动结束之日止。

**委托人（盖章）：** 中电科国海信通科技（海南）有限公司  
**法定代表人（签字）：** 张三  
**受托人（签字）：** 李四  
**日期：** 2025年8月15日  

---

## 三、供应商基本情况

### 公司简介
中电科国海信通科技（海南）有限公司成立于2020年，注册资本5000万元人民币，是一家专注于智慧农业、物联网技术、大数据分析的高新技术企业。公司拥有完整的研发、生产、销售和服务体系，在智慧农业领域具有丰富的项目经验和深厚的技术积累。

### 主营业务
- 智慧农业系统集成与解决方案
- 物联网设备研发、生产与销售
- 大数据分析与人工智能应用
- 软件开发与技术服务
- 系统集成与运维服务
- 农业技术推广与咨询服务

### 技术实力
- 拥有自主知识产权专利15项，软件著作权30项
- 获得高新技术企业认证、ISO9001质量管理体系认证
- 获得ISO14001环境管理体系认证、ISO45001职业健康安全管理体系认证
- 获得软件企业认定证书、安全开发服务资质证书
- 获得CMA计量认证、CNAS实验室认可证书

### 团队规模与结构
- **员工总数：** 120人
- **技术人员：** 85人（占比70.8%）
- **高级工程师：** 25人
- **项目经理：** 15人
- **博士学历：** 8人，硕士学历：32人

---

## 四、技术方案

{clean_content}

---

## 五、项目承诺

我方承诺所提供的所有材料真实、准确、完整，如有虚假，愿意承担相应的法律责任。我方承诺在投标有效期内不修改、不撤销投标文件，中标后严格按照招标文件要求与采购人签订合同并履行合同义务。

**投标人（盖章）：** 中电科国海信通科技（海南）有限公司  
**法定代表人（签字）：** 张三  
**日期：** 2025年8月15日  

---

*本投标文件共5页，第5页*
"""
    return content

def create_latex_content(markdown_content):
    """将Markdown内容转换为LaTeX格式"""
    # 处理标题
    lines = markdown_content.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            processed_lines.append('')
            continue
            
        # 处理一级标题
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            processed_lines.append(f'\\section{{{title}}}')
            processed_lines.append('')
            
        # 处理二级标题
        elif line.startswith('## '):
            title = line[3:].strip()
            processed_lines.append(f'\\subsection{{{title}}}')
            processed_lines.append('')
            
        # 处理三级标题
        elif line.startswith('### '):
            title = line[4:].strip()
            processed_lines.append(f'\\subsubsection{{{title}}}')
            processed_lines.append('')
            
        # 处理粗体文本
        elif '**' in line:
            # 替换粗体标记，处理嵌套情况
            parts = line.split('**')
            if len(parts) % 2 == 1:  # 奇数个部分，说明有完整的粗体标记
                result = ''
                for i, part in enumerate(parts):
                    if i % 2 == 0:  # 普通文本
                        result += part
                    else:  # 粗体文本
                        result += f'\\textbf{{{part}}}'
                processed_lines.append(result)
            else:
                # 处理不完整的粗体标记
                processed_lines.append(line)
            
        # 处理分隔线
        elif line == '---':
            processed_lines.append('\\hrule')
            processed_lines.append('')
            
        # 处理列表项
        elif line.startswith('- '):
            # 检查是否需要开始新的列表
            if not processed_lines or not processed_lines[-1].strip().startswith('\\begin{itemize}'):
                processed_lines.append('\\begin{itemize}')
            item_content = line[2:].strip()
            processed_lines.append(f'\\item {item_content}')
            
        # 处理空行和列表结束
        elif line == '':
            if processed_lines and processed_lines[-1].strip().startswith('\\item'):
                # 检查下一个非空行是否还是列表项
                next_non_empty = None
                for i, next_line in enumerate(lines[lines.index(line) + 1:], 1):
                    if next_line.strip():
                        next_non_empty = next_line.strip()
                        break
                if not next_non_empty or not next_non_empty.startswith('- '):
                    processed_lines.append('\\end{itemize}')
                    processed_lines.append('')
            else:
                processed_lines.append('')
                
        # 处理普通文本
        else:
            # 如果当前行是普通文本，且前一行是列表项，需要结束列表
            if processed_lines and processed_lines[-1].strip().startswith('\\item'):
                processed_lines.append('\\end{itemize}')
                processed_lines.append('')
            processed_lines.append(line)
    
    # 确保列表正确关闭
    if processed_lines and processed_lines[-1].strip().startswith('\\item'):
        processed_lines.append('\\end{itemize}')
        processed_lines.append('')
    
    return '\n'.join(processed_lines)

def create_tex_file(latex_content):
    """创建完整的LaTeX文件"""
    tex_template = r"""\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{fancyhdr}

% 页面设置
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}

% 页眉页脚设置
\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{智能化荔枝果园管理系统项目投标文件}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\setlength{\headheight}{15pt}

% 超链接设置
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    filecolor=black,
    urlcolor=black,
    citecolor=black
}

% 列表设置
\setlist[itemize]{leftmargin=2em}
\setlist[enumerate]{leftmargin=2em}

% 文档信息
\title{\textbf{智能化荔枝果园管理系统项目投标文件}}
\author{中电科国海信通科技（海南）有限公司}
\date{2025年8月15日}

\begin{document}

% 标题页（不显示页码）
\thispagestyle{empty}
\begin{center}
{\zihao{2}\heiti 智能化荔枝果园管理系统项目投标文件}\\[24pt]
{\zihao{4}\songti 项目编号：HHNNSHBB-2023100066}\\[8pt]
{\zihao{4}\songti 项目名称：智能化荔枝果园管理系统项目}\\[8pt]
{\zihao{4}\songti 标包名称：A包：智能化荔枝果园管理系统构建项目}\\[8pt]
{\zihao{4}\songti 标包编号：HHNNSHBB-20233100066-A}\\[24pt]
{\zihao{3}\heiti 供应商：中电科国海信通科技（海南）有限公司}\\[8pt]
{\zihao{5}\songti （单位盖章）}\\[28pt]
{\zihao{4}\songti 日期：2025年8月15日}
\end{center}
\clearpage

% 目录页（不显示页码）
\thispagestyle{empty}
\tableofcontents
\clearpage

% 正文从第1页开始编号
\pagenumbering{arabic}
\setcounter{page}{1}

{content}

\end{document}"""
    
    return tex_template.replace("{content}", latex_content)

def compile_pdf(tex_path, out_pdf):
    """编译LaTeX文件为PDF"""
    workdir = tex_path.parent
    
    try:
        print("使用xelatex编译...")
        # 第一次编译
        cmd1 = ["xelatex", "-interaction=nonstopmode", tex_path.name]
        result1 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        print("第一次xelatex编译完成")
        
        # 第二次编译（处理引用）
        result2 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        print("第二次xelatex编译完成")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists():
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            built_pdf.rename(out_pdf)
            print(f"PDF生成成功: {out_pdf}")
            return True
        else:
            print("PDF文件未生成")
            return False
            
    except FileNotFoundError:
        print("xelatex未找到，请安装TeX发行版")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"xelatex编译失败: {exc.stderr}")
        return False

def main():
    """主函数"""
    print("开始从cache生成标书PDF（修复版本）...")
    
    # 加载cache内容
    cache_content = load_cache_content()
    if not cache_content:
        print("无法加载cache内容，退出")
        return
    
    # 创建构建目录
    workdir = Path("build_cache_fixed")
    workdir.mkdir(exist_ok=True)
    
    # 生成内容
    print("生成标书内容...")
    markdown_content = create_content_from_cache(cache_content)
    
    # 转换为LaTeX
    print("转换为LaTeX格式...")
    latex_content = create_latex_content(markdown_content)
    
    # 创建完整的LaTeX文件
    print("创建LaTeX文件...")
    tex_content = create_tex_file(latex_content)
    
    # 保存文件
    tex_path = workdir / "main.tex"
    tex_path.write_text(tex_content, encoding='utf-8')
    
    # 保存Markdown文件用于查看
    md_path = workdir / "content.md"
    md_path.write_text(markdown_content, encoding='utf-8')
    
    # 编译PDF
    print("编译PDF...")
    out_pdf = Path("cache_bid_document_fixed.pdf")
    success = compile_pdf(tex_path, out_pdf)
    
    if success:
        print(f"✅ PDF生成完成！输出文件: {out_pdf}")
        print(f"📁 中间文件保存在: {workdir}")
    else:
        print("❌ PDF生成失败")

if __name__ == "__main__":
    main()
