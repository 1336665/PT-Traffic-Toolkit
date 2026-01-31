import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "PT Manager Pro"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/pt_manager.db"

    # JWT settings
    # SECURITY: SECRET_KEY must be set via environment variable in production
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Set to True to allow insecure default SECRET_KEY (NOT recommended for production)
    ALLOW_INSECURE_SECRET_KEY: bool = False

    # CORS settings
    # In production, set this to your frontend domain(s)
    # Example: "http://localhost:8080,https://yourdomain.com"
    CORS_ORIGINS: str = "*"

    # Data directory
    DATA_DIR: Path = Path("./data")

    # Telegram (optional)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # HTTP client defaults
    HTTP_TIMEOUT: float = 30.0
    # SECURITY: SSL verification is enabled by default. Only disable for trusted internal networks
    HTTP_VERIFY_SSL: bool = True
    HTTP_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # RSS tuning
    RSS_MAX_CONCURRENT_FREE_CHECKS: int = 8

    # Scheduler defaults
    SCHEDULER_JOB_MAX_INSTANCES: int = 1
    SCHEDULER_JOB_COALESCE: bool = True
    SCHEDULER_MISFIRE_GRACE_TIME: int = 60

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Security check for SECRET_KEY
_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"
if settings.SECRET_KEY == _DEFAULT_SECRET_KEY:
    import warnings
    if settings.ALLOW_INSECURE_SECRET_KEY:
        warnings.warn(
            "WARNING: Using default SECRET_KEY. This is insecure and should only be used for development!",
            UserWarning,
            stacklevel=1
        )
    else:
        raise ValueError(
            "SECURITY ERROR: Default SECRET_KEY detected. "
            "Please set a secure SECRET_KEY via environment variable or .env file. "
            "If you understand the risks and want to proceed anyway (development only), "
            "set ALLOW_INSECURE_SECRET_KEY=true"
        )

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
