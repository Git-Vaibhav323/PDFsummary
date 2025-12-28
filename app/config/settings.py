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
    
    # Groq API Configuration
    groq_api_key: str = Field(..., description="Groq API key (required)")
    groq_model: str = "llama-3.1-8b-instant"  # Fast and reliable model (llama-3.1-70b-versatile was decommissioned)
    
    @field_validator('groq_api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is provided and not a placeholder."""
        if not v:
            raise ValueError("GROQ_API_KEY is required. Please set it in your .env file.")
        
        # Strip whitespace
        v = v.strip()
        
        # Remove leading = if present (common .env file mistake: GROQ_API_KEY==value)
        if v.startswith('='):
            v = v[1:].strip()
            logger.warning("Removed leading '=' from API key - check your .env file format (should be GROQ_API_KEY=value, not GROQ_API_KEY==value)")
        
        if v == "":
            raise ValueError("GROQ_API_KEY is empty. Please set it in your .env file.")
        if "your_groq_api_key" in v.lower() or "your_" in v.lower():
            raise ValueError("GROQ_API_KEY appears to be a placeholder. Please set a valid API key in your .env file.")
        if len(v) < 20:
            raise ValueError(f"GROQ_API_KEY appears to be invalid (too short: {len(v)} chars). Please check your .env file.")
        return v
    
    # Local Embeddings Configuration (no API key needed)
    embedding_model: str = "all-MiniLM-L6-v2"  # Fast, lightweight sentence-transformers model
    
    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "pdf_documents"
    
    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    # Chunk limits for large documents
    max_chunks_per_document: int = 500  # Increased default limit (was 200)
    enable_large_document_processing: bool = True  # Allow processing large docs with warnings
    large_document_threshold_pages: int = 50  # Pages threshold for "large" document
    
    # Retrieval Configuration
    top_k_retrieval: int = 5
    
    # API Configuration
    api_host: str = "127.0.0.1"  # Use 127.0.0.1 instead of 0.0.0.0 for browser access
    api_port: int = 8000
    
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
    logger.error(f"Please ensure you have a .env file with GROQ_API_KEY set")
    # Create a dummy settings object to prevent import errors
    # The app will handle the error gracefully
    class DummySettings:
        groq_api_key = None
        groq_model = "llama-3.1-8b-instant"
        embedding_model = "all-MiniLM-L6-v2"
        chroma_persist_directory = "./chroma_db"
        chroma_collection_name = "pdf_documents"
        chunk_size = 1000
        chunk_overlap = 200
        top_k_retrieval = 5
        api_host = "127.0.0.1"
        api_port = 8000
        chart_output_dir = "./charts"
    settings = DummySettings()

