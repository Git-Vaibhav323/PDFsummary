"""
Text chunking with safe token handling to avoid overflow.
Uses recursive character splitting with overlap.
"""
from typing import List, Dict
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunks text safely to avoid token overflow."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into smaller pieces with metadata.
        
        Args:
            text: Text to chunk
            metadata: Base metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with:
                - text: Chunk text
                - chunk_index: Index of the chunk
                - metadata: Combined metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        base_metadata = metadata or {}
        chunks = self.splitter.split_text(text)
        
        chunk_list = []
        for idx, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
                
            chunk_metadata = {
                **base_metadata,
                "chunk_index": idx,
                "chunk_size": len(chunk_text)
            }
            
            chunk_list.append({
                "text": chunk_text,
                "chunk_index": idx,
                "metadata": chunk_metadata
            })
        
        logger.info(f"Created {len(chunk_list)} chunks from text")
        return chunk_list
    
    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Chunk text from multiple pages, preserving page information.
        
        Args:
            pages: List of page dictionaries with 'text' and 'page_number'
            
        Returns:
            List of chunk dictionaries with page metadata
        """
        all_chunks = []
        
        for page in pages:
            page_metadata = {
                "page_number": page.get("page_number", 0),
                "source": "pdf"
            }
            
            page_chunks = self.chunk_text(
                page.get("text", ""),
                metadata=page_metadata
            )
            
            all_chunks.extend(page_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks

