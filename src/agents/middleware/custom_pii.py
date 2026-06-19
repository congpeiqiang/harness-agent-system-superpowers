"""中国 PII 脱敏中间件 — 检测并脱敏中国手机号、身份证号、银行卡号"""
import re
from typing import Any

import structlog
from langchain_core.messages import AIMessage, HumanMessage

try:
    from langchain.agents.middleware import AgentMiddleware
except ImportError:
    try:
        from langgraph.prebuilt.middleware import AgentMiddleware
    except ImportError:
        # Fallback base class when no middleware framework is installed
        class AgentMiddleware:  # type: ignore[no-redef]
            """Minimal base class for environments without langchain/langgraph."""
            pass

logger = structlog.get_logger(__name__)

# 正则模式：中国手机号、18位身份证号、16-19位银行卡号
_PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
_ID_CARD_RE = re.compile(r"(?<!\d)(\d{17}[\dXx])(?!\d)")
_BANK_CARD_RE = re.compile(r"(?<!\d)(\d{15,18}\d)(?!\d)")


def _mask_phone(match: re.Match) -> str:
    """手机号脱敏：保留前3后4，中间****"""
    phone = match.group(1)
    return f"{phone[:3]}****{phone[7:]}"


def _mask_id_card(match: re.Match) -> str:
    """身份证号脱敏：保留前4后4，中间**********"""
    id_card = match.group(1)
    return f"{id_card[:4]}**********{id_card[-4:]}"


def _mask_bank_card(match: re.Match) -> str:
    """银行卡号脱敏：保留前4后4，中间****"""
    card = match.group(1)
    return f"{card[:4]}****{card[-4:]}"


class ChinaPIIMiddleware(AgentMiddleware):
    """中国 PII 脱敏中间件。

    在模型调用前脱敏用户输入中的中国手机号、身份证号、银行卡号；
    在模型调用后脱敏 LLM 输出中可能泄露的同类信息。
    """

    def redact(self, text: str) -> str:
        """对文本中的中国敏感信息进行脱敏处理。

        Args:
            text: 待脱敏文本

        Returns:
            脱敏后的文本
        """
        # 按顺序应用：身份证 → 银行卡 → 手机号
        # 身份证号最长(18位)，优先匹配，避免被银行卡正则误匹配
        result = _ID_CARD_RE.sub(_mask_id_card, text)
        result = _BANK_CARD_RE.sub(_mask_bank_card, result)
        result = _PHONE_RE.sub(_mask_phone, result)
        return result

    def before_model(self, state: dict, runtime: Any) -> dict[str, Any] | None:
        """模型调用前：脱敏最后一条用户消息。"""
        messages = state.get("messages", [])
        if not messages:
            return None

        # 找到最后一条 HumanMessage
        last_user_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if isinstance(messages[i], HumanMessage):
                last_user_idx = i
                break

        if last_user_idx is None:
            return None

        msg = messages[last_user_idx]
        if not msg.content:
            return None

        content = str(msg.content)
        new_content = self.redact(content)

        if new_content == content:
            return None

        logger.debug("china_pii_redacted_input", original_len=len(content))

        new_messages = list(messages)
        new_messages[last_user_idx] = HumanMessage(
            content=new_content, id=msg.id, name=msg.name
        )
        return {"messages": new_messages}

    def after_model(self, state: dict, runtime: Any) -> dict[str, Any] | None:
        """模型调用后：脱敏最后一条 AI 消息。"""
        messages = state.get("messages", [])
        if not messages:
            return None

        # 找到最后一条 AIMessage
        last_ai_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if isinstance(messages[i], AIMessage):
                last_ai_idx = i
                break

        if last_ai_idx is None:
            return None

        msg = messages[last_ai_idx]
        if not msg.content:
            return None

        content = str(msg.content)
        new_content = self.redact(content)

        if new_content == content:
            return None

        logger.debug("china_pii_redacted_output", original_len=len(content))

        new_messages = list(messages)
        new_messages[last_ai_idx] = AIMessage(
            content=new_content,
            id=msg.id,
            name=msg.name,
            tool_calls=msg.tool_calls,
        )
        return {"messages": new_messages}
