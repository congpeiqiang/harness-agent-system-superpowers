# 基于 deepagents 的 FecMall 智能客服 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 deepagents 框架新建一个与现有 langgraph 多 Agent 系统功能等价的 FecMall 智能客服 Agent,且完全不影响现有系统。

**Architecture:** 主 deep agent + 5 个 subagents(商品/订单/售后/用户/通用),复用现有全部 FecMall/RAG/MCP/Skill 工具、LLMFactory、MemoryManager。新增独立 API 路由 `/api/v1/deep/*`,放入 `app.state.deep_graph`,与现有 `app.state.graph` 并存。现有 `src/agents/`、`src/api/chat.py` 零改动。

**Tech Stack:** Python、deepagents 0.6.11、langgraph 1.2.6、langchain 1.3.9、FastAPI、pytest。

## Global Constraints

- 全程中文:文档、代码注释、新增文档文件名均用中文。
- 不修改现有 `src/agents/` 任何文件,不修改 `src/api/chat.py`、`src/api/stream_parser.py`、`src/api/schemas.py`(仅 import 复用)。
- [main.py](../../../src/main.py) 只能**追加**(新增 import、lifespan 内追加装配、文件末尾追加 `include_router`),不得修改现有行。
- deepagents 工厂函数为 `create_deep_agent`(无 async 版本);提示词参数 `system_prompt`;审批参数 `interrupt_on`,值为 `{tool_name: True}` 或 `{tool_name: InterruptOnConfig(...)}`。
- `SubAgent` TypedDict 字段:`name`/`description`/`system_prompt`/`tools`(NotRequired)/`model`(NotRequired)/`interrupt_on`(NotRequired)。
- 审批工具清单从现有配置读取:`settings.middleware.human_in_the_loop.approve_tool_names`,当前值 `[submit_order, remove_address, remove_cart_item, update_profile]`。
- 工具均为 `StructuredTool`,`.name` 即函数名。
- 测试用 mock 模型,不发真实 LLM 请求、不依赖外部服务(MCP/Milvus)。

---

### Task 1: 前置验证与依赖落档

**Files:**
- Modify: `requirements.txt`(确认/补充 deepagents 连带依赖版本)

**Interfaces:**
- Consumes: 无
- Produces: 一个已确认 deepagents 与现有系统共存可用的环境

- [ ] **Step 1: 验证 deepagents 与现有 agent 同时可导入**

Run:
```bash
python -c "import deepagents; print('deepagents', deepagents.__version__)"
python -c "from src.agents.graph_builder import build_agent_graph; from src.agents.supervisor import supervisor_node; print('existing agents OK')"
```
Expected: 两条均无异常,分别打印 `deepagents 0.6.11` 与 `existing agents OK`。

- [ ] **Step 2: 跑现有测试套件确认未被破坏**

Run: `pytest -q 2>&1 | tail -20`
Expected: 现有测试通过数与改动前一致(若环境缺外部服务导致的已有跳过/失败属基线,记录但不新增失败)。

- [ ] **Step 3: 核对 requirements.txt 依赖版本**

打开 `requirements.txt`,确认 `deepagents~=0.6.11` 在列(已在)。安装 deepagents 时 `langsmith` 被升级到 `0.8.18`,若 `requirements.txt` 仍写死旧 langsmith 版本则放宽约束;若未写死则无需改动。仅在确有版本钉死冲突时才修改,改动以一行注释说明原因。

- [ ] **Step 4: 提交(若 requirements.txt 有改动)**

```bash
git add requirements.txt
git commit -m "chore:确认deepagents依赖与现有系统共存"
```
若无改动则跳过本步。

---

### Task 2: 工具收集模块

**Files:**
- Create: `src/deep_agent/__init__.py`
- Create: `src/deep_agent/tools.py`
- Test: `tests/unit/deep_agent/test_tools.py`
- Create: `tests/unit/deep_agent/__init__.py`

**Interfaces:**
- Consumes: 现有 `src/tools/fecmall/*`、`src/tools/rag_tools.rag_search`
- Produces:
  - `get_product_tools() -> list`(5 个)
  - `get_order_tools() -> list`(8 个)
  - `get_aftersale_tools() -> list`(3 个)
  - `get_user_tools() -> list`(7 个)
  - `get_general_tools(mcp_tools: list, skill_tools: list) -> list`

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/__init__.py`(空文件)。

Create `tests/unit/deep_agent/test_tools.py`:
```python
"""deep_agent 工具收集模块测试。"""
from src.deep_agent.tools import (
    get_product_tools,
    get_order_tools,
    get_aftersale_tools,
    get_user_tools,
    get_general_tools,
)


