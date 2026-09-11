import secrets
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowly 2.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./knowly.db"
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Default Models
    DEFAULT_FAST_MODEL: str = "groq/llama-3.3-70b-versatile"
    DEFAULT_REASONING_MODEL: str = "openai/gpt-4o"
    DEFAULT_COMPLEX_MODEL: str = "anthropic/claude-3-5-sonnet"

    # Security - auto-generated if not provided (dev only)
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    STORAGE_DIR: str = "./storage"

    # CORS - comma-separated origins, defaults to dev hosts
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID: Optional[str] = None
    STRIPE_PRO_PRICE_ID: str = "price_pro_placeholder"

    # Plan Limits
    FREE_PLAN_DOC_LIMIT: int = 5

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def effective_stripe_price_id(self) -> str:
        return self.STRIPE_PRICE_ID or self.STRIPE_PRO_PRICE_ID or "price_pro_placeholder"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
