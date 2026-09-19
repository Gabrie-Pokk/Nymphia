from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    NYMPHIA_DATABASE_URL: str = "sqlite:///./nymphia.db"
    NYMPHIA_SECRET_KEY: str = "nymphia_super_secret_production_ready_key_change_me_in_prod_12345"
    NYMPHIA_S3_BUCKET: str = "nymphia-clinical-records"
    GEMINI_API_KEY: Optional[str] = None
    ENVIRONMENT: str = "development"
    
    # JWT algorithm and expiration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=[
            str(_BACKEND_DIR / ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
