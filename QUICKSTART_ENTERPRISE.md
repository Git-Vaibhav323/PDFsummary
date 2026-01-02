# Quick Start - Enterprise RAG Chatbot

## Prerequisites

- Python 3.9+
- OpenAI API key
- Virtual environment

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-key-here
MISTRAL_API_KEY=optional-mistral-key
```

### 3. Verify Configuration

```bash
python -c "from app.config.settings import settings; print(f'Model: {settings.openai_model}'); print(f'Embeddings: {settings.embedding_model_name}')"
```

Should output:
```
Model: gpt-4.1-mini
Embeddings: text-embedding-3-small
```

## Running the Server

### Start Backend

```bash
python run.py
```

Or with Streamlit:

```bash
streamlit run run_streamlit.py
```

## Testing the System

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### 2. Upload Document

```bash
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@sample.pdf"
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

### 3. Ask a Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the revenue for Q3?",
    "conversation_id": null
  }'
```

Response:
```json
{
  "answer": "Based on the document, the Q3 revenue was $127M, representing a 15% increase from Q2.",
  "table": null,
  "chart": {
    "type": "bar",
    "title": "Quarterly Revenue Comparison",
    "labels": ["Q1", "Q2", "Q3"],
    "values": [100, 110, 127],
    "xAxis": "Quarter",
    "yAxis": "Revenue (M)"
  },
  "conversation_id": null
}
```

### 4. Ask a Follow-up Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What about profit?"
  }'
```

The system will use memory to understand "it" refers to the quarterly comparison.

### 5. Clear Memory

```bash
curl -X DELETE http://localhost:8000/clear_memory
```

Response:
```json
{
  "message": "Conversation memory cleared successfully",
  "success": true
}
```

### 6. Get System Status

```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "initialized": true,
  "vector_store_ready": true,
  "memory_messages": 4,
  "config": {
    "model": "gpt-4.1-mini",
    "embedding_model": "text-embedding-3-small",
    "temperature": 0.0,
    "top_k_retrieval": 5,
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

## Key Features

### ✅ Fast Document Processing
- Asynchronous ingestion
- Staged pipeline (text extraction → chunking → embedding)
- Multi-document support

### ✅ Low-Latency Responses
- Optimized chunking (900-1100 tokens)
- Top-K retrieval (default: 5)
- Batched embeddings

### ✅ Smart Memory Management
- Global chat history
- Follow-up question resolution
- Fast clearing
- Memory NOT stored in vector DB

### ✅ Rich Visualizations
- Bar charts (category comparison)
- Line charts (time-series/trends)
- Pie charts (proportions)
- Markdown tables
- Deterministic generation

### ✅ Strict Grounding
- Answers only from retrieved documents
- "Not available in the uploaded document" fallback
- No external knowledge injection
- Deterministic output (temperature=0)

### ✅ Financial Data Support
- Revenue, profit, cost extraction
- Multi-year comparisons
- Trend analysis
- Professional visualizations

## Troubleshooting

### API Key Issues

```
Error: OPENAI_API_KEY is required
```

Solution: Check `.env` file has correct format:
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

### Model Issues

```
Error: model not found
```

Solution: Verify models in settings:
```bash
python -c "from app.config.settings import settings; print(settings.openai_model)"
```

Should print: `gpt-4.1-mini`

### Vector Store Issues

```
Error: Vector store not initialized
```

Solution: Upload a document first:
```bash
curl -X POST http://localhost:8000/upload_pdf -F "file=@sample.pdf"
```

### Memory Issues

Clear memory to reset conversation:
```bash
curl -X DELETE http://localhost:8000/clear_memory
```

## Performance Metrics

Expected performance (with gpt-4.1-mini + text-embedding-3-small):

| Operation | Latency | Notes |
|:--|--:|:--|
| Document Upload (10 pages) | 5-10s | Includes chunking + embedding |
| Question Answering | 2-3s | Memory + retrieval + generation |
| Memory Clearing | <100ms | Instant |
| Chart Generation | 1-2s | Included in answer time |
| Follow-up Questions | 2-3s | Memory-aware rewriting |

## Architecture

```
User Request
    ↓
[FastAPI Routes]
    ↓
[EnterpriseRAGSystem]
    ├─ DocumentProcessor (async)
    ├─ RAGRetriever
    ├─ VisualizationPipeline
    ├─ ConversationMemory
    └─ VectorStore (ChromaDB)
    ↓
Standardized JSON Response
```

## Model Stack

**FIXED for enterprise reliability:**

- **Chat/Reasoning**: gpt-4.1-mini
  - Fast, efficient reasoning
  - Cost-effective
  - Temperature: 0 (deterministic)

- **Embeddings**: text-embedding-3-small
  - Scalable embeddings
  - Fast processing
  - Optimized for retrieval

- **Temperature**: 0
  - Deterministic output
  - Reproducible responses
  - Enterprise reliability

## Next Steps

1. **Upload Documents**: Start with financial PDFs
2. **Test Questions**: Ask questions about the documents
3. **Monitor Performance**: Check response times and quality
4. **Adjust Parameters**: Fine-tune top_k_retrieval if needed
5. **Deploy**: Use with Render, Vercel, or your infrastructure

## Support

For issues or questions:

1. Check the [ENTERPRISE_RAG_IMPLEMENTATION.md](./ENTERPRISE_RAG_IMPLEMENTATION.md) documentation
2. Review logs in the terminal
3. Check `.env` configuration
4. Clear memory and try again

## Version Info

- **System**: Enterprise RAG v2.0.0
- **Model**: gpt-4.1-mini
- **Embeddings**: text-embedding-3-small
- **Vector DB**: ChromaDB
- **Framework**: FastAPI + LangChain
