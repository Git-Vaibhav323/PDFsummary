# Production-Ready RAG PDF Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot that allows users to upload PDF documents and chat with them using Groq API (for chat) and local embeddings (sentence-transformers), LangChain, LangGraph, and Chroma vector database.

## Features

- **PDF Processing**: Reliable text extraction using PyMuPDF (no OCR unless needed)
- **Smart Chunking**: Safe text chunking to avoid token overflow
- **Vector Storage**: Persistent Chroma vector database with embeddings
- **RAG Pipeline**: LangGraph-based flow for context retrieval and answer generation
- **Visualization**: Automatic chart generation (bar, line, pie) when numerical data is detected
- **Strict Grounding**: Answers are strictly based on PDF context - no hallucination
- **Error Handling**: Graceful handling of edge cases and API failures
- **FastAPI Backend**: RESTful API for PDF upload and chat
- **Streamlit Dashboard**: Beautiful web interface for easy interaction

## Tech Stack

- **Python 3.8+**
- **LangChain**: LLM framework
- **LangGraph**: Workflow orchestration
- **Groq API**: Fast chat model (free tier available)
- **sentence-transformers**: Local embeddings (free, no API needed)
- **Chroma**: Vector database with persistence
- **FastAPI**: Web framework
- **Streamlit**: Interactive web dashboard
- **PyMuPDF**: PDF text extraction
- **Matplotlib/Plotly**: Data visualization

## Project Structure

```
ragbotpdf/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── streamlit_app.py        # Streamlit dashboard
│   ├── config/
│   │   └── settings.py         # Configuration management
│   ├── rag/
│   │   ├── pdf_loader.py       # PDF text extraction
│   │   ├── chunker.py          # Text chunking
│   │   ├── embeddings.py       # Local embeddings wrapper (sentence-transformers)
│   │   ├── vector_store.py     # Chroma vector store
│   │   ├── retriever.py        # Context retrieval
│   │   ├── prompts.py          # Prompt templates
│   │   ├── visualization.py    # Chart generation
│   │   └── graph.py            # LangGraph RAG pipeline
│   └── api/
│       └── routes.py            # FastAPI routes
├── run.py                      # Run FastAPI server
├── run_streamlit.py            # Run Streamlit dashboard
├── requirements.txt
├── env.example
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Groq API key ([Get one here](https://console.groq.com/keys)) - for chat model
- sentence-transformers (installed automatically) - for free local embeddings

### 2. Installation

```bash
# Clone or navigate to the project directory
cd ragbotpdf

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the Application

**Option A: Streamlit Dashboard (Recommended for UI)**
```bash
# Run Streamlit dashboard
python run_streamlit.py

# Or directly with streamlit
streamlit run app/streamlit_app.py
```

The dashboard will be available at `http://localhost:8501`

**Note:** If you see connection errors, make sure to use `localhost:8501` or `127.0.0.1:8501` in your browser, not `0.0.0.0:8501`

**Option B: FastAPI Backend (For API access)**
```bash
# Start the FastAPI server
python run.py

# Or use uvicorn directly
uvicorn app.api.routes:app --host 127.0.0.1 --port 8000
```

The API will be available at `http://localhost:8000` or `http://127.0.0.1:8000`

**Note:** If port 8000 is already in use, the server will automatically try to find an available port.

## Streamlit Dashboard Usage

The Streamlit dashboard provides an intuitive web interface for interacting with your PDFs.

### Features:
- **📤 Easy PDF Upload**: Drag and drop or browse to upload PDFs
- **💬 Interactive Chat**: Real-time conversation with your documents
- **📊 Visual Charts**: Automatic visualization of numerical data
- **📈 Statistics**: Track your chat history and generated charts
- **⚙️ Settings Panel**: View configuration and system status

### How to Use:
1. **Start the Dashboard**: Run `python run_streamlit.py` or `streamlit run app/streamlit_app.py`
2. **Upload PDF**: Use the sidebar to upload a PDF document
3. **Wait for Processing**: The system will extract and process the PDF
4. **Start Chatting**: Ask questions in the chat interface
5. **View Visualizations**: Charts will automatically appear when relevant

### Interface Overview:
- **Left Sidebar**: PDF upload, status, settings, and controls
- **Main Area**: Chat interface with message history
- **Auto-refresh**: Messages and visualizations update automatically

## API Usage

### 1. Upload a PDF

```bash
curl -X POST "http://localhost:8000/upload_pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

Response:
```json
{
  "message": "PDF uploaded and processed successfully",
  "pages": 10,
  "chunks": 45,
  "document_ids": 45
}
```

### 2. Chat with the PDF

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of this document?"}'
```

Response:
```json
{
  "answer": "The main topic is...",
  "visualization": null
}
```

If visualization is generated:
```json
{
  "answer": "The data shows...",
  "visualization": {
    "chart_type": "bar",
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "title": "Chart Title"
  }
}
```

### 3. Health Check

```bash
curl http://localhost:8000/health
```

## LangGraph Flow

The RAG pipeline follows this flow:

1. **retrieve_context**: Fetch relevant chunks from Chroma vector store
2. **generate_answer**: Use Groq LLM to generate answer from context
3. **check_visualization**: Determine if visualization is needed
4. **extract_data** (conditional): Extract numerical data from context
5. **generate_chart** (conditional): Create visualization chart
6. **finalize_response**: Combine answer and optional visualization

## Key Features

### Strict Grounding

- Answers are generated ONLY from retrieved PDF context
- If information is not in the document, responds: "Not available in the uploaded document"
- No external knowledge or assumptions

### Visualization

- Automatically detects when charts would be helpful
- Supports bar charts, line charts, and pie charts
- Extracts numerical data directly from PDF context
- Returns base64-encoded chart images

### Error Handling

- Gracefully handles empty PDFs
- Retries API calls once on failure
- Validates inputs and provides clear error messages
- No crashes - all errors are caught and handled

### Vector Database

- Persistent storage in `./chroma_db` directory
- Supports reloading existing embeddings
- Metadata includes page numbers and chunk indices

## Configuration Options

Edit `.env` or environment variables:

- `GROQ_API_KEY`: Your Groq API key (required for chat)
- `GROQ_MODEL`: Chat model (default: `llama-3.1-8b-instant`)
- `EMBEDDING_MODEL`: Local embedding model (default: `all-MiniLM-L6-v2`)
- `CHROMA_PERSIST_DIRECTORY`: Vector DB directory (default: `./chroma_db`)
- `CHUNK_SIZE`: Text chunk size (default: `1000`)
- `CHUNK_OVERLAP`: Chunk overlap (default: `200`)
- `TOP_K_RETRIEVAL`: Number of chunks to retrieve (default: `5`)
- `API_HOST`: API host (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)

## Development

### Code Quality

- Type hints throughout
- Comprehensive docstrings
- Modular architecture
- Clean separation of concerns

### Testing

Test the API endpoints using curl, Postman, or any HTTP client.

Example workflow:
1. Upload a PDF with numerical data
2. Ask questions about the data
3. Verify answers are grounded in the PDF
4. Check if visualizations are generated for numerical questions

## Troubleshooting

### API Key Issues

- Ensure `GROQ_API_KEY` is set in `.env`
- Verify the API key is valid and has quota

### PDF Processing Errors

- Ensure PDFs contain extractable text (not just images)
- Check file size and format

### Vector Store Issues

- Delete `./chroma_db` directory to reset embeddings
- Ensure write permissions in the project directory

### Import Errors

- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## License

This project is provided as-is for production use.

## Support

For issues or questions, check the logs for detailed error messages. The application logs all operations at INFO level.

#
