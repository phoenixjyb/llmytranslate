"""
Optimized LLM Service for Phone Call Mode
Focuses on speed and efficiency for real-time conversations
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OptimizedLLMService:
    """Optimized LLM service for fast phone call responses"""
    
    def __init__(self):
        self.model_configs = {
            # Use actually available models for phone calls
            "gemma3:latest": {  # This model is available
                "max_tokens": 150,  # Shorter responses for phone calls
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": [".", "!", "?", "\n\n"],
                "context_window": 2048,
                "estimated_speed": "fast"  # Available model
            },
            "llama3.1:8b": {  # This model is available but larger
                "max_tokens": 120,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": [".", "!", "?", "\n"],
                "context_window": 1536,
                "estimated_speed": "moderate"  # Larger but available
            },
            # Keep original configs for when models become available
            # "gemma3:1b": {  # Currently unavailable
            #     "max_tokens": 150,  # Shorter responses for phone calls
            #     "temperature": 0.7,
            #     "top_p": 0.9,
            #     "stop_sequences": [".", "!", "?", "\n\n"],
            #     "context_window": 2048,
            #     "estimated_speed": "very_fast"  # <2s typical
            # },
            "phi3:mini": {
                "max_tokens": 120,
                "temperature": 0.6,
                "top_p": 0.8,
                "stop_sequences": [".", "!", "?"],
                "context_window": 1024,
                "estimated_speed": "ultra_fast"  # <1s typical
            },
            "llama3.2:1b": {
                "max_tokens": 100,
                "temperature": 0.8,
                "top_p": 0.85,
                "stop_sequences": [".", "!", "?", "\n"],
                "context_window": 1536,
                "estimated_speed": "very_fast"
            },
            # Fallback to larger models if needed
            "gemma2:2b": {
                "max_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": [".", "!", "?", "\n\n"],
                "context_window": 2048,
                "estimated_speed": "very_fast"  # Fast 2B parameter model
            },
            "gemma2:2b": {
                "max_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop_sequences": [".", "!", "?", "\n\n"],
                "context_window": 4096,
                "estimated_speed": "fast"  # 2-4s typical
            }
        }
        
        # Performance tracking
        self.performance_stats = {}
        self.model_availability = {}
        self.last_health_check = None
        
        # Connection pooling for Ollama
        self.connection_pool_size = 5
        self.active_connections = 0
        self.connection_semaphore = asyncio.Semaphore(self.connection_pool_size)
        
        logger.info("Optimized LLM service initialized")
    
    def get_optimal_model_for_phone_call(self, kid_friendly: bool = False, 
                                       language: str = "en") -> str:
        """Select the best model for phone call based on requirements"""
        # For kid-friendly mode, prefer more reliable models
        if kid_friendly:
            if self.is_model_available("gemma2:270m"):
                return "gemma2:270m"
            elif self.is_model_available("gemma3:latest"):
                return "gemma3:latest"
            elif self.is_model_available("llama3.1:8b"):
                return "llama3.1:8b"
        
        # For general phone calls, prioritize available models
        # Check available models starting with fastest
        if self.is_model_available("gemma2:270m"):
            return "gemma2:270m"
        elif self.is_model_available("gemma3:latest"):
            return "gemma3:latest"
        elif self.is_model_available("llama3.1:8b"):
            return "llama3.1:8b"
        elif self.is_model_available("gemma2:270m"):
            return "gemma2:270m"
        elif self.is_model_available("llama3.2:1b"):
            return "llama3.2:1b"
            return "llama3.2:1b"
        
        # Fallback to larger model
        return "gemma2:270m"
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available and responsive"""
        return self.model_availability.get(model_name, True)  # Assume available by default
    
    async def optimize_context_for_phone_call(self, conversation_history: List[Dict], 
                                            model: str) -> List[Dict]:
        """Optimize conversation context for phone call performance"""
        max_context = self.model_configs[model]["context_window"]
        
        # For phone calls, keep context short and relevant
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        max_chars = max_context * 3  # Conservative estimate
        
        optimized_context = []
        total_chars = 0
        
        # Always include system prompt
        if conversation_history and conversation_history[0].get("role") == "system":
            optimized_context.append(conversation_history[0])
            total_chars += len(conversation_history[0]["content"])
        
        # Add recent messages in reverse order
        for message in reversed(conversation_history[1:]):
            message_chars = len(message["content"])
            if total_chars + message_chars > max_chars:
                break
            optimized_context.insert(-1 if optimized_context and optimized_context[0].get("role") == "system" else 0, message)
            total_chars += message_chars
        
        logger.info(f"Optimized context: {len(optimized_context)} messages, {total_chars} chars")
        return optimized_context
    
    async def fast_completion(self, message: str, model: str, 
                            conversation_context: List[Dict] = None,
                            timeout: float = 10.0) -> Dict[str, Any]:
        """Optimized completion with timeout and performance tracking"""
        start_time = time.time()
        
        try:
            # Use connection pool to limit concurrent requests
            async with self.connection_semaphore:
                self.active_connections += 1
                
                # Get model config
                config = self.model_configs.get(model, self.model_configs["gemma2:2b"])
                
                # Optimize context
                if conversation_context:
                    conversation_context = await self.optimize_context_for_phone_call(
                        conversation_context, model
                    )
                
                # Import ollama client here to avoid circular imports
                from ..services.ollama_client import ollama_client
                
                # Create timeout task
                completion_task = asyncio.create_task(
                    ollama_client.chat_completion(
                        message=message,
                        model=model,
                        conversation_context=conversation_context or [],
                        max_tokens=config["max_tokens"],
                        temperature=config["temperature"],
                        top_p=config["top_p"],
                        stop_sequences=config.get("stop_sequences", [])
                    )
                )
                
                try:
                    result = await asyncio.wait_for(completion_task, timeout=timeout)
                except asyncio.TimeoutError:
                    completion_task.cancel()
                    raise TimeoutError(f"LLM completion timed out after {timeout}s")
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Track performance
                self.track_performance(model, duration, len(message))
                
                # Mark model as available
                self.model_availability[model] = True
                
                return {
                    **result,
                    "duration": duration,
                    "model_used": model,
                    "optimization_applied": True
                }
                
        except Exception as e:
            # Mark model as potentially unavailable if it fails repeatedly
            if model in self.performance_stats:
                self.performance_stats[model]["failures"] = self.performance_stats[model].get("failures", 0) + 1
                if self.performance_stats[model]["failures"] > 3:
                    self.model_availability[model] = False
                    logger.warning(f"Model {model} marked as unavailable due to failures")
            
            logger.error(f"Optimized LLM completion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
                "model_used": model
            }
        
        finally:
            self.active_connections -= 1
    
    def track_performance(self, model: str, duration: float, input_length: int):
        """Track model performance for optimization"""
        if model not in self.performance_stats:
            self.performance_stats[model] = {
                "total_requests": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "failures": 0,
                "last_used": None
            }
        
        stats = self.performance_stats[model]
        stats["total_requests"] += 1
        stats["total_duration"] += duration
        stats["average_duration"] = stats["total_duration"] / stats["total_requests"]
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["max_duration"] = max(stats["max_duration"], duration)
        stats["last_used"] = datetime.now().isoformat()
        
        logger.info(f"Model {model} performance: {duration:.2f}s (avg: {stats['average_duration']:.2f}s)")
    
    async def health_check_models(self) -> Dict[str, Any]:
        """Check health and availability of all models"""
        health_results = {}
        
        for model_name in self.model_configs.keys():
            try:
                start_time = time.time()
                
                # Simple test completion
                test_result = await self.fast_completion(
                    message="Hi",
                    model=model_name,
                    timeout=5.0
                )
                
                duration = time.time() - start_time
                
                health_results[model_name] = {
                    "available": test_result.get("success", False),
                    "response_time": duration,
                    "status": "healthy" if test_result.get("success", False) else "unhealthy",
                    "last_check": datetime.now().isoformat()
                }
                
                self.model_availability[model_name] = test_result.get("success", False)
                
            except Exception as e:
                health_results[model_name] = {
                    "available": False,
                    "response_time": None,
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                self.model_availability[model_name] = False
        
        self.last_health_check = datetime.now().isoformat()
        return health_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            "performance_stats": self.performance_stats,
            "model_availability": self.model_availability,
            "connection_pool": {
                "pool_size": self.connection_pool_size,
                "active_connections": self.active_connections,
                "available_connections": self.connection_pool_size - self.active_connections
            },
            "last_health_check": self.last_health_check,
            "recommended_models": {
                "fastest": self.get_optimal_model_for_phone_call(kid_friendly=False),
                "kid_friendly": self.get_optimal_model_for_phone_call(kid_friendly=True),
                "fallback": "gemma2:2b"
            }
        }
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics for health monitoring"""
        try:
            stats = {
                "service_name": "Optimized LLM Service",
                "status": "healthy",
                "uptime_seconds": time.time() - getattr(self, 'start_time', time.time()),
                "total_requests": getattr(self, 'total_requests', 0),
                "successful_requests": getattr(self, 'successful_requests', 0),
                "failed_requests": getattr(self, 'failed_requests', 0),
                "average_response_time": getattr(self, 'average_response_time', 0.0),
                "model_performance": getattr(self, 'model_stats', {}),
                "available_models": list(self.model_configs.keys()),
                "optimal_model": self.get_optimal_model_for_phone_call(kid_friendly=False),
                "connection_pool": {
                    "total_connections": self.connection_pool_size,
                    "active_connections": self.active_connections,
                    "available_connections": self.connection_pool_size - self.active_connections
                },
                "last_health_check": self.last_health_check,
                "recommended_models": {
                    "fastest": self.get_optimal_model_for_phone_call(kid_friendly=False),
                    "kid_friendly": self.get_optimal_model_for_phone_call(kid_friendly=True),
                    "fallback": "gemma2:2b"
                },
                "performance_metrics": {
                    "success_rate": (getattr(self, 'successful_requests', 0) / max(getattr(self, 'total_requests', 1), 1)) * 100,
                    "current_load": self.active_connections / self.connection_pool_size if self.connection_pool_size > 0 else 0
                }
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {
                "service_name": "Optimized LLM Service",
                "status": "error",
                "error": str(e),
                "uptime_seconds": 0,
                "total_requests": 0
            }
    
    async def warmup_models(self) -> Dict[str, bool]:
        """Warm up models for faster first responses"""
        logger.info("Warming up models for phone calls...")
        warmup_results = {}
        
        for model_name in ["gemma2:2b", "llama3.2:1b"]:
            try:
                # Send a simple warmup request
                result = await self.fast_completion(
                    message="Hello",
                    model=model_name,
                    timeout=15.0  # Longer timeout for warmup
                )
                warmup_results[model_name] = result.get("success", False)
                logger.info(f"Model {model_name} warmed up: {warmup_results[model_name]}")
                
            except Exception as e:
                warmup_results[model_name] = False
                logger.warning(f"Failed to warm up {model_name}: {e}")
        
        return warmup_results

# Global instance
optimized_llm_service = OptimizedLLMService()