def test_product_tools_count_and_names():
    tools = get_product_tools()
    names = {t.name for t in tools}
    assert len(tools) == 5
    assert names == {
        "search_products",
        "get_product_detail",
        "get_category_products",
        "get_product_reviews",
        "get_home_info",
    }


def test_order_tools_count():
    assert len(get_order_tools()) == 8


def test_aftersale_tools_include_rag():
    names = {t.name for t in get_aftersale_tools()}
    assert len(names) == 3
    assert "rag_search" in names


def test_user_tools_count():
    assert len(get_user_tools()) == 7


def test_general_tools_merges_injected():
    fake_mcp = ["MCP_TOOL"]
    fake_skill = ["SKILL_TOOL"]
    tools = get_general_tools(fake_mcp, fake_skill)
    assert "MCP_TOOL" in tools and "SKILL_TOOL" in tools
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_tools.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'src.deep_agent.tools'`(注意:目录下现有草稿 `agent.py` 在 Task 6 删除,本步不受影响)。

- [ ] **Step 3: 写实现**

Create `src/deep_agent/__init__.py`:
```python
"""deep_agent 包 —— 基于 deepagents 框架的 FecMall 智能客服 Agent。"""
```

Create `src/deep_agent/tools.py`:
```python
"""工具收集 —— 复用现有 FecMall / RAG 工具,并合并运行时注入的 MCP / Skill 工具。

按子 Agent 职责分组返回工具列表,与现有 src/agents 下 5 个专业 Agent 一一对应。
"""
from typing import Any

from src.tools.fecmall.product_tools import (
    get_category_products,
    get_home_info,
    get_product_detail,
    get_product_reviews,
    search_products,
)
from src.tools.fecmall.cart_tools import (
    add_to_cart,
    get_cart,
    remove_cart_item,
    update_cart_item,
)
from src.tools.fecmall.order_tools import (
    get_checkout_init,
    get_order_detail,
    get_order_list,
    submit_order,
)
from src.tools.fecmall.aftersale_tools import (
    get_refund_status,
    submit_complaint,
)
from src.tools.fecmall.customer_tools import (
    add_address,
    get_address_list,
    get_user_profile,
    login,
    register,
    remove_address,
    update_profile,
)
from src.tools.rag_tools import rag_search


def get_product_tools() -> list[Any]:
    """商品子 Agent 工具(与 ProductAgent 一致,5 个)。"""
    return [
        search_products,
        get_product_detail,
        get_category_products,
        get_product_reviews,
        get_home_info,
    ]


def get_order_tools() -> list[Any]:
    """订单子 Agent 工具(与 OrderAgent 一致,8 个)。"""
    return [
        get_cart,
        add_to_cart,
        update_cart_item,
        remove_cart_item,
        get_checkout_init,
        submit_order,
        get_order_list,
        get_order_detail,
    ]


def get_aftersale_tools() -> list[Any]:
    """售后子 Agent 工具(与 AfterSaleAgent 一致,3 个,含 RAG 检索)。"""
    return [
        submit_complaint,
        get_refund_status,
        rag_search,
    ]


def get_user_tools() -> list[Any]:
    """用户子 Agent 工具(与 UserAgent 一致,7 个)。"""
    return [
        login,
        register,
        get_user_profile,
        update_profile,
        get_address_list,
        add_address,
        remove_address,
    ]


def get_general_tools(mcp_tools: list[Any], skill_tools: list[Any]) -> list[Any]:
    """通用子 Agent 工具(与 GeneralAgent 一致):运行时注入的 MCP + Skill 工具。"""
    return list(mcp_tools) + list(skill_tools)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_tools.py -v`
Expected: 5 passed。

- [ ] **Step 5: 提交**

```bash
git add src/deep_agent/__init__.py src/deep_agent/tools.py tests/unit/deep_agent/__init__.py tests/unit/deep_agent/test_tools.py
git commit -m "feat:新增deep_agent工具收集模块"
```

---

### Task 3: 审批配置模块

**Files:**
- Create: `src/deep_agent/approval.py`
- Test: `tests/unit/deep_agent/test_approval.py`

**Interfaces:**
- Consumes: `src.config.settings.get_settings()`(读取 `middleware.human_in_the_loop.approve_tool_names`)
- Produces:
  - `get_approval_tool_names() -> list[str]`
  - `build_interrupt_on(tool_names: list) -> dict[str, Any]` —— 仅为该子 Agent 拥有的工具生成 `interrupt_on`

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/test_approval.py`:
```python
"""deep_agent 审批配置测试。"""
from src.deep_agent.approval import build_interrupt_on, get_approval_tool_names


class _FakeTool:
    def __init__(self, name):
        self.name = name


def test_approval_names_match_settings():
    names = get_approval_tool_names()
    # 与 config/settings.yaml 的 approve_tool_names 一致
    assert "submit_order" in names
    assert "remove_address" in names
    assert "remove_cart_item" in names
    assert "update_profile" in names


def test_build_interrupt_on_only_owned_tools():
    tools = [_FakeTool("submit_order"), _FakeTool("get_order_list")]
    cfg = build_interrupt_on(tools)
    # 只有敏感工具进入审批配置,普通工具不进入
    assert "submit_order" in cfg
    assert "get_order_list" not in cfg


def test_build_interrupt_on_empty_when_no_sensitive():
    tools = [_FakeTool("search_products")]
    assert build_interrupt_on(tools) == {}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_approval.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'src.deep_agent.approval'`。

