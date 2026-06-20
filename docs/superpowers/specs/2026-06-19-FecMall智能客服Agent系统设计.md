# FecMall 智能客服 Agent 系统 — 设计规格文档

> 版本: 1.0.0  
> 日期: 2026-06-19  
> 状态: 设计审批中

---

## 1. 项目概述

- 提示词

```python
    开发一个harmess agent应用，一定使用中文回答，
    基于现有FecMall商城系统构建智能客服，同时支持接入外部MCP和Skill，FecMall商城系统的swagger api对应url：https://www.fecmall.com/doc/fecshop-guide/develop/cn-2.0/guide-README.html中"Fecmall Appserver入口"选项内容，基于python3.13、 langchain、fastapi，支持记忆功能使用(使用异步sqlitesaver 和异步sqlitestore)，所有功能尽量使用异步操作，restful服务实现且不仅限异步流式返回astream、ainvoker，可观测性支持langsmith，生成单元测试，实现一个mcp server查询天气，再进你所能设计其他功能，贴近生产级。中文回答，生产的文档名和内容也是中文
```

### 1.1 目标

基于现有 FecMall 商城系统构建生产级智能客服 Agent 系统，支持多 Agent 协作、外部 MCP/Skill 扩展、异步流式响应、会话记忆与用户画像、RAG 知识库检索、全链路可观测。

### 1.2 核心技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 运行时 | Python | 3.13 |
| Web 框架 | FastAPI + Uvicorn | latest |
| Agent 框架 | LangChain + LangGraph | langchain==1.3.10, langgraph>=1.0 |
| LLM | OpenAI 兼容 API（多提供商可切换） | - |
| 持久化 | aiosqlite（异步 SQLite） | latest |
| 向量数据库 | Milvus | v2.4+ |
| MCP 协议 | mcp Python SDK（SSE 传输） | latest |
| HTTP 客户端 | httpx（异步） | latest |
| 配置管理 | pydantic-settings | latest |
| 可观测性 | LangSmith + structlog | latest |

### 1.3 关键依赖

```txt
langchain==1.3.10
langgraph>=1.0
langchain-openai>=0.3
langgraph-checkpoint-sqlite>=3.1
langchain-community>=0.3
langchain-text-splitters
pymilvus
mcp
langchain-mcp-adapters
httpx
aiosqlite
fastapi
uvicorn
pydantic-settings
structlog
python-dotenv
watchdog
```

---

## 2. 架构设计

### 2.1 架构选型：多 Agent 协作架构（方案 A）

采用 Supervisor + 专业 Agent 分发模式，每个 Agent 负责一个业务领域，工具集小（3-8 个），LLM 推理准确率更高。

**优势：**

- 职责清晰，每个 Agent 只负责一个领域
- 可独立迭代和扩展
- 故障隔离——一个 Agent 出问题不影响其他
- 可观测性好——每个 Agent 独立追踪

### 2.2 整体架构图

```
                        ┌─────────────────────────────────────┐
                        │           FastAPI 服务层              │
                        │  /api/chat  /api/stream  /api/sessions│
                        └──────────────┬──────────────────────┘
                                       │
                        ┌──────────────▼──────────────────────┐
                        │        Supervisor Agent (路由)        │
                        │  意图识别 → 分发到专业Agent            │
                        └──┬───┬───┬───┬───┬──────────────────┘
                           │   │   │   │   │
              ┌────────────┤   │   │   │   ├────────────┐
              ▼            ▼   ▼   ▼   ▼   ▼            ▼
        ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
        │ 商品Agent │ │订单   │ │售后   │ │通用   │ │ 用户Agent │
        │ (product)│ │Agent │ │Agent │ │Agent │ │ (user)   │
        └────┬─────┘ └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘
             │          │        │        │           │
             ▼          ▼        ▼        ▼           ▼
        ┌─────────────────────────────────────────────────────┐
        │                   工具层 (Tools)                      │
        │  ┌───────────┐ ┌────────┐ ┌─────┐ ┌──────────────┐  │
        │  │ FecMall   │ │ RAG    │ │ MCP │ │ Skill 插件    │  │
        │  │ API工具集  │ │ 检索   │ │ 工具│ │ (热加载)      │  │
        │  └───────────┘ └────────┘ └─────┘ └──────────────┘  │
        └─────────────────────────────────────────────────────┘
             │                    │         │
        ┌────▼────┐         ┌─────▼───┐ ┌───▼──────────┐
        │FecMall  │         │ Milvus  │ │ 天气MCP      │
        │商城系统  │         │ 向量库  │ │ Server(SSE)  │
        └─────────┘         └─────────┘ └──────────────┘

        ┌─────────────────────────────────────────────────────┐
        │                  持久化层                             │
        │  ┌──────────────────┐  ┌──────────────────────────┐  │
        │  │ AsyncSqliteSaver │  │ SqliteStore              │  │
        │  │ (会话检查点/异步) │  │ (用户画像/长期记忆/异步)  │  │
        │  └──────────────────┘  └──────────────────────────┘  │
        └─────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────┐
        │            中间件层 (LangChain Middleware)            │
        │  Summarization │ HumanInTheLoop │ ToolCallLimit      │
        │  ModelFallback │ PII Detection  │ ToolRetry          │
        │  ModelRetry    │ ChinaPII(自定义)                    │
        └─────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────┐
        │                 可观测性层                            │
        │  LangSmith自动追踪 │ structlog结构化日志 │ 业务指标   │
        └─────────────────────────────────────────────────────┘
```

