"""
FastAPI routes for PDF upload and chat functionality.
"""
import os
import shutil
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from app.rag.pdf_loader import PDFLoader
from app.rag.chunker import TextChunker
from app.rag.vector_store import VectorStore
from app.rag.retriever import ContextRetriever
from app.rag.graph import RAGGraph
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Initialize components
vector_store = None
retriever = None
rag_graph = None

# Initialize on startup
def initialize_components():
    """Initialize RAG components."""
    global vector_store, retriever, rag_graph
    try:
        # Initialize vector store (will create empty collection if none exists)
        vector_store = VectorStore()
        retriever = ContextRetriever(vector_store)
        # RAG graph will be initialized when first PDF is uploaded
        logger.info("RAG components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        # Don't raise - allow startup even if vector store has issues
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
    title="RAG PDF Chatbot",
    description="Production-ready RAG chatbot for PDF documents",
    version="1.0.0",
    lifespan=lifespan
)


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    question: str


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    visualization: Optional[dict] = None


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
        
        # Chunk text
        chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = chunker.chunk_pages(pdf_data["pages"])
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No text chunks could be created")
        
        # Add to vector store
        global vector_store, retriever, rag_graph
        if vector_store is None:
            vector_store = VectorStore()
            retriever = ContextRetriever(vector_store)
        
        doc_ids = vector_store.add_documents(chunks)
        
        # Initialize RAG graph if not already initialized
        if rag_graph is None:
            rag_graph = RAGGraph(retriever)
        
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
        request: Chat request with question
        
    Returns:
        Chat response with answer and optional visualization
    """
    global rag_graph
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    global rag_graph, retriever
    
    if rag_graph is None:
        if vector_store is None:
            raise HTTPException(status_code=503, detail="Vector store not initialized. Please upload a PDF first.")
        if retriever is None:
            retriever = ContextRetriever(vector_store)
        rag_graph = RAGGraph(retriever)
    
    try:
        # Invoke RAG graph
        result = rag_graph.invoke(request.question)
        
        return ChatResponse(
            answer=result.get("answer", "Error generating answer"),
            visualization=result.get("visualization")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "vector_store_initialized": vector_store is not None}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG PDF Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload_pdf",
            "chat": "POST /chat",
            "health": "GET /health"
        }
    }

