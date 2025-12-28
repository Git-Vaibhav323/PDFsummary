"""
Utility to check if embeddings are available before processing.
"""
import logging
from app.rag.embeddings import LocalEmbeddings

logger = logging.getLogger(__name__)


def check_embedding_availability() -> tuple:
    """
    Check if local embeddings are available by trying to embed a test string.
    
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        embeddings = LocalEmbeddings()
        # Try to embed a small test string
        test_result = embeddings.embed_query("test")
        if test_result and len(test_result) > 0:
            return True, "✅ Local embeddings are available (free, no API needed!)"
        else:
            return False, "Embedding returned empty result"
    except ImportError as e:
        return False, (
            "❌ **sentence-transformers not installed**\n\n"
            "Local embeddings require sentence-transformers library.\n\n"
            "**Solution:**\n"
            "Install with: `pip install sentence-transformers`\n\n"
            "This enables free, offline embeddings (no API needed!)"
        )
    except Exception as e:
        error_str = str(e)
        return False, f"Embedding check failed: {error_str[:200]}"