---

## 3. 项目目录结构

```
harness-agent-system/
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.mcp
│   └── docker-compose.yml
├── docs/
│   └── superpowers/
│       └── specs/
├── config/
│   ├── settings.yaml
│   ├── settings.example.yaml
│   └── logging.yaml
├── knowledge_base/
│   ├── faq/
│   │   ├── 商品相关FAQ.md
│   │   ├── 支付相关FAQ.md
│   │   ├── 配送相关FAQ.md
│   │   └── 账户相关FAQ.md
│   └── policies/
│       ├── 退换货政策.md
│       ├── 隐私政策.md
│       ├── 服务条款.md
│       └── 配送说明.md
├── src/
│   ├── __init__.py
│   ├── main.py                         # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py                     # 对话接口（同步+流式）
│   │   ├── sessions.py                 # 会话管理接口
│   │   ├── health.py                   # 健康检查接口
│   │   ├── stream_parser.py            # SSE 事件解析
│   │   └── schemas.py                  # Pydantic 模型
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py               # Supervisor 路由 Agent
│   │   ├── graph_builder.py            # LangGraph 状态图构建
│   │   ├── base_agent.py               # Agent 基类
│   │   ├── product_agent.py            # 商品 Agent
│   │   ├── order_agent.py              # 订单 Agent
│   │   ├── aftersale_agent.py          # 售后 Agent
│   │   ├── general_agent.py            # 通用 Agent
│   │   ├── user_agent.py               # 用户 Agent
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── custom_pii.py           # 中国PII增强检测
│   │       └── middleware_builder.py   # 中间件栈构建
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── fecmall/
│   │   │   ├── __init__.py
│   │   │   ├── client.py               # FecMall HTTP 客户端
│   │   │   ├── product_tools.py        # 商品工具（5个）
│   │   │   ├── cart_tools.py           # 购物车工具（4个）
│   │   │   ├── order_tools.py          # 订单工具（4个）
│   │   │   ├── customer_tools.py       # 客户工具（7个）
│   │   │   └── aftersale_tools.py      # 售后工具（2个）
│   │   ├── weather_tools.py            # 天气工具（MCP Client）
│   │   └── rag_tools.py               # RAG 检索工具
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server/
│   │   │   ├── __init__.py
│   │   │   └── weather_server.py       # 天气 MCP Server (SSE)
│   │   └── client/
│   │       ├── __init__.py
│   │       └── mcp_client.py           # MCP 客户端管理器
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base_skill.py               # Skill 基类
│   │   ├── loader.py                   # Skill 加载器（热加载）
│   │   ├── registry.py                 # Skill 注册表
│   │   └── builtin/
│   │       ├── __init__.py
│   │       └── currency_convert.py     # 汇率转换 Skill
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── memory_manager.py           # 双层记忆管理
│   │   └── user_profile.py             # 用户画像管理
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py                   # 文档加载器
│   │   ├── embeddings.py               # 向量化服务
│   │   ├── milvus_client.py            # Milvus 客户端
│   │   └── retriever.py               # RAG 检索器
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                 # 配置管理
│   │   └── llm_factory.py             # 多模型工厂
│   └── observability/
│       ├── __init__.py
│       ├── langsmith_setup.py          # LangSmith 初始化
│       ├── logging.py                  # 结构化日志
│       ├── metrics.py                  # 业务指标
│       └── tracing.py                  # 链路追踪
├── tests/
│   ├── unit/
│   └── integration/
├── data/                               # 运行时数据（SQLite数据库）
├── logs/                               # 日志目录
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 4. Agent 核心引擎

### 4.1 LangGraph 状态图

使用 LangGraph 编排多 Agent 协作，通过 `StateGraph` 定义节点和边，`Command` 做路由跳转。

**核心 API（langchain 1.3.10）：**

- Agent 创建：`from langchain.agents import create_agent`
- 工具定义：`from langchain_core.tools import tool`（`@tool` + `async def`）
- 状态图：`from langgraph.graph import StateGraph, END, START`
- 路由：`from langgraph.types import Command`
- 检查点：`from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver`
- 长期存储：`from langgraph.store.sqlite import SqliteStore`

### 4.2 共享状态

```python
class AgentState(TypedDict):
    messages: list          # 对话消息列表
    next_agent: str         # 路由目标
    user_id: str            # 用户ID
    session_id: str         # 会话ID
