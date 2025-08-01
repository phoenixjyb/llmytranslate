"""
Cross-platform conversation storage and management.
Handles platform-specific paths and storage optimization.
"""
import os
import json
import uuid
import platform
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationMetadata:
    """Metadata for conversation storage."""
    conversation_id: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    model_used: str
    platform: str
    title: Optional[str] = None

class CrossPlatformStorage:
    """Cross-platform storage handler for conversation data."""
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.storage_path = self._get_platform_storage_path()
        self.ensure_storage_directory()
        
    def _detect_platform(self) -> str:
        """Detect current platform."""
        system = platform.system().lower()
        platform_map = {
            "windows": "windows",
            "darwin": "macos",
            "linux": "linux"
        }
        return platform_map.get(system, "unix")
    
    def _get_platform_storage_path(self) -> Path:
        """Get platform-appropriate storage path."""
        app_name = "llmytranslate"
        
        if self.platform == "windows":
            # Windows: %APPDATA%\llmytranslate\conversations
            base_path = Path(os.environ.get("APPDATA", "C:/Users/Default/AppData/Roaming"))
        elif self.platform == "macos":
            # macOS: ~/Library/Application Support/llmytranslate/conversations
            base_path = Path.home() / "Library" / "Application Support"
        else:
            # Linux/Unix: ~/.local/share/llmytranslate/conversations
            base_path = Path.home() / ".local" / "share"
        
        return base_path / app_name / "conversations"
    
    def ensure_storage_directory(self) -> None:
        """Ensure storage directory exists with proper permissions."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Set appropriate permissions for the platform
            if self.platform != "windows":
                # Unix-like systems: owner read/write/execute, group read, others none
                os.chmod(self.storage_path, 0o750)
                
            logger.info(f"Storage directory ensured: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def get_conversation_file_path(self, conversation_id: str) -> Path:
        """Get file path for a specific conversation."""
        return self.storage_path / f"conversation_{conversation_id}.json"
    
    def get_metadata_file_path(self, conversation_id: str) -> Path:
        """Get metadata file path for a conversation."""
        return self.storage_path / f"metadata_{conversation_id}.json"

class ConversationManager:
    """Cross-platform conversation management with optimized storage."""
    
    def __init__(self, max_conversations: int = 100, max_history_per_conversation: int = 50):
        self.max_conversations = max_conversations
        self.max_history_per_conversation = max_history_per_conversation
        self.storage = CrossPlatformStorage()
        
        # In-memory cache for active conversations
        self._active_conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._conversation_metadata: Dict[str, ConversationMetadata] = {}
        
        # Platform-specific optimizations
        self._setup_platform_optimizations()
        
        # Load existing conversations metadata
        self._load_conversations_metadata()
    
    def _setup_platform_optimizations(self) -> None:
        """Setup platform-specific optimizations."""
        if self.storage.platform == "windows":
            # Windows-specific optimizations
            self._use_windows_file_apis = True
            self._enable_file_compression = True
        elif self.storage.platform == "macos":
            # macOS-specific optimizations
            self._use_spotlight_exclusion = True
            self._enable_icloud_sync = False  # Disable for privacy
        else:
            # Linux/Unix optimizations
            self._use_posix_optimizations = True
            self._enable_memory_mapping = True
    
    def _load_conversations_metadata(self) -> None:
        """Load conversation metadata from storage."""
        try:
            metadata_files = list(self.storage.storage_path.glob("metadata_*.json"))
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = ConversationMetadata(
                            conversation_id=data['conversation_id'],
                            created_at=datetime.fromisoformat(data['created_at']),
                            last_message_at=datetime.fromisoformat(data['last_message_at']),
                            message_count=data['message_count'],
                            model_used=data['model_used'],
                            platform=data['platform'],
                            title=data.get('title')
                        )
                        self._conversation_metadata[metadata.conversation_id] = metadata
                except Exception as e:
                    logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
                    
            logger.info(f"Loaded metadata for {len(self._conversation_metadata)} conversations")
        except Exception as e:
            logger.error(f"Failed to load conversations metadata: {e}")
    
    def create_conversation(self, model: str = "gemma3:latest") -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = ConversationMetadata(
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            message_count=0,
            model_used=model,
            platform=self.storage.platform
        )
        
        # Store in memory and persist metadata
        self._active_conversations[conversation_id] = []
        self._conversation_metadata[conversation_id] = metadata
        self._save_conversation_metadata(metadata)
        
        # Cleanup old conversations if needed
        self._cleanup_old_conversations()
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """Add a message to a conversation."""
        if conversation_id not in self._active_conversations:
            # Load conversation from storage if not in memory
            self._load_conversation(conversation_id)
        
        # Add message to in-memory cache
        if conversation_id not in self._active_conversations:
            self._active_conversations[conversation_id] = []
            
        self._active_conversations[conversation_id].append(message)
        
        # Update metadata
        if conversation_id in self._conversation_metadata:
            metadata = self._conversation_metadata[conversation_id]
            metadata.last_message_at = datetime.utcnow()
            metadata.message_count = len(self._active_conversations[conversation_id])
            
            # Auto-generate title from first user message
            if not metadata.title and message.get('role') == 'user':
                content = message.get('content', '')
                metadata.title = content[:50] + "..." if len(content) > 50 else content
            
            self._save_conversation_metadata(metadata)
        
        # Persist conversation to storage
        self._save_conversation(conversation_id)
        
        # Trim conversation if too long
        self._trim_conversation_if_needed(conversation_id)
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if conversation_id not in self._active_conversations:
            self._load_conversation(conversation_id)
        
        return self._active_conversations.get(conversation_id, [])
    
    def get_conversation_context(self, conversation_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context for AI processing."""
        conversation = self.get_conversation(conversation_id)
        return conversation[-max_messages:] if conversation else []
    
    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent conversations with metadata."""
        conversations = []
        
        # Sort by last message time
        sorted_metadata = sorted(
            self._conversation_metadata.values(),
            key=lambda x: x.last_message_at,
            reverse=True
        )
        
        for metadata in sorted_metadata[:limit]:
            conversations.append({
                "conversation_id": metadata.conversation_id,
                "title": metadata.title or f"Conversation {metadata.conversation_id[:8]}",
                "created_at": metadata.created_at.isoformat(),
                "last_message_at": metadata.last_message_at.isoformat(),
                "message_count": metadata.message_count,
                "model_used": metadata.model_used,
                "platform": metadata.platform
            })
        
        return conversations
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a specific conversation."""
        try:
            # Remove from memory
            if conversation_id in self._active_conversations:
                del self._active_conversations[conversation_id]
            
            if conversation_id in self._conversation_metadata:
                del self._conversation_metadata[conversation_id]
            
            # Remove from storage
            conversation_file = self.storage.get_conversation_file_path(conversation_id)
            metadata_file = self.storage.get_metadata_file_path(conversation_id)
            
            if conversation_file.exists():
                conversation_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Cleared conversation: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear conversation {conversation_id}: {e}")
            return False
    
    def save_conversation(self, conversation_id: str) -> bool:
        """Public method to save a conversation to persistent storage."""
        try:
            if conversation_id in self._active_conversations:
                self._save_conversation(conversation_id)
                return True
            else:
                logger.warning(f"Conversation {conversation_id} not found in active conversations")
                return False
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation_id}: {e}")
            return False
    
    def cleanup_expired_conversations(self, max_age_hours: int = 24) -> int:
        """Cleanup conversations older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_conversations = []
        
        for conv_id, metadata in self._conversation_metadata.items():
            if metadata.last_message_at < cutoff_time:
                expired_conversations.append(conv_id)
        
        for conv_id in expired_conversations:
            self.clear_conversation(conv_id)
        
        logger.info(f"Cleaned up {len(expired_conversations)} expired conversations")
        return len(expired_conversations)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information and statistics."""
        try:
            storage_size = sum(
                f.stat().st_size for f in self.storage.storage_path.rglob('*') if f.is_file()
            )
            
            return {
                "platform": self.storage.platform,
                "storage_path": str(self.storage.storage_path),
                "total_conversations": len(self._conversation_metadata),
                "active_in_memory": len(self._active_conversations),
                "storage_size_bytes": storage_size,
                "storage_size_mb": round(storage_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {"error": str(e)}
    
    def _load_conversation(self, conversation_id: str) -> None:
        """Load conversation from storage into memory."""
        try:
            conversation_file = self.storage.get_conversation_file_path(conversation_id)
            
            if conversation_file.exists():
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                    self._active_conversations[conversation_id] = conversation_data.get('messages', [])
                    logger.debug(f"Loaded conversation {conversation_id} from storage")
            else:
                logger.warning(f"Conversation file not found: {conversation_file}")
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
    
    def _save_conversation(self, conversation_id: str) -> None:
        """Save conversation to storage."""
        try:
            conversation_file = self.storage.get_conversation_file_path(conversation_id)
            conversation_data = {
                "conversation_id": conversation_id,
                "messages": self._active_conversations.get(conversation_id, []),
                "platform": self.storage.platform,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation_id}: {e}")
    
    def _save_conversation_metadata(self, metadata: ConversationMetadata) -> None:
        """Save conversation metadata to storage."""
        try:
            metadata_file = self.storage.get_metadata_file_path(metadata.conversation_id)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, default=str, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metadata for {metadata.conversation_id}: {e}")
    
    def _trim_conversation_if_needed(self, conversation_id: str) -> None:
        """Trim conversation if it exceeds maximum history length."""
        if conversation_id in self._active_conversations:
            messages = self._active_conversations[conversation_id]
            
            if len(messages) > self.max_history_per_conversation:
                # Keep the most recent messages
                trimmed_messages = messages[-self.max_history_per_conversation:]
                self._active_conversations[conversation_id] = trimmed_messages
                
                # Update metadata
                if conversation_id in self._conversation_metadata:
                    self._conversation_metadata[conversation_id].message_count = len(trimmed_messages)
                
                # Save trimmed conversation
                self._save_conversation(conversation_id)
                logger.info(f"Trimmed conversation {conversation_id} to {len(trimmed_messages)} messages")
    
    def _cleanup_old_conversations(self) -> None:
        """Cleanup old conversations if we exceed the maximum."""
        if len(self._conversation_metadata) > self.max_conversations:
            # Sort by last message time and remove oldest
            sorted_conversations = sorted(
                self._conversation_metadata.items(),
                key=lambda x: x[1].last_message_at
            )
            
            # Remove oldest conversations
            to_remove = len(self._conversation_metadata) - self.max_conversations
            for i in range(to_remove):
                conv_id = sorted_conversations[i][0]
                self.clear_conversation(conv_id)
                
            logger.info(f"Cleaned up {to_remove} old conversations")
