"""
LangGraph-based preprocessing pipeline for OCR, cleaning, and structured data extraction.
Runs during PDF upload before chunking and embedding.
"""
from typing import TypedDict, List, Dict, Optional
import logging
from langgraph.graph import StateGraph, END
from app.rag.ocr.mistral_ocr import MistralOCR
from app.rag.ocr.image_converter import PDFImageConverter
from app.rag.cleaning.text_cleaner import TextCleaner
from app.rag.extraction.structured_extractor import StructuredDataExtractor

logger = logging.getLogger(__name__)


class PreprocessingState(TypedDict, total=False):
    """State definition for preprocessing graph."""
    pdf_path: str
    raw_text: str
    pages: List[Dict]
    needs_ocr: bool
    ocr_text: Optional[str]
    ocr_pages: Optional[List[Dict]]
    cleaned_text: str
    cleaned_pages: List[Dict]
    structured_data: List[Dict]
    error: Optional[str]


class PreprocessingGraph:
    """LangGraph-based preprocessing pipeline."""
    
    def __init__(self, mistral_api_key: Optional[str] = None):
        """
        Initialize preprocessing graph.
        
        Args:
            mistral_api_key: Mistral API key (optional, will use env var if not provided)
        """
        try:
            self.ocr_service = MistralOCR(api_key=mistral_api_key)
            self.image_converter = PDFImageConverter()
            self.text_cleaner = TextCleaner(api_key=mistral_api_key)
            self.data_extractor = StructuredDataExtractor(api_key=mistral_api_key)
            self.graph = self._build_graph()
        except ValueError as e:
            logger.warning(f"Mistral API not configured: {e}. OCR features will be disabled.")
            self.ocr_service = None
            self.text_cleaner = None
            self.data_extractor = None
            self.graph = None
    
    def _build_graph(self) -> StateGraph:
        """Build the preprocessing LangGraph workflow."""
        workflow = StateGraph(PreprocessingState)
        
        # Add nodes
        workflow.add_node("detect_ocr", self._detect_ocr_node)
        workflow.add_node("ocr", self._ocr_node)
        workflow.add_node("clean_text", self._clean_text_node)
        workflow.add_node("extract_structured_data", self._extract_structured_data_node)
        
        # Set entry point
        workflow.set_entry_point("detect_ocr")
        
        # Add conditional edge for OCR
        workflow.add_conditional_edges(
            "detect_ocr",
            self._should_run_ocr,
            {
                "yes": "ocr",
                "no": "clean_text"
            }
        )
        
        # OCR -> clean_text
        workflow.add_edge("ocr", "clean_text")
        
        # clean_text -> extract_structured_data
        workflow.add_edge("clean_text", "extract_structured_data")
        
        # extract_structured_data -> END
        workflow.add_edge("extract_structured_data", END)
        
        # Compile the graph
        # Note: We don't use checkpointing for preprocessing as it's a one-time operation
        try:
            return workflow.compile()
        except Exception as e:
            logger.error(f"Error compiling preprocessing graph: {e}")
            return None
    
    def _detect_ocr_node(self, state: PreprocessingState) -> PreprocessingState:
        """Node 1: Detect if OCR is needed - enhanced for visual/unstructured data."""
        try:
            raw_text = state.get("raw_text", "")
            pages = state.get("pages", [])
            
            if not raw_text:
                logger.warning("No raw text provided for OCR detection")
                return {**state, "needs_ocr": True, "error": "No text extracted from PDF"}
            
            # Enhanced OCR detection: Check for visual/unstructured content
            # 1. Check if many pages have very little text (likely scanned/images)
            pages_with_little_text = 0
            total_chars = len(raw_text)
            avg_chars_per_page = total_chars / len(pages) if pages else 0
            
            for page in pages:
                page_text = page.get("text", "")
                if len(page_text.strip()) < 100:  # Less than 100 chars = likely visual content
                    pages_with_little_text += 1
            
            # If more than 30% of pages have little text, likely needs OCR
            if pages and (pages_with_little_text / len(pages)) > 0.3:
                logger.info(f"Detected {pages_with_little_text}/{len(pages)} pages with little text - enabling OCR for visual content")
                needs_ocr = True
            elif avg_chars_per_page < 200:  # Very low average = likely scanned PDF
                logger.info(f"Low average text per page ({avg_chars_per_page:.0f} chars) - enabling OCR")
                needs_ocr = True
            else:
                # Use standard OCR detection
                if self.ocr_service:
                    needs_ocr = self.ocr_service.needs_ocr(raw_text)
                else:
                    # If Mistral not configured, skip OCR
                    needs_ocr = False
                    logger.info("Mistral API not configured, skipping OCR")
            
            logger.info(f"OCR detection: needs_ocr={needs_ocr} (pages with little text: {pages_with_little_text}/{len(pages) if pages else 0})")
            return {**state, "needs_ocr": needs_ocr}
            
        except Exception as e:
            logger.error(f"Error in detect_ocr_node: {e}")
            return {**state, "needs_ocr": False, "error": f"OCR detection failed: {e}"}
    
    def _ocr_node(self, state: PreprocessingState) -> PreprocessingState:
        """Node 2: Run OCR on PDF pages."""
        try:
            if not self.ocr_service:
                logger.warning("OCR service not available, skipping OCR")
                return {**state, "ocr_text": state.get("raw_text", ""), "ocr_pages": state.get("pages", [])}
            
            pdf_path = state.get("pdf_path", "")
            if not pdf_path:
                return {**state, "error": "PDF path not provided for OCR"}
            
            logger.info("Starting OCR process...")
            
            # Convert PDF pages to images
            try:
                pages_data = self.image_converter.convert_all_pages(pdf_path)
            except Exception as convert_error:
                logger.error(f"Failed to convert PDF to images: {convert_error}")
                return {**state, "error": f"Failed to convert PDF pages to images: {convert_error}"}
            
            if not pages_data:
                return {**state, "error": "No pages could be converted to images"}
            
            # Extract text from images using OCR
            try:
                ocr_pages = self.ocr_service.extract_text_from_pages(pages_data)
            except Exception as ocr_error:
                logger.error(f"OCR failed: {ocr_error}")
                # Retry once
                try:
                    logger.info("Retrying OCR...")
                    ocr_pages = self.ocr_service.extract_text_from_pages(pages_data)
                except Exception as retry_error:
                    logger.error(f"OCR retry failed: {retry_error}")
                    return {**state, "error": "Text could not be extracted from the uploaded document."}
            
            # Combine OCR text from all pages
            ocr_text = "\n\n".join([
                f"--- Page {p['page_number']} ---\n\n{p['text']}"
                for p in ocr_pages if p.get("text")
            ])
            
            if not ocr_text.strip():
                return {**state, "error": "Text could not be extracted from the uploaded document."}
            
            logger.info(f"OCR completed: extracted {len(ocr_text)} characters from {len(ocr_pages)} pages")
            return {
                **state,
                "ocr_text": ocr_text,
                "ocr_pages": ocr_pages
            }
            
        except Exception as e:
            logger.error(f"Error in ocr_node: {e}", exc_info=True)
            return {**state, "error": f"OCR failed: {e}"}
    
    def _clean_text_node(self, state: PreprocessingState) -> PreprocessingState:
        """Node 3: Clean text (OCR output or raw text)."""
        try:
            # Determine which text to clean
            if state.get("needs_ocr", False) and state.get("ocr_text"):
                text_to_clean = state["ocr_text"]
                pages_to_clean = state.get("ocr_pages", [])
            else:
                text_to_clean = state.get("raw_text", "")
                pages_to_clean = state.get("pages", [])
            
            if not text_to_clean:
                logger.warning("No text to clean")
                return {**state, "cleaned_text": "", "cleaned_pages": []}
            
            # Clean text
            if self.text_cleaner:
                try:
                    cleaned_pages = self.text_cleaner.clean_pages(pages_to_clean)
                    cleaned_text = "\n\n".join([
                        f"--- Page {p['page_number']} ---\n\n{p['text']}"
                        for p in cleaned_pages if p.get("text")
                    ])
                except Exception as clean_error:
                    logger.warning(f"Text cleaning failed, using original text: {clean_error}")
                    cleaned_text = text_to_clean
                    cleaned_pages = pages_to_clean
            else:
                # If cleaner not available, use text as-is
                cleaned_text = text_to_clean
                cleaned_pages = pages_to_clean
            
            logger.info(f"Text cleaning completed: {len(text_to_clean)} -> {len(cleaned_text)} characters")
            return {
                **state,
                "cleaned_text": cleaned_text,
                "cleaned_pages": cleaned_pages
            }
            
        except Exception as e:
            logger.error(f"Error in clean_text_node: {e}")
            # Return original text if cleaning fails
            text = state.get("ocr_text") or state.get("raw_text", "")
            return {**state, "cleaned_text": text, "cleaned_pages": state.get("pages", [])}
    
    def _extract_structured_data_node(self, state: PreprocessingState) -> PreprocessingState:
        """Node 4: Extract structured data from cleaned text."""
        try:
            cleaned_text = state.get("cleaned_text", "")
            
            if not cleaned_text:
                logger.warning("No cleaned text for structured data extraction")
                return {**state, "structured_data": []}
            
            # Extract structured data
            if self.data_extractor:
                try:
                    structured_data = self.data_extractor.extract_structured_data(cleaned_text)
                except Exception as extract_error:
                    logger.warning(f"Structured data extraction failed: {extract_error}")
                    structured_data = []
            else:
                structured_data = []
            
            logger.info(f"Extracted {len(structured_data)} structured data items")
            return {**state, "structured_data": structured_data}
            
        except Exception as e:
            logger.error(f"Error in extract_structured_data_node: {e}")
            return {**state, "structured_data": []}
    
    def _should_run_ocr(self, state: PreprocessingState) -> str:
        """Conditional function to determine if OCR should run."""
        needs_ocr = state.get("needs_ocr", False)
        return "yes" if needs_ocr else "no"
    
    def process(self, pdf_path: str, pdf_data: Dict) -> Dict:
        """
        Process PDF through the preprocessing pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            pdf_data: Dictionary from PDFLoader with 'text', 'pages', etc.
            
        Returns:
            Dictionary with:
                - text: Final cleaned text (for chunking)
                - pages: Final cleaned pages
                - structured_data: Extracted structured data
                - error: Error message if any
        """
        if not self.graph:
            # If graph not available (Mistral not configured), return original data
            logger.info("Preprocessing graph not available, returning original PDF data")
            return {
                "text": pdf_data.get("text", ""),
                "pages": pdf_data.get("pages", []),
                "structured_data": [],
                "error": None
            }
        
        try:
            # Initialize state
            initial_state = {
                "pdf_path": pdf_path,
                "raw_text": pdf_data.get("text", ""),
                "pages": pdf_data.get("pages", []),
                "needs_ocr": False,
                "ocr_text": None,
                "ocr_pages": None,
                "cleaned_text": "",
                "cleaned_pages": [],
                "structured_data": [],
                "error": None
            }
            
            # Run preprocessing graph
            # Handle LangGraph checkpoint KeyError gracefully
            try:
                result = self.graph.invoke(initial_state)
            except KeyError as ke:
                # Handle LangGraph checkpoint KeyError (e.g., '__start__')
                if "'__start__'" in str(ke) or "__start__" in str(ke) or "__start__" in repr(ke):
                    logger.warning(f"LangGraph checkpoint error (non-critical): {ke}. Skipping preprocessing, using original data.")
                    # Fall back to original data - this is acceptable as preprocessing is optional
                    return {
                        "text": pdf_data.get("text", ""),
                        "pages": pdf_data.get("pages", []),
                        "structured_data": [],
                        "error": None  # Don't treat this as an error, just skip preprocessing
                    }
                else:
                    # Different KeyError, re-raise it
                    raise
            
            # Extract results
            cleaned_text = result.get("cleaned_text", "")
            cleaned_pages = result.get("cleaned_pages", [])
            structured_data = result.get("structured_data", [])
            error = result.get("error")
            
            # If there's an error or no cleaned text, fall back to original
            if error or not cleaned_text:
                logger.warning(f"Preprocessing failed or produced no text: {error}")
                return {
                    "text": pdf_data.get("text", ""),
                    "pages": pdf_data.get("pages", []),
                    "structured_data": structured_data,
                    "error": error
                }
            
            return {
                "text": cleaned_text,
                "pages": cleaned_pages,
                "structured_data": structured_data,
                "error": error
            }
            
        except Exception as e:
            # Check if this is the checkpoint KeyError that we already handled
            if isinstance(e, KeyError) and ("__start__" in str(e) or "__start__" in repr(e)):
                # This should have been caught above, but just in case
                logger.warning(f"LangGraph checkpoint error caught in outer handler: {e}. Using original data.")
                return {
                    "text": pdf_data.get("text", ""),
                    "pages": pdf_data.get("pages", []),
                    "structured_data": [],
                    "error": None
                }
            logger.error(f"Error in preprocessing pipeline: {e}", exc_info=True)
            # Fall back to original data
            return {
                "text": pdf_data.get("text", ""),
                "pages": pdf_data.get("pages", []),
                "structured_data": [],
                "error": f"Preprocessing failed: {e}"
            }

