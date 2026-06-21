# 基于 deepagents 框架的 FecMall 智能客服 Agent 设计

- **日期**:2026-06-21
- **状态**:已评审待实现
- **目标**:使用 deepagents 框架新建一个智能客服 Agent,实现与现有 langgraph 多 Agent 系统**等价的功能**,且**完全不影响**现有 langgraph Agent。

---

## 1. 背景

现有系统([src/agents/](../../../src/agents/))是一套基于 LangGraph `StateGraph` 的 **Supervisor 多 Agent 架构**:

- [supervisor.py](../../../src/agents/supervisor.py):意图识别,通过 `structured_output` 路由到 5 个专业 Agent,使用 `Command(goto=...)` 跳转。
- 5 个专业 Agent:商品(product)、订单(order)、售后(aftersale)、用户(user)、通用(general),各自挂载对应的 FecMall 工具。
- [graph_builder.py](../../../src/agents/graph_builder.py):把 Supervisor + 5 个 Agent 组装为 `StateGraph` 并编译。
- [main.py](../../../src/main.py):FastAPI 启动时编译图,放入 `app.state.graph`。
- [api/chat.py](../../../src/api/chat.py):对外提供 `/chat`(同步)、`/chat/stream`(SSE)、`/chat/{session_id}/approve`(人机审批恢复)。

涉及的底层能力:FecMall 工具(商品/购物车/订单/售后/用户)、RAG 知识库检索、MCP 工具(天气)、Skill 工具(汇率)、人机交互审批(敏感操作)、记忆持久化(checkpointer/store)、多模型工厂(LLMFactory)。

本次需求:用 **deepagents** 框架(`requirements.txt` 已声明 `deepagents~=0.6.11`)新建一个 Agent,功能与上面等价,新代码放在 [src/deep_agent/](../../../src/deep_agent/),**不修改** 现有 `src/agents/` 与 `src/api/chat.py`。

> deepagents 是 LangChain 在 `create_agent` 之上的更高层 Agent 框架,内置:规划工具(`write_todos`)、虚拟文件系统、子 Agent 委派(`task` 工具)。范式为「一个主 Agent + 若干 subagents」,主 Agent 通过 `task` 工具把任务委派给专精子 Agent,与现有「supervisor + 5 专业 Agent」高度对应。

---

## 2. 设计决策(已与用户确认)

| 决策点 | 选择 |
|---|---|
| Agent 结构 | **主 Agent + 5 个子 Agent**,镜像现有结构 |
| 工具与子系统 | **全部复用现有模块**(工具/LLMFactory/MemoryManager/MCP/Skill 注入),deep_agent 只写组装逻辑 |
| 人机审批 | **等价复刻**:对下单/支付/登录/注册等敏感工具配置审批中断 |
| 对外暴露 | **独立路由 + 独立 state 完全并存**:新增 `/api/v1/deep/*`,放入 `app.state.deep_graph`,现有接口零改动 |
| 流式 | **同步 + 流式都做**,对齐现有 |
| 测试 | **单元测试为主**,mock 模型,不依赖真实 LLM/外部服务 |

---

## 3. 总体架构

```
                 现有(不动)                              新增(本次)
  /api/v1/chat ──► app.state.graph              /api/v1/deep/chat ──► app.state.deep_graph
  (chat.py)        (StateGraph:                 (deep_chat.py)        (async_create_deep_agent:
                    supervisor + 5 agent)                              主 agent + 5 subagents)
       │                                                 │
       └────────────────────┬─────────────────────────────┘
                            ▼  二者共享同一套底层能力
   FecMall 工具 / RAG 检索 / MCP 注入 / Skill 注入 / LLMFactory / MemoryManager
```

- 新代码仅在 [src/deep_agent/](../../../src/deep_agent/) 与新增的 `src/api/deep_chat.py` 内。
- [main.py](../../../src/main.py) 只**追加**装配与路由注册,**不修改**任何现有行。
- 现有 [chat.py](../../../src/api/chat.py)、[graph_builder.py](../../../src/agents/graph_builder.py)、5 个专业 Agent **一行不改**。

