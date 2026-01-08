"""
Dashboard storage and persistence.
Stores generated financial dashboards with caching support.
"""
import sqlite3
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DashboardStorage:
    """Manages dashboard persistence in SQLite database."""
    
    def __init__(self, db_path: str = "data/dashboards.db"):
        """
        Initialize dashboard storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create dashboards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboards (
                dashboard_id TEXT PRIMARY KEY,
                document_ids TEXT NOT NULL,
                document_hash TEXT NOT NULL,
                company_name TEXT,
                dashboard_data TEXT NOT NULL,
                generated_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                version INTEGER DEFAULT 1
            )
        """)
        
        # Add document_hash column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE dashboards ADD COLUMN document_hash TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_ids 
            ON dashboards(document_ids)
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Dashboard storage initialized")
    
    def _generate_dashboard_id(self, document_ids: List[str], version: int = 1) -> str:
        """
        Generate dashboard ID from document IDs and version.
        
        Args:
            document_ids: List of document IDs
            version: Document version (default: 1)
            
        Returns:
            Dashboard ID hash
        """
        # Sort document IDs for consistent hashing
        sorted_ids = sorted(document_ids)
        hash_input = f"{':'.join(sorted_ids)}:v{version}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _compute_document_hash(self, document_ids: List[str]) -> str:
        """
        Compute hash of document content to detect changes.
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            Content hash string
        """
        from app.database.documents import DocumentStorage
        doc_storage = DocumentStorage()
        
        # Get document metadata and compute hash
        doc_hashes = []
        for doc_id in sorted(document_ids):
            doc = doc_storage.get_document(doc_id)
            if doc:
                # Hash based on document ID, filename, pages, and chunks
                doc_info = f"{doc_id}:{doc.get('filename', '')}:{doc.get('pages_count', 0)}:{doc.get('chunks_count', 0)}:{doc.get('updated_at', '')}"
                doc_hashes.append(doc_info)
        
        combined = "|".join(doc_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def save_dashboard(
        self,
        document_ids: List[str],
        dashboard_data: Dict[str, Any],
        company_name: Optional[str] = None,
        version: int = 1
    ) -> str:
        """
        Save dashboard data with document hash tracking.
        
        Args:
            document_ids: List of document IDs
            dashboard_data: Complete dashboard data dictionary
            company_name: Optional company name
            version: Document version
            
        Returns:
            Dashboard ID
        """
        dashboard_id = self._generate_dashboard_id(document_ids, version)
        document_hash = self._compute_document_hash(document_ids)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if dashboard exists
            cursor.execute("""
                SELECT dashboard_id, document_hash FROM dashboards 
                WHERE dashboard_id = ?
            """, (dashboard_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                existing_hash = existing[1] if len(existing) > 1 else None
                # Only update if document hash changed
                if existing_hash != document_hash:
                    cursor.execute("""
                        UPDATE dashboards 
                        SET dashboard_data = ?, updated_at = ?, company_name = ?, document_hash = ?
                        WHERE dashboard_id = ?
                    """, (
                        json.dumps(dashboard_data),
                        datetime.utcnow().isoformat(),
                        company_name,
                        document_hash,
                        dashboard_id
                    ))
                    logger.info(f"📝 Updated dashboard {dashboard_id} (document hash changed)")
                else:
                    logger.info(f"✅ Dashboard {dashboard_id} unchanged, skipping update")
            else:
                # Insert new dashboard
                cursor.execute("""
                    INSERT INTO dashboards 
                    (dashboard_id, document_ids, document_hash, company_name, dashboard_data, generated_at, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dashboard_id,
                    json.dumps(document_ids),
                    document_hash,
                    company_name,
                    json.dumps(dashboard_data),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    version
                ))
                logger.info(f"💾 Saved dashboard {dashboard_id}")
            
            conn.commit()
            return dashboard_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving dashboard: {e}")
            raise
        finally:
            conn.close()
    
    def get_dashboard(
        self,
        document_ids: List[str],
        version: int = 1,
        check_hash: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve dashboard data, optionally checking if document hash matches.
        
        Args:
            document_ids: List of document IDs
            version: Document version
            check_hash: If True, verify document hash matches (default: True)
            
        Returns:
            Dashboard data dictionary or None if not found or hash mismatch
        """
        dashboard_id = self._generate_dashboard_id(document_ids, version)
        current_hash = self._compute_document_hash(document_ids) if check_hash else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT dashboard_data, generated_at, updated_at, document_hash
                FROM dashboards 
                WHERE dashboard_id = ?
            """, (dashboard_id,))
            
            row = cursor.fetchone()
            
            if row:
                stored_hash = row[3] if len(row) > 3 else None
                
                # If checking hash and it doesn't match, return None to force regeneration
                if check_hash and stored_hash and stored_hash != current_hash:
                    logger.info(f"🔄 Dashboard {dashboard_id} document hash changed, will regenerate")
                    return None
                
                dashboard_data = json.loads(row[0])
                logger.info(f"📖 Retrieved dashboard {dashboard_id} (generated: {row[1]})")
                return dashboard_data
            else:
                logger.debug(f"Dashboard {dashboard_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving dashboard: {e}")
            return None
        finally:
            conn.close()
    
    def delete_dashboard(self, document_ids: List[str], version: int = 1) -> bool:
        """
        Delete dashboard.
        
        Args:
            document_ids: List of document IDs
            version: Document version
            
        Returns:
            True if deleted, False if not found
        """
        dashboard_id = self._generate_dashboard_id(document_ids, version)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM dashboards WHERE dashboard_id = ?", (dashboard_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            
            if deleted:
                logger.info(f"🗑️ Deleted dashboard {dashboard_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False
        finally:
            conn.close()
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """
        List all dashboards.
        
        Returns:
            List of dashboard metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT dashboard_id, document_ids, company_name, generated_at, updated_at, version
                FROM dashboards
                ORDER BY updated_at DESC
            """)
            
            dashboards = []
            for row in cursor.fetchall():
                dashboards.append({
                    "dashboard_id": row[0],
                    "document_ids": json.loads(row[1]),
                    "company_name": row[2],
                    "generated_at": row[3],
                    "updated_at": row[4],
                    "version": row[5]
                })
            
            return dashboards
            
        except Exception as e:
            logger.error(f"Error listing dashboards: {e}")
            return []
        finally:
            conn.close()


# Global instance
_dashboard_storage: Optional[DashboardStorage] = None


def get_dashboard_storage() -> DashboardStorage:
    """Get global dashboard storage instance."""
    global _dashboard_storage
    if _dashboard_storage is None:
        _dashboard_storage = DashboardStorage()
    return _dashboard_storage

