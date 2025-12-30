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
        model = SentenceTransformer(model_name)
        logger.info(f"✅ Successfully downloaded and cached {model_name}")
        logger.info(f"Model cached at: {model.cache_folder()}")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False

if __name__ == "__main__":
    success = download_embedding_model()
    exit(0 if success else 1)

