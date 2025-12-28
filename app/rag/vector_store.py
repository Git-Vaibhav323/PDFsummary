"""
Chroma vector database with persistent storage.
Manages document embeddings and retrieval.
"""
import os
from typing import List, Dict, Optional
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from app.config.settings import settings
from app.rag.embeddings import LocalEmbeddings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages Chroma vector database with persistence."""
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the Chroma collection (defaults to config)
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = settings.chroma_persist_directory
        self.embeddings = LocalEmbeddings()
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize Chroma
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize or load existing Chroma vectorstore."""
        try:
            # Try to load existing vectorstore first
            try:
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings.get_embeddings_model(),
                    persist_directory=self.persist_directory
                )
                logger.info(f"Vector store loaded from {self.persist_directory}")
            except Exception:
                # If loading fails, create a new one
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings.get_embeddings_model(),
                    persist_directory=self.persist_directory
                )
                logger.info(f"Vector store initialized at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict]) -> List[str]:
        """
        Add document chunks to the vector store with error handling.
        
        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
            
        Returns:
            List of document IDs
        """
        if not chunks:
            logger.warning("No chunks provided to add")
            return []
        
        try:
            import uuid
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk.get("metadata", {}) for chunk in chunks]
            # Use UUID to avoid ID collisions
            ids = [f"chunk_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(chunks))]
            
            # Validate text lengths (embedding models have token limits)
            max_text_length = 8000  # Safe limit for embeddings
            validated_texts = []
            validated_metadatas = []
            validated_ids = []
            
            for i, text in enumerate(texts):
                if len(text) > max_text_length:
                    logger.warning(f"Chunk {i} is too long ({len(text)} chars), truncating to {max_text_length}")
                    text = text[:max_text_length]
                if text.strip():  # Only add non-empty texts
                    validated_texts.append(text)
                    validated_metadatas.append(metadatas[i])
                    validated_ids.append(ids[i])
            
            if not validated_texts:
                raise ValueError("No valid text chunks to add after validation")
            
            logger.info(f"Adding {len(validated_texts)} chunks to vector store (out of {len(chunks)} total)")
            
            # Track successful additions
            successful_ids = []
            failed_count = 0
            
            # For small batches, try direct addition first
            if len(validated_texts) <= 25:
                try:
                    self.vectorstore.add_texts(
                        texts=validated_texts,
                        metadatas=validated_metadatas,
                        ids=validated_ids
                    )
                    successful_ids = validated_ids
                except Exception as e:
                    error_str = str(e)
                    # With local embeddings, this should not occur, but keep for error handling
                    if "limit: 0" in error_str or "free_tier" in error_str.lower():
                        raise ValueError(
                            "❌ **Embedding Error**\n\n"
                            "Local embeddings should not have API limits. This error is unexpected.\n\n"
                            "**Solutions:**\n"
                            "1. 🔄 **Restart the app** and try again\n"
                            "2. 📦 **Check if sentence-transformers is installed**: `pip install sentence-transformers`\n"
                            "3. 💻 **Check system resources** (memory/disk space)"
                        ) from e
                    
                    # If batch fails, try one at a time for small files
                    logger.warning(f"Batch addition failed, trying individual chunks: {e}")
                    for idx, (text, metadata, chunk_id) in enumerate(zip(validated_texts, validated_metadatas, validated_ids)):
                        try:
                            self.vectorstore.add_texts(
                                texts=[text],
                                metadatas=[metadata],
                                ids=[chunk_id]
                            )
                            successful_ids.append(chunk_id)
                        except Exception as individual_error:
                            failed_count += 1
                            error_str = str(individual_error)
                            logger.error(f"Failed to add chunk {idx}: {individual_error}")
                            
                            # With local embeddings, this should not occur
                            if "limit: 0" in error_str or "free_tier" in error_str.lower():
                                # If all chunks fail, raise immediately
                                if failed_count == len(validated_texts):
                                    raise ValueError(
                                        "❌ **Embedding Error**\n\n"
                                        "All chunks failed to embed. This should not happen with local embeddings.\n\n"
                                        "**Solutions:**\n"
                                        "1. 📦 **Check if sentence-transformers is installed**: `pip install sentence-transformers`\n"
                                        "2. 💻 **Check system resources** (memory/disk space)\n"
                                        "3. 🔄 **Restart the app** and try again"
                                    ) from individual_error
            else:
                # For larger batches, use normal flow
                try:
                    self.vectorstore.add_texts(
                        texts=validated_texts,
                        metadatas=validated_metadatas,
                        ids=validated_ids
                    )
                    successful_ids = validated_ids
                except Exception as e:
                    error_str = str(e)
                    if "limit: 0" in error_str or "free_tier" in error_str.lower():
                        raise ValueError(
                            "❌ **Embedding Error**\n\n"
                            "Local embeddings should not have API limits. Please check if sentence-transformers is installed."
                        ) from e
                    raise
            
            # Check if we have any successful additions
            if not successful_ids:
                raise ValueError(
                    f"Failed to add any chunks to vector store. All {len(validated_texts)} chunks failed. "
                    "This is unexpected with local embeddings. Please check if sentence-transformers is installed and system resources."
                )
            
            if failed_count > 0:
                logger.warning(f"Successfully added {len(successful_ids)} chunks, but {failed_count} chunks failed")
            
            # Persist to disk (Chroma 0.4+ auto-persists, but keep for compatibility)
            try:
                self.vectorstore.persist()
            except Exception as persist_error:
                # Chroma 0.4+ auto-persists, so this might raise a deprecation warning
                # That's okay, we can ignore it
                logger.debug(f"Persistence note: {persist_error}")
            
            logger.info(f"Successfully added {len(successful_ids)} chunks to vector store (out of {len(validated_texts)} total)")
            return successful_ids
            
        except ValueError as e:
            # Re-raise validation errors
            logger.error(f"Validation error adding documents: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error adding documents: {e}")
            
            # Check for specific API errors
            if "400" in error_msg or "Bad Request" in error_msg:
                raise ValueError(
                    f"API request failed (400 Bad Request). This might be due to:\n"
                    f"1. Text chunks are too large\n"
                    f"2. Invalid characters in the text\n"
                    f"3. API quota/rate limits\n"
                    f"Original error: {error_msg}"
                ) from e
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise ValueError(
                    "API quota exceeded or rate limit reached. Please wait a moment and try again."
                ) from e
            else:
                raise ValueError(f"Failed to add documents to vector store: {error_msg}") from e
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of document dictionaries with text and metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            documents = []
            for doc, score in results:
                documents.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            logger.info(f"Retrieved {len(documents)} documents for query")
            return documents
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error in similarity search: {e}")
            
            # With local embeddings, quota errors should not occur
            if "limit: 0" in error_str or "free_tier" in error_str.lower() or "429" in error_str:
                # Re-raise to propagate the error with clear message
                raise ValueError(
                    f"Embedding error (unexpected with local embeddings). "
                    f"Cannot perform similarity search. Please check if sentence-transformers is installed. "
                    f"Error: {error_str[:200]}"
                ) from e
            
            # For other errors, return empty list (might be empty vector store)
            return []
    
    def delete_collection(self):
        """Delete the entire collection (use with caution)."""
        try:
            # Delete the collection
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def get_retriever(self, k: int = 5):
        """
        Get a LangChain retriever from the vectorstore.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            LangChain retriever
        """
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

