"""
Background music service for phone calls.
Provides pleasant ambient sounds during AI processing.
"""

import asyncio
import logging
import base64
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

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
        """Generate a simple synthetic ambient sound using basic math."""
        try:
            import wave
            import struct
            import math
            import io
            
            # Generate 15 seconds of soft ambient sound
            sample_rate = 22050
            duration = 15.0
            amplitude = 0.2
            
            # Generate samples using basic math
            samples = []
            total_samples = int(sample_rate * duration)
            fade_samples = int(sample_rate * 1.0)  # 1 second fade
            
            for i in range(total_samples):
                t = i / sample_rate
                
                # Create layered ambient sound
                base_wave = amplitude * math.sin(2 * math.pi * 220 * t)  # A3
                harmonic = 0.3 * amplitude * math.sin(2 * math.pi * 330 * t + math.pi/3)  # E4
                sub_harmonic = 0.4 * amplitude * math.sin(2 * math.pi * 165 * t + math.pi/2)  # E3
                modulation = 0.1 * amplitude * math.sin(2 * math.pi * 0.1 * t)  # Slow modulation
                
                value = base_wave + harmonic + sub_harmonic + modulation
                
                # Apply fade in/out
                if i < fade_samples:
                    value *= (i / fade_samples)
                elif i > total_samples - fade_samples:
                    remaining = total_samples - i
                    value *= (remaining / fade_samples)
                
                samples.append(int(value * 32767))
            
            # Create WAV file in memory
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)      # Mono
                wav_file.setsampwidth(2)      # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                
                # Pack samples as 16-bit signed integers
                packed_data = struct.pack('<' + 'h' * len(samples), *samples)
                wav_file.writeframes(packed_data)
            
            buffer.seek(0)
            wav_data = buffer.read()
            
            # Return base64 encoded audio
            import base64
            return base64.b64encode(wav_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to generate synthetic ambient: {e}")
            return None
            
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
    
    def get_track_by_style(self, style: str) -> Optional[Dict[str, Any]]:
        """Get a track by style (gentle, meditation, uplifting, focus)."""
        style_tracks = [
            track for track in self.music_tracks.values() 
            if track.get("style") == style
        ]
        if style_tracks:
            return random.choice(style_tracks)
        return self.get_random_track()
    
    def get_track_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific background music track by name."""
        return self.music_tracks.get(name)
    
    def list_available_tracks(self) -> List[Dict[str, Any]]:
        """List all available background music tracks with their info."""
        return [
            {
                "name": track.get("name", "Unknown"),
                "duration": track.get("duration", 0),
                "style": track.get("style", "unknown"),
                "description": track.get("description", ""),
                "volume": track.get("volume", 0.3),
                "has_audio": track.get("audio_data") is not None
            }
            for track in self.music_tracks.values()
        ]
    
    def get_background_music(self, style: str = "default") -> Dict[str, Any]:
        """
        Get background music for phone calls.
        
        Args:
            style: Style of music ("gentle", "meditation", "uplifting", "focus", "default")
            
        Returns:
            Dict with music data
        """
        try:
            # Try to get pre-loaded track by style
            track = self.get_track_by_style(style)
            
            if track and track.get("audio_data"):
                return track
            
            # Generate synthetic audio if no pre-loaded track available
            audio_data = self._generate_synthetic_ambient_by_style(style)
            
            return {
                "name": f"{style.title()} Ambient",
                "duration": 15.0,
                "type": "synthetic",
                "style": style,
                "description": f"Generated {style} ambient music for phone calls",
                "audio_data": audio_data,
                "format": "wav",
                "volume": 0.3
            }
            
        except Exception as e:
            logger.error(f"Failed to get background music: {e}")
            return {
                "name": "Silent",
                "duration": 0.0,
                "type": "silent",
                "audio_data": None,
                "format": "wav",
                "volume": 0.0
            }
    
    def _generate_synthetic_ambient_by_style(self, style: str) -> Optional[str]:
        """Generate synthetic ambient audio for specific style."""
        try:
            import wave
            import struct
            import math
            import io
            import base64
            
            # Style-specific parameters
            style_params = {
                "gentle": {"freq": 220, "harmonics": [330, 165], "amplitude": 0.15},
                "meditation": {"freq": 110, "harmonics": [165, 82], "amplitude": 0.2},
                "uplifting": {"freq": 330, "harmonics": [440, 220], "amplitude": 0.18},
                "focus": {"freq": 165, "harmonics": [247, 110], "amplitude": 0.12},
                "default": {"freq": 196, "harmonics": [294, 147], "amplitude": 0.16}
            }
            
            params = style_params.get(style, style_params["default"])
            
            sample_rate = 22050
            duration = 15.0
            total_samples = int(sample_rate * duration)
            fade_samples = int(sample_rate * 1.0)
            
            samples = []
            for i in range(total_samples):
                t = i / sample_rate
                
                # Base frequency
                value = params["amplitude"] * math.sin(2 * math.pi * params["freq"] * t)
                
                # Add harmonics
                for j, harmonic_freq in enumerate(params["harmonics"]):
                    amplitude_factor = 0.3 - (j * 0.1)  # Decreasing amplitude for higher harmonics
                    phase = (j + 1) * math.pi / 3  # Different phase for each harmonic
                    value += amplitude_factor * params["amplitude"] * math.sin(2 * math.pi * harmonic_freq * t + phase)
                
                # Add gentle modulation
                value += 0.05 * params["amplitude"] * math.sin(2 * math.pi * 0.1 * t)
                
                # Apply fade in/out
                if i < fade_samples:
                    value *= (i / fade_samples)
                elif i > total_samples - fade_samples:
                    remaining = total_samples - i
                    value *= (remaining / fade_samples)
                
                samples.append(int(value * 32767))
            
            # Create WAV in memory
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                packed_data = struct.pack('<' + 'h' * len(samples), *samples)
                wav_file.writeframes(packed_data)
            
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to generate {style} ambient audio: {e}")
            return None
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
