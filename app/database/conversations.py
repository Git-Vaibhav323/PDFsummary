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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages(conversation_id)
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
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, title, created_at, created_at))
        
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
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
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
        visualization: Optional[Dict] = None
    ) -> Dict:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            visualization: Optional visualization data
            
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
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        
        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "visualization": visualization,
            "created_at": created_at
        }
    
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

