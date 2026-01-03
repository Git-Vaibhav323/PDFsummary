"""
Utility to check if embeddings are available before processing.
"""
import logging
from app.rag.embeddings import OpenAIEmbeddingsWrapper

logger = logging.getLogger(__name__)


def check_embedding_availability() -> tuple:
    """
    Check if OpenAI embeddings are available by trying to embed a test string.
    
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        embeddings = OpenAIEmbeddingsWrapper()
        # Try to embed a small test string
        test_result = embeddings.embed_query("test")
        if test_result and len(test_result) > 0:
            return True, "✅ OpenAI embeddings (text-embedding-3-small) are available!"
        else:
            return False, "Embedding returned empty result"
    except Exception as e:
        error_str = str(e)
        if "API key" in error_str or "authorization" in error_str.lower():
            return False, (
                "❌ **OpenAI API key not configured**\n\n"
                "OpenAI embeddings require a valid API key.\n\n"
                "**Solution:**\n"
                "Set OPENAI_API_KEY in your .env file\n\n"
                "Get an API key from: https://platform.openai.com/api-keys"
            )
        else:
            return False, f"Embedding check failed: {error_str[:200]}"

