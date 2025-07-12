#!/usr/bin/env python3
"""
检查Neo4j数据库中的Graphiti数据
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# 加载环境变量
load_dotenv()

def check_neo4j_data():
    """检查Neo4j数据库中的数据"""
    print("🔍 检查Neo4j数据库中的Graphiti数据")
    print("=" * 60)
    
    # 连接配置
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD')
    database = os.environ.get('NEO4J_DATABASE', 'neo4j')
    
    print(f"连接到: {uri} (数据库: {database})")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # 1. 检查所有节点类型
            print("\n📊 节点统计:")
            result = session.run("""
                MATCH (n) 
                RETURN labels(n) as labels, count(n) as count 
                ORDER BY count DESC
            """)
            
            for record in result:
                labels = record['labels']
                count = record['count']
                print(f"   {labels}: {count} 个节点")
            
            # 2. 检查Episodic节点详情
            print("\n📝 Episode详情:")
            result = session.run("""
                MATCH (n:Episodic) 
                RETURN n.name as name, 
                       n.content as content, 
                       n.source as source,
                       n.group_id as group_id,
                       n.created_at as created_at
                ORDER BY n.created_at DESC
            """)
            
            episodes = list(result)
            if episodes:
                for i, record in enumerate(episodes, 1):
                    print(f"\n   Episode {i}:")
                    print(f"     名称: {record['name']}")
                    print(f"     来源: {record['source']}")
                    print(f"     组ID: {record['group_id']}")
                    print(f"     时间: {record['created_at']}")
                    print(f"     内容: {record['content'][:100]}...")
            else:
                print("   ❌ 没有找到Episode节点")
            
            # 3. 检查Entity节点详情
            print(f"\n🏷️  Entity详情:")
            result = session.run("""
                MATCH (n:Entity) 
                RETURN n.name as name, 
                       n.entity_type as entity_type,
                       n.summary as summary,
                       n.group_id as group_id,
                       n.created_at as created_at
                ORDER BY n.created_at DESC
                LIMIT 10
            """)
            
            entities = list(result)
            if entities:
                for i, record in enumerate(entities, 1):
                    print(f"\n   Entity {i}:")
                    print(f"     名称: {record['name']}")
                    print(f"     类型: {record['entity_type']}")
                    print(f"     组ID: {record['group_id']}")
                    print(f"     时间: {record['created_at']}")
                    if record['summary']:
                        print(f"     摘要: {record['summary'][:80]}...")
            else:
                print("   ❌ 没有找到Entity节点")
            
            # 4. 检查关系
            print(f"\n🔗 关系统计:")
            result = session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) as rel_type, count(r) as count 
                ORDER BY count DESC
            """)
            
            for record in result:
                rel_type = record['rel_type']
                count = record['count']
                print(f"   {rel_type}: {count} 个关系")
            
            # 5. 检查最新的数据（按group_id）
            print(f"\n📅 按组ID分组的最新数据:")
            result = session.run("""
                MATCH (n:Episodic) 
                WITH n.group_id as group_id, max(n.created_at) as latest_time, count(n) as episode_count
                RETURN group_id, latest_time, episode_count
                ORDER BY latest_time DESC
            """)
            
            for record in result:
                group_id = record['group_id']
                latest_time = record['latest_time']
                episode_count = record['episode_count']
                print(f"   组 '{group_id}': {episode_count} episodes, 最新: {latest_time}")
            
            # 6. 搜索特定内容
            print(f"\n🔍 搜索包含'技术'的内容:")
            result = session.run("""
                MATCH (n:Episodic) 
                WHERE n.name CONTAINS '技术' OR n.content CONTAINS '技术'
                RETURN n.name as name, n.content as content
                ORDER BY n.created_at DESC
                LIMIT 5
            """)
            
            for record in result:
                name = record['name']
                content = record['content']
                print(f"   📄 {name}")
                print(f"      {content[:100]}...")
        
        driver.close()
        print(f"\n✅ 数据检查完成")
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def suggest_queries():
    """建议一些有用的Neo4j查询"""
    print(f"\n💡 建议的Neo4j查询语句:")
    print(f"=" * 60)
    
    queries = [
        ("查看所有Episode", "MATCH (n:Episodic) RETURN n.name, n.created_at ORDER BY n.created_at DESC"),
        ("查看所有Entity", "MATCH (n:Entity) RETURN n.name, n.entity_type, n.created_at ORDER BY n.created_at DESC"),
        ("查看节点统计", "MATCH (n) RETURN labels(n), count(n) ORDER BY count(n) DESC"),
        ("查看关系统计", "MATCH ()-[r]->() RETURN type(r), count(r) ORDER BY count(r) DESC"),
        ("查看特定组的数据", "MATCH (n) WHERE n.group_id = 'default' RETURN labels(n), count(n)"),
        ("搜索内容", "MATCH (n:Episodic) WHERE n.content CONTAINS '技术' RETURN n.name, n.content"),
        ("查看图结构", "MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20"),
    ]
    
    for i, (desc, query) in enumerate(queries, 1):
        print(f"\n{i}. {desc}:")
        print(f"   {query}")

if __name__ == "__main__":
    success = check_neo4j_data()
    if success:
        suggest_queries()
    else:
        print("请检查Neo4j连接配置")
