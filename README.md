# 智能化标书生成系统


本项目提供一套基于大语言模型的自动化投标文件生成工具。系统能够从招标文件中抽取需求、在本地知识库中检索相关资料、生成正式文档并渲染为 PDF。以下文档对使用流程、配置方式和内部结构进行了事无巨细的说明。

## 1. 核心功能
- 📄 **需求抽取**：从招标 PDF 中识别商务和技术条款并生成 Markdown 清单。
- 🔍 **资料检索**：遍历知识库并为每条需求匹配最相关的参考文件。
- 📝 **内容生成**：调用通义千问模型生成初稿并按需求分类汇总。
- 🧱 **模板渲染**：将 Markdown 转换为 LaTeX，并借助可定制模板编译为 PDF。
- 📦 **缓存与重用**：请求结果会缓存到磁盘，重复运行时自动复用以节省费用。

## 2. 环境要求
- **Python**：`>=3.10`
- **依赖安装**：`pip install -r requirements.txt`
- **LaTeX 环境**：需预先安装 `xelatex`、`pdflatex` 或 `latexmk`（任一即可）。
- **通义千问 API Key**：由 `llm_client.py` 内置管理，无需额外配置环境变量。

建议在虚拟环境中运行：
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 请使用 .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. 准备数据
项目根目录下提供了 `inputs/` 文件夹作为默认素材存放位置。该目录初始为空，请将待处理的招标 PDF 和需求 Markdown 放置于此，并在运行命令时通过参数引用，如 `--tender inputs/tender.pdf` 或 `--requirements inputs/requirements.md`。

### 3.1 招标文件
- 支持 **PDF** 格式。
- 文件路径通过 `--tender` 参数传入，如 `--tender inputs/tender.pdf`。


### 3.2 知识库
- 目录内可包含 Markdown、Word、XML 等文本资料，系统会自动识别。
- 本仓库自带示例知识库 `litchi-smart-orchard-bid/`，其中按包划分子目录，可直接用于测试。
- 调用时通过 `--kb` 参数指定该目录。

## 4. 运行方式
### 4.1 完整流程
当只有原始招标 PDF 时，可运行一站式流程：
```bash
python full_pipeline.py \
  --tender inputs/tender.pdf \

  --kb litchi-smart-orchard-bid \
  --out bid.pdf
```
**参数说明：**
- `--tender`：招标 PDF 文件路径。
- `--kb`：知识库目录。
- `--out`：生成的 PDF 输出路径。
- `--workdir`：可选，存放中间文件的目录（默认 `build/`）。
- `--topk`：每条需求引用的参考文件数量，默认 `3`。
- `--skip-extract`：若已手动准备好需求清单，可跳过需求抽取步骤。
- `--requirements-file`：与 `--skip-extract` 配合使用，指定现有需求 Markdown 文件。

执行过程中会按以下步骤输出进度：
1. **提取招标需求**：逐页解析 PDF 并生成 `extracted_requirements.md`。
2. **解析需求**：将文本转成结构化对象。
3. **扫描知识库**：读取并索引资料文件。
4. **检索相关内容**：为每条需求挑选最相关的 `topk` 个文件。
5. **内容生成**：撰写大纲、生成正文并合并为 `merged.md`。
6. **转换为 LaTeX**：调用模型将 Markdown 转换成 LaTeX，渲染得到 `main.tex`。
7. **编译 PDF**：通过 LaTeX 工具链生成最终的投标书。

中间产物均保存在 `--workdir` 指定目录，便于调试和复用。

### 4.2 直接从需求清单构建 PDF
若已拥有需求 Markdown 文件，可跳过抽取过程并直接生成 PDF：
```bash
python build_pdf.py \

  --requirements inputs/requirements.md \

  --kb litchi-smart-orchard-bid \
  --out bid.pdf
```
常用参数：
- `--latex-template`：指定自定义 LaTeX 模板；缺省时自动从 `templates/` 目录选择最合适的模板。
- `--workdir`：工作目录，默认 `build/`。
- `--topk`：每条需求引用的参考文件数量，默认 `5`。
- `--config`：读取额外的 TOML 配置文件。

## 5. 配置与自定义
### 5.1 模型与构建参数
根目录的 `pyproject.toml` 提供默认配置：
- `model`：所用的大模型名称。
- `temperature`：生成温度。
- `topk`：检索的参考文件数量。

运行脚本时可通过 `--config` 指定其他 TOML 文件，以覆盖默认设置。

### 5.2 项目信息
`pyproject.toml` 中 `[tool.build_pdf.project]` 段可声明项目元数据（如项目编号、投标单位等）。这些字段会写入环境变量，在模板中以 `\PROJECT_NO{}` 等方式引用。示例：
```toml
[tool.build_pdf.project]
bid_title = "荔枝智慧果园管理系统投标书"
project_no = "2024-001"
bid_date = "2024-06-30"
```
若未在配置文件中提供，也可直接在运行前设置对应环境变量，如：
```bash
export PROJECT_NO=2024-001
export BID_DATE=2024-06-30
```

### 5.3 模板定制
- 所有 LaTeX 模板位于 `templates/` 目录。默认按优先级选择最规范的中文模板。
- 若需使用自定义模板，可在运行命令中通过 `--latex-template templates/custom.tex` 指定。

### 5.4 缓存与重试
- 所有模型调用结果保存在 `build/cache/` 目录，下次运行会自动复用。
- 若 API 调用失败，`llm_client.py` 会在模型列表间自动轮换并重试。

## 6. 目录结构
```
├─ docs/                     # 示例需求及说明文档
├─ inputs/                   # 招标文件与需求清单（用户自行放置）
├─ litchi-smart-orchard-bid/ # 示例知识库
├─ scripts/                  # 辅助脚本，如 PDF 文本抽取等
├─ src/
│  ├─ caching.py             # LLM 调用结果缓存
│  ├─ content_merge.py       # 生成内容并合并
│  ├─ kb_search.py           # 知识库扫描与检索
│  ├─ latex_renderer.py      # Markdown → LaTeX 转换
│  ├─ pdf_builder.py         # 从需求到 PDF 的主流程
│  └─ requirements_parser.py # 需求解析
├─ templates/                # LaTeX 模板
├─ full_pipeline.py          # 一站式端到端脚本
├─ build_pdf.py              # 直接从需求构建 PDF 的入口
└─ README.md                 # 项目说明
```

## 7. 常见问题
1. **API Key 无效或超额**：请确认 `llm_client.py` 中配置的密钥仍可使用并且配额充足。
2. **LaTeX 编译失败**：请确保系统已安装完整的 LaTeX 工具链，并在日志中查看具体错误；程序会在 `build/` 目录留下 `main.tex` 供调试。
3. **知识库未找到内容**：检查 `--kb` 路径是否正确，或知识库文件是否为空。
4. **中文乱码**：确保运行环境和 LaTeX 模板均为 UTF‑8 编码，必要时安装中文字体。

## 8. 开发与贡献
欢迎通过 Pull Request 提交改进，或在 Issue 中反馈问题。开发时建议：
```bash
pip install -e .[dev]
pytest
```

## 9. 许可证
本项目基于 [MIT License](LICENSE) 开源，可自由修改与分发。
