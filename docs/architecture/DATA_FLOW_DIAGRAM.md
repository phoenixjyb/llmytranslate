# Data Flow and Processing

This document explains core runtime flows for both REST and WebSocket paths.

## Translation (REST)

1. Client submits form-encoded request to `/api/trans/vip/translate`
2. Auth service validates signature (optional in dev)
3. Translation service checks LRU/Redis cache
4. On miss, constructs prompt and calls Ollama via HTTPX
5. Receives response, formats Baidu-compatible JSON
6. Stores in cache (compressed) and returns result

## Optimized Translation

- Adds timing breakdown and performance metrics
- Tracks connection reuse and tokens/sec from Ollama
- May utilize different models based on strategy

## TTS (REST)

1. Client POSTs to `/api/tts/synthesize` or `/api/tts/translate-and-speak`
2. Server synthesizes audio (local models) or orchestrates translation then TTS
3. Returns base64-encoded audio with metadata

## Streaming TTS/Chat (WebSocket)

1. Web client connects to `/ws/streaming-tts`
2. Sends `start_streaming_chat` with message, conversation_id, model
3. Server pushes events:
   - `tts_streaming_started`
   - `llm_response_chunk` (incremental text)
   - `streaming_audio_chunk` (optional text cues)
   - `tts_streaming_completed` with summary
4. Web client updates UI as chunks arrive and speaks via SpeechSynthesis

## Android Flow

- Native STT/TTS path on-device for minimal latency
- WebSocket to server for LLM responses
- Fallback to REST if WebSocket unavailable

## Error Paths

- Redis unavailable: fallback to in-memory cache
- Ollama timeout: retry with backoff; surface friendly error
- WebSocket error: client shows notification and falls back to non-streaming send
