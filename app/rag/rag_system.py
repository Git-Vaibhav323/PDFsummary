"""
Enterprise RAG pipeline integrator.

Orchestrates all components:
- Document ingestion
- RAG retrieval
- Memory management
- Visualization
- Response formatting

Performance optimized with caching, batching, and timing logs.
"""
import logging
import asyncio
import time
from typing import Dict, Optional, List, Tuple
from app.rag.document_processor import DocumentProcessor
from app.rag.rag_pipeline import RAGRetriever
from app.rag.visualization_pipeline import VisualizationPipeline
from app.rag.response_handler import ResponseBuilder
from app.rag.memory import add_to_memory, get_global_memory, clear_memory as memory_clear
from app.database.documents import DocumentStorage
from app.rag.vector_store import VectorStore
from app.rag.cache_manager import get_cache_manager
from app.rag.web_search import WebSearchService, should_use_web_search
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EnterpriseRAGSystem:
    """Complete enterprise RAG system."""
    
    def __init__(self):
        """Initialize RAG system."""
        self.vector_store: Optional[VectorStore] = None
        self.doc_processor: Optional[DocumentProcessor] = None
        self.rag_retriever: Optional[RAGRetriever] = None
        self.viz_pipeline: Optional[VisualizationPipeline] = None
        self.document_storage: Optional[DocumentStorage] = None
        self.web_search: Optional[WebSearchService] = None
        self._initialized = False
        self.current_document_ids: List[str] = []  # Track all loaded documents (multi-doc support)
        
        logger.info("Enterprise RAG System initialized")
    
    def initialize(self):
        """Initialize all components (lazy loading)."""
        if self._initialized:
            return
        
        logger.info("Initializing RAG system components...")
        
        try:
            # Initialize vector store
            self.vector_store = VectorStore()
            
            # Initialize document processor
            self.doc_processor = DocumentProcessor()
            
            # Initialize RAG retriever
            self.rag_retriever = RAGRetriever(
                vector_store=self.vector_store,
                top_k=settings.top_k_retrieval
            )
            
            # Initialize visualization pipeline
            self.viz_pipeline = VisualizationPipeline()
            
            # Initialize document storage
            self.document_storage = DocumentStorage()
            
            # Initialize web search service
            self.web_search = WebSearchService()
            
            self._initialized = True
            logger.info("RAG system fully initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    async def ingest_document_async(self,
                                   document_id: str,
                                   pages: List[Dict],
                                   filename: str = "document.pdf") -> Dict:
        """
        Ingest document asynchronously.
        
        Args:
            document_id: Unique document ID
            pages: List of page dictionaries with 'text' and 'page_number'
            filename: Original filename
            
        Returns:
            Ingestion result with processing details
        """
        self.initialize()
        
        logger.info(f"Starting document ingestion: {filename}")
        
        try:
            # Step 1: Process document
            result = await self.doc_processor.process_document_async(
                document_id=document_id,
                pages=pages,
                filename=filename
            )
            
            chunks = result.get("chunks", [])
            logger.info(f"Processed {len(chunks)} chunks from {filename}")
            
            # Step 2: Add to vector store (embedding done here)
            doc_ids = self.vector_store.add_documents(chunks)
            logger.info(f"Added {len(doc_ids)} documents to vector store")
            
            # Step 3: Store document metadata
            if self.document_storage:
                metadata = result.get("metadata", {})
                self.document_storage.create_document(
                    document_id=document_id,
                    name=filename,
                    filename=filename,
                    chunks_count=len(chunks),
                    pages_count=len(pages),
                    status="processed",
                    metadata=metadata
                )
            
            # CRITICAL: Add document ID to list (multi-doc support)
            if document_id not in self.current_document_ids:
                self.current_document_ids.append(document_id)
            logger.info(f"✅ Added document {document_id} to active documents: {self.current_document_ids}")
            
            return {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "chunks_processed": len(chunks),
                "documents_indexed": len(doc_ids),
                "metadata": result.get("metadata")
            }
        
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def answer_question(self, question: str, use_memory: bool = True, fast_mode: bool = False, session_id: Optional[str] = None, document_ids: Optional[List[str]] = None, use_web_search: Optional[bool] = None) -> Dict:
        """
        Answer a question using RAG pipeline with caching and performance tracking.
        
        Supports multi-document queries and cross-document analysis.
        
        Args:
            question: User question
            use_memory: Whether to use conversation memory
            fast_mode: If True, use optimized fast retrieval (for finance agent)
            session_id: Optional session ID for memory scoping
            document_ids: Optional list of document IDs to filter by (None = all documents)
            use_web_search: User-controlled web search toggle (True = always, False = never, None = auto-detect)
            
        Returns:
            Dictionary with answer, optional visualizations, and web search metadata
        """
        self.initialize()
        
        start_time = time.time()
        cache_manager = get_cache_manager()
        
        logger.info(f"📋 Processing question: {question[:80]}... {'⚡ FAST MODE' if fast_mode else ''}")
        
        # CRITICAL: Set document filter(s) if specified
        # If document_ids provided, use those; otherwise use all active documents
        filter_doc_ids = document_ids if document_ids is not None else self.current_document_ids
        
        if filter_doc_ids:
            # For multi-doc, we'll search across all specified documents
            # The vector store will filter by document_id metadata
            logger.info(f"🔐 Document filter active: {filter_doc_ids}")
            # Note: Vector store filtering happens in retrieve() method
        else:
            logger.info(f"🔓 No document filter - searching across all documents")
            self.rag_retriever.set_document_filter(None)
        
        try:
            # Step 1: Check response cache first (skip cache in fast mode for freshness)
            if not fast_mode:
                cached_response = cache_manager.get_response(question)
                if cached_response:
                    logger.info(f"⚡ Cache HIT: Returning cached response")
                    return {
                        "success": True,
                        "response": cached_response,
                        "metadata": {
                            "source": "cache",
                            "latency_s": time.time() - start_time
                        }
                    }
            
            # Step 2: RAG pipeline (retrieval + answer generation) with timing
            retrieval_start = time.time()
            rag_result = self.rag_retriever.answer_question(
                question=question,
                use_memory=use_memory,
                fast_mode=fast_mode,
                session_id=session_id,
                document_ids=filter_doc_ids
            )
            retrieval_time = time.time() - retrieval_start
            
            answer = rag_result.get("answer", "")
            context = rag_result.get("context", "")
            retrieval_score = rag_result.get("retrieval_score", 0.0)
            
            logger.info(f"✅ RAG Pipeline: {retrieval_time:.3f}s | Answer: {len(answer)} chars | Context: {len(context)} chars")
            
            # Step 2.5: Check if web search is needed (user-controlled or auto-detect)
            web_search_results = None
            web_search_context = ""
            web_search_source = None
            web_search_used = False
            
            # If user explicitly requested web search, perform it BEFORE generating document answer
            # This allows us to prioritize web results when user wants them
            if self.web_search and self.web_search.is_available() and use_web_search is True:
                # User explicitly requested web search - perform search first
                web_search_source = "user_requested"
                logger.info("🌐 Web search: USER REQUESTED - performing search first")
                web_search_start = time.time()
                web_results = self.web_search.search(question, max_results=5)  # Get more results for user-requested
                web_search_time = time.time() - web_search_start
                
                if web_results:
                    web_search_results = web_results
                    web_search_context = self.web_search.format_search_results(web_results)
                    web_search_used = True
                    logger.info(f"✅ Web search ({web_search_source}): {web_search_time:.3f}s | {len(web_results)} results")
                    
                    # Generate answer primarily from web search results (with document context as supplement)
                    from app.rag.rag_pipeline import RAGRetriever
                    # Combine contexts: web search first (primary), then document context (supplement)
                    combined_context = f"{web_search_context}\n\n[Document Context (for reference only):]\n{context}"
                    web_answer = self.rag_retriever.generate_answer(
                        question=question,
                        context=combined_context,
                        use_memory=False
                    )
                    
                    # Use web search answer as primary, document answer as supplement if available
                    if answer and answer.strip() and "not available" not in answer.lower():
                        # Document has some info - combine them
                        answer = f"{web_answer}\n\n[Note: The uploaded document contains information up to 2022. The above information is from web search and may include more recent updates.]"
                    else:
                        # Document has no relevant info - use web search answer directly
                        answer = web_answer
            
            # Auto-detect web search (only if user didn't explicitly request it)
            elif self.web_search and self.web_search.is_available() and use_web_search is not False:
                # Determine if web search should be used automatically
                should_search = should_use_web_search(question, context, retrieval_score)
                
                if should_search:
                    web_search_source = "auto_triggered"
                    logger.info("🌐 Web search: AUTO-TRIGGERED based on context/score")
                    web_search_start = time.time()
                    web_results = self.web_search.search(question, max_results=3)
                    web_search_time = time.time() - web_search_start
                    
                    if web_results:
                        web_search_results = web_results
                        web_search_context = self.web_search.format_search_results(web_results)
                        web_search_used = True
                        logger.info(f"✅ Web search ({web_search_source}): {web_search_time:.3f}s | {len(web_results)} results")
                        
                        # Enhance answer with web search context when document context is weak
                        if retrieval_score < 0.6:
                            # Regenerate answer with web context
                            from app.rag.rag_pipeline import RAGRetriever
                            enhanced_answer = self.rag_retriever.generate_answer(
                                question=question,
                                context=f"{context}\n\n{web_search_context}",
                                use_memory=False
                            )
                            # Auto-triggered - supplement document answer
                            answer = f"{answer}\n\n[Additional information from web search:]\n{enhanced_answer}"
            
            # Step 3: Visualization pipeline (skip in fast mode for speed)
            viz_start = time.time()
            viz_result = None
            if not fast_mode and context:
                viz_result = self.viz_pipeline.process(
                    question=question,
                    context=context,
                    answer=answer
                )
                viz_time = time.time() - viz_start
                logger.info(f"📊 Visualization: {viz_time:.3f}s" + (f" | Type: {viz_result.get('chart', {}).get('type')}" if viz_result and viz_result.get('chart') else ""))
                
                # CRITICAL: Check for errors in visualization result
                if viz_result and "error" in viz_result:
                    logger.error(f"❌ Visualization error: {viz_result.get('error')}")
                    # Return error in metadata so API can handle it
                    return {
                        "success": True,
                        "response": ResponseBuilder.build_from_rag_result(
                            rag_result=rag_result,
                            viz_result={"error": viz_result.get("error")},
                            chat_history=get_global_memory().get_history()
                        ).model_dump(exclude_none=True),
                        "metadata": {
                            "retrieved_docs": rag_result.get("document_count", 0),
                            "has_visualization": False,
                            "viz_result": viz_result,  # Include error for API handling
                            "latency_s": time.time() - start_time,
                            "retrieval_s": retrieval_time
                        }
                    }
                
                if viz_result and viz_result.get("chart"):
                    chart_type = viz_result['chart'].get('type')
                    if chart_type == 'table':
                        logger.info(f"📋 Generated table visualization")
                    else:
                        logger.info(f"📈 Generated {chart_type} chart visualization")
            
            # Step 4: Get chat history (session-scoped)
            memory = get_global_memory(session_id)
            chat_history = memory.get_history()
            
            # Step 5: Build response
            response_dict = ResponseBuilder.build_from_rag_result(
                rag_result=rag_result,
                viz_result=viz_result,
                chat_history=chat_history
            ).model_dump(exclude_none=True)
            
            # Add web search metadata to response
            response_dict["web_search_used"] = web_search_used
            response_dict["web_search_source"] = web_search_source
            
            # Cache the response
            cache_manager.set_response(question, response_dict)
            
            total_time = time.time() - start_time
            logger.info(f"🎯 LATENCY: Total={total_time:.3f}s | Retrieval={retrieval_time:.3f}s | Visualization={viz_time if viz_result else 0:.3f}s")
            
            return {
                "success": True,
                "response": response_dict,
                "metadata": {
                    "retrieved_docs": rag_result.get("document_count", 0),
                    "has_visualization": bool(viz_result and viz_result.get("chart")),
                    "latency_s": total_time,
                    "retrieval_s": retrieval_time,
                    "cache_stats": cache_manager.get_stats(),
                    "web_search_used": web_search_used,
                    "web_search_source": web_search_source
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Question answering failed: {e}", exc_info=True)
            
            # Still try to return a response object
            memory = get_global_memory(session_id)
            response = ResponseBuilder.build_error_response(
                error=str(e),
                chat_history=memory.get_history()
            )
            
            return {
                "success": False,
                "response": response.model_dump(exclude_none=True),
                "error": str(e)
            }
    
    def get_memory_history(self, session_id: Optional[str] = None) -> List[Dict]:
        """Get conversation memory for a session."""
        memory = get_global_memory(session_id)
        return memory.get_history()
    
    def clear_memory(self, session_id: Optional[str] = None):
        """Clear conversation memory for a session."""
        memory_clear(session_id)
        logger.info(f"Conversation memory cleared for session: {session_id or 'default'}")
    
    def reset(self, clear_documents: bool = False):
        """
        Reset entire system.
        
        Args:
            clear_documents: If True, clear all documents from vector store
        """
        try:
            if clear_documents and self.vector_store:
                self.vector_store.clear_all_documents()
            if self.document_storage and clear_documents:
                self.document_storage.clear_all_documents()
            self.current_document_ids = []  # Clear document IDs tracking
            self._initialized = False
            logger.info("RAG system reset successfully")
        except Exception as e:
            logger.error(f"Error resetting system: {e}")
            raise
    
    def list_documents(self) -> List[Dict]:
        """List all uploaded documents."""
        if self.document_storage:
            return self.document_storage.list_documents()
        return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the system.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            # Remove from active list
            if document_id in self.current_document_ids:
                self.current_document_ids.remove(document_id)
            
            # Delete from storage
            if self.document_storage:
                self.document_storage.delete_document(document_id)
            
            # Note: We don't delete from vector store as it's expensive
            # Documents will be filtered out in retrieval if needed
            logger.info(f"Document {document_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_status(self, session_id: Optional[str] = None) -> Dict:
        """Get system status."""
        try:
            memory = get_global_memory(session_id)
            
            return {
                "initialized": self._initialized,
                "vector_store_ready": self.vector_store is not None,
                "memory_messages": len(memory),
                "active_documents": len(self.current_document_ids),
                "document_ids": self.current_document_ids,
                "config": {
                    "model": settings.openai_model,
                    "embedding_model": settings.embedding_model_name,
                    "temperature": settings.temperature,
                    "top_k_retrieval": settings.top_k_retrieval,
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap
                }
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"error": str(e)}


# Global RAG system instance
_rag_system: Optional[EnterpriseRAGSystem] = None


def get_rag_system() -> EnterpriseRAGSystem:
    """
    Get or create global RAG system instance.
    
    Returns:
        EnterpriseRAGSystem instance
    """
    global _rag_system
    if _rag_system is None:
        _rag_system = EnterpriseRAGSystem()
    return _rag_system


def initialize_rag_system():
    """Initialize RAG system components."""
    system = get_rag_system()
    system.initialize()
