"""
Configuration settings for the RAG chatbot application.
"""
import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)

# Find project root (where .env file should be)
def find_project_root():
    """Find the project root directory by looking for .env file."""
    current = Path(__file__).resolve()
    # Go up from app/config/settings.py to project root
    for parent in [current.parent.parent.parent, current.parent.parent]:
        env_file = parent / ".env"
        if env_file.exists():
            return str(parent)
    # Fallback to current working directory
    return os.getcwd()

PROJECT_ROOT = find_project_root()
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI API Configuration
    openai_api_key: str = Field(..., description="OpenAI API key (required)")
    openai_model: str = "gpt-4.1-mini"  # Fast, deterministic reasoning model (FIXED for enterprise)
    embedding_model_name: str = "text-embedding-3-small"  # Scalable embeddings (FIXED for enterprise)
    
    # Mistral API Configuration (for OCR and preprocessing)
    mistral_api_key: Optional[str] = Field(default=None, description="Mistral API key (optional, required for OCR)")
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is provided and not a placeholder."""
        if not v:
            raise ValueError("OPENAI_API_KEY is required. Please set it in your .env file.")
        
        # Strip whitespace
        v = v.strip()
        
        # Remove leading = if present (common .env file mistake: OPENAI_API_KEY==value)
        if v.startswith('='):
            v = v[1:].strip()
            logger.warning("Removed leading '=' from API key - check your .env file format (should be OPENAI_API_KEY=value, not OPENAI_API_KEY==value)")
        
        if v == "":
            raise ValueError("OPENAI_API_KEY is empty. Please set it in your .env file.")
        if "your_openai_api_key" in v.lower() or "your_" in v.lower() or "sk-" not in v:
            raise ValueError("OPENAI_API_KEY appears to be a placeholder. Please set a valid API key in your .env file.")
        if len(v) < 20:
            raise ValueError(f"OPENAI_API_KEY appears to be invalid (too short: {len(v)} chars). Please check your .env file.")
        return v
    
    # Local Embeddings Configuration (no API key needed)
    embedding_model: str = "all-MiniLM-L6-v2"  # Fast, lightweight sentence-transformers model
    
    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "pdf_documents"
    
    # Temperature setting (FIXED at 0 for deterministic output)
    temperature: float = 0.0  # Deterministic for enterprise reliability
    
    # Retrieval Configuration
    top_k_retrieval: int = 5
    
    # API Configuration
    # Render provides PORT environment variable, use 0.0.0.0 for production
    api_host: str = Field(default="0.0.0.0", description="API host (use 0.0.0.0 for production)")
    api_port: int = Field(default=8000, description="API port (Render provides PORT env var)")
    
    # Visualization Configuration
    chart_output_dir: str = "./charts"
    
    class Config:
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
try:
    if os.path.exists(ENV_FILE_PATH):
        logger.info(f"Loading .env file from: {ENV_FILE_PATH}")
    else:
        logger.warning(f".env file not found at: {ENV_FILE_PATH}")
        logger.warning(f"Current working directory: {os.getcwd()}")
        logger.warning(f"Project root: {PROJECT_ROOT}")
        # Try current directory as fallback
        if os.path.exists(".env"):
            logger.info("Found .env in current directory, using that instead")
            ENV_FILE_PATH = ".env"
    
    settings = Settings()
    logger.info("Settings loaded successfully")
except Exception as e:
    logger.error(f"Error loading settings: {e}")
    logger.error(f"Looking for .env at: {ENV_FILE_PATH}")
    logger.error(f"Please ensure you have a .env file with OPENAI_API_KEY set")
    # Create a dummy settings object to prevent import errors
    # The app will handle the error gracefully
    class DummySettings:
        openai_api_key = None
        openai_model = "gpt-4.1-mini"
        embedding_model_name = "text-embedding-3-small"
        embedding_model = "all-MiniLM-L6-v2"
        chroma_persist_directory = "./chroma_db"
        chroma_collection_name = "pdf_documents"
        temperature = 0.0
        top_k_retrieval = 5
        api_host = "127.0.0.1"
        api_port = 8000
        chart_output_dir = "./charts"
        mistral_api_key = None
    settings = DummySettings()

