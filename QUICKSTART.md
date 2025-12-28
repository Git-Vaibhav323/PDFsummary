# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 3: Run the Application

**For Streamlit Dashboard (Recommended):**
```bash
python run_streamlit.py
```
Then open your browser to: **http://localhost:8501**

**For FastAPI Backend:**
```bash
python run.py
```
Then access the API at: **http://localhost:8000**

## 📝 Usage

### Streamlit Dashboard:
1. Upload a PDF using the sidebar
2. Wait for processing to complete
3. Start chatting with your PDF!

### FastAPI:
```bash
# Upload PDF
curl -X POST "http://localhost:8000/upload_pdf" \
  -F "file=@your_document.pdf"

# Chat
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

## ⚠️ Troubleshooting

**Connection Error (ERR_ADDRESS_INVALID):**
- Use `localhost:8501` or `127.0.0.1:8501` in your browser
- Don't use `0.0.0.0:8501`

**Port Already in Use (Error 10048):**
- **Windows:** Find and close the process using the port:
  ```powershell
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  ```
- **Linux/Mac:** Find and close the process:
  ```bash
  lsof -ti:8000 | xargs kill -9
  ```
- Or change the port in `.env` file: `API_PORT=8001`

**Import Errors:**
- Make sure you're in the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

**API Key Issues:**
- Verify your `.env` file exists and contains `GROQ_API_KEY`
- Get your API key from: https://console.groq.com/keys
- Common issues:
  - Missing `.env` file → Create it in project root
  - Placeholder value → Replace with actual API key
  - Invalid key → Verify at https://console.groq.com/keys
- **Note:** Embeddings are now free and local (sentence-transformers) - no API key needed for embeddings!

**PDF Processing Errors:**
- Ensure PDFs contain extractable text (not just images)
- Check file size and format

