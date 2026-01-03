"""
Optimized document ingestion pipeline for high-performance RAG.

Handles:
- Asynchronous document processing
- Text extraction and table extraction
- Efficient chunking (900-1200 tokens, 120-150 overlap)
- Batch embedding generation
- Embedding caching
- Structured metadata storage
- Performance timing and monitoring
"""
import asyncio
import logging
import time
from typing import List, Dict, Optional, Tuple
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentMetadata:
    """Manages metadata for document chunks."""
    
    def __init__(self, document_id: str, filename: str, total_pages: int = 1):
        """
        Initialize document metadata.
        
        Args:
            document_id: Unique document identifier
            filename: Original filename
            total_pages: Total number of pages in document
        """
        self.document_id = document_id
        self.filename = filename
        self.total_pages = total_pages
        self.created_at = datetime.utcnow().isoformat()
        self.chunk_count = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "total_pages": self.total_pages,
            "created_at": self.created_at,
            "chunk_count": self.chunk_count
        }


class EmbeddingCache:
    """Cache embeddings to avoid reprocessing identical content."""
    
    def __init__(self, cache_dir: str = "./embedding_cache"):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, List[float]] = {}
        logger.info(f"Embedding cache initialized at {cache_dir}")
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cache_path(self, content_hash: str) -> Path:
        """Get file path for cached embedding."""
        return self.cache_dir / f"{content_hash}.json"
    
    def get(self, content: str) -> Optional[List[float]]:
        """
        Get cached embedding for content.
        
        Args:
            content: Content to look up
            
        Returns:
            Cached embedding or None
        """
        content_hash = self._hash_content(content)
        
        # Check memory cache first (fastest)
        if content_hash in self.memory_cache:
            logger.debug(f"Memory cache hit for {content_hash[:8]}")
            return self.memory_cache[content_hash]
        
        # Check disk cache
        cache_file = self.get_cache_path(content_hash)
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    embedding = data.get("embedding")
                    if embedding:
                        self.memory_cache[content_hash] = embedding
                        logger.debug(f"Disk cache hit for {content_hash[:8]}")
                        return embedding
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e}")
        
        return None
    
    def set(self, content: str, embedding: List[float]):
        """
        Cache embedding for content.
        
        Args:
            content: Content to cache
            embedding: Embedding vector
        """
        content_hash = self._hash_content(content)
        
        # Store in memory cache
        self.memory_cache[content_hash] = embedding
        
        # Store in disk cache
        cache_file = self.get_cache_path(content_hash)
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    "content_hash": content_hash,
                    "embedding": embedding,
                    "timestamp": datetime.utcnow().isoformat()
                }, f)
            logger.debug(f"Cached embedding for {content_hash[:8]}")
        except Exception as e:
            logger.warning(f"Error writing cache file {cache_file}: {e}")
    
    def clear(self):
        """Clear all caches."""
        self.memory_cache.clear()
        try:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")


class OptimizedChunker:
    """Optimized text chunker for token-efficient splitting."""
    
    # Approximate tokens per character (varies by model)
    TOKENS_PER_CHAR = 0.25
    
    def __init__(self, 
                 min_chunk_tokens: int = 900,
                 max_chunk_tokens: int = 1100,
                 overlap_tokens: int = 125):
        """
        Initialize optimized chunker.
        
        Args:
            min_chunk_tokens: Minimum tokens per chunk
            max_chunk_tokens: Maximum tokens per chunk
            overlap_tokens: Tokens to overlap between chunks
        """
        # Convert tokens to approximate characters
        self.min_chunk_chars = int(min_chunk_tokens / self.TOKENS_PER_CHAR)
        self.max_chunk_chars = int(max_chunk_tokens / self.TOKENS_PER_CHAR)
        self.overlap_chars = int(overlap_tokens / self.TOKENS_PER_CHAR)
        
        logger.info(f"Chunker config: {self.min_chunk_chars}-{self.max_chunk_chars} chars, "
                   f"{self.overlap_chars} char overlap")
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks with efficient overlap.
        
        Args:
            text: Text to chunk
            metadata: Base metadata for chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        chunks = []
        base_metadata = metadata or {}
        
        # Split by paragraphs first for better semantic boundaries
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max, save current chunk
            if current_chunk and len(current_chunk) + len(para) > self.max_chunk_chars:
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "metadata": {
                        **base_metadata,
                        "chunk_index": chunk_index,
                        "content_type": "text"
                    }
                })
                chunk_index += 1
                
                # Overlap: keep last part of previous chunk
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text
            
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        
        # Add final chunk if it has content
        if current_chunk and len(current_chunk.strip()) >= self.min_chunk_chars // 2:
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "metadata": {
                    **base_metadata,
                    "chunk_index": chunk_index,
                    "content_type": "text"
                }
            })
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """Get last portion of text for overlap with next chunk."""
        if len(text) <= self.overlap_chars:
            return text
        
        # Find last sentence boundary within overlap range
        start_pos = len(text) - self.overlap_chars
        last_period = text.rfind('.', start_pos)
        last_newline = text.rfind('\n', start_pos)
        
        boundary = max(last_period, last_newline)
        if boundary > start_pos:
            return text[boundary:].lstrip()
        
        return text[-self.overlap_chars:]


