"""
Optimized Ollama Client with Connection Pooling and Performance Enhancements
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class OptimizedOllamaClient:
    """
    High-performance Ollama client with:
    - Connection pooling and keep-alive
    - Persistent session management
    - Optimized request handling
    - Detailed timing metrics
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 default_model: str = "gemma3:latest",
                 max_connections: int = 10,
                 keep_alive_timeout: int = 30):
        
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.max_connections = max_connections
        self.keep_alive_timeout = keep_alive_timeout
        
        # Connection management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._initialized = False
        
        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "total_response_time": 0,
            "connection_reuses": 0,
            "model_loads": 0
        }
    
    async def initialize(self):
        """Initialize the client with optimized connection settings."""
        if self._initialized:
            return
            
        # Create optimized connector
        self._connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections,
            keepalive_timeout=self.keep_alive_timeout,
            enable_cleanup_closed=True,
            force_close=False,
            ttl_dns_cache=300  # 5-minute DNS cache
        )
        
        # Create session with optimized settings
        timeout = aiohttp.ClientTimeout(
            total=60,
            connect=10,
            sock_read=30
        )
        
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                'Connection': 'keep-alive',
                'Keep-Alive': f'timeout={self.keep_alive_timeout}',
                'User-Agent': 'LLMYTranslate-OptimizedClient/1.0'
            }
        )
        
        self._initialized = True
        logger.info("Optimized Ollama client initialized")
    
    async def close(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self):
        """Get an initialized session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            yield self._session
        except Exception as e:
            logger.error(f"Session error: {e}")
            # Reinitialize on error
            await self.close()
            await self.initialize()
            yield self._session
    
    async def warm_up_model(self, model: str = None) -> Dict[str, Any]:
        """Pre-load a model to reduce cold-start latency."""
        if not model:
            model = self.default_model
            
        logger.info(f"Warming up model: {model}")
        warm_start = time.time()
        
        try:
            # Send a minimal request to load the model
            result = await self.generate(
                prompt="Hi",
                model=model,
                max_tokens=1,
                options={
                    "temperature": 0.1,
                    "num_predict": 1
                }
            )
            
            warm_time = time.time() - warm_start
            self.stats["model_loads"] += 1
            
            logger.info(f"Model {model} warmed up in {warm_time:.2f}s")
            return {
                "success": True,
                "warm_up_time": warm_time,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Model warm-up failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "warm_up_time": time.time() - warm_start
            }
    
    async def translate(self, 
                       text: str, 
                       from_lang: str = "en", 
                       to_lang: str = "zh",
                       model: str = None) -> Dict[str, Any]:
        """
        Optimized translation with detailed timing breakdown.
        """
        if not model:
            model = self.default_model
            
        # Create optimized prompt
        if from_lang == "en" and to_lang == "zh":
            prompt = f"Translate to Chinese: {text}"
        elif from_lang == "zh" and to_lang == "en":
            prompt = f"Translate to English: {text}"
        else:
            prompt = f"Translate from {from_lang} to {to_lang}: {text}"
        
        return await self.generate(
            prompt=prompt,
            model=model,
            max_tokens=min(len(text) * 2 + 100, 512),  # Dynamic token limit
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "stop": ["\\n\\n", "Note:", "Explanation:"]  # Stop on explanations
            }
        )
    
    async def generate(self, 
                      prompt: str,
                      model: str = None,
                      max_tokens: int = 512,
                      options: Dict = None) -> Dict[str, Any]:
        """
        Generate text with detailed performance tracking.
        """
        if not model:
            model = self.default_model
            
        if not options:
            options = {}
        
        # Set optimized default options
        default_options = {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": max_tokens,
            "repeat_penalty": 1.1,
            "num_ctx": 2048  # Context window
        }
        default_options.update(options)
        
        # Start timing
        total_start = time.time()
        timing_breakdown = {}
        
        try:
            async with self.get_session() as session:
                # Step 1: Connection timing (should be minimal with pooling)
                conn_start = time.time()
                
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": default_options
                }
                
                # Step 2: Request timing
                request_start = time.time()
                timing_breakdown["connection_ms"] = round((request_start - conn_start) * 1000, 2)
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    # Step 3: Response parsing
                    parse_start = time.time()
                    timing_breakdown["request_ms"] = round((parse_start - request_start) * 1000, 2)
                    
                    result = await response.json()
                    
                    parse_time = time.time() - parse_start
                    total_time = time.time() - total_start
                    
                    timing_breakdown["parsing_ms"] = round(parse_time * 1000, 2)
                    timing_breakdown["total_ms"] = round(total_time * 1000, 2)
                    
                    # Extract Ollama metrics
                    eval_count = result.get("eval_count", 0)
                    eval_duration = result.get("eval_duration", 0)
                    prompt_eval_count = result.get("prompt_eval_count", 0)
                    prompt_eval_duration = result.get("prompt_eval_duration", 0)
                    
                    # Calculate performance metrics
                    ollama_metrics = {
                        "eval_count": eval_count,
                        "eval_duration_ms": round(eval_duration / 1_000_000, 2) if eval_duration else 0,
                        "prompt_eval_count": prompt_eval_count,
                        "prompt_eval_duration_ms": round(prompt_eval_duration / 1_000_000, 2) if prompt_eval_duration else 0,
                        "tokens_per_second": round(eval_count / (eval_duration / 1_000_000_000), 2) if eval_duration and eval_count else 0,
                        "total_tokens": eval_count + prompt_eval_count
                    }
                    
                    # Update stats
                    self.stats["total_requests"] += 1
                    self.stats["total_response_time"] += total_time
                    
                    # Check if connection was reused (heuristic based on fast connection time)
                    if timing_breakdown["connection_ms"] < 10:
                        self.stats["connection_reuses"] += 1
                    
                    translation = result.get("response", "").strip()
                    
                    return {
                        "success": True,
                        "translation": translation,
                        "timing_breakdown": timing_breakdown,
                        "ollama_metrics": ollama_metrics,
                        "model": model,
                        "prompt_length": len(prompt),
                        "response_length": len(translation)
                    }
                    
        except Exception as e:
            total_time = time.time() - total_start
            logger.error(f"Generation failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "timing_breakdown": {
                    "total_ms": round(total_time * 1000, 2),
                    **timing_breakdown
                },
                "model": model
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_requests = self.stats["total_requests"]
        
        if total_requests == 0:
            return {"message": "No requests processed yet"}
        
        avg_response_time = self.stats["total_response_time"] / total_requests
        connection_reuse_rate = (self.stats["connection_reuses"] / total_requests) * 100
        
        return {
            "total_requests": total_requests,
            "average_response_time_ms": round(avg_response_time * 1000, 2),
            "connection_reuse_rate_percent": round(connection_reuse_rate, 1),
            "model_loads": self.stats["model_loads"],
            "session_initialized": self._initialized
        }

# Global optimized client instance
optimized_ollama_client = OptimizedOllamaClient()

# Cleanup handler
async def cleanup_ollama_client():
    """Cleanup function for graceful shutdown."""
    await optimized_ollama_client.close()
