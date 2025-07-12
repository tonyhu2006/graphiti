# Graphiti与Gemini Balance集成指南

本文档说明如何在Graphiti中集成Gemini Balance代理服务，以实现负载均衡、速率限制管理和API请求优化。

## 什么是Gemini Balance

[Gemini Balance](https://github.com/snailyp/gemini-balance) 是一个Google Gemini API的代理和负载均衡服务，提供以下功能：

- **多密钥负载均衡**：支持配置多个Gemini API密钥进行自动轮询
- **OpenAI兼容API**：提供OpenAI格式的API端点，便于集成
- **速率限制管理**：自动处理API速率限制，避免429错误
- **实时监控**：提供密钥状态监控和使用统计
- **故障重试**：自动处理API请求失败和重试

## 配置步骤

### 1. 环境变量配置

在`.env`文件中添加Gemini Balance配置：

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your_gemini_balance_access_token
MODEL_NAME=gemini-2.5-flash
EMBEDDER_MODEL_NAME=embedding-001

# Gemini Balance代理配置
GEMINI_BALANCE_URL=http://localhost:8000
```

**重要说明：**
- `GOOGLE_API_KEY`：这里应该设置Gemini Balance的访问密码，而不是Google API密钥
- `GEMINI_BALANCE_URL`：您的Gemini Balance服务器地址

### 2. 验证配置

运行测试脚本验证配置：

```bash
cd mcp_server
python test_gemini_balance.py
```

成功输出应该显示：
```
✅ 使用Gemini Balance代理: http://localhost:8000
✅ GeminiClient创建成功
✅ 文本生成成功
✅ GeminiEmbedder创建成功
✅ 单个嵌入成功
✅ 批量嵌入成功
```

### 3. 运行MCP服务器

```bash
uv run graphiti_mcp_server.py --model gemini-2.5-flash --transport sse
```

成功启动时应该看到：
```
Using Gemini model: gemini-2.5-flash
Using Gemini embedder: embedding-001
Graphiti client initialized successfully
MCP server running on http://127.0.0.1:8000
```

## 技术实现

### LLM客户端集成

Graphiti的`GeminiClient`已经扩展支持自定义端点：

```python
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.config import LLMConfig

# 使用Gemini Balance
config = LLMConfig(
    api_key="your_balance_access_token",
    model="gemini-2.5-flash",
    base_url="http://localhost:8000"  # Gemini Balance URL
)

client = GeminiClient(config=config)
```

### 嵌入客户端集成

`GeminiEmbedder`同样支持自定义端点：

```python
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

# 使用Gemini Balance
config = GeminiEmbedderConfig(
    api_key="your_balance_access_token",
    embedding_model="embedding-001",
    base_url="http://localhost:8000"
)

embedder = GeminiEmbedder(config=config)
```

### 自动检测机制

当设置了`base_url`时，客户端会：

1. **自动切换到OpenAI兼容模式**：使用OpenAI格式的API调用
2. **转换消息格式**：将Graphiti消息格式转换为OpenAI格式
3. **处理响应**：将OpenAI格式响应转换回Graphiti格式
4. **保持兼容性**：对上层应用完全透明

## 优势对比

### 使用Gemini Balance的优势

| 功能 | 直接Gemini API | Gemini Balance |
|------|----------------|----------------|
| 负载均衡 | ❌ | ✅ 多密钥轮询 |
| 速率限制处理 | ❌ 需要手动处理 | ✅ 自动管理 |
| 故障重试 | ❌ 需要自己实现 | ✅ 内置重试机制 |
| 监控统计 | ❌ | ✅ 实时监控面板 |
| 成本优化 | ❌ | ✅ 智能路由 |
| 网络稳定性 | ❌ 依赖网络 | ✅ 代理服务器 |

### 性能对比

- **延迟**：Gemini Balance增加约10-50ms延迟（可接受）
- **吞吐量**：通过负载均衡可以显著提高
- **可靠性**：故障重试和多密钥提高可用性
- **成本**：智能路由可以降低API使用成本

## 故障排除

### 1. 连接失败

```bash
❌ API call failed with status 403: Forbidden
```

**解决方案**：
- 检查`GOOGLE_API_KEY`是否设置为正确的Gemini Balance访问密码
- 确认Gemini Balance服务器地址正确

### 2. 模型不支持

```bash
❌ Model not found: gemini-2.5-flash
```

**解决方案**：
- 检查Gemini Balance服务器是否配置了该模型
- 尝试使用其他支持的模型名称

### 3. 网络超时

```bash
❌ Request timeout
```

**解决方案**：
- 检查网络连接到Gemini Balance服务器
- 增加超时时间设置
- 检查防火墙设置

### 4. 嵌入API失败

```bash
❌ Embedding API call failed
```

**解决方案**：
- 确认Gemini Balance支持嵌入API
- 检查嵌入模型名称是否正确
- 验证API密钥权限

## 高级配置

### 自定义超时

```python
# 在LLMConfig中设置自定义超时
config = LLMConfig(
    api_key="your_token",
    model="gemini-2.5-flash",
    base_url="http://localhost:8000",
    # 注意：超时设置需要在HTTP客户端层面配置
)
```

### 并发控制

```env
# 调整并发限制以适应Gemini Balance
SEMAPHORE_LIMIT=5
```

### 日志配置

```env
# 启用详细日志以调试连接问题
LOG_LEVEL=DEBUG
```

## 最佳实践

1. **监控使用情况**：定期检查Gemini Balance的监控面板
2. **合理设置并发**：根据服务器性能调整`SEMAPHORE_LIMIT`
3. **备用方案**：保留直接API配置作为备用
4. **定期测试**：使用测试脚本验证服务可用性
5. **安全考虑**：保护好Gemini Balance的访问密码

## 支持和反馈

如果遇到问题：

1. 首先运行测试脚本诊断问题
2. 检查Gemini Balance服务器状态
3. 查看MCP服务器日志
4. 参考Gemini Balance官方文档

---

**🎉 恭喜！您现在可以通过Gemini Balance享受更稳定、更高效的Gemini API服务了！**
