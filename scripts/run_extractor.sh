#!/bin/bash

# 招标文件文档提取器启动脚本

echo "🔧 招标文件文档提取器"
echo "========================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖包
echo "📦 检查依赖包..."
if ! python3 -c "import pdfplumber, requests" &> /dev/null; then
    echo "⚠️ 缺少依赖包，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖包安装失败"
        exit 1
    fi
fi

# 检查API密钥
if [ -z "$QIANWEN_API_KEY" ]; then
    export QIANWEN_API_KEY="sk-fe0485c281964259b404907d483d3777"
fi

# 检查PDF文件
if [ ! -f "03.招标文件.pdf" ]; then
    echo "❌ 错误：未找到招标文件PDF"
    echo "请确保 '03.招标文件.pdf' 文件存在于当前目录"
    exit 1
fi

echo "✅ 环境检查通过"
echo "🚀 启动文档提取器..."

# 运行主程序
python3 extract_required_documents.py

# 检查运行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 文档提取完成！"
    echo "📁 输出文件："
    echo "  - required_documents.md (文档清单)"
    echo "  - extracted_documents_*.json (详细数据)"
else
    echo ""
    echo "❌ 文档提取失败，请检查错误信息"
    exit 1
fi

