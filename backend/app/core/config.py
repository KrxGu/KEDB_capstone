from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "KEDB Platform"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://kedb:kedb@localhost:5432/kedb"
    sync_database_url: str = "postgresql+psycopg://kedb:kedb@localhost:5432/kedb"
    redis_url: str = "redis://localhost:6379/0"
    rq_default_queue: str = "default"
    meilisearch_url: AnyUrl = "http://localhost:7700"
    meilisearch_master_key: str = "local_master_key"

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    reranker_model: str = "ms-marco-MiniLM-L-12-v2"
    suggestion_top_k: int = 5

    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8080
    worker_concurrency: int = 2

    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
