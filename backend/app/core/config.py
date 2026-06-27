"""
Application configuration module.

Handles all configuration settings from environment variables using Pydantic.
"""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # FastAPI Configuration
    DEBUG: bool = False
    APP_NAME: str = "AI Analytics Dashboard"
    APP_VERSION: str = "1.0.0"

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str | None = None

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./analytics.db"

    # Groq API Configuration
    GROQ_API_KEY: str

    # File Upload Configuration
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # Supabase Storage
    SUPABASE_STORAGE_BUCKET: str = "analytics-files"

    @property
    def SUPABASE_JWKS_URL(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
