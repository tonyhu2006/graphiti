#!/usr/bin/env python3
"""
诊断Neo4j连接和数据状态的脚本
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from neo4j import GraphDatabase
from graphiti_core.graphiti import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

# 加载环境变量
load_dotenv()

def test_neo4j_connection():
    """测试Neo4j连接"""
    print("=== 测试Neo4j连接 ===")
    
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD')
    database = os.environ.get('NEO4J_DATABASE', 'neo4j')
    
    print(f"连接信息:")
    print(f"  URI: {uri}")
    print(f"  用户: {user}")
    print(f"  数据库: {database}")
    print(f"  密码: {'已设置' if password else '未设置'}")
    
    try:
        # 创建驱动
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 测试连接
        with driver.session(database=database) as session:
            result = session.run("RETURN 'Neo4j连接成功' as message")
            record = result.single()
            print(f"✅ {record['message']}")
            
            # 检查数据库版本
            result = session.run("CALL dbms.components() YIELD name, versions")
            for record in result:
                if record['name'] == 'Neo4j Kernel':
                    print(f"   Neo4j版本: {record['versions'][0]}")
            
            # 检查现有数据
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()['node_count']
            print(f"   节点总数: {node_count}")
            
            # 检查Graphiti相关的节点
            result = session.run("MATCH (n:Entity) RETURN count(n) as entity_count")
            entity_count = result.single()['entity_count']
            print(f"   Entity节点数: {entity_count}")
            
            result = session.run("MATCH (n:Episodic) RETURN count(n) as episode_count")
            episode_count = result.single()['episode_count']
            print(f"   Episodic节点数: {episode_count}")
            
            # 检查最近的数据
            result = session.run("""
                MATCH (n:Episodic) 
                RETURN n.name as name, n.created_at as created_at, n.group_id as group_id
                ORDER BY n.created_at DESC 
                LIMIT 5
            """)
            
            print(f"\n   最近的Episodes:")
            for record in result:
                print(f"     - {record['name']} (group: {record['group_id']}, 时间: {record['created_at']})")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j连接失败: {e}")
        return False

async def test_graphiti_client():
    """测试Graphiti客户端"""
    print("\n=== 测试Graphiti客户端 ===")
    
    try:
        # 获取配置
        neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        neo4j_password = os.environ.get('NEO4J_PASSWORD')
        neo4j_database = os.environ.get('NEO4J_DATABASE', 'neo4j')
        
        api_key = os.environ.get('GOOGLE_API_KEY')
        base_url = os.environ.get('GEMINI_BALANCE_URL')
        
        # 创建LLM客户端
        llm_config = LLMConfig(
            api_key=api_key,
            model="gemini-2.5-flash",
            base_url=base_url
        )
        llm_client = GeminiClient(config=llm_config)
        
        # 创建嵌入客户端
        embedder_config = GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model="embedding-001",
            base_url=base_url
        )
        embedder = GeminiEmbedder(config=embedder_config)
        
        print(f"✅ 客户端创建成功")
        print(f"   LLM使用自定义端点: {getattr(llm_client, 'use_custom_endpoint', False)}")
        print(f"   嵌入使用自定义端点: {getattr(embedder, 'use_custom_endpoint', False)}")
        
        # 创建Graphiti实例
        graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            llm_client=llm_client,
            embedder=embedder
        )
        
        print(f"✅ Graphiti实例创建成功")
        
        # 测试添加一个简单的episode
        print(f"\n🔄 测试添加episode...")
        
        episode_name = "Neo4j诊断测试"
        episode_content = "这是一个用于诊断Neo4j连接和数据保存的测试episode。"
        
        await graphiti.add_episode(
            name=episode_name,
            episode_body=episode_content,
            source="diagnostic_test"
        )
        
        print(f"✅ Episode添加完成")
        
        # 验证数据是否保存
        print(f"\n🔄 验证数据保存...")
        
        # 直接查询数据库
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session(database=neo4j_database) as session:
            result = session.run("""
                MATCH (n:Episodic) 
                WHERE n.name CONTAINS $name
                RETURN n.name as name, n.content as content, n.created_at as created_at
                ORDER BY n.created_at DESC
                LIMIT 1
            """, name=episode_name)
            
            record = result.single()
            if record:
                print(f"✅ 数据保存成功!")
                print(f"   名称: {record['name']}")
                print(f"   内容: {record['content'][:50]}...")
                print(f"   时间: {record['created_at']}")
                return True
            else:
                print(f"❌ 数据未找到")
                return False
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Graphiti测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主诊断函数"""
    print("🔍 开始诊断Neo4j连接和数据状态")
    print("=" * 60)
    
    # 显示环境变量
    print(f"环境变量:")
    print(f"  NEO4J_URI: {os.environ.get('NEO4J_URI')}")
    print(f"  NEO4J_DATABASE: {os.environ.get('NEO4J_DATABASE')}")
    print(f"  GEMINI_BALANCE_URL: {os.environ.get('GEMINI_BALANCE_URL')}")
    print()
    
    # 运行测试
    neo4j_ok = test_neo4j_connection()
    graphiti_ok = await test_graphiti_client()
    
    print("\n" + "=" * 60)
    print(f"🎯 诊断结果:")
    print(f"   Neo4j连接: {'✅ 正常' if neo4j_ok else '❌ 失败'}")
    print(f"   Graphiti功能: {'✅ 正常' if graphiti_ok else '❌ 失败'}")
    
    if neo4j_ok and graphiti_ok:
        print("\n🎉 所有测试通过！Neo4j和Graphiti工作正常！")
    else:
        print("\n⚠️  发现问题，请检查配置和连接")
    
    return neo4j_ok and graphiti_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
