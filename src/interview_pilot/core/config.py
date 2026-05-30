from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InterviewPilot"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    api_version: str = "v1"
    debug: bool = True
    secret_key: str = "change-me-please-use-a-very-long-random-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite+aiosqlite:///./temps/interview_pilot.db"
    redis_url: str = "redis://localhost:6379/0"
    # 学习重点：默认用 memory，保证不启动 Redis 也能跑测试；部署时改成 redis。
    cache_backend: Literal["memory", "redis"] = "memory"
    dashboard_cache_ttl_seconds: int = 300
    message_queue_backend: Literal["memory", "redis"] = "memory"
    message_queue_name: str = "interview_pilot:events"
    enable_background_worker: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
