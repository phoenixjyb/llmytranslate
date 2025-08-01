"""
File upload and processing schemas for chatbot with image recognition.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import uuid
import base64

class FileUpload(BaseModel):
    """File upload model for various file types."""
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., ge=1, le=50*1024*1024, description="File size in bytes (max 50MB)")
    file_data: str = Field(..., description="Base64 encoded file data")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # File categorization
    file_category: Literal["image", "document", "audio", "video", "other"] = Field(..., description="File category")
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate supported content types."""
        supported_types = {
            # Images
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            # Documents
            'application/pdf', 'text/plain', 'text/markdown', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            # Audio
            'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4',
            # Video
            'video/mp4', 'video/avi', 'video/mov', 'video/webm'
        }
        if v not in supported_types:
            raise ValueError(f'Unsupported content type: {v}')
        return v
    
    @validator('file_category', pre=True, always=True)
    def set_file_category(cls, v, values):
        """Automatically set file category based on content type."""
        content_type = values.get('content_type', '')
        
        if content_type.startswith('image/'):
            return 'image'
        elif content_type.startswith('audio/'):
            return 'audio'
        elif content_type.startswith('video/'):
            return 'video'
        elif content_type in ['application/pdf', 'text/plain', 'text/markdown'] or 'document' in content_type:
            return 'document'
        else:
            return 'other'
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ImageAnalysisRequest(BaseModel):
    """Request for image analysis with optional text prompt."""
    file_upload: FileUpload = Field(..., description="Uploaded image file")
    prompt: Optional[str] = Field(default="Describe this image in detail.", description="Analysis prompt")
    analysis_type: Literal["describe", "ocr", "translate", "question"] = Field(default="describe", description="Type of analysis")
    model: Optional[str] = Field(default="llava:latest", description="Vision model to use")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000, description="Maximum response tokens")
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "What objects do you see in this image?",
                "analysis_type": "describe",
                "model": "llava:latest",
                "max_tokens": 1000
            }
        }

class DocumentProcessingRequest(BaseModel):
    """Request for document processing and analysis."""
    file_upload: FileUpload = Field(..., description="Uploaded document file")
    processing_type: Literal["extract", "summarize", "translate", "question"] = Field(default="extract", description="Processing type")
    prompt: Optional[str] = Field(default="Extract and summarize the key information.", description="Processing prompt")
    target_language: Optional[str] = Field(default=None, description="Target language for translation")
    model: Optional[str] = Field(default="gemma3:latest", description="LLM model to use")
    
    class Config:
        schema_extra = {
            "example": {
                "processing_type": "summarize",
                "prompt": "Summarize the main points of this document.",
                "model": "gemma3:latest"
            }
        }

class FileAnalysisResponse(BaseModel):
    """Response from file analysis (image or document)."""
    file_id: str = Field(..., description="File identifier")
    analysis_result: str = Field(..., description="Analysis or processing result")
    file_info: Dict[str, Any] = Field(..., description="File metadata")
    model_used: str = Field(..., description="Model used for analysis")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    extracted_text: Optional[str] = Field(default=None, description="Extracted text (for OCR/documents)")
    confidence_score: Optional[float] = Field(default=None, description="Analysis confidence score")
    detected_language: Optional[str] = Field(default=None, description="Detected language")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatWithFileRequest(BaseModel):
    """Chat request that includes file attachments."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    files: Optional[List[FileUpload]] = Field(default=[], description="Attached files")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    model: Optional[str] = Field(default="gemma3:latest", description="LLM model to use")
    vision_model: Optional[str] = Field(default="llava:latest", description="Vision model for images")
    auto_analyze_files: bool = Field(default=True, description="Automatically analyze attached files")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum response tokens")
    temperature: Optional[float] = Field(default=0.7, description="Response creativity")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Can you analyze this image and tell me what you see?",
                "auto_analyze_files": True,
                "model": "gemma3:latest",
                "vision_model": "llava:latest"
            }
        }

class FileUploadStatus(BaseModel):
    """Status of file upload and processing."""
    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    status: Literal["uploaded", "processing", "completed", "failed"] = Field(..., description="Processing status")
    progress: int = Field(default=0, ge=0, le=100, description="Processing progress percentage")
    message: Optional[str] = Field(default=None, description="Status message")
    result_available: bool = Field(default=False, description="Whether analysis result is available")
    
class SupportedFileTypes(BaseModel):
    """Information about supported file types and limits."""
    images: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "webp", "bmp"])
    documents: List[str] = Field(default=["pdf", "txt", "md", "doc", "docx", "xls", "xlsx", "ppt", "pptx"])
    audio: List[str] = Field(default=["mp3", "wav", "ogg", "m4a"])
    video: List[str] = Field(default=["mp4", "avi", "mov", "webm"])
    max_file_size_mb: int = Field(default=50)
    max_files_per_request: int = Field(default=5)
    supported_vision_models: List[str] = Field(default=["llava:latest", "llava:7b", "llava:13b"])
    supported_text_models: List[str] = Field(default=["gemma3:latest", "mistral:latest", "llama3:latest"])
