"""
Ollama client service for LLM communication.
"""

import asyncio
import json
import hashlib
import time
from typing import Optional, Dict, Any
import httpx
import requests  # Add requests as fallback for health checks
from structlog import get_logger

from ..core.config import get_settings
from ..models.schemas import OllamaRequest, OllamaResponse

logger = get_logger(__name__)


class OllamaClient:
    """Async client for Ollama API communication."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = self.settings.ollama.ollama_host
        self.model_name = self.settings.ollama.model_name
        self.timeout = self.settings.ollama.request_timeout
        self.max_retries = self.settings.ollama.max_retries
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Configure httpx client for direct connection
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health using requests library."""
        try:
            # Use requests instead of httpx due to compatibility issues
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "models": [model.get("name") for model in models],
                    "active_model": self.model_name
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            logger.error("Ollama health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models from Ollama using requests library."""
        try:
            # Use requests instead of httpx due to compatibility issues
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "success": True,
                    "models": models,
                    "count": len(models)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "models": []
                }
        except Exception as e:
            logger.error("Ollama list models failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "models": []
            }
    
    async def chat_completion(
        self,
        message: str,
        model: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simple chat completion for voice chat - direct Ollama API call using requests.
        """
        start_time = time.time()
        logger.info(f"[OLLAMA] chat_completion called with message: '{message[:50]}...'")
        print(f"[OLLAMA] DEBUG: chat_completion called with message: '{message[:50]}...'")
        
        try:
            if model is None:
                model = self.model_name
                
            logger.info(f"[OLLAMA] Using model: {model}, base_url: {self.base_url}")
            print(f"[OLLAMA] DEBUG: Using model: {model}, base_url: {self.base_url}")
            
            # Use requests library like other working methods
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": message,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": 0.9,
                    "num_predict": kwargs.get("max_tokens", 1000)
                }
            }
            
            # Make direct HTTP call using requests
            logger.info(f"[OLLAMA] Making POST request to: {url}")
            print(f"[OLLAMA] DEBUG: Making POST request to: {url}")
            response = requests.post(url, json=payload, timeout=90.0)  # Increased timeout to 90 seconds for queuing
            processing_time = time.time() - start_time
            logger.info(f"[OLLAMA] Request completed in {processing_time:.3f}s, status: {response.status_code}")
            print(f"[OLLAMA] DEBUG: Request completed in {processing_time:.3f}s, status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[OLLAMA] Response received: {len(result.get('response', ''))} chars")
                print(f"[OLLAMA] DEBUG: Response received: {len(result.get('response', ''))} chars")
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model_used": model,
                    "processing_time": processing_time
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Ollama API error: {response.status_code}",
                    "processing_time": processing_time
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Chat completion error: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def generate_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_name: Optional[str] = None,
        translation_mode: str = "succinct"
    ) -> Dict[str, Any]:
        """Generate translation using Ollama."""
        model = model_name or self.model_name
        prompt = self._create_translation_prompt(text, source_lang, target_lang, translation_mode)
        
        request_data = OllamaRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.1,  # Low temperature for consistent translations
                "top_p": 0.9,
                "num_predict": -1,  # Generate until done
            }
        )
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Sending translation request to Ollama",
                    attempt=attempt + 1,
                    model=model,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                # Create a temporary client for this request without proxy
                start_time = time.time()
                connection_start = time.time()
                
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    trust_env=False  # Don't use environment proxy settings
                ) as client:
                    connection_time = time.time() - connection_start
                    inference_start = time.time()
                    
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=request_data.dict(),
                    )
                
                inference_time = time.time() - inference_start
                
                if response.status_code == 200:
                    parsing_start = time.time()
                    result = response.json()
                    ollama_response = OllamaResponse(**result)
                    
                    # Extract the translation from the response
                    translation = self._extract_translation(ollama_response.response)
                    parsing_time = time.time() - parsing_start
                    
                    # Detailed timing breakdown
                    total_time = time.time() - start_time
                    
                    return {
                        "translation": translation,
                        "model": ollama_response.model,
                        "input_tokens": ollama_response.prompt_eval_count or 0,
                        "output_tokens": ollama_response.eval_count or 0,
                        "response_time": total_time,
                        "detailed_timing": {
                            "connection_ms": round(connection_time * 1000, 2),
                            "inference_ms": round(inference_time * 1000, 2),
                            "parsing_ms": round(parsing_time * 1000, 2),
                            "total_ms": round(total_time * 1000, 2),
                            "ollama_load_duration_ms": round((ollama_response.load_duration or 0) / 1e6, 2),
                            "ollama_prompt_eval_ms": round((ollama_response.prompt_eval_duration or 0) / 1e6, 2),
                            "ollama_eval_ms": round((ollama_response.eval_duration or 0) / 1e6, 2),
                            "ollama_total_ms": round((ollama_response.total_duration or 0) / 1e6, 2)
                        },
                        "success": True
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(
                        "Ollama request failed",
                        status_code=response.status_code,
                        response=response.text,
                        attempt=attempt + 1
                    )
                    
                    if attempt == self.max_retries - 1:
                        return {
                            "success": False,
                            "error": error_msg,
                            "translation": None
                        }
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(
                    "Ollama request exception",
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "translation": None
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "translation": None
        }
    
    def _create_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation_mode: str = "succinct"
    ) -> str:
        """Create a translation prompt for the LLM."""
        
        # Language mapping for better prompts
        lang_names = {
            "en": "English",
            "zh": "Chinese",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ja": "Japanese",
            "ko": "Korean",
            "auto": "automatically detected language"
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        if translation_mode == "verbose":
            # Verbose mode with explanations and alternatives
            if source_lang == "auto":
                prompt = f"""Please translate the following text to {target_name}. Provide multiple translation options with explanations of nuances, grammar breakdowns, and cultural context where relevant.

Text to translate: {text}

Please provide:
1. The most common/general translation
2. Alternative translations with different nuances
3. Brief explanations of grammar or cultural context
4. Pronunciation guides where helpful

Translation with explanations:"""
            else:
                prompt = f"""Please translate the following text from {source_name} to {target_name}. Provide multiple translation options with explanations of nuances, grammar breakdowns, and cultural context where relevant.

Text to translate: {text}

Please provide:
1. The most common/general translation
2. Alternative translations with different nuances  
3. Brief explanations of grammar or cultural context
4. Pronunciation guides where helpful

Translation with explanations:"""
        else:
            # Succinct mode - professional, direct translation only
            if source_lang == "auto":
                prompt = f"""Translate the following text to {target_name}. Provide ONLY the most accurate and natural translation. Do not include any explanations, alternatives, grammar breakdowns, or additional commentary.

Text: {text}

Translation:"""
            else:
                prompt = f"""Translate from {source_name} to {target_name}. Provide ONLY the most accurate and natural translation. Do not include any explanations, alternatives, grammar breakdowns, or additional commentary.

Text: {text}

Translation:"""
        
        return prompt
    
    def _extract_translation(self, response: str) -> str:
        """Extract the clean translation from LLM response."""
        # Remove common prefixes and suffixes
        translation = response.strip()
        
        # Remove common response patterns
        patterns_to_remove = [
            "Translation:",
            "The translation is:",
            "Here is the translation:",
            "The translated text is:",
        ]
        
        for pattern in patterns_to_remove:
            if translation.lower().startswith(pattern.lower()):
                translation = translation[len(pattern):].strip()
        
        # Remove quotes if they wrap the entire translation
        if (translation.startswith('"') and translation.endswith('"')) or \
           (translation.startswith("'") and translation.endswith("'")):
            translation = translation[1:-1]
        
        return translation
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using Ollama for general chat/conversation."""
        model = model or self.model_name
        
        # Merge provided options with defaults
        default_options = {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": max_tokens or -1,
        }
        if options:
            default_options.update(options)
        
        request_data = OllamaRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options=default_options
        )
        
        for attempt in range(self.max_retries):
            try:
                full_url = f"{self.base_url}/api/generate"
                logger.info(
                    "Sending chat request to Ollama",
                    attempt=attempt + 1,
                    model=model,
                    prompt_length=len(prompt),
                    full_url=full_url,
                    base_url=self.base_url
                )
                
                if not self.client:
                    # Create a new client for this request with explicit proxy bypass
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout),
                        trust_env=False  # Don't use environment proxy settings
                    ) as client:
                        response = await client.post(
                            full_url,
                            json=request_data.dict(),
                            headers={"Content-Type": "application/json"}
                        )
                else:
                    response = await self.client.post(
                        "/api/generate",
                        json=request_data.dict(),
                        headers={"Content-Type": "application/json"}
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(
                        "Chat response received from Ollama",
                        model=model,
                        response_length=len(result.get("response", ""))
                    )
                    
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "model": model,
                        "done": result.get("done", True),
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count")
                    }
                else:
                    logger.warning(
                        "Chat request failed",
                        status_code=response.status_code,
                        response=response.text[:500]
                    )
                    
            except Exception as e:
                logger.warning(
                    "Chat request exception",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "response": None
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "response": None
        }

    async def generate_vision(
        self,
        model: str,
        prompt: str,
        image_base64: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate a response using a vision model with image input."""
        
        # Prepare vision request data
        request_data = {
            "model": model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or 1000,
                "top_p": 0.9
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Sending vision request to Ollama",
                    attempt=attempt + 1,
                    model=model,
                    prompt_length=len(prompt)
                )
                
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout * 2),  # Vision models may take longer
                    trust_env=False
                ) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(
                        "Vision response received from Ollama",
                        model=model,
                        response_length=len(result.get("response", ""))
                    )
                    
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "model": result.get("model", model),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count"),
                        "total_duration": result.get("total_duration"),
                        "confidence": self._estimate_confidence(result.get("response", ""))
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(
                        "Ollama vision request failed",
                        status_code=response.status_code,
                        response=response.text,
                        attempt=attempt + 1
                    )
                    
                    if attempt == self.max_retries - 1:
                        return {
                            "success": False,
                            "error": error_msg,
                            "response": ""
                        }
                    
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(
                    "Ollama vision request exception",
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "response": ""
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "response": ""
        }

    async def generate_text(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate text using a text model."""
        return await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _estimate_confidence(self, response: str) -> Optional[float]:
        """Estimate confidence score based on response characteristics."""
        if not response:
            return 0.0
        
        # Simple heuristic based on response length and certainty words
        confidence_words = ['clearly', 'definitely', 'obvious', 'certain', 'sure']
        uncertainty_words = ['maybe', 'perhaps', 'might', 'possibly', 'unclear', 'difficult to tell']
        
        response_lower = response.lower()
        confidence_count = sum(1 for word in confidence_words if word in response_lower)
        uncertainty_count = sum(1 for word in uncertainty_words if word in response_lower)
        
        # Base confidence on response length and word indicators
        base_confidence = min(0.9, len(response) / 500)
        
        # Adjust based on confidence indicators
        if confidence_count > uncertainty_count:
            return min(0.95, base_confidence + 0.1)
        elif uncertainty_count > confidence_count:
            return max(0.3, base_confidence - 0.2)
        
        return base_confidence
    
    def create_cache_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model_name: Optional[str] = None,
        translation_mode: str = "succinct"
    ) -> str:
        """Create a cache key for translation request."""
        model = model_name or self.model_name
        key_string = f"{text}|{source_lang}|{target_lang}|{model}|{translation_mode}"
        return hashlib.md5(key_string.encode()).hexdigest()


# Global client instance
ollama_client = OllamaClient()
