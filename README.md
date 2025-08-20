# 智能化标书生成系统

## 项目概述

本项目是一个面向各类招投标场景的智能化标书生成系统，能够根据招标文件自动解析需求、检索资料并生成规范的投标响应文档。
系统以大语言模型（LLM）为核心，结合知识库检索与 LaTeX 排版，实现从需求提取到 PDF 输出的完整流程。
## 项目特色

-  **智能驱动**：基于LLM（大语言模型）的智能内容生成
-  **数据驱动**：大数据分析和机器学习算法支持
-  **技术先进**：采用最新的物联网和AI技术栈
-  **文档完整**：自动生成符合招标要求的投标文件
-  **精准定位**：面向投标文档的专业解决方案

## 项目结构

```
├── 📁 核心文件
│   ├── main.py                    # 主程序入口
│   ├── build_pdf.py               # PDF构建主程序
│   ├── llm_client.py              # LLM客户端
│   ├── config.py                  # 配置文件
│   └── requirements.txt           # Python依赖
│
├── 📁 src/                        # 源代码目录
│   ├── pdf_builder.py             # PDF构建核心逻辑
│   ├── requirements_parser.py     # 需求解析器
│   ├── kb_search.py               # 知识库搜索
│   ├── content_merge.py           # 内容合并
│   ├── latex_renderer.py          # LaTeX渲染器
│   ├── caching.py                 # 缓存管理
│   └── logging_utils.py           # 日志工具
│
├── 📁 scripts/                    # 脚本工具目录
│   ├── pdf_extractor.py           # PDF内容提取
│   ├── doc_loader.py              # 文档加载器
│   ├── analysis_parser.py         # 分析解析器
│   ├── chapter_extractor.py       # 章节提取器
│   ├── file_search.py             # 文件搜索
│   ├── response_writer.py         # 响应写入器
│   ├── utils.py                   # 工具函数
│   ├── test_extractor.py          # 测试提取器
│   └── simple_pdf_generator.py    # 简化PDF生成器
│
├── 📁 templates/                   # 模板文件
│   └── main.tex                   # LaTeX主模板
│
├── 📁 docs/                        # 文档目录
│   ├── README.md                   # 项目说明
│   ├── simple_requirements.md      # 简化需求
│   ├── required_documents.md       # 需求文档
│   └── test_requirements.md        # 测试需求
│
├── 📁 litchi-smart-orchard-bid/   # 荔枝果园投标项目
│   ├── README.md                   # 投标项目说明
│   ├── checklist.md                # 投标文件清单
│   ├── common/                     # 通用材料
│   │   ├── company_qualifications/ # 公司资质
│   │   ├── personnel/              # 人员配置
│   │   ├── performance/            # 业绩证明
│   │   └── pricing/                # 报价材料
│   ├── package_A/                  # A包：技术方案
│   ├── package_B/                  # B包：测试方案
│   └── package_C/                  # C包：服务方案
│
├── 📁 outputs/                     # 输出文件目录
│   ├── *.pdf                       # 生成的PDF文件
│   ├── *.log                       # 日志文件
│   └── *.aux                       # LaTeX辅助文件
│
├── 📁 examples/                    # 示例文件目录
│   ├── *.pdf                       # 示例PDF文件
│   └── *.zip                       # 示例压缩包
│
├── 📁 build/                       # 构建目录
│   ├── cache/                      # 缓存文件
│   ├── logs/                       # 构建日志
│   ├── main.tex                    # 生成的LaTeX文件
│   ├── merged.md                   # 合并后的内容
│   └── content.md                  # 原始内容
│
├── 📁 tests/                       # 测试目录
│   ├── test_kb_search.py           # 知识库搜索测试
│   ├── test_latex_renderer.py      # LaTeX渲染测试
│   └── test_requirements_parser.py # 需求解析测试
│
└── 📁 scoring_results/             # 评分结果目录
    ├── detailed_scoring_results_*.json  # 详细评分结果
    ├── scoring_report_*.txt            # 评分报告
    ├── scoring_results_*.xlsx          # 评分结果表格
    └── scoring_summary_*.json          # 评分摘要
```

## 核心功能

