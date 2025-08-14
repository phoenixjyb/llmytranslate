# Web Client Architecture & Guide

The web client provides chat, translation, and voice features with optional streaming TTS.

## Structure

```
web/
├── index.html
├── chat.html
├── translate.html
├── voice-chat.html
├── streaming-tts-test.html
└── assets/
    ├── chat.js
    ├── chat-streaming-integration.js
    ├── streaming-tts.js
    ├── streaming-tts-production.js
    ├── user-auth.js
    ├── chat.css
    ├── streaming-tts.css
    └── user-styles.css
```

## Key Features

- Chat UI with incremental assistant updates
- Streaming TTS over WebSocket (`/ws/streaming-tts`)
- Local browser SpeechSynthesis for low-latency audio
- Feature toggle stored in localStorage (Streaming TTS ON/OFF)
- Connection status indicator and notifications

## How It Works

- On connect, `StreamingTTSManager` opens a WebSocket
- Server sends `llm_response_chunk` events
- Client updates UI via `updateLLMTextInChat` and queues text to speech
- Final chunk triggers `finalizeStreamingMessage()`

## Run Locally

1. Start backend: `python run.py`
2. Open `web/chat.html` or `web/index.html` in a browser (or serve with a static server)
3. Toggle Streaming TTS in the UI

## Browser Notes

- SpeechSynthesis voice availability varies by OS/browser
- HTTPS will upgrade WS to WSS automatically

## Troubleshooting

- If the status shows Disconnected, backend `/ws/streaming-tts` may not be running
- If no audio: check `speechSynthesis` support and OS voices
- Use `live-debug.html` to inspect streaming events