---

## 4. 模块设计

### 4.1 目录结构

```
src/deep_agent/
├── __init__.py          导出 build_deep_agent
├── subagents.py         5 个子 agent 定义(名称/描述/提示词/工具)
├── approval.py          审批配置(敏感工具 → 中断)
├── tools.py             工具收集(复用现有 FecMall/RAG + 运行时注入 MCP/Skill)
└── builder.py           build_deep_agent():组装主 agent + subagents + 审批 + 持久化
```

每个文件职责单一,可独立理解与测试。

### 4.2 `subagents.py` — 子 Agent 定义

5 个子 Agent 直接复用现有专业 Agent 的「系统提示词 + 工具」,保证行为等价:

| 子 Agent | 工具来源(复用) | 提示词来源 |
|---|---|---|
| product | [product_agent.py](../../../src/agents/product_agent.py) 的 5 个工具 | 同 |
| order | [order_agent.py](../../../src/agents/order_agent.py) 的 8 个工具 | 同 |
| aftersale | [aftersale_agent.py](../../../src/agents/aftersale_agent.py) 的 3 个工具(含 `rag_search`) | 同 |
| user | [user_agent.py](../../../src/agents/user_agent.py) 的 7 个工具 | 同 |
| general | 运行时注入的 MCP + Skill 工具 | 同 [general_agent.py](../../../src/agents/general_agent.py) |

子 Agent 使用 deepagents 的 `SubAgent` TypedDict(已对 0.6.11 实测确认字段):

```python
class SubAgent(TypedDict):
    name: str
    description: str          # 供主 agent 判断何时委派(相当于路由依据)
    system_prompt: str
    tools: NotRequired[Sequence[BaseTool | Callable | dict]]
    model: NotRequired[str | BaseChatModel]
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]   # 审批配在子 agent 层
    ...
```

- `tools` 直接传现有工具函数,无需转工具名。
- `description` 写清各子 agent 的职责边界,主 agent 据此通过 `task` 委派(取代现有 supervisor 的 structured_output 路由)。
- 审批通过子 agent 的 `interrupt_on` 字段就近配置(下单工具配在 order、登录配在 user),比挂主 agent 更精准。

### 4.3 `tools.py` — 工具收集

- 内置工具:直接 import 现有 FecMall/RAG 工具函数,零重复。
- MCP/Skill 工具:沿用现有「运行时注入」模式,由 `build_deep_agent(mcp_tools=..., skill_tools=...)` 传入,注入到 general 子 Agent。

### 4.4 `approval.py` — 审批配置

把现有需审批的敏感工具(下单 `submit_order`、支付相关、登录 `login`、注册 `register` 等)映射为 deepagents 的 `interrupt_on` 配置,值为 `InterruptOnConfig(allowed_decisions=["approve","edit","reject"])`。审批就近配在对应子 Agent 的 `interrupt_on` 字段上(如下单配在 order 子 Agent)。集中在一个文件维护,便于与现有 [middleware](../../../src/agents/middleware/) 审批列表核对一致。

> 注:具体敏感工具清单在实现时以现有 middleware / 业务工具实际名称为准,确保与现有系统一致。

### 4.5 `builder.py` — 主组装

```python
async def build_deep_agent(*, mcp_tools, skill_tools, checkpointer, store):
    ...
```

- 用 `LLMFactory.create()` 取模型(复用现有多模型工厂)。
- 组装 5 个 subagents + 主 Agent 系统提示词(调度中心角色,内容对齐现有 `SUPERVISOR_PROMPT`,但改为通过 `task` 委派的 deepagents 范式)。
- 接入审批配置 + `checkpointer`/`store`(复用 [MemoryManager](../../../src/memory/memory_manager.py))。
- 调用 `create_deep_agent(model=..., subagents=[...], system_prompt=..., checkpointer=..., store=...)`,返回编译好的 `CompiledStateGraph`。该返回值原生支持 `ainvoke`/`astream_events`,async MCP 工具可直接传入(0.6.11 仅提供 `create_deep_agent`,无独立 async 工厂)。

