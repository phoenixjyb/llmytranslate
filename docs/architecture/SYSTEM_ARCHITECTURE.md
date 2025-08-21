# System Architecture Overview

This document describes the end-to-end architecture of LLMyTranslate across backend services and client applications (Web and Android).

## Components

- FastAPI Backend (Python)
  - REST endpoints: translation, optimized, TTS, health, discovery
  - WebSocket endpoints: streaming chat / streaming TTS (`/ws/streaming-tts`)
  - Services: translation_service, ollama_client, cache_service, auth_service, stats_service
  - Optional Redis cache with in-memory fallback
- Local LLM Runtime (Ollama)
  - Model hosting and inference (Gemma3, Llama3.1, Qwen, etc.)
  - GPU acceleration if available
- On‑device Inference (TensorFlow Lite)
  - Lightweight TFLite runtime with wrappers for TinyLlama (LLM) and SpeechT5 (TTS)
  - Primary target: Android on‑device; also used for local smoke tests
  - Backends: tensorflow.lite or tflite_runtime; NNAPI/XNNPACK delegates on mobile
- Clients
  - Web UI (static HTML/JS under `web/`)
    - Chat UI with streaming TTS (`web/assets/streaming-tts*.js`)
    - Multiple entry pages (chat.html, translate.html, voice-chat.html, etc.)
  - Android App (`android/`)
    - Native STT/TTS
    - WebSocket connection to backend for chat/translation
    - Optional on‑device model execution via TFLite (models stored as app assets)
- Remote Access (optional)
  - Tailscale / Ngrok for external connectivity
- Automation & Scripts
  - Cross-platform start/stop/setup scripts
  - Tests and diagnostics under `tests/` and root scripts

## High-Level Diagram (Mermaid)

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}} }%%
flowchart TD
  subgraph Clients
    Web[Web UI]
    Android[Android App]
  end
  subgraph Backend[FastAPI Backend]
    API[Auth & Routing]
    Svc[Services\ntranslation_service\ncache_service\nauth_service\nstats_service]
  end
  Cache[(Cache)]
  Ollama[Ollama LLM Runtime]

  Web -->|REST or WebSocket| API
  Android -->|REST or WebSocket| API
  API --> Svc
  Svc -->|Async HTTPX keep-alive| Ollama
  Svc <-->|LRU or Redis| Cache

  %% Optional on-device path (Android / local smoke tests)
  Android -. optional TFLite .-> Svc

  classDef store fill:#eef,stroke:#446;
  class Cache store;
```

## Key Flows

- Translation (REST): client -> /api/trans/vip/translate -> translation_service -> ollama_client -> response
- Optimized Translation: client -> /api/optimized/* -> cache + timing metrics + model selection
- TTS (REST): client -> /api/tts/* -> synthesis -> audio payload (base64)
- Streaming TTS/Chat (WebSocket): client <-> /ws/streaming-tts -> incremental text + TTS playback

### Streaming WebSocket Sequence

```mermaid
sequenceDiagram
    autonumber
    participant C as Client (Web/Android)
    participant WS as WebSocket /ws/streaming-tts
    participant API as FastAPI Router
    participant SVC as Streaming Service
    participant LLM as Ollama Runtime

    C->>WS: Connect
    WS->>API: Upgrade handshake
    API-->>C: 101 Switching Protocols

    C->>WS: start_streaming_chat(message, conversationId, model)
    WS->>API: Route to streaming handler
    API->>SVC: start_session()
    SVC-->>C: tts_streaming_started(sessionId)

    loop Incremental generation
        SVC->>LLM: generate_next_chunk()
        LLM-->>SVC: chunk(text, isFinal?)
        SVC-->>C: llm_response_chunk(content, isFinal=false)
        par Immediate speech (client)
            C-->>C: SpeechSynthesis.speak(content)
        and Optional audio (server)
            SVC-->>C: streaming_audio_chunk(index, text)
        end
    end

    SVC-->>C: tts_streaming_completed(summary)
    C-->>WS: Close
```

### WebSocket Message Types (summary)

- `tts_streaming_started`: `{ session_id }`
- `llm_response_chunk`: `{ content, is_final }`
- `streaming_audio_chunk`: `{ chunk_index, text, is_final }`
- `tts_streaming_completed`: `{ summary }`
- `tts_streaming_error`: `{ error }`

## Deployment

- Local development: `python run.py` with `.env.local`
- Remote mode: Nginx/ngrok/Tailscale with `.env.remote`
- Docker support available in `docker/`
- Android on‑device (optional): TFLite models under app assets (ignored in git),
  invoked via lightweight wrappers; server/web pipeline continues to use Ollama by default.

## Reliability & Performance

- Connection pooling with 100% reuse rate to Ollama
- Smart LRU caching with compression and persistence
- Async I/O in FastAPI + HTTPX
- Health and readiness probes
- Graceful fallbacks when Redis unavailable

## Security

- Baidu-compatible signature validation (configurable)
- Rate limiting (configurable)
- CORS configured for web clients

## Observability

- Structured logging
- Metrics endpoints under optimized API
- Test and diagnostic scripts
