"""用户画像管理"""
from .memory_manager import MemoryManager
from src.observability.logging import get_logger

logger = get_logger("user_profile")

class UserProfileManager:
    def __init__(self, memory: MemoryManager):
        self.memory = memory

    async def get_profile_summary(self, user_id: str) -> dict:
        prefs = await self.memory.get_user_preferences(user_id)
        if not prefs:
            return {"note": "新用户，暂无画像数据"}
        return prefs

    async def update_from_conversation(self, user_id: str, insights: dict):
        for key, value in insights.items():
            await self.memory.save_user_preference(user_id, key, value)
        logger.info("profile_updated", user_id=user_id, fields=list(insights.keys()))
