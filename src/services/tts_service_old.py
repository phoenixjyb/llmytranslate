# TTS Service with Dual Environment Support
# Manages communication between main service (Python 3.13) and TTS service (Python 3.12)

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import aiofiles
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using Coqui TTS."""
    
    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = Path(tempfile.gettempdir()) / "llm_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Model cache
        self._models = {}
        self._initialized = False
        
        # Available models for different languages
        self.model_configs = {
            'en': {
                'model_name': "tts_models/en/ljspeech/tacotron2-DDC",
                'description': "English TTS model"
            },
            'zh': {
                'model_name': "tts_models/zh-CN/baker/tacotron2-DDC", 
                'description': "Chinese TTS model"
            },
            'multilingual': {
                'model_name': "tts_models/multilingual/multi-dataset/xtts_v2",
                'description': "Multilingual TTS model"
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize TTS models asynchronously."""
        if not TTS_AVAILABLE:
            return False
            
        if self._initialized:
            return True
        
        try:
            # Initialize basic English model first
            loop = asyncio.get_event_loop()
            
            # Load models in background thread to avoid blocking
            await loop.run_in_executor(
                None,
                self._load_model,
                'en'
            )
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            return False
    
    def _load_model(self, language: str) -> bool:
        """Load TTS model for specific language."""
        try:
            if language in self._models:
                return True
                
            model_config = self.model_configs.get(language)
            if not model_config:
                return False
            
            print(f"Loading TTS model for {language}...")
            self._models[language] = TTS(model_name=model_config['model_name'])
            print(f"TTS model for {language} loaded successfully")
            return True
            
        except Exception as e:
            print(f"Failed to load TTS model for {language}: {e}")
            return False
    
    async def synthesize_speech(
        self, 
        text: str, 
        language: str = 'en',
        voice_speed: float = 1.0,
        output_format: str = 'wav'
    ) -> Dict[str, Any]:
        """Convert text to speech and return audio data."""
        
        if not TTS_AVAILABLE:
            return {
                'success': False,
                'error': 'TTS library not available. Install with: pip install coqui-tts',
                'processing_time': 0
            }
        
        start_time = time.time()
        
        try:
            # Validate input
            if len(text) > 5000:
                return {
                    'success': False,
                    'error': 'Text too long (max 5000 characters)',
                    'processing_time': time.time() - start_time
                }
            
            # Initialize if needed
            if not self._initialized:
                await self.initialize()
            
            # Select appropriate model
            model_key = language if language in self.model_configs else 'en'
            
            # Load model if not already loaded
            if model_key not in self._models:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._load_model, model_key)
            
            if model_key not in self._models:
                return {
                    'success': False,
                    'error': f'Could not load TTS model for language: {language}',
                    'processing_time': time.time() - start_time
                }
            
            tts_model = self._models[model_key]
            
            # Generate unique filename
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            audio_filename = self.temp_dir / f"tts_{text_hash}_{int(time.time() * 1000)}.{output_format}"
            
            # Synthesize speech (run in thread to avoid blocking)
            loop = asyncio.get_event_loop()
            synthesis_start = time.time()
            
            await loop.run_in_executor(
                None,
                self._synthesize_to_file,
                tts_model,
                text,
                str(audio_filename),
                voice_speed
            )
            
            synthesis_time = time.time() - synthesis_start
            
            # Read audio file and encode to base64
            encoding_start = time.time()
            with open(audio_filename, 'rb') as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            encoding_time = time.time() - encoding_start
            
            # Clean up temp file
            audio_filename.unlink(missing_ok=True)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'audio_base64': audio_base64,
                'format': output_format,
                'processing_time': processing_time,
                'text_length': len(text),
                'language': language,
                'voice_speed': voice_speed,
                'model_used': model_key,
                'audio_size_bytes': len(audio_data),
                'detailed_timing': {
                    'synthesis_ms': round(synthesis_time * 1000, 2),
                    'encoding_ms': round(encoding_time * 1000, 2),
                    'total_ms': round(processing_time * 1000, 2)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'language': language
            }
    
    def _synthesize_to_file(self, model, text: str, file_path: str, speed: float):
        """Synthesize speech to file (runs in executor thread)."""
        try:
            # Different synthesis methods based on model type
            if hasattr(model, 'tts_to_file'):
                # Standard TTS models
                model.tts_to_file(
                    text=text,
                    file_path=file_path,
                    speed=speed
                )
            else:
                # Fallback method
                model.tts_to_file(text, file_path)
                
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            raise
    
    async def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available TTS languages."""
        if not TTS_AVAILABLE:
            return []
        
        return [
            {
                'code': lang,
                'name': config['description'],
                'model': config['model_name'],
                'loaded': lang in self._models
            }
            for lang, config in self.model_configs.items()
        ]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get TTS service health status."""
        return {
            'tts_available': TTS_AVAILABLE,
            'initialized': self._initialized,
            'loaded_models': list(self._models.keys()),
            'available_languages': list(self.model_configs.keys()),
            'temp_dir': str(self.temp_dir),
            'temp_dir_exists': self.temp_dir.exists()
        }


# Create singleton instance
tts_service = TTSService()


class CachedTTSService:
    """TTS Service with caching support."""
    
    def __init__(self, base_service: TTSService):
        self.base_service = base_service
        self._cache = {}  # Simple in-memory cache
        self.max_cache_size = 100
    
    def _create_cache_key(self, text: str, language: str, voice_speed: float) -> str:
        """Create cache key for TTS request."""
        content = f"{text}:{language}:{voice_speed}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def synthesize_speech(self, text: str, **kwargs) -> Dict[str, Any]:
        """Synthesize speech with caching."""
        language = kwargs.get('language', 'en')
        voice_speed = kwargs.get('voice_speed', 1.0)
        
        # Check cache first
        cache_key = self._create_cache_key(text, language, voice_speed)
        
        if cache_key in self._cache:
            cached_result = self._cache[cache_key].copy()
            cached_result['cache_hit'] = True
            cached_result['processing_time'] = 0.001  # Near-instant cache hit
            return cached_result
        
        # Generate TTS
        result = await self.base_service.synthesize_speech(text, **kwargs)
        
        # Cache successful results (exclude audio data to save memory)
        if result.get('success') and len(self._cache) < self.max_cache_size:
            cache_result = result.copy()
            cache_result['cache_hit'] = False
            self._cache[cache_key] = cache_result
        
        return result
    
    async def clear_cache(self):
        """Clear TTS cache."""
        self._cache.clear()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._cache),
            'max_cache_size': self.max_cache_size,
            'cache_keys': list(self._cache.keys())[:10]  # First 10 keys
        }


# Create cached service instance
cached_tts_service = CachedTTSService(tts_service)
