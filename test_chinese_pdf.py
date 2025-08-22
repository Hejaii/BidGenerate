#!/usr/bin/env python3
"""
专门测试中文PDF生成，确保中文内容不乱码
"""

import tempfile
from pathlib import Path
from src.pdf_builder import build_pdf

def test_chinese_pdf_generation():
    """测试中文PDF生成流程"""
    print("🧪 测试中文PDF生成流程...")
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        work_dir = temp_path / "build_test"
        work_dir.mkdir()
        
        # 创建中文测试需求文件
        requirements_file = temp_path / "中文测试需求.md"
        requirements_content = """# 智能化荔枝果园管理系统项目需求

## 技术方案要求
- 系统架构设计必须采用微服务架构
- 技术选型需要考虑可扩展性和稳定性
- 性能指标要达到高并发处理能力

## 实施方案要求
- 项目计划要详细到每个阶段
- 资源配置要合理分配人力物力
- 质量控制要建立完善的管理体系

## 管理方案要求
- 组织架构要清晰明确职责分工
- 沟通机制要建立定期汇报制度
- 风险管理要制定应急预案
"""
        requirements_file.write_text(requirements_content, encoding="utf-8")
        
        # 创建中文测试知识库
        kb_dir = temp_path / "中文知识库"
        kb_dir.mkdir()
        
        # 创建中文技术文档
        doc1 = kb_dir / "技术方案.md"
        doc1.write_text("""# 系统架构设计

本项目采用微服务架构，主要包含以下组件：

## 前端层
- Web管理界面：提供直观的用户操作界面
- 移动端APP：支持移动设备访问
- 数据可视化大屏：实时展示果园状态

## 应用层
- 业务逻辑服务：处理核心业务逻辑
- 数据处理服务：负责数据清洗和转换
- 消息队列服务：确保系统间通信可靠

## 数据层
- 关系型数据库：存储结构化数据
- 时序数据库：存储传感器时序数据
- 缓存系统：提高数据访问性能
""", encoding="utf-8")
        
        doc2 = kb_dir / "实施方案.md"
        doc2.write_text("""# 项目计划

## 第一阶段：需求分析（30天）
- 需求调研：深入了解客户需求
- 需求分析：分析技术可行性
- 需求确认：与客户确认最终需求

## 第二阶段：系统设计（45天）
- 架构设计：设计系统整体架构
- 详细设计：设计具体功能模块
- 接口设计：设计系统间接口规范

## 第三阶段：开发实施（90天）
- 编码开发：按照设计进行编码
- 单元测试：确保代码质量
- 集成测试：验证系统集成效果
""", encoding="utf-8")
        
        doc3 = kb_dir / "管理方案.md"
        doc3.write_text("""# 组织架构

## 项目团队
- 项目经理：负责项目整体管理
- 技术负责人：负责技术方案制定
- 开发工程师：负责具体功能开发
- 测试工程师：负责质量保证

## 沟通机制
- 日常站会：每日15分钟进度同步
- 周例会：每周总结和下周计划
- 里程碑评审：关键节点评审会议
- 变更管理：建立变更申请流程
""", encoding="utf-8")
        
        # 输出PDF文件到当前目录
        output_pdf = Path("./中文测试PDF.pdf")
        
        try:
            print("   开始构建中文PDF...")
            print("   使用LLM进行中文内容解析和生成...")
            print(f"   输出文件: {output_pdf.absolute()}")
            print("   强制使用中文模板确保中文显示正常...")
            
            # 强制指定使用中文模板
            chinese_template = Path("templates/main_compatible.tex")
            if not chinese_template.exists():
                chinese_template = Path("templates/main.tex")
            
            print(f"   使用模板: {chinese_template}")
            
            # 调用build_pdf，强制使用中文模板
            build_pdf(
                requirements=requirements_file,
                kb=kb_dir,
                out=output_pdf,
                latex_template=chinese_template,  # 强制使用中文模板
                workdir=work_dir,
                topk=3,
                use_llm=True  # 启用LLM调用
            )
            
            # 检查输出文件
            if output_pdf.exists() and output_pdf.stat().st_size > 0:
                print(f"✅ 中文PDF生成成功！文件大小: {output_pdf.stat().st_size} 字节")
                print(f"   文件位置: {output_pdf.absolute()}")
                
                # 检查工作目录中的文件
                print("   检查生成的文件:")
                for file_path in work_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(work_dir)
                        size = file_path.stat().st_size
                        print(f"     {rel_path}: {size} 字节")
                
                return True
            else:
                print("❌ 中文PDF文件未生成或为空")
                return False
                
        except Exception as e:
            print(f"❌ 中文PDF生成失败: {e}")
            return False

def main():
    """主函数"""
    print("🚀 开始测试中文PDF生成流程...\n")
    print("📝 本次测试专门验证中文内容显示效果")
    print("🔤 确保使用中文模板，避免英文模板导致的中文乱码问题\n")
    
    if test_chinese_pdf_generation():
        print("\n🎉 中文PDF生成测试成功！")
        print("✅ PDF文件已保存到当前目录")
        print("✅ 使用中文模板确保中文显示正常")
        print("✅ 可以使用系统默认应用打开PDF文件")
        
        # 尝试打开PDF文件
        pdf_path = Path("./中文测试PDF.pdf")
        if pdf_path.exists():
            print(f"\n📄 中文PDF文件已生成: {pdf_path.absolute()}")
            print("💡 请使用以下命令打开PDF文件:")
            print(f"   open {pdf_path}")
            print("\n🔍 请检查以下内容是否正确显示中文:")
            print("   - 封面标题和项目信息")
            print("   - 目录页标题")
            print("   - 正文中的中文内容")
            print("   - 特殊中文字符（如：、等）")
    else:
        print("\n❌ 中文PDF生成测试失败")

if __name__ == "__main__":
    main()
