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
        this.audioContext = null;
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.pendingChunks = [];
        this.isProcessingQueue = false;
        this.streamingSession = null;
        this.chunkQueue = [];
        this.performanceMetrics = {
            totalSessions: 0,
            averageLatency: 0,
            chunksProcessed: 0,
            errorCount: 0
        };
        
        this.initializeWebSocket();
        this.initializeAudioContext();
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
    
    
    async initializeAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🎵 Audio context initialized for production streaming TTS');
        } catch (error) {
            console.warn('⚠️ Web Audio API not supported, using Speech Synthesis for production');
            this.audioContext = null;
        }
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
            toggleIcon.textContent = '🎶';
            toggle.classList.add('active');
            this.chatBot.showNotification('🎵 Streaming TTS enabled - AI will speak as it thinks!', 'success');
        } else {
            toggleText.textContent = 'Streaming TTS: OFF';
            toggleIcon.textContent = '🎵';
            toggle.classList.remove('active');
            this.stopCurrentPlayback();
            this.chatBot.showNotification('🔇 Streaming TTS disabled', 'info');
        }
        
        console.log(`🎵 Streaming TTS ${this.isStreamingEnabled ? 'enabled' : 'disabled'}`);
    }
    
    async sendStreamingRequest(message, conversationId, model) {
        if (!this.isStreamingEnabled) {
            // Fall back to regular request
            return null;
        }
        
        console.log('🚀 Starting streaming TTS request...');
        
        // Create WebSocket connection for streaming
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/streaming-tts`;
        
        try {
            const webSocket = new WebSocket(wsUrl);
            
            return new Promise((resolve, reject) => {
                let streamingComplete = false;
                let accumulatedResponse = '';
                
                webSocket.onopen = () => {
                    console.log('🔗 Streaming TTS WebSocket connected');
                    
                    // Send streaming request
                    const request = {
                        type: 'streaming_tts_request',
                        message: message,
                        conversation_id: conversationId,
                        model: model,
                        voice_settings: {
                            rate: 1.0,
                            pitch: 1.0,
                            volume: 0.8
                        }
                    };
                    
                    webSocket.send(JSON.stringify(request));
                };
                
                webSocket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📥 Streaming message:', data.type);
                        
                        switch (data.type) {
                            case 'tts_streaming_started':
                                this.handleStreamingStarted(data);
                                break;
                                
                            case 'streaming_audio_chunk':
                                this.handleAudioChunk(data);
                                accumulatedResponse += data.text || '';
                                break;
                                
                            case 'tts_streaming_completed':
                                this.handleStreamingCompleted(data);
                                streamingComplete = true;
                                webSocket.close();
                                resolve({
                                    response: accumulatedResponse,
                                    streaming: true,
                                    session_info: data.session_info
                                });
                                break;
                                
                            case 'tts_streaming_error':
                                console.error('❌ Streaming TTS error:', data.error);
                                reject(new Error(data.error));
                                break;
                        }
                    } catch (error) {
                        console.error('❌ Error parsing streaming message:', error);
                    }
                };
                
                webSocket.onerror = (error) => {
                    console.error('❌ Streaming WebSocket error:', error);
                    reject(new Error('Streaming connection failed'));
                };
                
                webSocket.onclose = () => {
                    console.log('🔌 Streaming WebSocket closed');
                    if (!streamingComplete) {
                        reject(new Error('Streaming connection closed unexpectedly'));
                    }
                };
                
                // Store session reference
                this.streamingSession = {
                    webSocket,
                    startTime: Date.now()
                };
            });
            
        } catch (error) {
            console.error('❌ Failed to create streaming WebSocket:', error);
            throw error;
        }
    }
    
    handleStreamingStarted(data) {
        console.log('🚀 Streaming TTS started:', data.message);
        
        // Show streaming indicator in chat
        this.showStreamingIndicator(data.message);
        
        // Initialize audio queue
        this.audioQueue = [];
        this.chunkQueue = [];
        this.pendingChunks = [];
        this.isPlaying = false;
        
        this.chatBot.showNotification('🎵 AI is thinking and will speak as thoughts form...', 'info');
    }
    
    async handleAudioChunk(data) {
        const { text, chunk_index, total_chunks, is_final } = data;
        
        console.log(`🎵 Audio chunk ${chunk_index + 1}/${total_chunks}: "${text.substring(0, 30)}..."`);
        
        // Add to chunk queue for display
        this.chunkQueue.push({
            text,
            index: chunk_index,
            total: total_chunks,
            isFinal: is_final,
            timestamp: Date.now()
        });
        
        // Update streaming display
        this.updateStreamingDisplay();
        
        // Add to TTS queue for speaking
        this.queueTextForSpeech(text, chunk_index, is_final);
    }
    
    async queueTextForSpeech(text, chunkIndex, isFinal) {
        if (!text.trim()) return;
        
        console.log(`🎤 Queuing for speech: "${text.substring(0, 40)}..."`);
        
        // Use Web Speech Synthesis API for browser compatibility
        if (this.speechSynthesis) {
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Configure voice settings
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 0.8;
            
            // Set voice if available
            const voices = this.speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.lang.startsWith('en') && !voice.name.includes('Google')
            );
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
            
            // Queue management
            utterance.onstart = () => {
                console.log(`🎤 Speaking chunk ${chunkIndex}: "${text.substring(0, 30)}..."`);
                this.isPlaying = true;
            };
            
            utterance.onend = () => {
                console.log(`✅ Finished speaking chunk ${chunkIndex}`);
                this.isPlaying = false;
                this.processNextInQueue();
            };
            
            utterance.onerror = (event) => {
                console.error(`❌ TTS error for chunk ${chunkIndex}:`, event.error);
                this.isPlaying = false;
                this.processNextInQueue();
            };
            
            // Add to pending queue
            this.pendingChunks.push({
                utterance,
                text,
                chunkIndex,
                isFinal
            });
            
            // Start processing if not already doing so
            if (!this.isProcessingQueue) {
                this.processNextInQueue();
            }
        }
    }
    
    processNextInQueue() {
        if (this.pendingChunks.length === 0) {
            this.isProcessingQueue = false;
            return;
        }
        
        if (this.isPlaying) {
            return; // Wait for current to finish
        }
        
        this.isProcessingQueue = true;
        const next = this.pendingChunks.shift();
        
        try {
            this.currentUtterance = next.utterance;
            this.speechSynthesis.speak(next.utterance);
        } catch (error) {
            console.error('❌ Error speaking text:', error);
            this.isPlaying = false;
            this.processNextInQueue();
        }
    }
    
    handleStreamingCompleted(data) {
        console.log('✅ Streaming TTS completed:', data.summary);
        
        const { total_chunks, total_duration_ms } = data.summary || {};
        
        // Update final display
        this.showStreamingComplete(total_chunks, total_duration_ms);
        
        // Show performance summary
        if (total_chunks && total_duration_ms) {
            const avgChunkTime = total_duration_ms / total_chunks;
            this.chatBot.showNotification(
                `🎵 Streaming TTS completed: ${total_chunks} chunks in ${total_duration_ms}ms (avg: ${avgChunkTime.toFixed(1)}ms/chunk)`, 
                'success'
            );
        }
        
        // Clean up session
        this.streamingSession = null;
    }
    
    showStreamingIndicator(message) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Create streaming indicator
        const indicator = document.createElement('div');
        indicator.id = 'streaming-indicator';
        indicator.className = 'streaming-indicator';
        indicator.innerHTML = `
            <div class="streaming-header">
                <span class="streaming-icon">🎵</span>
                <span class="streaming-title">AI Speaking in Real-time</span>
                <span class="streaming-status">Starting...</span>
            </div>
            <div class="streaming-chunks" id="streaming-chunks">
                <div class="chunk-placeholder">Preparing audio chunks...</div>
            </div>
        `;
        
        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    updateStreamingDisplay() {
        const chunksContainer = document.getElementById('streaming-chunks');
        if (!chunksContainer) return;
        
        // Clear placeholder
        chunksContainer.innerHTML = '';
        
        // Display all received chunks
        this.chunkQueue.forEach((chunk, index) => {
            const chunkElement = document.createElement('div');
            chunkElement.className = `streaming-chunk ${chunk.isFinal ? 'final-chunk' : ''}`;
            chunkElement.innerHTML = `
                <span class="chunk-index">${chunk.index + 1}/${chunk.total}</span>
                <span class="chunk-text">${chunk.text}</span>
                ${chunk.isFinal ? '<span class="final-badge">Final</span>' : ''}
            `;
            chunksContainer.appendChild(chunkElement);
        });
        
        // Update status
        const statusElement = document.querySelector('.streaming-status');
        if (statusElement) {
            statusElement.textContent = `${this.chunkQueue.length} chunks received`;
        }
        
        // Auto-scroll
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    showStreamingComplete(totalChunks, durationMs) {
        const indicator = document.getElementById('streaming-indicator');
        if (!indicator) return;
        
        // Update to completion state
        const header = indicator.querySelector('.streaming-header');
        if (header) {
            header.innerHTML = `
                <span class="streaming-icon">✅</span>
                <span class="streaming-title">Streaming TTS Completed</span>
                <span class="streaming-status">${totalChunks} chunks in ${durationMs}ms</span>
            `;
        }
        
        // Add completion badge
        const chunksContainer = document.getElementById('streaming-chunks');
        if (chunksContainer) {
            const completeBadge = document.createElement('div');
            completeBadge.className = 'streaming-complete-badge';
            completeBadge.textContent = '🎵 All audio chunks processed!';
            chunksContainer.appendChild(completeBadge);
        }
        
        // Auto-remove after delay
        setTimeout(() => {
            if (indicator && indicator.parentNode) {
                indicator.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => {
                    indicator.remove();
                }, 500);
            }
        }, 3000);
    }
    
    stopCurrentPlayback() {
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        
        this.isPlaying = false;
        this.isProcessingQueue = false;
        this.pendingChunks = [];
        this.currentUtterance = null;
        
        // Remove streaming indicator
        const indicator = document.getElementById('streaming-indicator');
        if (indicator) {
            indicator.remove();
        }
        
        console.log('🔇 Streaming TTS playback stopped');
    }
    
    cleanup() {
        this.stopCurrentPlayback();
        
        if (this.streamingSession && this.streamingSession.webSocket) {
            this.streamingSession.webSocket.close();
        }
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        console.log('🧹 Streaming TTS manager cleaned up');
    }
}

// Extend the existing ChatBot class with streaming TTS capability
if (typeof ChatBot !== 'undefined') {
    console.log('🔧 Enhancing ChatBot with Streaming TTS...');
    
    // Store original sendMessage method
    const originalSendMessage = ChatBot.prototype.sendMessage;
    
    // Override sendMessage to support streaming TTS
    ChatBot.prototype.sendMessage = async function() {
        // Initialize streaming TTS manager if not exists
        if (!this.streamingTTS) {
            this.streamingTTS = new StreamingTTSManager(this);
        }
        
        console.log('=== ENHANCED SEND MESSAGE WITH STREAMING TTS ===');
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        // Check if streaming TTS is enabled and no files attached
        if (this.streamingTTS.isStreamingEnabled && this.attachedFiles.length === 0 && message) {
            console.log('🎵 Using streaming TTS for message:', message.substring(0, 50));
            
            try {
                // Add user message
                this.addMessage(message, true);
                messageInput.value = '';
                
                // Show streaming status
                const sendButton = document.getElementById('send-button');
                sendButton.disabled = true;
                const sendText = sendButton.querySelector('.send-text');
                const sendLoading = sendButton.querySelector('.send-loading');
                sendText.style.display = 'none';
                sendLoading.style.display = 'inline';
                sendLoading.textContent = 'Streaming...';
                
                // Make streaming request
                const response = await this.streamingTTS.sendStreamingRequest(
                    message, 
                    this.conversationId, 
                    this.currentModel
                );
                
                if (response && response.streaming) {
                    console.log('✅ Streaming TTS response completed');
                    
                    // Add the complete response as a regular message
                    this.addMessage(response.response, false);
                    
                    // Update session info if provided
                    if (response.session_info) {
                        this.updateSessionInfo(response.session_info);
                    }
                    
                    this.showNotification('✅ Streaming TTS message completed!', 'success');
                } else {
                    throw new Error('Streaming TTS not available, falling back to regular mode');
                }
                
            } catch (error) {
                console.warn('⚠️ Streaming TTS failed, falling back to regular mode:', error);
                this.streamingTTS.isStreamingEnabled = false;
                this.streamingTTS.toggleStreaming(); // Update UI
                
                // Fall back to original method
                return originalSendMessage.call(this);
            } finally {
                // Reset button state
                const sendButton = document.getElementById('send-button');
                sendButton.disabled = false;
                const sendText = sendButton.querySelector('.send-text');
                const sendLoading = sendButton.querySelector('.send-loading');
                sendText.style.display = 'inline';
                sendLoading.style.display = 'none';
                sendLoading.textContent = '...';
                messageInput.focus();
            }
        } else {
            // Use original method for regular messages or file uploads
            console.log('📝 Using regular chat mode');
            return originalSendMessage.call(this);
        }
    };
    
    // Add cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (window.chatBot && window.chatBot.streamingTTS) {
            window.chatBot.streamingTTS.cleanup();
        }
    });
    
    console.log('✅ ChatBot enhanced with Streaming TTS support!');
} else {
    console.warn('⚠️ ChatBot class not found - Streaming TTS integration skipped');
}