```

### 4.3 access_token 传递机制

用户的 FecMall `access_token` 通过以下路径传递到工具层：

1. 前端请求 `POST /api/v1/chat` 携带 `access_token` 字段
2. API 层将 `access_token` 注入 `RunnableConfig` 的 `configurable` 字典
3. 工具函数通过 `config: RunnableConfig` 参数获取 `access_token`
4. 工具内部创建 `FecMallClient(access_token=token)` 发起请求

```python
# 工具中获取 access_token 的方式
@tool
async def get_cart(config: RunnableConfig) -> str:
    token = config["configurable"]["access_token"]
    async with FecMallClient(access_token=token) as client:
        ...
```

### 4.4 Supervisor Agent

- 使用 LLM `with_structured_output()` 做意图识别
- 输出 `RouteDecision`（target + reason）
- 通过 `Command(goto=target)` 路由到专业 Agent
- 所有专业 Agent 完成后回到 Supervisor（支持多轮调度）

### 4.5 专业 Agent 一览

| Agent | 职责 | 工具 | 系统 Prompt 要点 |
|-------|------|------|-----------------|
| **ProductAgent** | 商品搜索、详情、分类、评论 | `search_products`, `get_product_detail`, `get_category_products`, `get_product_reviews`, `get_home_info` | 专业导购，引用真实数据 |
| **OrderAgent** | 购物车、下单、支付、订单查询 | `get_cart`, `add_to_cart`, `update_cart_item`, `remove_cart_item`, `submit_order`, `get_order_list`, `get_order_detail`, `get_checkout_init` | 引导购买流程 |
| **AfterSaleAgent** | 退换货、投诉、FAQ | `submit_complaint`, `get_refund_status`, `rag_search` | 优先知识库回答 |
| **UserAgent** | 账户、地址、登录注册 | `login`, `register`, `get_user_profile`, `update_profile`, `get_address_list`, `add_address`, `remove_address` | 安全敏感操作需确认 |
| **GeneralAgent** | 天气、闲聊、Skill 扩展 | `get_weather`, `get_weather_forecast`（MCP），动态 Skill 工具 | 友好闲聊 + 外部能力 |

### 4.6 多模型配置

所有 LLM 提供商使用 OpenAI 兼容 API 格式（`ChatOpenAI`），通过 `base_url` 切换后端。支持按 Agent 覆盖模型配置。

```yaml
llm:
  default_provider: "deepseek"
  providers:
    openai:
      base_url: "https://api.openai.com/v1"
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4o"
      temperature: 0.3
    deepseek:
      base_url: "https://api.deepseek.com/v1"
      api_key: "${DEEPSEEK_API_KEY}"
      model: "deepseek-chat"
      temperature: 0.3
    ollama:
      base_url: "http://localhost:11434/v1"
      api_key: "ollama"
      model: "qwen2.5:14b"
      temperature: 0.3
  agent_overrides:
    supervisor:
      provider: "deepseek"
      model: "deepseek-chat"
