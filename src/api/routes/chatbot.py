"""
Cross-platform chatbot API routes with comprehensive conversation management.
Supports Windows, macOS, and Linux platforms with unified interface.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ...models.chat_schemas import (
    ChatRequest, ChatResponse, ConversationHistory, 
    ChatbotHealthCheck, ConversationSummary
)
from ...services.chatbot_service import chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Send a message to the chatbot and get AI response.
    
    Cross-platform support for conversation management with:
    - Windows: APPDATA storage integration
    - macOS: Application Support storage
    - Linux: XDG Base Directory compliance
    """
    try:
        logger.info(f"Processing chat message from {request.platform}")
        response = await chatbot_service.process_chat_message(request)
        return response
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[Dict[str, Any]])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of conversations to return")
):
    """
    List all conversations with metadata.
    
    Returns conversations sorted by last activity (most recent first).
    Includes platform information for cross-platform debugging.
    """
    try:
        conversations = await chatbot_service.list_conversations(limit=limit)
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/history", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str = Path(..., description="Conversation ID to retrieve")
):
    """
    Get complete conversation history for a specific conversation.
    
    Includes all messages with timestamps and platform information.
    """
    try:
        history = await chatbot_service.get_conversation_history(conversation_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get conversation history for {conversation_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str = Path(..., description="Conversation ID to clear")
):
    """
    Clear a specific conversation and its history.
    
    Removes conversation from both memory and cross-platform storage.
    """
    try:
        success = await chatbot_service.clear_conversation(conversation_id)
        if success:
            return {"message": f"Conversation {conversation_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str = Path(..., description="Conversation ID to export"),
    format: str = Query(default="json", regex="^(json|txt|markdown)$", description="Export format")
):
    """
    Export conversation in various formats for cross-platform compatibility.
    
    Supported formats:
    - json: Structured JSON with metadata
    - txt: Plain text format
    - markdown: Markdown formatted conversation
    """
    try:
        history = await chatbot_service.get_conversation_history(conversation_id)
        
        if format == "json":
            return JSONResponse(content=history.dict())
        
        elif format == "txt":
            content = f"Conversation: {history.summary.title or conversation_id}\n"
            content += f"Created: {history.summary.created_at}\n"
            content += f"Platform: {history.summary.platform}\n"
            content += "=" * 50 + "\n\n"
            
            for message in history.messages:
                content += f"[{message.timestamp}] {message.role.upper()}: {message.content}\n\n"
            
            return JSONResponse(
                content={"content": content, "filename": f"conversation_{conversation_id}.txt"},
                headers={"Content-Type": "text/plain"}
            )
        
        elif format == "markdown":
            content = f"# Conversation: {history.summary.title or conversation_id}\n\n"
            content += f"**Created:** {history.summary.created_at}  \n"
            content += f"**Platform:** {history.summary.platform}  \n"
            content += f"**Messages:** {history.summary.message_count}  \n\n"
            content += "---\n\n"
            
            for message in history.messages:
                role_emoji = "👤" if message.role == "user" else "🤖"
                content += f"## {role_emoji} {message.role.title()}\n"
                content += f"*{message.timestamp}*\n\n"
                content += f"{message.content}\n\n"
            
            return JSONResponse(
                content={"content": content, "filename": f"conversation_{conversation_id}.md"},
                headers={"Content-Type": "text/markdown"}
            )
    
    except Exception as e:
        logger.error(f"Failed to export conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/cleanup")
async def cleanup_expired_conversations(
    max_age_hours: int = Query(default=24, ge=1, le=8760, description="Maximum age in hours")
):
    """
    Cleanup conversations older than specified hours.
    
    Cross-platform cleanup that respects storage limitations:
    - Windows: Considers APPDATA quotas
    - macOS: Application Support cleanup
    - Linux: XDG compliance
    """
    try:
        cleaned_count = await chatbot_service.cleanup_expired_conversations(max_age_hours)
        return {
            "message": f"Cleaned up {cleaned_count} expired conversations",
            "max_age_hours": max_age_hours,
            "cleaned_count": cleaned_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=ChatbotHealthCheck)
async def chatbot_health_check():
    """
    Comprehensive health check for chatbot service.
    
    Platform-specific health information including:
    - Storage availability and usage
    - Ollama connectivity status
    - Platform-specific optimizations status
    """
    try:
        health = await chatbot_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Chatbot health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
async def get_chatbot_info():
    """
    Get detailed chatbot service information.
    
    Includes platform detection, performance metrics, and feature availability.
    """
    try:
        info = chatbot_service.get_service_info()
        return info
    except Exception as e:
        logger.error(f"Failed to get chatbot info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/info")
async def get_storage_info():
    """
    Get cross-platform storage information and statistics.
    
    Platform-specific storage details:
    - Windows: APPDATA usage and paths
    - macOS: Application Support details
    - Linux: XDG Base Directory information
    """
    try:
        storage_info = chatbot_service.conversation_manager.get_storage_info()
        return storage_info
    except Exception as e:
        logger.error(f"Failed to get storage info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/new")
async def create_new_conversation(
    model: str = Query(default="gemma2:latest", description="LLM model to use for this conversation"),
    title: Optional[str] = Query(default=None, description="Optional conversation title")
):
    """
    Create a new conversation with optional title and model selection.
    
    Cross-platform conversation initialization with platform-appropriate storage.
    """
    try:
        conversation_id = chatbot_service.conversation_manager.create_conversation(model=model)
        
        # Set title if provided
        if title and conversation_id in chatbot_service.conversation_manager._conversation_metadata:
            chatbot_service.conversation_manager._conversation_metadata[conversation_id].title = title
            chatbot_service.conversation_manager._save_conversation_metadata(
                chatbot_service.conversation_manager._conversation_metadata[conversation_id]
            )
        
        return {
            "conversation_id": conversation_id,
            "model": model,
            "title": title,
            "created_at": datetime.utcnow().isoformat(),
            "platform": chatbot_service.platform
        }
    except Exception as e:
        logger.error(f"Failed to create new conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_available_models():
    """
    List available LLM models from Ollama with cross-platform compatibility.
    
    Returns models available on the current platform with size and capability information.
    """
    try:
        # Use existing Ollama client to get available models
        models = await chatbot_service.ollama_client.list_models()
        
        # Format models for chatbot use
        formatted_models = []
        if models and "models" in models:
            for model in models["models"]:
                formatted_models.append({
                    "name": model.get("name", ""),
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                    "digest": model.get("digest", ""),
                    "platform_compatible": True,  # All models work cross-platform
                    "recommended_for_chat": model.get("name", "").startswith(("llama", "gemma", "mistral"))
                })
        
        return {
            "models": formatted_models,
            "total_count": len(formatted_models),
            "platform": chatbot_service.platform,
            "ollama_status": "available" if formatted_models else "no_models"
        }
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Platform-specific endpoints for advanced features

@router.get("/platform/capabilities")
async def get_platform_capabilities():
    """
    Get platform-specific capabilities and optimizations.
    
    Returns information about what features are available on the current platform.
    """
    try:
        platform = chatbot_service.platform
        
        capabilities = {
            "platform": platform,
            "storage_type": "file_system",
            "conversation_persistence": True,
            "cross_platform_sync": False,  # Future feature
            "export_formats": ["json", "txt", "markdown"],
            "import_formats": ["json"],
            "notification_support": False,
            "background_processing": True
        }
        
        # Platform-specific capabilities
        if platform == "windows":
            capabilities.update({
                "windows_service_integration": False,  # Future feature
                "event_viewer_logging": False,
                "registry_settings": False
            })
        elif platform == "macos":
            capabilities.update({
                "spotlight_integration": False,  # Future feature
                "keychain_integration": False,
                "macos_notifications": False
            })
        else:  # Linux/Unix
            capabilities.update({
                "systemd_integration": False,  # Future feature
                "desktop_notifications": False,
                "xdg_compliance": True
            })
        
        return capabilities
    except Exception as e:
        logger.error(f"Failed to get platform capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
