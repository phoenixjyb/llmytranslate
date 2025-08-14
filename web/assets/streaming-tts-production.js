/**
 * Production Streaming TTS Integration for Chat System
 * 
 * Enhanced version that integrates directly with the main chat interface,
 * providing seamless streaming TTS functionality with WebSocket connectivity.
 * 
 * Version: 2.0.0 - Production Integration
 */

class StreamingTTSManager {
    constructor(chatBot) {
        this.chatBot = chatBot;
        this.websocket = null;
        this.isConnected = false;
        this.isStreaming = false;
        this.currentSessionId = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.streamingEnabled = localStorage.getItem('streamingTTSEnabled') === 'true';
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.pendingChunks = [];
        this.isProcessingQueue = false;
        this.performanceMetrics = {
            totalSessions: 0,
            averageLatency: 0,
            chunksProcessed: 0,
            errorCount: 0
        };
        
        this.initializeWebSocket();
        this.setupStreamingToggle();
        this.enhanceChatInterface();
    }
    
    initializeWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/streaming-tts`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                console.log('🎵 Production Streaming TTS WebSocket connected');
                this.updateConnectionStatus('Connected');
                this.showNotification('🎵 Streaming TTS ready for real-time responses!', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleProductionMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                this.isStreaming = false;
                console.log('🎵 Streaming TTS WebSocket disconnected');
                this.updateConnectionStatus('Disconnected');
                
                // Attempt reconnection with exponential backoff
                setTimeout(() => this.initializeWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('🎵 Streaming TTS WebSocket error:', error);
                this.updateConnectionStatus('Error');
                this.performanceMetrics.errorCount++;
            };
            
        } catch (error) {
            console.error('🎵 Failed to initialize streaming TTS WebSocket:', error);
            this.updateConnectionStatus('Failed');
        }
    }
    
    handleProductionMessage(message) {
        console.log('🎵 Production streaming message:', message.type);
        
        switch (message.type) {
            case 'tts_streaming_started':
                this.handleStreamingStarted(message);
                break;
            case 'streaming_audio_chunk':
                this.handleStreamingChunk(message);
                break;
            case 'tts_streaming_completed':
                this.handleStreamingCompleted(message);
                break;
            case 'tts_streaming_error':
                this.handleStreamingError(message);
                break;
            case 'llm_response_chunk':
                // Handle LLM response chunks for streaming text + TTS
                this.handleLLMResponseChunk(message);
                break;
            default:
                console.log('🎵 Unknown streaming message type:', message.type);
        }
    }
    
    handleStreamingStarted(message) {
        this.isStreaming = true;
        this.currentSessionId = message.session_id;
        this.audioQueue = [];
        this.performanceMetrics.totalSessions++;
        
        console.log('🎵 Production streaming started for session:', message.session_id);
        this.showStreamingIndicator(true);
        this.updateConnectionStatus('Streaming');
        
        // Create or update the streaming message container
        this.createStreamingMessageContainer();
    }
    
    handleStreamingChunk(message) {
        const startTime = performance.now();
        
        const chunk = {
            index: message.chunk_index,
            text: message.text,
            isLast: message.is_final,
            timestamp: Date.now()
        };
        
        this.audioQueue.push(chunk);
        this.performanceMetrics.chunksProcessed++;
        
        console.log(`🎵 Chunk ${chunk.index + 1}: "${chunk.text}"`);
        
        // Play audio immediately with browser speech synthesis
        this.playStreamingAudio(chunk.text);
        
        // Update UI with streaming text
        this.updateStreamingTextInChat(chunk);
        
        // Track performance
        const latency = performance.now() - startTime;
        this.updatePerformanceMetrics(latency);
    }
    
    handleLLMResponseChunk(message) {
        // Handle combined LLM response + TTS streaming
        const chunk = {
            text: message.content,
            isLast: message.is_final || false,
            timestamp: Date.now()
        };
        
        // Update text in chat first
        this.updateLLMTextInChat(chunk);
        
        // Queue for TTS if enabled
        if (this.streamingEnabled) {
            this.queueTextForTTS(chunk.text);
        }
    }
    
    handleStreamingCompleted(message) {
        this.isStreaming = false;
        console.log('🎵 Production streaming completed:', message.summary);
        
        this.showStreamingIndicator(false);
        this.updateConnectionStatus('Connected');
        this.finalizeStreamingMessage();
        
        // Update performance metrics
        const summary = message.summary || {};
        const duration = summary.total_duration_ms || 0;
        console.log(`🎵 Session completed: ${this.audioQueue.length} chunks in ${duration}ms`);
    }
    
    handleStreamingError(message) {
        this.isStreaming = false;
        console.error('🎵 Production streaming error:', message.error);
        
        this.showStreamingIndicator(false);
        this.updateConnectionStatus('Error');
        this.performanceMetrics.errorCount++;
        
        // Show user-friendly error
        this.showNotification(`Streaming TTS temporarily unavailable: ${message.error}`, 'warning');
    }
    
    playStreamingAudio(text) {
        if (!('speechSynthesis' in window)) {
            console.warn('🎵 Speech synthesis not supported in this browser');
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        
        // Use high-quality voice if available
        const voices = speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Natural') || 
            voice.name.includes('Premium') ||
            (voice.lang.startsWith('en') && voice.localService)
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        utterance.onstart = () => {
            console.log(`🎵 Speaking: "${text}"`);
        };
        
        utterance.onend = () => {
            console.log(`🎵 Completed: "${text}"`);
        };
        
        utterance.onerror = (error) => {
            console.error('🎵 Speech synthesis error:', error);
            this.performanceMetrics.errorCount++;
        };
        
        speechSynthesis.speak(utterance);
    }
    
    createStreamingMessageContainer() {
        // Check if we already have a streaming message
        let streamingMessage = document.querySelector('.message.streaming-active');
        
        if (!streamingMessage) {
            const messagesContainer = document.getElementById('chat-messages');
            streamingMessage = document.createElement('div');
            streamingMessage.className = 'message bot-message streaming-active';
            streamingMessage.innerHTML = `
                <div class="message-content">
                    <strong>Assistant:</strong> 
                    <span class="streaming-text"></span>
                    <span class="streaming-cursor">▋</span>
                </div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
                <div class="streaming-status">🎵 Speaking as I think...</div>
            `;
            messagesContainer.appendChild(streamingMessage);
            this.scrollToBottom();
        }
        
        return streamingMessage;
    }
    
    updateStreamingTextInChat(chunk) {
        const streamingMessage = document.querySelector('.message.streaming-active');
        if (!streamingMessage) return;
        
        const streamingTextElement = streamingMessage.querySelector('.streaming-text');
        const currentText = streamingTextElement.textContent;
        streamingTextElement.textContent = currentText + ' ' + chunk.text;
        
        // Remove streaming elements if this is the last chunk
        if (chunk.isLast) {
            this.finalizeStreamingMessage();
        }
        
        this.scrollToBottom();
    }
    
    updateLLMTextInChat(chunk) {
        // Handle LLM text updates - similar to existing chat response handling
        let activeMessage = document.querySelector('.message.streaming-active');
        
        if (!activeMessage) {
            activeMessage = this.createStreamingMessageContainer();
        }
        
        const textElement = activeMessage.querySelector('.streaming-text');
        if (chunk.isLast) {
            // Replace with final text
            textElement.textContent = chunk.text;
            this.finalizeStreamingMessage();
        } else {
            // Append streaming text
            textElement.textContent += chunk.text;
        }
        
        this.scrollToBottom();
    }
    
    finalizeStreamingMessage() {
        const streamingMessage = document.querySelector('.message.streaming-active');
        if (streamingMessage) {
            // Remove streaming indicators
            const cursor = streamingMessage.querySelector('.streaming-cursor');
            const status = streamingMessage.querySelector('.streaming-status');
            if (cursor) cursor.remove();
            if (status) status.remove();
            
            // Remove streaming class
            streamingMessage.classList.remove('streaming-active');
        }
    }
    
    queueTextForTTS(text) {
        if (!this.streamingEnabled || !this.isConnected) return;
        
        // Queue text for speech synthesis
        this.pendingChunks.push(text);
        
        // Process queue if not already processing
        if (!this.isProcessingQueue) {
            this.processTextQueue();
        }
    }
    
    async processTextQueue() {
        this.isProcessingQueue = true;
        
        while (this.pendingChunks.length > 0) {
            const text = this.pendingChunks.shift();
            this.playStreamingAudio(text);
            
            // Add small delay between chunks
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        this.isProcessingQueue = false;
    }
    
    setupStreamingToggle() {
        // Add streaming TTS toggle to chat controls
        const chatControls = document.querySelector('.chat-controls');
        if (chatControls) {
            const streamingToggle = document.createElement('button');
            streamingToggle.id = 'streaming-tts-toggle';
            streamingToggle.className = 'streaming-toggle';
            streamingToggle.innerHTML = `
                <span class="toggle-icon">🎵</span>
                <span class="toggle-text">Streaming TTS: ${this.streamingEnabled ? 'ON' : 'OFF'}</span>
            `;
            streamingToggle.onclick = () => this.toggleStreaming();
            chatControls.appendChild(streamingToggle);
            console.log('✅ Streaming TTS toggle added to chat controls');
        }
    }
    
    toggleStreaming() {
        this.streamingEnabled = !this.streamingEnabled;
        localStorage.setItem('streamingTTSEnabled', this.streamingEnabled.toString());
        
        const toggle = document.getElementById('streaming-tts-toggle');
        const toggleText = toggle.querySelector('.toggle-text');
        
        toggleText.textContent = `Streaming TTS: ${this.streamingEnabled ? 'ON' : 'OFF'}`;
        toggle.className = `streaming-toggle ${this.streamingEnabled ? 'active' : ''}`;
        
        if (this.streamingEnabled) {
            this.showNotification('🎵 Streaming TTS enabled - responses will play as AI thinks!', 'success');
        } else {
            this.showNotification('🎵 Streaming TTS disabled - using traditional responses', 'info');
            // Stop any current playback
            this.stopCurrentPlayback();
        }
        
        console.log('🎵 Streaming TTS toggled:', this.streamingEnabled);
    }
    
    enhanceChatInterface() {
        // Add connection status indicator
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader) {
            const statusIndicator = document.createElement('div');
            statusIndicator.className = 'streaming-status-indicator';
            statusIndicator.innerHTML = `
                <span class="status-dot"></span>
                <span class="status-text">Streaming TTS</span>
            `;
            chatHeader.appendChild(statusIndicator);
        }
        
        // Load speech synthesis voices
        if ('speechSynthesis' in window) {
            speechSynthesis.getVoices();
            speechSynthesis.onvoiceschanged = () => {
                const voices = speechSynthesis.getVoices();
                console.log(`🎵 Loaded ${voices.length} TTS voices for production`);
            };
        }
    }
    
    // Method to enhance existing sendMessage function in ChatBot
    async enhanceSendMessage(originalSendMessage, message) {
        if (!this.streamingEnabled || !this.isConnected) {
            // Fall back to original sendMessage
            return originalSendMessage();
        }
        
        try {
            // Send streaming request via WebSocket
            const streamingRequest = {
                type: 'start_streaming_chat',
                message: message,
                conversation_id: this.chatBot.conversationId,
                model: this.chatBot.currentModel,
                session_id: 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
            };
            
            console.log('🎵 Sending streaming chat request...');
            this.websocket.send(JSON.stringify(streamingRequest));
            
            // Add user message to chat
            this.chatBot.addMessage(message, true);
            
            // Clear input
            const messageInput = document.getElementById('message-input');
            messageInput.value = '';
            
            // Update guest limits if applicable
            if (this.chatBot.isGuest) {
                this.chatBot.guestLimits.currentConversationMessages++;
            }
            
            return true; // Indicate successful streaming request
            
        } catch (error) {
            console.error('🎵 Failed to send streaming request:', error);
            // Fall back to original sendMessage
            return originalSendMessage();
        }
    }
    
    // Utility methods
    updateConnectionStatus(status) {
        const statusIndicator = document.querySelector('.streaming-status-indicator');
        if (statusIndicator) {
            const statusDot = statusIndicator.querySelector('.status-dot');
            statusDot.className = `status-dot status-${status.toLowerCase()}`;
        }
    }
    
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (this.chatBot && this.chatBot.showNotification) {
            this.chatBot.showNotification(message, type);
        } else {
            console.log(`📢 ${type.toUpperCase()}: ${message}`);
        }
    }
    
    showStreamingIndicator(show) {
        let indicator = document.querySelector('.streaming-indicator');
        
        if (show && !indicator) {
            // Create streaming indicator
            indicator = document.createElement('div');
            indicator.className = 'streaming-indicator active';
            indicator.innerHTML = `
                <div class="wave-animation">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
                <span>AI is speaking...</span>
            `;
            
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.appendChild(indicator);
        } else if (!show && indicator) {
            indicator.remove();
        }
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    stopCurrentPlayback() {
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        this.pendingChunks = [];
        this.isProcessingQueue = false;
    }
    
    updatePerformanceMetrics(latency) {
        this.performanceMetrics.averageLatency = 
            (this.performanceMetrics.averageLatency + latency) / 2;
    }
    
    cleanup() {
        this.stopCurrentPlayback();
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// CSS for production streaming TTS
const productionStreamingTTSStyles = `
    .streaming-message .streaming-cursor {
        animation: blink 1s infinite;
        color: #4299e1;
        font-weight: bold;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .streaming-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
        border: 2px solid #38b2ac;
        border-radius: 8px;
        color: #234e52;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
    }
    
