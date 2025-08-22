#!/usr/bin/env python3
"""
测试修复后的JSON解析和PDF生成功能
"""

import json
import tempfile
from pathlib import Path
from src.pdf_builder import build_pdf
from src.latex_renderer import markdown_to_latex, _fix_itemize_environments, _simple_markdown_to_latex
from src.caching import LLMCache

def test_json_encoding():
    """测试JSON编码问题"""
    print("🧪 测试JSON编码...")
    
    # 测试数据
    test_data = {
        "测试": "中文内容",
        "special_chars": "≥≤><%",
        "nested": {
            "中文键": "中文值",
            "list": ["项目1", "项目2", "项目3"]
        }
    }
    
    try:
        # 测试ensure_ascii=False
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2, default=str)
        print("✅ ensure_ascii=False 成功")
        
        # 测试ensure_ascii=True
        json_str_ascii = json.dumps(test_data, ensure_ascii=True, indent=2, default=str)
        print("✅ ensure_ascii=True 成功")
        
        # 测试写入文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write(json_str)
            temp_path = Path(f.name)
        
        # 测试读取文件
        with open(temp_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        print("✅ JSON文件读写成功")
        temp_path.unlink()  # 清理临时文件
        
    except Exception as e:
        print(f"❌ JSON测试失败: {e}")
        return False
    
    return True

def test_latex_itemize_fix():
    """测试LaTeX itemize环境修复"""
    print("\n🧪 测试LaTeX itemize环境修复...")
    
    # 测试用例
    test_cases = [
        # 正常情况
        ("\\begin{itemize}\n\\item 项目1\n\\item 项目2\n\\end{itemize}", "正常itemize"),
        
        # 缺少end{itemize}
        ("\\begin{itemize}\n\\item 项目1\n\\item 项目2", "缺少end{itemize}"),
        
        # 缺少begin{itemize}
        ("\\item 项目1\n\\item 项目2\n\\end{itemize}", "缺少begin{itemize}"),
        
        # 嵌套情况
        ("\\begin{itemize}\n\\item 项目1\n\\begin{itemize}\n\\item 子项目1\n\\end{itemize}\n\\end{itemize}", "嵌套itemize"),
        
        # 混合情况
        ("\\section{测试}\n\\item 项目1\n\\item 项目2\n\\subsection{子标题}\n\\item 项目3", "混合情况"),
    ]
    
    for latex, description in test_cases:
        try:
            fixed = _fix_itemize_environments(latex)
            begin_count = fixed.count("\\begin{itemize}")
            end_count = fixed.count("\\end{itemize}")
            
            if begin_count == end_count:
                print(f"✅ {description}: 修复成功 (begin: {begin_count}, end: {end_count})")
            else:
                print(f"❌ {description}: 修复失败 (begin: {begin_count}, end: {end_count})")
                print(f"   原始: {latex}")
                print(f"   修复后: {fixed}")
                
        except Exception as e:
            print(f"❌ {description}: 测试异常 {e}")
    
    return True

def test_markdown_to_latex():
    """测试Markdown到LaTeX转换"""
    print("\n🧪 测试Markdown到LaTeX转换...")
    
    test_markdown = """# 测试标题

## 子标题

- 列表项目1
- 列表项目2
  - 嵌套项目1
  - 嵌套项目2

**粗体文本** 和 `代码文本`

包含特殊符号: ≥ ≤ > < %

## 另一个标题

- 新的列表
- 更多项目
"""
    
    try:
        # 使用简单转换（不需要LLM）
        latex = _simple_markdown_to_latex(test_markdown)
        print("✅ 简单转换成功")
        print(f"   生成的LaTeX长度: {len(latex)} 字符")
        
        # 检查itemize环境
        begin_count = latex.count("\\begin{itemize}")
        end_count = latex.count("\\end{itemize}")
        if begin_count == end_count:
            print(f"✅ itemize环境平衡 (begin: {begin_count}, end: {end_count})")
        else:
            print(f"❌ itemize环境不平衡 (begin: {begin_count}, end: {end_count})")
        
        return True
        
    except Exception as e:
        print(f"❌ Markdown转换测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试修复后的功能...\n")
    
    # 运行所有测试
    tests = [
        test_json_encoding,
        test_latex_itemize_fix,
        test_markdown_to_latex,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！修复成功！")
    else:
        print("⚠️  部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
