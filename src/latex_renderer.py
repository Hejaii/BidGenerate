from __future__ import annotations

"""Rendering utilities: Markdown → LaTeX and template filling."""

from pathlib import Path
import os
import re

from llm_client import LLMClient as Client
from .caching import LLMCache, llm_rewrite


def markdown_to_latex(markdown: str, *, client: Client, cache: LLMCache, use_llm: bool = True) -> str:
    """Convert Markdown text to LaTeX."""
    if use_llm:
        system = """Convert the following Markdown into clean LaTeX code. 
        - Do NOT include \\documentclass, \\usepackage, \\begin{document}, or \\end{document}
        - Use proper LaTeX commands for formatting
        - Handle Chinese text properly with ctex
        - Use \\section{} for headers starting with #
        - Use \\subsection{} for headers starting with ##
        - Use \\textbf{} for bold text (text between **)
        - Use \\texttt{} for code/monospace text (text between `)
        - Use \\begin{itemize} and \\end{itemize} for lists
        - Use \\item for list items (lines starting with -)
        - Use \\% for percentage signs
        - Use \\textgreater{} for > and \\textless{} for <
        - Do NOT synthesize styles; keep plain Chinese text and paragraphs. Avoid colored links.
        - Ensure all special characters are properly escaped
        - IMPORTANT: Every \\begin{itemize} must have a corresponding \\end{itemize}
        - Return ONLY the LaTeX content, no other text"""
        user = f"Convert this Markdown to LaTeX:\n\n{markdown}"
        latex = llm_rewrite(client, system, user, cache)
        
        # 清理LLM返回的文本
        latex = latex.strip()
        if latex.startswith('```latex'):
            latex = latex[8:]
        if latex.startswith('```'):
            latex = latex[3:]
        if latex.endswith('```'):
            latex = latex[:-3]
        latex = latex.strip()
        
        # 如果LLM生成失败，使用备用转换
        if "\\documentclass" in latex or "\\begin{document}" in latex:
            # 直接清除文档结构，保留正文
            parts = []
            for line in latex.split('\n'):
                if ("\\documentclass" in line) or ("\\usepackage" in line) or ("\\begin{document}" in line) or ("\\end{document}" in line):
                    continue
                parts.append(line)
            latex = "\n".join(parts)
        
        # 修复itemize环境问题
        latex = _fix_itemize_environments(latex)
    else:
        latex = _simple_markdown_to_latex(markdown)
    
    return latex


def _fix_itemize_environments(latex: str) -> str:
    """修复LaTeX代码中itemize环境不完整的问题"""
    lines = latex.split('\n')
    fixed_lines = []
    itemize_stack = []
    
    for line in lines:
        line = line.strip()
        if not line:
            fixed_lines.append('')
            continue
            
        # 检查itemize环境
        if '\\begin{itemize}' in line:
            itemize_stack.append(True)
            fixed_lines.append(line)
        elif '\\end{itemize}' in line:
            if itemize_stack:
                itemize_stack.pop()
            fixed_lines.append(line)
        elif line.startswith('\\item'):
            if not itemize_stack:
                # 如果遇到item但没有itemize环境，先创建环境
                fixed_lines.append('\\begin{itemize}')
                itemize_stack.append(True)
            fixed_lines.append(line)
        elif line.startswith('\\section{') or line.startswith('\\subsection{') or line.startswith('\\subsubsection{'):
            # 在标题前关闭所有未关闭的itemize环境
            while itemize_stack:
                fixed_lines.append('\\end{itemize}')
                itemize_stack.pop()
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # 确保所有itemize环境都正确关闭
    while itemize_stack:
        fixed_lines.append('\\end{itemize}')
        itemize_stack.pop()
    
    return '\n'.join(fixed_lines)


