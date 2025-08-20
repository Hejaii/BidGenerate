#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标文要求评分程序快速启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import requests
        print("✓ requests 已安装")
    except ImportError:
        print("✗ requests 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("✓ requests 安装完成")
    
    # 检查可选依赖
    try:
        import pandas
        print("✓ pandas 已安装 (支持Excel输出)")
    except ImportError:
        print("⚠ pandas 未安装 (将跳过Excel输出)")
    
    try:
        import openpyxl
        print("✓ openpyxl 已安装 (支持Excel输出)")
    except ImportError:
        print("⚠ openpyxl 未安装 (将跳过Excel输出)")

def check_config():
    """检查配置文件"""
    config_file = Path(__file__).parent / "config.py"
    if not config_file.exists():
        print("✗ 配置文件 config.py 不存在")
        return False
    
    print("✓ 配置文件 config.py 存在")
    return True

def check_paths():
    """检查路径配置"""
    try:
        # 动态导入配置
        sys.path.append(str(Path(__file__).parent))
        import config
        
        # 检查项目根目录
        if not os.path.exists(config.PROJECT_ROOT):
            print(f"✗ 项目根目录不存在: {config.PROJECT_ROOT}")
            return False
        print(f"✓ 项目根目录存在: {config.PROJECT_ROOT}")
        
        # 检查要求文件
        if not os.path.exists(config.REQUIREMENTS_FILE):
            print(f"✗ 要求文件不存在: {config.REQUIREMENTS_FILE}")
            return False
        print(f"✓ 要求文件存在: {config.REQUIREMENTS_FILE}")
        
        # 检查输出目录
        output_dir = Path(config.OUTPUT_DIR)
        if not output_dir.exists():
            print(f"⚠ 输出目录不存在，将自动创建: {config.OUTPUT_DIR}")
        else:
            print(f"✓ 输出目录存在: {config.OUTPUT_DIR}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入配置文件失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 检查路径配置失败: {e}")
        return False

def show_menu():
    """显示菜单"""
    print("\n" + "="*50)
    print("标文要求评分程序")
    print("="*50)
    print("1. 运行基础版评分程序")
    print("2. 运行增强版评分程序 (推荐)")
    print("3. 检查系统状态")
    print("4. 查看使用说明")
    print("5. 退出")
    print("="*50)

def run_basic_scorer():
    """运行基础版评分程序"""
    print("\n正在启动基础版评分程序...")
    try:
        script_path = Path(__file__).parent / "requirement_scorer.py"
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"程序运行失败: {e}")
    except KeyboardInterrupt:
        print("\n程序被用户中断")

def run_enhanced_scorer():
    """运行增强版评分程序"""
    print("\n正在启动增强版评分程序...")
    try:
        script_path = Path(__file__).parent / "enhanced_requirement_scorer.py"
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"程序运行失败: {e}")
    except KeyboardInterrupt:
        print("\n程序被用户中断")

def check_system_status():
    """检查系统状态"""
    print("\n=== 系统状态检查 ===")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查依赖
    print("\n依赖检查:")
    check_dependencies()
    
    # 检查配置
    print("\n配置检查:")
    check_config()
    
    # 检查路径
    print("\n路径检查:")
    check_paths()
    
    print("\n系统状态检查完成")

def show_usage():
    """显示使用说明"""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n" + "="*60)
                print("使用说明")
                print("="*60)
                print(content)
        except Exception as e:
            print(f"读取说明文件失败: {e}")
    else:
        print("说明文件 README.md 不存在")

def main():
    """主函数"""
    print("欢迎使用标文要求评分程序！")
    
    # 初始检查
    print("\n正在检查系统状态...")
    if not check_config():
        print("配置文件检查失败，请确保 config.py 文件存在")
        return
    
    if not check_paths():
        print("路径配置检查失败，请修改 config.py 中的路径配置")
        return
    
    # 主循环
    while True:
        try:
            show_menu()
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == "1":
                run_basic_scorer()
            elif choice == "2":
                run_enhanced_scorer()
            elif choice == "3":
                check_system_status()
            elif choice == "4":
                show_usage()
            elif choice == "5":
                print("感谢使用，再见！")
                break
            else:
                print("无效选择，请输入 1-5 之间的数字")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断，正在退出...")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print("请检查配置或联系技术支持")

if __name__ == "__main__":
    main()


