"""
Pydantic models and schemas for the LLM Translation Service.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TranslationRequest(BaseModel):
    """Translation request model compatible with Baidu API."""
    q: str = Field(..., description="Text to translate")
    from_lang: str = Field(..., alias="from", description="Source language code")
    to: str = Field(..., description="Target language code")
    appid: Optional[str] = Field(None, description="App ID")
    salt: Optional[str] = Field(None, description="Random salt")
    sign: Optional[str] = Field(None, description="Signature")
    translation_mode: Optional[str] = Field("succinct", description="Translation mode: 'succinct' or 'verbose'")
    
    @field_validator('translation_mode')
    @classmethod
    def validate_translation_mode(cls, v):
        if v not in ["succinct", "verbose"]:
            return "succinct"  # Default fallback
        return v


class TranslationResult(BaseModel):
    """Individual translation result."""
    src: str = Field(..., description="Source text")
    dst: str = Field(..., description="Translated text")


class TranslationResponse(BaseModel):
    """Translation response model compatible with Baidu API."""
    from_lang: str = Field(..., alias="from", description="Source language")
    to: str = Field(..., description="Target language")
    trans_result: List[TranslationResult] = Field(..., description="Translation results")
    error_code: Optional[str] = Field("52000", description="Error code (52000 = success)")
    error_msg: Optional[str] = Field("success", description="Error message")


class SupportedLanguagesResponse(BaseModel):
    """Supported languages response."""
    languages: Dict[str, str] = Field(..., description="Language code to name mapping")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    services: Dict[str, Any] = Field(..., description="Service health details")


class StatisticsResponse(BaseModel):
    """Statistics response."""
    total_requests: int = Field(..., description="Total translation requests")
    total_characters: int = Field(..., description="Total characters translated")
    average_response_time: float = Field(..., description="Average response time in seconds")
    uptime: str = Field(..., description="Service uptime")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")


class APIKeyInfo(BaseModel):
    """API key information."""
    app_id: str = Field(..., description="App ID")
    app_secret: str = Field(..., description="App secret")
    name: str = Field(..., description="Key name")
    is_active: bool = Field(True, description="Key active status")
    rate_limit_per_minute: int = Field(60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(1000, description="Rate limit per hour")
    rate_limit_per_day: int = Field(10000, description="Rate limit per day")
    created_at: Union[str, datetime] = Field(..., description="Creation timestamp")
    last_used_at: Optional[Union[str, datetime]] = Field(None, description="Last usage timestamp")
    requests_count: int = Field(0, description="Total requests count")
    
    @field_validator('created_at', 'last_used_at', mode='before')
    @classmethod
    def validate_datetime_fields(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class OllamaRequest(BaseModel):
    """Ollama API request model."""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Text prompt")
    stream: bool = Field(False, description="Stream response")
    options: Optional[Dict[str, Any]] = Field(None, description="Model options")


class OllamaResponse(BaseModel):
    """Ollama API response model."""
    model: str = Field(..., description="Model name")
    response: str = Field(..., description="Generated response")
    done: bool = Field(..., description="Completion status")
    context: Optional[List[int]] = Field(None, description="Context tokens")
    total_duration: Optional[int] = Field(None, description="Total duration in nanoseconds")
    load_duration: Optional[int] = Field(None, description="Load duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(None, description="Prompt evaluation count")
    prompt_eval_duration: Optional[int] = Field(None, description="Prompt evaluation duration")
    eval_count: Optional[int] = Field(None, description="Evaluation count")
    eval_duration: Optional[int] = Field(None, description="Evaluation duration")


class TTSRequest(BaseModel):
    """Text-to-Speech request model."""
    text: str = Field(..., description="Text to convert to speech")
    language: str = Field(default="en", description="Language code (en, zh, etc.)")
    voice_speed: float = Field(default=1.0, description="Voice speed (0.5-2.0)")
    output_format: str = Field(default="wav", description="Audio format (wav, mp3)")
    use_cache: bool = Field(default=True, description="Use cached results if available")
    
    @field_validator('voice_speed')
    @classmethod
    def validate_voice_speed(cls, v):
        if not (0.5 <= v <= 2.0):
            return 1.0  # Default fallback
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text_length(cls, v):
        if len(v) > 5000:
            raise ValueError("Text too long (max 5000 characters)")
        return v


class TTSResponse(BaseModel):
    """Text-to-Speech response model."""
    success: bool = Field(..., description="Success status")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio data")
    content_type: Optional[str] = Field(None, description="Audio content type")
    format: Optional[str] = Field(None, description="Audio format")
    processing_time: float = Field(..., description="Processing time in seconds")
    text_length: int = Field(..., description="Length of input text")
    language: str = Field(..., description="Language used")
    voice: Optional[str] = Field(None, description="Voice used")
    voice_speed: float = Field(..., description="Voice speed used")
    model_used: Optional[str] = Field(None, description="TTS model used")
    audio_size_bytes: Optional[int] = Field(None, description="Audio file size in bytes")
    cache_hit: Optional[bool] = Field(None, description="Whether result was from cache")
    error: Optional[str] = Field(None, description="Error message if failed")
    detailed_timing: Optional[Dict[str, float]] = Field(None, description="Detailed timing breakdown")
    
    # Voice chat specific fields
    text_input: Optional[str] = Field(None, description="Original user input (for voice chat)")
    text_response: Optional[str] = Field(None, description="AI response text (for voice chat)")
    stt_time: Optional[float] = Field(None, description="Speech-to-text processing time")
    llm_time: Optional[float] = Field(None, description="LLM processing time")
    tts_time: Optional[float] = Field(None, description="Text-to-speech processing time")
    conversation_flow: Optional[Dict[str, Any]] = Field(None, description="Voice conversation metadata")


class TranslateAndSpeakRequest(BaseModel):
    """Combined translation and TTS request model."""
    text: str = Field(..., description="Text to translate and speak")
    from_lang: str = Field(..., description="Source language code")
    to_lang: str = Field(..., description="Target language code")
    voice_speed: float = Field(default=1.0, description="Voice speed (0.5-2.0)")
    translation_mode: str = Field(default="succinct", description="Translation mode")
    use_cache: bool = Field(default=True, description="Use cached results if available")


class TranslateAndSpeakResponse(BaseModel):
    """Combined translation and TTS response model."""
    success: bool = Field(..., description="Success status")
    original_text: str = Field(..., description="Original input text")
    translated_text: str = Field(..., description="Translated text")
    audio_base64: str = Field(..., description="Base64-encoded audio data")
    audio_format: str = Field(..., description="Audio format")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    voice_speed: float = Field(..., description="Voice speed used")
    translation_mode: str = Field(..., description="Translation mode used")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    detailed_timing: Dict[str, float] = Field(..., description="Detailed timing breakdown")
    load_duration: Optional[int] = Field(None, description="Load duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(None, description="Prompt evaluation token count")
    prompt_eval_duration: Optional[int] = Field(None, description="Prompt evaluation duration")
    eval_count: Optional[int] = Field(None, description="Generation token count")
    eval_duration: Optional[int] = Field(None, description="Generation duration")
