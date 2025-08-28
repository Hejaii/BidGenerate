# 快速开始指南

## 🚀 5分钟快速上手

本指南将帮助您在5分钟内快速上手智能化荔枝果园管理系统项目，生成您的第一个投标文件。

## 环境准备

### 1. 检查Python环境
```bash
python3 --version
# 确保版本 >= 3.8
```

### 2. 安装依赖包
```bash
pip install -r requirements.txt
```

> 项目已在 `llm_client.py` 中内置示例 API 密钥，如需更换可直接修改该文件。

### 3. 安装LaTeX（可选）
- **macOS**: `brew install --cask mactex`
- **Ubuntu**: `sudo apt-get install texlive-full`
- **Windows**: 下载安装MiKTeX

## 快速体验

### 方法1：使用简化生成器（推荐新手）

```bash
# 运行简化PDF生成器
python scripts/simple_pdf_generator.py
```

**输出**：`test_bid_document.pdf` - 一个5页的标书示例

### 方法2：使用LLM智能生成器

```bash
# 使用LLM生成专业标书
python build_pdf.py --requirements test_requirements.md --kb litchi-smart-orchard-bid --out my_bid.pdf
```

**输出**：`my_bid.pdf` - 基于AI生成的个性化标书

## 自定义您的标书

### 1. 修改需求文件
编辑 `test_requirements.md`：
```markdown
# 我的项目需求

**1. 技术方案要求**
- 页码：第1页
- 内容：系统架构设计

**2. 实施方案要求**
- 页码：第2页
- 内容：项目计划安排
```

### 2. 添加您的材料
在 `litchi-smart-orchard-bid/` 目录下添加您的：
- 公司资质证书
- 人员简历
- 项目业绩
- 技术方案

### 3. 重新生成
```bash
python build_pdf.py --requirements test_requirements.md --kb litchi-smart-orchard-bid --out my_custom_bid.pdf
```

## 常见问题解决

### ❌ LaTeX编译失败
```bash
# 检查LaTeX安装
which xelatex

# 如果没有安装，使用简化生成器
python scripts/simple_pdf_generator.py
```

### ❌ 依赖包缺失
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt
```

## 下一步

### 深入学习
1. 阅读 [README.md](../README.md) 了解项目全貌
2. 查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 理解项目结构
3. 探索 `src/` 目录了解核心算法

### 高级功能
1. **自定义模板**：修改 `templates/main.tex`
2. **扩展知识库**：在 `litchi-smart-orchard-bid/` 添加更多材料
3. **批量处理**：编写脚本批量生成多个文档

### 贡献项目
1. 报告Bug和问题
2. 提交功能建议
3. 贡献代码改进
4. 完善文档说明

## 示例输出

成功运行后，您将看到：

```
✅ PDF生成完成！输出文件: my_bid.pdf
📁 中间文件保存在: build/
```

生成的文件包括：
- **主文件**：`my_bid.pdf` - 您的投标文件
- **中间文件**：`build/` 目录下的各种文件
- **日志文件**：构建过程的详细日志

## 技术支持

如果遇到问题：
1. 查看错误日志
2. 检查配置文件
3. 参考常见问题
4. 提交Issue到项目仓库

---

🎉 **恭喜！您已经成功生成了第一个智能投标文件！**

现在您可以：
- 查看生成的PDF文件
- 根据实际需求调整内容
- 探索更多高级功能
- 为项目做出贡献
