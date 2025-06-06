import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="DEBUG")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_KEY: Optional[str] = None
    JWT_SECRET: str = Field(default="your-secret-key-change-in-production")
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/agentic_comms")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    REDIS_STREAM_BATCH_SIZE: int = Field(default=10)
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = Field(...)
    AZURE_OPENAI_ENDPOINT: str = Field(...)
    AZURE_OPENAI_DEPLOYMENT: str = Field(default="gpt-4o")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-01")
    
    # Deepgram
    DEEPGRAM_API_KEY: str = Field(...)
    
    # Pinecone
    PINECONE_API_KEY: str = Field(...)
    PINECONE_ENVIRONMENT: str = Field(default="us-west1-gcp-free")
    PINECONE_INDEX_NAME: str = Field(default="agentic-comms-memory")
    
    # Email Configuration
    EMAIL_PROVIDER: str = Field(default="smtp")
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Grafana Observability
    GRAFANA_API_KEY: Optional[str] = None
    GRAFANA_ORG_ID: Optional[str] = None
    
    # Scaling Configuration
    MAX_CONCURRENT_AGENTS: int = Field(default=1000)
    WORKER_POOL_SIZE: int = Field(default=50)
    
    # Performance Targets
    MAX_RESPONSE_TIME_MS: int = Field(default=5000)
    MAX_TTS_LATENCY_MS: int = Field(default=1000)
    TARGET_AUTO_RESOLUTION_RATE: float = Field(default=0.8)
    
    # Feature Flags
    ENABLE_VOICE: bool = Field(default=True)
    ENABLE_EMAIL: bool = Field(default=True)
    ENABLE_CHAT: bool = Field(default=True)
    ENABLE_ESCALATION: bool = Field(default=True)
    ENABLE_VECTOR_MEMORY: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment

# Global settings instance
settings = Settings()

# Validation
def validate_settings():
    """Validate critical settings"""
    required_keys = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "DEEPGRAM_API_KEY",
        "PINECONE_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not getattr(settings, key, None):
            missing_keys.append(key)
    
    if missing_keys:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
    
    return True 