# 项目结构说明

## 目录组织原则

本项目采用功能模块化的目录结构，按照以下原则组织：

1. **核心文件**：项目的主要入口文件和配置文件
2. **源代码**：核心业务逻辑和算法实现
3. **脚本工具**：辅助脚本和工具函数
4. **文档资料**：项目文档和说明材料
5. **输出文件**：生成的结果文件和日志
6. **示例文件**：示例和演示文件
7. **测试代码**：单元测试和集成测试

## 详细目录说明

### 📁 根目录
```
├── main.py                    # 主程序入口点
├── build_pdf.py               # PDF构建主程序
├── llm_client.py              # LLM客户端配置
├── config.py                  # 全局配置文件
├── requirements.txt           # Python依赖包列表
├── pyproject.toml            # 项目配置文件
├── README.md                  # 项目主要说明文档
└── .gitignore                # Git忽略文件配置
```

### 📁 src/ - 源代码目录
```
src/
├── __init__.py               # Python包初始化文件
├── pdf_builder.py            # PDF构建核心逻辑
├── requirements_parser.py    # 需求解析器
├── kb_search.py              # 知识库搜索功能
├── content_merge.py          # 内容合并算法
├── latex_renderer.py         # LaTeX渲染器
├── caching.py                # 缓存管理
└── logging_utils.py          # 日志工具
```

**说明**：包含项目的核心业务逻辑，所有模块都经过精心设计，支持扩展和维护。

### 📁 scripts/ - 脚本工具目录
```
scripts/
├── pdf_extractor.py          # PDF内容提取工具
├── doc_loader.py             # 文档加载器
├── analysis_parser.py        # 分析解析器
├── chapter_extractor.py      # 章节提取器
├── file_search.py            # 文件搜索工具
├── response_writer.py        # 响应写入器
├── utils.py                  # 通用工具函数
├── test_extractor.py         # 测试提取器
├── simple_pdf_generator.py   # 简化PDF生成器
├── run_extractor.bat         # Windows批处理脚本
└── run_extractor.sh          # Linux/macOS shell脚本
```

**说明**：包含各种辅助工具和脚本，支持不同的使用场景和操作系统。

### 📁 templates/ - 模板文件目录
```
templates/
└── main.tex                  # LaTeX主模板文件
```

**说明**：包含文档生成的模板文件，支持自定义样式和格式。

### 📁 docs/ - 文档目录
```
docs/
├── README.md                 # 项目说明文档
├── simple_requirements.md    # 简化需求说明
├── required_documents.md     # 需求文档详细说明
├── test_requirements.md      # 测试需求说明
└── PROJECT_STRUCTURE.md      # 项目结构说明（本文件）
```

**说明**：包含项目的各种文档和说明材料，帮助用户理解和使用项目。

### 📁 litchi-smart-orchard-bid/ - 荔枝果园投标项目
```
litchi-smart-orchard-bid/
├── README.md                 # 投标项目说明
├── checklist.md              # 投标文件清单检查表
├── common/                   # 通用材料
│   ├── company_qualifications/  # 公司资质证书
│   ├── personnel/               # 人员配置材料
│   ├── performance/             # 业绩证明材料
│   └── pricing/                 # 报价材料
├── package_A/                # A包：技术方案
├── package_B/                # B包：测试方案
├── package_C/                # C包：服务方案
└── scripts/                  # 投标项目相关脚本
```

**说明**：这是一个完整的投标项目示例，展示了如何使用本项目生成专业的投标文件。

### 📁 outputs/ - 输出文件目录
```
outputs/
├── *.pdf                     # 生成的PDF文件
├── *.log                     # 日志文件
├── *.aux                     # LaTeX辅助文件
├── *.out                     # LaTeX输出文件
└── *.toc                     # LaTeX目录文件
```

**说明**：包含程序运行过程中生成的各种输出文件，便于查看和调试。

### 📁 examples/ - 示例文件目录
```
examples/
├── *.pdf                     # 示例PDF文件
└── *.zip                     # 示例压缩包
```

**说明**：包含各种示例文件，帮助用户理解项目的使用方法和输出效果。

### 📁 build/ - 构建目录
```
build/
├── cache/                    # 缓存文件目录
├── logs/                     # 构建日志目录
├── main.tex                  # 生成的LaTeX文件
├── merged.md                 # 合并后的内容文件
└── content.md                # 原始内容文件
```

**说明**：包含构建过程中的临时文件和中间结果，支持增量构建和调试。

### 📁 tests/ - 测试目录
```
tests/
├── __init__.py               # 测试包初始化文件
├── test_kb_search.py         # 知识库搜索测试
├── test_latex_renderer.py    # LaTeX渲染测试
└── test_requirements_parser.py # 需求解析测试
```

**说明**：包含完整的测试用例，确保代码质量和功能正确性。

### 📁 scoring_results/ - 评分结果目录
```
scoring_results/
├── detailed_scoring_results_*.json  # 详细评分结果
├── scoring_report_*.txt             # 评分报告
├── scoring_results_*.xlsx           # 评分结果表格
└── scoring_summary_*.json           # 评分摘要
```

**说明**：包含项目评分和评估的结果文件，支持数据分析和报告生成。

## 文件命名规范

### 代码文件
- **Python文件**：使用小写字母和下划线，如 `pdf_builder.py`
- **配置文件**：使用小写字母，如 `config.py`
- **测试文件**：以 `test_` 开头，如 `test_kb_search.py`

### 文档文件
- **Markdown文件**：使用小写字母和下划线，如 `project_structure.md`
- **配置文件**：使用小写字母和点号，如 `requirements.txt`

### 输出文件
- **PDF文件**：使用描述性名称，如 `bid_document.pdf`
- **日志文件**：包含时间戳，如 `build_20250819_160000.log`

## 依赖关系

### 核心依赖
- `main.py` → `src/` 模块
- `build_pdf.py` → `src/pdf_builder.py`
- `llm_client.py` → `config.py`

### 模块依赖
- `src/pdf_builder.py` → 其他所有src模块
- `src/content_merge.py` → `llm_client.py`
- `src/kb_search.py` → `llm_client.py`

### 外部依赖
- Python 3.8+
- DashScope API
- LaTeX发行版
- 各种Python包（见requirements.txt）

## 扩展指南

### 添加新功能
1. 在 `src/` 目录下创建新模块
2. 在 `tests/` 目录下添加测试用例
3. 更新 `docs/` 目录下的相关文档
4. 在 `scripts/` 目录下添加相应的工具脚本

### 修改现有功能
1. 修改 `src/` 目录下的相应模块
2. 更新相关的测试用例
3. 更新文档说明
4. 确保向后兼容性

### 添加新的输出格式
1. 在 `src/` 目录下创建新的渲染器
2. 在 `templates/` 目录下添加相应的模板
3. 更新配置文件和文档
4. 添加相应的测试用例

## 维护说明

### 定期清理
- 清理 `build/` 目录下的临时文件
- 清理 `outputs/` 目录下的旧文件
- 清理 `__pycache__/` 目录

### 版本管理
- 使用语义化版本号
- 记录重要的变更
- 维护更新日志
- 定期发布新版本

### 质量保证
- 运行完整的测试套件
- 检查代码覆盖率
- 进行代码审查
- 更新依赖包版本