class TableExtractor:
    """Extract and process tabular data from documents."""
    
    def extract_tables(self, text: str) -> List[Dict]:
        """
        Extract table-like content from text.
        
        Args:
            text: Text to extract tables from
            
        Returns:
            List of extracted tables with metadata
        """
        # Basic table detection: lines with multiple columns (separated by spaces/tabs)
        tables = []
        lines = text.split('\n')
        
        table_lines = []
        for line in lines:
            # Detect table-like rows (multiple columns)
            if self._is_table_row(line):
                table_lines.append(line)
            elif table_lines:
                # End of table
                if len(table_lines) >= 2:
                    table = self._parse_table(table_lines)
                    if table:
                        tables.append(table)
                table_lines = []
        
        # Don't forget last table
        if table_lines and len(table_lines) >= 2:
            table = self._parse_table(table_lines)
            if table:
                tables.append(table)
        
        return tables
    
    def _is_table_row(self, line: str) -> bool:
        """Detect if line is part of a table."""
        # Look for multiple columns separated by spaces or pipes
        col_count = len(line.split('|')) if '|' in line else len(line.split())
        return col_count >= 2 and len(line.strip()) > 20
    
    def _parse_table(self, lines: List[str]) -> Optional[Dict]:
        """Parse table lines into structured data."""
        try:
            # Extract columns
            if '|' in lines[0]:
                # Pipe-delimited table
                headers = [h.strip() for h in lines[0].split('|') if h.strip()]
                rows = []
                for line in lines[1:]:
                    if '|' in line:
                        row = [c.strip() for c in line.split('|') if c.strip()]
                        if len(row) == len(headers):
                            rows.append(row)
            else:
                # Space-delimited table
                headers = lines[0].split()
                rows = [line.split() for line in lines[1:] if len(line.split()) == len(headers)]
            
            if headers and rows:
                return {
                    "headers": headers,
                    "rows": rows,
                    "content_type": "table"
                }
        except Exception as e:
            logger.debug(f"Table parsing failed: {e}")
        
        return None


class DocumentProcessor:
    """High-performance document ingestion pipeline."""
    
    def __init__(self, 
                 embedding_model=None,
                 cache_dir: str = "./embedding_cache"):
        """
        Initialize document processor.
        
        Args:
            embedding_model: Embedding model instance
            cache_dir: Directory for embedding cache
        """
        self.embedding_model = embedding_model
        self.cache = EmbeddingCache(cache_dir)
        self.chunker = OptimizedChunker(
            min_chunk_tokens=900,
            max_chunk_tokens=1100,
            overlap_tokens=125
        )
        self.table_extractor = TableExtractor()
        self.embeddings_batch = []  # For batching
    
    async def process_document_async(self, 
                                     document_id: str,
                                     pages: List[Dict],
                                     filename: str = "document.pdf") -> Dict:
        """
        Process document asynchronously with performance tracking.
        
        Args:
            document_id: Unique document ID
            pages: List of page dictionaries with 'text' and 'page_number'
            filename: Original filename
            
        Returns:
            Processing result with chunks and metadata
        """
        doc_start_time = time.time()
        logger.info(f"📄 Starting document processing: {filename} ({len(pages)} pages)")
        
        metadata = DocumentMetadata(document_id, filename, len(pages))
        
        # Stage 1: Text extraction
        extract_start = time.time()
        all_text = self._extract_text(pages)
        extract_time = time.time() - extract_start
        logger.info(f"   ✅ Text extraction: {extract_time:.3f}s | {len(all_text)} chars")
        
        # Stage 2: Table extraction
        table_start = time.time()
        tables = self.table_extractor.extract_tables(all_text)
        table_time = time.time() - table_start
        logger.info(f"   ✅ Table extraction: {table_time:.3f}s | {len(tables)} tables found")
        
        # Stage 3: Chunking
        chunk_start = time.time()
        chunks = self.chunker.chunk_text(
            all_text,
            metadata={
                "document_id": document_id,
                "filename": filename,
                "total_pages": len(pages)
            }
        )
        chunk_time = time.time() - chunk_start
        logger.info(f"   ✅ Chunking: {chunk_time:.3f}s | {len(chunks)} chunks created")
        
        # Stage 4: Batch embedding (will be done by vector store)
        # Cache ready for retrieval, embedding done by vector store in batch
        
        metadata.chunk_count = len(chunks)
        
        total_time = time.time() - doc_start_time
        logger.info(f"📊 Processing complete: {total_time:.3f}s total | Extract: {extract_time:.3f}s | Table: {table_time:.3f}s | Chunk: {chunk_time:.3f}s")
        
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks": chunks,
            "tables": tables,
            "metadata": metadata.to_dict(),
            "processed_at": datetime.utcnow().isoformat(),
            "processing_time_s": total_time
        }
    
    def _extract_text(self, pages: List[Dict]) -> str:
        """Extract text from pages."""
        all_text = []
        for page in pages:
            text = page.get("text", "").strip()
            if text:
                all_text.append(text)
        
        return "\n\n".join(all_text)
    
    async def process_documents_batch(self, 
                                      documents: List[Tuple[str, List[Dict], str]]) -> List[Dict]:
        """
        Process multiple documents concurrently.
        
        Args:
            documents: List of (document_id, pages, filename) tuples
            
        Returns:
            List of processing results
        """
        logger.info(f"Processing {len(documents)} documents in parallel")
        
        tasks = [
            self.process_document_async(doc_id, pages, filename)
            for doc_id, pages, filename in documents
        ]
        
        results = await asyncio.gather(*tasks)
        
        logger.info(f"Batch processing complete: {len(results)} documents processed")
        return results
    
    def cache_embedding(self, chunk_text: str, embedding: List[float]):
        """Cache an embedding."""
        self.cache.set(chunk_text, embedding)
    
    def get_cached_embedding(self, chunk_text: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        return self.cache.get(chunk_text)
    
    def clear_cache(self):
        """Clear embedding cache."""
        self.cache.clear()
