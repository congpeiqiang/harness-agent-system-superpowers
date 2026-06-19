"""UserAgent — 用户账户与地址管理专家。"""
from src.agents.base_agent import BaseAgent
from src.tools.fecmall.customer_tools import (
    add_address,
    get_address_list,
    get_user_profile,
    login,
    register,
    remove_address,
    update_profile,
)


class UserAgent(BaseAgent):
    """用户 Agent，负责登录注册、个人资料和收货地址管理。"""

    name: str = "user"
    system_prompt: str = (
        "你是一个专业的用户账户助手。你可以帮助用户登录、注册新账户、"
        "查看和更新个人资料，以及管理收货地址（添加、查看、删除）。"
        "请在执行敏感操作（如修改资料、删除地址）前向用户确认。"
        "回答时请使用中文，注意保护用户的隐私信息。"
    )

    def get_tools(self) -> list:
        """返回用户相关的 7 个工具。"""
        return [
            login,
            register,
            get_user_profile,
            update_profile,
            get_address_list,
            add_address,
            remove_address,
        ]
