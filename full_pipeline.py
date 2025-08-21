#!/usr/bin/env python3
"""End-to-end pipeline: extract requirements then build PDF."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
import logging

import pdfplumber

from scripts.pdf_extractor import QianwenAPI
from llm_client import LLMClient as Client
from src.caching import LLMCache
from src.requirements_parser import parse_requirements
from src.kb_search import scan_kb, rank_files
from src.content_merge import merge_contents
from src.latex_renderer import markdown_to_latex, render_main_tex
from src.pdf_builder import compile_pdf, load_config, DEFAULT_TEMPLATE


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.step_times = {}
        
    def start_step(self, step_name: str, description: str = ""):
        """开始一个新步骤"""
        self.current_step += 1
        step_start = time.time()
        
        print(f"\n{'='*60}")
        print(f"🚀 步骤 {self.current_step}/{self.total_steps}: {step_name}")
        if description:
            print(f"📋 {description}")
        print(f"⏰ 开始时间: {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        self.step_times[step_name] = {"start": step_start}
        
    def end_step(self, step_name: str, result_info: str = ""):
        """结束当前步骤"""
        if step_name in self.step_times:
            step_time = time.time() - self.step_times[step_name]["start"]
            self.step_times[step_name]["end"] = time.time()
            self.step_times[step_name]["duration"] = step_time
            
            print(f"\n✅ 步骤 {self.current_step}/{self.total_steps} 完成: {step_name}")
            if result_info:
                print(f"📊 {result_info}")
            print(f"⏱️  耗时: {step_time:.2f}秒")
            
            # 显示总体进度
            elapsed_total = time.time() - self.start_time
            estimated_total = (elapsed_total / self.current_step) * self.total_steps
            remaining = estimated_total - elapsed_total
            
            print(f"📈 总体进度: {self.current_step}/{self.total_steps} ({self.current_step/self.total_steps*100:.1f}%)")
            print(f"⏳ 预计剩余时间: {remaining/60:.1f}分钟")
            
    def show_final_summary(self):
        """显示最终总结"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print("🎉 所有步骤完成！")
        print(f"{'='*60}")
        
        print(f"⏱️  总耗时: {total_time/60:.2f}分钟")
        print("\n📊 各步骤耗时详情:")
        
        for step_name, timing in self.step_times.items():
            duration = timing.get("duration", 0)
            print(f"  • {step_name}: {duration:.2f}秒")
        
        print(f"\n🚀 平均每步耗时: {total_time/self.total_steps:.2f}秒")


