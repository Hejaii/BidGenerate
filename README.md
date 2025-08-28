# 智能化标书生成系统

本项目提供一套完整的命令行工具，帮助用户根据招标需求自动生成符合格式的投标文件。系统利用大语言模型和模板渲染，实现从需求解析、内容检索到 PDF 输出的全流程。

## 功能概述
- 📄 **需求解析**：读取招标文件并抽取关键条目。
- 🔍 **知识库检索**：在本地资料库中查找匹配内容。
- 📝 **内容生成**：由 LLM 生成和整合投标方案。
- 🧱 **模板渲染**：将生成的 Markdown 转换为 LaTeX 后编译为 PDF。

## 快速上手
```bash
# 一站式流程：提取招标需求并生成 PDF
python full_pipeline.py --tender path/to/tender.pdf --kb litchi-smart-orchard-bid --out bid.pdf

# 若已有需求清单，可直接构建 PDF
python build_pdf.py --requirements docs/test_requirements.md --kb litchi-smart-orchard-bid --out bid.pdf
```

更多命令与配置可查看源码及各脚本注释。

## 目录结构
- `src/`：核心功能模块。
- `scripts/`：辅助脚本工具。
- `templates/`：LaTeX 模板文件。
- `docs/`：示例需求及项目文档。

## 开发
欢迎贡献代码或提出改进意见。请直接提交 Pull Request。

## 许可证
本项目采用 MIT 许可证。
