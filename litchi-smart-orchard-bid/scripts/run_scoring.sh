#!/bin/bash

echo "============================================================"
echo "智能评分程序 - Linux/Mac启动脚本"
echo "============================================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.7或更高版本"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "Python检查通过: $(python3 --version)"
echo

# 切换到脚本目录
cd "$(dirname "$0")"

# 检查必要文件
if [ ! -f "scoring_config.py" ]; then
    echo "错误: 找不到配置文件 scoring_config.py"
    exit 1
fi

if [ ! -f "simple_scorer.py" ]; then
    echo "错误: 找不到主程序文件 simple_scorer.py"
    exit 1
fi

echo "文件检查完成，正在启动智能评分程序..."
echo

# 运行Python程序
python3 simple_scorer.py

echo
echo "程序执行完成"



