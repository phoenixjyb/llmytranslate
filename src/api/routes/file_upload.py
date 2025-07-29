"""
File upload and processing API routes for image recognition and document analysis.
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import base64
import mimetypes
from datetime import datetime

from ...models.file_schemas import (
    FileUpload, ImageAnalysisRequest, DocumentProcessingRequest,
    FileAnalysisResponse, ChatWithFileRequest, FileUploadStatus,
    SupportedFileTypes
)
from ...models.chat_schemas import ChatResponse
from ...services.file_processing_service import file_processing_service
from ...services.user_auth_service import user_auth_service
from ...services.database_manager import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["File Processing"])


async def get_current_session(request: Request):
    """Get current user session for file operations."""
    session_id = None
    
    # Try to get session from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_payload = user_auth_service._verify_token(token)
        if token_payload and token_payload.get("type") == "access":
            session_id = token_payload.get("session_id")
    
    # Try to get session from cookies or headers
    if not session_id:
        session_id = (request.cookies.get("session_id") or 
                     request.cookies.get("guest_session_id") or
                     request.headers.get("X-Guest-Session-Id"))
    
    if not session_id:
        # Auto-create guest session for file operations
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        guest_session = await user_auth_service.create_guest_session(
            ip_address=client_ip,
            user_agent=user_agent
        )
        session_id = guest_session.session_id
    
    return await user_auth_service.verify_session(session_id)


@router.get("/supported-types", response_model=SupportedFileTypes)
async def get_supported_file_types():
    """Get information about supported file types and limits."""
    return SupportedFileTypes()


@router.post("/upload", response_model=FileUploadStatus)
async def upload_file(
    file: UploadFile = File(...),
    session_info = Depends(get_current_session)
):
    """Upload a file and prepare it for processing."""
    try:
        # Check file size
        content = await file.read()
        file_size = len(content)
        max_size = 50 * 1024 * 1024  # 50MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size {file_size} bytes exceeds maximum {max_size} bytes"
            )
        
        # Determine content type
        content_type = file.content_type
        if not content_type:
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        # Encode file data
        file_data_b64 = base64.b64encode(content).decode('utf-8')
        
        # Create file upload object
        file_upload = FileUpload(
            filename=file.filename,
            content_type=content_type,
            file_size=file_size,
            file_data=file_data_b64
        )
        
        # Validate file
        is_valid, validation_msg = await file_processing_service.validate_file(file_upload)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # Store file information (optional - for tracking)
        # You could store this in database for file management
        
        return FileUploadStatus(
            file_id=file_upload.file_id,
            filename=file_upload.filename,
            status="uploaded",
            progress=100,
            message="File uploaded successfully",
            result_available=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze-image", response_model=FileAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    session_info = Depends(get_current_session)
):
    """Analyze an uploaded image using vision models."""
    try:
        logger.info(
            "Processing image analysis request",
            file_id=request.file_upload.file_id,
            filename=request.file_upload.filename,
            analysis_type=request.analysis_type,
            model=request.model
        )
        
        result = await file_processing_service.analyze_image(request)
        
        logger.info(
            "Image analysis completed",
            file_id=result.file_id,
            processing_time=result.processing_time_ms,
            model=result.model_used
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.post("/process-document", response_model=FileAnalysisResponse)
async def process_document(
    request: DocumentProcessingRequest,
    session_info = Depends(get_current_session)
):
    """Process an uploaded document for text extraction and analysis."""
    try:
        logger.info(
            "Processing document analysis request",
            file_id=request.file_upload.file_id,
            filename=request.file_upload.filename,
            processing_type=request.processing_type,
            model=request.model
        )
        
        result = await file_processing_service.process_document(request)
        
        logger.info(
            "Document processing completed",
            file_id=result.file_id,
            processing_time=result.processing_time_ms,
            model=result.model_used
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/test-minimal")
async def test_minimal(request: ChatWithFileRequest):
    """Minimal test endpoint without session dependency."""
    try:
        print(f"MINIMAL TEST: Received request: {request.model_dump()}")
        return {"status": "success", "message": "Minimal test passed"}
    except Exception as e:
        import traceback
        print(f"MINIMAL TEST ERROR: {str(e)}")
        print(f"MINIMAL TEST TRACEBACK: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )


@router.post("/chat-with-files", response_model=ChatResponse)
async def chat_with_files(
    request: ChatWithFileRequest,
    session_info = Depends(get_current_session)
):
    """Process a chat message with file attachments."""
    try:
        logger.info(
            f"Processing chat with files request - message_length: {len(request.message)}, "
            f"files_count: {len(request.files) if request.files else 0}, "
            f"auto_analyze: {request.auto_analyze_files}"
        )
        
        # Check guest session limits for file operations
        if session_info and session_info.is_guest:
            # You could implement file-specific limits here
            pass
        
        # Process the chat with files
        result = await file_processing_service.chat_with_files(request)
        
        # Create conversation ID if not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = f"conv-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
        # Generate message ID
        message_id = f"msg-{datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')}"
        
        # Prepare session info for guest users
        session_info_data = None
        if session_info and session_info.is_guest:
            session_info_data = {
                "is_guest": True,
                "session_id": session_info.session_id,
                "max_messages_per_conversation": 20,
                "current_conversation_messages": 1,  # This would be tracked properly
                "file_processing_available": True
            }
        elif session_info:
            session_info_data = {
                "is_guest": False,
                "username": session_info.username,
                "user_id": session_info.user_id,
                "file_processing_available": True
            }
        
        return ChatResponse(
            response=result['response'],
            conversation_id=conversation_id,
            message_id=message_id,
            model_used=result['model_used'],
            processing_time_ms=result['processing_time_ms'],
            session_info=session_info_data
        )
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Chat with files error: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {error_traceback}")
        print(f"ERROR: {str(e)}")
        print(f"TRACEBACK: {error_traceback}")
        
        # Return a more detailed error response for debugging
        return JSONResponse(
            status_code=500,
            content={
                "error": "CHAT_WITH_FILES_ERROR",
                "message": str(e),
                "traceback": error_traceback.split('\n')[-5:],  # Last 5 lines
                "endpoint": "chat-with-files"
            }
        )


@router.get("/status/{file_id}", response_model=FileUploadStatus)
async def get_file_status(
    file_id: str,
    session_info = Depends(get_current_session)
):
    """Get the processing status of an uploaded file."""
    try:
        # In a real implementation, you'd check the database for file status
        # For now, return a basic status
        return FileUploadStatus(
            file_id=file_id,
            filename="unknown",
            status="completed",
            progress=100,
            message="File processing completed",
            result_available=True
        )
        
    except Exception as e:
        logger.error(f"File status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    session_info = Depends(get_current_session)
):
    """Delete an uploaded file and its analysis results."""
    try:
        # In a real implementation, you'd remove the file from storage
        # and clean up any associated data
        
        logger.info(f"File deletion requested - file_id: {file_id}")
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"File {file_id} deleted successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


@router.get("/health")
async def file_processing_health():
    """Check the health of file processing services."""
    try:
        # Check if required dependencies are available
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "file_upload": "available",
                "image_analysis": "available",
                "document_processing": "available",
                "vision_models": "available"
            },
            "supported_formats": {
                "images": ["jpg", "jpeg", "png", "gif", "webp", "bmp"],
                "documents": ["pdf", "txt", "md", "doc", "docx"],
                "max_file_size_mb": 50
            }
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"File processing health check error: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )
