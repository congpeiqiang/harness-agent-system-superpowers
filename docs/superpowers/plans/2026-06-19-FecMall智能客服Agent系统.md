# FecMall 智能客服 Agent 系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 FecMall 商城系统构建生产级多 Agent 智能客服系统，支持 MCP/Skill 扩展、异步流式响应、记忆、RAG、可观测性。

**Architecture:** Supervisor + 5 个专业 Agent 协作架构（LangGraph 状态图编排），工具层对接 FecMall API / MCP Server / Skill 插件，持久化使用 AsyncSqliteSaver + SqliteStore 双层记忆，RAG 使用 Milvus 向量库，可观测性使用 LangSmith。

**Tech Stack:** Python 3.13, langchain==1.3.10, langgraph>=1.0, FastAPI, httpx, pymilvus, mcp, aiosqlite, structlog

## Global Constraints

- Python 3.13，所有 I/O 操作使用 async/await
- langchain==1.3.10，Agent 创建使用 `from langchain.agents import create_agent`（非 `create_react_agent`）
- 工具定义使用 `@tool` + `async def`，从 `langchain_core.tools` 导入
- 检查点使用 `from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver`
- 长期存储使用 `from langgraph.store.sqlite import SqliteStore`
- 所有 API Key 通过环境变量注入，禁止硬编码
- 中文注释和文档
- 每个 Task 完成后 git commit

---

## Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: 所有 `__init__.py` 和空目录

**Interfaces:**
- Produces: 完整项目目录结构，所有 Python 包可导入

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p src/{api,agents/middleware,tools/fecmall,mcp/{server,client},skills/builtin,memory,rag,config,observability}
mkdir -p tests/{unit,integration}
mkdir -p data logs config knowledge_base/{faq,policies}
touch data/.gitkeep logs/.gitkeep
touch src/__init__.py src/api/__init__.py src/agents/__init__.py src/agents/middleware/__init__.py
touch src/tools/__init__.py src/tools/fecmall/__init__.py
touch src/mcp/__init__.py src/mcp/server/__init__.py src/mcp/client/__init__.py
touch src/skills/__init__.py src/skills/builtin/__init__.py
touch src/memory/__init__.py src/rag/__init__.py src/config/__init__.py src/observability/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
langchain==1.3.10
langgraph>=1.0
langchain-openai>=0.3
langgraph-checkpoint-sqlite>=3.1
langchain-community>=0.3
langchain-text-splitters
pymilvus>=2.4
mcp>=1.0
langchain-mcp-adapters
httpx>=0.27
aiosqlite
fastapi>=0.115
uvicorn[standard]
pydantic-settings
pyyaml
structlog
python-dotenv
watchdog
starlette
langsmith
pytest
pytest-asyncio
```

- [ ] **Step 3: 创建 pyproject.toml**

```toml
[project]
name = "fecmall-agent-system"
version = "1.0.0"
description = "FecMall 智能客服 Agent 系统"
requires-python = ">=3.13"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: 创建 .gitignore**

```
__pycache__/
*.pyc
.env
data/*.db
logs/*.log
.venv/
*.egg-info/
dist/
build/
```

- [ ] **Step 5: 创建 .env.example**

```env
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
FECMALL_BASE_URL=http://localhost/appserver
FECMALL_DEFAULT_CURRENCY=USD
FECMALL_DEFAULT_LANG=en_US
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_MODEL=text-embedding-3-small
WEATHER_API_KEY=xxx
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_sk_xxx
LANGSMITH_PROJECT=fecmall-agent-dev
```

- [ ] **Step 6: 验证并 Commit**

```bash
python -c "import src; print('OK')"
git add -A
git commit -m "feat: 初始化项目脚手架和目录结构"
```

---

## Task 2: 配置管理

**Files:**
- Create: `src/config/settings.py`
- Create: `config/settings.yaml`
- Test: `tests/unit/test_settings.py`

**Interfaces:**
- Produces: `get_settings() -> Settings`
- Produces: `Settings` 类含 `llm`, `fecmall`, `milvus`, `embedding`, `middleware`, `observability`

