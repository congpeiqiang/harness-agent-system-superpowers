import pytest
from src.memory.memory_manager import MemoryManager

@pytest.mark.asyncio
async def test_memory_manager_init():
    manager = MemoryManager(":memory:", ":memory:")
    checkpointer = await manager.get_checkpointer()
    assert checkpointer is not None
    store = await manager.get_store()
    assert store is not None

@pytest.mark.asyncio
async def test_user_preference_save_and_get():
    manager = MemoryManager(":memory:", ":memory:")
    await manager.save_user_preference("user1", "language", {"value": "zh-CN"})
    prefs = await manager.get_user_preferences("user1")
    assert "language" in prefs
    assert prefs["language"]["value"] == "zh-CN"
