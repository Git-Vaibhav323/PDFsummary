"""
Conversation storage using SQLite database.
Manages conversation threads and messages.
"""
import sqlite3
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Database file path - use same project root detection as settings
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


class ConversationStorage:
    """Manages conversation storage in SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize conversation storage.
        
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
        
        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                metadata TEXT,  -- JSON metadata (e.g., web_search_preference)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing conversations table to add metadata column if it doesn't exist
        try:
            # Check if metadata column exists by trying to query it
            cursor.execute("PRAGMA table_info(conversations)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'metadata' not in columns:
                # Column doesn't exist, add it
                logger.info("Adding metadata column to conversations table...")
                cursor.execute("""
                    ALTER TABLE conversations ADD COLUMN metadata TEXT DEFAULT '{}'
                """)
                conn.commit()
                logger.info("✅ Successfully added metadata column to conversations table")
        except Exception as e:
            logger.warning(f"Could not check/add metadata column: {e}")
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                visualization TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        
        # Create conversation_documents table to track document associations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_documents (
                conversation_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (conversation_id, document_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages(conversation_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_at 
            ON messages(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_documents_conversation_id 
            ON conversation_documents(conversation_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_documents_document_id 
            ON conversation_documents(document_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
            ON conversations(updated_at DESC)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Conversation database initialized at {self.db_path}")
    
    def create_conversation(self, title: Optional[str] = None) -> Dict:
        """
        Create a new conversation.
        
        Args:
            title: Optional title for the conversation (defaults to "New Conversation")
            
        Returns:
            Dictionary with conversation details
        """
        import uuid
        conversation_id = str(uuid.uuid4())
        title = title or "New Conversation"
        created_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (id, title, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (conversation_id, title, json.dumps({}), created_at, created_at))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created conversation {conversation_id} with title '{title}'")
        
        return {
            "id": conversation_id,
            "title": title,
            "created_at": created_at,
            "updated_at": created_at,
            "message_count": 0
        }
    
    def list_conversations(self, limit: int = 50) -> List[Dict]:
        """
        List all conversations ordered by most recent first.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        conversations = []
        for row in rows:
            conversations.append({
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": row["message_count"]
            })
        
        return conversations
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a conversation with its messages.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with conversation and messages, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get conversation
        cursor.execute("""
            SELECT id, title, metadata, created_at, updated_at
            FROM conversations
            WHERE id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Parse metadata
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        # Get messages
        cursor.execute("""
            SELECT id, role, content, visualization, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        message_rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for msg_row in message_rows:
            messages.append({
                "id": msg_row["id"],
                "role": msg_row["role"],
                "content": msg_row["content"],
                "visualization": msg_row["visualization"],
                "created_at": msg_row["created_at"]
            })
        
        return {
            "id": row["id"],
            "title": row["title"],
            "metadata": metadata,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": messages,
            "message_count": len(messages)
        }
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        visualization: Optional[Dict] = None,
        prevent_duplicates: bool = True
    ) -> Dict:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            visualization: Optional visualization data
            prevent_duplicates: If True, check for duplicate messages before inserting
            
        Returns:
            Dictionary with message details
        """
        if role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")
        
        # Check if conversation exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Prevent duplicate messages (check last message with same content and role)
        if prevent_duplicates:
            cursor.execute("""
                SELECT id, content FROM messages 
                WHERE conversation_id = ? AND role = ?
                ORDER BY created_at DESC LIMIT 1
            """, (conversation_id, role))
            last_msg = cursor.fetchone()
            if last_msg and last_msg[1] == content:
                conn.close()
                logger.warning(f"Duplicate message detected, skipping: {content[:50]}...")
                # Return existing message info
                return {
                    "id": last_msg[0],
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "visualization": visualization,
                    "created_at": datetime.utcnow().isoformat(),
                    "duplicate": True
                }
        
        # Add message
        visualization_json = json.dumps(visualization) if visualization else None
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, visualization, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (conversation_id, role, content, visualization_json, created_at))
        
        message_id = cursor.lastrowid
        
        # Update conversation updated_at
        cursor.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """, (created_at, conversation_id))
        
        # Update title if it's still "New Conversation" and this is the first user message
        if role == "user":
            cursor.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
            title_row = cursor.fetchone()
            if title_row and title_row[0] == "New Conversation":
                # Use first 50 chars of user message as title
                title = content[:50] + ("..." if len(content) > 50 else "")
                cursor.execute("""
                    UPDATE conversations
                    SET title = ?
                    WHERE id = ?
                """, (title, conversation_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Persisted {role} message to conversation {conversation_id}")
        
        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "visualization": visualization,
            "created_at": created_at
        }
    
    def associate_documents(self, conversation_id: str, document_ids: List[str]) -> None:
        """
        Associate documents with a conversation.
        
        Args:
            conversation_id: Conversation ID
            document_ids: List of document IDs to associate
        """
        if not document_ids:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if conversation exists
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Insert document associations (ignore duplicates)
        created_at = datetime.utcnow().isoformat()
        for doc_id in document_ids:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO conversation_documents (conversation_id, document_id, created_at)
                    VALUES (?, ?, ?)
                """, (conversation_id, doc_id, created_at))
            except sqlite3.IntegrityError:
                # Already exists, skip
                pass
        
        conn.commit()
        conn.close()
        
        logger.info(f"Associated {len(document_ids)} documents with conversation {conversation_id}")
    
    def get_conversation_documents(self, conversation_id: str) -> List[str]:
        """
        Get document IDs associated with a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of document IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT document_id FROM conversation_documents
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        document_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return document_ids
    
    def clear_conversation_messages(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation without deleting the conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if cleared, False if conversation not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if conversation exists
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # Delete all messages
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        deleted_count = cursor.rowcount
        
        # Update conversation updated_at
        cursor.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), conversation_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted_count} messages from conversation {conversation_id}")
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted conversation {conversation_id}")
        return True
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """
        Update conversation title.
        
        Args:
            conversation_id: Conversation ID
            title: New title
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
        """, (title, datetime.utcnow().isoformat(), conversation_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Updated conversation {conversation_id} title to '{title}'")
        
        return updated
    
    def update_conversation_metadata(self, conversation_id: str, metadata: Dict) -> bool:
        """
        Update conversation metadata (e.g., web_search_preference).
        
        Args:
            conversation_id: Conversation ID
            metadata: Dictionary of metadata to update (will be merged with existing)
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing metadata
        cursor.execute("""
            SELECT COALESCE(metadata, '{}') FROM conversations WHERE id = ?
        """, (conversation_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        # Merge with existing metadata
        existing_metadata = {}
        if row[0]:
            try:
                existing_metadata = json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                existing_metadata = {}
        
        existing_metadata.update(metadata)
        
        # Update metadata
        cursor.execute("""
            UPDATE conversations
            SET metadata = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(existing_metadata), datetime.utcnow().isoformat(), conversation_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