    .wave-animation {
        display: flex;
        gap: 3px;
    }
    
    .wave-bar {
        width: 4px;
        height: 20px;
        background: #38b2ac;
        border-radius: 2px;
        animation: wave 1.5s ease-in-out infinite;
    }
    
    .wave-bar:nth-child(2) { animation-delay: 0.1s; }
    .wave-bar:nth-child(3) { animation-delay: 0.2s; }
    .wave-bar:nth-child(4) { animation-delay: 0.3s; }
    
    @keyframes wave {
        0%, 40%, 100% { transform: scaleY(0.4); }
        20% { transform: scaleY(1); }
    }
    
    @keyframes slideIn {
        from { transform: translateY(-10px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .streaming-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 14px;
        font-weight: 500;
    }
    
    .streaming-toggle:hover {
        background: #edf2f7;
        border-color: #cbd5e0;
    }
    
    .streaming-toggle.active {
        background: #e6fffa;
        border-color: #38b2ac;
        color: #234e52;
    }
    
    .streaming-status-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        margin-left: auto;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #cbd5e0;
    }
    
    .status-dot.status-connected { background: #48bb78; }
    .status-dot.status-connecting { background: #ed8936; }
    .status-dot.status-disconnected { background: #f56565; }
    .status-dot.status-streaming { 
        background: #4299e1; 
        animation: pulse 2s infinite;
    }
    .status-dot.status-error { background: #e53e3e; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .streaming-status {
        font-size: 12px;
        color: #4a5568;
        font-style: italic;
        margin-top: 4px;
    }
    
    .message.streaming-active {
        border-left: 4px solid #38b2ac;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    }
`;

// Inject CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = productionStreamingTTSStyles;
document.head.appendChild(styleSheet);

// Export for production use
window.StreamingTTSManager = StreamingTTSManager;

console.log('🎵 Production Streaming TTS Manager loaded and ready!');
