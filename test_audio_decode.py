#!/usr/bin/env python3
"""
Test script to decode TTS audio response and save as WAV file
"""

import json
import base64

def test_audio_decode():
    """Decode the TTS response and save as WAV file."""
    try:
        # Read the response
        with open('tts_test_response.json', 'r') as f:
            data = json.load(f)

        if data['success']:
            # Decode the base64 audio
            audio_data = base64.b64decode(data['audio_base64'])
            
            # Save to a WAV file
            with open('test_audio.wav', 'wb') as f:
                f.write(audio_data)
            
            print(f'✅ Audio saved: {len(audio_data)} bytes')
            print(f'⏱️  Processing time: {data["processing_time"]:.2f} seconds')
            print(f'📝 Text length: {data["text_length"]} characters')
            print(f'🎤 Language: {data["language"]}')
            print(f'🔊 Voice speed: {data["voice_speed"]}')
            print('🎵 You can play test_audio.wav to hear the TTS output!')
        else:
            print('❌ TTS failed:', data.get('error'))
            
    except Exception as e:
        print(f'💥 Error: {e}')

if __name__ == "__main__":
    test_audio_decode()
