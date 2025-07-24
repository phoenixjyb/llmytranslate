"""
Ollama client service for LLM communication.
"""

import asyncio
import json
import hashlib
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
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate translation using Ollama."""
        model = model_name or self.model_name
        prompt = self._create_translation_prompt(text, source_lang, target_lang)
        
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
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    trust_env=False  # Don't use environment proxy settings
                ) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=request_data.dict(),
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    ollama_response = OllamaResponse(**result)
                    
                    # Extract the translation from the response
                    translation = self._extract_translation(ollama_response.response)
                    
                    return {
                        "translation": translation,
                        "model": ollama_response.model,
                        "input_tokens": ollama_response.prompt_eval_count or 0,
                        "output_tokens": ollama_response.eval_count or 0,
                        "response_time": (ollama_response.total_duration or 0) / 1e9,  # Convert to seconds
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
        target_lang: str
    ) -> str:
        """Create a translation prompt for the LLM."""
        
        # Language mapping for better prompts
        lang_names = {
            "en": "English",
            "zh": "Chinese",
            "auto": "automatically detected language"
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        if source_lang == "auto":
            prompt = f"""Please translate the following text to {target_name}. Provide only the translation without any additional explanation or commentary.

Text to translate: {text}

Translation:"""
        else:
            prompt = f"""Please translate the following text from {source_name} to {target_name}. Provide only the translation without any additional explanation or commentary.

Text to translate: {text}

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
        model_name: Optional[str] = None
    ) -> str:
        """Create a cache key for translation request."""
        model = model_name or self.model_name
        key_string = f"{text}|{source_lang}|{target_lang}|{model}"
        return hashlib.md5(key_string.encode()).hexdigest()


# Global client instance
ollama_client = OllamaClient()