- [ ] **Step 1: 写测试** `tests/unit/test_settings.py`

```python
import os
import pytest
from src.config.settings import get_settings, Settings

def test_settings_loads_defaults():
    settings = Settings()
    assert settings.llm.default_provider == "deepseek"
    assert settings.fecmall.default_currency == "USD"
    assert settings.middleware.tool_call_limit.run_limit == 15

def test_settings_env_override():
    os.environ["FECMALL_BASE_URL"] = "http://test-server/appserver"
    settings = Settings()
    assert settings.fecmall.base_url == "http://test-server/appserver"
    del os.environ["FECMALL_BASE_URL"]

def test_get_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/unit/test_settings.py -v
```

- [ ] **Step 3: 创建 config/settings.yaml**

```yaml
llm:
  default_provider: "deepseek"
  providers:
    openai:
      base_url: "https://api.openai.com/v1"
      model: "gpt-4o"
      temperature: 0.3
    deepseek:
      base_url: "https://api.deepseek.com/v1"
      model: "deepseek-chat"
      temperature: 0.3
    ollama:
      base_url: "http://localhost:11434/v1"
      model: "qwen2.5:14b"
      temperature: 0.3
  agent_overrides:
    supervisor:
      provider: "deepseek"

fecmall:
  base_url: "http://localhost/appserver"
  default_currency: "USD"
  default_lang: "en_US"
  timeout: 30

milvus:
  uri: "http://localhost:19530"
  token: ""
  collection_name: "fecmall_knowledge"

embedding:
  model: "text-embedding-3-small"

middleware:
  summarization:
    max_tokens: 4000
    keep_messages: 6
  human_in_the_loop:
    enabled: true
    approve_tool_names: [submit_order, remove_address, remove_cart_item, update_profile]
  tool_call_limit:
    run_limit: 15
    thread_limit: 100
  tool_retry:
    max_retries: 3
    backoff_factor: 2.0
  model_retry:
    max_retries: 3
    retry_delay: 1.0

observability:
  langsmith:
    enabled: true
    project: "fecmall-agent"
  logging:
    level: "INFO"
    format: "json"
```

- [ ] **Step 4: 创建 src/config/settings.py**

```python
"""配置管理 — pydantic-settings + YAML"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class LLMProviderConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.3

class AgentOverride(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None

class LLMConfig(BaseModel):
    default_provider: str = "deepseek"
    providers: dict[str, LLMProviderConfig] = {}
    agent_overrides: dict[str, AgentOverride] = {}

class FecMallConfig(BaseModel):
    base_url: str = "http://localhost/appserver"
    default_currency: str = "USD"
    default_lang: str = "en_US"
    timeout: int = 30

class MilvusConfig(BaseModel):
    uri: str = "http://localhost:19530"
    token: str = ""
    collection_name: str = "fecmall_knowledge"

class EmbeddingConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "text-embedding-3-small"

class SummarizationConfig(BaseModel):
    max_tokens: int = 4000
    keep_messages: int = 6

class HumanInTheLoopConfig(BaseModel):
    enabled: bool = True
    approve_tool_names: list[str] = []

class ToolCallLimitConfig(BaseModel):
    run_limit: int = 15
    thread_limit: int = 100

class RetryConfig(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 2.0

class ModelRetryConfig(BaseModel):
    max_retries: int = 3
    retry_delay: float = 1.0

class MiddlewareConfig(BaseModel):
    summarization: SummarizationConfig = SummarizationConfig()
    human_in_the_loop: HumanInTheLoopConfig = HumanInTheLoopConfig()
    tool_call_limit: ToolCallLimitConfig = ToolCallLimitConfig()
    tool_retry: RetryConfig = RetryConfig()
    model_retry: ModelRetryConfig = ModelRetryConfig()

class LangSmithConfig(BaseModel):
    enabled: bool = True
    project: str = "fecmall-agent"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"

class ObservabilityConfig(BaseModel):
    langsmith: LangSmithConfig = LangSmithConfig()
    logging: LoggingConfig = LoggingConfig()

class Settings(BaseSettings):
    llm: LLMConfig = LLMConfig()
    fecmall: FecMallConfig = FecMallConfig()
    milvus: MilvusConfig = MilvusConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    middleware: MiddlewareConfig = MiddlewareConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    weather_api_key: str = Field(default="", alias="WEATHER_API_KEY")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    model_config = {"env_prefix": "", "extra": "ignore"}

    def __init__(self, **kwargs):
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
            merged = {**yaml_config, **kwargs}
            super().__init__(**merged)
        else:
            super().__init__(**kwargs)
        if self.openai_api_key and "openai" in self.llm.providers:
            self.llm.providers["openai"].api_key = self.openai_api_key
        if self.deepseek_api_key and "deepseek" in self.llm.providers:
            self.llm.providers["deepseek"].api_key = self.deepseek_api_key

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: 运行测试并 Commit**

```bash
pip install pydantic-settings pyyaml
python -m pytest tests/unit/test_settings.py -v
git add -A
git commit -m "feat: 添加配置管理模块"
```

---

## Task 3: 多模型工厂

**Files:** Create `src/config/llm_factory.py`, Test `tests/unit/test_llm_factory.py`

**Interfaces:** Consumes `get_settings()`, Produces `LLMFactory.create(agent_name) -> ChatOpenAI`

- [ ] **Step 1: 写测试** — 验证默认模型创建、Agent覆盖、实例缓存
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 `src/config/llm_factory.py`**（完整代码见设计文档 §4.6）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加多模型工厂"`

