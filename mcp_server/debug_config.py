#!/usr/bin/env python3
"""
调试配置传递的脚本
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径的最前面，确保使用本地开发版本
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(f"DEBUG: 项目根目录: {project_root}")
print(f"DEBUG: Python路径: {sys.path[:3]}")  # 显示前3个路径

# 强制重新加载模块
import importlib
import graphiti_core.llm_client.gemini_client
import graphiti_core.llm_client.config
importlib.reload(graphiti_core.llm_client.gemini_client)
importlib.reload(graphiti_core.llm_client.config)

from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.config import LLMConfig

# 加载环境变量
load_dotenv()

def debug_config():
    """调试配置传递"""
    print("=== 调试配置传递 ===")
    
    # 获取环境变量
    api_key = os.environ.get('GOOGLE_API_KEY')
    base_url = os.environ.get('GEMINI_BALANCE_URL')
    
    print(f"环境变量:")
    print(f"  GOOGLE_API_KEY: {'已设置' if api_key else '未设置'}")
    print(f"  GEMINI_BALANCE_URL: {base_url}")
    
    # 创建LLMConfig
    config = LLMConfig(
        api_key=api_key,
        model="gemini-2.5-flash",
        base_url=base_url
    )
    
    print(f"\nLLMConfig:")
    print(f"  api_key: {'已设置' if config.api_key else '未设置'}")
    print(f"  model: {config.model}")
    print(f"  base_url: {config.base_url}")
    
    # 创建GeminiClient
    print(f"\n创建GeminiClient...")
    client = GeminiClient(config=config)
    print(f"GeminiClient创建完成")

    print(f"\nGeminiClient:")
    print(f"  model: {client.model}")
    print(f"  base_url: {getattr(client, 'base_url', 'NOT_SET')}")
    print(f"  use_custom_endpoint: {getattr(client, 'use_custom_endpoint', 'NOT_SET')}")
    print(f"  config.base_url: {client.config.base_url}")

    # 检查所有属性
    print(f"\n所有属性:")
    for attr in dir(client):
        if not attr.startswith('_'):
            try:
                value = getattr(client, attr)
                if not callable(value):
                    print(f"  {attr}: {value}")
            except:
                pass
    
    # 检查条件
    print(f"\n条件检查:")
    print(f"  config.base_url is not None: {config.base_url is not None}")
    print(f"  bool(config.base_url): {bool(config.base_url)}")
    print(f"  config.base_url == '': {config.base_url == ''}")
    
    return client

if __name__ == "__main__":
    debug_config()
