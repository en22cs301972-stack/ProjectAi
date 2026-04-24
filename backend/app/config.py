import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Learning Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/aiplatform"
    DATABASE_URL_SYNC: str = "postgresql://user:password@localhost:5432/aiplatform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Encryption key for API key storage
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here!!"

    # Code execution
    CODE_EXECUTION_TIMEOUT: int = 30
    MAX_CODE_LENGTH: int = 10000

    # Certificate
    CERTIFICATE_TEMPLATE_PATH: str = "app/assets/certificate_template.png"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
