from __future__ import annotations

"""Orchestrate end-to-end build from requirements to PDF."""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
import os
from datetime import datetime
from .latex_env import ensure_latex_env
try:
    import tomllib
except ImportError:
    import toml as tomllib
try:  # pragma: no cover - fallback when tqdm is not installed
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover
    from contextlib import contextmanager

    @contextmanager
    def tqdm(*args, **kwargs):
        class Dummy:
            def update(self, *a, **k):
                pass

        yield Dummy()

from llm_client import LLMClient as Client
from .logging_utils import get_logger
from .caching import LLMCache
from .requirements_parser import parse_requirements
from .kb_search import scan_kb, rank_files
from .content_merge import merge_contents
from .latex_renderer import markdown_to_latex, render_main_tex


# 尝试使用兼容的模板，避免字体问题
def get_default_template() -> Path:
    """获取默认的LaTeX模板，优先使用规范版模板"""
    # 按优先级尝试不同的模板，首选 main.tex 以确保编号和目录样式规范
    templates = [
        Path("templates/main.tex"),              # 原始规范模板，包含完整编号/目录样式
        Path("templates/main_chinese_simple.tex"), # 中文兼容模板
        Path("templates/main_compatible.tex"),    # 兼容性好的中文模板
        Path("templates/main_english.tex"),      # 英文模板（备用）
        Path("templates/main_simple.tex"),       # 最简单的英文模板（最后备用）
    ]
    
    for template in templates:
        if template.exists():
            return template
    
    # 如果都不存在，返回默认的
    return Path("templates/main.tex")

DEFAULT_TEMPLATE = get_default_template()


def load_config(path: Optional[Path] = None) -> Dict:
    """Load build configuration from a TOML file.

    If ``path`` is ``None`` the function attempts to read ``pyproject.toml``
    in the current working directory. This allows callers (or CLI users) to
    supply an explicit configuration file without relying on project-level
    defaults.
    """
    path = path or Path("pyproject.toml")
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return data.get("tool", {}).get("build_pdf", {})
    return {}


def format_bid_date(value: str) -> str:
    """将多种输入格式的日期标准化为 ``YYYY年MM月DD日`` 或 ``YYYY年MM月``。

    标书中有时仅给出年和月，此时输出 ``YYYY年MM月``；若提供具体日期则
    统一格式为 ``YYYY年MM月DD日``。
    """
    formats = {
        "%Y-%m-%d": "%Y年%m月%d日",
        "%Y/%m/%d": "%Y年%m月%d日",
        "%Y年%m月%d日": "%Y年%m月%d日",
        "%Y年%m月%d": "%Y年%m月%d日",
        "%Y年%m月": "%Y年%m月",
    }
    for fmt, out_fmt in formats.items():
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime(out_fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid bid_date format: {value}")


def apply_project_config(project: Dict[str, str]) -> None:
    """根据配置设置项目相关环境变量，并校验必填字段"""
    if not project:
        return

    mapping = {
        "bid_title": "BID_TITLE",
        "bid_doc_type": "BID_DOC_TYPE",
        "project_no": "PROJECT_NO",
        "project_name": "PROJECT_NAME",
        "package_name": "PACKAGE_NAME",
        "package_no": "PACKAGE_NO",
        "supplier_name": "SUPPLIER_NAME",
        "bid_date": "BID_DATE",
    }

    required = ["project_no", "bid_date"]
    missing = [k for k in required if not project.get(k)]
    if missing:
        raise ValueError(f"Missing project field(s): {', '.join(missing)}")

    for key, env in mapping.items():
        val = project.get(key)
        if val:
            if key == "bid_date":
                val = format_bid_date(val)
            os.environ[env] = val


def ensure_latex_env(logger: logging.Logger) -> None:
    """Ensure XeLaTeX and Chinese fonts are available.

    Some environments lack the LaTeX toolchain or CJK fonts which causes
    errors like ``mktexpk: don't know how to create bitmap font for
    unihei6c``.  This helper tries to install a minimal set of packages at
    runtime so that PDF compilation has a better chance of succeeding.  The
    installation is best-effort and failures are only logged.
    """

    try:
        subprocess.run(["xelatex", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return  # xelatex already present
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.info("xelatex not found; attempting to install TeX Live and fonts...")

    try:
        subprocess.run(["apt-get", "update"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(
            [
                "apt-get",
                "install",
                "-y",
                "texlive-xetex",
                "texlive-latex-recommended",
                "texlive-fonts-recommended",
                "texlive-lang-chinese",
                "fonts-noto-cjk",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(["fc-cache", "-fv"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("LaTeX environment with Chinese fonts installed")
    except Exception as exc:  # pragma: no cover - install is best effort
        logger.warning("Failed to install LaTeX dependencies: %s", exc)


def build_pdf(
    requirements: Path,
    kb: Path,
    out: Path,
    *,
    latex_template: Path | None = None,
    workdir: Path | None = None,
    topk: int = 5,
    use_llm: bool = True,
    config_path: Path | None = None,
) -> None:
    """Main pipeline to build PDF."""
    workdir = workdir or Path("build")
    workdir.mkdir(parents=True, exist_ok=True)
    logger = get_logger("build_pdf", workdir)
    cache = LLMCache(workdir / "cache")
    config = load_config(config_path)
    # 将配置中的项目元信息注入到环境变量中
    apply_project_config(config.get("project", {}))
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
    
    # 步骤4: 生成内容
    print("📝 步骤4/5: 生成内容...")
    with tqdm(total=1, desc="生成内容", unit="文档") as pbar:
        req_dir = workdir / "requirements"
        merged_md, meta = merge_contents(
            requirements_items,
            ranked,
            client=client,
            cache=cache,
            use_llm=True,
            output_dir=req_dir,
        )
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
    """Compile LaTeX into PDF using XeLaTeX after ensuring environment."""
    workdir = tex_path.parent
    ensure_latex_env(logger)
    cmd = ["xelatex", "-interaction=nonstopmode", tex_path.name]

    try:
        subprocess.run(cmd, cwd=workdir, check=True)
        subprocess.run(cmd, cwd=workdir, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        logger.warning(f"xelatex failed: {exc}")
        cmd = ["pdflatex", "-interaction=nonstopmode", tex_path.name]
        try:
            subprocess.run(cmd, cwd=workdir, check=True)
            subprocess.run(cmd, cwd=workdir, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc2:
            logger.error(f"pdflatex failed: {exc2}")
            raise RuntimeError("PDF编译失败，请检查LaTeX环境配置") from exc2
    built_pdf = workdir / (tex_path.stem + ".pdf")
    if not built_pdf.exists():
        raise RuntimeError("未生成PDF文件")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if out_pdf.exists():
        out_pdf.unlink()
    built_pdf.rename(out_pdf)
    logger.info(f"PDF生成成功: {out_pdf}")

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
    parser.add_argument("--config", type=Path, default=None, help="Path to TOML config")

    args = parser.parse_args()
    use_llm = args.use_llm.lower() == "true"
    build_pdf(
        args.requirements,
        args.kb,
        args.out,
        latex_template=args.latex_template,
        workdir=args.workdir,
        topk=args.topk,
        use_llm=use_llm,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()
