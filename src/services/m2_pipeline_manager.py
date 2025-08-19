"""
M2 Pipeline Service Manager
Integrates M2-optimized configuration with the main LLM service
"""

import asyncio
import time
import psutil
from typing import Dict, Any, Optional, List
from structlog import get_logger

from .ollama_client import ollama_client
from ..config.m2_pipeline import m2_config

logger = get_logger(__name__)


class M2PipelineManager:
    """Manages M2 MacBook pipeline with intelligent model routing"""
    
    def __init__(self):
        self.loaded_models = set()
        self.model_performance_stats = {}
        self.current_memory_usage = 0.0
        self.request_queue = asyncio.Queue()
        self.processing_lock = asyncio.Semaphore(m2_config.get_concurrent_request_limit() if m2_config else 8)
        
        # Initialize with startup models
        if m2_config:
            self.startup_models = m2_config.get_startup_models()
            self.lazy_load_models = m2_config.get_lazy_load_models()
        else:
            self.startup_models = ["gemma3:270m", "gemma2:2b"]
            self.lazy_load_models = ["gemma3:latest", "llava:latest"]
            
        logger.info("M2 Pipeline Manager initialized", 
                   startup_models=self.startup_models)
    
    async def startup(self):
        """Initialize the M2 pipeline with startup models"""
        logger.info("🍎 Starting M2 Pipeline...")
        
        # Pre-load startup models for instant response
        for model in self.startup_models:
            try:
                await self._ensure_model_loaded(model)
                logger.info(f"✅ Startup model loaded: {model}")
            except Exception as e:
                logger.error(f"❌ Failed to load startup model {model}: {e}")
        
        # Check system resources
        await self._update_system_metrics()
        logger.info("🚀 M2 Pipeline ready", 
                   loaded_models=list(self.loaded_models),
                   memory_usage=f"{self.current_memory_usage:.1f}%")
    
    async def intelligent_translate(self, 
                                  text: str, 
                                  source_lang: str, 
                                  target_lang: str,
                                  max_response_time: Optional[float] = None,
                                  quality_mode: str = "balanced") -> Dict[str, Any]:
        """Intelligent translation with automatic model selection"""
        
        start_time = time.time()
        
        # Select optimal model based on requirements
        if max_response_time:
            selected_model = self._select_model_by_speed(max_response_time)
        else:
            selected_model = self._select_model_by_quality(quality_mode)
        
        logger.info("🎯 Model selected", 
                   model=selected_model, 
                   max_time=max_response_time,
                   quality=quality_mode)
        
        # Ensure model is loaded
        await self._ensure_model_loaded(selected_model)
        
        try:
            async with self.processing_lock:
                # Perform translation
                result = await ollama_client.generate_translation(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model_name=selected_model
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Update performance stats
                self._update_performance_stats(selected_model, duration, len(text))
                
                # Add M2 pipeline metadata
                if result.get("success"):
                    result.update({
                        "pipeline": "m2_macbook",
                        "model_tier": self._get_model_tier(selected_model),
                        "response_time": duration,
                        "gpu_accelerated": True,
                        "unified_memory": True
                    })
                
                return result
                
        except Exception as e:
            logger.error("Translation error", model=selected_model, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "pipeline": "m2_macbook"
            }
    
    async def vision_translate(self, 
                             image_path: str,
                             target_lang: str = "zh",
                             max_response_time: Optional[float] = None) -> Dict[str, Any]:
        """Vision-enabled translation using multimodal models"""
        
        # Select vision-capable model
        vision_model = "qwen2.5vl:7b" if max_response_time and max_response_time > 5 else "llava:latest"
        
        logger.info("🔍 Vision translation", model=vision_model, image=image_path)
        
        await self._ensure_model_loaded(vision_model)
        
        try:
            # This would integrate with vision capabilities
            # For now, return placeholder
            return {
                "success": True,
                "translation": "Vision translation not yet implemented",
                "model": vision_model,
                "pipeline": "m2_macbook_vision"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pipeline": "m2_macbook_vision"
            }
    
    def _select_model_by_speed(self, max_seconds: float) -> str:
        """Select model based on speed requirement"""
        if not m2_config:
            return "gemma2:2b"  # Safe default
            
        selected = m2_config.get_model_for_speed_requirement(max_seconds)
        if not selected:
            # Fallback to fastest available
            fallback_models = m2_config.get_fallback_models()
            selected = fallback_models[0] if fallback_models else "gemma3:270m"
            
        return selected
    
    def _select_model_by_quality(self, quality_mode: str) -> str:
        """Select model based on quality requirements (updated with real performance data)"""
        quality_map = {
            "fastest": "gemma3:270m",        # 0.2-0.3s
            "balanced": "gemma2:2b",         # 0.4-0.8s  
            "quality": "gemma3:latest",      # 1-3s
            "detailed": "llava:latest",      # 8-15s with alternatives
            "expert_vision": "qwen2.5vl:7b"  # 30s+ for complex vision
        }
        return quality_map.get(quality_mode, "gemma2:2b")
    
    def _get_model_tier(self, model_name: str) -> str:
        """Get the tier classification for a model (updated with real performance)"""
        model_tier_map = {
            "gemma3:270m": "ultra_fast",
            "gemma2:2b": "fast", 
            "gemma3:latest": "capable",
            "llava:latest": "advanced",
            "qwen2.5vl:7b": "expert"
        }
        return model_tier_map.get(model_name, "unknown")
    
    async def _ensure_model_loaded(self, model_name: str):
        """Ensure a model is loaded and ready"""
        if model_name in self.loaded_models:
            return
            
        # Check if we need to unload models due to memory constraints
        await self._manage_memory()
        
        # Load the model (this happens automatically when we use it)
        # Ollama loads models on first use
        self.loaded_models.add(model_name)
        logger.info(f"📥 Model marked as loaded: {model_name}")
    
    async def _manage_memory(self):
        """Manage memory usage by unloading unused models"""
        await self._update_system_metrics()
        
        memory_threshold = m2_config.get_memory_threshold() if m2_config else 0.75
        
        if self.current_memory_usage > memory_threshold:
            # Unload lazy-loaded models first
            models_to_unload = [m for m in self.loaded_models if m in self.lazy_load_models]
            
            for model in models_to_unload[:2]:  # Unload up to 2 models
                self.loaded_models.discard(model)
                logger.info(f"🗑️  Model unloaded due to memory pressure: {model}")
    
    async def _update_system_metrics(self):
        """Update system memory and performance metrics"""
        try:
            memory = psutil.virtual_memory()
            self.current_memory_usage = memory.percent / 100.0
        except Exception as e:
            logger.warning("Could not update system metrics", error=str(e))
            self.current_memory_usage = 0.5  # Conservative estimate
    
    def _update_performance_stats(self, model: str, duration: float, input_length: int):
        """Update performance statistics for a model"""
        if model not in self.model_performance_stats:
            self.model_performance_stats[model] = {
                "requests": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf')
            }
        
        stats = self.model_performance_stats[model]
        stats["requests"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["requests"]
        stats["max_time"] = max(stats["max_time"], duration)
        stats["min_time"] = min(stats["min_time"], duration)
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        await self._update_system_metrics()
        
        return {
            "pipeline": "m2_macbook",
            "status": "healthy",
            "loaded_models": list(self.loaded_models),
            "startup_models": self.startup_models,
            "memory_usage": f"{self.current_memory_usage*100:.1f}%",
            "concurrent_limit": m2_config.get_concurrent_request_limit() if m2_config else 8,
            "performance_stats": self.model_performance_stats,
            "chip": "Apple M2",
            "gpu_acceleration": True,
            "unified_memory": "16GB LPDDR5"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for M2 pipeline"""
        try:
            # Test ollama connection
            ollama_health = await ollama_client.health_check()
            
            # Test model availability
            models_health = await ollama_client.list_models()
            
            # System metrics
            await self._update_system_metrics()
            
            return {
                "pipeline": "m2_macbook",
                "status": "healthy",
                "ollama": ollama_health,
                "models": models_health,
                "memory_usage": self.current_memory_usage,
                "loaded_models": list(self.loaded_models),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "pipeline": "m2_macbook", 
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }


# Global M2 pipeline manager instance
m2_pipeline = M2PipelineManager()
