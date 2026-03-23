from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application Settings
    Loads from environment variables with defaults for development
    """
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/te_platform"
    DATABASE_ECHO: bool = False
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AES Encryption Configuration
    AES_KEY: str = None  # Must be 32 bytes (256 bits) - will be base64 encoded
    AES_IV: str = None   # Must be 16 bytes (128 bits) - will be base64 encoded
    
    # Application Configuration
    APP_NAME: str = "TE Legal Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Audit Configuration
    ENABLE_AUDIT_LOGGING: bool = True
    AUDIT_RETENTION_DAYS: int = 365
    
    # Bcrypt Configuration
    BCRYPT_ROUNDS: int = 12
    
    MISTRAL_API_KEY: str = ""
    
    class Config:
        # Use absolute path to .env in backend directory
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This ensures settings are loaded only once.
    """
    return Settings()