---

## 5. API 层

新增 `src/api/deep_chat.py`,镜像现有三个端点,前缀加 `/deep`,读取 `app.state.deep_graph`:

| 端点 | 说明 |
|---|---|
| `POST /api/v1/deep/chat` | 同步对话,逻辑参照现有 `chat()`(提取末条 AI 消息) |
| `POST /api/v1/deep/chat/stream` | SSE 流式,复用现有 [stream_parser.py](../../../src/api/stream_parser.py) 的 `parse_graph_event` |
| `POST /api/v1/deep/chat/{session_id}/approve` | 审批恢复,`Command(resume=...)` 作用于 `deep_graph` |

请求/响应复用现有 [schemas.py](../../../src/api/schemas.py)(`ChatRequest`/`ChatResponse`/`ApprovalDecision`),保持调用方一致。deepagents 基于 LangGraph 运行时,同样支持 `ainvoke`/`astream_events`/`Command(resume=...)`,端点逻辑可平移。

---

## 6. 装配([main.py](../../../src/main.py) 仅追加)

在现有 `build_agent_graph(...)` 装配之后追加(复用已初始化的 memory/mcp_manager/registry):

```python
from src.deep_agent import build_deep_agent
from src.api import deep_chat

# lifespan 内:
deep_graph = await build_deep_agent(
    mcp_tools=mcp_manager.get_tools(),
    skill_tools=registry.get_all_tools(),
    checkpointer=await memory.get_checkpointer(),
    store=await memory.get_store(),
)
app.state.deep_graph = deep_graph

# 文件末尾:
app.include_router(deep_chat.router)
```

现有 `app.state.graph` 与 [chat.py](../../../src/api/chat.py) 完全不受影响。

---

## 7. 测试

`tests/unit/deep_agent/`,单元测试为主,mock 模型,不依赖真实 LLM/外网:

| 测试文件 | 验证内容 |
|---|---|
| `test_subagents.py` | 5 个子 Agent 的工具数量、名称与现有专业 Agent 一一对应 |
| `test_approval.py` | 敏感工具审批配置与现有 middleware 审批列表一致 |
| `test_tools.py` | 工具收集正确(内置 + 注入) |
| `test_builder.py` | `build_deep_agent` 用假 checkpointer/store/mock 模型可成功组装(不发真实请求) |

---

## 8. 前置依赖与风险

1. **deepagents 安装(已解决)**:内网源 `pypi.weintdata.cn` 无该包,改用清华源 `https://pypi.tuna.tsinghua.edu.cn/simple` 已成功安装 `deepagents-0.6.11`。
2. **API 签名确认(已完成)**:已对 0.6.11 实测确认 —— 工厂函数为 `create_deep_agent`(无 `async_create_deep_agent`),提示词参数为 `system_prompt`,审批参数为 `interrupt_on`,`SubAgent` 字段含 `name/description/system_prompt/tools/model/interrupt_on`。设计已据此定稿,无需兼容封装。
3. **依赖冲突(已初步验证,风险可控)**:安装 deepagents 时连带升级 `langsmith 0.4.26 → 0.8.18`、引入 `anthropic`/`langchain-anthropic`/`langchain-google-genai`,pip 报告与 `langchain-deepseek 0.1.4`、`langgraph-supervisor 0.0.29` 存在版本约束冲突。但实测 `import deepagents` 与现有 `from src.agents.graph_builder import build_agent_graph`(及 supervisor)**均能正常导入**——冲突的两个包当前项目并未实际 import,故现有 agent 不受影响。实现计划仍应在第一步跑一次现有测试 / 启动 `src.main` 做完整确认。

---

## 9. 不在本次范围(YAGNI)

- 不重写/不重构现有 `src/agents/`。
- 不引入配置开关切换两套 Agent(明确选择独立并存)。
- 不新增真实端到端冒烟测试(仅单元测试)。
- 不改动现有 `schemas.py`/`chat.py`/`stream_parser.py`(仅复用)。
