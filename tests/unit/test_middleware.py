"""中间件单元测试"""
import pytest
from src.agents.middleware.custom_pii import ChinaPIIMiddleware


@pytest.fixture
def pii_middleware():
    return ChinaPIIMiddleware()


class TestChinaPIIMiddlewareRedact:
    """测试 ChinaPIIMiddleware.redact() 方法"""

    def test_redact_phone_number(self, pii_middleware):
        """手机号应被脱敏：保留前3后4，中间用****替代"""
        text = "我的手机号是13812345678，请联系我"
        result = pii_middleware.redact(text)
        assert "138****5678" in result
        assert "13812345678" not in result

    def test_redact_id_card(self, pii_middleware):
        """18位身份证号应被脱敏：保留前4后4，中间用**********替代"""
        text = "我的身份证号是110101199001011234"
        result = pii_middleware.redact(text)
        assert "1101**********1234" in result
        assert "110101199001011234" not in result

    def test_redact_bank_card(self, pii_middleware):
        """16-19位银行卡号应被脱敏：保留前4后4，中间用****替代"""
        text = "我的银行卡号是6222021234567890123"
        result = pii_middleware.redact(text)
        assert "6222****0123" in result
        assert "6222021234567890123" not in result

    def test_clean_text_unchanged(self, pii_middleware):
        """不含敏感信息的文本不应被修改"""
        text = "这是一段普通的文本，没有任何敏感信息"
        result = pii_middleware.redact(text)
        assert result == text

    def test_redact_multiple_pii(self, pii_middleware):
        """同一段文本中的多个敏感信息应全部被脱敏"""
        text = "手机号13900001111，身份证110101199505051234"
        result = pii_middleware.redact(text)
        assert "139****1111" in result
        assert "1101**********1234" in result
        assert "13900001111" not in result
        assert "110101199505051234" not in result
