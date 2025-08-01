"""
File processing service for image recognition and document analysis.
"""
import asyncio
import base64
import io
import time
import tempfile
import os
from typing import Optional, Dict, Any, List, Tuple
import httpx
from PIL import Image
import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for Word documents
from structlog import get_logger
from fastapi import HTTPException

from ..core.config import get_settings
from ..models.file_schemas import (
    FileUpload, ImageAnalysisRequest, DocumentProcessingRequest, 
    FileAnalysisResponse, ChatWithFileRequest
)
from .ollama_client import ollama_client

logger = get_logger(__name__)


class FileProcessingService:
    """Service for processing uploaded files with AI analysis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        self.supported_doc_formats = {'.pdf', '.txt', '.md', '.doc', '.docx'}
        
    async def validate_file(self, file_upload: FileUpload) -> Tuple[bool, str]:
        """Validate uploaded file."""
        try:
            # Check file size
            if file_upload.file_size > self.max_file_size:
                return False, f"File size {file_upload.file_size} bytes exceeds maximum {self.max_file_size} bytes"
            
            # Check content type
            if file_upload.file_category not in ['image', 'document']:
                return False, f"Unsupported file category: {file_upload.file_category}"
            
            # Validate base64 data
            try:
                file_data = base64.b64decode(file_upload.file_data)
                if len(file_data) != file_upload.file_size:
                    return False, "File size mismatch with encoded data"
            except Exception as e:
                return False, f"Invalid base64 encoding: {str(e)}"
            
            return True, "File validation successful"
            
        except Exception as e:
            logger.error("File validation error", error=str(e))
            return False, f"Validation error: {str(e)}"
    
    async def analyze_image(self, request: ImageAnalysisRequest) -> FileAnalysisResponse:
        """Analyze image using vision model."""
        start_time = time.time()
        
        try:
            # Validate file
            is_valid, validation_msg = await self.validate_file(request.file_upload)
            if not is_valid:
                raise ValueError(validation_msg)
            
            # Decode image data
            image_data = base64.b64decode(request.file_upload.file_data)
            
            # Prepare image for vision model
            image_base64 = request.file_upload.file_data
            
            # Prepare prompt based on analysis type
            prompt = self._prepare_image_prompt(request.prompt, request.analysis_type)
            
            # Call vision model
            vision_response = await ollama_client.generate_vision(
                model=request.model,
                prompt=prompt,
                image_base64=image_base64,
                max_tokens=request.max_tokens
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract additional metadata
            image_info = self._extract_image_metadata(image_data)
            
            return FileAnalysisResponse(
                file_id=request.file_upload.file_id,
                analysis_result=vision_response.get('response', ''),
                file_info={
                    'filename': request.file_upload.filename,
                    'content_type': request.file_upload.content_type,
                    'file_size': request.file_upload.file_size,
                    'dimensions': image_info.get('dimensions'),
                    'format': image_info.get('format')
                },
                model_used=request.model,
                processing_time_ms=processing_time,
                confidence_score=vision_response.get('confidence'),
                detected_language=self._detect_language(vision_response.get('response', ''))
            )
            
        except Exception as e:
            logger.error("Image analysis error", error=str(e), file_id=request.file_upload.file_id)
            raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")
    
    async def process_document(self, request: DocumentProcessingRequest) -> FileAnalysisResponse:
        """Process document and extract/analyze content."""
        start_time = time.time()
        
        try:
            # Validate file
            is_valid, validation_msg = await self.validate_file(request.file_upload)
            if not is_valid:
                raise ValueError(validation_msg)
            
            # Extract text from document
            extracted_text = await self._extract_document_text(request.file_upload)
            
            # Prepare prompt for text analysis
            prompt = self._prepare_document_prompt(
                extracted_text, 
                request.prompt, 
                request.processing_type,
                request.target_language
            )
            
            # Analyze with text model
            analysis_response = await ollama_client.generate_text(
                model=request.model,
                prompt=prompt,
                max_tokens=2000
            )
            
            # Extract analysis result with fallback
            analysis_result = ""
            if analysis_response and isinstance(analysis_response, dict):
                analysis_result = analysis_response.get('response', '')
                if not analysis_result:
                    analysis_result = f"Analysis completed but no response text available. Raw response: {analysis_response}"
            else:
                analysis_result = f"Analysis failed - unexpected response format: {analysis_response}"
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return FileAnalysisResponse(
                file_id=request.file_upload.file_id,
                analysis_result=analysis_result,
                file_info={
                    'filename': request.file_upload.filename,
                    'content_type': request.file_upload.content_type,
                    'file_size': request.file_upload.file_size,
                    'text_length': len(extracted_text),
                    'processing_type': request.processing_type
                },
                model_used=request.model,
                processing_time_ms=processing_time,
                extracted_text=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                detected_language=self._detect_language(extracted_text)
            )
            
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}, file_id: {request.file_upload.file_id}")
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
    
    async def chat_with_files(self, request: ChatWithFileRequest) -> Dict[str, Any]:
        """Process chat message with file attachments."""
        start_time = time.time()
        file_analyses = []
        
        try:
            # Process each attached file
            if request.files and request.auto_analyze_files:
                for file_upload in request.files:
                    if file_upload.file_category == 'image':
                        # Analyze image
                        image_request = ImageAnalysisRequest(
                            file_upload=file_upload,
                            prompt="Describe this image in detail for chat context.",
                            analysis_type="describe",
                            model=request.vision_model
                        )
                        analysis = await self.analyze_image(image_request)
                        file_analyses.append({
                            'type': 'image',
                            'filename': file_upload.filename,
                            'analysis': analysis.analysis_result
                        })
                    
                    elif file_upload.file_category == 'document':
                        # Process document
                        doc_request = DocumentProcessingRequest(
                            file_upload=file_upload,
                            processing_type="extract",
                            prompt="Extract and summarize key information for chat context."
                        )
                        analysis = await self.process_document(doc_request)
                        file_analyses.append({
                            'type': 'document',
                            'filename': file_upload.filename,
                            'analysis': analysis.analysis_result,
                            'extracted_text': analysis.extracted_text
                        })
            
            # Prepare enhanced chat prompt with file context
            enhanced_prompt = self._prepare_chat_with_files_prompt(
                request.message, 
                file_analyses
            )
            
            # Generate chat response with file context
            chat_response = await ollama_client.generate_text(
                model=request.model,
                prompt=enhanced_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Extract response with fallback
            response_text = ""
            if chat_response and isinstance(chat_response, dict):
                response_text = chat_response.get('response', '')
                if not response_text:
                    response_text = f"Chat completed but no response text available. File analyses: {len(file_analyses)} files processed."
            else:
                response_text = f"Chat failed - unexpected response format. File analyses: {len(file_analyses)} files processed."
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                'response': response_text,
                'file_analyses': file_analyses,
                'model_used': request.model,
                'processing_time_ms': processing_time,
                'files_processed': len(request.files) if request.files else 0
            }
            
        except Exception as e:
            logger.error(f"Chat with files error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chat with files failed: {str(e)}")
    
    def _prepare_image_prompt(self, user_prompt: str, analysis_type: str) -> str:
        """Prepare prompt for image analysis."""
        base_prompts = {
            'describe': "Analyze this image and provide a detailed description of what you see.",
            'ocr': "Extract and transcribe any text visible in this image.",
            'translate': "Identify and translate any text in this image to English.",
            'question': user_prompt
        }
        
        base = base_prompts.get(analysis_type, base_prompts['describe'])
        
        if user_prompt and analysis_type != 'question':
            return f"{base} {user_prompt}"
        return base
    
    def _prepare_document_prompt(self, text: str, user_prompt: str, processing_type: str, target_language: Optional[str] = None) -> str:
        """Prepare prompt for document processing."""
        base_prompts = {
            'extract': "Extract and organize the key information from this document:",
            'summarize': "Provide a comprehensive summary of this document:",
            'translate': f"Translate this document to {target_language or 'English'}:",
            'question': f"Based on this document, {user_prompt}"
        }
        
        base = base_prompts.get(processing_type, base_prompts['extract'])
        
        # Truncate text if too long
        max_text_length = 8000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "\\n\\n[Document truncated...]"
        
        return f"{base}\\n\\nDocument Content:\\n{text}\\n\\nAnalysis:"
    
    def _prepare_chat_with_files_prompt(self, message: str, file_analyses: List[Dict]) -> str:
        """Prepare enhanced chat prompt with file context."""
        if not file_analyses:
            return message
        
        context_parts = ["Based on the following file analyses, please respond to the user's message:"]
        
        for i, analysis in enumerate(file_analyses, 1):
            context_parts.append(f"\\nFile {i} ({analysis['filename']}):")
            if analysis['type'] == 'image':
                context_parts.append(f"Image Description: {analysis['analysis']}")
            elif analysis['type'] == 'document':
                context_parts.append(f"Document Summary: {analysis['analysis']}")
                if analysis.get('extracted_text'):
                    context_parts.append(f"Extracted Text: {analysis['extracted_text'][:500]}...")
        
        context_parts.append(f"\\nUser Message: {message}")
        context_parts.append("\\nResponse:")
        
        return "\\n".join(context_parts)
    
    def _extract_image_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """Extract metadata from image."""
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                'dimensions': f"{image.width}x{image.height}",
                'format': image.format,
                'mode': image.mode
            }
        except Exception as e:
            logger.warning("Failed to extract image metadata", error=str(e))
            return {}
    
    async def _extract_document_text(self, file_upload: FileUpload) -> str:
        """Extract text content from various document formats."""
        try:
            file_data = base64.b64decode(file_upload.file_data)
            content_type = file_upload.content_type
            
            if content_type == 'application/pdf':
                return await self._extract_pdf_text(file_data)
            elif content_type == 'text/plain':
                return file_data.decode('utf-8')
            elif content_type == 'text/markdown':
                return file_data.decode('utf-8')
            elif 'word' in content_type or content_type.endswith('.docx'):
                return await self._extract_word_text(file_data)
            else:
                # Try to decode as text
                return file_data.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error("Text extraction error", error=str(e))
            return "Error: Could not extract text from document."
    
    async def _extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_data)
                tmp_file.flush()
                
                doc = fitz.open(tmp_file.name)
                text_parts = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_parts.append(page.get_text())
                
                doc.close()
                os.unlink(tmp_file.name)
                
                return "\\n".join(text_parts)
                
        except Exception as e:
            logger.error("PDF text extraction error", error=str(e))
            return "Error: Could not extract text from PDF."
    
    async def _extract_word_text(self, doc_data: bytes) -> str:
        """Extract text from Word document."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(doc_data)
                tmp_file.flush()
                
                doc = docx.Document(tmp_file.name)
                text_parts = []
                
                for paragraph in doc.paragraphs:
                    text_parts.append(paragraph.text)
                
                os.unlink(tmp_file.name)
                
                return "\\n".join(text_parts)
                
        except Exception as e:
            logger.error("Word text extraction error", error=str(e))
            return "Error: Could not extract text from Word document."
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Simple language detection (can be enhanced with proper library)."""
        if not text:
            return None
        
        # Simple heuristic for common languages
        chinese_chars = sum(1 for char in text if '\\u4e00' <= char <= '\\u9fff')
        total_chars = len(text)
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return 'zh'
        else:
            return 'en'


# Global service instance
file_processing_service = FileProcessingService()
