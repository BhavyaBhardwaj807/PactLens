from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import os

# Load .env file explicitly
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    api_title: str = "PactLens API"
    api_description: str = "Legal contract analysis with RAG"
    api_version: str = "0.1.0"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # File Upload
    upload_dir: str = "./data/uploads"
    max_upload_size: int = 50 * 1024 * 1024
    allowed_extensions: list = ["pdf"]
    
    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    embedding_model: str = "models/embedding-001"
    
    # RAG
    chunk_size: int = 1000
    chunk_overlap: int = 100
    top_k_similar: int = 5
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ✅ THIS IS THE KEY FIX
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # 👈 prevents crash
    )


settings = Settings()
