"""
Optimized Translation Service with Performance Enhancements
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from .optimized_ollama_client import optimized_ollama_client
from .enhanced_cache_service import enhanced_cache_service

logger = logging.getLogger(__name__)

@dataclass
class TranslationRequest:
    """Translation request data."""
    text: str
    from_lang: str
    to_lang: str
    model: Optional[str] = None
    use_cache: bool = True
    max_length: Optional[int] = None
    translation_mode: str = "succinct"  # "succinct" or "verbose"

@dataclass
class TranslationResult:
    """Translation result with performance metrics."""
    translation: str
    success: bool
    cached: bool = False
    timing_breakdown: Dict[str, Any] = None
    model_used: str = ""
    error: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

class OptimizedTranslationService:
    """
    High-performance translation service combining:
    - Optimized Ollama client with connection pooling
    - Enhanced caching with compression
    - Smart model selection
    - Detailed performance tracking
    """
    
    def __init__(self):
        self.ollama_client = optimized_ollama_client
        self.cache_service = enhanced_cache_service
        
        # Performance tracking
        self.stats = {
            "total_translations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time_saved": 0,
            "average_response_time": 0,
            "model_usage": {}
        }
        
        # Model preferences (fastest to slowest)
        self.model_preferences = [
            "gemma3:latest",      # Fastest, good quality
            "llama3.1:8b",        # Slower but higher quality
            "llava:latest"        # Fallback
        ]
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service and warm up models."""
        if self._initialized:
            return
        
        logger.info("Initializing optimized translation service...")
        
        # Initialize Ollama client
        await self.ollama_client.initialize()
        
        # Warm up the primary model to reduce cold start latency
        await self.ollama_client.warm_up_model(self.model_preferences[0])
        
        self._initialized = True
        logger.info("Optimized translation service initialized")
    
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        Perform optimized translation with caching and performance tracking.
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        timing_breakdown = {"start_time": start_time}
        
        try:
            # Step 1: Input validation and preprocessing
            validation_start = time.time()
            
            if not request.text.strip():
                return TranslationResult(
                    translation="",
                    success=False,
                    error="Empty text provided",
                    timing_breakdown=timing_breakdown
                )
            
            # Determine model to use
            model = request.model or self.model_preferences[0]
            
            # Preprocess text (normalize whitespace, etc.)
            normalized_text = request.text.strip()
            if request.max_length and len(normalized_text) > request.max_length:
                normalized_text = normalized_text[:request.max_length]
            
            timing_breakdown["validation_ms"] = round((time.time() - validation_start) * 1000, 2)
            
            # Step 2: Cache lookup
            cache_start = time.time()
            cached_result = None
            
            if request.use_cache:
                cached_result = await self.cache_service.get_translation(
                    normalized_text,
                    request.from_lang,
                    request.to_lang,
                    model,
                    request.translation_mode
                )
            
            timing_breakdown["cache_lookup_ms"] = round((time.time() - cache_start) * 1000, 2)
            
            # Step 3: Return cached result if available
            if cached_result:
                total_time = time.time() - start_time
                
                self.stats["cache_hits"] += 1
                self.stats["total_translations"] += 1
                self.stats["total_time_saved"] += 5.0  # Assume 5s saved per cache hit
                
                timing_breakdown["total_ms"] = round(total_time * 1000, 2)
                
                return TranslationResult(
                    translation=cached_result["translation"],
                    success=True,
                    cached=True,
                    timing_breakdown=timing_breakdown,
                    model_used=model,
                    performance_metrics={
                        "cache_hit": True,
                        "access_count": cached_result.get("access_count", 0),
                        "cache_timestamp": cached_result.get("cache_timestamp", 0)
                    }
                )
            
            # Step 4: LLM translation
            self.stats["cache_misses"] += 1
            
            llm_start = time.time()
            
            ollama_result = await self.ollama_client.translate(
                text=normalized_text,
                from_lang=request.from_lang,
                to_lang=request.to_lang,
                model=model,
                translation_mode=request.translation_mode
            )
            
            timing_breakdown["llm_inference_ms"] = round((time.time() - llm_start) * 1000, 2)
            
            if not ollama_result["success"]:
                return TranslationResult(
                    translation="",
                    success=False,
                    error=ollama_result.get("error", "LLM translation failed"),
                    timing_breakdown=timing_breakdown,
                    model_used=model
                )
            
            translation = ollama_result["translation"]
            
            # Step 5: Cache the result
            cache_store_start = time.time()
            
            if request.use_cache:
                await self.cache_service.store_translation(
                    normalized_text,
                    request.from_lang,
                    request.to_lang,
                    model,
                    translation,
                    request.translation_mode
                )
            
            timing_breakdown["cache_store_ms"] = round((time.time() - cache_store_start) * 1000, 2)
            
            # Step 6: Finalize metrics
            total_time = time.time() - start_time
            timing_breakdown["total_ms"] = round(total_time * 1000, 2)
            
            # Update stats
            self.stats["total_translations"] += 1
            
            if model not in self.stats["model_usage"]:
                self.stats["model_usage"][model] = 0
            self.stats["model_usage"][model] += 1
            
            # Update average response time
            total_requests = self.stats["total_translations"]
            current_avg = self.stats["average_response_time"]
            self.stats["average_response_time"] = (
                (current_avg * (total_requests - 1) + total_time) / total_requests
            )
            
            # Combine timing data
            if ollama_result.get("timing_breakdown"):
                timing_breakdown.update(ollama_result["timing_breakdown"])
            
            return TranslationResult(
                translation=translation,
                success=True,
                cached=False,
                timing_breakdown=timing_breakdown,
                model_used=model,
                performance_metrics={
                    "cache_hit": False,
                    "ollama_metrics": ollama_result.get("ollama_metrics", {}),
                    "prompt_length": ollama_result.get("prompt_length", 0),
                    "response_length": ollama_result.get("response_length", 0)
                }
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            timing_breakdown["total_ms"] = round(total_time * 1000, 2)
            
            logger.error(f"Translation service error: {e}")
            
            return TranslationResult(
                translation="",
                success=False,
                error=str(e),
                timing_breakdown=timing_breakdown,
                model_used=request.model or "unknown"
            )
    
    async def get_available_models(self) -> list[str]:
        """Get list of available models."""
        return self.model_preferences.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = self.cache_service.get_cache_stats()
        ollama_stats = self.ollama_client.get_performance_stats()
        
        total_requests = self.stats["total_translations"]
        cache_hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "translation_service": {
                "total_translations": total_requests,
                "cache_hit_rate_percent": round(cache_hit_rate, 1),
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "average_response_time_ms": round(self.stats["average_response_time"] * 1000, 2),
                "total_time_saved_seconds": self.stats["total_time_saved"],
                "model_usage": self.stats["model_usage"],
                "preferred_models": self.model_preferences
            },
            "cache_service": cache_stats,
            "ollama_client": ollama_stats
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization tasks."""
        optimizations = []
        
        # Warm up all models
        for model in self.model_preferences:
            result = await self.ollama_client.warm_up_model(model)
            optimizations.append(f"Model {model}: {'✅' if result['success'] else '❌'}")
        
        # Get performance recommendations
        stats = self.get_performance_stats()
        recommendations = []
        
        cache_hit_rate = stats["translation_service"]["cache_hit_rate_percent"]
        if cache_hit_rate < 30:
            recommendations.append("Low cache hit rate - consider increasing cache size")
        elif cache_hit_rate > 80:
            recommendations.append("Excellent cache performance")
        
        avg_response = stats["translation_service"]["average_response_time_ms"]
        if avg_response > 5000:
            recommendations.append("High response times - consider using faster model")
        elif avg_response < 2000:
            recommendations.append("Excellent response times")
        
        return {
            "optimizations_applied": optimizations,
            "recommendations": recommendations,
            "current_stats": stats
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.cache_service.cleanup()
        await self.ollama_client.close()

# Global optimized service instance
optimized_translation_service = OptimizedTranslationService()
