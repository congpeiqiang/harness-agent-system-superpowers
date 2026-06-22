# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

FecMall 智能客服系统 — 基于多 Agent 架构的电商客服平台，Python 3.13+，FastAPI + LangGraph + deepagents。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动主服务（热重载）
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 MCP 天气服务（独立进程）
uvicorn src.mcp_client_service.server.weather_server:starlette_app --host 0.0.0.0 --port 8001

# Docker 全栈部署（含 Milvus、etcd、MinIO）
cd docker && docker compose up -d

# 运行全部测试
pytest

# 运行单个测试模块
pytest tests/unit/test_agents.py -v

# 运行单个测试函数
pytest tests/unit/test_agents.py::test_function_name -v
```

## 架构要点

### 双 Agent 系统并存

项目同时维护两套 Agent 实现，共享工具层和基础设施：

1. **LangGraph 版本** (`src/agents/`) — Supervisor 状态图模式，`START → supervisor → {5个专家Agent} → supervisor` 循环
2. **deepagents 版本** (`src/deep_agent/`) — 使用 `create_deep_agent` + subagent `task` 工具委托

**关键约束**：修改工具或提示词时，必须同步更新两套系统。

### 5 个专家 Agent

product（商品）、order（订单）、aftersale（售后）、user（用户）、general（通用/动态MCP工具），每个继承 `BaseAgent` 抽象类。

### 工具层 (`src/tools/fecmall/`)

- 所有工具使用 `@tool` 装饰的 async 函数
- 通过 `FecMallClient`（httpx async 上下文管理器）调用 FecMall API
- Token 从 `RunnableConfig` 中通过 `get_token()` 提取
- 共 23 个工具：商品5 + 购物车4 + 订单4 + 售后2 + 用户7 + RAG 1

### 中间件栈（8层，有序）

`src/agents/middleware/middleware_builder.py` 按顺序构建：ModelRetry → ModelFallback → Summarization → PII → ChinaPII → HumanInTheLoop → ToolRetry → ToolCallLimit

### 双层记忆系统

- **短期**：`AsyncSqliteSaver`（会话 checkpoint，`data/checkpoints.db`）
- **长期**：`AsyncSqliteStore`（用户偏好，`data/store.db`）

### 配置体系

- YAML 文件 `config/settings.yaml` + 环境变量合并
- Pydantic Settings + `lru_cache` 单例（`get_settings()`）
- 环境变量覆盖模式：`FECMALL_BASE_URL` → `fecmall.base_url`

### RAG 系统

- Milvus 向量数据库，`knowledge_base/faq/` 和 `knowledge_base/policies/` 下的 Markdown 文档
- 文本分块：500字符，50重叠
- `RAGRetriever` 单例模式

### Skill 系统

- `BaseSkill` 抽象类，`SkillRegistry` 注册管理，`SkillLoader` 从 `src/skills/builtin/` 动态加载
- 支持热重载：`POST /api/v1/skills/reload`

### API 路由

- `/api/v1/chat` 系列 — LangGraph 版本
- `/api/v1/deep/chat` 系列 — deepagents 版本
- `/api/v1/sessions` — 会话 CRUD
- `/api/v1/health`、`/api/v1/metrics`、`/api/v1/skills` — 运维端点

## 重要注意事项

- **全异步架构**：httpx、SQLite (aiosqlite)、MCP、FastAPI 均为 async
- **MCP 目录**：`src/mcp_client_service/`（原名 `src/mcp/`，因与第三方 `mcp` 包冲突而重命名）
- **导入兼容**：`BaseAgent._import_create_agent()` 尝试多条导入路径以适配 API 演进
- **人工审批工具**：`submit_order`、`remove_address`、`remove_cart_item`、`update_profile` 需 HumanInTheLoop 审批
- **代码和提示词语言**：中文为主
- **测试**：pytest + pytest-asyncio，`asyncio_mode = "auto"`，使用 `unittest.mock.MagicMock`
