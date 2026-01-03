"""
FastAPI routes for enterprise RAG chatbot.

Integrates:
- High-performance document ingestion
- RAG retrieval with memory
- Visualization pipeline
- Standardized API responses
- Performance monitoring and caching
"""
import os
import asyncio
import logging
import time
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

from app.config.settings import settings
from app.rag.rag_system import get_rag_system, initialize_rag_system
from app.rag.pdf_loader import PDFLoader
from app.rag.memory import clear_memory
from app.database.conversations import ConversationStorage

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
    visualization: Optional[dict] = None  # Frontend-compatible visualization format
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


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class CreateConversationRequest(BaseModel):
    """Create conversation request model."""
    title: Optional[str] = None


# Global conversation storage
conversation_storage = None


def get_conversation_storage() -> ConversationStorage:
    """Get conversation storage instance (lazy loaded)."""
    global conversation_storage
    if conversation_storage is None:
        conversation_storage = ConversationStorage()
    return conversation_storage


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
@app.post("/upload_pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file with comprehensive timing.
    
    CRITICAL: Clears all previous documents before adding new PDF
    to prevent cross-contamination between different uploads.
    
    Args:
        file: PDF file upload
        
    Returns:
        Upload response with processing details and performance metrics
    """
    import time
    upload_start = time.time()
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    temp_path = f"./temp_{file.filename}"
    
    try:
        # ============================================================
        # CRITICAL FIX: Clear all previous documents before new upload
        # This prevents summaries/answers from different PDFs bleeding
        # ============================================================
        clear_start = time.time()
        rag_system = get_rag_system()
        try:
            rag_system.reset()  # Clear vector store AND memory
            clear_time = time.time() - clear_start
            logger.info(f"🗑️  Cleared previous documents: {clear_time:.3f}s")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear previous documents: {e}")
            # Continue anyway - don't fail the upload
        
        # Save file
        save_start = time.time()
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        save_time = time.time() - save_start
        
        logger.info(f"📄 Processing PDF: {file.filename} ({len(content)/1024/1024:.2f} MB) | Save: {save_time:.3f}s")
        
        # Load PDF
        load_start = time.time()
        pdf_loader = PDFLoader()
        pdf_data = pdf_loader.load_pdf(temp_path)
        load_time = time.time() - load_start
        
        if not pdf_data or not pdf_data.get("pages"):
            raise HTTPException(status_code=400, detail="PDF is empty or cannot be read")
        
        pages = pdf_data.get("pages", [])
        total_pages = pdf_data.get("total_pages", len(pages))
        logger.info(f"   ✅ PDF loaded: {load_time:.3f}s | {total_pages} pages")
        
        # Get RAG system and ingest (will be fresh after reset)
        rag_system = get_rag_system()
        rag_system.initialize()  # Reinitialize after reset
        
        # Generate document ID
        import uuid
        document_id = str(uuid.uuid4())
        
        # Ingest document asynchronously
        ingest_start = time.time()
        result = await rag_system.ingest_document_async(
            document_id=document_id,
            pages=pages,
            filename=file.filename
        )
        ingest_time = time.time() - ingest_start
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Document ingestion failed: {result.get('error')}"
            )
        
        chunks_processed = result.get("chunks_processed", 0)
        documents_indexed = result.get("documents_indexed", 0)
        
        total_time = time.time() - upload_start
        logger.info(f"✅ PDF processing complete: {total_time:.3f}s total")
        logger.info(f"   • Pages: {total_pages} | Chunks: {chunks_processed} | Indexed: {documents_indexed}")
        logger.info(f"   • Timeline: Save={save_time:.3f}s | Load={load_time:.3f}s | Ingest={ingest_time:.3f}s")
        
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
        logger.error(f"❌ Error processing PDF: {e}", exc_info=True)
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
    import time
    start_time = time.time()
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # ============================================================
    # CRITICAL: RESPONSE GUARD - Detect explicit summary requests
    # ============================================================
    question_lower = request.question.lower().strip()
    explicit_summary_keywords = [
        "summarize", "summary", "summarise", "overview", "overview of the document",
        "give me a summary", "provide a summary", "create a summary", "make a summary",
        "high-level summary", "executive summary", "document summary",
        "what is in this document", "what does this document contain",
        "introduce the document", "introduction to the document",
        "get the summary", "tell me the summary", "explain this document"
    ]
    
    is_explicit_summary_request = any(kw in question_lower for kw in explicit_summary_keywords)
    logger.info(f"🔍 RESPONSE GUARD: Explicit summary request = {is_explicit_summary_request}")
    logger.info(f"   Question: {request.question}")
    
    # ============================================================
    # FAST-PATH: Check if this is a Finance Agent FAQ question
    # ============================================================
    faq_questions = {
        "summarize the overall financial performance of the company in 1-2 sentences.": "FAQ",
        "what was the revenue change compared to the previous period? (brief)": "FAQ",
        "list key profitability metrics (net profit, operating margin, ebitda) in one line each.": "FAQ",
        "what are the top 3 cost components impacting financial performance?": "FAQ",
        "briefly summarize cash flow from operations, investing, and financing.": "FAQ",
        "what is the current debt position? (summary)": "FAQ",
        "what are the 2-3 main financial risks highlighted?": "FAQ",
        "which business segment or region performed best? (brief)": "FAQ",
        "is there forward-looking guidance provided? (yes/no + brief outlook)": "FAQ",
        "what is the key financial takeaway for investors in 1 sentence?": "FAQ",
    }
    
    # Check if question matches an FAQ (for fast response path)
    is_faq_question = question_lower in [q.lower() for q in faq_questions.keys()]
    if is_faq_question:
        logger.info(f"⚡ FAST-PATH: Detected FAQ question - using optimized pipeline")
    
    try:
        # Get RAG system
        rag_system = get_rag_system()
        
        # Process question
        retrieval_start = time.time()
        result = rag_system.answer_question(
            question=request.question,
            use_memory=True
        )
        total_time = time.time() - start_time
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process question: {result.get('error')}"
            )
        
        response = result.get("response", {})
        
        logger.info(f"⏱️ PERFORMANCE: Total latency = {total_time:.2f}s")
        
        # ============================================================
        # CRITICAL: VALIDATE RESPONSE - No unsolicited summaries
        # ============================================================
        answer_text = response.get("answer", "").strip()
        
        # Check if answer looks like an unsolicited summary/overview
        summary_indicators = [
            answer_text.lower().startswith("this document"),
            answer_text.lower().startswith("the document"),
            answer_text.lower().startswith("based on the document"),
            answer_text.lower().startswith("the uploaded document"),
            "document overview" in answer_text.lower(),
            "document summary" in answer_text.lower(),
            "contains the following" in answer_text.lower() and not is_explicit_summary_request,
            "includes information about" in answer_text.lower() and len(answer_text) > 500 and not is_explicit_summary_request,
        ]
        
        is_unsolicited_summary = any(summary_indicators) and not is_explicit_summary_request
        
        if is_unsolicited_summary:
            logger.error(f"❌ RESPONSE GUARD TRIGGERED: Unsolicited summary detected!")
            logger.error(f"   Answer started with summary pattern, but user did NOT ask for summary")
            logger.error(f"   Blocking response and returning user prompt instruction")
            
            return ChatResponse(
                answer="Please ask a specific question about the document.",
                chart=None,
                visualization=None,
                table=None,
                chat_history=response.get("chat_history"),
                conversation_id=request.conversation_id
            )
        
        logger.info(f"✅ Chat response validated: {response.get('answer')[:100]}...")
        logger.info(f"📊 Chart data: {response.get('chart')}")
        logger.info(f"📋 Table data: {response.get('table')}")
        logger.info(f"📈 Visualization data: {response.get('visualization')}")
        
        # ============================================================
        # GLOBAL CHART INTENT DETECTION - MUST BE FIRST
        # ============================================================
        question_lower = request.question.lower()
        is_chart_request = any(kw in question_lower for kw in [
            'chart', 'charts', 'graph', 'graphs', 'visualize', 'visualization', 'visualizations',
            'visualise', 'show chart', 'display chart', 'give me chart', 'give me charts',
            'generate chart', 'create chart', 'plot', 'plotting', 'show charts'
        ])
        
        logger.info(f"🎯 GLOBAL CHART INTENT DETECTION: is_chart_request = {is_chart_request}")
        
        # ============================================================
        # IMMEDIATE ERROR CHECK - Before any other processing
        # ============================================================
        # Check if visualization already has an error from RAG system
        raw_viz = response.get("visualization")
        if raw_viz and isinstance(raw_viz, dict) and "error" in raw_viz:
            error_msg = raw_viz.get("error", "No structured numerical data available to generate a chart.")
            logger.error(f"❌ IMMEDIATE ERROR CHECK: visualization has error: {error_msg}")
            return ChatResponse(
                answer=error_msg,
                chart=None,
                visualization=None,
                table=None,
                chat_history=response.get("chat_history"),
                conversation_id=request.conversation_id
            )
        
        # ============================================================
        # IMMEDIATE TABLE BLOCK - If chart requested and visualization is table
        # ============================================================
        if is_chart_request and raw_viz and isinstance(raw_viz, dict):
            viz_type = raw_viz.get("chart_type") or raw_viz.get("type")
            has_headers_rows = raw_viz.get("headers") and raw_viz.get("rows")
            
            if viz_type == "table" or (has_headers_rows and not raw_viz.get("labels")):
                logger.error(f"❌ IMMEDIATE TABLE BLOCK: Chart requested but visualization is table - BLOCKED")
                return ChatResponse(
                    answer="No structured numerical data available to generate a chart.",
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
        
        # CRITICAL: If chart requested but no chart/table, try to extract and CONVERT to chart
        if not response.get("chart") and not response.get("table"):
            answer_text = response.get("answer", "")
            if "table" in answer_text.lower() or "trial balance" in answer_text.lower():
                logger.info("🔍 Detected table mention but no chart data - attempting extraction...")
                # Try to extract table from context if available
                try:
                    # Get the context that was used
                    context = result.get("response", {}).get("metadata", {}).get("context", "")
                    if context:
                        # Look for table patterns in context
                        import re
                        # Pattern for table with Account | Debit | Credit
                        table_pattern = r'(Account|Item|Description)[\s\|]*(Debit|Credit|Amount|Value)'
                        if re.search(table_pattern, context, re.IGNORECASE):
                            logger.info("✅ Found table pattern in context - extracting...")
                            # Extract table data from context
                            lines = context.split('\n')
                            headers = []
                            rows = []
                            in_table = False
                            
                            for line in lines:
                                # Look for header row
                                if 'Account' in line and ('Debit' in line or 'Credit' in line):
                                    # Extract headers
                                    parts = re.split(r'\s{2,}|\t|\|', line.strip())
                                    headers = [p.strip() for p in parts if p.strip()]
                                    in_table = True
                                    continue
                                
                                if in_table and headers:
                                    # Extract data rows
                                    parts = re.split(r'\s{2,}|\t|\|', line.strip())
                                    if len(parts) >= len(headers):
                                        row = [p.strip() for p in parts[:len(headers)]]
                                        if any(cell and cell != '-' for cell in row):
                                            rows.append(row)
                            
                            if headers and rows:
                                logger.info(f"✅ Extracted table: {len(headers)} columns, {len(rows)} rows")
                                
                                # ============================================================
                                # CRITICAL: IF CHART REQUESTED, CONVERT TABLE TO CHART
                                # ============================================================
                                if is_chart_request:
                                    logger.info("🔄 CHART REQUESTED - Converting table to chart...")
                                    # Extract account names and values for chart
                                    labels = []
                                    values = []
                                    
                                    # Find which columns are account names and which are numeric
                                    account_col = 0
                                    value_col = 1  # Default to first numeric column
                                    
                                    # Try to find Debit or Credit column
                                    for idx, header in enumerate(headers):
                                        header_lower = header.lower()
                                        if 'debit' in header_lower or 'credit' in header_lower or 'amount' in header_lower or 'value' in header_lower:
                                            value_col = idx
                                            break
                                    
                                    for row in rows:
                                        if len(row) > max(account_col, value_col):
                                            account_name = str(row[account_col]).strip()
                                            # Skip totals and empty rows
                                            if account_name.lower() in ['total', 'sum', '-', ''] or 'total' in account_name.lower():
                                                continue
                                            
                                            # Extract numeric value
                                            value_str = str(row[value_col]).replace(',', '').replace('$', '').replace('₹', '').strip()
                                            try:
                                                value = float(re.sub(r'[^\d.]', '', value_str)) if value_str and value_str != '-' else 0
                                            except:
                                                value = 0
                                            
                                            if account_name and value > 0:
                                                labels.append(account_name)
                                                values.append(value)
                                    
                                    if len(labels) >= 2 and len(values) >= 2:
                                        logger.info(f"✅ CONVERTED TO CHART: {len(labels)} data points")
                                        response["chart"] = {
                                            "type": "bar",
                                            "labels": labels,
                                            "values": values,
                                            "title": "Trial Balance",
                                            "xAxis": "Account",
                                            "yAxis": "Amount"
                                        }
                                    else:
                                        logger.warning(f"⚠️ Not enough data for chart: {len(labels)} labels, {len(values)} values")
                                        # Don't create table - return error instead
                                        response["chart"] = None
                                else:
                                    # NOT a chart request - OK to create table
                                    response["chart"] = {
                                        "type": "table",
                                        "headers": headers,
                                        "rows": rows,
                                        "title": "Trial Balance"
                                    }
                except Exception as extract_error:
                    logger.warning(f"Table extraction failed: {extract_error}")
        
        # Get conversation storage for storing message
        conv_storage = get_conversation_storage()
        
        # Store message if conversation_id provided
        if request.conversation_id:
            try:
                conv_storage.add_message(
                    conversation_id=request.conversation_id,
                    role="user",
                    content=request.question
                )
                conv_storage.add_message(
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=response.get("answer", "")
                )
            except Exception as e:
                logger.warning(f"Could not store conversation message: {e}")
        
        # CRITICAL: Check if visualization pipeline returned an error
        viz_result = result.get("response", {}).get("metadata", {}).get("viz_result")
        if viz_result and isinstance(viz_result, dict) and "error" in viz_result:
            error_msg = viz_result.get("error", "No structured financial data available to generate a chart.")
            logger.error(f"❌ Visualization error: {error_msg}")
            return ChatResponse(
                answer=error_msg,
                chart=None,
                visualization=None,
                table=None,
                chat_history=response.get("chat_history"),
                conversation_id=request.conversation_id
            )
        
        # Map chart to visualization for frontend compatibility
        chart_data = response.get("chart")
        visualization = None
        
        # CRITICAL: Check if visualization field already exists (from graph.py or other sources)
        if response.get("visualization"):
            viz_data = response.get("visualization")
            # Filter out error objects
            if isinstance(viz_data, dict) and "error" in viz_data:
                error_msg = viz_data.get("error", "No structured financial data available to generate a chart.")
                logger.error(f"❌ Visualization error: {error_msg}")
                return ChatResponse(
                    answer=error_msg,
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
            # ============================================================
            # CRITICAL EARLY BLOCK: If chart requested and viz_data is table, BLOCK NOW
            # ============================================================
            elif is_chart_request and isinstance(viz_data, dict):
                viz_chart_type = viz_data.get("chart_type") or viz_data.get("type")
                if viz_chart_type == "table":
                    logger.error(f"❌ EARLY BLOCK: response.visualization is table when chart requested - BLOCKED")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                # Check for headers/rows without labels/values (hidden table)
                elif viz_data.get("headers") and viz_data.get("rows") and not viz_data.get("labels"):
                    logger.error(f"❌ EARLY BLOCK: response.visualization has headers/rows but no labels - BLOCKED")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                else:
                    # Normalize table if it's a table
                    if viz_data.get("chart_type") == "table" or viz_data.get("type") == "table":
                        from app.rag.table_normalizer import TableNormalizer
                        viz_data = TableNormalizer.normalize_table_data(viz_data)
                    visualization = viz_data
            else:
                visualization = viz_data
        
        # If no visualization from response, try to build from chart
        if not visualization and chart_data:
            # CRITICAL: Filter out error objects in chart_data too
            if isinstance(chart_data, dict) and "error" in chart_data:
                error_msg = chart_data.get("error", "No structured financial data available to generate a chart.")
                logger.error(f"❌ Chart error: {error_msg}")
                return ChatResponse(
                    answer=error_msg,
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
            elif chart_data and chart_data.get("type") == "table":
                # CRITICAL: NEVER return table when chart requested (use global is_chart_request)
                if is_chart_request:
                    logger.error("❌ CRITICAL: Table returned when chart requested - BLOCKED")
                    return ChatResponse(
                        answer="No structured financial data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                # Normalize table structure before returning
                from app.rag.table_normalizer import TableNormalizer
                normalized_table = TableNormalizer.normalize_table(
                    chart_data.get("headers", []),
                    chart_data.get("rows", []),
                    chart_data.get("title")
                )
                # Only return table if NOT a chart request
                visualization = {
                    "chart_type": "table",
                    "type": "table",
                    "headers": normalized_table["headers"],
                    "rows": normalized_table["rows"],
                    "title": normalized_table["title"],
                    "markdown": response.get("table")
                }
            elif chart_data and chart_data.get("labels") and chart_data.get("values"):
                # Valid chart data
                visualization = {
                    "chart_type": chart_data.get("type", "bar"),
                    "type": chart_data.get("type", "bar"),
                    "title": chart_data.get("title", ""),
                    "labels": chart_data.get("labels", []),
                    "values": chart_data.get("values", []),
                    "xAxis": chart_data.get("xAxis"),
                    "yAxis": chart_data.get("yAxis")
                }
        
        # CRITICAL: Use global is_chart_request (already defined at top)
        # Chart intent already detected above - no need to redefine
        
        if is_chart_request and not visualization:
            logger.error("❌ Chart requested but no visualization generated - attempting fallback extraction")
            
            # CRITICAL FALLBACK: Try to extract chart data from answer text and metadata context
            try:
                answer_text = response.get("answer", "")
                context_text = result.get("response", {}).get("metadata", {}).get("context", "") if result else ""
                
                # First try answer text
                if answer_text:
                    logger.info(f"🔄 Attempting to extract chart data from answer text: {answer_text[:200]}...")
                    
                    # Try to parse key-value pairs from answer
                    import re
                    
                    # Pattern 1: "Item: Value" or "Item = Value"
                    pattern1 = r'([A-Za-z\s]+)[\:\=]\s*([\d,\.]+)'
                    matches = re.findall(pattern1, answer_text)
                    
                    if matches and len(matches) >= 2:
                        logger.info(f"✅ FALLBACK: Extracted {len(matches)} key-value pairs from answer")
                        labels = [m[0].strip() for m in matches if m[0].strip()]
                        values = []
                        for m in matches:
                            try:
                                val = float(m[1].replace(',', ''))
                                values.append(val)
                            except:
                                pass
                        
                        if len(labels) >= 2 and len(values) >= 2 and len(labels) == len(values):
                            visualization = {
                                "chart_type": "bar",
                                "type": "bar",
                                "title": "Financial Data",
                                "labels": labels,
                                "values": values,
                                "xAxis": "Category",
                                "yAxis": "Value"
                            }
                            logger.info(f"✅ Successfully created fallback chart from answer text")
                
                # If answer extraction failed, try context
                if not visualization and context_text:
                    logger.info(f"🔄 Answer extraction failed, attempting to extract from context...")
                    
                    # Look for financial data in context
                    pattern2 = r'\n\s*([A-Za-z\s\-]+?)\s*[\:\-]?\s*([\d,\.]+)'
                    matches = re.findall(pattern2, context_text)
                    
                    if matches and len(matches) >= 2:
                        logger.info(f"✅ FALLBACK: Extracted {len(matches)} data points from context")
                        labels = []
                        values = []
                        for label, val_str in matches:
                            label = label.strip().rstrip('-:')
                            if len(label) > 2 and not label.lower().startswith('page'):
                                try:
                                    val = float(val_str.replace(',', ''))
                                    labels.append(label)
                                    values.append(val)
                                except:
                                    pass
                        
                        if len(labels) >= 2 and len(values) >= 2:
                            visualization = {
                                "chart_type": "bar",
                                "type": "bar",
                                "title": "Financial Data",
                                "labels": labels[:20],  # Limit to 20 points
                                "values": values[:20],
                                "xAxis": "Category",
                                "yAxis": "Value"
                            }
                            logger.info(f"✅ Successfully created fallback chart from context")
                else:
                    logger.warning(f"⚠️ No context or extraction patterns matched")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback extraction failed: {fallback_error}", exc_info=True)
            
            # If still no visualization, return error
            if not visualization:
                logger.error("❌ All chart generation methods failed")
                return ChatResponse(
                    answer="No structured financial data available to generate a chart.",
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
        
        # CRITICAL: Final check - if chart requested, ensure visualization is NOT a table
        if is_chart_request and visualization:
            if visualization.get("chart_type") == "table" or visualization.get("type") == "table":
                logger.error("❌ CRITICAL: Visualization is table when chart requested - BLOCKED")
                return ChatResponse(
                    answer="No structured financial data available to generate a chart.",
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
        
        # ============================================================
        # FINAL API RESPONSE GUARD - ABSOLUTE BLOCK ON TABLES
        # ============================================================
        # This is the LAST check before returning response
        # NO EXCEPTIONS - NO TABLES when chart requested
        # ENTERPRISE SCOPE: Applies to ALL financial documents
        if is_chart_request:
            logger.info(f"🔒 FINAL GUARD: Chart requested detected - enforcing strict contract")
            
            # Check if visualization is a table in ANY form
            is_table_visualization = False
            table_reason = None
            
            if visualization:
                # Check 1: chart_type = "table"
                if visualization.get("chart_type") == "table":
                    is_table_visualization = True
                    table_reason = "chart_type = 'table'"
                    logger.error(f"❌ FINAL GUARD: {table_reason} - BLOCKED")
                
                # Check 2: type = "table"
                if visualization.get("type") == "table":
                    is_table_visualization = True
                    table_reason = "type = 'table'"
                    logger.error(f"❌ FINAL GUARD: {table_reason} - BLOCKED")
                
                # Check 3: markdown tables (ANY markdown with table syntax)
                if visualization.get("markdown"):
                    markdown_str = str(visualization.get("markdown"))
                    if "|" in markdown_str and ("---" in markdown_str or len(markdown_str.split("\n")) > 2):
                        is_table_visualization = True
                        table_reason = "markdown table detected"
                        logger.error(f"❌ FINAL GUARD: {table_reason} - BLOCKED")
                
                # Check 4: headers/rows structure (ALWAYS block when chart requested)
                # CRITICAL: Block headers/rows even if not explicitly marked as table type
                if visualization.get("headers") and visualization.get("rows"):
                    # If it has headers/rows but NO valid chart data, it's a table
                    if not visualization.get("labels") or not visualization.get("values"):
                        is_table_visualization = True
                        table_reason = "headers/rows structure without chart data"
                        logger.error(f"❌ FINAL GUARD: {table_reason} - BLOCKED")
                    # Also block if explicitly marked as table
                    elif visualization.get("chart_type") == "table" or visualization.get("type") == "table":
                        is_table_visualization = True
                        table_reason = "headers/rows with table type"
                        logger.error(f"❌ FINAL GUARD: {table_reason} - BLOCKED")
            
            # If table detected, DISCARD visualization completely
            if is_table_visualization:
                logger.error(f"❌ FINAL GUARD: DISCARDING table visualization (reason: {table_reason}) - returning error")
                return ChatResponse(
                    answer="No structured numerical data available to generate a chart.",
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
            
            # Final validation: Ensure visualization is a valid chart type
            if visualization:
                valid_chart_types = ["bar", "line", "pie", "stacked_bar"]
                chart_type = visualization.get("chart_type") or visualization.get("type")
                
                if not chart_type or chart_type not in valid_chart_types:
                    logger.error(f"❌ FINAL GUARD: Invalid or missing chart_type '{chart_type}' - must be one of {valid_chart_types}")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                
                # Ensure chart has required fields (labels and values)
                labels = visualization.get("labels")
                values = visualization.get("values")
                
                if not labels or not isinstance(labels, list) or len(labels) < 2:
                    logger.error(f"❌ FINAL GUARD: Chart missing or invalid labels: {labels}")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                
                if not values or not isinstance(values, list) or len(values) < 2:
                    logger.error(f"❌ FINAL GUARD: Chart missing or invalid values: {values}")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                
                if len(labels) != len(values):
                    logger.error(f"❌ FINAL GUARD: Labels/values length mismatch: {len(labels)} vs {len(values)}")
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
                
                logger.info(f"✅ FINAL GUARD: Valid chart confirmed - type: {chart_type}, labels: {len(labels)}, values: {len(values)}")
            else:
                # No visualization at all when chart requested
                logger.error("❌ FINAL GUARD: Chart requested but no visualization provided")
                return ChatResponse(
                    answer="No structured numerical data available to generate a chart.",
                    chart=None,
                    visualization=None,
                    table=None,
                    chat_history=response.get("chat_history"),
                    conversation_id=request.conversation_id
                )
        
        # ============================================================
        # CRITICAL: Remove errors from valid table/chart data
        # ============================================================
        # Initialize final_visualization to avoid UnboundLocalError
        if not visualization:
            final_visualization = None
        else:
            final_visualization = visualization
        
        if final_visualization and isinstance(final_visualization, dict):
            has_chart = final_visualization.get("labels") and final_visualization.get("values")
            has_table = final_visualization.get("headers") and final_visualization.get("rows")
            
            # If we have valid table/chart data, remove any error
            if has_table or has_chart:
                if "error" in final_visualization:
                    logger.warning("⚠️ Removing error from final_visualization - valid table/chart data exists")
                    final_visualization.pop("error", None)
        
        # ============================================================
        # FINAL SANITIZATION - ABSOLUTE LAST CHECK BEFORE RETURN
        # ============================================================
        # This is the FINAL boundary - no table can pass through
        final_chart_data = None
        if not final_visualization:
            final_visualization = visualization
        final_table = None
        
        if is_chart_request:
            # CRITICAL: Remove ANY table data from chart_data
            if chart_data:
                if chart_data.get("type") == "table" or chart_data.get("chart_type") == "table":
                    logger.error("❌ FINAL SANITIZATION: Discarding table chart_data")
                    final_chart_data = None
                elif "error" not in chart_data:
                    final_chart_data = chart_data
            
            # CRITICAL: Final check on visualization (should have passed guard above, but double-check)
            if final_visualization:
                if (final_visualization.get("chart_type") == "table" or 
                    final_visualization.get("type") == "table" or
                    (final_visualization.get("headers") and final_visualization.get("rows") and 
                     not final_visualization.get("labels") and not final_visualization.get("values"))):
                    logger.error("❌ FINAL SANITIZATION: Discarding table visualization (should not reach here)")
                    final_visualization = None
                    # If we reach here, something went wrong - return error
                    return ChatResponse(
                        answer="No structured numerical data available to generate a chart.",
                        chart=None,
                        visualization=None,
                        table=None,
                        chat_history=response.get("chat_history"),
                        conversation_id=request.conversation_id
                    )
            
            # NEVER return table when chart requested
            final_table = None
        else:
            # Not a chart request - allow table
            if chart_data and "error" not in chart_data:
                if chart_data.get("type") != "table" and chart_data.get("chart_type") != "table":
                    final_chart_data = chart_data
            final_table = response.get("table")
        
        # ============================================================
        # FINAL RESPONSE - ABSOLUTE BOUNDARY
        # ============================================================
        logger.info(f"📤 FINAL RESPONSE: chart_requested={is_chart_request}, has_visualization={bool(final_visualization)}, has_chart={bool(final_chart_data)}")
        
        # CRITICAL: Fix answer if we have a valid chart or table but answer says "Not available"
        final_answer = response.get("answer", "")
        question_lower = request.question.lower()
        is_table_request = ("table" in question_lower or "tabular" in question_lower) and not is_chart_request
        
        if final_visualization and isinstance(final_visualization, dict):
            # Check if it's a table (has headers/rows, no labels/values, or chart_type is "table")
            viz_type = final_visualization.get("chart_type") or final_visualization.get("type")
            has_table_structure = (final_visualization.get("headers") and final_visualization.get("rows") and 
                                  not final_visualization.get("labels") and not final_visualization.get("values"))
            is_table_type = viz_type == "table"
            has_table = has_table_structure or is_table_type
            
            # Check if it's a chart (has labels/values)
            has_chart = final_visualization.get("labels") and final_visualization.get("values")
            
            # PRIORITY: Check chart request first - NEVER set table message if chart requested
            if is_chart_request:
                if has_table:
                    # Chart requested but we have table - this should have been blocked, but ensure error message
                    logger.error("❌ CRITICAL: Chart requested but table detected in final answer fix - should not happen")
                    final_answer = "No structured numerical data available to generate a chart."
                elif has_chart:
                    # We have a chart - use chart message
                    if "not available" in final_answer.lower() or final_answer.strip() == "" or not final_answer:
                        final_answer = "Here is the visualization based on the document data."
                        logger.info("📤 Fixed answer: replaced 'Not available' with chart description")
            else:
                # Not a chart request - check table first (more specific)
                if has_table:
                    # We have a table - ALWAYS replace "Not available" message
                    if "not available" in final_answer.lower() or final_answer.strip() == "" or not final_answer:
                        final_answer = "The requested table is shown below."
                        logger.info("📤 Fixed answer: replaced 'Not available' with table message")
                elif has_chart:
                    # We have a chart - use chart message
                    if "not available" in final_answer.lower() or final_answer.strip() == "" or not final_answer:
                        final_answer = "Here is the visualization based on the document data."
                        logger.info("📤 Fixed answer: replaced 'Not available' with chart description")
        
        return ChatResponse(
            answer=final_answer,
            chart=final_chart_data,
            visualization=final_visualization,
            table=final_table,  # Always None if chart requested
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


# Conversation endpoints (preserved for backward compatibility)
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
        conv_storage = get_conversation_storage()
        conversation = conv_storage.create_conversation(title=request.title)
        
        return ConversationResponse(
            id=conversation["id"],
            title=conversation["title"],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            message_count=0
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")


@app.get("/conversations")
async def list_conversations():
    """
    List all conversations.
    
    Returns:
        List of conversations
    """
    try:
        conv_storage = get_conversation_storage()
        conversations = conv_storage.list_conversations()
        
        return {
            "conversations": [
                ConversationResponse(
                    id=c["id"],
                    title=c["title"],
                    created_at=c["created_at"],
                    updated_at=c["updated_at"],
                    message_count=c.get("message_count", 0)
                ).model_dump() for c in conversations
            ]
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation details.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Conversation details with messages
    """
    try:
        conv_storage = get_conversation_storage()
        conversation = conv_storage.get_conversation(conversation_id)
        
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
        conv_storage = get_conversation_storage()
        deleted = conv_storage.delete_conversation(conversation_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


@app.get("/stats")
async def get_stats():
    """
    Get performance statistics and cache metrics.
    
    Returns:
        Statistics including latency, cache hit rates, and system metrics
    """
    try:
        from app.rag.cache_manager import get_cache_manager
        from app.rag.embeddings import OpenAIEmbeddingsWrapper
        
        cache_manager = get_cache_manager()
        embeddings = OpenAIEmbeddingsWrapper()
        
        return {
            "status": "operational",
            "cache_metrics": cache_manager.get_stats(),
            "embedding_model": {
                "model": "text-embedding-3-small",
                "dimension": 1536,
                "batching": True,
                "batch_size": 50
            },
            "retrieval": {
                "default_k": 4,
                "max_k": 6,
                "confidence_threshold": 0.6,
                "caching_enabled": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"error": str(e), "status": "error"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Enterprise RAG Chatbot API",
        "version": "2.0.0",
        "endpoints": {
            "upload": "POST /upload_pdf",
            "chat": "POST /chat",
            "clear_memory": "DELETE /clear_memory",
            "remove_file": "DELETE /remove_file",
            "status": "GET /status",
            "health": "GET /health",
            "create_conversation": "POST /conversations",
            "list_conversations": "GET /conversations",
            "get_conversation": "GET /conversations/{id}",
            "delete_conversation": "DELETE /conversations/{id}"
        }
    }
    """
    Upload and process a PDF file.
    
    Args:
        file: PDF file upload
        
    Returns:
        Success message with processing details
    """

