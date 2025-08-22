#!/usr/bin/env python3
"""
测试不同的API密钥配置和模型
"""

import os
from llm_client import LLMClient

def test_api_key_config():
    """测试不同的API密钥配置"""
    print("🧪 测试API密钥配置...")
    
    # 测试1: 使用环境变量
    print("\n1. 测试环境变量 DASHSCOPE_API_KEY:")
    env_key = os.getenv("DASHSCOPE_API_KEY")
    if env_key:
        print(f"   环境变量值: {env_key[:10]}...")
        try:
            client = LLMClient(api_key=env_key)
            print(f"   ✅ 使用环境变量创建客户端成功，模型: {client.model}")
        except Exception as e:
            print(f"   ❌ 使用环境变量失败: {e}")
    else:
        print("   ⚠️  环境变量 DASHSCOPE_API_KEY 未设置")
    
    # 测试2: 使用默认API密钥
    print("\n2. 测试默认API密钥:")
    try:
        client = LLMClient()
        print(f"   ✅ 使用默认密钥创建客户端成功，模型: {client.model}")
        print(f"   当前使用的API密钥: {client.api_key[:10]}...")
    except Exception as e:
        print(f"   ❌ 使用默认密钥失败: {e}")
    
    # 测试3: 尝试不同的模型
    print("\n3. 测试不同的模型:")
    try:
        client = LLMClient()
        print(f"   当前模型: {client.model}")
        
        # 尝试切换到第一个模型
        client._model_index = 0
        print(f"   切换到第一个模型: {client.model}")
        
        # 尝试切换到最后一个模型
        client._model_index = len(client.models) - 1
        print(f"   切换到最后一个模型: {client.model}")
        
    except Exception as e:
        print(f"   ❌ 模型测试失败: {e}")
    
    # 测试4: 尝试简单的API调用
    print("\n4. 测试API调用:")
    try:
        client = LLMClient()
        print(f"   使用模型: {client.model}")
        print(f"   使用API密钥: {client.api_key[:10]}...")
        
        messages = [
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "请简单回复'测试成功'"}
        ]
        
        print("   发送测试消息...")
        response = client.chat(messages)
        print(f"   ✅ API调用成功，响应: {response}")
        
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")
        
        # 尝试切换到下一个模型
        try:
            print("   尝试切换到下一个模型...")
            client._rotate_model()
            print(f"   新模型: {client.model}")
            
            print("   再次尝试API调用...")
            response = client.chat(messages)
            print(f"   ✅ 使用新模型成功，响应: {response}")
            
        except Exception as e2:
            print(f"   ❌ 新模型也失败: {e2}")

def test_different_models():
    """测试不同的模型配置"""
    print("\n🧪 测试不同的模型配置...")
    
    # 测试不同的模型列表
    test_models = [
        ["qwen-plus-1127"],  # 单个模型
        ["qwen-plus-1127", "qwen-plus-1220"],  # 两个模型
        ["qwen-plus-0112", "qwen-plus-0919", "qwen-plus-0723"],  # 三个模型
    ]
    
    for i, models in enumerate(test_models, 1):
        print(f"\n{i}. 测试模型列表: {models}")
        try:
            client = LLMClient(models=models)
            print(f"   ✅ 创建客户端成功，当前模型: {client.model}")
            
            # 测试API调用
            messages = [
                {"role": "system", "content": "你是一个有用的助手。"},
                {"role": "user", "content": "请简单回复'测试成功'"}
            ]
            
            response = client.chat(messages)
            print(f"   ✅ API调用成功，响应: {response}")
            break  # 如果成功就停止测试
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            continue

def main():
    """主函数"""
    print("🚀 开始测试API密钥配置...\n")
    
    # 测试API密钥配置
    test_api_key_config()
    
    # 测试不同模型配置
    test_different_models()
    
    print("\n📊 测试完成！")
    print("\n💡 建议:")
    print("1. 检查 DASHSCOPE_API_KEY 环境变量是否正确设置")
    print("2. 确认API密钥是否有效且未过期")
    print("3. 检查是否有足够的API调用额度")
    print("4. 尝试使用不同的模型")

if __name__ == "__main__":
    main()