```

### 4.7 BaseAgent 基类

所有专业 Agent 继承 `BaseAgent`，提供统一的 `invoke_node` 和 `stream_node` 方法。内部调用 `create_agent(model, tools, prompt, middleware)` 构建 Agent。

---

## 5. 中间件体系

### 5.1 七个必选中间件

中间件通过 `create_agent(middleware=[...])` 注入，按注册顺序执行。

| # | 中间件 | 导入路径 | 钩子位置 | 作用 | 关键参数 |
|---|--------|---------|---------|------|---------|
| 1 | **ModelRetryMiddleware** | `langchain.agents.middleware` | `wrap_model_call` | 模型调用失败时自动重试 | `max_retries=3`, `retry_delay=1.0` |
| 2 | **ModelFallbackMiddleware** | `langchain.agents.middleware` | `wrap_model_call` | 主模型失败后切换备用模型 | `fallback_models=[...]` |
| 3 | **SummarizationMiddleware** | `langchain.agents.middleware` | `before_model` | 对话历史接近 token 上限时自动摘要 | `max_tokens=4000`, `keep_messages=6` |
| 4 | **PIIDetectionMiddleware** | `langchain.agents.middleware` | `before_model` + `after_model` | 脱敏用户输入/Agent 输出中的敏感信息 | `detection_types`, `redaction_strategy="mask"` |
| 5 | **HumanInTheLoopMiddleware** | `langchain.agents.middleware` | `before_tool` | 敏感工具调用前暂停等待人工审批 | `approve_tool_names=[...]` |
| 6 | **ToolRetryMiddleware** | `langchain.agents.middleware` | `wrap_tool_call` | 工具调用失败时指数退避重试 | `max_retries=3`, `backoff_factor=2.0` |
| 7 | **ToolCallLimitMiddleware** | `langchain.agents.middleware` | `after_tool` | 限制工具调用次数防止无限循环 | `run_limit=15`, `thread_limit=100` |

### 5.2 执行顺序

```
用户消息
  → before_model: [PII脱敏] → [对话摘要]
  → wrap_model_call: [模型重试] → [模型回退] → LLM推理
  → before_tool: [人工审批（敏感操作）]
  → wrap_tool_call: [工具重试] → 执行工具
  → after_tool: [调用限制检查]
  → 下一轮 LLM 或返回结果
```

### 5.3 自定义 ChinaPII 中间件

继承 `AgentMiddleware`，在内置 `PIIDetectionMiddleware` 基础上增强中国特有敏感信息检测：
- 手机号：`1[3-9]\d{9}`
- 身份证号：18 位
- 银行卡号：16-19 位

### 5.4 人工审批流程

1. `HumanInTheLoopMiddleware` 在敏感工具调用前暂停 Agent
2. SSE 流中推送 `approval_required` 事件到前端
3. 前端展示确认弹窗
4. 用户选择后调用 `POST /api/v1/chat/{session_id}/approve`
5. 使用 `Command(resume={...})` 恢复 Agent 执行

需审批的工具：`submit_order`, `remove_address`, `remove_cart_item`, `update_profile`

---

## 6. FecMall API 集成

### 6.1 HTTP 客户端

使用 `httpx.AsyncClient` 封装 FecMall Appserver API，支持 `async with` 上下文管理。

请求头：
- `fecshop-currency`: 货币代码
- `fecshop-lang`: 语言代码
- `access-token`: 用户认证 token

### 6.2 API 端点映射

**商品模块** (`product_tools.py` → ProductAgent)：

- `GET /catalogsearch/index/index` → `search_products`
- `GET /catalog/product/index` → `get_product_detail`
- `GET /catalog/category/product` → `get_category_products`
- `GET /catalog/product/reviewlist` → `get_product_reviews`
- `GET /home/index` → `get_home_info`

**购物车模块** (`cart_tools.py` → OrderAgent)：
- `GET /checkout/cart/index` → `get_cart`
- `POST /catalog/product/addtocart` → `add_to_cart`
- `POST /checkout/cart/updateinfo` → `update_cart_item`
- `POST /checkout/cart/updateinfo`（qty=0）→ `remove_cart_item`

**订单模块** (`order_tools.py` → OrderAgent)：
- `POST /checkout/onepage/submitOrder` → `submit_order`
- `GET /customer/order/list` → `get_order_list`
- 订单详情 → `get_order_detail`
- `GET /checkout/onepage/index` → `get_checkout_init`

**客户模块** (`customer_tools.py` → UserAgent)：
- `POST /customer/login` → `login`
- `POST /customer/register` → `register`
- 用户信息 → `get_user_profile` / `update_profile`
- 地址管理 → `get_address_list` / `add_address` / `remove_address`

**售后模块** (`aftersale_tools.py` → AfterSaleAgent)：
- 投诉提交 → `submit_complaint`（组合工具：先通过 `get_order_detail` 验证订单，再通过 RAG 检索退换货政策，生成投诉记录存入本地 SqliteStore）
- 退款状态 → `get_refund_status`（组合工具：通过 `get_order_detail` 查询订单状态字段判断退款进度）

所有工具使用 `@tool` + `async def` 定义，内部通过 `FecMallClient` 发起异步 HTTP 请求。

---

## 7. MCP Server — 天气查询

### 7.1 传输方式

使用 SSE (Server-Sent Events) 传输，基于 Starlette HTTP 服务，独立进程运行在 `port 8001`。

### 7.2 MCP Server 工具

- `get_weather(city)` — 查询指定城市实时天气（温度、湿度、天气状况、风力）
- `get_weather_forecast(city, days)` — 查询未来 N 天天气预报

数据源：OpenWeatherMap API

### 7.3 MCP Client

使用 `langchain-mcp-adapters` 将 MCP 工具转换为 LangChain Tool，供 GeneralAgent 使用。`MCPClientManager` 管理多个 MCP Server 连接的生命周期。

---

## 8. Skill 插件系统

### 8.1 设计

- Skill 作为 Python 模块加载，继承 `BaseSkill` 基类
- 通过 `SkillLoader` 扫描指定目录，动态加载所有 Skill
- `SkillRegistry` 管理已加载 Skill 及其工具
- 支持热加载/卸载（基于 watchdog 文件监控）

### 8.2 BaseSkill 接口

```python
class BaseSkill(ABC):
    name: str
    description: str
    version: str

    def get_tools(self) -> list[BaseTool]: ...
    async def on_load(self): ...
    async def on_unload(self): ...
