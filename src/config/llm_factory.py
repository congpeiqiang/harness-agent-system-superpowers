"""多模型工厂 — 统一管理多个 LLM 提供商"""
from langchain_openai import ChatOpenAI
from src.config.settings import get_settings


class LLMFactory:
    """多模型工厂。所有提供商使用 OpenAI 兼容格式（ChatOpenAI），通过 base_url 切换不同后端。"""

    _instances: dict[str, ChatOpenAI] = {}

    @classmethod
    def create(cls, agent_name: str = "default") -> ChatOpenAI:
        """根据 agent 名称创建或获取对应的 ChatOpenAI 实例。

        查找优先级：
        1. 检查 agent_overrides 中是否有该 agent 的覆盖配置
        2. 若有覆盖，使用覆盖指定的 provider/model
        3. 若无覆盖，使用默认 provider 及其 model
        4. 相同 provider+model 组合会缓存复用实例
        """
        settings = get_settings()
        llm_config = settings.llm

        # 查找 agent 覆盖配置
        override = llm_config.agent_overrides.get(agent_name)
        if override:
            provider_name = override.provider or llm_config.default_provider
            model_name = override.model
        else:
            provider_name = llm_config.default_provider
            model_name = None

        # 获取提供商配置
        provider = llm_config.providers.get(provider_name)
        if not provider:
            raise ValueError(f"未知的 LLM 提供商: {provider_name}")

        # 解析 API Key：优先使用提供商配置中的 key，其次使用全局环境变量 key
        api_key = provider.api_key
        if provider_name == "openai":
            api_key = api_key or settings.openai_api_key
        elif provider_name == "deepseek":
            api_key = api_key or settings.deepseek_api_key

        # 确定最终使用的模型名称
        final_model = model_name or provider.model

        # 缓存 key = 提供商:模型，相同组合复用实例
        cache_key = f"{provider_name}:{final_model}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = ChatOpenAI(
                base_url=provider.base_url,
                api_key=api_key or "not-set",
                model=final_model,
                temperature=provider.temperature,
            )

        return cls._instances[cache_key]
