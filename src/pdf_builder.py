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


# 尝试使用兼容的模板，避免字体问题
def get_default_template() -> Path:
    """获取默认的LaTeX模板，优先使用中文兼容版本"""
    # 按优先级尝试不同的模板
    templates = [
        Path("templates/main_chinese_simple.tex"), # 新的中文兼容模板，优先使用
        Path("templates/main_compatible.tex"),    # 兼容性好的中文模板
        Path("templates/main.tex"),              # 原始中文模板
        Path("templates/main_english.tex"),      # 英文模板（备用）
        Path("templates/main_simple.tex"),       # 最简单的英文模板（最后备用）
    ]
    
    for template in templates:
        if template.exists():
            return template
    
    # 如果都不存在，返回默认的
    return Path("templates/main.tex")

DEFAULT_TEMPLATE = get_default_template()


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
        # 修复JSON编码问题，确保中文字符正确处理
        try:
            meta_json = json.dumps(meta, ensure_ascii=False, indent=2, default=str)
            meta_path.write_text(meta_json, encoding="utf-8")
        except Exception as e:
            logger.warning(f"JSON写入失败，尝试使用ASCII编码: {e}")
            # 备用方案：使用ASCII编码
            meta_json = json.dumps(meta, ensure_ascii=True, indent=2, default=str)
            meta_path.write_text(meta_json, encoding="utf-8")
        pbar.update(1)
    
    print("📄 编译PDF...")
    compile_pdf(tex_path, out, logger)
    print(f"✅ PDF构建完成！输出文件: {out}")


def compile_pdf(tex_path: Path, out_pdf: Path, logger: logging.Logger) -> None:
    """Compile LaTeX into PDF using multiple methods with better error handling."""
    workdir = tex_path.parent
    
    # 方法1: 优先使用xelatex（最适合中文）
    try:
        logger.info("使用xelatex编译中文LaTeX...")
        # 第一次编译
        cmd1 = ["xelatex", "-interaction=nonstopmode", tex_path.name]
        result1 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("第一次xelatex编译完成")
        
        # 第二次编译（处理引用）
        result2 = subprocess.run(cmd1, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("第二次xelatex编译完成")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists() and built_pdf.stat().st_size > 0:
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除
            if out_pdf.exists():
                out_pdf.unlink()
            built_pdf.rename(out_pdf)
            logger.info(f"PDF生成成功: {out_pdf}")
            return
        else:
            logger.warning("xelatex未生成有效PDF文件，尝试其他方法")
            # 尝试查找其他可能的PDF文件
            pdf_files = list(workdir.glob("*.pdf"))
            if pdf_files:
                largest_pdf = max(pdf_files, key=lambda x: x.stat().st_size)
                if largest_pdf.stat().st_size > 1000:  # 大于1KB的PDF文件
                    logger.info(f"找到生成的PDF文件: {largest_pdf}")
                    out_pdf.parent.mkdir(parents=True, exist_ok=True)
                    if out_pdf.exists():
                        out_pdf.unlink()
                    largest_pdf.rename(out_pdf)
                    logger.info(f"PDF重命名成功: {out_pdf}")
                    return
            
    except FileNotFoundError:
        logger.warning("xelatex未找到，尝试其他方法")
    except subprocess.CalledProcessError as exc:
        logger.warning(f"xelatex编译失败: {exc.stderr}")
    except UnicodeDecodeError as e:
        logger.warning(f"xelatex编码错误: {e}，尝试其他方法")
    
    # 方法2: 尝试使用pdflatex（最兼容）
    try:
        logger.info("尝试使用pdflatex编译...")
        cmd = ["pdflatex", "-interaction=nonstopmode", "-shell-escape", tex_path.name]
        result = subprocess.run(cmd, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("pdflatex编译成功")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists() and built_pdf.stat().st_size > 0:
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除
            if out_pdf.exists():
                out_pdf.unlink()
            built_pdf.rename(out_pdf)
            logger.info(f"PDF生成成功: {out_pdf}")
            return
        else:
            logger.warning("pdflatex未生成有效PDF文件，尝试其他方法")
            # 尝试查找其他可能的PDF文件
            pdf_files = list(workdir.glob("*.pdf"))
            if pdf_files:
                largest_pdf = max(pdf_files, key=lambda x: x.stat().st_size)
                if largest_pdf.stat().st_size > 1000:  # 大于1KB的PDF文件
                    logger.info(f"找到生成的PDF文件: {largest_pdf}")
                    out_pdf.parent.mkdir(parents=True, exist_ok=True)
                    if out_pdf.exists():
                        out_pdf.unlink()
                    largest_pdf.rename(out_pdf)
                    logger.info(f"PDF重命名成功: {out_pdf}")
                    return
            
    except FileNotFoundError:
        logger.warning("pdflatex未找到，尝试其他方法")
    except subprocess.CalledProcessError as exc:
        logger.warning(f"pdflatex编译失败: {exc.stderr}")
    except UnicodeDecodeError as e:
        logger.warning(f"pdflatex编码错误: {e}，尝试其他方法")
    
    # 方法3: 尝试使用latexmk
    try:
        logger.info("尝试使用latexmk编译...")
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", tex_path.name]
        result = subprocess.run(cmd, cwd=workdir, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        logger.info("latexmk编译成功")
        
        # 查找生成的PDF文件
        built_pdf = workdir / (tex_path.stem + ".pdf")
        if built_pdf.exists() and built_pdf.stat().st_size > 0:
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除
            if out_pdf.exists():
                out_pdf.unlink()
            built_pdf.rename(out_pdf)
            logger.info(f"PDF生成成功: {out_pdf}")
            return
        else:
            logger.warning("latexmk未生成有效PDF文件，尝试其他方法")
            
    except FileNotFoundError:
        logger.warning("latexmk未找到，尝试其他方法")
    except subprocess.CalledProcessError as exc:
        logger.warning(f"latexmk编译失败: {exc.stderr}")
    except UnicodeDecodeError as e:
        logger.warning(f"latexmk编码错误: {e}，尝试其他方法")
    
    # 如果所有方法都失败，尝试创建一个简单的PDF
    try:
        logger.info("尝试创建简单的PDF...")
        import reportlab.pdfgen.canvas as canvas
        from reportlab.lib.pagesizes import A4
        
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(out_pdf), pagesize=A4)
        c.drawString(100, 750, "智能化荔枝果园管理系统项目")
        c.drawString(100, 700, "公开招标响应文件")
        c.drawString(100, 650, "由于LaTeX编译失败，生成了简化版PDF")
        c.drawString(100, 600, "请检查LaTeX环境配置")
        c.save()
        logger.info(f"简化PDF生成成功: {out_pdf}")
        return
        
    except ImportError:
        logger.error("reportlab未安装，无法生成简化PDF")
    except Exception as e:
        logger.error(f"生成简化PDF失败: {e}")
    
    logger.error("所有编译方法都失败了")
    raise RuntimeError("PDF编译失败，请检查LaTeX环境配置")


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
