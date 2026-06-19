"""双层记忆管理 — AsyncSqliteSaver (会话) + AsyncSqliteStore (长期)"""
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.sqlite import AsyncSqliteStore
from src.observability.logging import get_logger

logger = get_logger("memory")

class MemoryManager:
    """双层记忆：1. Checkpointer（会话内短期） 2. Store（跨会话长期）"""
    def __init__(self, checkpoint_db: str, store_db: str):
        self.checkpoint_db = checkpoint_db
        self.store_db = store_db
        self._checkpointer = None
        self._checkpointer_cm = None
        self._store = None
        self._store_cm = None

    async def get_checkpointer(self) -> AsyncSqliteSaver:
        if self._checkpointer is None:
            self._checkpointer_cm = AsyncSqliteSaver.from_conn_string(self.checkpoint_db)
            self._checkpointer = await self._checkpointer_cm.__aenter__()
        return self._checkpointer

    async def get_store(self) -> AsyncSqliteStore:
        if self._store is None:
            self._store_cm = AsyncSqliteStore.from_conn_string(self.store_db)
            self._store = await self._store_cm.__aenter__()
        return self._store

    async def save_user_preference(self, user_id: str, key: str, value: dict):
        store = await self.get_store()
        await store.aput(namespace=(user_id, "preferences"), key=key, value=value)
        logger.info("preference_saved", user_id=user_id, key=key)

    async def get_user_preferences(self, user_id: str) -> dict:
        store = await self.get_store()
        items = await store.asearch((user_id, "preferences"))
        return {item.key: item.value for item in items}

    async def close(self):
        if self._checkpointer_cm:
            await self._checkpointer_cm.__aexit__(None, None, None)
        if self._store_cm:
            await self._store_cm.__aexit__(None, None, None)
