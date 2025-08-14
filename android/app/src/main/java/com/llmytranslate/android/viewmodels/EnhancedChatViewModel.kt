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
import com.llmytranslate.android.utils.TermuxStreamingConfig
import com.llmytranslate.android.utils.TermuxDebugger
import com.llmytranslate.android.utils.ConnectionLogger
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.delay
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
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
        observeSTTErrors()
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
            
            // Test Termux connection with detailed debugging
            val (connected, message) = termuxOllamaClient.testConnection()
            
            if (!connected) {
                // Run detailed diagnostics if connection fails
                Log.w("EnhancedChatViewModel", "Termux connection failed, running diagnostics...")
                val debugInfo = TermuxDebugger.debugTermuxConnection(context)
                Log.i("EnhancedChatViewModel", "Debug info:\n$debugInfo")
                
                // Show debug info in chat for troubleshooting
                addSystemMessage("🔍 Termux Connection Debug:\n$debugInfo")
            } else {
                // Focus on realistic mobile CPU optimization instead of GPU
                checkAndReportMobileOptimization()
                
                addSystemMessage("🚀 Native mode enabled - Termux Ollama connected")
            }
            
            _uiState.value = _uiState.value.copy(
                termuxConnected = connected,
                isNativeMode = connected // Auto-enable native mode if Termux is available
            )
            
            if (connected) {
                addSystemMessage("🚀 Native mode enabled - Termux Ollama connected")
                TermuxStreamingConfig.updateTermuxConnection(true)
            } else {
                addSystemMessage("🌐 Web mode - $message")
                TermuxStreamingConfig.updateTermuxConnection(false)
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
        _uiState.value = _uiState.value.copy(processingStage = "🤔 Ollama is thinking...")
        
        // Add progress updates during processing
        val progressJob = viewModelScope.launch {
            var dots = 0
            while (true) {
                delay(1000)
                dots = (dots + 1) % 4
                val thinking = "🤔 Ollama is thinking" + ".".repeat(dots)
                _uiState.value = _uiState.value.copy(processingStage = thinking)
            }
        }
        
        try {
            // Keep gemma2:2b as default for quality, qwen2:0.5b as performance fallback
            val defaultModel = "gemma2:2b"     // Primary model - better quality
            val performanceModel = "qwen2:0.5b" // Fallback for speed if needed
            
            val result = withTimeoutOrNull(45000L) { // 45 second timeout
                termuxOllamaClient.chatCompletion(
                    prompt = text,
                    model = defaultModel, // Use gemma2:2b as primary
                    timeoutMs = 40000L // 40 second internal timeout
                )
            }
            
            // If fast model fails, mention model optimization
            progressJob.cancel()
            
            return if (result?.success == true) {
                addSystemMessage("✅ Native processing successful (${result.latencyMs}ms via ${result.method})")
                result.response
            } else {
                val errorMsg = result?.error ?: "Timeout after 45 seconds - Ollama may be too slow on CPU"
                
                val healthSummary = termuxOllamaClient.getConnectionHealthSummary()
                
                addSystemMessage("⚠️ Native processing failed: $errorMsg")
                addSystemMessage(healthSummary)
                addSystemMessage("💡 To speed up mobile Ollama:")
                addSystemMessage("   • ollama pull qwen2:0.5b (fastest, 350MB)")
                addSystemMessage("   • ollama pull phi3:mini (fast, 1.3GB)")
                addSystemMessage("   • Current model may be too large for smooth mobile use")
                addSystemMessage("🌐 Switching to web fallback...")
                
                processWithWebService(text)
            }
        } finally {
            progressJob.cancel()
        }
    }
    
    /**
     * Process message using web service fallback.
     */
    private suspend fun processWithWebService(text: String): String = withContext(Dispatchers.IO) {
        _uiState.value = _uiState.value.copy(processingStage = "Web service processing...")
        
        return@withContext try {
            // Try to discover servers first
            val networkManager = com.llmytranslate.android.utils.NetworkManager(context)
            val servers = networkManager.discoverServers()
            
            if (servers.isEmpty()) {
                "❌ No LLMyTranslate servers found on network\n\nPlease ensure:\n• Server is running on port 8000\n• Device is connected to same WiFi network\n• Server allows connections from other devices"
            } else {
                val server = servers.first()
                
                // Make HTTP request to chat API
                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                
                val mediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
                val json = """
                    {
                        "message": "$text",
                        "conversation_id": "android_${System.currentTimeMillis()}",
                        "model": "gemma2:2b"
                    }
                """.trimIndent()
                
                val request = okhttp3.Request.Builder()
                    .url("${server.baseUrl}/api/chat")
                    .post(json.toRequestBody(mediaType))
                    .addHeader("Content-Type", "application/json")
                    .build()
                
                val response = client.newCall(request).execute()
                
                if (response.isSuccessful) {
                    val responseBody = response.body?.string() ?: ""
                    
                    // Parse JSON response to extract the actual message
                    try {
                        val jsonResponse = org.json.JSONObject(responseBody)
                        val message = jsonResponse.optString("response", responseBody)
                        if (message.isNotBlank()) message else "✅ Connected to ${server.host}:${server.port}"
                    } catch (e: Exception) {
                        responseBody.ifBlank { "✅ Server responded successfully" }
                    }
                } else {
                    "❌ Server error (${response.code}): ${response.message}\n\nServer: ${server.host}:${server.port}"
                }
            }
            
        } catch (e: Exception) {
            Log.e("ChatViewModel", "Web service error", e)
            "❌ Web service error: ${e.message}\n\nTroubleshooting:\n• Check server is running: http://localhost:8000\n• Verify network connectivity\n• Try native mode if available"
        }
    }
    
    /**
     * Start voice input using native STT.
     */
    fun startVoiceInput() {
        viewModelScope.launch {
            try {
                sttService.startListening(continuous = false)
                _uiState.value = _uiState.value.copy(
                    isProcessing = true,
                    processingStage = "Listening for speech..."
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isProcessing = false,
                    processingStage = ""
                )
                addSystemMessage("❌ Failed to start voice input: ${e.message}")
            }
        }
    }
    
    /**
     * Stop voice input.
     */
    fun stopVoiceInput() {
        viewModelScope.launch {
            try {
                sttService.stopListening()
                _uiState.value = _uiState.value.copy(
                    isProcessing = false,
                    processingStage = ""
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isProcessing = false,
                    processingStage = ""
                )
            }
        }
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
                // Clear listening state when STT completes
                _uiState.value = _uiState.value.copy(
                    isProcessing = false,
                    processingStage = ""
                )
                
                result?.let {
                    // Only process meaningful speech, not fallback/error messages
                    val text = it.text.trim()
                    val isValidSpeech = text.isNotBlank() && 
                        !text.contains("cloud services unavailable", ignoreCase = true) &&
                        !text.contains("Speech detected", ignoreCase = true) &&
                        !text.contains("transcription services unavailable", ignoreCase = true) &&
                        !text.contains("Audio recorded", ignoreCase = true) &&
                        !text.contains("not available", ignoreCase = true) &&
                        !text.contains("not implemented", ignoreCase = true) &&
                        text.length > 5 // Minimum meaningful length
                    
                    if (isValidSpeech) {
                        Log.i("EnhancedChatViewModel", "✅ Processing valid speech: '$text'")
                        sendMessage(text)
                    } else {
                        Log.w("EnhancedChatViewModel", "⚠️ Skipping fallback message: '$text'")
                        // Show helpful message instead of processing fallback text
                        addSystemMessage("🎤 Voice recording completed. Please try speaking more clearly or check microphone settings.")
                    }
                }
            }
        }
    }
    
    /**
     * Observe STT errors to clear processing state.
     */
    private fun observeSTTErrors() {
        viewModelScope.launch {
            sttService.error.collect { error ->
                if (error != null) {
                    // Clear processing state on STT error
                    _uiState.value = _uiState.value.copy(
                        isProcessing = false,
                        processingStage = ""
                    )
                    addSystemMessage("❌ Speech recognition error: $error")
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
    
    /**
     * Reset Termux connection health and try native mode again.
     */
    fun resetTermuxConnection() {
        viewModelScope.launch {
            termuxOllamaClient.resetConnectionHealth()
            addSystemMessage("🔄 Connection health reset - testing Termux Ollama again...")
            
            // Re-test connection
            val (connected, message) = termuxOllamaClient.testConnection()
            _uiState.value = _uiState.value.copy(
                termuxConnected = connected,
                isNativeMode = connected
            )
            
            if (connected) {
                addSystemMessage("✅ Termux Ollama reconnected!")
                TermuxStreamingConfig.updateTermuxConnection(true)
            } else {
                addSystemMessage("❌ Still can't connect: $message")
                TermuxStreamingConfig.updateTermuxConnection(false)
            }
        }
    }
    
    /**
     * Get detailed connection diagnostics.
     */
    fun getConnectionDiagnostics() {
        viewModelScope.launch {
            val healthSummary = termuxOllamaClient.getConnectionHealthSummary()
            val debugInfo = TermuxDebugger.debugTermuxConnection(context)
            
            addSystemMessage("📊 Connection Diagnostics:")
            addSystemMessage(healthSummary)
            addSystemMessage(debugInfo)
            
            // Print logcat instructions
            ConnectionLogger.printLogcatInstructions()
            addSystemMessage("🔍 Logcat filter command printed to logs!")
            addSystemMessage("Use: adb logcat -s LLMyTranslate_Connection*")
        }
    }
    
    /**
     * Check realistic mobile optimization and provide practical recommendations.
     */
    private fun checkAndReportMobileOptimization() {
        viewModelScope.launch {
            try {
                addSystemMessage("📱 Mobile Performance Analysis")
                addSystemMessage("💻 Using CPU optimization (GPU not available in Termux)")
                
                // Get device specs
                val cpuCores = Runtime.getRuntime().availableProcessors()
                val maxMemory = Runtime.getRuntime().maxMemory() / (1024 * 1024) // MB
                
                addSystemMessage("� Device Specs:")
                addSystemMessage("  • CPU cores: $cpuCores")
                addSystemMessage("  • Available memory: ${maxMemory}MB")
                
                addSystemMessage("⚡ Realistic Performance Expectations:")
                addSystemMessage("  • gemma2:2b (1.6GB): 3-8 seconds response")
                addSystemMessage("  • phi3:mini (1.3GB): 2-5 seconds response")
                addSystemMessage("  • qwen2:0.5b (350MB): 1-3 seconds response")
                
                addSystemMessage("🔧 Termux CPU Optimization Commands:")
                addSystemMessage("  export OLLAMA_NUM_PARALLEL=1")
                addSystemMessage("  export OLLAMA_MAX_LOADED_MODELS=1")
                addSystemMessage("  export OLLAMA_NUM_THREAD=$cpuCores")
                addSystemMessage("  export OLLAMA_KEEP_ALIVE=5m")
                addSystemMessage("  export OLLAMA_GPU=0  # Be honest - no GPU")
                
                addSystemMessage("� Mobile Optimization Tips:")
                addSystemMessage("  ✅ Close other apps to free memory")
                addSystemMessage("  ✅ Use quantized models when available")
                addSystemMessage("  ✅ Keep phone plugged in during heavy use")
                addSystemMessage("  ✅ Avoid multitasking during inference")
                
                if (maxMemory < 3000) {
                    addSystemMessage("⚠️ Limited memory detected")
                    addSystemMessage("  • Consider qwen2:0.5b for better performance")
                    addSystemMessage("  • Close background apps before using")
                }
                
            } catch (e: Exception) {
                Log.e("EnhancedChatViewModel", "Mobile optimization check failed: ${e.message}", e)
                addSystemMessage("❌ Mobile optimization check failed: ${e.message}")
                addSystemMessage("💻 Using default CPU-only settings")
            }
        }
    }
    
    /**
     * Manual mobile optimization diagnostics for troubleshooting.
     */
    fun runMobileOptimizationCheck() {
        addSystemMessage("🔍 Running mobile performance diagnostics...")
        checkAndReportMobileOptimization()
    }
}
