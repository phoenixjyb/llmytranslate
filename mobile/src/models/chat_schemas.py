"""
Cross-platform chatbot data models with platform-aware configurations.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import platform
import uuid

class ChatMessage(BaseModel):
    """Individual chat message model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatRequest(BaseModel):
    """Chat request model with cross-platform support."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    model: Optional[str] = Field(default="gemma3:latest", description="LLM model to use")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000, description="Maximum response tokens")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity")
    platform: Optional[str] = Field(default_factory=lambda: platform.system().lower(), description="Client platform")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Hello! Can you help me with Python programming?",
                "conversation_id": "conv-123",
                "model": "gemma3:latest",
                "system_prompt": "You are a helpful programming assistant.",
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }

class ChatResponse(BaseModel):
    """Chat response model with performance metrics."""
    response: str = Field(..., description="AI assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    message_id: str = Field(..., description="Response message identifier")
    model_used: str = Field(..., description="LLM model that generated the response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Performance metrics
    processing_time_ms: Optional[int] = Field(default=None, description="Response generation time")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    cached: Optional[bool] = Field(default=False, description="Whether response was cached")
    
    # Platform information
    server_platform: str = Field(default_factory=lambda: platform.system().lower())
    
    # Session information (optional)
    session_info: Optional[Dict[str, Any]] = Field(default=None, description="Session status and limits")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationSummary(BaseModel):
    """Conversation summary for listing and management."""
    conversation_id: str = Field(..., description="Conversation identifier")
    created_at: datetime = Field(..., description="Conversation creation time")
    last_message_at: datetime = Field(..., description="Last activity time")
    message_count: int = Field(default=0, ge=0, description="Number of messages")
    title: Optional[str] = Field(default=None, description="Conversation title")
    model_used: str = Field(..., description="Primary model used")
    platform: str = Field(default_factory=lambda: platform.system().lower())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationHistory(BaseModel):
    """Complete conversation history."""
    conversation_id: str = Field(..., description="Conversation identifier")
    messages: List[ChatMessage] = Field(default=[], description="All conversation messages")
    summary: ConversationSummary = Field(..., description="Conversation metadata")
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.summary.message_count = len(self.messages)
        self.summary.last_message_at = message.timestamp

class ChatbotHealthCheck(BaseModel):
    """Health check response for chatbot service."""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    platform: str = Field(default_factory=lambda: platform.system().lower())
    
    # Service metrics
    active_conversations: int = Field(default=0, ge=0)
    total_messages_today: int = Field(default=0, ge=0)
    average_response_time_ms: Optional[float] = Field(default=None)
    
    # Platform-specific info
    ollama_status: str = Field(default="unknown")
    storage_status: str = Field(default="unknown")
    memory_usage_mb: Optional[float] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatbotConfig(BaseModel):
    """Cross-platform chatbot configuration."""
    enabled: bool = Field(default=True)
    default_model: str = Field(default="gemma3:latest")
    max_conversations: int = Field(default=100, ge=1, le=1000)
    max_conversation_history: int = Field(default=50, ge=1, le=200)
    conversation_timeout_seconds: int = Field(default=3600, ge=300, le=86400)  # 5 min to 24 hours
    
    # Platform-specific paths (auto-detected if not specified)
    storage_path: Optional[str] = Field(default=None)
    log_path: Optional[str] = Field(default=None)
    
    # Performance settings
    concurrent_conversations: int = Field(default=10, ge=1, le=100)
    response_timeout_seconds: int = Field(default=30, ge=5, le=120)
    memory_limit_mb: int = Field(default=500, ge=100, le=2000)
    
    # Integration settings
    translation_integration: bool = Field(default=True)
    shared_ollama_client: bool = Field(default=True)
    shared_cache: bool = Field(default=True)
    
    # Web interface
    web_interface_enabled: bool = Field(default=True)
    web_port: int = Field(default=8001, ge=1024, le=65535)
    cors_origins: List[str] = Field(default=["*"])
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "default_model": "gemma3:latest",
                "max_conversations": 100,
                "max_conversation_history": 50,
                "conversation_timeout_seconds": 3600,
                "concurrent_conversations": 10,
                "response_timeout_seconds": 30,
                "translation_integration": True,
                "web_interface_enabled": True,
                "web_port": 8001
            }
        }

# Platform-specific model extensions
if platform.system().lower() == "windows":
    class WindowsChatbotConfig(ChatbotConfig):
        """Windows-specific chatbot configuration."""
        windows_service_integration: bool = Field(default=False)
        use_windows_notifications: bool = Field(default=True)
        windows_log_event_viewer: bool = Field(default=False)

elif platform.system().lower() == "darwin":  # macOS
    class MacOSChatbotConfig(ChatbotConfig):
        """macOS-specific chatbot configuration."""
        use_macos_notifications: bool = Field(default=True)
        keychain_integration: bool = Field(default=False)
        spotlight_indexing: bool = Field(default=True)

else:  # Linux and other Unix
    class LinuxChatbotConfig(ChatbotConfig):
        """Linux/Unix-specific chatbot configuration."""
        systemd_integration: bool = Field(default=False)
        use_desktop_notifications: bool = Field(default=True)
        syslog_integration: bool = Field(default=True)
