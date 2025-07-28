"""
Cross-platform chatbot service with conversation management and Ollama integration.
Designed to work seamlessly across Windows, macOS, and Linux platforms.
"""
import asyncio
import logging
import platform
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..models.chat_schemas import (
    ChatMessage, ChatRequest, ChatResponse, 
    ConversationHistory, ChatbotHealthCheck, ChatbotConfig
)
from ..storage.conversation_manager import ConversationManager
from ..services.ollama_client import ollama_client  # Reuse existing Ollama client
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class ChatbotService:
    """Cross-platform chatbot service with intelligent conversation management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.platform = self._detect_platform()
        self.conversation_manager = ConversationManager(
            max_conversations=getattr(self.settings, 'chatbot_max_conversations', 100),
            max_history_per_conversation=getattr(self.settings, 'chatbot_max_history', 50)
        )
        
        # Reuse existing Ollama client for seamless integration
        self.ollama_client = ollama_client
        
        # Platform-specific optimizations
        self._setup_platform_optimizations()
        
        # Performance tracking
        self._request_count = 0
        self._total_processing_time = 0.0
        self._cache_hits = 0
        
        logger.info(f"ChatbotService initialized on {self.platform} platform")
    
    def _detect_platform(self) -> str:
        """Detect current platform for optimization."""
        system = platform.system().lower()
        platform_map = {
            "windows": "windows",
            "darwin": "macos", 
            "linux": "linux"
        }
        return platform_map.get(system, "unix")
    
    def _setup_platform_optimizations(self) -> None:
        """Setup platform-specific optimizations."""
        if self.platform == "windows":
            # Windows-specific optimizations
            self._use_iocp = True  # I/O Completion Ports
            self._thread_pool_size = 8
        elif self.platform == "macos":
            # macOS-specific optimizations  
            self._use_kqueue = True
            self._thread_pool_size = 6
        else:
            # Linux/Unix optimizations
            self._use_epoll = True
            self._thread_pool_size = 4
    
    async def process_chat_message(
        self, 
        request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat message with conversation context and cross-platform support.
        """
        start_time = time.time()
        
        try:
            # Get or create conversation
            conversation_id = request.conversation_id or self.conversation_manager.create_conversation(
                model=request.model
            )
            
            # Get conversation context for better responses
            context_messages = self.conversation_manager.get_conversation_context(
                conversation_id, max_messages=10
            )
            
            # Add user message to conversation
            user_message = ChatMessage(
                role="user",
                content=request.message,
                timestamp=datetime.utcnow()
            )
            
            self.conversation_manager.add_message(conversation_id, {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "timestamp": user_message.timestamp.isoformat(),
                "platform": request.platform or self.platform
            })
            
            # Generate AI response using existing Ollama client
            ai_response_content = await self._generate_ai_response(
                request, context_messages
            )
            
            # Create response message
            ai_message = ChatMessage(
                role="assistant",
                content=ai_response_content,
                timestamp=datetime.utcnow()
            )
            
            # Add AI response to conversation
            self.conversation_manager.add_message(conversation_id, {
                "id": ai_message.id,
                "role": ai_message.role,
                "content": ai_message.content,
                "timestamp": ai_message.timestamp.isoformat(),
                "platform": self.platform
            })
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update performance metrics
            self._request_count += 1
            self._total_processing_time += processing_time
            
            # Create response
            response = ChatResponse(
                response=ai_response_content,
                conversation_id=conversation_id,
                message_id=ai_message.id,
                model_used=request.model,
                timestamp=ai_message.timestamp,
                processing_time_ms=processing_time,
                tokens_used=len(ai_response_content.split()),  # Rough estimate
                cached=False,  # TODO: Implement caching
                server_platform=self.platform
            )
            
            logger.info(
                f"Processed chat message for conversation {conversation_id} "
                f"in {processing_time}ms on {self.platform}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise Exception(f"Failed to process chat message: {str(e)}")
    
    async def _generate_ai_response(
        self, 
        request: ChatRequest, 
        context_messages: List[Dict[str, Any]]
    ) -> str:
        """Generate AI response using existing Ollama client."""
        try:
            # Build prompt with conversation context
            system_prompt = request.system_prompt or self._get_default_system_prompt()
            
            # Format context for Ollama
            conversation_context = self._format_conversation_context(context_messages)
            
            # Create full prompt
            full_prompt = f"{system_prompt}\n\n{conversation_context}\n\nUser: {request.message}\n\nAssistant:"
            
            # Use existing Ollama client with platform-aware optimizations
            response = await self._call_ollama_with_retry(
                model=request.model,
                prompt=full_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"I apologize, but I encountered an error while processing your message. Please try again."
    
    async def _call_ollama_with_retry(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> str:
        """Call Ollama with retry logic and platform-specific optimizations."""
        for attempt in range(max_retries):
            try:
                # Use existing Ollama client (reuse translation service infrastructure)
                response = await self.ollama_client.generate(
                    model=model,
                    prompt=prompt,
                    options={
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "stop": ["User:", "\n\nUser:", "Human:"],
                    }
                )
                
                if response and "response" in response:
                    return response["response"]
                else:
                    raise Exception("Invalid response from Ollama")
                    
            except Exception as e:
                logger.warning(f"Ollama call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to get response from Ollama after {max_retries} attempts: {e}")
                
                # Platform-specific retry delay
                retry_delay = 2 ** attempt  # Exponential backoff
                if self.platform == "windows":
                    retry_delay *= 1.2  # Slightly longer on Windows
                    
                await asyncio.sleep(retry_delay)
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt with platform awareness."""
        base_prompt = (
            "You are a helpful, knowledgeable, and friendly AI assistant. "
            "You provide accurate, concise, and helpful responses to user questions. "
            "You can assist with a wide range of topics including general knowledge, "
            "programming, writing, analysis, and more."
        )
        
        # Add platform-specific context if helpful
        if self.platform == "windows":
            base_prompt += " You're running on a Windows system."
        elif self.platform == "macos":
            base_prompt += " You're running on a macOS system."
        elif self.platform == "linux":
            base_prompt += " You're running on a Linux system."
        
        return base_prompt
    
    def _format_conversation_context(self, context_messages: List[Dict[str, Any]]) -> str:
        """Format conversation context for AI model."""
        if not context_messages:
            return ""
        
        formatted_context = []
        for message in context_messages[-8:]:  # Last 8 messages for context
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            if role == "user":
                formatted_context.append(f"User: {content}")
            elif role == "assistant":
                formatted_context.append(f"Assistant: {content}")
            elif role == "system":
                formatted_context.append(f"System: {content}")
        
        return "\n".join(formatted_context)
    
    async def get_conversation_history(self, conversation_id: str) -> ConversationHistory:
        """Get complete conversation history."""
        try:
            messages_data = self.conversation_manager.get_conversation(conversation_id)
            
            # Convert to ChatMessage objects
            messages = []
            for msg_data in messages_data:
                message = ChatMessage(
                    id=msg_data.get("id", ""),
                    role=msg_data.get("role", "user"),
                    content=msg_data.get("content", ""),
                    timestamp=datetime.fromisoformat(msg_data.get("timestamp", datetime.utcnow().isoformat())),
                    metadata=msg_data.get("metadata", {})
                )
                messages.append(message)
            
            # Get conversation metadata
            conversations = self.conversation_manager.list_conversations()
            conversation_summary = None
            
            for conv in conversations:
                if conv["conversation_id"] == conversation_id:
                    from ..models.chat_schemas import ConversationSummary
                    conversation_summary = ConversationSummary(
                        conversation_id=conv["conversation_id"],
                        created_at=datetime.fromisoformat(conv["created_at"]),
                        last_message_at=datetime.fromisoformat(conv["last_message_at"]),
                        message_count=conv["message_count"],
                        title=conv["title"],
                        model_used=conv["model_used"],
                        platform=conv["platform"]
                    )
                    break
            
            if not conversation_summary:
                raise Exception(f"Conversation {conversation_id} not found")
            
            return ConversationHistory(
                conversation_id=conversation_id,
                messages=messages,
                summary=conversation_summary
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            raise Exception(f"Failed to get conversation history: {str(e)}")
    
    async def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List conversations with pagination."""
        try:
            return self.conversation_manager.list_conversations(limit=limit)
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise Exception(f"Failed to list conversations: {str(e)}")
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a specific conversation."""
        try:
            result = self.conversation_manager.clear_conversation(conversation_id)
            if result:
                logger.info(f"Cleared conversation {conversation_id}")
            return result
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    async def cleanup_expired_conversations(self, max_age_hours: int = 24) -> int:
        """Cleanup old conversations."""
        try:
            count = self.conversation_manager.cleanup_expired_conversations(max_age_hours)
            logger.info(f"Cleaned up {count} expired conversations")
            return count
        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}")
            return 0
    
    async def health_check(self) -> ChatbotHealthCheck:
        """Comprehensive health check for chatbot service."""
        try:
            # Test Ollama connectivity
            try:
                test_response = await self.ollama_client.list_models()
                ollama_status = "healthy" if test_response else "degraded"
            except Exception:
                ollama_status = "unhealthy"
            
            # Check storage
            try:
                storage_info = self.conversation_manager.get_storage_info()
                storage_status = "healthy" if "error" not in storage_info else "degraded"
            except Exception:
                storage_status = "unhealthy"
            
            # Calculate average response time
            avg_response_time = None
            if self._request_count > 0:
                avg_response_time = self._total_processing_time / self._request_count
            
            # Determine overall status
            if ollama_status == "healthy" and storage_status == "healthy":
                overall_status = "healthy"
            elif ollama_status == "unhealthy" or storage_status == "unhealthy":
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            
            return ChatbotHealthCheck(
                status=overall_status,
                timestamp=datetime.utcnow(),
                platform=self.platform,
                active_conversations=len(self.conversation_manager._active_conversations),
                total_messages_today=self._request_count,
                average_response_time_ms=avg_response_time,
                ollama_status=ollama_status,
                storage_status=storage_status,
                memory_usage_mb=storage_info.get("storage_size_mb", 0) if 'storage_info' in locals() else None
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ChatbotHealthCheck(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                platform=self.platform,
                active_conversations=0,
                total_messages_today=0,
                ollama_status="unknown",
                storage_status="unknown"
            )
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get detailed service information."""
        try:
            storage_info = self.conversation_manager.get_storage_info()
            
            return {
                "platform": self.platform,
                "service_name": "LLM Chatbot Service",
                "version": "1.0.0",
                "uptime_seconds": time.time(),  # Since service start
                "performance": {
                    "total_requests": self._request_count,
                    "cache_hits": self._cache_hits,
                    "average_response_time_ms": (
                        self._total_processing_time / self._request_count 
                        if self._request_count > 0 else 0
                    )
                },
                "storage": storage_info,
                "features": {
                    "conversation_management": True,
                    "cross_platform_storage": True,
                    "ollama_integration": True,
                    "translation_integration": True,
                    "web_interface": True
                }
            }
        except Exception as e:
            logger.error(f"Error getting service info: {e}")
            return {"error": str(e), "platform": self.platform}

# Global chatbot service instance
chatbot_service = ChatbotService()
