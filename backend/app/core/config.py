"""
Core configuration for the Chatbot application.
Uses Pydantic Settings for environment variable management.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="Chatbot")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Gemini/Vertex AI Configuration (via Proxy)
    endpoint: str = Field(default="", description="API endpoint URL")
    api_key: str = Field(default="", description="API key for authentication")
    deployment_name: str = Field(default="vertex_ai.gemini-3-pro-preview", description="Model deployment name")
    embedding_deployment: str = Field(default="vertex_ai.gemini-3-embedding", description="Embedding model deployment name")

    # AI Configuration
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
