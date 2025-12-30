"""
PDF text extraction using PyMuPDF (fitz).
Handles text extraction reliably without OCR unless explicitly needed.
"""
import fitz  # PyMuPDF
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PDFLoader:
    """Loads and extracts text from PDF files using PyMuPDF."""
    
    def __init__(self):
        """Initialize the PDF loader."""
        pass
    
    def load_pdf(self, file_path: str) -> Dict[str, any]:
        """
        Load PDF and extract text with page information.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing:
                - text: Full extracted text
                - pages: List of page dictionaries with text and page number
                - total_pages: Total number of pages
                
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is empty or cannot be read
        """
        doc = None
        try:
            doc = fitz.open(file_path)
            
            # Save page_count before any operations
            total_pages = doc.page_count
            
            if total_pages == 0:
                raise ValueError("PDF has no pages")
            
            full_text = ""
            pages = []
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                
                if not page_text.strip():
                    logger.warning(f"Page {page_num + 1} has no extractable text")
                    continue
                
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
                pages.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
            
            if not full_text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            # Create result before closing document
            result = {
                "text": full_text,
                "raw_text": full_text,  # Preserve raw text for OCR detection
                "pages": pages,
                "total_pages": total_pages,
                "file_path": file_path
            }
            
            logger.info(f"Successfully extracted text from {len(pages)} pages")
            return result
            
        except fitz.FileDataError as e:
            logger.error(f"Error reading PDF file: {e}")
            raise ValueError(f"Cannot read PDF file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading PDF: {e}")
            raise
        finally:
            # Ensure document is always closed
            if doc is not None:
                try:
                    doc.close()
                except Exception as close_error:
                    logger.warning(f"Error closing PDF document: {close_error}")
    
    def extract_text_only(self, file_path: str) -> str:
        """
        Extract only the text content from PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
        """
        result = self.load_pdf(file_path)
        return result["text"]

