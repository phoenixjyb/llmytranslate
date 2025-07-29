# TTS Service Integration Plan for LLM Translation Service

## 🎯 Recommended TTS Solution: Coqui TTS + FastAPI Integration

### Why Coqui TTS is Perfect for Your Setup:
- ✅ **Local Deployment**: No external dependencies, runs offline
- ✅ **Python Integration**: Seamless FastAPI integration
- ✅ **High Quality**: State-of-the-art neural TTS models
- ✅ **Multi-language**: Supports Chinese, English, and many others
- ✅ **GPU Acceleration**: Works with your NVIDIA Quadro P2000
- ✅ **Open Source**: No licensing costs or API limits

## 🚀 Implementation Plan

### Phase 1: Basic TTS Service Integration

#### 1. Install Coqui TTS
```powershell
# In your existing virtual environment
pip install coqui-tts
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 2. Create TTS Service Class
```python
# src/services/tts_service.py
from TTS.api import TTS
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import time

class TTSService:
    def __init__(self):
        # Initialize models for different languages
        self.models = {
            'en': TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC"),
            'zh': TTS(model_name="tts_models/zh-CN/baker/tacotron2-DDC"),
            'multilingual': TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
        }
        self.temp_dir = Path(tempfile.gettempdir()) / "llm_tts"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def synthesize_speech(
        self, 
        text: str, 
        language: str = 'en',
        voice_speed: float = 1.0,
        output_format: str = 'wav'
    ) -> Dict[str, Any]:
        """Convert text to speech and return audio data."""
        
        start_time = time.time()
        
        try:
            # Select appropriate model
            model_key = language if language in self.models else 'multilingual'
            tts_model = self.models[model_key]
            
            # Generate unique filename
            audio_filename = self.temp_dir / f"tts_{int(time.time() * 1000)}.{output_format}"
            
            # Synthesize speech (run in thread to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: tts_model.tts_to_file(
                    text=text,
                    file_path=str(audio_filename),
                    speed=voice_speed
                )
            )
            
            # Read audio file and encode to base64
            with open(audio_filename, 'rb') as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up temp file
            audio_filename.unlink()
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'audio_base64': audio_base64,
                'format': output_format,
                'processing_time': processing_time,
                'text_length': len(text),
                'language': language,
                'voice_speed': voice_speed
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
```

#### 3. Add TTS API Routes
```python
# src/api/routes/tts.py
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
from ...services.tts_service import TTSService
from ...models.schemas import TTSRequest, TTSResponse

router = APIRouter()
tts_service = TTSService()

@router.post("/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(
    text: str = Form(..., description="Text to convert to speech"),
    language: str = Form(default="en", description="Language code (en, zh, etc.)"),
    voice_speed: float = Form(default=1.0, description="Voice speed (0.5-2.0)"),
    output_format: str = Form(default="wav", description="Audio format (wav, mp3)")
) -> TTSResponse:
    """Convert text to speech."""
    
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
    
    result = await tts_service.synthesize_speech(
        text=text,
        language=language,
        voice_speed=voice_speed,
        output_format=output_format
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result['error'])
    
    return TTSResponse(**result)

@router.post("/translate-and-speak")
async def translate_and_speak(
    text: str = Form(..., description="Text to translate and speak"),
    from_lang: str = Form(..., description="Source language"),
    to_lang: str = Form(..., description="Target language"),
    voice_speed: float = Form(default=1.0, description="Voice speed")
):
    """Translate text and convert to speech in one request."""
    
    # Import translation service
    from ...services.translation_service import translation_service
    
    # First translate the text
    translation_result = await translation_service.translate_text(
        text=text,
        source_lang=from_lang,
        target_lang=to_lang
    )
    
    if not translation_result.get('success'):
        raise HTTPException(status_code=500, detail="Translation failed")
    
    translated_text = translation_result['translation']
    
    # Then convert to speech
    tts_result = await tts_service.synthesize_speech(
        text=translated_text,
        language=to_lang,
        voice_speed=voice_speed
    )
    
    if not tts_result['success']:
        raise HTTPException(status_code=500, detail="TTS failed")
    
    return {
        'original_text': text,
        'translated_text': translated_text,
        'audio_base64': tts_result['audio_base64'],
        'translation_time': translation_result.get('response_time', 0),
        'tts_time': tts_result['processing_time'],
        'total_time': translation_result.get('response_time', 0) + tts_result['processing_time']
    }
```

#### 4. Add TTS Models to Schemas
```python
# Add to src/models/schemas.py
from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_speed: float = 1.0
    output_format: str = "wav"

class TTSResponse(BaseModel):
    success: bool
    audio_base64: Optional[str] = None
    format: Optional[str] = None
    processing_time: float
    text_length: int
    language: str
    voice_speed: float
    error: Optional[str] = None
```

#### 5. Update Main App
```python
# In src/main.py, add TTS routes
from .api.routes import translation, health, admin, discovery, optimized, chatbot, tts

def create_app() -> FastAPI:
    # ... existing code ...
    
    app.include_router(tts.router, prefix="/api")  # Add TTS routes
    
    # ... rest of existing code ...
```

### Phase 2: Enhanced Features

#### 1. Voice Cloning (Advanced)
```python
# Enhanced TTS with voice cloning capabilities
class AdvancedTTSService(TTSService):
    async def clone_voice_and_speak(
        self, 
        text: str, 
        reference_audio_base64: str,
        language: str = 'en'
    ):
        """Clone a voice from reference audio and synthesize speech."""
        # Implementation using XTTS v2 model
        pass
```

#### 2. Multi-Speaker Support
```python
# Support for different speaker voices
AVAILABLE_SPEAKERS = {
    'en': ['female_1', 'male_1', 'female_2', 'male_2'],
    'zh': ['female_zh', 'male_zh']
}
```

#### 3. Real-time Streaming TTS
```python
# Streaming TTS for longer texts
@router.post("/tts/stream")
async def stream_tts(text: str):
    """Stream TTS audio as it's generated."""
    # WebSocket implementation for real-time audio streaming
    pass
```

## 🎨 Frontend Integration

### Enhanced Translation UI with TTS
```javascript
// Add to web/assets/chat.js or create new tts.js
class TTSManager {
    constructor() {
        this.isPlaying = false;
        this.currentAudio = null;
    }
    
    async playTranslation(text, language = 'en') {
        try {
            const response = await fetch('/api/tts/synthesize', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({
                    text: text,
                    language: language,
                    voice_speed: 1.0,
                    output_format: 'wav'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Convert base64 to audio and play
                const audioData = `data:audio/wav;base64,${result.audio_base64}`;
                this.currentAudio = new Audio(audioData);
                
                this.currentAudio.onloadstart = () => this.showPlayingIndicator();
                this.currentAudio.onended = () => this.hidePlayingIndicator();
                
                await this.currentAudio.play();
            }
        } catch (error) {
            console.error('TTS Error:', error);
        }
    }
    
    showPlayingIndicator() {
        // Add visual indicator that audio is playing
    }
    
    hidePlayingIndicator() {
        // Remove visual indicator
    }
}

// Integration with existing translation UI
const ttsManager = new TTSManager();

// Add play button to translation results
function addTTSButton(translationElement, text, language) {
    const playButton = document.createElement('button');
    playButton.innerHTML = '🔊 Play';
    playButton.onclick = () => ttsManager.playTranslation(text, language);
    translationElement.appendChild(playButton);
}
```

## 🔧 Configuration Updates

### Environment Variables
```env
# Add to .env file
TTS__ENABLED=true
TTS__DEFAULT_LANGUAGE=en
TTS__MAX_TEXT_LENGTH=5000
TTS__VOICE_SPEED=1.0
TTS__OUTPUT_FORMAT=wav
TTS__GPU_ACCELERATION=true
TTS__CACHE_ENABLED=true
```

### Requirements Update
```txt
# Add to requirements.txt
coqui-tts>=0.20.0
torch>=2.0.0
torchaudio>=2.0.0
librosa>=0.10.0
soundfile>=0.12.1
```

## 🚀 Alternative TTS Options

### 1. Edge-TTS (Microsoft) - Free & Fast
```python
# Lightweight alternative using Microsoft Edge TTS
import edge_tts
import asyncio

async def edge_tts_synthesize(text: str, voice: str = "en-US-AriaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name
```

### 2. Google Cloud TTS API
```python
# For production with high quality needs
from google.cloud import texttospeech

class GoogleTTSService:
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
    
    async def synthesize(self, text: str, language: str = "en-US"):
        # Implementation using Google Cloud TTS
        pass
```

### 3. Azure Cognitive Services TTS
```python
# Microsoft Azure TTS integration
import azure.cognitiveservices.speech as speechsdk

class AzureTTSService:
    def __init__(self, subscription_key: str, region: str):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
```

## 📊 Performance Considerations

### Caching Strategy
```python
# TTS Result Caching
from ...services.cache_service import cache_service

class CachedTTSService(TTSService):
    async def synthesize_speech(self, text: str, **kwargs):
        cache_key = f"tts:{hash(text)}:{kwargs.get('language', 'en')}:{kwargs.get('voice_speed', 1.0)}"
        
        # Check cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        # Generate TTS
        result = await super().synthesize_speech(text, **kwargs)
        
        # Cache successful results
        if result.get('success'):
            await cache_service.set(cache_key, result, ttl=3600)  # 1 hour
        
        return result
```

## 🎯 Integration Benefits

1. **🔄 Seamless Workflow**: Translate → Speak in one request
2. **🌐 Multi-language**: Support for your existing language pairs
3. **⚡ Performance**: Local processing, no API delays
4. **🔒 Privacy**: All processing stays local
5. **💰 Cost-effective**: No per-request API charges
6. **🔧 Customizable**: Full control over voice characteristics

## 📈 Usage Examples

### Translation + TTS Workflow
```python
# Example API call for translate-and-speak
response = requests.post('http://localhost:8000/api/translate-and-speak', data={
    'text': 'Hello, how are you today?',
    'from_lang': 'en',
    'to_lang': 'zh',
    'voice_speed': 1.2
})

# Returns: translated text + audio in base64
audio_data = response.json()['audio_base64']
```

This TTS integration will perfectly complement your existing translation service, providing a complete language solution with both text translation and speech synthesis capabilities!
