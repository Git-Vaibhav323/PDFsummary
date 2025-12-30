"""
FastAPI routes for PDF upload and chat functionality.
"""
import os
import shutil
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from app.rag.pdf_loader import PDFLoader
from app.rag.chunker import TextChunker
from app.rag.vector_store import VectorStore
from app.rag.retriever import ContextRetriever
from app.rag.graph import RAGGraph
from app.config.settings import settings
from app.database.conversations import ConversationStorage

logger = logging.getLogger(__name__)

# Initialize components
vector_store = None
retriever = None
rag_graph = None
conversation_storage = ConversationStorage()

# Initialize on startup
def initialize_components():
    """Initialize RAG components."""
    global vector_store, retriever, rag_graph
    # Don't initialize vector_store here - it will be lazy-loaded on first PDF upload
    # This prevents the heavy embedding model from loading during startup
    logger.info("RAG components ready for lazy initialization")
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    initialize_components()
    yield
    # Shutdown (if needed)
    pass

# FastAPI app
app = FastAPI(
    title="PDF Chatbot",
    description="Production-ready RAG chatbot for PDF documents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - allow Netlify domains and localhost for development
import os

# Get allowed origins from environment or use defaults
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Parse comma-separated origins from environment
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default origins for development and production
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
    ]
    # Add common Netlify patterns (will be replaced with actual domain)
    # User should set ALLOWED_ORIGINS environment variable in Render with their Netlify URL
    # Example: ALLOWED_ORIGINS=https://your-app.netlify.app,https://your-app.netlify.app/*

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    question: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    visualization: Optional[dict] = None
    conversation_id: Optional[str] = None


class CreateConversationRequest(BaseModel):
    """Create conversation request model."""
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


