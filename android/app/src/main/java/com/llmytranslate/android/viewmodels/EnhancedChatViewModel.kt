package com.llmytranslate.android.viewmodels

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.llmytranslate.android.models.ConnectionState
import com.llmytranslate.android.models.Message
import com.llmytranslate.android.models.WebSocketMessage
import com.llmytranslate.android.services.TermuxOllamaClient
import com.llmytranslate.android.services.STTService
import com.llmytranslate.android.services.TTSService
import com.llmytranslate.android.services.WebSocketService
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*

/**
 * Enhanced chat ViewModel that coordinates native services for optimal performance.
 * Provides intelligent routing between native and web-based processing.
 */
class EnhancedChatViewModel(
    private val context: Context
) : ViewModel() {
    
    // Initialize services
    private val termuxOllamaClient = TermuxOllamaClient()
    private val sttService = STTService(context)
    private val ttsService = TTSService(context)
    private val webSocketService = WebSocketService()
    
    data class ChatUiState(
        val messages: List<Message> = emptyList(),
        val isProcessing: Boolean = false,
        val processingStage: String = "",
        val isNativeMode: Boolean = true,
        val termuxConnected: Boolean = false,
        val lastLatencyMs: Long = 0,
        val averageLatencyMs: Long = 0,
        val showPerformanceInfo: Boolean = true
    )
    
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()
    
    // Connection state from WebSocket service
    val connectionState: StateFlow<ConnectionState> = webSocketService.connectionState
    
    // STT service states
    val isListening: StateFlow<Boolean> = sttService.isListeningState
    val partialSTTResults: StateFlow<String> = sttService.partialResults
    
    // TTS service states  
    val isSpeaking: StateFlow<Boolean> = ttsService.isSpeakingState
    
    private val latencyHistory = mutableListOf<Long>()
    
    init {
        observeSTTResults()
        observeTTSEvents()
        observeWebSocketMessages()
    }
    
    /**
     * Initialize all native services.
     */
    fun initialize() {
        viewModelScope.launch {
            // Initialize native services
            sttService.initialize()
            // TTSService initializes automatically in constructor
            
            // Test Termux connection
            val (connected, message) = termuxOllamaClient.testConnection()
            _uiState.value = _uiState.value.copy(
                termuxConnected = connected,
                isNativeMode = connected // Auto-enable native mode if Termux is available
            )
            
            if (connected) {
                addSystemMessage("🚀 Native mode enabled - Termux Ollama connected")
            } else {
                addSystemMessage("🌐 Web mode - $message")
            }
        }
    }
    
    /**
     * Send text message using optimal processing method.
     */
    fun sendMessage(text: String) {
        viewModelScope.launch {
            val startTime = System.currentTimeMillis()
            
            // Add user message
            val userMessage = Message(
                id = UUID.randomUUID().toString(),
                text = text,
                isUser = true,
                timestamp = System.currentTimeMillis()
            )
            addMessage(userMessage)
            
            _uiState.value = _uiState.value.copy(
                isProcessing = true,
                processingStage = "Thinking..."
            )
            
            try {
                val response = if (_uiState.value.isNativeMode && _uiState.value.termuxConnected) {
                    // Use native Termux Ollama for fastest response
                    processWithNative(text)
                } else {
                    // Fallback to web service
                    processWithWebService(text)
                }
                
                val latency = System.currentTimeMillis() - startTime
                updateLatencyStats(latency)
                
                if (response.isNotBlank()) {
                    val aiMessage = Message(
                        id = UUID.randomUUID().toString(),
                        text = response,
                        isUser = false,
                        timestamp = System.currentTimeMillis()
                    )
                    addMessage(aiMessage)
                    
                    // Auto-speak response if TTS is available
                    if (ttsService.isInitializedState.value) {
                        ttsService.speak(response)
                    }
                }
                
            } catch (e: Exception) {
                addSystemMessage("❌ Error: ${e.message}")
            } finally {
                _uiState.value = _uiState.value.copy(
                    isProcessing = false,
                    processingStage = ""
                )
            }
        }
    }
    
    /**
     * Process message using native Termux Ollama (fastest path).
     */
    private suspend fun processWithNative(text: String): String {
        _uiState.value = _uiState.value.copy(processingStage = "Native AI processing...")
        
        val result = termuxOllamaClient.chatCompletion(
            prompt = text,
            model = "gemma2:2b",
            timeoutMs = 30000L
        )
        
        return if (result.success) {
            result.response
        } else {
            // Fallback to web service if native fails
            addSystemMessage("⚠️ Native processing failed, using web fallback")
            processWithWebService(text)
        }
    }
    
    /**
     * Process message using web service fallback.
     */
    private suspend fun processWithWebService(text: String): String {
        _uiState.value = _uiState.value.copy(processingStage = "Web service processing...")
        
        // TODO: Implement WebSocket-based processing
        // For now, return placeholder
        return "Web service response to: $text"
    }
    
    /**
     * Start voice input using native STT.
     */
    fun startVoiceInput() {
        sttService.startListening(continuous = false)
        _uiState.value = _uiState.value.copy(processingStage = "Listening...")
    }
    
    /**
     * Stop voice input.
     */
    fun stopVoiceInput() {
        sttService.stopListening()
        _uiState.value = _uiState.value.copy(processingStage = "")
    }
    
    /**
     * Stop TTS playback.
     */
    fun stopSpeaking() {
        ttsService.stop()
    }
    
    /**
     * Play audio for a specific message.
     */
    fun playMessageAudio(message: Message) {
        if (!message.isUser && ttsService.isInitializedState.value) {
            ttsService.speak(message.text)
        }
    }
    
    /**
     * Toggle between native and web processing modes.
     */
    fun toggleNativeMode() {
        val newMode = !_uiState.value.isNativeMode
        _uiState.value = _uiState.value.copy(isNativeMode = newMode)
        
        addSystemMessage(
            if (newMode) "🚀 Switched to native mode" 
            else "🌐 Switched to web mode"
        )
    }
    
    /**
     * Observe STT final results and auto-send messages.
     */
    private fun observeSTTResults() {
        viewModelScope.launch {
            sttService.finalResults.collect { result ->
                result?.let {
                    if (it.text.isNotBlank()) {
                        sendMessage(it.text)
                    }
                }
            }
        }
    }
    
    /**
     * Observe TTS events for UI updates.
     */
    private fun observeTTSEvents() {
        viewModelScope.launch {
            ttsService.isSpeakingState.collect { isSpeaking ->
                // Update UI when TTS starts/stops speaking
                _uiState.value = _uiState.value.copy(
                    isProcessing = isSpeaking
                )
            }
        }
    }
    
    /**
     * Observe WebSocket messages for streaming TTS and other events.
     */
    private fun observeWebSocketMessages() {
        viewModelScope.launch {
            webSocketService.incomingMessages.collect { message ->
                message?.let { handleWebSocketMessage(it) }
            }
        }
    }
    
    /**
     * Handle incoming WebSocket messages, especially streaming TTS chunks.
     */
    private fun handleWebSocketMessage(message: WebSocketMessage) {
        when (message.type) {
            "tts_streaming_started" -> {
                addSystemMessage("🚀 AI started speaking (streaming)")
                message.sessionId?.let { sessionId ->
                    ttsService.startStreaming(sessionId)
                }
            }
            
            "streaming_audio_chunk" -> {
                // Handle streaming audio chunk for immediate playback
                message.text?.let { text ->
                    val chunkIndex = message.chunkIndex ?: 0
                    val isFirstChunk = chunkIndex == 0
                    
                    Log.d("StreamingTTS", "🎵 Received chunk $chunkIndex: '${text.take(30)}...'")
                    ttsService.addStreamingChunk(text, chunkIndex, isFirstChunk)
                }
            }
            
            "tts_streaming_completed" -> {
                addSystemMessage("✅ AI finished speaking")
                ttsService.completeStreaming()
            }
            
            "tts_streaming_error" -> {
                addSystemMessage("❌ Speech error: ${message.message}")
                ttsService.stopStreaming()
            }
            
            "ai_response" -> {
                // Handle traditional (non-streaming) AI response
                message.text?.let { text ->
                    val aiMessage = Message(
                        id = UUID.randomUUID().toString(),
                        text = text,
                        isUser = false,
                        timestamp = System.currentTimeMillis()
                    )
                    addMessage(aiMessage)
                    
                    // Speak with traditional TTS if not using streaming
                    if (ttsService.isInitializedState.value && !ttsService.isStreamingState.value) {
                        ttsService.speak(text)
                    }
                }
            }
            
            "session_started" -> {
                addSystemMessage("🔗 Connected to LLMyTranslate server")
            }
            
            "error" -> {
                addSystemMessage("❌ Server error: ${message.message}")
            }
        }
    }
    
    /**
     * Add message to the conversation.
     */
    private fun addMessage(message: Message) {
        _uiState.value = _uiState.value.copy(
            messages = _uiState.value.messages + message
        )
    }
    
    /**
     * Add system message for status updates.
     */
    private fun addSystemMessage(text: String) {
        val systemMessage = Message(
            id = UUID.randomUUID().toString(),
            text = text,
            isUser = false,
            timestamp = System.currentTimeMillis(),
            isSystem = true
        )
        addMessage(systemMessage)
    }
    
    /**
     * Update latency statistics for performance monitoring.
     */
    private fun updateLatencyStats(latencyMs: Long) {
        latencyHistory.add(latencyMs)
        
        // Keep only last 10 measurements
        if (latencyHistory.size > 10) {
            latencyHistory.removeAt(0)
        }
        
        val averageLatency = latencyHistory.average().toLong()
        
        _uiState.value = _uiState.value.copy(
            lastLatencyMs = latencyMs,
            averageLatencyMs = averageLatency
        )
    }
}
