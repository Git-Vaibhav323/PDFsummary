"""
Local embeddings using sentence-transformers (free, no API needed).
"""
from typing import List
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """Wrapper for local sentence-transformers embeddings (free, no API needed)."""
    
    def __init__(self):
        """Initialize local embeddings using sentence-transformers."""
        try:
            model_name = getattr(settings, 'embedding_model', 'all-MiniLM-L6-v2')
            
            logger.info(f"Loading local embedding model: {model_name}")
            logger.info("This may take a moment on first run (downloading model)...")
            
            # Use HuggingFace embeddings (sentence-transformers under the hood)
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},  # Use CPU by default
                encode_kwargs={'normalize_embeddings': True}  # Normalize for better similarity
            )
            
            logger.info(f"Local embeddings initialized successfully with model: {model_name}")
            logger.info("✅ Using free local embeddings - no API costs!")
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to initialize local embeddings: {e}")
            raise
    
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
        
        try:
            # Local embeddings are fast and don't have rate limits
            # Process in reasonable batches for memory efficiency
            batch_size = 32  # Good batch size for local embeddings
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(texts) + batch_size - 1) // batch_size
                
                logger.debug(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
                
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Successfully embedded {len(texts)} documents")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
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
        
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def get_embeddings_model(self):
        """Get the underlying embeddings model for direct use."""
        return self.embeddings
