# Handling Large PDFs - Guide

## Why Large PDFs Are Challenging

The RAG chatbot processes PDFs by:
1. **Extracting text** from each page
2. **Chunking** the text into smaller pieces
3. **Embedding** each chunk using Gemini API
4. **Storing** embeddings in the vector database

### Current Limitations

1. **API Quota Limits**
   - Gemini API has rate limits (requests per minute)
   - Free tier has quota limits (requests per day)
   - Each chunk requires an API call for embedding

2. **Processing Time**
   - 100 chunks ≈ 2-5 minutes
   - 500 chunks ≈ 10-20 minutes
   - 1000+ chunks ≈ 30+ minutes

3. **Memory Usage**
   - Large documents consume more RAM
   - Vector database grows with chunk count

## Current Configuration

### Default Limits
- **Max chunks per document**: 500 (configurable)
- **Chunk size**: 1000 characters (adaptive for large docs)
- **Batch size**: 30-50 chunks per API call
- **Delay between batches**: 1-2 seconds

### Adaptive Chunking Strategy

The system automatically adjusts for large documents:

| Document Size | Chunk Size | Strategy |
|--------------|------------|----------|
| < 50 pages | 1000 chars | Standard |
| 50-100 pages | 800 chars | Optimized |
| 100-200 pages | 700 chars | Aggressive |
| 200+ pages | 600 chars | Maximum optimization |

## How to Process Larger PDFs

### Option 1: Increase Limits (Recommended for Small-Medium PDFs)

Edit your `.env` file:

```env
# Increase chunk limit
MAX_CHUNKS_PER_DOCUMENT=1000

# Enable large document processing
ENABLE_LARGE_DOCUMENT_PROCESSING=true
```

**Trade-offs:**
- ✅ More content indexed
- ⚠️ Longer processing time
- ⚠️ Higher API usage
- ⚠️ Risk of quota limits

### Option 2: Split Large PDFs (Recommended for Very Large PDFs)

For PDFs with 200+ pages:

1. **Split by chapters/sections** (best approach)
2. **Split by page ranges** (e.g., 50 pages per file)
3. **Process each split separately**

**Benefits:**
- ✅ Avoids quota limits
- ✅ Faster processing per file
- ✅ Can process in parallel
- ✅ Better error recovery

### Option 3: Optimize Chunking Strategy

For very large documents, you can:

1. **Increase chunk size** (fewer chunks):
   ```env
   CHUNK_SIZE=1500
   CHUNK_OVERLAP=300
   ```

2. **Decrease chunk size** (more, smaller chunks):
   ```env
   CHUNK_SIZE=600
   CHUNK_OVERLAP=100
   ```

**Note:** Larger chunks = fewer API calls but may lose context. Smaller chunks = more API calls but better granularity.

## Best Practices

### For Documents < 100 Pages
- Use default settings
- Should process in 5-10 minutes
- Low risk of quota issues

### For Documents 100-200 Pages
- System automatically optimizes
- Processing time: 10-20 minutes
- Monitor for quota warnings

### For Documents 200+ Pages
- **Recommended**: Split into smaller files
- Or increase limits and be patient
- Processing time: 20-60+ minutes
- High risk of quota limits

## Troubleshooting

### "API quota exceeded" Error

**Causes:**
- Too many chunks processed in short time
- Daily quota limit reached
- Rate limit exceeded

**Solutions:**
1. Wait 5-10 minutes and retry
2. Split PDF into smaller files
3. Process during off-peak hours
4. Check quota at: https://makersuite.google.com/app/apikey

### "Processing takes too long"

**Causes:**
- Very large document
- Slow API responses
- Network issues

**Solutions:**
1. Split PDF into smaller files
2. Increase batch size (risky - may hit quota)
3. Process during off-peak hours
4. Use a faster internet connection

### "Out of memory" Error

**Causes:**
- Very large document
- Too many chunks in memory

**Solutions:**
1. Split PDF into smaller files
2. Reduce chunk size
3. Increase system RAM
4. Process in batches manually

## Configuration Reference

All settings in `.env`:

```env
# Chunking
CHUNK_SIZE=1000                    # Characters per chunk
CHUNK_OVERLAP=200                  # Overlap between chunks
MAX_CHUNKS_PER_DOCUMENT=500        # Maximum chunks to process
ENABLE_LARGE_DOCUMENT_PROCESSING=true  # Allow processing large docs
LARGE_DOCUMENT_THRESHOLD_PAGES=50  # Pages threshold for "large" doc
```

## Performance Estimates

| Pages | Estimated Chunks | Processing Time | API Calls |
|-------|-----------------|-----------------|-----------|
| 10 | 20-30 | 1-2 min | 20-30 |
| 50 | 80-120 | 3-5 min | 80-120 |
| 100 | 150-250 | 8-15 min | 150-250 |
| 200 | 300-500 | 15-30 min | 300-500 |
| 500 | 700-1200 | 40-90 min | 700-1200 |

*Times are estimates and depend on API response times and network conditions.*

## Recommendations

1. **For production use**: Keep documents under 200 pages
2. **For research/analysis**: Split large documents by topic
3. **For testing**: Use smaller sample documents first
4. **For large-scale processing**: Implement batch processing with delays

