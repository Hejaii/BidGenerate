from __future__ import annotations

"""Orchestrate end-to-end build from requirements to PDF."""

import json
import subprocess
from pathlib import Path
from typing import Dict, List
import logging
try:
    import tomllib
except ImportError:
    import toml as tomllib
from tqdm import tqdm

from llm_client import LLMClient as Client
from .logging_utils import get_logger
from .caching import LLMCache
from .requirements_parser import parse_requirements
from .kb_search import scan_kb, rank_files
from .content_merge import merge_contents
from .latex_renderer import markdown_to_latex, render_main_tex


DEFAULT_TEMPLATE = Path("templates/main.tex")


def load_config() -> Dict:
    path = Path("pyproject.toml")
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return data.get("tool", {}).get("build_pdf", {})
    return {}


def build_pdf(requirements: Path, kb: Path, out: Path, *, latex_template: Path | None = None, workdir: Path | None = None, topk: int = 5, use_llm: bool = True) -> None:
    """Main pipeline to build PDF."""
    workdir = workdir or Path("build")
    workdir.mkdir(parents=True, exist_ok=True)
    logger = get_logger("build_pdf", workdir)
    cache = LLMCache(workdir / "cache")
    config = load_config()
    temperature = config.get("temperature")
    # 强制使用百炼模型客户端，禁止本地启发式
    client = Client(models=None, temperature=temperature if temperature is not None else 0.2)
    import inspect
    logger.debug("LLMClient.chat signature: %s", inspect.signature(client.chat))
    logger.debug("LLMClient.chat_json signature: %s", inspect.signature(client.chat_json))

    print("🚀 开始构建PDF文档...")
    
    # 步骤1: 解析需求
    print("📋 步骤1/5: 解析需求清单...")
    with tqdm(total=1, desc="解析需求", unit="文件") as pbar:
        requirements_items = parse_requirements(requirements, client=client, cache=cache, use_llm=True)
        pbar.update(1)
    
    # 步骤2: 扫描知识库
    print("🔍 步骤2/5: 扫描知识库...")
    files = scan_kb(kb)
    print(f"   发现 {len(files)} 个文件")
    
    # 步骤3: 检索相关内容
    print("🎯 步骤3/5: 检索相关内容...")
    ranked: Dict[str, List] = {}
    with tqdm(total=len(requirements_items), desc="检索内容", unit="需求") as pbar:
        for item in requirements_items:
            ranked[item.id] = rank_files(item, files, topk=topk, client=client, cache=cache, use_llm=True)
            pbar.update(1)
    
    # 步骤4: 合并内容
    print("📝 步骤4/5: 合并内容...")
    with tqdm(total=1, desc="合并内容", unit="文档") as pbar:
        merged_md, meta = merge_contents(requirements_items, ranked, client=client, cache=cache, use_llm=True)
        merged_md_path = workdir / "merged.md"
        merged_md_path.write_text(merged_md, encoding="utf-8")
        pbar.update(1)
    
    # 步骤5: 生成LaTeX和PDF
    print("🔄 步骤5/5: 生成LaTeX和PDF...")
    with tqdm(total=2, desc="生成PDF", unit="步骤") as pbar:
        latex_body = markdown_to_latex(merged_md, client=client, cache=cache, use_llm=use_llm)
        template = latex_template or DEFAULT_TEMPLATE
        tex_path = workdir / "main.tex"
        render_main_tex(latex_body, template, tex_path)
        pbar.update(1)
        
        meta_path = workdir / "meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        pbar.update(1)
    
    print("📄 编译PDF...")
    compile_pdf(tex_path, out, logger)
    print(f"✅ PDF构建完成！输出文件: {out}")


def compile_pdf(tex_path: Path, out_pdf: Path, logger: logging.Logger) -> None:
    """Compile LaTeX into PDF using latexmk or xelatex."""
    workdir = tex_path.parent
    
    # 首先尝试使用latexmk
    try:
        logger.info("尝试使用latexmk编译...")
        cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-pdf", tex_path.name]
        result = subprocess.run(cmd, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("latexmk编译成功")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists():
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            built_pdf.rename(out_pdf)
            logger.info(f"PDF生成成功: {out_pdf}")
            return
        else:
            logger.warning("latexmk未生成PDF文件，尝试直接使用xelatex")
            
    except FileNotFoundError:
        logger.warning("latexmk未找到，尝试使用xelatex")
    except subprocess.CalledProcessError as exc:
        logger.warning(f"latexmk编译失败: {exc.stderr}")
    except UnicodeDecodeError as e:
        logger.warning(f"latexmk编码错误: {e}，尝试使用xelatex")
    
    # 如果latexmk失败，尝试直接使用xelatex
    try:
        logger.info("使用xelatex直接编译...")
        # 第一次编译
        cmd1 = ["xelatex", "-interaction=nonstopmode", tex_path.name]
        result1 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("第一次xelatex编译完成")
        
        # 第二次编译（处理引用）
        result2 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("第二次xelatex编译完成")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists():
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            built_pdf.rename(out_pdf)
            logger.info(f"PDF生成成功: {out_pdf}")
            return
        else:
            # 尝试查找.xdv文件并转换
            xdv_file = workdir / (tex_path.stem + ".xdv")
            if xdv_file.exists():
                logger.info("找到.xdv文件，尝试转换为PDF...")
                cmd_convert = ["xdvipdfmx", xdv_file.name, "-o", out_pdf.name]
                subprocess.run(cmd_convert, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
                logger.info(f"PDF转换成功: {out_pdf}")
                return
                
    except FileNotFoundError:
        logger.error("xelatex未找到；请安装TeX发行版")
    except subprocess.CalledProcessError as exc:
        logger.error(f"xelatex编译失败: {exc.stderr}")
    except UnicodeDecodeError as e:
        logger.error(f"xelatex编码错误: {e}")
    
    logger.error("所有编译方法都失败了")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build PDF from requirements and knowledge base")
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--kb", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--latex-template", type=Path, default=None)
    parser.add_argument("--workdir", type=Path, default=Path("build"))
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--use-llm", type=str, default="true")

    args = parser.parse_args()
    use_llm = args.use_llm.lower() == "true"
    build_pdf(args.requirements, args.kb, args.out, latex_template=args.latex_template, workdir=args.workdir, topk=args.topk, use_llm=use_llm)


if __name__ == "__main__":
    main()