### 1. 智能投标文件生成
- **需求解析**：自动解析招标文件要求
- **内容检索**：从知识库中智能检索相关内容
- **内容合并**：在生成阶段通过提示词产出可直接拼接的片段，最终合并时无需再次调用LLM
- **PDF生成**：自动生成符合要求的投标文件
- **分页布局**：每条需求自动分页呈现，避免内容过于紧凑
- **需求分类**：LLM区分需生成文字与需原文复制的条目

### 2. 技术方案设计
- **系统架构**：分层架构设计，支持扩展
- **功能模块**：环境监测、智能灌溉、病虫害监测等
- **技术选型**：现代化的技术栈选择
- **实施方案**：详细的项目实施计划

### 3. 知识库管理
- **文档扫描**：自动扫描和索引文档
- **智能搜索**：基于语义的文档检索
- **内容排名**：智能排序相关内容
- **缓存管理**：提高检索效率

## 技术架构

### 后端技术
- **Python 3.8+**：主要开发语言
- **DashScope API**：通义千问大语言模型
- **LaTeX**：专业文档排版
- **JSON**：数据交换格式

### 核心算法
- **语义搜索**：基于LLM的智能检索
- **内容合并**：智能内容整合算法
- **文档生成**：自动化文档生成
- **缓存优化**：智能缓存策略

### 部署要求
- **操作系统**：Windows/macOS/Linux
- **Python环境**：Python 3.8+
- **TeX发行版**：支持XeLaTeX
- **内存要求**：建议8GB以上

## 快速开始

### 环境准备

1. **安装Python依赖**
```bash
pip install -r requirements.txt
```

2. **配置API密钥**
```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

3. **安装TeX发行版**
- Windows: 安装MiKTeX或TeX Live
- macOS: 安装MacTeX
- Linux: 安装TeX Live

### 基本使用

1. **生成投标文件**
```bash
python build_pdf.py --requirements test_requirements.md --kb litchi-smart-orchard-bid --out bid_document.pdf
```

2. **提取文档内容**
```bash
python scripts/pdf_extractor.py
```

3. **运行测试**
```bash
python -m pytest tests/
```

### 高级配置

1. **自定义模板**
- 修改 `templates/main.tex` 文件
- 调整页面设置和样式

2. **配置LLM参数**
- 修改 `config.py` 中的参数
- 调整温度和最大token数

3. **扩展知识库**
- 在 `litchi-smart-orchard-bid/` 目录添加文档
- 更新文档结构和内容

## 使用示例

### 示例1：生成五页标书
```bash
# 使用简化生成器
python scripts/simple_pdf_generator.py

# 使用LLM生成器
python build_pdf.py --requirements test_requirements.md --kb litchi-smart-orchard-bid --out test_bid.pdf --topk 3
```

### 示例2：端到端运行（先提取需求再生成PDF）
```bash
python full_pipeline.py --tender path/to/tender.pdf --kb litchi-smart-orchard-bid --out my_bid.pdf
```

### 示例3：自定义需求文件
```markdown
# 自定义需求文件
**1. 技术方案要求**
- 页码：第1页
- 内容：系统架构设计

**2. 实施方案要求**
- 页码：第2页
- 内容：项目计划安排
```

### 示例4：批量处理
```bash
# 批量生成多个文档
for req in docs/*.md; do
    python build_pdf.py --requirements "$req" --kb litchi-smart-orchard-bid --out "outputs/$(basename "$req" .md).pdf"
done
```

## 开发指南

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 编写完整的文档字符串
- 添加适当的注释

### 贡献指南
1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 常见问题

### Q1: LLM API调用失败
**A**: 检查API密钥配置，确保网络连接正常，可以尝试切换模型。

### Q2: LaTeX编译错误
**A**: 确保安装了完整的TeX发行版，检查LaTeX语法是否正确。



## 更新日志

### v1.0.0 (2025-08-19)


## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

- **项目维护者**：中电科国海信通科技（海南）有限公司
- **技术支持**：tech-support@company.com
- **项目地址**：https://github.com/company/smart-orchard-system

## 致谢

感谢所有为项目做出贡献的开发者和用户，特别感谢：
- 通义千问团队提供的LLM服务
- LaTeX社区提供的专业排版工具
- 开源社区的各种优秀工具和库

---

*本项目致力于推动智慧农业发展，通过技术创新提升农业生产效率和质量。*
