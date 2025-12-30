"""
Streamlit dashboard for PDF Chatbot.
Provides a user-friendly interface for uploading PDFs and chatting with them.
"""
import streamlit as st
import os
import sys
import tempfile
import time
from typing import Optional, Dict, List
import base64
from PIL import Image
import io
import logging
import pandas as pd

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load .env file directly as fallback
try:
    from dotenv import load_dotenv
    # Try multiple .env locations
    env_paths = [
        os.path.join(parent_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        ".env"
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            break
except ImportError:
    # python-dotenv not installed, that's OK - pydantic-settings will handle it
    pass
except Exception as e:
    logging.warning(f"Could not load .env file: {e}")

# Import RAG components
from app.rag.pdf_loader import PDFLoader
from app.rag.chunker import TextChunker
from app.rag.vector_store import VectorStore
from app.rag.retriever import ContextRetriever
from app.rag.graph import RAGGraph
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "retriever" not in st.session_state:
        st.session_state.retriever = None
    if "rag_graph" not in st.session_state:
        st.session_state.rag_graph = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pdf_uploaded" not in st.session_state:
        st.session_state.pdf_uploaded = False
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = None


def initialize_rag_components():
    """Initialize RAG components if not already initialized."""
    try:
        if st.session_state.vector_store is None:
            with st.spinner("Initializing vector store..."):
                st.session_state.vector_store = VectorStore()
                st.session_state.retriever = ContextRetriever(st.session_state.vector_store)
                st.session_state.rag_graph = RAGGraph(st.session_state.retriever)
        return True
    except ValueError as e:
        # API key validation errors
        error_msg = str(e)
        if "API key" in error_msg or "OPENAI_API_KEY" in error_msg:
            st.error("🔑 **API Key Error**")
            st.error(error_msg)
            st.info("💡 **How to fix:**\n1. Create a `.env` file in the project root\n2. Add: `OPENAI_API_KEY=your_actual_api_key`\n3. Get your API key from: https://platform.openai.com/api-keys")
        else:
            st.error(f"Error initializing RAG components: {e}")
        logger.error(f"Error initializing RAG components: {e}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
            st.error("🔑 **Invalid API Key**")
            st.error("Your OpenAI API key is invalid or missing. Please check your `.env` file.")
            st.info("Get your API key from: https://platform.openai.com/api-keys")
        else:
            st.error(f"Error initializing RAG components: {e}")
        logger.error(f"Error initializing RAG components: {e}")
        return False


def process_pdf(uploaded_file) -> Dict:
    """
    Process uploaded PDF file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Dictionary with processing results
    """
    tmp_path = None
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Read file bytes
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return {"success": False, "error": "Uploaded file is empty"}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file.flush()  # Flush before context exits
            os.fsync(tmp_file.fileno())  # Ensure written to disk
            tmp_path = tmp_file.name
        # File is now closed and written to disk
        
        # Load PDF
        pdf_loader = PDFLoader()
        pdf_data = pdf_loader.load_pdf(tmp_path)
        
        if not pdf_data or not pdf_data.get("pages"):
            return {"success": False, "error": "PDF is empty or cannot be read"}
        
        # Run preprocessing pipeline (OCR, cleaning, structured data extraction)
        try:
            from app.rag.preprocessing_graph import PreprocessingGraph
            mistral_key = os.getenv("MISTRAL_API_KEY") or (settings.mistral_api_key if hasattr(settings, 'mistral_api_key') else None)
            preprocessing = PreprocessingGraph(mistral_api_key=mistral_key)
            processed_data = preprocessing.process(tmp_path, pdf_data)
            
            # Update pdf_data with processed results
            pdf_data["text"] = processed_data["text"]
            pdf_data["pages"] = processed_data["pages"]
            pdf_data["structured_data"] = processed_data.get("structured_data", [])
            
            if processed_data.get("error"):
                logger.warning(f"Preprocessing warning: {processed_data['error']}")
        except Exception as preprocess_error:
            logger.warning(f"Preprocessing failed, using original PDF data: {preprocess_error}")
            # Continue with original data if preprocessing fails
        
        # Check embedding availability before processing
        from app.rag.embedding_check import check_embedding_availability
        embedding_available, embedding_error = check_embedding_availability()
        
        if not embedding_available:
            return {
                "success": False,
                "error": embedding_error
            }
        
        # Initialize components if needed
        if not initialize_rag_components():
            return {"success": False, "error": "Failed to initialize RAG components"}
        
        # Chunk text with adaptive chunking for large documents
        chunk_size = settings.chunk_size
        chunk_overlap = settings.chunk_overlap
        max_chunks = getattr(settings, 'max_chunks_per_document', 500)
        large_doc_threshold = getattr(settings, 'large_document_threshold_pages', 50)
        enable_large = getattr(settings, 'enable_large_document_processing', True)
        
        # For very large documents, use adaptive chunking strategy (silently)
        if pdf_data["total_pages"] > large_doc_threshold:
            # Calculate optimal chunk size based on document size
            # Larger documents get smaller chunks to keep total chunk count manageable
            if pdf_data["total_pages"] > 200:
                chunk_size = min(chunk_size, 600)  # Very large docs: smaller chunks
            elif pdf_data["total_pages"] > 100:
                chunk_size = min(chunk_size, 700)  # Large docs: medium chunks
            else:
                chunk_size = min(chunk_size, 800)  # Medium-large docs
        
        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = chunker.chunk_pages(pdf_data["pages"])
        
        if not chunks:
            return {"success": False, "error": "No text chunks could be created"}
        
        # Handle chunk limits - process all chunks silently without warnings
        if len(chunks) > max_chunks:
            if not enable_large:
                # Truncate if large document processing is disabled
                chunks = chunks[:max_chunks]
        
        # Process silently without progress indicators - allow user to chat immediately
        # Progress bars and status messages removed for better UX
        
        # Clear old documents before adding new ones to avoid mixing documents
        try:
            logger.info("Clearing old documents from vector store...")
            st.session_state.vector_store.clear_all_documents()
            logger.info("Old documents cleared successfully")
        except Exception as clear_error:
            logger.warning(f"Could not clear old documents (this is OK if vector store is empty): {clear_error}")
            # Continue anyway - might be first upload
        
        # Add to vector store - process silently in background
        try:
            logger.info(f"Starting to add {len(chunks)} chunks to vector store")
            doc_ids = st.session_state.vector_store.add_documents(chunks)
            logger.info(f"Successfully added {len(doc_ids)} chunks to vector store")
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"ValueError processing PDF: {error_msg}")
            
            # Note: With local embeddings, this error should not occur
            # But keep for backward compatibility
            if "free tier" in error_msg.lower() or "limit: 0" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"❌ **Embedding Error**\n\n"
                            f"Local embeddings should work without API limits. This error is unexpected.\n\n"
                            f"**Solutions:**\n"
                            f"1. 🔄 **Restart the app** and try again\n"
                            f"2. 📦 **Check if sentence-transformers is installed**: `pip install sentence-transformers`\n"
                            f"3. 💻 **Check system resources** (memory/disk space)\n\n"
                            f"*Error: {error_msg[:300]}*"
                }
            # Check if it's a quota error
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"⚠️ **API Quota/Rate Limit Reached**\n\n"
                            f"The document has {len(chunks)} chunks which exceeded your API limits.\n\n"
                            f"**Solutions:**\n"
                            f"1. ⏳ **Wait 5-10 minutes** and try again (quota resets)\n"
                            f"2. 📄 **Try a smaller PDF** (fewer pages)\n"
                            f"3. 🔍 **Check your quota** at: https://platform.openai.com/usage\n"
                            f"4. 💡 **Split the PDF** into smaller files\n\n"
                            f"*Error details: {error_msg[:300]}*"
                }
            # Return error instead of raising for better UX
            return {"success": False, "error": f"Processing error: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error processing PDF: {e}", exc_info=True)
            return {"success": False, "error": f"Unexpected error: {error_msg}. Please check the console/logs for details."}
        
        return {
            "success": True,
            "pages": pdf_data["total_pages"],
            "chunks": len(chunks),
            "document_ids": len(doc_ids)
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"PDF processing error: {error_msg}")
        
        # Check for specific error types
        if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
            return {
                "success": False,
                "error": "Invalid OpenAI API key. Please check your .env file and ensure OPENAI_API_KEY is set correctly."
            }
        elif "400" in error_msg or "Bad Request" in error_msg:
            return {
                "success": False,
                "error": f"API request failed. The PDF might be too large or contain invalid content. Try:\n1. Using a smaller PDF\n2. Checking if the PDF has extractable text\n3. Waiting a moment and trying again\n\nDetails: {error_msg}"
            }
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            return {
                "success": False,
                "error": "API quota exceeded. Please wait a moment and try again, or check your OpenAI API quota."
            }
        
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        
        # Check for API key errors in exception message
        if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
            return {
                "success": False,
                "error": "Invalid or missing OpenAI API key. Please check your .env file. Get your API key from: https://platform.openai.com/api-keys"
            }
        elif "400" in error_msg or "Bad Request" in error_msg or "AxiosError" in error_msg:
            return {
                "success": False,
                "error": f"API request failed (400 error). This might be due to:\n1. PDF is too large or has too many pages\n2. Text chunks are too large\n3. API rate limits\n\nTry splitting the PDF into smaller files or wait a moment and try again.\n\nError: {error_msg}"
            }
        
        return {"success": False, "error": f"Unexpected error: {error_msg}"}
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                logger.warning(f"Could not delete temp file: {cleanup_error}")




