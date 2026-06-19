"""Tests for BaseAgent and 5 professional agents."""
import pytest
from unittest.mock import MagicMock


class TestBaseAgent:
    """BaseAgent is abstract and cannot be instantiated directly."""

    def test_cannot_instantiate(self):
        from src.agents.base_agent import BaseAgent
        with pytest.raises(TypeError):
            BaseAgent()

    def test_subclass_must_implement_get_tools(self):
        from src.agents.base_agent import BaseAgent

        class IncompleteAgent(BaseAgent):
            name = "test"
            system_prompt = "test"

        with pytest.raises(TypeError):
            IncompleteAgent()

    def test_subclass_with_get_tools_works(self):
        from src.agents.base_agent import BaseAgent

        class CompleteAgent(BaseAgent):
            name = "test"
            system_prompt = "test"

            def get_tools(self):
                return []

        agent = CompleteAgent()
        assert agent.name == "test"
        assert agent.get_tools() == []


class TestProductAgent:
    def test_tool_count(self):
        from src.agents.product_agent import ProductAgent
        agent = ProductAgent()
        assert len(agent.get_tools()) == 5

    def test_tool_names(self):
        from src.agents.product_agent import ProductAgent
        agent = ProductAgent()
        tool_names = {t.name for t in agent.get_tools()}
        assert tool_names == {
            "search_products",
            "get_product_detail",
            "get_category_products",
            "get_product_reviews",
            "get_home_info",
        }

    def test_name_and_prompt(self):
        from src.agents.product_agent import ProductAgent
        agent = ProductAgent()
        assert agent.name == "product"
        assert agent.system_prompt  # non-empty


class TestOrderAgent:
    def test_tool_count(self):
        from src.agents.order_agent import OrderAgent
        agent = OrderAgent()
        assert len(agent.get_tools()) == 8

    def test_tool_names(self):
        from src.agents.order_agent import OrderAgent
        agent = OrderAgent()
        tool_names = {t.name for t in agent.get_tools()}
        assert tool_names == {
            "get_cart",
            "add_to_cart",
            "update_cart_item",
            "remove_cart_item",
            "get_checkout_init",
            "submit_order",
            "get_order_list",
            "get_order_detail",
        }

    def test_name_and_prompt(self):
        from src.agents.order_agent import OrderAgent
        agent = OrderAgent()
        assert agent.name == "order"
        assert agent.system_prompt


class TestAfterSaleAgent:
    def test_tool_count(self):
        from src.agents.aftersale_agent import AfterSaleAgent
        agent = AfterSaleAgent()
        assert len(agent.get_tools()) == 3

    def test_tool_names(self):
        from src.agents.aftersale_agent import AfterSaleAgent
        agent = AfterSaleAgent()
        tool_names = {t.name for t in agent.get_tools()}
        assert tool_names == {
            "submit_complaint",
            "get_refund_status",
            "rag_search",
        }

    def test_name_and_prompt(self):
        from src.agents.aftersale_agent import AfterSaleAgent
        agent = AfterSaleAgent()
        assert agent.name == "aftersale"
        assert agent.system_prompt


class TestGeneralAgent:
    def test_no_extra_tools(self):
        from src.agents.general_agent import GeneralAgent
        agent = GeneralAgent()
        assert agent.get_tools() == []

    def test_with_extra_tools(self):
        from src.agents.general_agent import GeneralAgent
        mock_tool1 = MagicMock()
        mock_tool1.name = "mcp_tool_1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "skill_tool_1"
        agent = GeneralAgent(extra_tools=[mock_tool1, mock_tool2])
        assert len(agent.get_tools()) == 2
        tool_names = {t.name for t in agent.get_tools()}
        assert tool_names == {"mcp_tool_1", "skill_tool_1"}

    def test_name_and_prompt(self):
        from src.agents.general_agent import GeneralAgent
        agent = GeneralAgent()
        assert agent.name == "general"
        assert agent.system_prompt


class TestUserAgent:
    def test_tool_count(self):
        from src.agents.user_agent import UserAgent
        agent = UserAgent()
        assert len(agent.get_tools()) == 7

    def test_tool_names(self):
        from src.agents.user_agent import UserAgent
        agent = UserAgent()
        tool_names = {t.name for t in agent.get_tools()}
        assert tool_names == {
            "login",
            "register",
            "get_user_profile",
            "update_profile",
            "get_address_list",
            "add_address",
            "remove_address",
        }

    def test_name_and_prompt(self):
        from src.agents.user_agent import UserAgent
        agent = UserAgent()
        assert agent.name == "user"
        assert agent.system_prompt