---

## Task 4: 可观测性基础

**Files:** Create `src/observability/{logging,langsmith_setup,metrics,tracing}.py`, Test `tests/unit/test_observability.py`

**Interfaces:** Produces `setup_logging()`, `setup_langsmith()`, `AgentMetrics`, `AgentTracer`

- [ ] **Step 1: 写测试** — 验证日志初始化、指标递增、追踪ID生成
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 4 个可观测性模块**（完整代码见设计文档 §12）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加可观测性模块"`

---

## Task 5: FecMall HTTP 客户端

**Files:** Create `src/tools/fecmall/client.py`, Test `tests/unit/test_fecmall_client.py`

**Interfaces:** Consumes `get_settings()`, Produces `FecMallClient`（async with）

- [ ] **Step 1: 写测试** — 验证上下文管理器、默认请求头、access-token 注入
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 `client.py`**（完整代码见设计文档 §6.1）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 FecMall 异步 HTTP 客户端"`

---

## Task 6: FecMall 商品工具

**Files:** Create `src/tools/fecmall/product_tools.py`, Test `tests/unit/test_product_tools.py`

**Interfaces:** Consumes `FecMallClient`, Produces 5 个 @tool 异步工具

- [ ] **Step 1: 写测试** — mock FecMallClient，验证 search_products 和 get_product_detail
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 5 个工具**（search_products, get_product_detail, get_category_products, get_product_reviews, get_home_info）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 FecMall 商品工具"`

---

## Task 7: FecMall 购物车 + 订单 + 客户 + 售后工具

**Files:** Create `src/tools/fecmall/{cart,order,customer,aftersale}_tools.py`, Test `tests/unit/test_fecmall_tools.py`

**Interfaces:** Consumes `FecMallClient`, Produces 17 个 @tool 异步工具

- [ ] **Step 1: 写测试** — 验证 get_cart、login 等关键工具
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 4 个工具文件**（cart 4个 + order 4个 + customer 7个 + aftersale 2个）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 FecMall 购物车/订单/客户/售后工具"`

---

## Task 8: MCP 天气 Server

**Files:** Create `src/mcp/server/weather_server.py`, Test `tests/unit/test_weather_server.py`

**Interfaces:** Produces MCP 工具 `get_weather`/`get_weather_forecast` + Starlette SSE 应用

- [ ] **Step 1: 写测试** — 验证 format_weather_data 和 format_forecast_data
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 weather_server.py**（SSE 传输 + Starlette 路由）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加天气查询 MCP Server"`

