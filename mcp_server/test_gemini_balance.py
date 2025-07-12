#!/usr/bin/env python3
"""
测试Gemini Balance集成的脚本
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径的最前面，确保使用本地开发版本
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.prompts.models import Message

# 加载环境变量
load_dotenv()

async def test_gemini_balance_llm():
    """测试Gemini Balance LLM客户端"""
    print("=== 测试Gemini Balance LLM客户端 ===")
    
    # 获取配置
    api_key = os.environ.get('GOOGLE_API_KEY')
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    
    if not api_key:
        print("❌ GOOGLE_API_KEY未设置")
        return False
    
    if not base_url:
        print("⚠️  GEMINI_BALANCE_URL未设置，将使用直接Gemini API")
        base_url = None
    else:
        print(f"✅ 使用Gemini Balance代理: {base_url}")
    
    try:
        # 创建LLM客户端
        config = LLMConfig(
            api_key=api_key,
            model="gemini-2.5-flash",
            base_url=base_url
        )
        
        client = GeminiClient(config=config)
        print(f"✅ GeminiClient创建成功")
        print(f"   - 模型: {client.model}")
        print(f"   - 使用自定义端点: {getattr(client, 'use_custom_endpoint', False)}")
        print(f"   - Base URL: {getattr(client, 'base_url', None)}")
        
        # 测试简单的文本生成
        messages = [
            Message(role="user", content="请用一句话介绍什么是人工智能。")
        ]
        
        print("\n🔄 测试文本生成...")
        response = await client.generate_response(messages)
        
        if response and 'content' in response:
            print(f"✅ 文本生成成功:")
            print(f"   回复: {response['content'][:100]}...")
            return True
        else:
            print(f"❌ 文本生成失败: {response}")
            return False
            
    except Exception as e:
        print(f"❌ LLM测试失败: {e}")
        return False

async def test_gemini_balance_embedder():
    """测试Gemini Balance嵌入客户端"""
    print("\n=== 测试Gemini Balance嵌入客户端 ===")
    
    # 获取配置
    api_key = os.environ.get('GOOGLE_API_KEY')
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    
    try:
        # 创建嵌入客户端
        config = GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model="embedding-001",
            base_url=base_url
        )
        
        embedder = GeminiEmbedder(config=config)
        print(f"✅ GeminiEmbedder创建成功")
        print(f"   - 模型: {embedder.config.embedding_model}")
        print(f"   - 使用自定义端点: {getattr(embedder, 'use_custom_endpoint', False)}")
        print(f"   - Base URL: {getattr(embedder, 'base_url', None)}")
        
        # 测试单个文本嵌入
        print("\n🔄 测试单个文本嵌入...")
        text = "这是一个测试文本"
        embedding = await embedder.create(text)
        
        if embedding and len(embedding) > 0:
            print(f"✅ 单个嵌入成功:")
            print(f"   维度: {len(embedding)}")
            print(f"   前5个值: {embedding[:5]}")
        else:
            print(f"❌ 单个嵌入失败")
            return False
        
        # 测试批量嵌入
        print("\n🔄 测试批量嵌入...")
        texts = ["文本1", "文本2", "文本3"]
        embeddings = await embedder.create_batch(texts)
        
        if embeddings and len(embeddings) == len(texts):
            print(f"✅ 批量嵌入成功:")
            print(f"   数量: {len(embeddings)}")
            print(f"   每个维度: {len(embeddings[0])}")
            return True
        else:
            print(f"❌ 批量嵌入失败")
            return False
            
    except Exception as e:
        print(f"❌ 嵌入测试失败: {e}")
        return False

async def test_direct_api_comparison():
    """比较直接API和Gemini Balance的响应"""
    print("\n=== 比较直接API和Gemini Balance ===")
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    
    if not base_url:
        print("⚠️  跳过比较测试，因为GEMINI_BALANCE_URL未设置")
        return True
    
    try:
        # 直接API客户端
        direct_config = LLMConfig(
            api_key=api_key,
            model="gemini-2.5-flash"
        )
        direct_client = GeminiClient(config=direct_config)
        
        # Gemini Balance客户端
        balance_config = LLMConfig(
            api_key=api_key,
            model="gemini-2.5-flash",
            base_url=base_url
        )
        balance_client = GeminiClient(config=balance_config)
        
        # 测试消息
        messages = [
            Message(role="user", content="请说'Hello World'")
        ]
        
        print("🔄 测试直接API...")
        try:
            direct_response = await direct_client.generate_response(messages)
            print(f"✅ 直接API响应: {direct_response.get('content', '')[:50]}...")
        except Exception as e:
            print(f"❌ 直接API失败: {e}")
            direct_response = None
        
        print("🔄 测试Gemini Balance...")
        try:
            balance_response = await balance_client.generate_response(messages)
            print(f"✅ Gemini Balance响应: {balance_response.get('content', '')[:50]}...")
        except Exception as e:
            print(f"❌ Gemini Balance失败: {e}")
            balance_response = None
        
        if direct_response and balance_response:
            print("✅ 两种方式都成功响应")
            return True
        elif balance_response:
            print("✅ Gemini Balance成功（直接API可能有网络问题）")
            return True
        else:
            print("❌ 两种方式都失败")
            return False
            
    except Exception as e:
        print(f"❌ 比较测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试Gemini Balance集成")
    print("=" * 50)
    
    # 显示配置信息
    api_key = os.environ.get('GOOGLE_API_KEY')
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    
    print(f"API密钥: {'已设置' if api_key else '未设置'}")
    print(f"Gemini Balance URL: {base_url if base_url else '未设置'}")
    print()
    
    # 运行测试
    tests = [
        test_gemini_balance_llm(),
        test_gemini_balance_embedder(),
        test_direct_api_comparison(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # 统计结果
    success_count = sum(1 for result in results if result is True)
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print(f"🎯 测试完成: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！Gemini Balance集成成功！")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
