"""
Ollama client service for LLM communication.
"""

import asyncio
import json
import hashlib
import time
from typing import Optional, Dict, Any
import httpx
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
        """Check Ollama service health."""
        try:
            # Create a temporary client for health check
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5.0)
            ) as client:
                response = await client.get(f"{self.base_url}/api/tags")
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
