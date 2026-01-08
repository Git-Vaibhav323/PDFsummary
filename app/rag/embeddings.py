"""
OpenAI embeddings using text-embedding-3-small with batching and caching.
Optimized for performance with batch processing and token-aware batching.
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
MAX_TOKENS_PER_REQUEST = 250000  # Safe limit below OpenAI's 300k hard limit
APPROX_CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 characters


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
            
            # Initialize OpenAI embeddings with timeout configuration
            self._embeddings = OpenAIEmbeddings(
                model=self.model_name,
                api_key=settings.openai_api_key,
                timeout=60.0,  # 60 second timeout
                max_retries=3  # Retry up to 3 times
            )
            
            logger.info(f"✅ OpenAI embeddings initialized")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Dimension: {EMBEDDING_DIMENSION}")
            logger.info(f"   Batch size: {self.batch_size} docs (token-aware)")
            
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
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // APPROX_CHARS_PER_TOKEN
    
    def _create_smart_batches(self, texts: List[str]) -> List[List[str]]:
        """
        Create batches that respect both document count and token limits.
        
        Args:
            texts: List of texts to batch
            
        Returns:
            List of batches, each within token limits
        """
        batches = []
        current_batch = []
        current_token_count = 0
        
        for text in texts:
            text_tokens = self._estimate_tokens(text)
            
            # If single text exceeds limit, truncate it
            if text_tokens > MAX_TOKENS_PER_REQUEST:
                logger.warning(f"⚠️ Text has ~{text_tokens} tokens, truncating to fit {MAX_TOKENS_PER_REQUEST} limit")
                # Truncate to safe character limit
                max_chars = MAX_TOKENS_PER_REQUEST * APPROX_CHARS_PER_TOKEN
                text = text[:max_chars]
                text_tokens = MAX_TOKENS_PER_REQUEST
            
            # Check if adding this text would exceed limits
            would_exceed_tokens = (current_token_count + text_tokens) > MAX_TOKENS_PER_REQUEST
            would_exceed_batch_size = len(current_batch) >= self.batch_size
            
            if current_batch and (would_exceed_tokens or would_exceed_batch_size):
                # Save current batch and start new one
                batches.append(current_batch)
                logger.debug(f"   Batch {len(batches)}: {len(current_batch)} docs, ~{current_token_count} tokens")
                current_batch = [text]
                current_token_count = text_tokens
            else:
                # Add to current batch
                current_batch.append(text)
                current_token_count += text_tokens
        
        # Don't forget the last batch
        if current_batch:
            batches.append(current_batch)
            logger.debug(f"   Batch {len(batches)}: {len(current_batch)} docs, ~{current_token_count} tokens")
        
        return batches
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents using smart batch processing.
        
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
            
            # Create smart batches based on token count
            batches = self._create_smart_batches(texts)
            total_batches = len(batches)
            
            logger.info(f"📊 Embedding {len(texts)} chunks in {total_batches} smart batches...")
            
            # Process each batch
            all_embeddings = []
            for batch_idx, batch in enumerate(batches, 1):
                batch_start = time.time()
                logger.info(f"   Batch {batch_idx}/{total_batches}: embedding {len(batch)} texts...")
                
                try:
                    batch_embeddings = self._embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    
                    batch_elapsed = time.time() - batch_start
                    logger.info(f"   ✅ Batch {batch_idx}/{total_batches} done in {batch_elapsed:.2f}s")
                    
                except Exception as batch_error:
                    logger.error(f"   ❌ Batch {batch_idx}/{total_batches} failed: {batch_error}")
                    # Try to continue with remaining batches
                    raise
            
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
