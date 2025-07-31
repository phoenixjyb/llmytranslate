"""
Enhanced Background Music Generator
Creates multiple ambient music tracks for phone calls
"""

import numpy as np
import wave
import io
import base64
import json
from pathlib import Path

def generate_ambient_track(name: str, duration: float = 15.0, style: str = "gentle") -> dict:
    """Generate different styles of ambient music."""
    sample_rate = 22050  # Higher quality
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    if style == "gentle":
        # Soft, gentle ambient with nature-like tones
        freq1, freq2, freq3 = 220, 330, 165  # A3, E4, E3
        wave1 = 0.08 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.05 * np.sin(2 * np.pi * freq2 * t + np.pi/3)
        wave3 = 0.06 * np.sin(2 * np.pi * freq3 * t + np.pi/2)
        # Add some gentle modulation
        mod = 0.02 * np.sin(2 * np.pi * 0.1 * t)
        combined = wave1 + wave2 + wave3 + mod
        
    elif style == "meditation":
        # Deeper, more meditative tones
        freq1, freq2, freq3 = 110, 165, 82.4  # A2, E3, E2
        wave1 = 0.1 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.07 * np.sin(2 * np.pi * freq2 * t + np.pi/4)
        wave3 = 0.08 * np.sin(2 * np.pi * freq3 * t + np.pi/6)
        # Add breathing-like modulation
        breathing = 0.03 * np.sin(2 * np.pi * 0.05 * t)
        combined = wave1 + wave2 + wave3 + breathing
        
    elif style == "uplifting":
        # Brighter, more positive tones
        freq1, freq2, freq3, freq4 = 261.6, 329.6, 392, 523.2  # C4, E4, G4, C5
        wave1 = 0.06 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.05 * np.sin(2 * np.pi * freq2 * t + np.pi/4)
        wave3 = 0.04 * np.sin(2 * np.pi * freq3 * t + np.pi/3)
        wave4 = 0.03 * np.sin(2 * np.pi * freq4 * t + np.pi/2)
        # Add gentle sparkle
        sparkle = 0.02 * np.sin(2 * np.pi * 0.3 * t) * np.sin(2 * np.pi * 1760 * t)
        combined = wave1 + wave2 + wave3 + wave4 + sparkle
        
    elif style == "focus":
        # Minimal, focused ambient for concentration
        freq1, freq2 = 440, 660  # A4, E5
        wave1 = 0.07 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.04 * np.sin(2 * np.pi * freq2 * t + np.pi/2)
        # Add subtle pulse
        pulse = 0.02 * np.sin(2 * np.pi * 0.2 * t)
        combined = wave1 + wave2 + pulse
    
    else:  # default gentle
        freq1, freq2, freq3 = 200, 300, 150
        wave1 = 0.1 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.05 * np.sin(2 * np.pi * freq2 * t + np.pi/4)
        wave3 = 0.08 * np.sin(2 * np.pi * freq3 * t + np.pi/2)
        combined = wave1 + wave2 + wave3
    
    # Apply fade in/out
    fade_duration = 2.0  # 2 seconds
    fade_samples = int(sample_rate * fade_duration)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    combined[:fade_samples] *= fade_in
    combined[-fade_samples:] *= fade_out
    
    # Normalize and convert to 16-bit
    combined = combined / np.max(np.abs(combined)) * 0.8  # Prevent clipping
    audio_data = (combined * 32767).astype(np.int16)
    
    # Convert to WAV
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    wav_buffer.seek(0)
    audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
    
    return {
        "name": name,
        "duration": duration,
        "type": "generated",
        "style": style,
        "description": f"{style.capitalize()} ambient music for phone calls",
        "audio_data": audio_base64,
        "format": "wav",
        "volume": 0.25,
        "sample_rate": sample_rate
    }

def create_music_library():
    """Create a library of background music tracks."""
    
    tracks = [
        ("Gentle Waves", 15.0, "gentle"),
        ("Deep Meditation", 20.0, "meditation"), 
        ("Bright Morning", 12.0, "uplifting"),
        ("Focused Mind", 18.0, "focus"),
        ("Peaceful Garden", 16.0, "gentle"),
    ]
    
    music_dir = Path("audio_cache/background_music")
    music_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎵 Generating background music library...")
    
    for name, duration, style in tracks:
        print(f"   Creating: {name} ({style}, {duration}s)")
        
        try:
            track_data = generate_ambient_track(name, duration, style)
            
            # Save as JSON file
            filename = name.lower().replace(" ", "_") + ".json"
            filepath = music_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(track_data, f, indent=2)
            
            print(f"   ✅ Saved: {filename}")
            
        except Exception as e:
            print(f"   ❌ Failed to create {name}: {e}")
    
    print("\n🎉 Background music library created!")
    print(f"📁 Location: {music_dir.absolute()}")

if __name__ == "__main__":
    create_music_library()
