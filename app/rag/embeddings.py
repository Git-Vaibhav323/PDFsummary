"""
OpenAI embeddings using text-embedding-3-small with batching and caching.
Optimized for performance with batch processing.
"""
from typing import List
import logging
import time
from langchain_openai import OpenAIEmbeddings
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Performance constants
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 50  # OpenAI recommends 50-100 for optimal throughput


class OpenAIEmbeddingsWrapper:
    """Wrapper for OpenAI embeddings with batching and performance tracking."""
    
    def __init__(self):
        """Initialize OpenAI embeddings."""
        self._embeddings = None
        self.model_name = settings.embedding_model_name  # text-embedding-3-small
        self.batch_size = BATCH_SIZE
        self._embed_count = 0
        self._total_embed_time = 0.0
    
    def _ensure_initialized(self):
        """Lazy-load the embeddings on first use."""
        if self._embeddings is not None:
            return
        
        try:
            logger.info(f"🚀 Initializing OpenAI embeddings: {self.model_name}")
            
            # Initialize OpenAI embeddings
            self._embeddings = OpenAIEmbeddings(
                model=self.model_name,
                api_key=settings.openai_api_key
            )
            
            logger.info(f"✅ OpenAI embeddings initialized")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Dimension: {EMBEDDING_DIMENSION}")
            logger.info(f"   Batch size: {self.batch_size}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI embeddings: {e}")
            raise
    
    def get_embeddings_model(self):
        """Get embeddings model for LangChain compatibility."""
        self._ensure_initialized()
        return self._embeddings
    
    @property
    def embeddings(self):
        """Get embeddings model for LangChain compatibility."""
        return self.get_embeddings_model()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents using batch processing.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        self._ensure_initialized()
        
        try:
            start_time = time.time()
            logger.info(f"📊 Embedding {len(texts)} chunks (batch_size={self.batch_size})...")
            
            # Process in batches for better performance
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                logger.debug(f"   Batch {i//self.batch_size + 1}: embedding {len(batch)} texts...")
                
                batch_embeddings = self._embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
            
            elapsed = time.time() - start_time
            self._embed_count += len(texts)
            self._total_embed_time += elapsed
            
            rate = len(texts) / max(elapsed, 0.01)
            logger.info(f"✅ Embedded {len(texts)} documents in {elapsed:.2f}s ({rate:.0f} docs/sec)")
            
            return all_embeddings
            
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
            start_time = time.time()
            logger.debug(f"🔍 Embedding query: {text[:50]}...")
            
            # Use OpenAI embeddings API
            embedding = self._embeddings.embed_query(text)
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ Query embedded in {elapsed:.3f}s")
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error embedding query: {e}")
            raise
    
    def get_embeddings_model(self):
        """Get the underlying embeddings model for direct use with LangChain."""
        self._ensure_initialized()
        return self._embeddings
