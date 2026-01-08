"""
Web search integration using Tavily API for external information retrieval.
"""
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily not installed. Web search will be disabled. Install with: pip install tavily-python")


def _get_tavily_api_key() -> Optional[str]:
    """
    Get Tavily API key from environment or .env file.
    
    Returns:
        API key string or None if not found
    """
    # First try direct environment variable (for runtime/env vars)
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        return api_key
    
    # Try loading from .env file using pydantic-settings
    try:
        from app.config.settings import Settings
        # Check if settings has tavily_key (if we add it to Settings)
        # For now, try loading .env manually
        from pathlib import Path
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("TAVILY_API_KEY=") and not line.startswith("#"):
                        # Extract value, handling quoted strings
                        value = line.split("=", 1)[1].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        if value and "your_tavily" not in value.lower():
                            return value
    except Exception as e:
        logger.debug(f"Could not load TAVILY_API_KEY from .env: {e}")
    
    return None


class WebSearchService:
    """Web search service using Tavily API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize web search service.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var or .env file)
        """
        self.api_key = api_key or _get_tavily_api_key()
        self.client = None
        
        if TAVILY_AVAILABLE and self.api_key:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Web search service initialized with Tavily")
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily client: {e}")
                self.client = None
        else:
            if not TAVILY_AVAILABLE:
                logger.warning("Tavily library not available. Web search disabled.")
            elif not self.api_key:
                logger.warning("TAVILY_API_KEY not set. Web search disabled.")
    
    def is_available(self) -> bool:
        """Check if web search is available."""
        return self.client is not None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, content, score
        """
        if not self.is_available():
            logger.warning("Web search not available")
            return []
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0)
                })
            
            logger.info(f"Web search returned {len(results)} results for: {query[:50]}")
            return results
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def format_search_results(self, results: List[Dict]) -> str:
        """
        Format search results into context string.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        formatted = ["[Web Search Results - Current Information from the Internet]"]
        for i, result in enumerate(results, 1):
            formatted.append(f"\n{i}. {result['title']}")
            formatted.append(f"   URL: {result['url']}")
            # Include more content for better context (up to 800 chars per result)
            content = result.get('content', '')
            if len(content) > 800:
                formatted.append(f"   Content: {content[:800]}...")
            else:
                formatted.append(f"   Content: {content}")
        
        return "\n".join(formatted)


def should_use_web_search(question: str, document_context: str, retrieval_score: float) -> bool:
    """
    Determine if web search should be used.
    
    Args:
        question: User question
        document_context: Retrieved document context
        retrieval_score: Similarity score of retrieved documents
        
    Returns:
        True if web search should be used
    """
    # Check for explicit web search requests
    web_search_keywords = [
        "search online", "search the web", "latest", "current", "recent",
        "today", "now", "2024", "2025", "external", "internet", "web"
    ]
    
    question_lower = question.lower()
    if any(keyword in question_lower for keyword in web_search_keywords):
        logger.info("Web search triggered by explicit request")
        return True
    
    # Check if document context is insufficient (low retrieval score)
    if retrieval_score < 0.5 and len(document_context) < 200:
        logger.info(f"Web search triggered by low retrieval score: {retrieval_score}")
        return True
    
    # Check for time-sensitive questions
    time_sensitive_keywords = [
        "current", "latest", "recent", "today", "now", "this year",
        "this month", "this week"
    ]
    
    if any(keyword in question_lower for keyword in time_sensitive_keywords):
        logger.info("Web search triggered by time-sensitive question")
        return True
    
    return False

