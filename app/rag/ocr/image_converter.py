"""
Convert PDF pages to images for OCR processing.
"""
import fitz  # PyMuPDF
from typing import List, Dict
import base64
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class PDFImageConverter:
    """Converts PDF pages to base64-encoded images for OCR."""
    
    def __init__(self, dpi: int = 200):
        """
        Initialize the PDF image converter.
        
        Args:
            dpi: Resolution for image conversion (default: 200)
        """
        self.dpi = dpi
    
    def convert_page_to_image(self, pdf_path: str, page_num: int) -> str:
        """
        Convert a single PDF page to base64-encoded PNG image.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Base64-encoded PNG image as string
            
        Raises:
            ValueError: If page cannot be converted
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            
            if page_num >= doc.page_count:
                raise ValueError(f"Page {page_num} does not exist (PDF has {doc.page_count} pages)")
            
            page = doc[page_num]
            
            # Convert page to image (pixmap)
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)  # Scale factor for DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.debug(f"Converted page {page_num + 1} to image ({len(img_base64)} chars base64)")
            return img_base64
            
        except Exception as e:
            logger.error(f"Error converting page {page_num + 1} to image: {e}")
            raise ValueError(f"Failed to convert page {page_num + 1} to image: {e}") from e
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass
    
    def convert_all_pages(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Convert all PDF pages to base64-encoded images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with:
                - page_number: Page number (1-indexed)
                - image_base64: Base64-encoded PNG image
                - image_size: Size of base64 string in characters
        """
        doc = None
        pages_data = []
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count
            
            logger.info(f"Converting {total_pages} pages to images...")
            
            for page_num in range(total_pages):
                try:
                    image_base64 = self.convert_page_to_image(pdf_path, page_num)
                    pages_data.append({
                        "page_number": page_num + 1,
                        "image_base64": image_base64,
                        "image_size": len(image_base64)
                    })
                except Exception as page_error:
                    logger.warning(f"Failed to convert page {page_num + 1}: {page_error}")
                    # Continue with other pages
                    continue
            
            logger.info(f"Successfully converted {len(pages_data)}/{total_pages} pages to images")
            return pages_data
            
        except Exception as e:
            logger.error(f"Error converting PDF pages to images: {e}")
            raise ValueError(f"Failed to convert PDF pages: {e}") from e
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

