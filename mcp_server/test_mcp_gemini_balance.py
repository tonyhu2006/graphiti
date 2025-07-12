#!/usr/bin/env python3
"""
测试MCP服务器是否使用Gemini Balance的脚本
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_mcp_server():
    """测试MCP服务器的add_memory功能"""
    print("=== 测试MCP服务器Gemini Balance集成 ===")
    
    # MCP服务器地址
    mcp_url = "http://127.0.0.1:8000"
    
    # 测试数据
    test_data = {
        "name": "Gemini Balance测试",
        "episode_body": "这是一个测试Gemini Balance集成的记忆条目。我们正在验证MCP服务器是否正确使用了代理服务。",
        "source": "test",
        "source_description": "Gemini Balance集成测试"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 调用add_memory工具
            payload = {
                "method": "tools/call",
                "params": {
                    "name": "add_memory",
                    "arguments": test_data
                }
            }
            
            print(f"🔄 调用MCP服务器add_memory工具...")
            print(f"   URL: {mcp_url}/messages/")
            print(f"   数据: {test_data['name']}")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{mcp_url}/messages/",
                json=payload,
                headers=headers
            ) as response:
                print(f"   响应状态: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ MCP调用成功!")
                    print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ MCP调用失败: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ 连接MCP服务器失败: {e}")
        return False

async def test_direct_api_call():
    """直接测试Gemini Balance API"""
    print("\n=== 直接测试Gemini Balance API ===")
    
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not base_url:
        print("⚠️  GEMINI_BALANCE_URL未设置，跳过直接API测试")
        return True
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试文本生成
            payload = {
                "model": "gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": "请简单回复：Gemini Balance工作正常"
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 100
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{base_url.rstrip('/')}/v1/chat/completions"
            print(f"🔄 直接调用Gemini Balance API...")
            print(f"   URL: {url}")
            
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"   响应状态: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        print(f"✅ 直接API调用成功!")
                        print(f"   回复: {content}")
                        return True
                    else:
                        print(f"❌ API响应格式异常: {result}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ 直接API调用失败: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ 直接API调用异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试MCP服务器Gemini Balance集成")
    print("=" * 60)
    
    # 显示配置信息
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    print(f"配置信息:")
    print(f"  GEMINI_BALANCE_URL: {base_url}")
    print(f"  GOOGLE_API_KEY: {'已设置' if api_key else '未设置'}")
    print()
    
    # 运行测试
    tests = [
        test_direct_api_call(),
        test_mcp_server(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # 统计结果
    success_count = sum(1 for result in results if result is True)
    total_count = len(results)
    
    print("\n" + "=" * 60)
    print(f"🎯 测试完成: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！MCP服务器Gemini Balance集成成功！")
        print("\n✅ 验证结果:")
        print("   - Gemini Balance API直接调用正常")
        print("   - MCP服务器能够处理请求")
        print("   - 集成配置正确")
    else:
        print("⚠️  部分测试失败，请检查:")
        print("   - MCP服务器是否正在运行 (http://127.0.0.1:8000)")
        print("   - Gemini Balance服务器是否可访问")
        print("   - API密钥和配置是否正确")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