def _simple_markdown_to_latex(markdown: str) -> str:
    """Simple Markdown to LaTeX conversion without LLM."""
    lines = markdown.split('\n')
    latex_lines = []
    itemize_stack = []  # 跟踪itemize环境的嵌套
    
    for line in lines:
        line = line.strip()
        if not line:
            latex_lines.append('')
            continue
            
        # 检查是否是标题行
        if line.startswith('# '):
            # 关闭所有未关闭的itemize环境
            while itemize_stack:
                latex_lines.append('\\end{itemize}')
                itemize_stack.pop()
            latex_lines.append(f"\\section{{{line[2:]}}}")
        elif line.startswith('## '):
            # 关闭所有未关闭的itemize环境
            while itemize_stack:
                latex_lines.append('\\end{itemize}')
                itemize_stack.pop()
            latex_lines.append(f"\\subsection{{{line[3:]}}}")
        elif line.startswith('### '):
            # 关闭所有未关闭的itemize环境
            while itemize_stack:
                latex_lines.append('\\end{itemize}')
                itemize_stack.pop()
            latex_lines.append(f"\\subsubsection{{{line[4:]}}}")
        elif line.startswith('- '):
            if not itemize_stack:
                latex_lines.append('\\begin{itemize}')
                itemize_stack.append(True)
            latex_lines.append(f"\\item {line[2:]}")
        elif line.startswith('**') and line.endswith('**'):
            content = line[2:-2]
            # 处理占位符
            content = content.replace('{{', '').replace('}}', '')
            latex_lines.append(f"\\textbf{{{content}}}")
        elif line.startswith('`') and line.endswith('`'):
            content = line[1:-1]
            latex_lines.append(f"\\texttt{{{content}}}")
        elif line == '---':
            latex_lines.append('\\vspace{0.5cm}')
            latex_lines.append('\\hrule')
            latex_lines.append('\\vspace{0.5cm}')
        else:
            # 处理特殊字符和占位符
            processed_line = line.replace('%', '\\%').replace('>', '\\textgreater{}').replace('<', '\\textless{}')
            processed_line = processed_line.replace('{{', '').replace('}}', '')
            # 处理特殊数学符号
            processed_line = processed_line.replace('≥', '$\\geq$').replace('≤', '$\\leq$')
            processed_line = processed_line.replace('>', '$>$').replace('<', '$<$')
            latex_lines.append(processed_line)
    
    # 确保所有itemize环境都正确关闭
    while itemize_stack:
        latex_lines.append('\\end{itemize}')
        itemize_stack.pop()
    
    return '\n'.join(latex_lines)


def render_main_tex(body: str, template_path: Path, output_path: Path) -> str:
    """Fill the LaTeX template with body content."""
    template = template_path.read_text(encoding="utf-8")
    
    # 确保body不包含文档类声明
    if "\\documentclass" in body:
        # 移除重复的文档类声明
        lines = body.split('\n')
        filtered_lines = []
        in_document = False
        for line in lines:
            if "\\documentclass" in line or "\\usepackage" in line or "\\begin{document}" in line:
                continue
            if "\\end{document}" in line:
                break
            filtered_lines.append(line)
        body = '\n'.join(filtered_lines)
    
    # 覆盖封面元信息（来自环境变量，避免在仓库中硬编码）
    env_to_macro = {
        "BID_TITLE": r"\\newcommand{\\BidTitle}{%s}",
        "BID_DOC_TYPE": r"\\newcommand{\\BidDocType}{%s}",
        "PROJECT_NO": r"\\newcommand{\\ProjectNo}{%s}",
        "PROJECT_NAME": r"\\newcommand{\\ProjectName}{%s}",
        "PACKAGE_NAME": r"\\newcommand{\\PackageName}{%s}",
        "PACKAGE_NO": r"\\newcommand{\\PackageNo}{%s}",
        "SUPPLIER_NAME": r"\\newcommand{\\SupplierName}{%s}",
        "BID_DATE": r"\\newcommand{\\BidDate}{%s}",
    }

    def replace_macro(tex_src: str, macro_cmd: str, value: str) -> str:
        # 将宏定义整行替换为新的值
        pattern = rf"^\\newcommand\{{{re.escape(macro_cmd)}\}}\{{.*?\}}\s*$"
        replacement = f"\\newcommand{{{macro_cmd}}}{{{value}}}"
        return re.sub(pattern, replacement, tex_src, flags=re.MULTILINE)

    tex = template
    for env, fmt in env_to_macro.items():
        val = os.getenv(env)
        if val:
            macro_name = re.search(r"\\\\newcommand\{(\\\\\w+)\}", fmt).group(1)
            tex = replace_macro(tex, macro_name, val)

    tex = tex.replace("%%CONTENT%%", body)
    output_path.write_text(tex, encoding="utf-8")
    return tex
