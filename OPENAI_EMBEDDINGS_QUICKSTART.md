# OpenAI Embeddings Migration - Quick Start

## What Changed
✅ **From:** Local sentence-transformers (`all-MiniLM-L6-v2`) - Free, offline
✅ **To:** OpenAI API (`text-embedding-3-small`) - Paid, cloud-based

## Why This Change
- Better embedding quality and consistency
- Scalable, production-ready embeddings
- Same API key as chat completions
- Centralized cost management

## What You Need to Do

### 1. Verify Your API Key
Make sure your `.env` file has a valid OpenAI API key:
```
OPENAI_API_KEY=sk-...your_key_here...
```

### 2. Check Your OpenAI Account
- Visit: https://platform.openai.com/account/billing/overview
- Ensure you have credits or a payment method
- Check usage limits at: https://platform.openai.com/account/billing/limits

### 3. Restart the Application
```bash
# Kill any running instances
# Then restart fresh
python run.py
# or
streamlit run app/streamlit_app.py
```

### 4. Test Functionality
1. Upload a PDF
2. Check for embedding errors in logs
3. Ask a question to test retrieval
4. Monitor OpenAI API usage dashboard

## Important Notes

### API Costs
- **Embeddings:** $0.02 per 1M tokens (text-embedding-3-small)
- **Chat:** $0.30/$1.50 per 1M tokens in/out (gpt-4.1-mini)
- Example: 100 PDFs × 10,000 tokens = 1M tokens = $0.02

### Old Embeddings Are Invalid
- Old Chroma vector database will need to be regenerated
- Delete `chroma_db/` folder to force re-embedding
- First run will take longer (embedding all documents)

### Rate Limits
If you see "rate limit" errors:
1. Wait a moment and retry
2. Check your usage at platform.openai.com
3. Upgrade your API plan if needed

## Troubleshooting

### "API key not found" Error
```
❌ Solution:
1. Check .env file exists in project root
2. Verify OPENAI_API_KEY=sk-... format
3. No quotes around the key
4. Restart the application
```

### "Invalid API key" Error
```
❌ Solution:
1. Visit https://platform.openai.com/api-keys
2. Generate a new API key
3. Update .env file
4. Restart application
```

### "Rate limit exceeded" Error
```
❌ Solution:
1. Wait 1-2 minutes
2. Check usage: https://platform.openai.com/account/usage
3. Consider upgrading your plan
4. Retry the operation
```

### Old Embeddings Not Working
```
❌ Solution:
1. Delete the chroma_db folder (optional)
2. Upload PDFs again
3. System will auto-generate new OpenAI embeddings
```

## Files Changed
- `app/rag/embeddings.py` - Now uses OpenAI API
- `app/rag/vector_store.py` - Updated imports
- `app/rag/embedding_check.py` - Updated validation
- `app/rag/graph.py` - Updated error messages
- `app/streamlit_app.py` - Updated UI and error handling
- `app/config/settings.py` - Cleaned up configuration

## Rollback to Local Embeddings
If you need to revert:
1. Restore git version: `git checkout app/rag/embeddings.py`
2. Change imports back to `LocalEmbeddings`
3. Ensure `sentence-transformers` is installed
4. Regenerate embeddings by re-uploading PDFs

## Questions or Issues?
- Check logs for specific error messages
- Verify API key at https://platform.openai.com/api-keys
- Check rate limits at https://platform.openai.com/account/billing/limits
- See full migration guide: `EMBEDDING_MODEL_MIGRATION.md`

---
**Status:** ✅ Migration Complete
**Date:** 2024