```

### 8.3 内置 Skill

- `currency_convert` — 货币汇率转换工具

### 8.4 Skill 工具聚合

所有 Skill 的工具通过 `registry.get_all_tools()` 聚合，供 GeneralAgent 使用。

---

## 9. 记忆与持久化

### 9.1 双层记忆架构

| 层次 | 组件 | 作用 | 隔离方式 |
|------|------|------|---------|
| 短期记忆 | `AsyncSqliteSaver`（检查点） | 会话内对话历史、Agent 状态 | `thread_id`（session_id） |
| 长期记忆 | `AsyncSqliteStore` | 用户画像、偏好、跨会话知识 | `namespace`（user_id + 类别） |

### 9.2 导入路径

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.sqlite import AsyncSqliteStore
```

### 9.3 图编译时注入

```python
graph.compile(checkpointer=checkpointer, store=store)
```

### 9.4 用户画像

通过 `AsyncSqliteStore` 存储用户偏好、购物习惯、常用地址等信息。每次对话时加载画像注入 Agent 的 system prompt。

---

## 10. RAG 知识库（Milvus）

### 10.1 架构

```
知识库文档(Markdown) → 文档加载 → 文本切片 → Embedding向量化 → Milvus存储
                                                              ↓
                                              RAG检索工具 → AfterSaleAgent使用
```

### 10.2 Milvus Collection

- Collection 名称：`fecmall_knowledge`
- 字段：`id`（主键自增）、`content`（文本内容）、`source`（文档来源）、`category`（faq/policy）、`embedding`（1536维向量）
- 索引：IVF_FLAT + COSINE 距离

### 10.3 文档结构

```
knowledge_base/
├── faq/           # 常见问题（商品、支付、配送、账户）
└── policies/      # 政策文档（退换货、隐私、服务条款、配送说明）
```

### 10.4 Embedding

使用 OpenAI 兼容 Embedding API（如 `text-embedding-3-small`），通过 `OpenAIEmbeddings` 调用。

### 10.5 RAG 检索工具

`@tool async def rag_search(query, category)` — 从 Milvus 中检索相关文档，供 AfterSaleAgent 使用。

---

## 11. FastAPI REST 服务

