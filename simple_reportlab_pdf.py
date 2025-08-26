#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用reportlab生成PDF - 简单版本
"""

import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def load_cache_content():
    """加载cache中的内容"""
    cache_file = "build_test_current/cache/ea77395a1ae0fe44de82925f16558b630159268ac89a144eaf30f849f64bab8d.json"
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取cache文件失败: {e}")
        return "技术方案内容加载失败"

def create_pdf():
    """创建PDF文档"""
    # 创建PDF文件
    pdf_path = "cache_bid_document_reportlab.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    
    # 获取样式
    styles = getSampleStyleSheet()
    
    # 创建自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # 构建文档内容
    story = []
    
    # 标题页
    story.append(Paragraph("智能化荔枝果园管理系统项目投标文件", title_style))
    story.append(Spacer(1, 50))
    
    # 项目信息
    story.append(Paragraph("项目编号：HHNNSHBB-2023100066", normal_style))
    story.append(Paragraph("项目名称：智能化荔枝果园管理系统项目", normal_style))
    story.append(Paragraph("标包名称：A包：智能化荔枝果园管理系统构建项目", normal_style))
    story.append(Paragraph("标包编号：HHNNSHBB-20233100066-A", normal_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("供应商：中电科国海信通科技（海南）有限公司", normal_style))
    story.append(Paragraph("日期：2025年8月15日", normal_style))
    
    story.append(PageBreak())
    
    # 目录
    story.append(Paragraph("目录", heading_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("一、投标函", normal_style))
    story.append(Paragraph("二、法定代表人身份证明", normal_style))
    story.append(Paragraph("三、法定代表人授权委托书", normal_style))
    story.append(Paragraph("四、供应商基本情况", normal_style))
    story.append(Paragraph("五、技术方案", normal_style))
    story.append(Paragraph("六、项目承诺", normal_style))
    
    story.append(PageBreak())
    
    # 一、投标函
    story.append(Paragraph("一、投标函", heading_style))
    story.append(Paragraph("致：海南省农业农村厅", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("我方已仔细研究了上述项目的招标文件，愿意按照招标文件的要求承担上述项目的建设任务，并承诺：", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. 我方完全理解并接受招标文件的全部内容，愿意按照招标文件的要求提供所有服务", normal_style))
    story.append(Paragraph("2. 我方承诺在投标有效期内不修改、不撤销投标文件", normal_style))
    story.append(Paragraph("3. 我方承诺中标后按照招标文件的要求与采购人签订合同", normal_style))
    story.append(Paragraph("4. 我方承诺按照招标文件的要求提供所有必要的技术支持和售后服务", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("投标人（盖章）：中电科国海信通科技（海南）有限公司", normal_style))
    story.append(Paragraph("法定代表人（签字）：张三", normal_style))
    story.append(Paragraph("投标日期：2025年8月15日", normal_style))
    
    story.append(PageBreak())
    
    # 二、法定代表人身份证明
    story.append(Paragraph("二、法定代表人身份证明", heading_style))
    story.append(Paragraph("投标人名称：中电科国海信通科技（海南）有限公司", normal_style))
    story.append(Paragraph("法定代表人：张三", normal_style))
    story.append(Paragraph("身份证号码：460100199001011234", normal_style))
    story.append(Paragraph("职务：董事长兼总经理", normal_style))
    story.append(Paragraph("联系电话：0898-12345678", normal_style))
    story.append(Paragraph("联系地址：海南省海口市美兰区国兴大道123号", normal_style))
    
    story.append(PageBreak())
    
    # 三、法定代表人授权委托书
    story.append(Paragraph("三、法定代表人授权委托书", heading_style))
    story.append(Paragraph("委托人：中电科国海信通科技（海南）有限公司", normal_style))
    story.append(Paragraph("法定代表人：张三", normal_style))
    story.append(Paragraph("受托人：李四", normal_style))
    story.append(Paragraph("职务：技术总监", normal_style))
    story.append(Paragraph("身份证号码：460100198502023456", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("授权范围：代表本公司参加智能化荔枝果园管理系统项目的投标活动，包括但不限于：投标文件的编制、递交、开标、评标、合同谈判、合同签署等一切与投标相关的事宜。", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("授权期限：自本授权委托书签署之日起至本项目招标活动结束之日止。", normal_style))
    
    story.append(PageBreak())
    
    # 四、供应商基本情况
    story.append(Paragraph("四、供应商基本情况", heading_style))
    
    story.append(Paragraph("公司简介", subheading_style))
    story.append(Paragraph("中电科国海信通科技（海南）有限公司成立于2020年，注册资本5000万元人民币，是一家专注于智慧农业、物联网技术、大数据分析的高新技术企业。公司拥有完整的研发、生产、销售和服务体系，在智慧农业领域具有丰富的项目经验和深厚的技术积累。", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("主营业务", subheading_style))
    story.append(Paragraph("• 智慧农业系统集成与解决方案", normal_style))
    story.append(Paragraph("• 物联网设备研发、生产与销售", normal_style))
    story.append(Paragraph("• 大数据分析与人工智能应用", normal_style))
    story.append(Paragraph("• 软件开发与技术服务", normal_style))
    story.append(Paragraph("• 系统集成与运维服务", normal_style))
    story.append(Paragraph("• 农业技术推广与咨询服务", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("技术实力", subheading_style))
    story.append(Paragraph("• 拥有自主知识产权专利15项，软件著作权30项", normal_style))
    story.append(Paragraph("• 获得高新技术企业认证、ISO9001质量管理体系认证", normal_style))
    story.append(Paragraph("• 获得ISO14001环境管理体系认证、ISO45001职业健康安全管理体系认证", normal_style))
    story.append(Paragraph("• 获得软件企业认定证书、安全开发服务资质证书", normal_style))
    story.append(Paragraph("• 获得CMA计量认证、CNAS实验室认可证书", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("团队规模与结构", subheading_style))
    story.append(Paragraph("• 员工总数：120人", normal_style))
    story.append(Paragraph("• 技术人员：85人（占比70.8%）", normal_style))
    story.append(Paragraph("• 高级工程师：25人", normal_style))
    story.append(Paragraph("• 项目经理：15人", normal_style))
    story.append(Paragraph("• 博士学历：8人，硕士学历：32人", normal_style))
    
    story.append(PageBreak())
    
    # 五、技术方案
    story.append(Paragraph("五、技术方案", heading_style))
    
    # 加载cache内容并分段处理
    cache_content = load_cache_content()
    paragraphs = cache_content.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # 处理标题
            if para.startswith('###'):
                title = para.replace('###', '').strip()
                story.append(Paragraph(title, subheading_style))
            elif para.startswith('##'):
                title = para.replace('##', '').strip()
                story.append(Paragraph(title, heading_style))
            elif para.startswith('#'):
                title = para.replace('#', '').strip()
                story.append(Paragraph(title, title_style))
            else:
                # 处理普通段落
                story.append(Paragraph(para, normal_style))
            story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # 六、项目承诺
    story.append(Paragraph("六、项目承诺", heading_style))
    story.append(Paragraph("我方承诺所提供的所有材料真实、准确、完整，如有虚假，愿意承担相应的法律责任。我方承诺在投标有效期内不修改、不撤销投标文件，中标后严格按照招标文件要求与采购人签订合同并履行合同义务。", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("投标人（盖章）：中电科国海信通科技（海南）有限公司", normal_style))
    story.append(Paragraph("法定代表人（签字）：张三", normal_style))
    story.append(Paragraph("日期：2025年8月15日", normal_style))
    
    # 生成PDF
    doc.build(story)
    print(f"✅ PDF生成完成！输出文件: {pdf_path}")
    return pdf_path

def main():
    """主函数"""
    print("开始使用reportlab生成标书PDF...")
    
    try:
        pdf_path = create_pdf()
        print(f"PDF文件已生成: {pdf_path}")
    except Exception as e:
        print(f"PDF生成失败: {e}")

if __name__ == "__main__":
    main()
