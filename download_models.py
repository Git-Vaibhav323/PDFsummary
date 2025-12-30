"""
Pre-download embedding models during build to avoid runtime delays.
Run this during deployment to cache models.
"""
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_embedding_model():
    """Download and cache the embedding model."""
    model_name = "all-MiniLM-L6-v2"
    logger.info(f"Downloading embedding model: {model_name}")
    logger.info("This will cache the model for faster startup...")
    
    try:
        # This downloads and caches the model
        # Set cache folder to /root/.cache to persist in Docker
        import os
        os.environ['TRANSFORMERS_CACHE'] = '/root/.cache/huggingface'
        os.environ['HF_HOME'] = '/root/.cache/huggingface'
        
        model = SentenceTransformer(model_name)
        logger.info(f"✅ Successfully downloaded and cached {model_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't fail build if model download fails - will download at runtime
        logger.warning("Model download failed, will download at runtime")
        return True  # Return True to not fail build

if __name__ == "__main__":
    success = download_embedding_model()
    exit(0 if success else 1)

