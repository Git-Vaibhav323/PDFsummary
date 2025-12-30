"""
OCR implementation using Mistral Vision API.
Extracts text from PDF page images.
"""
import os
from typing import List, Dict, Optional
import logging

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None

logger = logging.getLogger(__name__)


class MistralOCR:
    """OCR service using Mistral Vision API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mistral OCR client.
        
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
        self.model = "pixtral-large-latest"  # Mistral's vision-capable model
    
    def extract_text_from_image(self, image_base64: str, page_num: int = 1) -> str:
        """
        Extract text from a single base64-encoded image using Mistral Vision.
        
        Args:
            image_base64: Base64-encoded PNG image
            page_num: Page number for logging
            
        Returns:
            Extracted text as plain string
            
        Raises:
            ValueError: If OCR fails
        """
        try:
            prompt = (
                "Extract ALL text and structured data from this image. "
                "CRITICAL INSTRUCTIONS:\n"
                "1. Extract ALL text content including tables, charts, financial data, and structured information\n"
                "2. For tables: Preserve the structure with clear column separators (use | or tabs)\n"
                "3. For financial data: Extract numbers, dates, labels, and values exactly as shown\n"
                "4. Preserve line breaks, spacing, and formatting\n"
                "5. Include ALL numbers, dates, percentages, and numerical values\n"
                "6. Extract text from charts, graphs, and visual elements\n"
                "7. Do NOT summarize, explain, or add commentary\n"
                "8. Do NOT use markdown formatting\n"
                "9. Return plain text with preserved structure\n"
                "10. If you see tables, extract them row by row with clear column separation"
            )
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{image_base64}"
                            }
                        ]
                    }
                ],
                temperature=0.0  # Deterministic output
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            if not extracted_text:
                logger.warning(f"No text extracted from page {page_num}")
                return ""
            
            logger.info(f"Extracted {len(extracted_text)} characters from page {page_num}")
            return extracted_text
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OCR failed for page {page_num}: {error_msg}")
            
            # Retry once
            try:
                logger.info(f"Retrying OCR for page {page_num}...")
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": f"data:image/png;base64,{image_base64}"
                                }
                            ]
                        }
                    ],
                    temperature=0.0
                )
                extracted_text = response.choices[0].message.content.strip()
                logger.info(f"Retry successful: extracted {len(extracted_text)} characters from page {page_num}")
                return extracted_text
            except Exception as retry_error:
                logger.error(f"OCR retry also failed for page {page_num}: {retry_error}")
                raise ValueError(f"OCR failed for page {page_num}: {retry_error}") from retry_error
    
    def extract_text_from_pages(self, pages_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Extract text from multiple PDF page images.
        
        Args:
            pages_data: List of dictionaries with 'page_number' and 'image_base64'
            
        Returns:
            List of dictionaries with:
                - page_number: Page number
                - text: Extracted text
                - char_count: Character count
        """
        extracted_pages = []
        
        logger.info(f"Starting OCR for {len(pages_data)} pages...")
        
        for page_data in pages_data:
            page_num = page_data["page_number"]
            image_base64 = page_data["image_base64"]
            
            try:
                text = self.extract_text_from_image(image_base64, page_num)
                
                extracted_pages.append({
                    "page_number": page_num,
                    "text": text,
                    "char_count": len(text)
                })
                
            except Exception as e:
                logger.error(f"Failed to extract text from page {page_num}: {e}")
                # Add empty text for failed pages
                extracted_pages.append({
                    "page_number": page_num,
                    "text": "",
                    "char_count": 0
                })
                continue
        
        successful = sum(1 for p in extracted_pages if p["char_count"] > 0)
        logger.info(f"OCR completed: {successful}/{len(pages_data)} pages successful")
        
        return extracted_pages
    
    def needs_ocr(self, extracted_text: str) -> bool:
        """
        Determine if OCR is needed based on extracted text quality.
        
        Args:
            extracted_text: Text extracted from PDF
            
        Returns:
            True if OCR is needed, False otherwise
        """
        if not extracted_text:
            return True
        
        # Check text length
        text_length = len(extracted_text.strip())
        if text_length < 200:
            logger.info(f"Text too short ({text_length} chars), OCR needed")
            return True
        
        # Check if text is mostly whitespace
        non_whitespace = len([c for c in extracted_text if not c.isspace()])
        whitespace_ratio = 1 - (non_whitespace / len(extracted_text)) if extracted_text else 1.0
        
        if whitespace_ratio > 0.7:
            logger.info(f"Text is mostly whitespace ({whitespace_ratio:.2%}), OCR needed")
            return True
        
        return False

