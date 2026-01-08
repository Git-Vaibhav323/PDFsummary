"""
Document storage model for tracking multiple uploaded documents.
Manages document metadata and relationships.
"""
import sqlite3
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Use same database path as conversations
def find_project_root():
    """Find the project root directory."""
    current = os.path.abspath(__file__)
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, ".git")) or os.path.exists(os.path.join(current, "requirements.txt")):
            return str(current)
        current = os.path.dirname(current)
    return os.getcwd()

PROJECT_ROOT = find_project_root()
DB_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DB_DIR, "conversations.db")


class DocumentStorage:
    """Manages document metadata storage in SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize document storage.
        
        Args:
            db_path: Path to SQLite database file (defaults to ./data/conversations.db)
        """
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chunks_count INTEGER DEFAULT 0,
                pages_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processed',
                metadata TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_upload_time 
            ON documents(upload_time DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_status 
            ON documents(status)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Document database initialized at {self.db_path}")
    
    def create_document(
        self,
        document_id: str,
        name: str,
        filename: str,
        chunks_count: int = 0,
        pages_count: int = 0,
        status: str = "processed",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new document record.
        
        Args:
            document_id: Unique document ID
            name: Document display name
            filename: Original filename
            chunks_count: Number of chunks created
            pages_count: Number of pages
            status: Document status (processed, processing, error)
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with document details
        """
        upload_time = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (id, name, filename, upload_time, chunks_count, pages_count, status, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (document_id, name, filename, upload_time, chunks_count, pages_count, status, metadata_json, upload_time))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created document {document_id}: {name}")
        
        return {
            "id": document_id,
            "name": name,
            "filename": filename,
            "upload_time": upload_time,
            "chunks_count": chunks_count,
            "pages_count": pages_count,
            "status": status,
            "metadata": metadata,
            "updated_at": upload_time
        }
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document details, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, upload_time, chunks_count, pages_count, status, metadata, updated_at
            FROM documents
            WHERE id = ?
        """, (document_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except:
                pass
        
        return {
            "id": row["id"],
            "name": row["name"],
            "filename": row["filename"],
            "upload_time": row["upload_time"],
            "chunks_count": row["chunks_count"],
            "pages_count": row["pages_count"],
            "status": row["status"],
            "metadata": metadata,
            "updated_at": row["updated_at"]
        }
    
    def list_documents(self, limit: int = 100) -> List[Dict]:
        """
        List all documents ordered by most recent first.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, upload_time, chunks_count, pages_count, status, metadata, updated_at
            FROM documents
            ORDER BY upload_time DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            metadata = None
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except:
                    pass
            
            documents.append({
                "id": row["id"],
                "name": row["name"],
                "filename": row["filename"],
                "upload_time": row["upload_time"],
                "chunks_count": row["chunks_count"],
                "pages_count": row["pages_count"],
                "status": row["status"],
                "metadata": metadata,
                "updated_at": row["updated_at"]
            })
        
        return documents
    
    def update_document(
        self,
        document_id: str,
        chunks_count: Optional[int] = None,
        pages_count: Optional[int] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            chunks_count: Updated chunks count
            pages_count: Updated pages count
            status: Updated status
            metadata: Updated metadata dictionary
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if chunks_count is not None:
            updates.append("chunks_count = ?")
            params.append(chunks_count)
        
        if pages_count is not None:
            updates.append("pages_count = ?")
            params.append(pages_count)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(document_id)
        
        query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Updated document {document_id}")
        
        return updated
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document record.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM documents WHERE id = ?", (document_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted document {document_id}")
        return True
    
    def clear_all_documents(self) -> int:
        """
        Clear all document records.
        
        Returns:
            Number of documents deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {count} documents")
        return count

