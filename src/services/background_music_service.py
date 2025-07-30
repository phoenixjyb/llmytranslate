"""
Background music service for phone calls.
Provides pleasant ambient sounds during AI processing.
"""

import asyncio
import logging
import base64
import random
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BackgroundMusicService:
    """
    Manages background music for phone calls.
    Provides ambient sounds during AI processing delays.
    """
    
    def __init__(self):
        self.music_dir = Path(__file__).parent.parent.parent / "audio_cache" / "background_music"
        self.ensure_music_directory()
        self.music_tracks = self._load_music_tracks()
        self.is_available = len(self.music_tracks) > 0
        
        logger.info(f"Background music service initialized. Available tracks: {len(self.music_tracks)}")
    
    def ensure_music_directory(self):
        """Ensure background music directory exists."""
        try:
            self.music_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple default track if none exist
            default_track = self.music_dir / "default_ambient.json"
            if not default_track.exists():
                self._create_default_music_track(default_track)
                
        except Exception as e:
            logger.warning(f"Failed to create music directory: {e}")
    
    def _create_default_music_track(self, track_path: Path):
        """Create a default ambient music track (metadata only)."""
        try:
            import json
            
            # This is just metadata - actual audio would be generated or provided
            default_track_info = {
                "name": "Gentle Ambient",
                "duration": 30.0,
                "type": "ambient",
                "description": "Soft ambient tones for background",
                "audio_data": None,  # Would contain base64 encoded audio in real implementation
                "format": "mp3",
                "volume": 0.3
            }
            
            with open(track_path, 'w') as f:
                json.dump(default_track_info, f, indent=2)
                
            logger.info("Created default background music track metadata")
            
        except Exception as e:
            logger.warning(f"Failed to create default music track: {e}")
    
    def _load_music_tracks(self) -> Dict[str, Dict[str, Any]]:
        """Load available music tracks."""
        tracks = {}
        
        try:
            if not self.music_dir.exists():
                return tracks
            
            for track_file in self.music_dir.glob("*.json"):
                try:
                    import json
                    with open(track_file, 'r') as f:
                        track_info = json.load(f)
                        tracks[track_file.stem] = track_info
                except Exception as e:
                    logger.warning(f"Failed to load music track {track_file}: {e}")
            
            if not tracks:
                # Create a synthetic ambient track
                tracks["synthetic_ambient"] = {
                    "name": "Synthetic Ambient",
                    "duration": 10.0,
                    "type": "synthetic",
                    "description": "Generated ambient sound",
                    "audio_data": self._generate_synthetic_ambient(),
                    "format": "wav",
                    "volume": 0.2
                }
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to load music tracks: {e}")
            return {}
    
    def _generate_synthetic_ambient(self) -> Optional[str]:
        """Generate a simple synthetic ambient sound."""
        try:
            import numpy as np
            import wave
            import io
            
            # Generate 10 seconds of soft ambient sound
            sample_rate = 16000
            duration = 10.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Create a gentle ambient sound with multiple sine waves
            frequency1 = 200  # Base frequency
            frequency2 = 300  # Harmonic
            frequency3 = 150  # Sub-harmonic
            
            # Generate waves with fade in/out
            wave1 = 0.1 * np.sin(2 * np.pi * frequency1 * t)
            wave2 = 0.05 * np.sin(2 * np.pi * frequency2 * t + np.pi/4)
            wave3 = 0.08 * np.sin(2 * np.pi * frequency3 * t + np.pi/2)
            
            # Combine waves
            combined = wave1 + wave2 + wave3
            
            # Apply fade in/out
            fade_samples = int(sample_rate * 1.0)  # 1 second fade
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            
            combined[:fade_samples] *= fade_in
            combined[-fade_samples:] *= fade_out
            
            # Convert to 16-bit integers
            audio_data = (combined * 32767).astype(np.int16)
            
            # Convert to WAV format in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Encode as base64
            wav_buffer.seek(0)
            audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            logger.warning(f"Failed to generate synthetic ambient sound: {e}")
            return None
    
    def get_random_track(self) -> Optional[Dict[str, Any]]:
        """Get a random background music track."""
        if not self.music_tracks:
            return None
        
        track_name = random.choice(list(self.music_tracks.keys()))
        return self.music_tracks[track_name]
    
    def get_track_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific background music track by name."""
        return self.music_tracks.get(name)
    
    async def get_background_music(self, duration: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        Get background music for a specific duration.
        
        Args:
            duration: Desired duration in seconds
            
        Returns:
            Dict with music data or None if not available
        """
        if not self.is_available:
            return None
        
        try:
            # Get a suitable track
            track = self.get_random_track()
            if not track:
                return None
            
            # For now, return the track as-is
            # In a more advanced implementation, we could trim or loop the audio
            return {
                "name": track["name"],
                "audio_data": track.get("audio_data"),
                "format": track.get("format", "wav"),
                "volume": track.get("volume", 0.3),
                "duration": min(track.get("duration", 10.0), duration)
            }
            
        except Exception as e:
            logger.error(f"Failed to get background music: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check background music service health."""
        return {
            "status": "healthy" if self.is_available else "limited",
            "available_tracks": len(self.music_tracks),
            "tracks": list(self.music_tracks.keys()),
            "music_directory": str(self.music_dir),
            "synthetic_generation": "numpy" in globals()
        }

# Global instance
background_music_service = BackgroundMusicService()
