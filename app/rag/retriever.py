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
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            
            if not results:
                logger.warning(f"No results found for query: {query}")
                return []
            
            logger.info(f"Retrieved {len(results)} relevant chunks")
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
            return ""
        
        context_parts = []
        for idx, doc in enumerate(retrieved_docs, 1):
            page_num = doc.get("metadata", {}).get("page_number", "Unknown")
            text = doc.get("text", "")
            context_parts.append(f"[Context {idx} - Page {page_num}]\n{text}\n")
        
        return "\n".join(context_parts)

