"""
Simple Background Music Generator (without numpy dependency)
Creates basic ambient music files for phone calls.
"""

import os
import json
import wave
import struct
import math
from pathlib import Path

def create_ambient_tone(frequency, duration, sample_rate=22050, amplitude=0.2):
    """Create a simple ambient tone using basic math."""
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        # Create a simple sine wave with gentle modulation
        base_wave = amplitude * math.sin(2 * math.pi * frequency * t)
        # Add gentle modulation
        modulation = 0.1 * amplitude * math.sin(2 * math.pi * 0.1 * t)
        value = base_wave + modulation
        
        # Apply fade in/out
        fade_duration = 1.0
        fade_samples = int(fade_duration * sample_rate)
        if i < fade_samples:
            value *= (i / fade_samples)
        elif i > len(range(int(sample_rate * duration))) - fade_samples:
            remaining = len(range(int(sample_rate * duration))) - i
            value *= (remaining / fade_samples)
        
        samples.append(int(value * 32767))  # Convert to 16-bit
    return samples

def save_wav_file(samples, filename, sample_rate=22050):
    """Save samples to a WAV file."""
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        # Pack samples as 16-bit signed integers
        packed_data = struct.pack('<' + 'h' * len(samples), *samples)
        wav_file.writeframes(packed_data)

def create_background_music_track(name, style, description, frequency, duration=15.0):
    """Create a background music track with both WAV file and metadata."""
    
    # Create directory
    music_dir = Path("audio_cache/background_music")
    music_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate audio
    print(f"🎵 Generating {name} ({style})...")
    samples = create_ambient_tone(frequency, duration)
    
    # Save WAV file
    wav_path = music_dir / f"{name}.wav"
    save_wav_file(samples, str(wav_path))
    print(f"   ✅ Created WAV: {wav_path}")
    
    # Create metadata
    metadata = {
        "name": name.replace("_", " ").title(),
        "style": style,
        "description": description,
        "duration": duration,
        "frequency": frequency,
        "volume": 0.3,
        "file_path": str(wav_path),
        "sample_rate": 22050,
        "channels": 1,
        "bit_depth": 16
    }
    
    # Save metadata JSON
    json_path = music_dir / f"{name}.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✅ Created metadata: {json_path}")
    
    return metadata

def main():
    """Generate background music library."""
    print("🎼 Creating Background Music Library...")
    
    tracks = [
        {
            "name": "gentle_waves",
            "style": "gentle", 
            "description": "Soft ambient waves for relaxation during phone calls",
            "frequency": 220,  # A3
            "duration": 18.0
        },
        {
            "name": "deep_meditation",
            "style": "meditation",
            "description": "Deep meditative tones for calm conversations", 
            "frequency": 110,  # A2
            "duration": 20.0
        },
        {
            "name": "bright_morning",
            "style": "uplifting",
            "description": "Bright and uplifting tones for positive conversations",
            "frequency": 330,  # E4
            "duration": 15.0
        },
        {
            "name": "focused_mind", 
            "style": "focus",
            "description": "Minimal ambient tones for enhanced focus during calls",
            "frequency": 165,  # E3
            "duration": 16.0
        },
        {
            "name": "default_ambient",
            "style": "default",
            "description": "Standard ambient background music for phone calls",
            "frequency": 196,  # G3
            "duration": 17.0
        }
    ]
    
    for track in tracks:
        create_background_music_track(**track)
    
    print(f"\n✅ Background music library created!")
    print(f"📁 Location: audio_cache/background_music/")
    print(f"🎵 Tracks: {len(tracks)} ambient music files")
    print("\n📋 Available tracks:")
    for track in tracks:
        print(f"   • {track['name']} - {track['description']}")

if __name__ == "__main__":
    main()
