"""
Configuration settings for Agentic AI Demo
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # General Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_KEY: str = "demo-api-key-2024"
    
    # LLM Configuration (Ollama)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024
    LLM_TOP_P: float = 0.9
    LLM_TIMEOUT: int = 60
    
    # Vector Database (ChromaDB)
    CHROMA_HOST: str = "http://localhost:8000"
    CHROMA_COLLECTION_NAME: str = "incidents"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600
    
    # PostgreSQL Configuration (Optional)
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agentic"
    POSTGRES_USER: str = "agentic"
    POSTGRES_PASSWORD: str = "agentic123"
    
    # RAG Configuration
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K_RESULTS: int = 5
    RAG_RERANK_ENABLED: bool = True
    RAG_HYBRID_SEARCH: bool = True
    
    # CAG Configuration
    CAG_ENABLED: bool = True
    CAG_CORRECTION_THRESHOLD: float = 0.7
    CAG_MAX_ITERATIONS: int = 3
    CAG_CONFIDENCE_TARGET: float = 0.85
    CAG_FEEDBACK_WEIGHT: float = 0.3
    
    # Predictive Analytics
    PREDICTION_ENABLED: bool = True
    PREDICTION_MODEL: str = "random_forest"
    PREDICTION_UPDATE_FREQUENCY: int = 3600
    PREDICTION_MIN_SAMPLES: int = 100
    
    # Agent Configuration
    AGENT_MAX_CONCURRENT: int = 5
    AGENT_TIMEOUT: int = 300
    AGENT_RETRY_ATTEMPTS: int = 3
    AGENT_LEARNING_RATE: float = 0.01
    
    # Monitoring
    MONITORING_ENABLED: bool = True
    METRICS_EXPORT_INTERVAL: int = 60
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3002
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:80"
    
    # Feature Flags
    FEATURE_REAL_TIME_UPDATES: bool = True
    FEATURE_AUTO_TRIAGE: bool = True
    FEATURE_KNOWLEDGE_GRAPH: bool = True
    FEATURE_SENTIMENT_ANALYSIS: bool = True
    FEATURE_MULTI_AGENT: bool = True
    
    # Performance Tuning
    MAX_CONNECTIONS: int = 100
    CONNECTION_TIMEOUT: int = 30
    REQUEST_TIMEOUT: int = 60
    BATCH_SIZE: int = 32
    
    # Development Settings
    HOT_RELOAD: bool = True
    MOCK_DATA: bool = True
    SAMPLE_DATA_SIZE: int = 1000
    SEED_VALUE: int = 42
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

# Create settings instance
settings = Settings()