"""
Background Music API routes for phone calls.
Provides ambient music selection and streaming.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import io
import base64

from ...services.background_music_service import BackgroundMusicService

router = APIRouter(prefix="/background-music", tags=["background-music"])

# Request/Response Models
class MusicTrackInfo(BaseModel):
    name: str
    duration: float
    style: str
    description: str
    volume: float
    has_audio: bool

class MusicSelectionRequest(BaseModel):
    style: Optional[str] = None  # "gentle", "meditation", "uplifting", "focus"
    track_name: Optional[str] = None
    call_session_id: Optional[str] = None

class MusicResponse(BaseModel):
    success: bool
    track_info: Optional[MusicTrackInfo] = None
    audio_data: Optional[str] = None  # base64 encoded
    error: Optional[str] = None

# Initialize service
background_music_service = BackgroundMusicService()

@router.get("/tracks", response_model=List[MusicTrackInfo])
async def list_available_tracks():
    """Get list of all available background music tracks."""
    try:
        tracks = background_music_service.list_available_tracks()
        return [MusicTrackInfo(**track) for track in tracks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tracks: {str(e)}")

@router.get("/track/{track_name}", response_model=MusicResponse)
async def get_track_by_name(track_name: str):
    """Get a specific background music track by name."""
    try:
        track = background_music_service.get_track_by_name(track_name)
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        track_info = MusicTrackInfo(
            name=track.get("name", track_name),
            duration=track.get("duration", 0),
            style=track.get("style", "unknown"),
            description=track.get("description", ""),
            volume=track.get("volume", 0.3),
            has_audio=track.get("audio_data") is not None
        )
        
        audio_data = None
        if track.get("audio_data"):
            audio_data = base64.b64encode(track["audio_data"]).decode('utf-8')
        
        return MusicResponse(
            success=True,
            track_info=track_info,
            audio_data=audio_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get track: {str(e)}")

@router.post("/select", response_model=MusicResponse)
async def select_background_music(request: MusicSelectionRequest):
    """Select background music based on style or track name."""
    try:
        track = None
        
        if request.track_name:
            track = background_music_service.get_track_by_name(request.track_name)
        elif request.style:
            track = background_music_service.get_track_by_style(request.style)
        else:
            track = background_music_service.get_random_track()
        
        if not track:
            # Generate default track if none found
            track = background_music_service.get_background_music("default")
        
        track_info = MusicTrackInfo(
            name=track.get("name", "Generated Track"),
            duration=track.get("duration", 15.0),
            style=track.get("style", "ambient"),
            description=track.get("description", "Ambient background music"),
            volume=track.get("volume", 0.3),
            has_audio=track.get("audio_data") is not None
        )
        
        audio_data = None
        if track.get("audio_data"):
            audio_data = base64.b64encode(track["audio_data"]).decode('utf-8')
        
        return MusicResponse(
            success=True,
            track_info=track_info,
            audio_data=audio_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select music: {str(e)}")

@router.get("/styles")
async def get_available_styles():
    """Get list of available music styles."""
    return JSONResponse({
        "styles": [
            {
                "name": "gentle",
                "description": "Soft ambient waves for relaxation during phone calls"
            },
            {
                "name": "meditation", 
                "description": "Deep meditative tones for calm conversations"
            },
            {
                "name": "uplifting",
                "description": "Bright and uplifting tones for positive conversations"
            },
            {
                "name": "focus",
                "description": "Minimal ambient tones for enhanced focus during calls"
            },
            {
                "name": "default",
                "description": "Standard ambient background music"
            }
        ]
    })

@router.get("/health")
async def background_music_health():
    """Health check for background music service."""
    try:
        tracks = background_music_service.list_available_tracks()
        return JSONResponse({
            "status": "healthy",
            "tracks_available": len(tracks),
            "service": "BackgroundMusicService"
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "service": "BackgroundMusicService"
        }, status_code=500)

@router.post("/generate")
async def generate_custom_track(style: str = "default", duration: float = 15.0):
    """Generate a custom background music track on demand."""
    try:
        track = background_music_service.get_background_music(style)
        
        track_info = MusicTrackInfo(
            name=f"Generated {style.title()} Track",
            duration=duration,
            style=style,
            description=f"Custom generated {style} ambient music",
            volume=0.3,
            has_audio=track.get("audio_data") is not None
        )
        
        audio_data = None
        if track.get("audio_data"):
            audio_data = base64.b64encode(track["audio_data"]).decode('utf-8')
        
        return MusicResponse(
            success=True,
            track_info=track_info,
            audio_data=audio_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate track: {str(e)}")
