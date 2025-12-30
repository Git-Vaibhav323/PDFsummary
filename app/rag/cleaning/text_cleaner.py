"""
Text cleaning using Mistral API.
Cleans OCR output to improve readability and structure.
"""
import os
from typing import Optional
import logging

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None

logger = logging.getLogger(__name__)


class TextCleaner:
    """Text cleaning service using Mistral API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize text cleaner.
        
        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            
        Raises:
            ValueError: If API key is not provided or mistralai is not installed
        """
        if not MISTRAL_AVAILABLE:
            raise ValueError(
                "mistralai package is not installed. Install it with: pip install mistralai"
            )
        
        if api_key is None:
            api_key = os.getenv("MISTRAL_API_KEY")
        
        if not api_key:
            raise ValueError(
                "MISTRAL_API_KEY is not set. Please set it in your .env file or environment variables."
            )
        
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-large-latest"  # Use latest Mistral model for text processing
    
    def clean_text(self, text: str, page_num: Optional[int] = None) -> str:
        """
        Clean OCR output text.
        
        Args:
            text: Raw OCR text to clean
            page_num: Optional page number for logging
            
        Returns:
            Cleaned text
            
        Raises:
            ValueError: If cleaning fails
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for cleaning (page {page_num})")
            return ""
        
        try:
            prompt = (
                "Clean and normalize the following OCR text. "
                "Tasks:\n"
                "1. Remove headers and footers (page numbers, document titles repeated on every page)\n"
                "2. Fix broken line breaks (join lines that should be together)\n"
                "3. Normalize spacing (remove excessive spaces, fix indentation)\n"
                "4. Preserve numbers exactly (do not change any numerical values)\n"
                "5. Preserve tables and structured data\n"
                "6. Do NOT summarize or paraphrase content\n"
                "7. Do NOT add explanations or commentary\n"
                "8. Return ONLY the cleaned text\n\n"
                f"OCR Text:\n{text[:8000]}"  # Limit to avoid token limits
            )
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # Deterministic output
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            
            # Remove any markdown code blocks if present
            if cleaned_text.startswith("```"):
                lines = cleaned_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()
            
            logger.info(f"Cleaned text: {len(text)} -> {len(cleaned_text)} characters (page {page_num})")
            return cleaned_text
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Text cleaning failed (page {page_num}): {error_msg}")
            
            # If cleaning fails, return original text
            logger.warning(f"Returning original text due to cleaning failure")
            return text
    
    def clean_pages(self, pages: list) -> list:
        """
        Clean text from multiple pages.
        
        Args:
            pages: List of page dictionaries with 'text' and 'page_number'
            
        Returns:
            List of cleaned page dictionaries
        """
        cleaned_pages = []
        
        logger.info(f"Cleaning text from {len(pages)} pages...")
        
        for page in pages:
            page_num = page.get("page_number", 0)
            original_text = page.get("text", "")
            
            if not original_text:
                cleaned_pages.append(page)
                continue
            
            try:
                cleaned_text = self.clean_text(original_text, page_num)
                cleaned_pages.append({
                    **page,
                    "text": cleaned_text,
                    "char_count": len(cleaned_text)
                })
            except Exception as e:
                logger.error(f"Failed to clean page {page_num}: {e}")
                # Keep original text if cleaning fails
                cleaned_pages.append(page)
        
        logger.info(f"Text cleaning completed for {len(cleaned_pages)} pages")
        return cleaned_pages

