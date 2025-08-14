# Software Design Document (SDD)

## Purpose
Detailed design of LLMyTranslate server and clients with emphasis on separation of concerns and extensibility.

## Backend (FastAPI)

- Entry: `run.py` (Uvicorn server)
- API Modules: `src/api/routes/*`
  - translation.py: Baidu-compatible endpoint
  - optimized.py: optimized endpoints and stats
  - discovery.py: service discovery utilities
  - health.py: health/readiness checks
  - (optional) chatbot.py: chat endpoints if enabled
- Services: `src/services/*`
  - translation_service.py: Orchestrates translation flow, caching, metrics
  - ollama_client.py: HTTPX async client to Ollama with pooling and retries
  - cache_service.py: LRU + Redis-backed cache
  - auth_service.py: signature validation and API keys
  - stats_service.py: runtime metrics
- Core Config: `src/core/config.py`, `.env*`
- Models: `src/models/schemas.py` (+ chat_schemas.py if enabled)

### Design Patterns
- Facade per route module, delegating to service objects
- Adapter for Ollama HTTP API
- Strategy for model selection (fast/accurate)
- Repository-like cache layer with in-memory/Redis backing
- DTOs with Pydantic models

### Error Handling
- Service-level exceptions mapped to API error responses
- Graceful fallbacks for Redis unavailability
- Timeouts and retries for Ollama calls

## Web Client

- Static HTML pages in `web/`
- Assets in `web/assets/`
  - chat.js, chat-streaming-integration.js
  - streaming-tts.js, streaming-tts-production.js
  - user-auth.js, stylesheets
- Streaming over WebSocket `/ws/streaming-tts`
  - Incremental UI updates for assistant text
  - Browser SpeechSynthesis for immediate playback
- Feature toggles persisted in localStorage

## Android Client

- Kotlin/Compose app under `android/app`
- Services:
  - WebSocketService: backend connectivity
  - STTService, TTSService: on-device speech
  - NetworkManager: discovery and connectivity
- UI:
  - Chat screen, voice call screen, settings
  - Material 3 components

## Data Contracts

- REST translation: Baidu-compatible form params
- Streaming WebSocket messages:
  - tts_streaming_started { session_id }
  - llm_response_chunk { content, is_final }
  - streaming_audio_chunk { chunk_index, text, is_final }
  - tts_streaming_completed { summary }
  - tts_streaming_error { error }

## Configuration

- `.env.local` / `.env.remote` toggle deployment mode
- OLLAMA_* parameters for model host and timeouts
- AUTH_* parameters for signature enforcement
- CACHE_* parameters for Redis and in-memory cache

## Testing Strategy

- Unit tests in `tests/unit`
- Integration tests in `tests/integration`
- Websocket tests: `test_streaming_server.py`, `test_streaming_tts_integration.py`
- Android: Gradle unit tests + manual device tests (S24 Ultra)

## Extensibility

- Add new models via config
- Plug additional endpoints under `src/api/routes`
- Swap cache backend with minimal changes
- Extend WebSocket protocol for new events
