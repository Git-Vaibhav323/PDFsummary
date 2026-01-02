"""
Enterprise RAG pipeline integrator.

Orchestrates all components:
- Document ingestion
- RAG retrieval
- Memory management
- Visualization
- Response formatting
"""
import logging
import asyncio
from typing import Dict, Optional, List, Tuple
from app.rag.document_processor import DocumentProcessor
from app.rag.rag_pipeline import RAGRetriever
from app.rag.visualization_pipeline import VisualizationPipeline
from app.rag.response_handler import ResponseBuilder
from app.rag.memory import add_to_memory, get_global_memory, clear_memory as memory_clear
from app.rag.vector_store import VectorStore
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
        self._initialized = False
        
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
    
    def answer_question(self, question: str, use_memory: bool = True) -> Dict:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User question
            use_memory: Whether to use conversation memory
            
        Returns:
            Dictionary with answer and optional visualizations
        """
        self.initialize()
        
        logger.info(f"Processing question: {question[:100]}")
        
        try:
            # Step 1: RAG pipeline (retrieval + answer generation)
            rag_result = self.rag_retriever.answer_question(
                question=question,
                use_memory=use_memory
            )
            
            answer = rag_result.get("answer", "")
            context = rag_result.get("context", "")
            
            logger.info(f"Generated answer ({len(answer)} chars)")
            
            # Step 2: Visualization pipeline
            viz_result = None
            if context:
                viz_result = self.viz_pipeline.process(
                    question=question,
                    context=context,
                    answer=answer
                )
                
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
                            "viz_result": viz_result  # Include error for API handling
                        }
                    }
                
                if viz_result and viz_result.get("chart"):
                    chart_type = viz_result['chart'].get('type')
                    if chart_type == 'table':
                        logger.info(f"Generated table visualization")
                    else:
                        logger.info(f"✅ Generated {chart_type} chart visualization")
            
            # Step 3: Get chat history
            memory = get_global_memory()
            chat_history = memory.get_history()
            
            # Step 4: Build response
            response = ResponseBuilder.build_from_rag_result(
                rag_result=rag_result,
                viz_result=viz_result,
                chat_history=chat_history
            )
            
            return {
                "success": True,
                "response": response.model_dump(exclude_none=True),
                "metadata": {
                    "retrieved_docs": rag_result.get("document_count", 0),
                    "has_visualization": bool(viz_result and viz_result.get("chart"))
                }
            }
        
        except Exception as e:
            logger.error(f"Question answering failed: {e}", exc_info=True)
            
            # Still try to return a response object
            memory = get_global_memory()
            response = ResponseBuilder.build_error_response(
                error=str(e),
                chat_history=memory.get_history()
            )
            
            return {
                "success": False,
                "response": response.model_dump(exclude_none=True),
                "error": str(e)
            }
    
    def get_memory_history(self) -> List[Dict]:
        """Get conversation memory."""
        memory = get_global_memory()
        return memory.get_history()
    
    def clear_memory(self):
        """Clear conversation memory."""
        memory_clear()
        logger.info("Conversation memory cleared")
    
    def reset(self):
        """Reset entire system."""
        try:
            if self.vector_store:
                self.vector_store.clear_all_documents()
            memory_clear()
            self._initialized = False
            logger.info("RAG system reset successfully")
        except Exception as e:
            logger.error(f"Error resetting system: {e}")
            raise
    
    def get_status(self) -> Dict:
        """Get system status."""
        try:
            memory = get_global_memory()
            
            return {
                "initialized": self._initialized,
                "vector_store_ready": self.vector_store is not None,
                "memory_messages": len(memory),
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