# Routes
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    
    Args:
        file: PDF file upload
        
    Returns:
        Success message with processing details
    """
    global vector_store
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file temporarily
    temp_path = f"./temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Load PDF
        pdf_loader = PDFLoader()
        pdf_data = pdf_loader.load_pdf(temp_path)
        
        if not pdf_data or not pdf_data.get("pages"):
            raise HTTPException(status_code=400, detail="PDF is empty or cannot be read")
        
        # Run preprocessing pipeline (OCR, cleaning, structured data extraction)
        try:
            from app.rag.preprocessing_graph import PreprocessingGraph
            import os
            mistral_key = os.getenv("MISTRAL_API_KEY")
            preprocessing = PreprocessingGraph(mistral_api_key=mistral_key)
            processed_data = preprocessing.process(temp_path, pdf_data)
            
            # Update pdf_data with processed results
            pdf_data["text"] = processed_data["text"]
            pdf_data["pages"] = processed_data["pages"]
            pdf_data["structured_data"] = processed_data.get("structured_data", [])
            
            if processed_data.get("error"):
                logger.warning(f"Preprocessing warning: {processed_data['error']}")
        except Exception as preprocess_error:
            logger.warning(f"Preprocessing failed, using original PDF data: {preprocess_error}")
            # Continue with original data if preprocessing fails
        
        # Chunk text
        chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = chunker.chunk_pages(pdf_data["pages"])
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No text chunks could be created")
        
        # Clear old documents before adding new ones to avoid mixing documents
        global vector_store, retriever, rag_graph
        if vector_store is None:
            vector_store = VectorStore()
            retriever = ContextRetriever(vector_store)
            rag_graph = None  # Will be recreated after adding documents
        else:
            # Clear existing documents to avoid mixing old and new content
            try:
                logger.info("Clearing old documents from vector store...")
                # Try to delete and recreate collection to fix any HNSW index issues
                try:
                    vector_store.delete_collection()
                    logger.info("Deleted old collection to fix potential HNSW issues")
                    # Reinitialize vector store - CRITICAL: This creates a new collection with new UUID
                    vector_store = VectorStore()
                    retriever = ContextRetriever(vector_store)
                    # CRITICAL: Reset rag_graph so it uses the new retriever with new collection
                    rag_graph = None
                    logger.info("Reinitialized vector store and reset RAG graph")
                except Exception as delete_error:
                    logger.warning(f"Could not delete collection: {delete_error}, trying clear_all_documents...")
                    vector_store.clear_all_documents()
                    # Still reset rag_graph to ensure it uses current vector store
                    rag_graph = None
                logger.info("Old documents cleared successfully")
            except Exception as clear_error:
                logger.warning(f"Could not clear old documents (this is OK if vector store is empty): {clear_error}")
                # Try to recreate vector store
                try:
                    vector_store = VectorStore()
                    retriever = ContextRetriever(vector_store)
                    rag_graph = None  # Reset to ensure fresh graph
                except Exception as recreate_error:
                    logger.error(f"Failed to recreate vector store: {recreate_error}")
        
        # Add new documents to vector store
        logger.info(f"Starting to add {len(chunks)} chunks to vector store (this may take several minutes for large files)...")
        doc_ids = vector_store.add_documents(chunks)
        
        # Verify documents were added successfully
        if not doc_ids or len(doc_ids) == 0:
            raise HTTPException(status_code=500, detail="Failed to add documents to vector store. No documents were indexed.")
        
        logger.info(f"Successfully indexed {len(doc_ids)} document chunks")
        
        # CRITICAL: Always recreate RAG graph after adding documents to ensure it uses the current retriever
        # This ensures the graph uses the correct collection UUID
        logger.info("Reinitializing RAG graph with updated retriever...")
        rag_graph = RAGGraph(retriever)
        logger.info("RAG graph reinitialized successfully")
        
        # Clean up temp file
        os.remove(temp_path)
        
        return JSONResponse(content={
            "message": "PDF uploaded and processed successfully",
            "pages": pdf_data["total_pages"],
            "chunks": len(chunks),
            "document_ids": len(doc_ids)
        })
        
    except ValueError as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the PDF using RAG.
    
    Args:
        request: Chat request with question and optional conversation_id
        
    Returns:
        Chat response with answer, optional visualization, and conversation_id
    """
    global rag_graph, conversation_storage, retriever, vector_store
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # CRITICAL: Ensure components are properly initialized and synchronized
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized. Please upload a PDF first.")
    
    # Ensure retriever uses the current vector_store instance
    if retriever is None or retriever.vector_store is not vector_store:
        logger.info("Reinitializing retriever to match current vector store...")
        retriever = ContextRetriever(vector_store)
    
    # Ensure rag_graph uses the current retriever instance
    if rag_graph is None or rag_graph.retriever is not retriever:
        logger.info("Reinitializing RAG graph to match current retriever...")
        rag_graph = RAGGraph(retriever)
    
    try:
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation = conversation_storage.create_conversation()
            conversation_id = conversation["id"]
        
        logger.info(f"Chat request received for conversation {conversation_id}: {request.question[:100]}...")
        
        # Store user message
        conversation_storage.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.question
        )
        
        # Invoke RAG graph
        result = rag_graph.invoke(request.question)
        
        logger.info(f"Graph returned result. Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        answer = result.get("answer", "")
        visualization = result.get("visualization")
        
        logger.info(f"Extracted answer length: {len(answer)} characters")
        logger.info(f"Answer preview: {answer[:200] if answer else 'EMPTY'}...")
        logger.info(f"Visualization present: {visualization is not None}")
        
        # DEBUG: Log visualization details
        if visualization:
            logger.info(f"Visualization type: {type(visualization)}")
            if isinstance(visualization, dict):
                logger.info(f"Visualization keys: {list(visualization.keys())}")
                logger.info(f"Chart type: {visualization.get('chart_type')}")
                logger.info(f"Has headers: {bool(visualization.get('headers'))}")
                logger.info(f"Has rows: {bool(visualization.get('rows'))}")
                if visualization.get('headers'):
                    logger.info(f"Headers: {visualization.get('headers')[:5]}")
                if visualization.get('rows'):
                    logger.info(f"Rows count: {len(visualization.get('rows'))}")
        else:
            logger.warning("⚠️ No visualization object in response!")
        
        if not answer or not answer.strip():
            logger.error("Answer is empty in API response!")
            answer = "I couldn't generate an answer. Please try rephrasing your question or ensure the document was uploaded correctly."
        
        # Store assistant message
        conversation_storage.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            visualization=visualization
        )
        
        return ChatResponse(
            answer=answer,
            visualization=visualization,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.delete("/remove_file")
async def remove_file():
    """
    Remove the uploaded file and clear the vector store.
    
    Returns:
        Success message
    """
    global vector_store, retriever, rag_graph
    
    try:
        if vector_store is not None:
            logger.info("Clearing all documents from vector store...")
            vector_store.clear_all_documents()
            logger.info("All documents cleared successfully")
        
        # Reset components
        vector_store = None
        retriever = None
        rag_graph = None
        
        return JSONResponse(content={
            "message": "File removed successfully",
            "success": True
        })
    except Exception as e:
        logger.error(f"Error removing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing file: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "vector_store_initialized": vector_store is not None}


# Conversation endpoints
@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest = CreateConversationRequest()):
    """
    Create a new conversation.
    
    Args:
        request: Optional conversation title
        
    Returns:
        Created conversation details
    """
    try:
        conversation = conversation_storage.create_conversation(title=request.title)
        return ConversationResponse(**conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")


@app.get("/conversations")
async def list_conversations(limit: int = 50):
    """
    List all conversations.
    
    Args:
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversations
    """
    try:
        conversations = conversation_storage.list_conversations(limit=limit)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get a conversation with its messages.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Conversation with messages
    """
    try:
        conversation = conversation_storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    try:
        deleted = conversation_storage.delete_conversation(conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PDF Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload_pdf",
            "chat": "POST /chat",
            "remove_file": "DELETE /remove_file",
            "health": "GET /health",
            "create_conversation": "POST /conversations",
            "list_conversations": "GET /conversations",
            "get_conversation": "GET /conversations/{id}",
            "delete_conversation": "DELETE /conversations/{id}"
        }
    }