def _fallback_data_extraction(response_text: str) -> Dict:
    """
    Fallback method to extract data when JSON parsing fails.
    Tries to find numbers and labels in the text.
    """
    import re
    
    try:
        # First, try to extract from JSON-like structure even if incomplete
        # Look for "values": [numbers] pattern
        values_match = re.search(r'"values"\s*:\s*\[([^\]]+)\]', response_text, re.DOTALL)
        labels_match = re.search(r'"labels"\s*:\s*\[([^\]]+)\]', response_text, re.DOTALL)
        
        if values_match and labels_match:
            values = []
            labels = []
            
            # Extract values
            values_str = values_match.group(1)
            for num_match in re.finditer(r'[\d,]+\.?\d*', values_str):
                try:
                    val = float(num_match.group().replace(',', ''))
                    values.append(val)
                except ValueError:
                    continue
            
            # Extract labels
            labels_str = labels_match.group(1)
            # Remove quotes and extract
            labels_clean = re.sub(r'["\']', '', labels_str)
            for label_match in re.finditer(r'([^,]+)', labels_clean):
                label = label_match.group(1).strip()
                if label and label not in ['[', ']', '{', '}']:
                    labels.append(label)
            
            # Match lengths and limit
            min_len = min(len(values), len(labels), 20)  # Max 20 items
            if min_len >= 2:
                return {
                    "data_type": "bar",
                    "values": values[:min_len],
                    "labels": labels[:min_len],
                    "title": "Extracted Data",
                    "x_axis": "Category",
                    "y_axis": "Value"
                }
        
        # Fallback: Try to find numbers and associated labels
        # Look for patterns like "Q1: $500,000" or "Region A: 100"
        patterns = [
            r'([A-Za-z0-9\s]+?):\s*\$?([\d,]+\.?\d*)',  # "Label: $number"
            r'([A-Za-z0-9\s]+?)\s+([\d,]+\.?\d*)%',      # "Label 50%"
            r'([A-Za-z0-9\s]+?)\s+([\d,]+\.?\d*)',       # "Label number"
        ]
        
        values = []
        labels = []
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                for match in matches[:20]:  # Limit to 20 matches
                    try:
                        label = match[0].strip()
                        value_str = match[1].replace(',', '').replace('$', '').replace('%', '')
                        value = float(value_str)
                        if label and value and label not in ['[', ']', '{', '}']:
                            labels.append(label)
                            values.append(value)
                    except (ValueError, IndexError):
                        continue
                
                if len(values) >= 2:  # Need at least 2 data points
                    return {
                        "data_type": "bar",
                        "values": values[:20],  # Limit to 20
                        "labels": labels[:20],
                        "title": "Extracted Data",
                        "x_axis": "Category",
                        "y_axis": "Value"
                    }
    except Exception as e:
        logger.debug(f"Fallback extraction failed: {e}")
    
    return {"error": "Could not extract data"}


