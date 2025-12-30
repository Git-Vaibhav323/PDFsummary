"""
Retriever for fetching relevant context from vector store.
"""
from typing import List, Dict, Optional
import logging
from app.rag.vector_store import VectorStore
from app.config.settings import settings

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves relevant context from vector store for RAG."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the retriever.
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
        self.top_k = settings.top_k_retrieval
    
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query/question
            k: Number of documents to retrieve (defaults to config)
            
        Returns:
            List of relevant document chunks with metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to retriever")
            return []
        
        k = k or self.top_k
        logger.info(f"Retrieving up to {k} documents for query: {query[:100]}...")
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            
            if not results:
                logger.warning(f"No results found for query: {query[:100]}...")
                logger.warning("Similarity search returned no results, trying fallback: getting all documents from collection")
                
                # Fallback: Get all documents from the collection if similarity search fails
                try:
                    fallback_results = self.vector_store.get_all_documents(limit=k * 2)  # Get more for better coverage
                    if fallback_results:
                        logger.info(f"Fallback retrieval succeeded: got {len(fallback_results)} documents")
                        # Log sample of retrieved content
                        for i, doc in enumerate(fallback_results[:2], 1):
                            text_preview = doc.get("text", "")[:100] if doc.get("text") else "NO TEXT"
                            logger.debug(f"Fallback chunk {i} preview: {text_preview}...")
                        return fallback_results
                    else:
                        logger.error("Fallback retrieval also returned no documents. Vector store may be empty.")
                        return []
                except Exception as fallback_error:
                    logger.error(f"Fallback retrieval failed: {fallback_error}")
                    return []
            
            logger.info(f"Retrieved {len(results)} relevant chunks")
            # Log sample of retrieved content
            for i, doc in enumerate(results[:2], 1):  # Log first 2
                text_preview = doc.get("text", "")[:100] if doc.get("text") else "NO TEXT"
                logger.debug(f"Chunk {i} preview: {text_preview}...")
            return results
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error retrieving context: {e}")
            
            # Check if it's a quota/embedding issue
            if "limit: 0" in error_str or "free_tier" in error_str.lower() or "429" in error_str:
                # Re-raise with clearer message
                raise ValueError(
                    "Embedding API quota exceeded. Free tier has limit: 0. "
                    "Cannot retrieve context without embeddings. Please upgrade to a paid plan."
                ) from e
            
            # Try fallback retrieval even on error
            try:
                logger.info("Trying fallback retrieval after error...")
                fallback_results = self.vector_store.get_all_documents(limit=k * 2)
                if fallback_results:
                    logger.info(f"Fallback retrieval succeeded after error: got {len(fallback_results)} documents")
                    return fallback_results
            except Exception as fallback_error:
                logger.error(f"Fallback retrieval also failed: {fallback_error}")
            
            return []
    
    def format_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into a single context string.
        
        Args:
            retrieved_docs: List of retrieved document dictionaries
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            logger.warning("format_context called with empty retrieved_docs")
            return ""
        
        context_parts = []
        valid_docs = 0
        for idx, doc in enumerate(retrieved_docs, 1):
            page_num = doc.get("metadata", {}).get("page_number", "Unknown")
            text = doc.get("text", "")
            
            if not text or not text.strip():
                logger.warning(f"Document {idx} has empty text field")
                continue
            
            context_parts.append(f"[Context {idx} - Page {page_num}]\n{text}\n")
            valid_docs += 1
        
        if valid_docs == 0:
            logger.error("All retrieved documents have empty text fields!")
            return ""
        
        formatted_context = "\n".join(context_parts)
        logger.info(f"Formatted context from {valid_docs}/{len(retrieved_docs)} documents, total length: {len(formatted_context)} characters")
        return formatted_context

