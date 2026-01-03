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
from app.rag.embeddings import OpenAIEmbeddingsWrapper

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
        self.embeddings = OpenAIEmbeddingsWrapper()
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize Chroma
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize or load existing Chroma vectorstore."""
        try:
            # Initialize ChromaDB client with proper settings
            # Use a singleton pattern to avoid multiple instances
            if not hasattr(VectorStore, '_chroma_client'):
                VectorStore._chroma_client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=ChromaSettings(
                        anonymized_telemetry=False
                    )
                )
                logger.info(f"ChromaDB client initialized for {self.persist_directory}")
            
            # Try to load existing vectorstore first
            try:
                # Check if collection exists and get its metadata
                try:
                    collection = VectorStore._chroma_client.get_collection(name=self.collection_name)
                    collection_count = collection.count()
                    logger.info(f"Found existing collection '{self.collection_name}' with {collection_count} documents")
                    
                    # If we find the old collection with 219 documents (from old embeddings),
                    # delete it since OpenAI embeddings are incompatible with sentence-transformers
                    if collection_count >= 200:  # Likely the old collection
                        logger.warning(f"Collection has {collection_count} documents (likely old embeddings), deleting...")
                        VectorStore._chroma_client.delete_collection(name=self.collection_name)
                        logger.info(f"Old collection deleted, will create fresh one with OpenAI embeddings")
                        collection_count = 0
                except Exception as e:
                    collection_count = 0
                    logger.info(f"Collection '{self.collection_name}' does not exist, will create new one: {e}")
                
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings.get_embeddings_model(),
                    persist_directory=self.persist_directory,
                    client=VectorStore._chroma_client,
                    collection_metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                logger.info(f"Vector store loaded from {self.persist_directory}")
            except Exception as e:
                logger.warning(f"Failed to load existing vectorstore: {e}, creating new one")
                # If loading fails, create a new one with proper metadata
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings.get_embeddings_model(),
                    persist_directory=self.persist_directory,
                    client=VectorStore._chroma_client,
                    collection_metadata={"hnsw:space": "cosine"}  # Use cosine similarity
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
                    # Check for API limits or quota errors
                    if "limit: 0" in error_str or "free_tier" in error_str.lower() or "quota" in error_str.lower():
                        raise ValueError(
                            "❌ **OpenAI Embedding API Error**\n\n"
                            "The OpenAI API has rate limits or quota restrictions.\n\n"
                            "**Solutions:**\n"
                            "1. 💳 **Check your OpenAI account** - Verify you have credits\n"
                            "2. ⏱️ **Wait a moment** - Try again after a brief delay\n"
                            "3. 🔑 **Verify API key** - Ensure OPENAI_API_KEY is correct in .env\n"
                            "4. 🔄 **Restart the app** and try again"
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
                            
                            # Check for API limits or quota errors
                            if "limit: 0" in error_str or "free_tier" in error_str.lower() or "quota" in error_str.lower():
                                # If all chunks fail, raise immediately
                                if failed_count == len(validated_texts):
                                    raise ValueError(
                                        "❌ **OpenAI Embedding API Error**\n\n"
                                        "All chunks failed to embed due to API limits.\n\n"
                                        "**Solutions:**\n"
                                        "1. 💳 **Check your OpenAI account** - Verify you have credits\n"
                                        "2. ⏱️ **Wait a moment** - Try again after a brief delay\n"
                                        "3. 🔑 **Verify API key** - Ensure OPENAI_API_KEY is correct in .env\n"
                                        "4. 🔄 **Restart the app** and try again"
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
                    if "limit: 0" in error_str or "free_tier" in error_str.lower() or "quota" in error_str.lower():
                        raise ValueError(
                            "❌ **OpenAI Embedding API Error**\n\n"
                            "The OpenAI API has rate limits or quota restrictions.\n\n"
                            "**Solutions:**\n"
                            "1. 💳 **Check your OpenAI account** - Verify you have credits\n"
                            "2. ⏱️ **Wait a moment** - Try again after a brief delay\n"
                            "3. 🔑 **Verify API key** - Ensure OPENAI_API_KEY is correct in .env"
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
            
            # Verify embeddings were stored by checking collection
            try:
                collection = self.vectorstore._collection
                if collection:
                    # Get a sample to verify embeddings exist
                    sample_data = collection.get(ids=successful_ids[:min(3, len(successful_ids))], include=["embeddings"])
                    if sample_data.get("embeddings") and len(sample_data["embeddings"]) > 0:
                        logger.info("Verified embeddings are stored in collection")
                    else:
                        logger.warning("Embeddings may not be stored properly in collection")
            except Exception as verify_error:
                logger.debug(f"Could not verify embeddings: {verify_error}")
            
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
    
    def _manual_similarity_search(
        self,
        query: str,
        k: int,
        collection_data: Dict,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Manual cosine similarity search for small collections to bypass HNSW index.
        
        Args:
            query: Search query text
            k: Number of results to return
            collection_data: Collection data from ChromaDB
            filter_dict: Optional metadata filters
            
        Returns:
            List of document dictionaries with text, metadata, and similarity scores
        """
        try:
            import numpy as np
            use_numpy = True
        except ImportError:
            logger.warning("numpy not available, using Python built-in for cosine similarity")
            use_numpy = False
            np = None  # Set to None to avoid NameError
        
        try:
            # Get query embedding
            query_embedding_list = self.embeddings.embed_query(query)
            if use_numpy:
                query_embedding = np.array(query_embedding_list)
            else:
                query_embedding = query_embedding_list
            
            # Get all documents and their embeddings
            all_ids = collection_data.get("ids", [])
            all_documents = collection_data.get("documents", [])
            all_metadatas = collection_data.get("metadatas", [])
            all_embeddings = collection_data.get("embeddings", [])
            
            # Check if embeddings are None or empty
            if not all_embeddings or len(all_embeddings) == 0 or all_embeddings[0] is None:
                logger.warning("No embeddings found in collection data, embeddings may not be stored")
                logger.warning("Falling back to re-embedding documents (this is slower but works)")
                # If embeddings aren't stored, we need to re-embed the documents
                if all_documents:
                    try:
                        all_embeddings = self.embeddings.embed_documents(all_documents)
                        logger.info(f"Re-embedded {len(all_embeddings)} documents for manual similarity search")
                    except Exception as embed_error:
                        logger.error(f"Failed to re-embed documents: {embed_error}")
                        return []
                else:
                    logger.error("No documents found in collection")
                    return []
            
            # Filter out None embeddings
            valid_indices = []
            for i, emb in enumerate(all_embeddings):
                if emb is not None and len(emb) > 0:
                    valid_indices.append(i)
            
            if not valid_indices:
                logger.warning("No valid embeddings found, re-embedding all documents")
                if all_documents:
                    all_embeddings = self.embeddings.embed_documents(all_documents)
                    valid_indices = list(range(len(all_documents)))
                else:
                    return []
            
            # Filter to only valid entries
            if len(valid_indices) < len(all_documents):
                logger.info(f"Filtering to {len(valid_indices)} valid embeddings out of {len(all_documents)} documents")
                all_ids = [all_ids[i] for i in valid_indices]
                all_documents = [all_documents[i] for i in valid_indices]
                all_metadatas = [all_metadatas[i] if i < len(all_metadatas) else {} for i in valid_indices]
                all_embeddings = [all_embeddings[i] for i in valid_indices]
            
            if len(all_embeddings) != len(all_documents):
                logger.warning(f"Embedding count ({len(all_embeddings)}) doesn't match document count ({len(all_documents)})")
                # Use the minimum length to avoid index errors
                min_len = min(len(all_embeddings), len(all_documents), len(all_metadatas) if all_metadatas else len(all_documents))
                all_embeddings = all_embeddings[:min_len]
                all_documents = all_documents[:min_len]
                all_metadatas = all_metadatas[:min_len] if all_metadatas else [{}] * min_len
                all_ids = all_ids[:min_len]
            
            # Calculate cosine similarities
            similarities = []
            for i, doc_embedding in enumerate(all_embeddings):
                # Apply metadata filter if provided
                if filter_dict:
                    doc_metadata = all_metadatas[i] if i < len(all_metadatas) else {}
                    if not all(k in doc_metadata and doc_metadata[k] == v for k, v in filter_dict.items()):
                        continue
                
                # Cosine similarity: since embeddings are normalized, it's just the dot product
                if use_numpy:
                    doc_embedding_array = np.array(doc_embedding)
                    similarity = float(np.dot(query_embedding, doc_embedding_array))
                else:
                    # Manual dot product for normalized vectors (cosine similarity)
                    similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                similarities.append((i, similarity))
            
            # Sort by similarity (descending) and get top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_k_similarities = similarities[:min(k, len(similarities))]
            
            # Build result documents
            documents = []
            for idx, score in top_k_similarities:
                if idx < len(all_documents):
                    documents.append({
                        "text": all_documents[idx],
                        "metadata": all_metadatas[idx] if idx < len(all_metadatas) else {},
                        "score": float(score)
                    })
            
            logger.info(f"Retrieved {len(documents)} documents using manual cosine similarity")
            return documents
            
        except Exception as e:
            logger.error(f"Error in manual similarity search: {e}", exc_info=True)
            # Try one more time with re-embedding if embeddings were missing
            try:
                if all_documents and len(all_documents) > 0:
                    logger.info("Retrying manual search with re-embedded documents...")
                    all_embeddings = self.embeddings.embed_documents(all_documents)
                    query_embedding_list = self.embeddings.embed_query(query)
                    
                    # Determine if numpy is available for retry
                    try:
                        import numpy as np
                        retry_use_numpy = True
                    except ImportError:
                        retry_use_numpy = False
                    
                    if retry_use_numpy:
                        query_embedding = np.array(query_embedding_list)
                    else:
                        query_embedding = query_embedding_list
                    
                    similarities = []
                    for i, doc_embedding in enumerate(all_embeddings):
                        if filter_dict:
                            doc_metadata = all_metadatas[i] if i < len(all_metadatas) else {}
                            if not all(k in doc_metadata and doc_metadata[k] == v for k, v in filter_dict.items()):
                                continue
                        
                        if retry_use_numpy:
                            doc_embedding_array = np.array(doc_embedding)
                            similarity = float(np.dot(query_embedding, doc_embedding_array))
                        else:
                            similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                        similarities.append((i, similarity))
                    
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    top_k_similarities = similarities[:min(k, len(similarities))]
                    
                    documents = []
                    for idx, score in top_k_similarities:
                        if idx < len(all_documents):
                            documents.append({
                                "text": all_documents[idx],
                                "metadata": all_metadatas[idx] if idx < len(all_metadatas) else {},
                                "score": float(score)
                            })
                    
                    if documents:
                        logger.info(f"Retry succeeded: Retrieved {len(documents)} documents using manual cosine similarity")
                        return documents
            except Exception as retry_error:
                logger.error(f"Retry also failed: {retry_error}", exc_info=True)
            
            return []
    
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
            # Always try to get collection data first for fallback
            collection_data = None
            collection_size = 0
            try:
                collection = self.vectorstore._collection
                if collection:
                    # Get collection data WITH embeddings included for fallback
                    collection_data = collection.get(include=["embeddings", "documents", "metadatas"])
                    collection_size = len(collection_data.get("ids", []))
                    logger.info(f"Collection has {collection_size} documents")
                    
                    # For collections of any size, prefer manual similarity to avoid HNSW issues
                    # HNSW index can fail even with proper parameters, so manual search is more reliable
                    if collection_size > 0:
                        logger.info(f"Using manual cosine similarity to bypass HNSW index (collection size: {collection_size})")
                        manual_results = self._manual_similarity_search(query, k, collection_data, filter_dict)
                        if manual_results:
                            return manual_results
                        else:
                            logger.warning("Manual similarity search returned no results, will try HNSW as fallback")
            except Exception as size_check_error:
                logger.warning(f"Could not get collection data for manual search: {size_check_error}, proceeding with HNSW search")
            
            # Try with score first for larger collections
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
            except Exception as score_error:
                error_str = str(score_error)
                # If similarity_search_with_score fails (e.g., ChromaDB HNSW index issue), try without score
                if "contigious" in error_str.lower() or "contiguous" in error_str.lower() or "ef" in error_str.lower() or "M is too small" in error_str or "hnsw" in error_str.lower():
                    logger.warning(f"similarity_search_with_score failed ({error_str[:100]}), trying similarity_search without scores...")
                    try:
                        # Fallback to similarity_search without scores
                        results = self.vectorstore.similarity_search(
                            query=query,
                            k=k,
                            filter=filter_dict
                        )
                        
                        documents = []
                        for doc in results:
                            documents.append({
                                "text": doc.page_content,
                                "metadata": doc.metadata,
                                "score": 0.0  # No score available
                            })
                        
                        logger.info(f"Retrieved {len(documents)} documents for query (without scores)")
                        return documents
                    except Exception as fallback_error:
                        logger.error(f"Both similarity search methods failed: {fallback_error}")
                        # Last resort: Use manual cosine similarity if we have collection data
                        if collection_data:
                            logger.warning("Attempting manual cosine similarity as last resort...")
                            try:
                                manual_results = self._manual_similarity_search(query, k, collection_data, filter_dict)
                                if manual_results:
                                    logger.info(f"Manual similarity search succeeded, retrieved {len(manual_results)} documents")
                                    return manual_results
                            except Exception as manual_error:
                                logger.error(f"Manual similarity search also failed: {manual_error}")
                        
                        # Final fallback: Use ChromaDB client directly to bypass HNSW index
                        logger.warning("Attempting direct ChromaDB client query as final fallback...")
                        try:
                            # Reuse existing client instead of creating a new one
                            if hasattr(VectorStore, '_chroma_client') and VectorStore._chroma_client:
                                client = VectorStore._chroma_client
                            else:
                                # Fallback: create client if it doesn't exist
                                client = chromadb.PersistentClient(
                                    path=self.persist_directory,
                                    settings=ChromaSettings(anonymized_telemetry=False)
                                )
                                VectorStore._chroma_client = client
                            
                            collection = client.get_collection(name=self.collection_name)
                            
                            # Get all collection data with embeddings for manual search
                            all_data = collection.get(include=["embeddings", "documents", "metadatas"])
                            if all_data and all_data.get("ids"):
                                # Use manual similarity search with all data
                                logger.info("Using manual cosine similarity with direct client data")
                                manual_results = self._manual_similarity_search(query, k, all_data, filter_dict)
                                if manual_results:
                                    return manual_results
                            
                            # If manual search still fails, try direct query (but this might also fail with HNSW)
                            query_embedding = self.embeddings.embed_query(query)
                            collection_size = len(all_data.get("ids", [])) if all_data else 0
                            n_results = min(k, max(collection_size, 1)) if collection_size > 0 else k
                            
                            # Try query with where clause to bypass index issues
                            try:
                                results = collection.query(
                                    query_embeddings=[query_embedding],
                                    n_results=n_results,
                                    include=["documents", "metadatas"]
                                )
                                
                                documents = []
                                if results.get('ids') and len(results['ids'][0]) > 0:
                                    for i in range(len(results['ids'][0])):
                                        text = results['documents'][0][i] if results.get('documents') and results['documents'][0] else ""
                                        metadata = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
                                        
                                        if text:
                                            documents.append({
                                                "text": text,
                                                "metadata": metadata,
                                                "score": 0.0  # No score from direct query
                                            })
                                    
                                    logger.info(f"Retrieved {len(documents)} documents using direct ChromaDB client")
                                    return documents
                            except Exception as query_error:
                                logger.error(f"Direct query failed: {query_error}, trying manual search with all data")
                                # Final attempt: manual search with all collection data
                                if all_data and all_data.get("ids"):
                                    return self._manual_similarity_search(query, k, all_data, filter_dict)
                            
                            logger.warning("All retrieval methods failed, returning empty list")
                            return []
                        except Exception as direct_error:
                            logger.error(f"Direct ChromaDB client query also failed: {direct_error}")
                            # Try one more time with manual search if we can get the data
                            try:
                                if hasattr(VectorStore, '_chroma_client') and VectorStore._chroma_client:
                                    collection = VectorStore._chroma_client.get_collection(name=self.collection_name)
                                    all_data = collection.get(include=["embeddings", "documents", "metadatas"])
                                    if all_data:
                                        return self._manual_similarity_search(query, k, all_data, filter_dict)
                            except:
                                pass
                            # Return empty list as final fallback
                            return []
                else:
                    raise
            
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
    
    def similarity_search_with_score(self, query: str, k: int = 4, filter_dict: Optional[Dict] = None) -> tuple:
        """
        Search for similar documents and return results with confidence score.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            Tuple of (documents list, confidence score 0-1)
        """
        results = self.similarity_search(query, k, filter_dict)
        
        if not results:
            return [], 0.0
        
        # Calculate confidence from the score of the top result
        top_score = results[0].get("score", 0.0) if isinstance(results[0], dict) else 0.0
        
        # Convert similarity score (0-1) to confidence (0-1)
        # Higher similarity = higher confidence
        confidence = min(1.0, max(0.0, top_score))
        
        logger.debug(f"Retrieved {len(results)} results with top confidence: {confidence:.2f}")
        return results, confidence
    
    def clear_all_documents(self):
        """
        Clear all documents from the vector store.
        This is useful when uploading a new document to avoid mixing old and new content.
        """
        try:
            # Get all document IDs from the collection
            collection = self.vectorstore._collection
            if collection:
                # Get all IDs
                all_ids = collection.get()["ids"]
                if all_ids:
                    logger.info(f"Clearing {len(all_ids)} documents from vector store")
                    # Delete all documents
                    collection.delete(ids=all_ids)
                    logger.info("Successfully cleared all documents from vector store")
                else:
                    logger.info("Vector store is already empty")
            else:
                logger.warning("Collection not found, cannot clear documents")
        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            # Try alternative method: delete and recreate collection
            try:
                logger.info("Attempting to clear by deleting and recreating collection...")
                self.delete_collection()
                # Reinitialize the vectorstore
                self._initialize_vectorstore()
                logger.info("Successfully cleared vector store by recreating collection")
            except Exception as recreate_error:
                logger.error(f"Failed to clear vector store: {recreate_error}")
                raise ValueError(f"Could not clear vector store: {recreate_error}") from recreate_error
    
    def delete_collection(self):
        """Delete the entire collection (use with caution)."""
        try:
            # Reuse existing client if available
            if hasattr(VectorStore, '_chroma_client') and VectorStore._chroma_client:
                client = VectorStore._chroma_client
            else:
                # Create client if it doesn't exist
                client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                VectorStore._chroma_client = client
            
            client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            # Reinitialize empty collection
            self._initialize_vectorstore()
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def get_all_documents(self, limit: int = 20) -> List[Dict]:
        """
        Get all documents from the collection as a fallback when similarity search fails.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries with text and metadata
        """
        try:
            collection = self.vectorstore._collection
            if not collection:
                logger.warning("Collection not available for get_all_documents")
                return []
            
            # Get all documents from the collection
            all_data = collection.get(limit=limit, include=["documents", "metadatas"])
            
            documents = []
            if all_data and all_data.get("ids"):
                ids = all_data.get("ids", [])
                docs = all_data.get("documents", [])
                metadatas = all_data.get("metadatas", [])
                
                for i in range(len(ids)):
                    text = docs[i] if i < len(docs) else ""
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    
                    if text and text.strip():
                        documents.append({
                            "text": text,
                            "metadata": metadata,
                            "score": 0.0  # No similarity score for fallback
                        })
                
                logger.info(f"Retrieved {len(documents)} documents from collection (fallback method)")
                return documents
            else:
                logger.warning("No documents found in collection")
                return []
                
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []
    
    def get_retriever(self, k: int = 5):
        """
        Get a LangChain retriever from the vectorstore.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            LangChain retriever
        """
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