def extract_requirements(pdf_path: Path, api: QianwenAPI, out_path: Path, progress: ProgressTracker) -> Path:
    """Extract requirement texts from a tender PDF into a markdown file."""
    lines = []
    
    # 获取PDF总页数
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pdf.pages)
        progress.start_step("提取招标需求", f"从PDF中提取商务和技术要求，共{total_pages}页")
        
        for page_number, page in enumerate(pdf.pages, 1):
            print(f"  📄 正在处理第 {page_number}/{total_pages} 页...")
            text = page.extract_text() or ""
            
            # 显示页面处理进度
            page_progress = page_number / total_pages * 100
            print(f"     📊 页面进度: {page_progress:.1f}%")
            
            for req in api.extract_all_requirements(text, page_number):
                lines.append(f"- {req['requirement_text']}")
            
            # 显示当前提取的要求数量
            print(f"     ✅ 第{page_number}页提取了 {len([l for l in lines if l.startswith('-')])} 个要求")
    
    out_path.write_text("\n".join(lines), encoding="utf-8")
    
    progress.end_step("提取招标需求", f"成功提取 {len(lines)} 个要求，保存到 {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract requirements then build bid PDF")
    parser.add_argument("--tender", type=Path, required=True, help="招标PDF文件")
    parser.add_argument("--kb", type=Path, required=True, help="知识库目录")
    parser.add_argument("--out", type=Path, required=True, help="输出PDF路径")
    parser.add_argument("--workdir", type=Path, default=Path("build"), help="工作目录")
    parser.add_argument("--topk", type=int, default=3, help="每条需求选取的参考数量")
    args = parser.parse_args()

    # 初始化进度跟踪器
    total_steps = 7  # 总步骤数
    progress = ProgressTracker(total_steps)
    
    print("🚀 荔枝智慧果园投标文件生成器启动")
    print(f"📁 招标文件: {args.tender}")
    print(f"📚 知识库: {args.kb}")
    print(f"📄 输出文件: {args.out}")
    print(f"⚙️  工作目录: {args.workdir}")
    print(f"🎯 每条需求参考数量: {args.topk}")

    workdir = args.workdir
    workdir.mkdir(parents=True, exist_ok=True)
    cache = LLMCache(workdir / "cache")
    config = load_config()
    temperature = config.get("temperature")
    client = Client(models=None, temperature=temperature if temperature is not None else 0.2)
    api = QianwenAPI(os.getenv("DASHSCOPE_API_KEY", ""))

    # 步骤1: 提取需求
    req_md = extract_requirements(args.tender, api, workdir / "extracted_requirements.md", progress)

    # 步骤2: 解析需求
    progress.start_step("解析需求", "将提取的文本转换为结构化需求对象")
    requirements = parse_requirements(req_md, client=client, cache=cache, use_llm=True)
    progress.end_step("解析需求", f"成功解析 {len(requirements)} 个需求")

    # 步骤3: 扫描知识库
    progress.start_step("扫描知识库", f"扫描知识库目录: {args.kb}")
    files = scan_kb(args.kb)
    progress.end_step("扫描知识库", f"发现 {len(files)} 个知识库文件")

    # 步骤4: 检索相关内容
    progress.start_step("检索相关内容", f"为每个需求检索最相关的 {args.topk} 个参考文件")
    ranked = {}
    for i, item in enumerate(requirements, 1):
        print(f"  🔍 正在检索需求 {i}/{len(requirements)}: {item.id}")
        ranked[item.id] = rank_files(item, files, topk=args.topk, client=client, cache=cache, use_llm=True)
    
    total_ranked = sum(len(refs) for refs in ranked.values())
    progress.end_step("检索相关内容", f"为 {len(requirements)} 个需求检索到 {total_ranked} 个相关文件")

    # 步骤5: 生成并合并内容
    progress.start_step("生成并合并内容", "使用LLM生成投标文件内容并合并")
    merged_md, meta = merge_contents(requirements, ranked, client=client, cache=cache, use_llm=True)
    md_path = workdir / "merged.md"
    md_path.write_text(merged_md, encoding="utf-8")
    
    content_length = len(merged_md)
    progress.end_step("生成并合并内容", f"生成了 {content_length} 字符的内容，保存到 {md_path}")

    # 步骤6: 转换为LaTeX
    progress.start_step("转换为LaTeX", "将Markdown内容转换为LaTeX格式")
    latex_body = markdown_to_latex(merged_md, client=client, cache=cache, use_llm=True)
    tex_path = workdir / "main.tex"
    render_main_tex(latex_body, DEFAULT_TEMPLATE, tex_path)
    meta_path = workdir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    
    latex_length = len(latex_body)
    progress.end_step("转换为LaTeX", f"生成了 {latex_length} 字符的LaTeX内容，保存到 {tex_path}")

    # 步骤7: 编译PDF
    progress.start_step("编译PDF", f"使用LaTeX编译生成最终PDF文件")
    logger = logging.getLogger("full_pipeline")
    compile_pdf(tex_path, args.out, logger)
    progress.end_step("编译PDF", f"PDF生成完成: {args.out}")

    # 显示最终总结
    progress.show_final_summary()
    
    print(f"\n🎯 最终结果: {args.out}")
    print(f"📊 文件大小: {args.out.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
