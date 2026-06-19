"""配置管理 — pydantic-settings + YAML"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class LLMProviderConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.3

class AgentOverride(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None

class LLMConfig(BaseModel):
    default_provider: str = "deepseek"
    providers: dict[str, LLMProviderConfig] = {}
    agent_overrides: dict[str, AgentOverride] = {}

class FecMallConfig(BaseModel):
    base_url: str = "http://localhost/appserver"
    default_currency: str = "USD"
    default_lang: str = "en_US"
    timeout: int = 30

class MilvusConfig(BaseModel):
    uri: str = "http://localhost:19530"
    token: str = ""
    collection_name: str = "fecmall_knowledge"

class EmbeddingConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "text-embedding-3-small"

class SummarizationConfig(BaseModel):
    max_tokens: int = 4000
    keep_messages: int = 6

class HumanInTheLoopConfig(BaseModel):
    enabled: bool = True
    approve_tool_names: list[str] = []

class ToolCallLimitConfig(BaseModel):
    run_limit: int = 15
    thread_limit: int = 100

class RetryConfig(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 2.0

class ModelRetryConfig(BaseModel):
    max_retries: int = 3
    retry_delay: float = 1.0

class MiddlewareConfig(BaseModel):
    summarization: SummarizationConfig = SummarizationConfig()
    human_in_the_loop: HumanInTheLoopConfig = HumanInTheLoopConfig()
    tool_call_limit: ToolCallLimitConfig = ToolCallLimitConfig()
    tool_retry: RetryConfig = RetryConfig()
    model_retry: ModelRetryConfig = ModelRetryConfig()

class LangSmithConfig(BaseModel):
    enabled: bool = True
    project: str = "fecmall-agent"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"

class ObservabilityConfig(BaseModel):
    langsmith: LangSmithConfig = LangSmithConfig()
    logging: LoggingConfig = LoggingConfig()

# 嵌套配置段前缀映射，用于环境变量覆盖 (如 FECMALL_BASE_URL -> fecmall.base_url)
_NESTED_ENV_PREFIXES = ("FECMALL", "MILVUS", "EMBEDDING", "LLM")

class Settings(BaseSettings):
    llm: LLMConfig = LLMConfig()
    fecmall: FecMallConfig = FecMallConfig()
    milvus: MilvusConfig = MilvusConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    middleware: MiddlewareConfig = MiddlewareConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    weather_api_key: str = Field(default="", alias="WEATHER_API_KEY")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    model_config = {"env_prefix": "", "extra": "ignore"}

    def __init__(self, **kwargs):
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
            merged = {**yaml_config, **kwargs}
        else:
            merged = {**kwargs}
        # 环境变量覆盖嵌套配置 (支持 FECMALL_BASE_URL -> fecmall.base_url 格式)
        for env_key, env_val in os.environ.items():
            upper = env_key.upper()
            for prefix in _NESTED_ENV_PREFIXES:
                if upper.startswith(prefix + "_"):
                    section = prefix.lower()
                    field = upper[len(prefix) + 1:].lower()
                    if section in merged and isinstance(merged[section], dict) and field in merged[section]:
                        merged[section][field] = env_val
        super().__init__(**merged)
        if self.openai_api_key and "openai" in self.llm.providers:
            self.llm.providers["openai"].api_key = self.openai_api_key
        if self.deepseek_api_key and "deepseek" in self.llm.providers:
            self.llm.providers["deepseek"].api_key = self.deepseek_api_key

@lru_cache()
def get_settings() -> Settings:
    return Settings()
