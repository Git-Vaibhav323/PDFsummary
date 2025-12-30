"""
Pre-download embedding models during build to avoid runtime delays.
Run this during deployment to cache models.
"""
import logging
import os
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_embedding_model():
    """Download and cache the embedding model."""
    model_name = "all-MiniLM-L6-v2"
    
    # Set cache directory to a persistent location
    # This must match the cache directory used at runtime
    cache_dir = os.path.join(os.getcwd(), '.model_cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Set environment variables for HuggingFace cache
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    
    logger.info(f"Downloading embedding model: {model_name}")
    logger.info(f"Cache directory: {cache_dir}")
    
    try:
        # This downloads and caches the model
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        logger.info(f"✅ Successfully downloaded and cached {model_name}")
        logger.info(f"✅ Model cached at: {cache_dir}")
        
        # Verify the model works
        test_embedding = model.encode("test")
        logger.info(f"✅ Model verification successful (embedding shape: {test_embedding.shape})")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't fail build if model download fails - will download at runtime
        logger.warning("⚠️ Model download failed, will download at runtime")
        return True  # Return True to not fail build

if __name__ == "__main__":
    success = download_embedding_model()
    exit(0 if success else 1)

