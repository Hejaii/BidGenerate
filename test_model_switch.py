#!/usr/bin/env python3
# -*- coding: utf-8
"""
测试LLMClient的模型切换功能
"""

from llm_client import LLMClient

def test_model_switch():
    """测试模型切换功能"""
    
    print("🚀 测试LLMClient模型切换功能...")
    
    # 创建客户端实例
    client = LLMClient()
    
    print(f"当前模型: {client.model}")
    print(f"模型列表: {client.models}")
    
    # 手动切换到下一个模型（跳过第一个已用完免费额度的模型）
    print("\n🔄 手动切换到下一个模型...")
    client._rotate_model()
    print(f"现在使用模型: {client.model}")
    
    # 再切换一次
    print("\n🔄 再切换一次...")
    client._rotate_model()
    print(f"现在使用模型: {client.model}")
    
    # 测试简单的对话
    print("\n🧪 测试简单对话...")
    try:
        messages = [
            {"role": "user", "content": "你好，请简单回复一下"}
        ]
        
        response = client.chat(messages, max_tokens=100)
        print(f"✅ 对话成功！回复: {response}")
        
    except Exception as e:
        print(f"❌ 对话失败: {e}")
        print("尝试切换到下一个模型...")
        client._rotate_model()
        print(f"现在使用模型: {client.model}")
        
        try:
            response = client.chat(messages, max_tokens=100)
            print(f"✅ 第二次尝试成功！回复: {response}")
        except Exception as e2:
            print(f"❌ 第二次尝试也失败: {e2}")

if __name__ == "__main__":
    test_model_switch()