---

## Task 9: MCP Client Manager

**Files:** Create `src/mcp/client/mcp_client.py`, Test `tests/unit/test_mcp_client.py`

**Interfaces:** Produces `MCPClientManager`（connect/disconnect_all/get_tools/list_servers）

- [ ] **Step 1: 写测试** — 验证初始化工具列表为空
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 mcp_client.py**（使用 langchain-mcp-adapters 转换工具）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 MCP 客户端管理器"`

---

## Task 10: Skill 插件系统

**Files:** Create `src/skills/{base_skill,registry,loader}.py` + `builtin/currency_convert.py`, Test `tests/unit/test_skills.py`

**Interfaces:** Produces `BaseSkill`, `SkillRegistry`, `SkillLoader`, `CurrencyConvertSkill`

- [ ] **Step 1: 写测试** — 验证注册/列表/工具聚合/注销
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 4 个模块**（基类 + 注册表 + 加载器 + 内置汇率Skill）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 Skill 插件系统"`

---

## Task 11: 记忆管理

**Files:** Create `src/memory/{memory_manager,user_profile}.py`, Test `tests/unit/test_memory.py`

**Interfaces:** Produces `MemoryManager`（AsyncSqliteSaver + SqliteStore）, `UserProfileManager`

- [ ] **Step 1: 写测试** — 验证初始化（:memory:）、偏好存取
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 memory_manager.py + user_profile.py**
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加双层记忆管理"`

---

## Task 12: RAG 知识库（Milvus）

**Files:** Create `src/rag/{embeddings,milvus_client,loader,retriever}.py` + `src/tools/rag_tools.py` + 知识库文档, Test `tests/unit/test_rag.py`

**Interfaces:** Produces `EmbeddingService`, `MilvusManager`, `DocumentLoader`, `RAGRetriever`, `rag_search` @tool

- [ ] **Step 1: 创建知识库文档** — `knowledge_base/faq/*.md` + `knowledge_base/policies/*.md`（至少 8 个文件）
- [ ] **Step 2: 写测试** — 验证 DocumentLoader 加载文档
- [ ] **Step 3: 运行测试确认失败**
- [ ] **Step 4: 实现 5 个模块**（embeddings + milvus_client + loader + retriever + rag_tools）
- [ ] **Step 5: 运行测试确认通过**
- [ ] **Step 6: Commit** `git commit -m "feat: 添加 RAG 知识库（Milvus）"`

---

## Task 13: 中间件体系

**Files:** Create `src/agents/middleware/{custom_pii,middleware_builder}.py`, Test `tests/unit/test_middleware.py`

**Interfaces:** Produces `ChinaPIIMiddleware`, `build_middleware_stack()`

- [ ] **Step 1: 写测试** — 验证手机号/身份证/银行卡脱敏
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 custom_pii.py**（ChinaPIIMiddleware 继承 AgentMiddleware）
- [ ] **Step 4: 实现 middleware_builder.py**（构建 7+1 个中间件栈）
- [ ] **Step 5: 运行测试确认通过**
- [ ] **Step 6: Commit** `git commit -m "feat: 添加中间件体系"`

---

## Task 14: BaseAgent + 5 个专业 Agent

**Files:** Create `src/agents/{base_agent,product_agent,order_agent,aftersale_agent,general_agent,user_agent}.py`, Test `tests/unit/test_agents.py`

**Interfaces:** Consumes `create_agent`, `build_middleware_stack()`, 各工具模块; Produces 6 个 Agent 类

- [ ] **Step 1: 写测试** — 验证各 Agent 的工具数量和名称
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 base_agent.py**（invoke_node + stream_node）
- [ ] **Step 4: 实现 5 个专业 Agent**（ProductAgent, OrderAgent, AfterSaleAgent, GeneralAgent, UserAgent）
- [ ] **Step 5: 运行测试确认通过**
- [ ] **Step 6: Commit** `git commit -m "feat: 添加 BaseAgent 和 5 个专业 Agent"`

---

## Task 15: Supervisor + LangGraph 状态图