### 11.1 API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/v1/chat` | 同步对话（`ainvoke`） |
| `POST` | `/api/v1/chat/stream` | SSE 流式对话（`astream_events`） |
| `POST` | `/api/v1/chat/{session_id}/approve` | 人工审批回调 |
| `GET` | `/api/v1/sessions` | 获取用户会话列表 |
| `POST` | `/api/v1/sessions` | 创建新会话 |
| `GET` | `/api/v1/sessions/{session_id}/history` | 获取会话历史 |
| `DELETE` | `/api/v1/sessions/{session_id}` | 删除会话 |
| `GET` | `/api/v1/skills` | 列出已加载 Skill |
| `POST` | `/api/v1/skills/reload` | 重新加载 Skill |
| `GET` | `/api/v1/health` | 健康检查 |
| `GET` | `/api/v1/metrics` | 运营指标 |

### 11.2 SSE 流式事件类型

| 事件 | 说明 |
|------|------|
| `token` | Agent 生成的文本片段 |
| `tool_start` | 开始调用工具 |
| `tool_end` | 工具调用完成 |
| `agent_switch` | Agent 路由切换 |
| `approval_required` | 需要人工审批 |
| `done` | 响应完成 |
| `error` | 错误信息 |

### 11.3 依赖注入

通过 FastAPI 的 `Depends` + `lifespan` 上下文管理器初始化所有组件（Agent Graph、Memory、MCP、Skill、RAG），注入到路由处理函数。

---

## 12. 可观测性

### 12.1 LangSmith 集成

通过环境变量启用，**零代码**自动追踪所有 LangChain/LangGraph 调用：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_sk_xxx
LANGSMITH_PROJECT=fecmall-agent-production
```

自动追踪内容：
- LLM 调用（input/output/tokens/latency）
- 工具调用（input/output/duration）
- Agent 路由链路（Supervisor → 专业 Agent）
- 中间件事件

### 12.2 自定义增强

- `@traceable` 装饰器标记 Supervisor 路由节点，添加业务元数据（user_id, session_id, route_target）
- `structlog` 结构化日志补充业务指标（PII 脱敏次数、人工审批次数、模型回退次数）

### 12.3 业务指标

```python
@dataclass
class AgentMetrics:
    total_requests: int
    total_tool_calls: int
    agent_route_counts: dict
    avg_response_time_ms: float
    error_count: int
    pii_redaction_count: int
    human_approval_count: int
    model_fallback_count: int
```

---

## 13. 生产部署

### 13.1 Docker Compose 服务

| 服务 | 端口 | 说明 |
|------|------|------|
| `agent-server` | 8000 | 主应用（FastAPI） |
| `weather-mcp` | 8001 | 天气 MCP Server |
| `milvus-standalone` | 19530 | Milvus 向量数据库 |
| `milvus-etcd` | - | Milvus 元数据存储 |
| `milvus-minio` | - | Milvus 对象存储 |

### 13.2 健康检查

`GET /api/v1/health` 返回系统状态：版本、运行时间、LLM 提供商、Milvus 连接状态、MCP 服务状态、活跃 Skill 数量。

### 13.3 配置管理

- `config/settings.yaml` — 主配置文件（LLM、数据库、MCP、中间件参数）
- `.env` — 敏感信息（API Keys）
- `pydantic-settings` 管理配置加载，支持环境变量覆盖

---

## 14. 安全考虑

- **认证**：FecMall API 通过 `access-token` 请求头认证
- **PII 保护**：中间件层自动脱敏敏感信息（手机号、身份证、银行卡）
- **人工审批**：敏感操作（下单、删除地址）需用户确认
- **调用限制**：`ToolCallLimitMiddleware` 防止 Agent 无限循环
- **CORS**：FastAPI 中间件配置跨域策略
- **密钥管理**：所有 API Key 通过环境变量注入，不硬编码

---

## 15. 错误处理策略

- **LLM 调用失败**：`ModelRetryMiddleware` 重试 → `ModelFallbackMiddleware` 切换备用模型
- **工具调用失败**：`ToolRetryMiddleware` 指数退避重试（最多 3 次）
- **Agent 调用超限**：`ToolCallLimitMiddleware` 终止并返回友好错误
- **FecMall API 异常**：httpx 超时/错误处理，返回结构化错误信息给 Agent
- **流式异常**：SSE 推送 `error` 事件，不中断连接
