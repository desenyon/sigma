"""Conversation state management for efficient context handling."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MessageRole(Enum):
    """Role of a message in the conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Record of a tool call."""
    id: str
    name: str
    args: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass 
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to LLM-compatible format."""
        d = {
            "role": self.role.value,
            "content": self.content
        }
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "args": tc.args}
                for tc in self.tool_calls
            ]
        return d


class ConversationState:
    """Manages conversation history and context window."""
    
    def __init__(self, max_messages: int = 50, max_tokens: int = 8000):
        self.messages: List[Message] = []
        self.tool_history: List[ToolCall] = []
        self.metadata: Dict[str, Any] = {}
        self._max_messages = max_messages
        self._max_tokens = max_tokens
        self._created_at = datetime.now()
        
    def add_message(
        self, 
        role: MessageRole, 
        content: str, 
        tool_calls: List[ToolCall] = None,
        metadata: Dict[str, Any] = None
    ) -> Message:
        """Add a message to the conversation."""
        msg = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            metadata=metadata or {}
        )
        self.messages.append(msg)
        
        if tool_calls:
            self.tool_history.extend(tool_calls)
        
        if len(self.messages) > self._max_messages:
            self._prune_old_messages()
            
        return msg
    
    def add_user_message(self, content: str) -> Message:
        """Add a user message."""
        return self.add_message(MessageRole.USER, content)
    
    def add_assistant_message(
        self, 
        content: str, 
        tool_calls: List[ToolCall] = None
    ) -> Message:
        """Add an assistant message."""
        return self.add_message(MessageRole.ASSISTANT, content, tool_calls)
    
    def add_tool_result(self, tool_call_id: str, result: Any) -> Message:
        """Add a tool result message."""
        content = json.dumps(result) if not isinstance(result, str) else result
        return self.add_message(
            MessageRole.TOOL, 
            content,
            metadata={"tool_call_id": tool_call_id}
        )
    
    def get_context_window(
        self, 
        include_system: bool = True,
        max_messages: int = None
    ) -> List[Dict[str, str]]:
        """Get messages formatted for LLM context."""
        messages = []
        
        if include_system and self.metadata.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": self.metadata["system_prompt"]
            })
        
        limit = max_messages or self._max_messages
        recent = self.messages[-limit:]
        
        for msg in recent:
            messages.append(msg.to_dict())
            
        return messages
    
    def get_last_user_query(self) -> Optional[str]:
        """Get the most recent user message."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER:
                return msg.content
        return None
    
    def get_last_assistant_response(self) -> Optional[str]:
        """Get the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg.content
        return None
    
    def clear(self):
        """Clear the conversation."""
        self.messages = []
        self.tool_history = []
        
    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation to JSON-serializable format."""
        return {
            "created_at": self._created_at.isoformat(),
            "message_count": len(self.messages),
            "tool_calls": len(self.tool_history),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "tool_calls": [
                        {"name": tc.name, "duration_ms": tc.duration_ms}
                        for tc in msg.tool_calls
                    ]
                }
                for msg in self.messages
            ],
            "metadata": self.metadata
        }
    
    def _prune_old_messages(self):
        """Remove old messages while keeping context coherent."""
        keep_count = self._max_messages // 2
        if self.messages[0].role == MessageRole.SYSTEM:
            self.messages = [self.messages[0]] + self.messages[-keep_count:]
        else:
            self.messages = self.messages[-keep_count:]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        user_count = sum(1 for m in self.messages if m.role == MessageRole.USER)
        assistant_count = sum(1 for m in self.messages if m.role == MessageRole.ASSISTANT)
        tool_count = len(self.tool_history)
        
        total_chars = sum(len(m.content) for m in self.messages)
        
        return {
            "total_messages": len(self.messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "tool_calls": tool_count,
            "total_characters": total_chars,
            "duration_minutes": (datetime.now() - self._created_at).seconds / 60
        }


class ConversationManager:
    """Manages multiple conversations."""
    
    def __init__(self):
        self._conversations: Dict[str, ConversationState] = {}
        self._active_id: Optional[str] = None
        
    def create_conversation(self, conversation_id: str = None) -> ConversationState:
        """Create a new conversation."""
        import uuid
        cid = conversation_id or str(uuid.uuid4())[:8]
        self._conversations[cid] = ConversationState()
        self._active_id = cid
        return self._conversations[cid]
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)
    
    def get_active(self) -> Optional[ConversationState]:
        """Get the active conversation."""
        if self._active_id:
            return self._conversations.get(self._active_id)
        return None
    
    def set_active(self, conversation_id: str) -> bool:
        """Set the active conversation."""
        if conversation_id in self._conversations:
            self._active_id = conversation_id
            return True
        return False
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs."""
        return list(self._conversations.keys())
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            if self._active_id == conversation_id:
                self._active_id = None
            return True
        return False
