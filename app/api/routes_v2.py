"""
FastAPI routes for enterprise RAG chatbot.

Integrates:
- High-performance document ingestion
- RAG retrieval with memory
- Visualization pipeline
- Standardized API responses
"""
import os
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

from app.config.settings import settings
from app.rag.rag_system import get_rag_system, initialize_rag_system
from app.rag.pdf_loader import PDFLoader
from app.rag.memory import clear_memory, get_global_memory

logger = logging.getLogger(__name__)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    question: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    table: Optional[str] = None
    chart: Optional[dict] = None
    chat_history: Optional[list] = None
    conversation_id: Optional[str] = None


class UploadResponse(BaseModel):
    """File upload response model."""
    message: str
    pages: int
    chunks: int
    document_ids: int


class StatusResponse(BaseModel):
    """System status response."""
    initialized: bool
    vector_store_ready: bool
    memory_messages: int
    config: dict


class ClearMemoryResponse(BaseModel):
    """Clear memory response."""
    message: str
    success: bool


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("🚀 FastAPI application starting...")
    try:
        initialize_rag_system()
        logger.info("✅ RAG system initialized")
    except Exception as e:
        logger.warning(f"RAG system initialization deferred to first request: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 Application shutting down...")


# FastAPI app
app = FastAPI(
    title="Enterprise RAG Chatbot",
    description="High-performance RAG chatbot for PDF documents",
    version="2.0.0",
    lifespan=lifespan
)


# CORS configuration
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default origins for development
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

# Pattern to match Netlify deploy previews
netlify_pattern = re.compile(r"https://.*\.netlify\.app$")

def check_cors_origin(origin: str) -> bool:
    """Check if origin is allowed."""
    if origin in allowed_origins:
        return True
    if netlify_pattern.match(origin):
        return True
    return False


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.netlify\.app",
)


# Routes
@app.post("/upload_pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    
    Args:
        file: PDF file upload
        
    Returns:
        Upload response with processing details
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    temp_path = f"./temp_{file.filename}"
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Processing PDF: {file.filename}")
        
        # Load PDF
        pdf_loader = PDFLoader()
        pdf_data = pdf_loader.load_pdf(temp_path)
        
        if not pdf_data or not pdf_data.get("pages"):
            raise HTTPException(status_code=400, detail="PDF is empty or cannot be read")
        
        pages = pdf_data.get("pages", [])
        total_pages = pdf_data.get("total_pages", len(pages))
        
        # Get RAG system and ingest
        rag_system = get_rag_system()
        
        # Generate document ID
        import uuid
        document_id = str(uuid.uuid4())
        
        # Ingest document asynchronously
        result = await rag_system.ingest_document_async(
            document_id=document_id,
            pages=pages,
            filename=file.filename
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Document ingestion failed: {result.get('error')}"
            )
        
        chunks_processed = result.get("chunks_processed", 0)
        documents_indexed = result.get("documents_indexed", 0)
        
        logger.info(f"✅ PDF processed: {total_pages} pages, "
                   f"{chunks_processed} chunks, {documents_indexed} indexed")
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return UploadResponse(
            message="PDF uploaded and processed successfully",
            pages=total_pages,
            chunks=chunks_processed,
            document_ids=documents_indexed
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the PDF using RAG.
    
    Args:
        request: Chat request with question
        
    Returns:
        Chat response with answer and optional visualizations
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Get RAG system
        rag_system = get_rag_system()
        
        # Process question
        result = rag_system.answer_question(
            question=request.question,
            use_memory=True
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process question: {result.get('error')}"
            )
        
        response = result.get("response", {})
        
        logger.info(f"✅ Chat response generated: {response.get('answer')[:100]}...")
        
        return ChatResponse(
            answer=response.get("answer", ""),
            table=response.get("table"),
            chart=response.get("chart"),
            chat_history=response.get("chat_history"),
            conversation_id=request.conversation_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.delete("/clear_memory", response_model=ClearMemoryResponse)
async def clear_memory_endpoint():
    """
    Clear conversation memory.
    
    Returns:
        Clear memory response
    """
    try:
        clear_memory()
        logger.info("✅ Conversation memory cleared")
        
        return ClearMemoryResponse(
            message="Conversation memory cleared successfully",
            success=True
        )
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")


@app.delete("/remove_file")
async def remove_file():
    """
    Remove uploaded document and reset vector store.
    
    Returns:
        Success message
    """
    try:
        rag_system = get_rag_system()
        rag_system.reset()
        
        logger.info("✅ Document removed and system reset")
        
        return JSONResponse(content={
            "message": "File removed successfully",
            "success": True
        })
    except Exception as e:
        logger.error(f"Error removing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing file: {str(e)}")


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system status.
    
    Returns:
        System status information
    """
    try:
        rag_system = get_rag_system()
        status = rag_system.get_status()
        
        return StatusResponse(
            initialized=status.get("initialized", False),
            vector_store_ready=status.get("vector_store_ready", False),
            memory_messages=status.get("memory_messages", 0),
            config=status.get("config", {})
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }
