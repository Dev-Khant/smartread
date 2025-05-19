import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    WORKERS: int = 1
    
    # Database settings
    MONGODB_URL: str
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # API Keys
    MISTRAL_API_KEY: str
    GROQ_API_KEY: str
    SERPER_API_KEY: Optional[str] = None
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: str = "1/minute"
    
    # Processing settings
    MAX_CONCURRENT_PAGES: int = 3
    MAX_RETRIES: int = 3
    CACHE_TTL: int = 3600
    
    # Feature flags
    USE_ASYNC_ROUTES: bool = True
    ENABLE_CACHING: bool = True
    ENABLE_RATE_LIMITING: bool = True
    
    @validator("ALLOWED_ORIGINS")
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("MONGODB_URL")
    def validate_mongodb_url(cls, v):
        if not v:
            raise ValueError("MONGODB_URL is required")
        return v
    
    @validator("MISTRAL_API_KEY")
    def validate_mistral_key(cls, v):
        if not v:
            raise ValueError("MISTRAL_API_KEY is required")
        return v
    
    @validator("GROQ_API_KEY")
    def validate_groq_key(cls, v):
        if not v:
            raise ValueError("GROQ_API_KEY is required")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    ENVIRONMENT: str = "development"
    WORKERS: int = 1
    ENABLE_RATE_LIMITING: bool = False


class ProductionSettings(Settings):
    """Production environment settings"""
    ENVIRONMENT: str = "production"
    WORKERS: int = 4
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_REQUESTS: int = 5


class TestingSettings(Settings):
    """Testing environment settings"""
    ENVIRONMENT: str = "testing"
    MONGODB_URL: str = "mongodb://localhost:27017/smartread_test"
    REDIS_URL: Optional[str] = None
    ENABLE_CACHING: bool = False


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Export the appropriate settings
settings = get_settings()
