"""
Token-based text chunking optimized for performance.
Uses recursive splitting with token-aware sizing.
"""
from typing import List, Dict
import logging
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# OpenAI text-embedding-3-small token estimate: ~4 characters = 1 token
CHARS_PER_TOKEN = 4


class TextChunker:
    """Chunks text using token-aware sizing for optimal performance."""
    
    def __init__(self, chunk_size: int = 1050, chunk_overlap: int = 135):
        """
        Initialize the text chunker with performance-optimized defaults.
        
        Args:
            chunk_size: Target chunk size in tokens (default: 1050 ≈ 4200 chars)
            chunk_overlap: Overlap in tokens (default: 135 ≈ 540 chars)
        """
        # Convert tokens to characters for splitter (1 token ≈ 4 chars)
        self.chunk_size_tokens = chunk_size
        self.chunk_overlap_tokens = chunk_overlap
        self.chunk_size_chars = chunk_size * CHARS_PER_TOKEN
        self.chunk_overlap_chars = chunk_overlap * CHARS_PER_TOKEN
        
        logger.info(f"TextChunker initialized: {chunk_size} tokens (~{self.chunk_size_chars} chars), overlap: {chunk_overlap} tokens (~{self.chunk_overlap_chars} chars)")
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size_chars,
            chunk_overlap=self.chunk_overlap_chars,
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
        
        start_time = time.time()
        base_metadata = metadata or {}
        chunks = self.splitter.split_text(text)
        
        chunk_list = []
        for idx, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            
            # Estimate token count for logging
            estimated_tokens = len(chunk_text) / CHARS_PER_TOKEN
            
            chunk_metadata = {
                **base_metadata,
                "chunk_index": idx,
                "chunk_size": len(chunk_text),
                "estimated_tokens": int(estimated_tokens)
            }
            
            chunk_list.append({
                "text": chunk_text,
                "chunk_index": idx,
                "metadata": chunk_metadata
            })
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Created {len(chunk_list)} chunks in {elapsed:.2f}s | Avg: {len(chunk_list)/max(elapsed, 0.01):.0f} chunks/sec")
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

