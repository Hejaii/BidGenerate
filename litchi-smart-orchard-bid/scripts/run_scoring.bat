@echo off
chcp 65001 >nul
title 智能评分程序

echo ============================================================
echo 智能评分程序 - Windows启动脚本
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python检查通过
echo.

REM 切换到脚本目录
cd /d "%~dp0"

REM 检查必要文件
if not exist "scoring_config.py" (
    echo 错误: 找不到配置文件 scoring_config.py
    pause
    exit /b 1
)

if not exist "simple_scorer.py" (
    echo 错误: 找不到主程序文件 simple_scorer.py
    pause
    exit /b 1
)

echo 文件检查完成，正在启动智能评分程序...
echo.

REM 运行Python程序
python simple_scorer.py

echo.
echo 程序执行完成
pause



