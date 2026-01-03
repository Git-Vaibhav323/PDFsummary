"""
Retriever for fetching relevant context from vector store.
Optimized for speed with caching and early-exit strategies.
"""
from typing import List, Dict, Optional, Tuple
import logging
import re
import time
from app.rag.vector_store import VectorStore
from app.rag.cache_manager import get_cache_manager
from app.config.settings import settings

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves relevant context from vector store for RAG with caching."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the retriever.
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
        self.base_k = 4  # Default retrieval count
        self.max_k = 6  # Extended retrieval for long queries
        self.max_context_tokens = 1500  # Max context size
        self.confidence_threshold = 0.6  # Confidence threshold for early exit
        self.cache_manager = get_cache_manager()
    
    def _get_dynamic_k(self, query: str) -> int:
        """
        Dynamically determine k based on query length.
        Longer queries may need more context.
        
        Args:
            query: User query
            
        Returns:
            Number of chunks to retrieve (4-6)
        """
        # If query is long (>80 tokens), retrieve more chunks
        query_tokens = len(query) / 4  # Rough estimate
        if query_tokens > 80:
            k = self.max_k
            logger.debug(f"Long query ({int(query_tokens)} tokens) → k={k}")
        else:
            k = self.base_k
        return k
    
    def retrieve(self, query: str, document_id: str = "", k: Optional[int] = None) -> Tuple[List[Dict], float]:
        """
        Retrieve top-K relevant context for a query with caching and confidence scoring.
        
        Args:
            query: User query/question
            document_id: Optional document context for filtering
            k: Number of documents to retrieve (auto-determined if None)
            
        Returns:
            Tuple of (retrieved chunks, confidence score 0-1)
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return [], 0.0
        
        start_time = time.time()
        
        # Check cache first
        cached_results = self.cache_manager.get_retrieval(query, document_id)
        if cached_results is not None:
            logger.info(f"📦 RETRIEVAL CACHE HIT: {len(cached_results)} chunks")
            return cached_results, 0.95  # High confidence for cached results
        
        # Determine k dynamically
        k = k or self._get_dynamic_k(query)
        k = min(k, self.max_k)  # Enforce max
        
        logger.info(f"🔍 RETRIEVAL: Fetching top {k} chunks (confidence threshold: {self.confidence_threshold})...")
        
        try:
            results, confidence = self.vector_store.similarity_search_with_score(query, k=k)
            
            if not results:
                logger.warning(f"⚠️ No results from similarity search, trying fallback...")
                try:
                    fallback_results = self.vector_store.get_all_documents(limit=k * 2)
                    if fallback_results:
                        logger.info(f"✅ Fallback retrieval succeeded: {len(fallback_results)} documents")
                        confidence = 0.5  # Low confidence for fallback
                        results = fallback_results[:k]
                    else:
                        logger.error("❌ Vector store is empty")
                        return [], 0.0
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback retrieval failed: {fallback_error}")
                    return [], 0.0
            
            elapsed = time.time() - start_time
            
            # Early exit if confidence is too low
            if confidence < self.confidence_threshold:
                logger.warning(f"⚠️ Low confidence retrieval ({confidence:.2f} < {self.confidence_threshold}) - returning fewer chunks")
                results = results[:max(1, k // 2)]  # Return at least 1, at most k/2
            
            results = results[:k]  # Ensure we return at most k results
            
            # Cache the results
            self.cache_manager.set_retrieval(query, results, document_id)
            
            logger.info(f"✅ RETRIEVAL: {len(results)} chunks in {elapsed:.3f}s (confidence: {confidence:.2f})")
            return results, confidence
            
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return [], 0.0
    
    def compress_context(self, text: str) -> str:
        """
        Compress context by removing boilerplate and duplicates.
        
        Args:
            text: Raw text from document
            
        Returns:
            Compressed text
        """
        # Remove page numbers and headers/footers
        text = re.sub(r'Page \d+|^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*\n+', '\n', text)  # Remove excessive whitespace
        
        # Remove duplicate sentences
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def filter_boilerplate(self, text: str) -> str:
        """
        Remove boilerplate text that doesn't add information value.
        
        Args:
            text: Raw text from document
            
        Returns:
            Filtered text
        """
        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r'^\s*(Copyright|©|®|™|All rights reserved).*$',
            r'^\s*(Confidential|For Internal Use Only).*$',
            r'^\s*(Table of Contents|Index|References).*$',
            r'^\s*(Page \d+|p\.\s*\d+).*$',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text
    
    def format_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into compressed context string.
        
        Args:
            retrieved_docs: List of retrieved document dictionaries
            
        Returns:
            Formatted, compressed context string (max 1500 tokens)
        """
        if not retrieved_docs:
            logger.warning("format_context called with empty retrieved_docs")
            return ""
        
        context_parts = []
        total_chars = 0
        valid_docs = 0
        
        for idx, doc in enumerate(retrieved_docs, 1):
            page_num = doc.get("metadata", {}).get("page_number", "Unknown")
            text = doc.get("text", "")
            
            if not text or not text.strip():
                logger.warning(f"Document {idx} has empty text field")
                continue
            
            # Compress the text
            compressed_text = self.compress_context(text)
            compressed_text = self.filter_boilerplate(compressed_text)
            
            # Check if adding this would exceed token limit (~4 chars per token)
            estimated_tokens = len(compressed_text) // 4
            if total_chars + len(compressed_text) > self.max_context_tokens * 4:
                logger.info(f"⚠️ Context size limit reached, stopping at {valid_docs} documents")
                break
            
            context_parts.append(f"[Page {page_num}]\n{compressed_text}\n")
            total_chars += len(compressed_text)
            valid_docs += 1
        
        if valid_docs == 0:
            logger.error("❌ All retrieved documents have empty text fields!")
            return ""
        
        formatted_context = "\n".join(context_parts)
        estimated_tokens = len(formatted_context) // 4
        logger.info(f"✅ CONTEXT: {valid_docs} documents, ~{estimated_tokens} tokens, {len(formatted_context)} chars")
        
        return formatted_context

