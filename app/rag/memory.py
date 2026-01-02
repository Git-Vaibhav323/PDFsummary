"""
Lightweight memory system for conversation context.

Key principles:
- Single global chat history
- Used ONLY for follow-up question resolution
- NOT embedded or stored in vector database
- Fast clear_memory() function
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
    """Lightweight, fast conversation memory system."""
    
    def __init__(self, max_history: int = 20):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of messages to keep in memory
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self.created_at = datetime.utcnow().isoformat()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add message to memory.
        
        Args:
            role: 'user' or 'assistant'
            content: Message text
            metadata: Optional metadata
        """
        message = Message(role, content, metadata)
        self.messages.append(message)
        
        # Keep only last N messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        logger.debug(f"Added {role} message. Memory now has {len(self.messages)} messages")
    
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
    
    def get_context_for_question_rewriting(self) -> str:
        """
        Get context string for question rewriting.
        
        Used ONLY to resolve references in follow-up questions.
        
        Returns:
            Formatted context string
        """
        if not self.messages:
            return ""
        
        # Get last few exchanges (user-assistant pairs)
        context_lines = []
        for msg in self.messages[-4:]:  # Last 2 exchanges
            role = msg.role.upper()
            context_lines.append(f"{role}: {msg.content[:200]}")  # Truncate for clarity
        
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


class GlobalMemoryManager:
    """
    Global manager for conversation memory.
    
    Maintains a single memory instance for the application.
    """
    
    _instance: Optional[ConversationMemory] = None
    
    @classmethod
    def get_memory(cls) -> ConversationMemory:
        """
        Get or create global memory instance.
        
        Returns:
            Global ConversationMemory instance
        """
        if cls._instance is None:
            cls._instance = ConversationMemory(max_history=20)
            logger.info("Global memory manager initialized")
        return cls._instance
    
    @classmethod
    def reset_memory(cls):
        """Reset to create new memory instance."""
        if cls._instance:
            cls._instance.clear()
        cls._instance = ConversationMemory(max_history=20)
        logger.info("Global memory reset")
    
    @classmethod
    def clear_memory(cls):
        """Clear all memory (fast clear)."""
        if cls._instance:
            cls._instance.clear()
        else:
            logger.warning("No memory to clear")


def get_global_memory() -> ConversationMemory:
    """
    Convenience function to get global memory.
    
    Returns:
        Global ConversationMemory instance
    """
    return GlobalMemoryManager.get_memory()


def clear_memory():
    """
    Clear all conversation memory instantly.
    
    Clears the global chat history completely.
    """
    GlobalMemoryManager.clear_memory()


def add_to_memory(role: str, content: str, metadata: Optional[Dict] = None):
    """
    Add message to global memory.
    
    Args:
        role: 'user' or 'assistant'
        content: Message text
        metadata: Optional metadata
    """
    memory = get_global_memory()
    memory.add_message(role, content, metadata)


def get_memory_context() -> str:
    """
    Get memory context for question rewriting.
    
    Returns:
        Formatted context for resolving references
    """
    memory = get_global_memory()
    return memory.get_context_for_question_rewriting()
