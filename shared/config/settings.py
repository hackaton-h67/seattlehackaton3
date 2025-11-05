"""
Configuration settings for Service-Sense.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    log_level: str = "info"

    # LLM Configuration
    llm_provider: str = "claude"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5-20250929"
    openai_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    llm_timeout: int = 30

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    neo4j_database: str = "service-sense"
    neo4j_max_connections: int = 50

    # ChromaDB Configuration
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "service-requests"

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "service_sense"
    postgres_user: str = "service_sense"
    postgres_password: str = "changeme"
    postgres_max_connections: int = 20

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # Seattle Open Data
    seattle_data_api: str = "https://data.seattle.gov/resource/5ngg-rpne.json"
    seattle_data_app_token: Optional[str] = None
    seattle_data_sync_interval: int = 3600

    # ML Configuration
    ml_model_path: str = "ml/models"
    ml_ensemble_weights: str = "0.25,0.25,0.25,0.25"
    ml_prediction_threshold: float = 0.7
    ml_confidence_level: float = 0.90

    # Audio Processing
    whisper_model: str = "large-v3"
    whisper_language: str = "en"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    audio_max_duration: int = 300
    audio_sample_rate: int = 16000

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32

    # Feature Flags
    enable_audio_input: bool = True
    enable_graph_search: bool = True
    enable_vector_search: bool = True
    enable_ml_prediction: bool = True
    enable_ab_testing: bool = False
    enable_feedback_loop: bool = True
    enable_location_features: bool = True
    enable_temporal_features: bool = True
    enable_historical_features: bool = True

    # Performance & Limits
    max_request_size_mb: int = 10
    request_timeout_seconds: int = 30
    rate_limit_per_minute: int = 100
    cache_ttl_seconds: int = 300

    # Security
    secret_key: str = "changeme-in-production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    enable_api_key_auth: bool = False
    api_key: Optional[str] = None

    # Development
    debug: bool = False
    testing: bool = False
    mock_llm: bool = False
    mock_audio_processing: bool = False

    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def chroma_url(self) -> str:
        """Construct ChromaDB connection URL."""
        return f"http://{self.chroma_host}:{self.chroma_port}"


# Global settings instance
settings = Settings()
