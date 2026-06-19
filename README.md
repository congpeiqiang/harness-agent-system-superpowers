# FecMall 智能客服系统

基于 LangGraph 构建的多 Agent 智能客服系统，为 FecMall 电商平台提供自动化客户服务，支持商品查询、订单管理、售后服务、天气查询等多场景对话能力。

## ✨ 核心特性

- **多 Agent 协作**：Supervisor 模式调度商品、订单、售后、用户、通用五个专业 Agent
- **MCP 工具集成**：通过 Model Context Protocol 接入天气查询等外部服务
- **双层记忆系统**：短期对话记忆 + 长期用户画像，实现上下文连贯的个性化服务
- **RAG 知识库检索**：基于 Milvus 向量数据库，支持 FAQ 和政策法规的语义检索
- **技能注册系统**：可扩展的 Skill 框架，内置货币换算等技能，支持热加载
- **可观测性**：集成 LangSmith 追踪、结构化日志、Prometheus 指标
- **流式响应**：SSE 流式输出，支持 Human-in-the-Loop 人工介入机制
- **Docker 部署**：完整的容器化部署方案，一键启动全套服务

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Milvus 2.4+（向量数据库）
- FecMall API 服务（后端电商平台）

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd harness-agent-system-superpowers

# 安装依赖
pip install -r requirements.txt

# 复制并编辑配置文件
cp config/settings.yaml config/settings.local.yaml
# 按需修改 settings.local.yaml 中的 API Key 和服务地址
```

### 配置

在 `config/settings.yaml` 中配置以下关键参数：

```yaml
llm:
  default_provider: deepseek
  providers:
    deepseek:
      base_url: https://api.deepseek.com
      api_key: your-deepseek-key
      model: deepseek-chat

fecmall:
  base_url: http://your-fecmall-server/appserver

milvus:
  uri: http://localhost:19530
  collection_name: fecmall_knowledge
```

或通过环境变量覆盖：

```bash
export DEEPSEEK_API_KEY=your-key
export MILVUS_URI=http://localhost:19530
export FECMALL_BASE_URL=http://your-server/appserver
export WEATHER_API_KEY=your-openweathermap-key
export LANGSMITH_API_KEY=your-langsmith-key
```

### 启动

```bash
# 启动主服务
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 或同时启动 MCP 天气服务
uvicorn src.mcp.server.weather_server:starlette_app --host 0.0.0.0 --port 8001
```

启动后访问：
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

## 🐳 Docker 部署

使用 Docker Compose 一键部署全套服务：

```bash
cd docker

# 设置环境变量（或创建 .env 文件）
export DEEPSEEK_API_KEY=your-key
export WEATHER_API_KEY=your-key

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f agent-server

# 停止服务
docker compose down
```

Docker Compose 包含以下服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| agent-server | 8000 | 主 Agent 服务（FastAPI） |
| weather-mcp | 8001 | 天气 MCP Server（SSE） |
| milvus-standalone | 19530 | Milvus 向量数据库 |
| milvus-minio | 9001 | Milvus 对象存储 |
| milvus-etcd | 2379 | Milvus 元数据存储 |

## 📡 API 文档

启动服务后访问 http://localhost:8000/docs 查看交互式 API 文档。

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat` | 同步对话 |
| POST | `/api/v1/chat/stream` | 流式对话（SSE） |
| POST | `/api/v1/chat/{session_id}/approve` | 审批工具调用 |
| POST | `/api/v1/sessions` | 创建会话 |
| GET | `/api/v1/sessions/{id}/history` | 查询会话历史 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |
| GET | `/api/v1/health` | 健康检查 |
| GET | `/api/v1/metrics` | 系统指标 |
| GET | `/api/v1/skills` | 技能列表 |
| POST | `/api/v1/skills/reload` | 重新加载技能 |

## 🏗️ 项目结构

```
.
├── config/
│   └── settings.yaml            # 应用配置
├── docker/
│   ├── Dockerfile               # 主服务镜像
│   ├── Dockerfile.mcp           # MCP 服务镜像
│   └── docker-compose.yml       # 全套服务编排
├── knowledge_base/
│   ├── faq/                     # FAQ 知识库文档
│   └── policies/                # 政策法规文档
├── src/
│   ├── agents/                  # Agent 定义
│   │   ├── supervisor.py        # Supervisor 调度器
│   │   ├── product_agent.py     # 商品 Agent
│   │   ├── order_agent.py       # 订单 Agent
│   │   ├── aftersale_agent.py   # 售后 Agent
│   │   ├── user_agent.py        # 用户 Agent
│   │   ├── general_agent.py     # 通用 Agent
│   │   └── middleware/          # Agent 中间件（PII 过滤等）
│   ├── api/                     # FastAPI 路由
│   │   ├── chat.py              # 对话接口
│   │   ├── sessions.py          # 会话管理
│   │   ├── health.py            # 健康检查
│   │   └── schemas.py           # Pydantic 数据模型
│   ├── config/                  # 配置管理
│   │   ├── settings.py          # Pydantic Settings
│   │   └── llm_factory.py       # LLM Provider 工厂
│   ├── mcp/                     # MCP 集成
│   │   ├── client/              # MCP 客户端
│   │   └── server/              # MCP 服务端（天气）
│   ├── memory/                  # 记忆管理
│   │   ├── memory_manager.py    # 双层记忆管理
│   │   └── user_profile.py      # 用户画像
│   ├── observability/           # 可观测性
│   │   ├── langsmith_setup.py   # LangSmith 集成
│   │   ├── logging.py           # 结构化日志
│   │   ├── metrics.py           # Prometheus 指标
│   │   └── tracing.py           # 分布式追踪
│   ├── rag/                     # RAG 检索
│   │   ├── retriever.py         # 检索器
│   │   ├── embeddings.py        # Embedding 生成
│   │   ├── milvus_client.py     # Milvus 客户端
│   │   └── loader.py            # 文档加载器
│   ├── skills/                  # 技能系统
│   │   ├── registry.py          # 技能注册中心
│   │   ├── loader.py            # 技能加载器
│   │   └── builtin/             # 内置技能
│   ├── tools/                   # 工具集
│   │   ├── fecmall/             # FecMall API 工具
│   │   └── rag_tools.py         # RAG 检索工具
│   └── main.py                  # FastAPI 应用入口
└── tests/                       # 测试用例
```

## 🧪 测试

```bash
# 运行全部测试
pytest

# 运行特定模块测试
pytest tests/test_agents.py -v
```

## 📄 许可证

MIT License
