from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InterviewPilot"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    api_version: str = "v1"
    debug: bool = True
    secret_key: str = "change-me"
    database_url: str = "sqlite+aiosqlite:///./interview_pilot.db"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
