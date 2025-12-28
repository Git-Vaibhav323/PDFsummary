# Gemini API Free Tier Limitation

## ⚠️ Critical Issue

**The Gemini API Free Tier does NOT support embeddings.**

### The Problem

- **Embedding Quota**: `limit: 0` (zero requests allowed)
- **Embedding Model**: `embedding-001` is not available on free tier
- **Impact**: Cannot process PDFs or perform RAG without embeddings

### What Works on Free Tier

✅ **Chat Model** (`gemini-pro`): Works fine  
❌ **Embeddings** (`embedding-001`): **NOT AVAILABLE** (limit: 0)

## Solutions

### Option 1: Upgrade to Paid Plan (Recommended)

1. Go to: https://ai.dev/usage?tab=rate-limit
2. Check your current plan
3. Upgrade to a paid plan that includes embeddings
4. Paid plans include embedding quota

### Option 2: Wait for Quota Reset

If you have a paid plan but hit limits:
- Wait for the daily quota reset (24 hours)
- Or wait for the retry time shown in error messages

### Option 3: Use Alternative Embeddings (Code Changes Required)

Switch to a different embedding provider:
- OpenAI embeddings (requires OpenAI API key)
- Cohere embeddings
- Hugging Face embeddings
- Local embeddings (sentence-transformers)

**Note:** This requires modifying the codebase.

## Current Error Messages

The system now:
1. ✅ Detects free tier limitation early
2. ✅ Shows clear error messages
3. ✅ Tracks successful vs failed chunks
4. ✅ Provides actionable solutions

## How to Verify Your Plan

1. Visit: https://ai.dev/usage?tab=rate-limit
2. Check "Embed Content Requests" quota
3. If limit is 0, you're on free tier
4. Upgrade to get embedding access

## Testing After Upgrade

Once you upgrade:
1. Restart the Streamlit app
2. Try uploading a PDF again
3. The system will automatically use your new quota

