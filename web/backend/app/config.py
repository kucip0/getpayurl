import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "GetPayurl Web"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 数据库
    DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent / 'getpayurl.db'}"

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