**Files:** Create `src/agents/{supervisor,graph_builder}.py`, Test `tests/unit/test_graph.py`

**Interfaces:** Consumes 所有 Agent/Memory/MCP/Skill; Produces `build_agent_graph()` 返回编译后的 LangGraph

- [ ] **Step 1: 写测试** — 验证 RouteDecision 结构
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 supervisor.py**（@traceable + structured_output 路由）
- [ ] **Step 4: 实现 graph_builder.py**（StateGraph + 6 节点 + compile）
- [ ] **Step 5: 运行测试确认通过**
- [ ] **Step 6: Commit** `git commit -m "feat: 添加 Supervisor 和 LangGraph 状态图"`

---

## Task 16: Pydantic 模型 + SSE 解析

**Files:** Create `src/api/{schemas,stream_parser}.py`, Test `tests/unit/test_schemas.py`

**Interfaces:** Produces `ChatRequest`, `ChatResponse`, `StreamEvent`, `SessionInfo`, `HealthResponse`, `ApprovalDecision`

- [ ] **Step 1: 写测试** — 验证请求模型、SSE 事件模型
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 schemas.py + stream_parser.py**
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 Pydantic 模型和 SSE 解析"`

---

## Task 17: API 路由

**Files:** Create `src/api/{chat,sessions,health}.py`, Test `tests/unit/test_api.py`

**Interfaces:** Consumes app.state.graph/memory/mcp/skill; Produces 11 个 REST 端点

- [ ] **Step 1: 写测试** — 验证请求验证、健康检查响应
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 chat.py**（POST /chat, POST /chat/stream, POST /approve）
- [ ] **Step 4: 实现 sessions.py**（POST/GET/DELETE sessions）
- [ ] **Step 5: 实现 health.py**（GET /health, /metrics, /skills, POST /skills/reload）
- [ ] **Step 6: 运行测试确认通过**
- [ ] **Step 7: Commit** `git commit -m "feat: 添加 API 路由"`

---

## Task 18: FastAPI 应用入口

**Files:** Create `src/main.py`, Test `tests/integration/test_app_startup.py`

**Interfaces:** Consumes 所有模块; Produces FastAPI 应用

- [ ] **Step 1: 写测试** — 验证健康检查端点返回 200
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现 main.py**（lifespan + CORS + 路由注册）
- [ ] **Step 4: 运行测试确认通过**
- [ ] **Step 5: Commit** `git commit -m "feat: 添加 FastAPI 应用入口"`

---

## Task 19: Docker 部署 + README

**Files:** Create `docker/{Dockerfile,Dockerfile.mcp,docker-compose.yml}`, `README.md`, 剩余知识库文档

- [ ] **Step 1: 创建 Dockerfile**（python:3.13-slim + uvicorn）
- [ ] **Step 2: 创建 Dockerfile.mcp**（天气 MCP Server 独立镜像）
- [ ] **Step 3: 创建 docker-compose.yml**（agent-server + weather-mcp + milvus 全套）
- [ ] **Step 4: 补充知识库文档**（支付FAQ、配送FAQ、账户FAQ、隐私政策、服务条款、配送说明）
- [ ] **Step 5: 创建 README.md**（特性列表 + 快速开始 + API 文档）
- [ ] **Step 6: Commit** `git commit -m "feat: 添加 Docker 部署和 README"`

---

## 实施总结

| 阶段 | Task | 内容 | 预估时间 |
|------|------|------|---------|
| 基础 | 1-4 | 脚手架 + 配置 + LLM工厂 + 可观测性 | 2h |
| 集成 | 5-10 | FecMall客户端/工具 + MCP + Skill | 4h |
| 记忆/RAG | 11-12 | 双层记忆 + RAG知识库 | 2h |
| Agent | 13-15 | 中间件 + 专业Agent + Supervisor | 3h |
| API/App | 16-18 | Pydantic + 路由 + 应用入口 | 2h |
| 部署 | 19 | Docker + 知识库 + README | 1h |
| **合计** | **19** | | **~14h** |
