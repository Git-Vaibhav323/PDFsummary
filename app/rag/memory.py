"""
Lightweight memory system for conversation context with session support.

Key principles:
- Session-scoped chat history
- Used ONLY for follow-up question resolution
- NOT embedded or stored in vector database
- Fast clear_memory() function
- Token-safe truncation
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Message:
    """Represents a single message in conversation."""
    
    def __init__(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Initialize message.
        
        Args:
            role: 'user' or 'assistant'
            content: Message text
            metadata: Optional metadata (visualization, etc.)
        """
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class ConversationMemory:
    """Lightweight, fast conversation memory system with token-safe truncation."""
    
    def __init__(self, max_history: int = 20, max_tokens: int = 4000, session_id: Optional[str] = None):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of messages to keep in memory
            max_tokens: Maximum tokens to keep (approximate)
            session_id: Optional session ID for scoping
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.session_id = session_id
        self.created_at = datetime.utcnow().isoformat()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add message to memory with token-safe truncation.
        
        Args:
            role: 'user' or 'assistant'
            content: Message text
            metadata: Optional metadata
        """
        message = Message(role, content, metadata)
        self.messages.append(message)
        
        # Truncate based on message count
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        # Truncate based on token count (approximate: 1 token ≈ 4 chars)
        total_chars = sum(len(msg.content) for msg in self.messages)
        total_tokens = total_chars // 4
        
        if total_tokens > self.max_tokens:
            # Remove oldest messages until under token limit
            while total_tokens > self.max_tokens and len(self.messages) > 2:
                removed = self.messages.pop(0)
                total_chars -= len(removed.content)
                total_tokens = total_chars // 4
        
        logger.debug(f"Added {role} message. Memory now has {len(self.messages)} messages (~{total_tokens} tokens)")
    
    def get_history(self) -> List[Dict]:
        """
        Get full conversation history.
        
        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_last_n_messages(self, n: int = 5) -> List[Dict]:
        """
        Get last N messages for context.
        
        Args:
            n: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self.messages[-n:]]
    
    def get_context_for_question_rewriting(self, max_turns: int = 10) -> str:
        """
        Get context string for question rewriting with last N turns.
        
        Used ONLY to resolve references in follow-up questions.
        
        Args:
            max_turns: Maximum number of turns (user+assistant pairs) to include
            
        Returns:
            Formatted context string
        """
        if not self.messages:
            return ""
        
        # Get last N turns (user-assistant pairs)
        # Each turn = 2 messages (user + assistant)
        num_messages = min(len(self.messages), max_turns * 2)
        recent_messages = self.messages[-num_messages:]
        
        context_lines = []
        for msg in recent_messages:
            role = msg.role.upper()
            # Truncate long messages but keep essential context
            content = msg.content[:300] if len(msg.content) > 300 else msg.content
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def clear(self):
        """Clear all memory instantly."""
        self.messages.clear()
        logger.info("Conversation memory cleared")
    
    def __len__(self) -> int:
        """Return number of messages in memory."""
        return len(self.messages)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ConversationMemory({len(self.messages)} messages)"


class SessionMemoryManager:
    """
    Session-scoped memory manager for conversation memory.
    
    Maintains per-session memory instances.
    """
    
    _instances: Dict[str, ConversationMemory] = {}
    _default_session_id: str = "default"
    
    @classmethod
    def get_memory(cls, session_id: Optional[str] = None) -> ConversationMemory:
        """
        Get or create memory instance for a session.
        
        Args:
            session_id: Session ID (defaults to "default")
            
        Returns:
            ConversationMemory instance for the session
        """
        sid = session_id or cls._default_session_id
        
        if sid not in cls._instances:
            cls._instances[sid] = ConversationMemory(
                max_history=20,
                max_tokens=4000,
                session_id=sid
            )
            logger.info(f"Memory initialized for session: {sid}")
        
        return cls._instances[sid]
    
    @classmethod
    def reset_memory(cls, session_id: Optional[str] = None):
        """Reset memory for a session."""
        sid = session_id or cls._default_session_id
        
        if sid in cls._instances:
            cls._instances[sid].clear()
            del cls._instances[sid]
            logger.info(f"Memory reset for session: {sid}")
        
        # Create new instance
        cls._instances[sid] = ConversationMemory(
            max_history=20,
            max_tokens=4000,
            session_id=sid
        )
    
    @classmethod
    def clear_memory(cls, session_id: Optional[str] = None):
        """Clear memory for a session (fast clear)."""
        sid = session_id or cls._default_session_id
        
        if sid in cls._instances:
            cls._instances[sid].clear()
            logger.info(f"Memory cleared for session: {sid}")
        else:
            logger.warning(f"No memory to clear for session: {sid}")
    
    @classmethod
    def clear_all_sessions(cls):
        """Clear all session memories."""
        cls._instances.clear()
        logger.info("All session memories cleared")


# Backward compatibility: GlobalMemoryManager as alias
class GlobalMemoryManager:
    """Backward compatibility wrapper for SessionMemoryManager."""
    
    @classmethod
    def get_memory(cls, session_id: Optional[str] = None) -> ConversationMemory:
        """Get memory for default session."""
        return SessionMemoryManager.get_memory(session_id)
    
    @classmethod
    def reset_memory(cls):
        """Reset default session memory."""
        SessionMemoryManager.reset_memory()
    
    @classmethod
    def clear_memory(cls):
        """Clear default session memory."""
        SessionMemoryManager.clear_memory()


def get_global_memory(session_id: Optional[str] = None) -> ConversationMemory:
    """
    Convenience function to get memory for a session.
    
    Args:
        session_id: Optional session ID (defaults to "default")
    
    Returns:
        ConversationMemory instance for the session
    """
    return SessionMemoryManager.get_memory(session_id)


def clear_memory(session_id: Optional[str] = None):
    """
    Clear conversation memory for a session.
    
    Args:
        session_id: Optional session ID (defaults to "default")
    """
    SessionMemoryManager.clear_memory(session_id)


def add_to_memory(role: str, content: str, metadata: Optional[Dict] = None, session_id: Optional[str] = None):
    """
    Add message to session memory.
    
    Args:
        role: 'user' or 'assistant'
        content: Message text
        metadata: Optional metadata
        session_id: Optional session ID (defaults to "default")
    """
    memory = get_global_memory(session_id)
    memory.add_message(role, content, metadata)


def get_memory_context(session_id: Optional[str] = None, max_turns: int = 10) -> str:
    """
    Get memory context for question rewriting.
    
    Args:
        session_id: Optional session ID (defaults to "default")
        max_turns: Maximum number of turns to include
        
    Returns:
        Formatted context for resolving references
    """
    memory = get_global_memory(session_id)
    return memory.get_context_for_question_rewriting(max_turns=max_turns)
