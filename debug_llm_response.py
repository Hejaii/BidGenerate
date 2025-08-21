#!/usr/bin/env python3
# -*- coding: utf-8
"""
调试LLMClient的响应内容
"""

from llm_client import LLMClient

def debug_llm_response():
    """调试LLMClient的响应"""
    
    print("🔍 调试LLMClient响应...")
    
    # 创建客户端实例
    client = LLMClient()
    
    # 测试简单的prompt
    test_prompt = """你是"要求抽取器"。请分析以下招标文件内容，提取所有商务要求和技术要求。

请按照以下JSON格式输出，只返回JSON，不要其他文字：

{
  "requirements": [
    {
      "category": "商务要求/技术要求",
      "requirement_text": "完整的要求内容",
      "score": 分数值（如果没有分数则写0）,
      "is_important": true/false（如果要求开头有▲符号则为true）,
      "requirement_summary": "不超过50字的概括"
    }
  ]
}

如果页面中没有商务或技术要求，请返回空数组。

重要：请严格按照JSON格式输出，不要包含任何其他文字、说明或解释。"""

    test_content = "投标人需提供付款方式和条件说明。"
    
    messages = [
        {
            "role": "user",
            "content": f"{test_prompt}\n\n页面内容：\n{test_content}"
        }
    ]
    
    try:
        print("📤 发送请求...")
        response = client.chat(messages, temperature=0.1, max_tokens=1000)
        
        print("📥 收到响应:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # 尝试解析JSON
        try:
            import json
            parsed = json.loads(response)
            print("✅ JSON解析成功!")
            print(f"解析结果: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print("响应内容可能不是有效的JSON格式")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    debug_llm_response()
