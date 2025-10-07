from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
from typing import Optional

class Settings(BaseSettings):
    GITHUB_TOKEN: str = Field(..., env="GITHUB_TOKEN")
    LLM_API_KEY: Optional[str] = Field(None, env="LLM_API_KEY")
    STUDENT_SECRET: Optional[str] = Field(None, env="STUDENT_SECRET")
    EVALUATOR_URL: Optional[AnyHttpUrl] = Field(None, env="EVALUATOR_URL")
    APP_ENV: str = Field("dev", env="APP_ENV")
    PORT: int = Field(8000, env="PORT")
    RETRY_MAX_ATTEMPTS: int = Field(5, env="RETRY_MAX_ATTEMPTS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached settings instance. Use this instead of creating Settings() directly
    so the same instance is reused across imports.
    """
    return Settings()