- [ ] **Step 3: 写实现**

Create `src/deep_agent/approval.py`:
```python
"""审批配置 —— 把现有配置中的敏感工具映射为 deepagents 的 interrupt_on。

审批工具清单来源与现有系统一致:settings.middleware.human_in_the_loop.approve_tool_names
(当前:submit_order / remove_address / remove_cart_item / update_profile)。
审批就近配置在拥有该工具的子 Agent 上。
"""
from typing import Any

from src.config.settings import get_settings

# 允许的人工决策类型,与现有 HumanInTheLoopMiddleware 用法一致
ALLOWED_DECISIONS = ["approve", "edit", "reject"]


def get_approval_tool_names() -> list[str]:
    """返回需要人工审批的工具名清单(读取现有配置)。"""
    settings = get_settings()
    return list(settings.middleware.human_in_the_loop.approve_tool_names)


def build_interrupt_on(tools: list[Any]) -> dict[str, Any]:
    """为给定子 Agent 的工具生成 interrupt_on 配置。

    只有同时满足「在审批清单中」且「属于该子 Agent」的工具才会被纳入。

    Args:
        tools: 子 Agent 的工具列表(元素需有 .name 属性)。

    Returns:
        {tool_name: {"allowed_decisions": [...]}} 形式的 interrupt_on 字典;
        若该子 Agent 不含任何敏感工具,返回空 dict。
    """
    approval_names = set(get_approval_tool_names())
    interrupt_on: dict[str, Any] = {}
    for tool in tools:
        name = getattr(tool, "name", None)
        if name in approval_names:
            interrupt_on[name] = {"allowed_decisions": list(ALLOWED_DECISIONS)}
    return interrupt_on
```

> 说明:此处用普通 dict 表达 `InterruptOnConfig`(它是 TypedDict),deepagents 接受 `dict[str, bool | InterruptOnConfig]`。如需类型对象,可改为 `from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig`,但 dict 形式等价且更易测试。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_approval.py -v`
Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add src/deep_agent/approval.py tests/unit/deep_agent/test_approval.py
git commit -m "feat:新增deep_agent审批配置模块"
```

---

### Task 4: 子 Agent 定义模块

**Files:**
- Create: `src/deep_agent/subagents.py`
- Test: `tests/unit/deep_agent/test_subagents.py`

**Interfaces:**
- Consumes: Task 2 的 `get_*_tools`、Task 3 的 `build_interrupt_on`
- Produces:
  - `build_subagents(mcp_tools: list, skill_tools: list) -> list[dict]` —— 返回 5 个 `SubAgent` dict,字段含 `name`/`description`/`system_prompt`/`tools`/`interrupt_on`

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/test_subagents.py`:
```python
"""deep_agent 子 Agent 定义测试。"""
from src.deep_agent.subagents import build_subagents


def test_five_subagents_with_expected_names():
    subs = build_subagents(mcp_tools=[], skill_tools=[])
    names = {s["name"] for s in subs}
    assert names == {"product", "order", "aftersale", "user", "general"}


def test_each_subagent_has_required_fields():
    subs = build_subagents(mcp_tools=[], skill_tools=[])
    for s in subs:
        assert s["name"]
        assert s["description"]
        assert s["system_prompt"]
        assert "tools" in s


def test_order_subagent_has_approval_on_submit_order():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=[], skill_tools=[])}
    order = subs["order"]
    assert "submit_order" in order["interrupt_on"]


def test_product_subagent_has_no_approval():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=[], skill_tools=[])}
    # 商品子 Agent 无敏感工具,interrupt_on 为空
    assert subs["product"]["interrupt_on"] == {}


