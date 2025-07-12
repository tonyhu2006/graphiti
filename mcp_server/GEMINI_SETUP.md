# Graphiti MCP Server with Google Gemini

本文档说明如何配置Graphiti MCP服务器使用Google Gemini模型。

## 问题解决

您遇到的错误是因为MCP服务器原本只支持OpenAI模型，现在已经修改为支持Google Gemini。

## 前置要求

1. **安装Gemini支持**：
   ```bash
   pip install "graphiti-core[google-genai]"
   ```

2. **获取Google API密钥**：
   - 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
   - 创建新的API密钥
   - 保存密钥以备使用

3. **Neo4j数据库**：
   - 确保Neo4j正在运行
   - 默认连接：`bolt://localhost:7687`

## 环境变量设置

### 方法1：使用环境变量

```bash
# 设置Google API密钥
export GOOGLE_API_KEY=your_actual_google_api_key

# 设置Neo4j连接参数
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password

# 设置嵌入模型（可选）
export EMBEDDER_MODEL_NAME=embedding-001
```

### 方法2：使用PowerShell脚本

编辑 `run_gemini_mcp.ps1` 文件，将 `YOUR_GOOGLE_API_KEY` 替换为您的实际API密钥，然后运行：

```powershell
.\run_gemini_mcp.ps1
```

## 运行MCP服务器

### 基本命令

```bash
uv run graphiti_mcp_server.py --model gemini-2.5-flash --transport sse
```

### 完整配置示例

```bash
uv run graphiti_mcp_server.py \
  --model gemini-2.5-flash \
  --small-model gemini-2.5-flash-lite-preview-06-17 \
  --transport sse \
  --temperature 0.0
```

## 支持的Gemini模型

### LLM模型
- `gemini-2.5-flash` (推荐)
- `gemini-2.0-flash`
- `gemini-1.5-pro`

### 嵌入模型
- `embedding-001` (默认)

### 重排序模型
- `gemini-2.0-flash-exp` (自动使用)

## 验证配置

运行测试脚本验证配置：

```bash
python test_gemini.py
```

成功输出应该显示：
- ✓ Gemini模型检测正常
- ✓ API密钥检测正常
- ✓ LLM客户端创建成功
- ✓ 嵌入客户端创建成功

## 故障排除

### 1. "Gemini support not available" 错误
```bash
pip install "graphiti-core[google-genai]"
```

### 2. "GOOGLE_API_KEY must be set" 错误
确保设置了正确的环境变量：
```bash
echo $GOOGLE_API_KEY  # Linux/Mac
echo $env:GOOGLE_API_KEY  # PowerShell
```

### 3. Neo4j连接错误
确保Neo4j正在运行并检查连接参数：
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_neo4j_password
```

## 配置文件示例

创建 `.env` 文件：

```env
# Google Gemini配置
GOOGLE_API_KEY=your_actual_google_api_key
MODEL_NAME=gemini-2.5-flash
EMBEDDER_MODEL_NAME=embedding-001

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 其他设置
LLM_TEMPERATURE=0.0
SEMAPHORE_LIMIT=10
```

## 性能优化

1. **并发限制**：调整 `SEMAPHORE_LIMIT` 环境变量
2. **温度设置**：使用较低的温度值（0.0-0.3）获得更确定性的输出
3. **模型选择**：
   - 使用 `gemini-2.5-flash` 获得最佳性能
   - 使用 `gemini-2.5-flash-lite-preview-06-17` 作为小模型

## 日志输出

成功启动时应该看到：
```
Using Gemini model: gemini-2.5-flash
Using temperature: 0.0
Using Gemini embedder: embedding-001
Using Gemini cross encoder for reranking
Graphiti client initialized successfully
```

## 下一步

配置成功后，您可以：
1. 在Claude Desktop或其他MCP客户端中使用Graphiti
2. 添加episodes到知识图谱
3. 执行语义搜索
4. 管理实体和关系

有关更多信息，请参考 [Graphiti文档](https://help.getzep.com/graphiti/)。
