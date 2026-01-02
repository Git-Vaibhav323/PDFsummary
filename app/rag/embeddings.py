"""
Local embeddings using sentence-transformers (free, no API needed).
"""
from typing import List
import logging
import os
from sentence_transformers import SentenceTransformer
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """Wrapper for local sentence-transformers embeddings (free, no API needed)."""
    
    def __init__(self):
        """Initialize local embeddings using sentence-transformers."""
        self._model = None
        self.model_name = getattr(settings, 'embedding_model', 'all-MiniLM-L6-v2')
            
    def _ensure_initialized(self):
        """Lazy-load the embedding model on first use."""
        if self._model is not None:
            return
        
        try:
            # Use the same cache directory as download_models.py
            cache_dir = os.path.join(os.getcwd(), '.model_cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Set environment variables for HuggingFace cache
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
            os.environ['TRANSFORMERS_CACHE'] = cache_dir
            os.environ['HF_HOME'] = cache_dir
            
            logger.info(f"Loading local embedding model: {self.model_name}")
            logger.info(f"Using cache directory: {cache_dir}")
            
            # Check if model is already cached
            if os.path.exists(cache_dir) and any(os.scandir(cache_dir)):
                logger.info("✅ Found cached model, loading from cache...")
            else:
                logger.info("⚠️ Model not found in cache, will download (this may take a moment)...")
            
            # Use SentenceTransformer directly (more reliable than LangChain wrapper)
            self._model = SentenceTransformer(self.model_name, cache_folder=cache_dir)
            
            logger.info(f"✅ Model {self.model_name} loaded successfully")
            logger.info("✅ Using free local embeddings - no API costs!")
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to initialize local embeddings: {e}")
            raise
    
    @property
    def embeddings(self):
        """Get embeddings model for LangChain compatibility."""
        self._ensure_initialized()
        return self
    
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        self._ensure_initialized()
        
        try:
            logger.info(f"Embedding {len(texts)} document chunks...")
            
            # Use SentenceTransformer directly - faster and more reliable
            # Convert to float32 numpy arrays then to lists for ChromaDB compatibility
            embeddings = self._model.encode(
                texts,
                batch_size=16,  # Smaller batch size for memory efficiency on free tier
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Convert numpy arrays to lists
            embeddings_list = embeddings.tolist()
            
            logger.info(f"✅ Successfully embedded {len(texts)} documents")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"❌ Error embedding documents: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty")
        
        self._ensure_initialized()
        
        try:
            logger.debug(f"Embedding query: {text[:50]}...")
            
            # Use SentenceTransformer directly
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Convert numpy array to list
            embedding_list = embedding.tolist()
            
            logger.debug("✅ Query embedded successfully")
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ Error embedding query: {e}")
            raise
    
    def get_embeddings_model(self):
        """Get the underlying embeddings model for direct use."""
        self._ensure_initialized()
        return self