# Visualization functions removed
def _extract_all_numerical_data_removed():
    """
    Extract all numerical data from the document for visualization.
    Returns lists of tables and charts.
    Uses direct text extraction first (most reliable), then LLM extraction.
    """
    if not st.session_state.retriever:
        logger.warning("No retriever available")
        return [], []
    
    # Initialize RAG graph if needed
    if not st.session_state.rag_graph:
        if not initialize_rag_components():
            logger.warning("Failed to initialize RAG components")
            return [], []
    
    try:
        # Get all chunks from vector store - use multiple queries to get comprehensive data
        all_chunks = []
        queries = [
            "numbers statistics data",
            "revenue sales financial",
            "percentage proportion",
            "table chart graph"
        ]
        
        seen_texts = set()
        for query in queries:
            try:
                chunks = st.session_state.retriever.retrieve(query, k=10)
                for chunk in chunks:
                    text = chunk.get("text", "")
                    if text and text not in seen_texts:
                        all_chunks.append(chunk)
                        seen_texts.add(text)
            except Exception as e:
                logger.debug(f"Query '{query}' failed: {e}")
                continue
        
        if not all_chunks:
            logger.warning("No chunks retrieved for visualization")
            return [], []
        
        logger.info(f"Retrieved {len(all_chunks)} unique chunks for visualization")
        
        # Combine all context (limit to avoid token issues)
        full_context = st.session_state.retriever.format_context(all_chunks[:30])  # Increased to 30 chunks
        
        from app.rag.visualization import VisualizationGenerator
        viz_gen = VisualizationGenerator()
        
        tables = []
        charts = []
        
        # METHOD 1: Try direct text extraction first (most reliable)
        logger.info("Attempting direct text extraction...")
        extracted_data = _extract_from_text_directly(full_context)
        
        if "error" not in extracted_data:
            values = extracted_data.get("values", [])
            labels = extracted_data.get("labels", [])
            logger.info(f"Direct extraction found {len(values)} data points")
            
            if values and labels and len(values) >= 2 and len(labels) >= 2:
                # Ensure arrays match
                min_len = min(len(values), len(labels), 20)
                extracted_data["values"] = values[:min_len]
                extracted_data["labels"] = labels[:min_len]
                
                logger.info(f"Attempting to generate chart with {min_len} data points...")
                logger.debug(f"Data sample - Values: {extracted_data['values'][:5]}, Labels: {extracted_data['labels'][:5]}")
                
                try:
                    chart = viz_gen.generate_chart(extracted_data)
                    
                    if chart is None:
                        logger.error("Chart generation returned None")
                    elif "error" in chart:
                        error_msg = chart.get("error", "Unknown error")
                        logger.warning(f"Chart generation returned error: {error_msg}")
                        logger.debug(f"Extracted data: {extracted_data}")
                    elif "image_base64" not in chart:
                        logger.error(f"Chart missing image_base64 field. Chart keys: {list(chart.keys())}")
                    else:
                        charts.append(chart)
                        logger.info(f"✅ Successfully generated chart from direct extraction ({min_len} points)")
                        logger.debug(f"Chart has {len(chart.get('image_base64', ''))} chars of base64 data")
                        
                except Exception as chart_error:
                    logger.error(f"Exception during chart generation: {chart_error}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"Direct extraction data validation failed: {len(values) if values else 0} values, {len(labels) if labels else 0} labels")
        else:
            logger.info(f"Direct extraction returned error: {extracted_data.get('error')}")
        
        # METHOD 2: If direct extraction didn't work, try LLM extraction
        if not charts:
            logger.info("Direct extraction didn't produce charts, trying LLM extraction...")
            try:
                simple_prompt = f"""Find and extract numerical data from this document. Look for:
- Numbers with labels (e.g., "Q1: 500", "Revenue: $1000")
- Percentages (e.g., "Market share: 25%")
- Counts and measurements
- Any data that can be visualized

Document content:
{full_context[:5000]}

Return ONLY valid JSON with this structure:
{{
    "data_type": "bar",
    "values": [numbers only, max 15 items],
    "labels": [what each number represents, max 15 items, must match values count],
    "title": "Document Data",
    "x_axis": "Category",
    "y_axis": "Value"
}}

CRITICAL: Return ONLY the JSON object. No markdown, no explanations, no other text."""
                
                response = st.session_state.rag_graph.llm.invoke(simple_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                logger.info(f"LLM response received ({len(response_text)} chars)")
                logger.debug(f"LLM response preview: {response_text[:300]}")
                
                # Parse extracted data
                extracted_data = viz_gen.parse_extracted_data(response_text)
                
                # If parsing failed, try fallback
                if "error" in extracted_data:
                    logger.info("LLM JSON parsing failed, trying fallback extraction...")
                    extracted_data = _fallback_data_extraction(response_text)
                
                # Validate and generate visualization
                if "error" not in extracted_data:
                    values = extracted_data.get("values", [])
                    labels = extracted_data.get("labels", [])
                    
                    logger.info(f"Extracted data: {len(values) if values else 0} values, {len(labels) if labels else 0} labels")
                    
                    if values and labels and len(values) >= 2 and len(labels) >= 2:
                        min_len = min(len(values), len(labels), 20)
                        extracted_data["values"] = values[:min_len]
                        extracted_data["labels"] = labels[:min_len]
                        
                        chart = viz_gen.generate_chart(extracted_data)
                        if "error" not in chart:
                            charts.append(chart)
                            logger.info(f"✅ Successfully generated chart from LLM extraction ({min_len} points)")
                        else:
                            logger.warning(f"Chart generation failed: {chart.get('error')}")
                    else:
                        logger.warning(f"Insufficient data after LLM extraction: {len(values) if values else 0} values, {len(labels) if labels else 0} labels")
                else:
                    logger.warning(f"LLM extraction returned error: {extracted_data.get('error')}")
            
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}", exc_info=True)
        
        # METHOD 3: If still no charts, try extracting from ALL chunks without filtering
        if not charts:
            logger.info("Trying extraction from all document chunks...")
            try:
                # Get all chunks without query filtering
                all_text = "\n".join([chunk.get("text", "") for chunk in all_chunks])
                extracted_data = _extract_from_text_directly(all_text)
                
                if "error" not in extracted_data:
                    values = extracted_data.get("values", [])
                    labels = extracted_data.get("labels", [])
                    
                    if values and labels and len(values) >= 2:
                        min_len = min(len(values), len(labels), 20)
                        extracted_data["values"] = values[:min_len]
                        extracted_data["labels"] = labels[:min_len]
                        
                        chart = viz_gen.generate_chart(extracted_data)
                        if "error" not in chart:
                            charts.append(chart)
                            logger.info(f"✅ Successfully generated chart from all chunks ({min_len} points)")
            except Exception as e:
                logger.error(f"Final extraction attempt failed: {e}")
        
        logger.info(f"Final result: {len(charts)} charts, {len(tables)} tables")
        return tables, charts
        
    except Exception as e:
        logger.error(f"Error extracting all numerical data: {e}", exc_info=True)
        return [], []


def _extract_from_text_directly(context_text: str) -> Dict:
    """
    Directly extract numerical data from text using regex patterns.
    More reliable than LLM extraction for simple cases.
    """
    import re
    
    if not context_text or len(context_text.strip()) < 10:
        return {"error": "Context text too short"}
    
    try:
        values = []
        labels = []
        seen_pairs = set()  # Track (label, value) pairs to avoid duplicates
        
        # Pattern 1: Find labeled numbers (e.g., "Q1: 500", "Revenue: $1000", "Page 5: 42")
        pattern1 = r'([A-Za-z][A-Za-z0-9\s]{0,40}?):\s*\$?([\d,]+\.?\d*)'
        matches1 = re.findall(pattern1, context_text, re.IGNORECASE)
        
        # Pattern 2: Find numbers with labels before them (e.g., "Revenue 500", "Sales $1000")
        pattern2 = r'([A-Za-z][A-Za-z0-9\s]{1,30})\s+([\d,]+\.?\d*)\s*(?:dollars?|USD|\$|percent|%)?'
        matches2 = re.findall(pattern2, context_text, re.IGNORECASE)
        
        # Pattern 3: Find percentages (e.g., "Market share 25%", "Growth 15%")
        pattern3 = r'([A-Za-z][A-Za-z0-9\s]{1,30}?)\s+([\d,]+\.?\d*)%'
        matches3 = re.findall(pattern3, context_text, re.IGNORECASE)
        
        # Pattern 4: Find table-like data (e.g., "Q1\t500", "Region A\t1000")
        pattern4 = r'([A-Za-z][A-Za-z0-9\s]{0,25}?)[\t|]\s*([\d,]+\.?\d*)'
        matches4 = re.findall(pattern4, context_text, re.IGNORECASE)
        
        # Pattern 5: Find numbers in parentheses with labels (e.g., "Revenue (500)", "Sales ($1000)")
        pattern5 = r'([A-Za-z][A-Za-z0-9\s]{1,25}?)\s*\([^\d]*([\d,]+\.?\d*)'
        matches5 = re.findall(pattern5, context_text, re.IGNORECASE)
        
        # Combine all matches
        all_matches = matches1 + matches2 + matches3 + matches4 + matches5
        
        logger.debug(f"Found {len(all_matches)} potential data points from regex patterns")
        
        for label, value_str in all_matches[:50]:  # Increased limit to 50
            try:
                label_clean = label.strip()
                # Skip if label is too short, too long, or is just a number
                if len(label_clean) < 2 or len(label_clean) > 50 or label_clean.isdigit():
                    continue
                
                # Skip common non-data words
                skip_words = ['page', 'chapter', 'section', 'figure', 'table', 'the', 'and', 'or', 'is', 'are']
                if label_clean.lower() in skip_words or any(word in label_clean.lower() for word in ['page', 'chapter']):
                    continue
                
                # Clean value - remove commas, currency symbols, etc.
                value_clean = value_str.replace(',', '').replace('$', '').replace('%', '').replace('USD', '').strip()
                
                # Skip if value is empty or too large (likely a page number or year)
                if not value_clean:
                    continue
                
                value = float(value_clean)
                
                # Skip very small numbers (likely page numbers) or very large (likely years or IDs)
                if value < 0.01 or value > 1000000:
                    continue
                
                # Create unique key for this pair
                pair_key = (label_clean.lower(), round(value, 2))
                
                # Avoid duplicates
                if pair_key not in seen_pairs:
                    labels.append(label_clean)
                    values.append(value)
                    seen_pairs.add(pair_key)
                    
                    if len(values) >= 20:  # Stop at 20 good matches
                        break
                        
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid match: {label} = {value_str} ({e})")
                continue
        
        logger.info(f"Direct extraction: {len(values)} valid data points found")
        
        if len(values) >= 2:
            return {
                "data_type": "bar",
                "values": values[:20],  # Limit to 20
                "labels": labels[:20],
                "title": "Extracted Data from Document",
                "x_axis": "Category",
                "y_axis": "Value"
            }
        else:
            logger.warning(f"Direct extraction found only {len(values)} data points (need at least 2)")
    
    except Exception as e:
        logger.error(f"Direct extraction failed: {e}", exc_info=True)
    
    return {"error": "Could not extract enough data"}


def generate_table_from_data(data: Dict):
    """Generate a Streamlit table from extracted data."""
    try:
        import pandas as pd
        
        values = data.get("values", [])
        labels = data.get("labels", [])
        
        if not values or not labels:
            return None
        
        # Create DataFrame
        df = pd.DataFrame({
            data.get("x_axis", "Category"): labels,
            data.get("y_axis", "Value"): values
        })
        
        return df
    except Exception as e:
        logger.error(f"Error generating table: {e}")
        return None


# Visualization section removed
def _show_visualizations_section_removed():
    """Display the visualizations section with all charts and tables."""
    st.header("📊 Document Visualizations")
    
    if not st.session_state.pdf_uploaded:
        st.info("📄 Please upload a PDF document first to see visualizations.")
        return
    
    if not st.session_state.retriever:
        st.warning("⚠️ Document not processed. Please process the PDF first.")
        return
    
    # Button to extract and generate visualizations
    if st.button("🔄 Generate All Visualizations", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_container = st.empty()
        
        try:
            status_text.text("Step 1/3: Retrieving document content...")
            progress_bar.progress(20)
            time.sleep(0.3)  # Small delay for UX
            
            status_text.text("Step 2/3: Extracting numerical data...")
            progress_bar.progress(50)
            
            tables, charts = extract_all_numerical_data()
            
            status_text.text("Step 3/3: Generating visualizations...")
            progress_bar.progress(80)
            
            st.session_state.document_tables = tables
            st.session_state.document_visualizations = charts
            
            progress_bar.progress(100)
            status_text.text("Complete!")
            
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            if len(charts) > 0 or len(tables) > 0:
                st.success(f"✅ Generated {len(charts)} charts and {len(tables)} tables!")
                st.balloons()  # Celebration effect
            else:
                error_container.warning("⚠️ No visualizations could be generated.")
                
                # Show debug information
                with st.expander("🔍 Debug Information"):
                    st.markdown("**What we tried:**")
                    st.markdown("1. Direct text extraction (regex patterns)")
                    st.markdown("2. LLM-based extraction")
                    st.markdown("3. Extraction from all document chunks")
                    
                    # Try to show what data was found (even if not enough for chart)
                    try:
                        if st.session_state.retriever:
                            # Get a sample of chunks to show
                            sample_chunks = st.session_state.retriever.retrieve("numbers data", k=3)
                            if sample_chunks:
                                st.markdown("**Sample content from document:**")
                                for i, chunk in enumerate(sample_chunks[:2], 1):
                                    text_preview = chunk.get("text", "")[:200]
                                    st.code(f"Chunk {i}: {text_preview}...", language=None)
                    except Exception as e:
                        st.debug(f"Could not show sample: {e}")
                
                with st.expander("💡 Why might this happen?"):
                    st.markdown("""
                    **Possible reasons:**
                    - The document doesn't contain extractable numerical data
                    - Numbers are in images (not extractable text)
                    - Data format is not recognized
                    - Numbers are too scattered or not labeled
                    
                    **Try this:**
                    - Ask specific questions in the **Chat** tab like:
                      - "Show me the revenue data"
                      - "Graph the sales numbers"
                      - "Compare the statistics"
                    - These will generate visualizations on-demand
                    - Make sure your PDF has extractable text (not just scanned images)
                    """)
            
            st.rerun()
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            error_msg = str(e)
            error_container.error(f"❌ Error: {error_msg}")
            logger.error(f"Error in visualization generation: {e}", exc_info=True)
            
            # Show helpful error message
            with st.expander("🔍 Troubleshooting"):
                st.markdown(f"""
                **Error Details:** `{error_msg[:200]}`
                
                **Try:**
                1. Check if the PDF has extractable text (not just images)
                2. Try asking questions in the Chat tab instead
                3. Check the console/logs for more details
                """)
    
    st.markdown("---")
    
    # Display Tables
    if st.session_state.document_tables:
        st.subheader("📋 Tables")
        for i, table_data in enumerate(st.session_state.document_tables):
            with st.expander(f"Table {i+1}: {table_data.get('title', 'Data Table')}"):
                df = generate_table_from_data(table_data)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Could not generate table from this data.")
        st.markdown("---")
    
    # Display Charts
    if st.session_state.document_visualizations:
        st.subheader("📈 Charts & Graphs")
        
        # Filter out any charts with errors
        valid_charts = [c for c in st.session_state.document_visualizations if c and "error" not in c]
        
        if valid_charts:
            # Group charts by type
            bar_charts = [c for c in valid_charts if c.get("chart_type") == "bar"]
            line_charts = [c for c in valid_charts if c.get("chart_type") == "line"]
            pie_charts = [c for c in valid_charts if c.get("chart_type") == "pie"]
            other_charts = [c for c in valid_charts if c.get("chart_type") not in ["bar", "line", "pie"]]
            
            # Display Bar Charts
            if bar_charts:
                st.markdown("#### 📊 Bar Charts")
                for idx, chart in enumerate(bar_charts):
                    with st.container():
                        st.markdown(f"**{chart.get('title', f'Bar Chart {idx+1}')}**")
                        try:
                            display_chart(chart)
                        except Exception as e:
                            st.error(f"Error displaying chart: {e}")
                            logger.error(f"Error displaying chart: {e}")
                        st.markdown("---")
            
            # Display Line Charts
            if line_charts:
                st.markdown("#### 📈 Line Charts")
                for idx, chart in enumerate(line_charts):
                    with st.container():
                        st.markdown(f"**{chart.get('title', f'Line Chart {idx+1}')}**")
                        try:
                            display_chart(chart)
                        except Exception as e:
                            st.error(f"Error displaying chart: {e}")
                            logger.error(f"Error displaying chart: {e}")
                        st.markdown("---")
            
            # Display Pie Charts
            if pie_charts:
                st.markdown("#### 🥧 Pie Charts")
                for idx, chart in enumerate(pie_charts):
                    with st.container():
                        st.markdown(f"**{chart.get('title', f'Pie Chart {idx+1}')}**")
                        try:
                            display_chart(chart)
                        except Exception as e:
                            st.error(f"Error displaying chart: {e}")
                            logger.error(f"Error displaying chart: {e}")
                        st.markdown("---")
            
            # Display Other Charts
            if other_charts:
                st.markdown("#### 📊 Other Charts")
                for idx, chart in enumerate(other_charts):
                    with st.container():
                        st.markdown(f"**{chart.get('title', f'Chart {idx+1}')}**")
                        try:
                            display_chart(chart)
                        except Exception as e:
                            st.error(f"Error displaying chart: {e}")
                            logger.error(f"Error displaying chart: {e}")
                        st.markdown("---")
        else:
            st.warning("⚠️ Charts were generated but could not be displayed. Check the logs for errors.")
    else:
        if st.session_state.pdf_uploaded:
            st.info("💡 Click '🔄 Generate All Visualizations' to extract and display charts from your document.")
    
    # Summary
    if st.session_state.document_visualizations or st.session_state.document_tables:
        st.markdown("### 📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Charts", len(st.session_state.document_visualizations))
        with col2:
            st.metric("Total Tables", len(st.session_state.document_tables))
        with col3:
            total = len(st.session_state.document_visualizations) + len(st.session_state.document_tables)
            st.metric("Total Visualizations", total)


def check_api_key():
    """Check if API key is configured."""
    try:
        from app.config.settings import settings
        import os
        
        # Check if settings loaded properly
        if settings is None or not hasattr(settings, 'openai_api_key'):
            return False, "Settings not loaded properly"
        
        # Check API key
        api_key = getattr(settings, 'openai_api_key', None)
        if not api_key:
            # Try to load from environment directly as fallback
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                return True, None
            return False, "API key is missing. Please set OPENAI_API_KEY in your .env file"
        
        api_key = str(api_key).strip()
        if len(api_key) < 20:
            return False, f"API key appears to be invalid (length: {len(api_key)})"
        
        return True, None
    except Exception as e:
        # Try environment variable as fallback
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and len(api_key.strip()) >= 20:
            return True, None
        return False, f"Error checking API key: {str(e)}"


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Check API key configuration
    api_key_valid, api_key_error = check_api_key()
    
    # Header
    st.markdown('<p class="main-header">📚 PDF Chatbot</p>', unsafe_allow_html=True)
    
    # Show API key warning if needed
    if not api_key_valid:
        st.error("🔑 **API Key Configuration Required**")
        st.error(api_key_error or "OpenAI API key is not configured")
        
        # Show debugging info
        with st.expander("🔍 Debug Information"):
            import os
            st.code(f"""
Current working directory: {os.getcwd()}
.env file exists: {os.path.exists('.env')}
.env file path: {os.path.abspath('.env')}
Environment variable OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}
            """)
        
        st.info("""
        **To fix this:**
        1. Ensure `.env` file exists in: `E:\\ragbotpdf\\.env`
        2. The file should contain exactly:
           ```
           OPENAI_API_KEY=sk-...your_key_here
           ```
        3. **Important:** No spaces around the `=` sign
        4. **Important:** No quotes around the value (unless your key contains quotes)
        5. Get your API key from: https://platform.openai.com/api-keys
        6. Restart the Streamlit app after making changes
        """)
        st.stop()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📄 PDF Upload")
        
        uploaded_file = st.file_uploader(
            "Upload a PDF document",
            type=["pdf"],
            help="Upload a PDF file to start chatting with it"
        )
        
        if uploaded_file is not None:
            if st.button("Process PDF", type="primary"):
                with st.spinner("Processing PDF..."):
                    result = process_pdf(uploaded_file)
                    
                    if result["success"]:
                        st.session_state.pdf_uploaded = True
                        st.session_state.pdf_name = uploaded_file.name
                        st.session_state.chat_history = []  # Clear chat history
                        st.rerun()  # Immediately show chat interface
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        st.markdown("---")
        
        # Status
        st.header("📊 Status")
        if st.session_state.pdf_uploaded:
            st.success("✅ PDF Ready")
            if st.session_state.pdf_name:
                st.caption(f"File: {st.session_state.pdf_name}")
        else:
            st.warning("⚠️ No PDF uploaded")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Settings
        with st.expander("⚙️ Settings"):
            st.caption(f"**Chunk Size:** {settings.chunk_size}")
            st.caption(f"**Chunk Overlap:** {settings.chunk_overlap}")
            st.caption(f"**Top K Retrieval:** {settings.top_k_retrieval}")
            st.caption(f"**Model:** {settings.openai_model}")
            st.caption(f"**Embeddings:** Local (sentence-transformers) - Free!")
    
    # Main content area
    if not st.session_state.pdf_uploaded:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 👋 Welcome to PDF Chatbot!
            
            **Get started:**
            1. 📤 Upload a PDF document using the sidebar
            2. ⏳ Wait for processing to complete
            3. 💬 Start chatting with your document!
            
            **Features:**
            - 📄 Extract and understand PDF content
            - 🔍 Smart context retrieval
            - 🎯 Strict grounding in document content
            """)
    else:
        # Chat interface
        st.header("💬 Chat with Your PDF")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        # Display text answer
                        st.write(message["content"])
                        
                        # Display visualization if present
                        if "visualization" in message and message["visualization"]:
                            viz = message["visualization"]
                            
                            # Check if it's a valid chart (has image_base64)
                            if isinstance(viz, dict) and "image_base64" in viz and "error" not in viz:
                                try:
                                    import base64
                                    from io import BytesIO
                                    from PIL import Image
                                    
                                    # Decode base64 image
                                    img_data = base64.b64decode(viz["image_base64"])
                                    img = Image.open(BytesIO(img_data))
                                    
                                    # Display chart
                                    st.image(img, caption=viz.get("title", "Chart"), use_container_width=True)
                                except Exception as e:
                                    logger.error(f"Error displaying chart: {e}")
                                    st.warning("Chart could not be displayed")
                            elif isinstance(viz, dict) and "error" in viz:
                                # Don't display error messages for visualization
                                pass
        
        # Chat input
        user_question = st.chat_input("Ask a question about your PDF...")
        
        if user_question:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            # Generate response
            try:
                if st.session_state.rag_graph is None:
                    if not initialize_rag_components():
                        error_msg = "RAG system not initialized. Please upload a PDF first."
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        st.rerun()
                        return
                
                # Invoke RAG graph
                result = st.session_state.rag_graph.invoke(user_question)
                
                answer = result.get("answer", "Error generating answer")
                visualization = result.get("visualization")
                
                # CRITICAL FIX: Ensure visualization is a chart, not a table
                # If visualization exists but is not a valid chart, don't include it
                if visualization:
                    if isinstance(visualization, dict):
                        # Check if it's a valid chart with image_base64
                        if "image_base64" not in visualization or "error" in visualization:
                            # Not a valid chart, don't include it
                            visualization = None
                        # If it has image_base64, it's a valid chart - keep it
                    else:
                        # Not a dict, invalid format
                        visualization = None
                
                # Add assistant message to history with visualization
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "visualization": visualization
                })
                
            except Exception as e:
                error_msg = f"Error processing question: {str(e)}"
                logger.error(f"Error in chat: {e}")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg
                })
            
            st.rerun()
        
        # Statistics
        if st.session_state.chat_history:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Messages", len(st.session_state.chat_history))
            with col2:
                user_messages = sum(1 for msg in st.session_state.chat_history if msg["role"] == "user")
                st.metric("Questions Asked", user_messages)


if __name__ == "__main__":
    main()

