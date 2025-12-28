"""
Streamlit dashboard for RAG PDF Chatbot.
Provides a user-friendly interface for uploading PDFs and chatting with them.
"""
import streamlit as st
import os
import sys
import tempfile
import time
from typing import Optional, Dict
import base64
from PIL import Image
import io
import logging

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
    page_title="RAG PDF Chatbot",
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
        if "API key" in error_msg or "GROQ_API_KEY" in error_msg:
            st.error("🔑 **API Key Error**")
            st.error(error_msg)
            st.info("💡 **How to fix:**\n1. Create a `.env` file in the project root\n2. Add: `GROQ_API_KEY=your_actual_api_key`\n3. Get your API key from: https://console.groq.com/keys")
        else:
            st.error(f"Error initializing RAG components: {e}")
        logger.error(f"Error initializing RAG components: {e}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
            st.error("🔑 **Invalid API Key**")
            st.error("Your Groq API key is invalid or missing. Please check your `.env` file.")
            st.info("Get your API key from: https://console.groq.com/keys")
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
        
        # For very large documents, use adaptive chunking strategy
        if pdf_data["total_pages"] > large_doc_threshold:
            # Calculate optimal chunk size based on document size
            # Larger documents get smaller chunks to keep total chunk count manageable
            if pdf_data["total_pages"] > 200:
                chunk_size = min(chunk_size, 600)  # Very large docs: smaller chunks
                st.info(f"📄 Very large document detected ({pdf_data['total_pages']} pages). Using optimized chunking strategy...")
            elif pdf_data["total_pages"] > 100:
                chunk_size = min(chunk_size, 700)  # Large docs: medium chunks
                st.info(f"📄 Large document detected ({pdf_data['total_pages']} pages). Using optimized chunking...")
            else:
                chunk_size = min(chunk_size, 800)  # Medium-large docs
                st.info(f"📄 Large document detected ({pdf_data['total_pages']} pages). Processing...")
        
        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = chunker.chunk_pages(pdf_data["pages"])
        
        if not chunks:
            return {"success": False, "error": "No text chunks could be created"}
        
        # Handle chunk limits with user option for large documents
        if len(chunks) > max_chunks:
            if enable_large:
                # Ask user if they want to proceed with full document
                st.warning(
                    f"⚠️ **Large Document Warning**\n\n"
                    f"Your document has **{len(chunks)} chunks** (limit: {max_chunks}).\n\n"
                    f"**Options:**\n"
                    f"1. Process all chunks (may take 10-30+ minutes, risk of quota limits)\n"
                    f"2. Process first {max_chunks} chunks (faster, but some content won't be indexed)\n\n"
                    f"*Note: Processing time increases with chunk count. Each chunk requires an API call.*"
                )
                
                # For now, we'll process all chunks but with warnings
                # In a full implementation, you could add a user choice here
                st.info(f"🔄 Processing all {len(chunks)} chunks. This may take a while...")
                # Don't truncate - process all chunks
            else:
                # Truncate if large document processing is disabled
                st.warning(f"⚠️ Document has {len(chunks)} chunks. Limiting to {max_chunks} to avoid quota issues. Some content may not be indexed.")
                chunks = chunks[:max_chunks]
        
        # Show progress for documents
        progress_bar = None
        status_text = None
        if len(chunks) > 20:
            progress_bar = st.progress(0)
            status_text = st.empty()
            if len(chunks) > 50:
                status_text.text(f"Processing {len(chunks)} chunks (this may take a while due to API rate limits)...")
            else:
                status_text.text(f"Processing {len(chunks)} chunks...")
        
        # Add to vector store with progress tracking
        try:
            logger.info(f"Starting to add {len(chunks)} chunks to vector store")
            doc_ids = st.session_state.vector_store.add_documents(chunks)
            logger.info(f"Successfully added {len(doc_ids)} chunks to vector store")
            
            if progress_bar and status_text:
                progress_bar.progress(1.0)
                status_text.text("Processing complete!")
                time.sleep(0.5)  # Brief pause to show completion
                progress_bar.empty()
                status_text.empty()
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"ValueError processing PDF: {error_msg}")
            if progress_bar:
                progress_bar.empty()
            if status_text:
                status_text.empty()
            
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
                            f"3. 🔍 **Check your quota** at: https://console.groq.com/keys\n"
                            f"4. 💡 **Split the PDF** into smaller files\n\n"
                            f"*Error details: {error_msg[:300]}*"
                }
            # Return error instead of raising for better UX
            return {"success": False, "error": f"Processing error: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error processing PDF: {e}", exc_info=True)
            if progress_bar:
                progress_bar.empty()
            if status_text:
                status_text.empty()
            
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
                "error": "Invalid Groq API key. Please check your .env file and ensure GROQ_API_KEY is set correctly."
            }
        elif "400" in error_msg or "Bad Request" in error_msg:
            return {
                "success": False,
                "error": f"API request failed. The PDF might be too large or contain invalid content. Try:\n1. Using a smaller PDF\n2. Checking if the PDF has extractable text\n3. Waiting a moment and trying again\n\nDetails: {error_msg}"
            }
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            return {
                "success": False,
                "error": "API quota exceeded. Please wait a moment and try again, or check your Groq API quota."
            }
        
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        
        # Check for API key errors in exception message
        if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
            return {
                "success": False,
                "error": "Invalid or missing Groq API key. Please check your .env file. Get your API key from: https://console.groq.com/keys"
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


def display_chart(visualization: Dict):
    """
    Display visualization chart from base64 image.
    
    Args:
        visualization: Dictionary containing chart data
    """
    if not visualization or "error" in visualization:
        return
    
    try:
        if "image_base64" in visualization:
            # Decode base64 image
            image_data = base64.b64decode(visualization["image_base64"])
            image = Image.open(io.BytesIO(image_data))
            
            st.image(image, caption=visualization.get("title", "Chart"), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying chart: {e}")
        logger.error(f"Error displaying chart: {e}")


def check_api_key():
    """Check if API key is configured."""
    try:
        from app.config.settings import settings
        import os
        
        # Check if settings loaded properly
        if settings is None or not hasattr(settings, 'groq_api_key'):
            return False, "Settings not loaded properly"
        
        # Check API key
        api_key = getattr(settings, 'groq_api_key', None)
        if not api_key:
            # Try to load from environment directly as fallback
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                return True, None
            return False, "API key is missing. Please set GROQ_API_KEY in your .env file"
        
        api_key = str(api_key).strip()
        if len(api_key) < 20:
            return False, f"API key appears to be invalid (length: {len(api_key)})"
        
        return True, None
    except Exception as e:
        # Try environment variable as fallback
        import os
        api_key = os.getenv('GROQ_API_KEY')
        if api_key and len(api_key.strip()) >= 20:
            return True, None
        return False, f"Error checking API key: {str(e)}"


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Check API key configuration
    api_key_valid, api_key_error = check_api_key()
    
    # Header
    st.markdown('<p class="main-header">📚 RAG PDF Chatbot</p>', unsafe_allow_html=True)
    
    # Show API key warning if needed
    if not api_key_valid:
        st.error("🔑 **API Key Configuration Required**")
        st.error(api_key_error or "Groq API key is not configured")
        
        # Show debugging info
        with st.expander("🔍 Debug Information"):
            import os
            st.code(f"""
Current working directory: {os.getcwd()}
.env file exists: {os.path.exists('.env')}
.env file path: {os.path.abspath('.env')}
Environment variable GROQ_API_KEY: {'Set' if os.getenv('GROQ_API_KEY') else 'Not set'}
            """)
        
        st.info("""
        **To fix this:**
        1. Ensure `.env` file exists in: `E:\\ragbotpdf\\.env`
        2. The file should contain exactly:
           ```
           GROQ_API_KEY=gsk_...your_key_here
           ```
        3. **Important:** No spaces around the `=` sign
        4. **Important:** No quotes around the value (unless your key contains quotes)
        5. Get your API key from: https://console.groq.com/keys
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
                        st.success(f"✅ PDF processed successfully!")
                        st.info(f"**Pages:** {result['pages']}\n\n**Chunks:** {result['chunks']}")
                        st.session_state.pdf_uploaded = True
                        st.session_state.pdf_name = uploaded_file.name
                        st.session_state.chat_history = []  # Clear chat history
                        st.rerun()
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
            st.caption(f"**Model:** {settings.groq_model}")
            st.caption(f"**Embeddings:** Local (sentence-transformers) - Free!")
    
    # Main content area
    if not st.session_state.pdf_uploaded:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 👋 Welcome to RAG PDF Chatbot!
            
            **Get started:**
            1. 📤 Upload a PDF document using the sidebar
            2. ⏳ Wait for processing to complete
            3. 💬 Start chatting with your document!
            
            **Features:**
            - 📄 Extract and understand PDF content
            - 🔍 Smart context retrieval
            - 📊 Automatic chart generation for numerical data
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
                        st.write(message["content"])
                        
                        # Display visualization if available
                        if "visualization" in message and message["visualization"]:
                            st.markdown("**📊 Visualization:**")
                            display_chart(message["visualization"])
        
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
                
                # Add assistant message to history
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
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Messages", len(st.session_state.chat_history))
            with col2:
                user_messages = sum(1 for msg in st.session_state.chat_history if msg["role"] == "user")
                st.metric("Questions Asked", user_messages)
            with col3:
                visualizations = sum(1 for msg in st.session_state.chat_history 
                                  if msg.get("visualization") and "error" not in msg.get("visualization", {}))
                st.metric("Charts Generated", visualizations)


if __name__ == "__main__":
    main()

