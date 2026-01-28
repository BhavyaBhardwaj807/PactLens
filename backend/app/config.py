"""
PactLens Backend - Configuration
Environment and app settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    api_title: str = "PactLens API"
    api_description: str = "Legal contract analysis with RAG"
    api_version: str = "0.1.0"
    
    # Environment
    environment: str = os.getenv("FASTAPI_ENV", "development")
    debug: bool = environment == "development"
    
    # File Upload
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = ["pdf"]
    
    # Google Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-1.5-pro"
    embedding_model: str = "models/embedding-001"
    
    # RAG
    chunk_size: int = 1000
    chunk_overlap: int = 100
    top_k_similar: int = 5
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"


settings = Settings()
