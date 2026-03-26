from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SiteANA"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql://siteana:siteana_password@localhost:5432/siteana"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"  # 允許額外欄位，解決 Alembic 呼叫時的問題
    )

settings = Settings()