def test_general_subagent_receives_injected_tools():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=["M"], skill_tools=["S"])}
    assert "M" in subs["general"]["tools"]
    assert "S" in subs["general"]["tools"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_subagents.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'src.deep_agent.subagents'`。

- [ ] **Step 3: 写实现**

Create `src/deep_agent/subagents.py`:
```python
"""子 Agent 定义 —— 5 个 SubAgent,镜像现有 src/agents 下 5 个专业 Agent。

每个子 Agent 的系统提示词与工具均与对应的现有专业 Agent 保持一致,
审批通过 interrupt_on 就近配置在拥有敏感工具的子 Agent 上。
"""
from typing import Any

from src.deep_agent.approval import build_interrupt_on
from src.deep_agent.tools import (
    get_aftersale_tools,
    get_general_tools,
    get_order_tools,
    get_product_tools,
    get_user_tools,
)

# 系统提示词与现有专业 Agent 对齐(见 src/agents/*_agent.py)
PRODUCT_PROMPT = (
    "你是一个专业的电商商品助手。你可以帮助用户搜索商品、查看商品详情、"
    "浏览分类商品、阅读商品评论以及获取首页推荐信息。"
    "请根据用户的需求,使用合适的工具为他们提供准确的商品信息。"
    "回答时请使用中文,并对商品信息做出清晰的总结和推荐。"
)
ORDER_PROMPT = (
    "你是一个专业的电商订单助手。你可以帮助用户管理购物车(添加、修改、删除商品)、"
    "查看购物车内容、初始化结算、提交订单、查看订单列表和订单详情。"
    "请在执行敏感操作(如提交订单、删除商品)前向用户确认。"
    "回答时请使用中文,并对订单信息做出清晰的总结。"
)
AFTERSALE_PROMPT = (
    "你是一个专业的电商售后助手。你可以帮助用户提交售后投诉、查询订单退款状态,"
    "以及从知识库中搜索退换货政策和常见问题。"
    "在处理投诉时请耐心倾听用户的问题,并提供清晰的解决方案。"
    "回答时请使用中文,语气友好且有同理心。"
)
USER_PROMPT = (
    "你是一个专业的用户账户助手。你可以帮助用户登录、注册新账户、"
    "查看和更新个人资料,以及管理收货地址(添加、查看、删除)。"
    "请在执行敏感操作(如修改资料、删除地址)前向用户确认。"
    "回答时请使用中文,注意保护用户的隐私信息。"
)
GENERAL_PROMPT = (
    "你是一个通用的智能助手。你可以使用各种外部工具来帮助用户完成任务,"
    "包括天气查询、货币转换等功能。"
    "请根据用户的需求选择合适的工具,并提供准确的信息。"
    "回答时请使用中文。"
)

# 主 Agent 据 description 判断委派,内容对齐现有 supervisor 路由说明
_DESCRIPTIONS = {
    "product": "处理商品搜索、详情、分类、评论、首页推荐等商品相关问题。",
    "order": "处理购物车、下单、支付、订单查询等订单相关问题。",
    "aftersale": "处理退换货、投诉、售后、FAQ、政策等售后相关问题。",
    "user": "处理账户、地址、登录、注册、个人信息等用户相关问题。",
    "general": "处理天气、汇率、闲聊及其他通用问题。",
}


def _make_subagent(name: str, prompt: str, tools: list[Any]) -> dict[str, Any]:
    """构造单个 SubAgent dict(含按需生成的 interrupt_on)。"""
    return {
        "name": name,
        "description": _DESCRIPTIONS[name],
        "system_prompt": prompt,
        "tools": tools,
        "interrupt_on": build_interrupt_on(tools),
    }


def build_subagents(mcp_tools: list[Any], skill_tools: list[Any]) -> list[dict[str, Any]]:
    """构建 5 个子 Agent 定义。

    Args:
        mcp_tools: 运行时注入的 MCP 工具(给 general 子 Agent)。
        skill_tools: 运行时注入的 Skill 工具(给 general 子 Agent)。

    Returns:
        SubAgent dict 列表,可直接传给 create_deep_agent(subagents=...)。
    """
    return [
        _make_subagent("product", PRODUCT_PROMPT, get_product_tools()),
        _make_subagent("order", ORDER_PROMPT, get_order_tools()),
        _make_subagent("aftersale", AFTERSALE_PROMPT, get_aftersale_tools()),
        _make_subagent("user", USER_PROMPT, get_user_tools()),
        _make_subagent(
            "general", GENERAL_PROMPT, get_general_tools(mcp_tools, skill_tools)
        ),
    ]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_subagents.py -v`
Expected: 5 passed。

- [ ] **Step 5: 提交**

```bash
git add src/deep_agent/subagents.py tests/unit/deep_agent/test_subagents.py
git commit -m "feat:新增deep_agent子Agent定义模块"
```

---

### Task 5: Agent 组装器

**Files:**
- Create: `src/deep_agent/builder.py`
- Modify: `src/deep_agent/__init__.py`(导出 `build_deep_agent`)
- Test: `tests/unit/deep_agent/test_builder.py`

**Interfaces:**
- Consumes: Task 4 的 `build_subagents`、`src.config.llm_factory.LLMFactory`
- Produces:
  - `async def build_deep_agent(*, mcp_tools, skill_tools, checkpointer, store) -> CompiledStateGraph`
  - `SUPERVISOR_PROMPT: str`(主 Agent 调度提示词)

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/test_builder.py`:
```python
"""deep_agent 组装器测试 —— 用 mock 模型,不发真实请求。"""
from unittest.mock import patch

import pytest

from src.deep_agent.builder import build_deep_agent


class _FakeModel:
    """占位模型,组装阶段不会真正调用它。"""


@pytest.mark.asyncio
async def test_build_deep_agent_returns_compiled_graph():
    captured = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return "COMPILED_GRAPH"

    with patch("src.deep_agent.builder.LLMFactory.create", return_value=_FakeModel()), \
         patch("src.deep_agent.builder.create_deep_agent", side_effect=fake_create_deep_agent):
        result = await build_deep_agent(
            mcp_tools=[], skill_tools=[], checkpointer="CP", store="ST"
        )

    assert result == "COMPILED_GRAPH"
    # 5 个子 Agent 已传入
    assert len(captured["subagents"]) == 5
    # 持久化层透传
    assert captured["checkpointer"] == "CP"
    assert captured["store"] == "ST"
    # 主 Agent 系统提示词非空
    assert captured["system_prompt"]
```

> 注:`pytest.mark.asyncio` 需要 `pytest-asyncio`。先 Step 2 运行,若报缺插件,在 Step 2 处按提示 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pytest-asyncio` 并在 `pyproject.toml`/`pytest.ini` 设 `asyncio_mode = auto`(若现有测试已用 async fixture 则已具备,无需改)。

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_builder.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'src.deep_agent.builder'`(或缺 pytest-asyncio,按上注处理后再跑,应仍因缺 builder 而 FAIL)。

- [ ] **Step 3: 写实现**

Create `src/deep_agent/builder.py`:
```python
"""Agent 组装器 —— 用 deepagents 的 create_deep_agent 组装主 Agent + 5 子 Agent。

复用 LLMFactory(模型)、MemoryManager(checkpointer/store)、现有全部工具。
返回 CompiledStateGraph,原生支持 ainvoke / astream_events / Command(resume=...)。
"""
from typing import Any

from deepagents import create_deep_agent

from src.config.llm_factory import LLMFactory
from src.deep_agent.subagents import build_subagents
from src.observability.logging import get_logger

logger = get_logger("deep_agent.builder")

# 主 Agent 调度提示词,角色对齐现有 supervisor,但采用 deepagents 的 task 委派范式
SUPERVISOR_PROMPT = (
    "你是 FecMall 商城智能客服调度中心。"
    "请根据用户问题,使用 task 工具委派给合适的专业子客服处理:\n"
    "- product: 商品搜索、详情、分类、评论、推荐\n"
    "- order: 购物车、下单、支付、订单查询\n"
    "- aftersale: 退换货、投诉、售后、FAQ、政策\n"
    "- user: 账户、地址、登录、注册、个人信息\n"
    "- general: 天气、汇率、闲聊、其他\n"
    "对于复杂任务,可拆解为多个子任务分别委派。回答时请使用中文。"
)


async def build_deep_agent(
    *,
    mcp_tools: list[Any],
    skill_tools: list[Any],
    checkpointer: Any,
    store: Any,
) -> Any:
    """构建并返回基于 deepagents 的客服 Agent(CompiledStateGraph)。

    Args:
        mcp_tools: 运行时注入的 MCP 工具(给 general 子 Agent)。
        skill_tools: 运行时注入的 Skill 工具(给 general 子 Agent)。
        checkpointer: 会话级持久化(来自 MemoryManager.get_checkpointer())。
        store: 跨会话长期存储(来自 MemoryManager.get_store())。

    Returns:
        编译好的 deep agent 图。
    """
    model = LLMFactory.create(agent_name="supervisor")
    subagents = build_subagents(mcp_tools=mcp_tools, skill_tools=skill_tools)

    graph = create_deep_agent(
        model=model,
        system_prompt=SUPERVISOR_PROMPT,
        subagents=subagents,
        checkpointer=checkpointer,
        store=store,
    )
    logger.info("deep_agent_built", subagents=len(subagents))
    return graph
```

Modify `src/deep_agent/__init__.py` 为:
```python
"""deep_agent 包 —— 基于 deepagents 框架的 FecMall 智能客服 Agent。"""
from src.deep_agent.builder import build_deep_agent

__all__ = ["build_deep_agent"]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_builder.py -v`
Expected: 1 passed。

- [ ] **Step 5: 跑整个 deep_agent 测试目录回归**

Run: `pytest tests/unit/deep_agent/ -v`
Expected: 全部通过(Task 2-5 共 14 个测试)。

- [ ] **Step 6: 提交**

```bash
git add src/deep_agent/builder.py src/deep_agent/__init__.py tests/unit/deep_agent/test_builder.py
git commit -m "feat:新增deep_agent组装器"
```

---

### Task 6: 清理草稿文件

**Files:**
- Delete: `src/deep_agent/agent.py`(导入路径全错的旧草稿,与新结构冲突)

**Interfaces:**
- Consumes: 无
- Produces: 干净的 `src/deep_agent/` 目录(仅 `__init__.py`/`tools.py`/`approval.py`/`subagents.py`/`builder.py`)

- [ ] **Step 1: 确认草稿无被引用**

Run: `grep -rn "deep_agent.agent\|from src.deep_agent import.*agent" src/ tests/ | grep -v "deep_agent.agent" || echo "no direct import of draft"`
另检查 `src/deep_agent/agent.py` 顶部 import 的 `src.core.config`、`src.app.*`、`app.tools.*` 均不存在,确认它是不可用草稿。
Expected: 无任何模块 import 该草稿(它从未被 `__init__.py` 导出)。

- [ ] **Step 2: 删除草稿**

```bash
git rm src/deep_agent/agent.py
```
若该文件尚未被 git 跟踪(状态为 `??`),改用:`rm src/deep_agent/agent.py`。

- [ ] **Step 3: 回归确认未受影响**

Run: `pytest tests/unit/deep_agent/ -v && python -c "from src.deep_agent import build_deep_agent; print('import OK')"`
Expected: 测试全过,打印 `import OK`。

- [ ] **Step 4: 提交**

```bash
git add -A src/deep_agent/
git commit -m "chore:删除deep_agent旧草稿agent.py"
```

---

### Task 7: 独立 API 路由

**Files:**
- Create: `src/api/deep_chat.py`
- Test: `tests/unit/deep_agent/test_deep_chat_api.py`

**Interfaces:**
- Consumes: 现有 `src.api.schemas`(ChatRequest/ChatResponse/ApprovalDecision)、`src.api.stream_parser.parse_graph_event`;运行时读 `req.app.state.deep_graph`
- Produces: `router`(APIRouter,prefix `/api/v1/deep`),含 `chat`/`chat_stream`/`approve` 三端点

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/test_deep_chat_api.py`:
```python
"""deep_chat 路由测试 —— mock deep_graph,验证同步对话端点。"""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from src.api import deep_chat


class _FakeGraph:
    async def ainvoke(self, payload, config):
        return {"messages": [HumanMessage(content="你好"), AIMessage(content="您好,有什么可以帮您?")]}


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(deep_chat.router)
    app.state.deep_graph = _FakeGraph()
    return TestClient(app)


def test_deep_chat_returns_last_ai_message(client):
    resp = client.post(
        "/api/v1/deep/chat",
        json={"message": "你好", "user_id": "u1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "您好,有什么可以帮您?"
    assert body["session_id"]


def test_deep_chat_prefix_isolated_from_existing():
    # 路由前缀必须是 /api/v1/deep,避免与现有 /api/v1/chat 冲突
    assert deep_chat.router.prefix == "/api/v1/deep"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_deep_chat_api.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'src.api.deep_chat'`。

- [ ] **Step 3: 写实现**

Create `src/api/deep_chat.py`:
```python
"""deepagents 版对话路由 —— POST /deep/chat, /deep/chat/stream, /deep/chat/{id}/approve。

与现有 /api/v1/chat 完全并存,读取 app.state.deep_graph,复用现有 schemas 与 stream_parser。
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from src.api.schemas import ApprovalDecision, ChatRequest, ChatResponse
from src.api.stream_parser import parse_graph_event
from src.observability.logging import get_logger
from src.observability.metrics import get_metrics

logger = get_logger("api.deep_chat")
router = APIRouter(prefix="/api/v1/deep", tags=["deep-chat"])


def _build_config(req: ChatRequest, session_id: str) -> dict:
    """构造 LangGraph configurable 配置。"""
    return {
        "configurable": {
            "thread_id": session_id,
            "user_id": req.user_id,
            "access_token": req.access_token or "",
        }
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, req: Request):
    """同步对话 —— 调用 deep_graph 并返回末条 AI 消息。"""
    graph = req.app.state.deep_graph
    session_id = body.session_id or str(uuid.uuid4())
    config = _build_config(body, session_id)

    metrics = get_metrics()
    metrics.increment_request()

    start = datetime.now(timezone.utc)
    result = await graph.ainvoke(
        {"messages": [("user", body.message)]},
        config=config,
    )

    messages = result.get("messages", [])
    last_msg = ""
    agent_name = None
    tool_calls: list[str] = []

    for msg in messages:
        role = getattr(msg, "type", "") if not isinstance(msg, tuple) else msg[0]
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", "") if not isinstance(msg, tuple) else msg[1]
            last_msg = content or last_msg
            if not isinstance(msg, tuple):
                agent_name = getattr(msg, "name", None) or agent_name
            tcs = getattr(msg, "tool_calls", None)
            if tcs:
                tool_calls.extend(tc.get("name", "") for tc in tcs)
        elif role == "tool":
            name = getattr(msg, "name", "") if not isinstance(msg, tuple) else ""
            if name:
                tool_calls.append(name)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    metrics.record_response_time(elapsed)

    return ChatResponse(
        session_id=session_id,
        message=last_msg,
        agent_name=agent_name,
        tool_calls=tool_calls,
        created_at=datetime.now(timezone.utc),
    )


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, req: Request):
    """SSE 流式对话 —— 复用现有 parse_graph_event。"""
    graph = req.app.state.deep_graph
    session_id = body.session_id or str(uuid.uuid4())
    config = _build_config(body, session_id)

    metrics = get_metrics()
    metrics.increment_request()

    async def event_generator():
        try:
            async for event in graph.astream_events(
                {"messages": [("user", body.message)]},
                config=config,
                version="v2",
            ):
                parsed = parse_graph_event(event)
                if parsed is not None:
                    yield f"event: {parsed.event}\ndata: {json.dumps({'data': parsed.data, 'agent_name': parsed.agent_name}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            logger.error("deep_stream_error", error=str(e))
            metrics.increment_error()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/{session_id}/approve")
async def approve(session_id: str, body: ApprovalDecision, req: Request):
    """人机审批恢复 —— 对 deep_graph 执行 Command(resume=...)。"""
    graph = req.app.state.deep_graph

    metrics = get_metrics()
    if body.approved:
        metrics.human_approval_count += 1
    else:
        metrics.human_rejection_count += 1

    logger.info("deep_approval_received", session_id=session_id, approved=body.approved)

    await graph.ainvoke(
        Command(resume={"approved": body.approved, "reason": body.reason or ""}),
        config={"configurable": {"thread_id": session_id}},
    )

    return {
        "session_id": session_id,
        "approved": body.approved,
        "reason": body.reason,
        "status": "processed",
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_deep_chat_api.py -v`
Expected: 2 passed。(若缺 `httpx`/`fastapi.testclient` 依赖,按提示 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple httpx`。)

- [ ] **Step 5: 提交**

```bash
git add src/api/deep_chat.py tests/unit/deep_agent/test_deep_chat_api.py
git commit -m "feat:新增deepagents版独立对话路由"
```

---

### Task 8: 装配到 FastAPI 应用

**Files:**
- Modify: [src/main.py](../../../src/main.py)(仅追加:1 行 import 区追加、lifespan 内追加装配块、文件末尾追加 include_router)
- Test: `tests/unit/deep_agent/test_main_wiring.py`

**Interfaces:**
- Consumes: `src.deep_agent.build_deep_agent`、`src.api.deep_chat`、lifespan 内已有的 `memory`/`mcp_manager`/`registry`
- Produces: 启动后 `app.state.deep_graph` 存在;`/api/v1/deep/*` 路由已注册;现有 `app.state.graph` 与 `/api/v1/chat` 不变

- [ ] **Step 1: 写失败测试**

Create `tests/unit/deep_agent/test_main_wiring.py`:
```python
"""装配测试 —— 验证 main 已注册 deep 路由且未破坏现有路由。"""
from src.main import app


def test_deep_routes_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/deep/chat" in paths
    assert "/api/v1/deep/chat/stream" in paths


def test_existing_chat_routes_still_present():
    paths = {r.path for r in app.routes}
    # 现有路由必须仍在,证明并存未受影响
    assert "/api/v1/chat" in paths
    assert "/api/v1/chat/stream" in paths
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/deep_agent/test_main_wiring.py -v`
Expected: FAIL —— `/api/v1/deep/chat` 不在路由集合中(`test_deep_routes_registered` 失败);`test_existing_chat_routes_still_present` 应通过。

- [ ] **Step 3: 修改 main.py(仅追加)**

在 [src/main.py](../../../src/main.py) 顶部 import 区,现有 `from src.api import chat, health, sessions` 之后追加:
```python
from src.api import deep_chat
from src.deep_agent import build_deep_agent
```

在 lifespan 内,现有 `app.state.graph = graph`(`# --- Agent Graph ---` 块)之后追加:
```python
    # --- Deep Agent (deepagents 版,与上面的 graph 并存) ----------------
    deep_graph = await build_deep_agent(
        mcp_tools=mcp_manager.get_tools(),
        skill_tools=registry.get_all_tools(),
        checkpointer=await memory.get_checkpointer(),
        store=await memory.get_store(),
    )
    app.state.deep_graph = deep_graph
    logger.info("deep_agent_ready")
```

在文件末尾现有 `app.include_router(health.router)` 之后追加:
```python
app.include_router(deep_chat.router)
```

> 注意:不得修改任何现有行;以上均为新增。`mcp_manager.get_tools()`、`registry.get_all_tools()`、`memory.get_checkpointer()/get_store()` 均为现有可用方法。

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/deep_agent/test_main_wiring.py -v`
Expected: 2 passed。

> 若导入 `src.main` 触发 lifespan 外的真实初始化失败(本测试仅 import app、不进入 lifespan,故 deep_graph 的真实构建不会在此运行),按报错排查 import 级副作用。

- [ ] **Step 5: 全量回归 + 现有系统未破坏确认**

Run:
```bash
pytest tests/unit/deep_agent/ -v
python -c "import src.main; print('main import OK')"
```
Expected: deep_agent 全部测试通过;`main import OK`。

- [ ] **Step 6: 提交**

```bash
git add src/main.py tests/unit/deep_agent/test_main_wiring.py
git commit -m "feat:将deepagents版Agent装配到FastAPI应用"
```

---

### Task 9: 文档与收尾

**Files:**
- Modify: `README.md`(新增「deepagents 版 Agent」一节,说明端点与启用方式)

**Interfaces:**
- Consumes: 无
- Produces: 用户可读的使用说明

- [ ] **Step 1: 在 README.md 追加章节**

在 README.md 合适位置追加一节(中文),内容包含:
```markdown
## deepagents 版智能客服 Agent(与 langgraph 版并存)

本项目在原有 langgraph 多 Agent 系统之外,另提供一套基于 deepagents 框架的等价实现,
二者同时在线、互不影响。

- 代码位置:`src/deep_agent/`(主 Agent + 商品/订单/售后/用户/通用 5 个子 Agent)
- 对外端点:
  - `POST /api/v1/deep/chat` —— 同步对话
  - `POST /api/v1/deep/chat/stream` —— SSE 流式对话
  - `POST /api/v1/deep/chat/{session_id}/approve` —— 人机审批恢复
- 原 langgraph 版端点 `POST /api/v1/chat` 等保持不变。
- 依赖:`deepagents~=0.6.11`(已在 requirements.txt)。
```

- [ ] **Step 2: 全量测试最终回归**

Run: `pytest tests/unit/deep_agent/ -v`
Expected: 全部通过(Task 2-8 累计约 19 个测试)。

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs:补充deepagents版Agent使用说明"
```

---

## 任务依赖关系

```
Task 1 (前置验证)
   └─► Task 2 (工具收集) ─► Task 3 (审批) ─► Task 4 (子Agent) ─► Task 5 (组装器)
                                                                      └─► Task 6 (清理草稿)
                                                                      └─► Task 7 (API路由) ─► Task 8 (装配) ─► Task 9 (文档)
```

Task 2→3→4→5 严格顺序(后者依赖前者接口);Task 6 可在 Task 5 后任意时刻进行;Task 7 依赖 Task 5(需 build_deep_agent 存在用于装配,但 API 测试本身 mock graph,可独立);Task 8 依赖 Task 5 与 Task 7;Task 9 最后。
