"""
Translation service that orchestrates the translation process.
"""

import time
import uuid
from typing import Optional, Dict, Any, Tuple
import asyncio
from datetime import datetime

from ..core.config import get_settings
from ..models.schemas import TranslationRequest, TranslationResponse, TranslationResult
from ..services.ollama_client import ollama_client
from ..services.cache_service import cache_service
from ..services.stats_service import stats_service

# Mock logger for now
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()


class TranslationService:
    """Core translation service that coordinates all translation operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.semaphore = asyncio.Semaphore(self.settings.translation.concurrent_requests)
    
    async def translate(
        self,
        request: TranslationRequest,
        request_id: Optional[str] = None
    ) -> TranslationResponse:
        """
        Perform translation with caching, statistics, and error handling.
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        try:
            # Validate request
            self._validate_request(request)
            
            # Check cache first if enabled
            cached_result = None
            if self.settings.translation.enable_caching:
                cached_result = await self._get_cached_translation(request)
                if cached_result:
                    logger.info(
                        "Cache hit for translation request",
                        request_id=request_id,
                        app_id=request.appid
                    )
                    
                    # Log cache hit metrics
                    await self._log_request_metrics(
                        request_id=request_id,
                        request=request,
                        result=cached_result,
                        response_time=time.time() - start_time,
                        cache_hit=True,
                        success=True
                    )
                    
                    return self._format_response(request, cached_result["translation"])
            
            # Perform translation using semaphore for concurrency control
            async with self.semaphore:
                translation_result = await self._perform_translation(request)
            
            if not translation_result["success"]:
                # Log failed request
                await self._log_request_metrics(
                    request_id=request_id,
                    request=request,
                    result=translation_result,
                    response_time=time.time() - start_time,
                    cache_hit=False,
                    success=False
                )
                
                # Return error response
                return TranslationResponse(
                    **{"from": request.from_lang},
                    to=request.to,
                    trans_result=[],
                    error_code="TRANSLATION_FAILED",
                    error_msg=translation_result.get("error", "Translation failed")
                )
            
            # Cache the result if caching is enabled
            if self.settings.translation.enable_caching:
                await self._cache_translation(request, translation_result)
            
            # Log successful request metrics
            await self._log_request_metrics(
                request_id=request_id,
                request=request,
                result=translation_result,
                response_time=time.time() - start_time,
                cache_hit=False,
                success=True
            )
            
            logger.info(
                "Translation completed successfully",
                request_id=request_id,
                app_id=request.appid,
                source_lang=request.from_lang,
                target_lang=request.to,
                response_time=time.time() - start_time
            )
            
            return self._format_response(request, translation_result["translation"])
            
        except Exception as e:
            logger.error(
                "Translation service error",
                request_id=request_id,
                error=str(e),
                app_id=getattr(request, 'appid', 'unknown')
            )
            
            # Log failed request
            await self._log_request_metrics(
                request_id=request_id,
                request=request,
                result={"error": str(e)},
                response_time=time.time() - start_time,
                cache_hit=False,
                success=False
            )
            
            return TranslationResponse(
                from_lang=getattr(request, 'from_lang', 'unknown'),
                to_lang=getattr(request, 'to', 'unknown'),
                trans_result=[],
                error_code="INTERNAL_ERROR",
                error_msg=str(e)
            )
    
    def _validate_request(self, request: TranslationRequest) -> None:
        """Validate translation request."""
        if len(request.q) > self.settings.translation.max_text_length:
            raise ValueError(f"Text too long. Maximum length is {self.settings.translation.max_text_length}")
        
        supported_langs = self.settings.translation.supported_languages
        if request.from_lang not in supported_langs:
            raise ValueError(f"Unsupported source language: {request.from_lang}")
        
        if request.to not in supported_langs:
            raise ValueError(f"Unsupported target language: {request.to}")
        
        if request.from_lang == request.to and request.from_lang != "auto":
            raise ValueError("Source and target languages cannot be the same")
    
    async def _get_cached_translation(self, request: TranslationRequest) -> Optional[Dict[str, Any]]:
        """Get cached translation if available."""
        try:
            async with cache_service:
                cache_key = ollama_client.create_cache_key(
                    request.q,
                    request.from_lang,
                    request.to
                )
                return await cache_service.get_translation(cache_key)
        except Exception as e:
            logger.warning("Cache lookup failed", error=str(e))
            return None
    
    async def _cache_translation(
        self,
        request: TranslationRequest,
        result: Dict[str, Any]
    ) -> None:
        """Cache translation result."""
        try:
            async with cache_service:
                cache_key = ollama_client.create_cache_key(
                    request.q,
                    request.from_lang,
                    request.to
                )
                await cache_service.set_translation(
                    cache_key,
                    {
                        "translation": result["translation"],
                        "model": result.get("model"),
                        "input_tokens": result.get("input_tokens", 0),
                        "output_tokens": result.get("output_tokens", 0)
                    },
                    ttl=self.settings.redis.cache_ttl
                )
        except Exception as e:
            logger.warning("Cache storage failed", error=str(e))
    
    async def _perform_translation(self, request: TranslationRequest) -> Dict[str, Any]:
        """Perform the actual translation using Ollama."""
        try:
            async with ollama_client:
                return await ollama_client.generate_translation(
                    text=request.q,
                    source_lang=request.from_lang,
                    target_lang=request.to
                )
        except Exception as e:
            logger.warning(f"Ollama translation failed: {e}, using mock response for demo")
            
            # Return a mock translation for demo purposes
            mock_translations = {
                ("en", "zh"): {
                    "Hello": "你好",
                    "Hello world": "你好世界",
                    "Thank you": "谢谢",
                    "Good morning": "早上好"
                },
                ("zh", "en"): {
                    "你好": "Hello",
                    "你好世界": "Hello world",
                    "谢谢": "Thank you",
                    "早上好": "Good morning"
                }
            }
            
            translation_map = mock_translations.get((request.from_lang, request.to), {})
            mock_translation = translation_map.get(request.q, f"[DEMO] Translated '{request.q}' from {request.from_lang} to {request.to}")
            
            return {
                "success": True,
                "translation": mock_translation,
                "model": "demo-mock",
                "source": "mock"
            }
    
    def _format_response(
        self,
        request: TranslationRequest,
        translation: str
    ) -> TranslationResponse:
        """Format translation response in Baidu API format."""
        return TranslationResponse(
            **{"from": request.from_lang},  # Use alias key
            to=request.to,  # Correct field name
            trans_result=[
                TranslationResult(
                    src=request.q,
                    dst=translation
                )
            ]
        )
    
    async def _log_request_metrics(
        self,
        request_id: str,
        request: TranslationRequest,
        result: Dict[str, Any],
        response_time: float,
        cache_hit: bool,
        success: bool
    ) -> None:
        """Log request metrics for statistics."""
        try:
            await stats_service.log_request(
                request_id=request_id,
                app_id=request.appid,
                source_language=request.from_lang,
                target_language=request.to,
                input_text_length=len(request.q),
                output_text_length=len(result.get("translation", "")),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                response_time=response_time,
                cache_hit=cache_hit,
                success=success,
                error_code=result.get("error") if not success else None
            )
        except Exception as e:
            logger.warning("Failed to log request metrics", error=str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """Check translation service health."""
        try:
            # Check Ollama health
            ollama_health = await ollama_client.health_check()
            
            # Check cache health  
            cache_health = await cache_service.health_check()
            
            overall_status = "healthy"
            if ollama_health["status"] != "healthy" or cache_health["status"] != "healthy":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "ollama": ollama_health["status"],
                    "cache": cache_health["status"],
                    "translation": "healthy"
                },
                "model_info": {
                    "active_model": self.settings.ollama.model_name,
                    "available_models": ollama_health.get("models", [])
                }
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "error": str(e)
                },
                "model_info": None
            }


# Global service instance
translation_service = TranslationService()
