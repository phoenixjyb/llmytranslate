package com.llmytranslate.android.services

import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import com.llmytranslate.android.models.*
import com.llmytranslate.android.utils.PerformanceTracker
import com.llmytranslate.android.utils.NetworkOperation
import com.squareup.moshi.Moshi
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI
import java.util.*
import kotlin.system.measureTimeMillis

/**
 * WebSocketService manages real-time communication with LLMyTranslate server.
 * Handles connection lifecycle, message routing, and automatic reconnection.
 */
class WebSocketService : Service() {
    
    companion object {
        private const val TAG = "WebSocketService"
        private const val RECONNECT_DELAY_MS = 3000L
        private const val MAX_RECONNECT_ATTEMPTS = 5
    }
    
    private val moshi = Moshi.Builder().build()
    
    private val binder = WebSocketBinder()
    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    private var webSocketClient: WebSocketClient? = null
    private var currentServerUrl: String? = null
    private var currentSessionId: String? = null
    private var reconnectAttempts = 0
    private var isReconnecting = false
    
    private val messageAdapter = moshi.adapter(WebSocketMessage::class.java)
    
    // State flows for UI updates
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _incomingMessages = MutableStateFlow<WebSocketMessage?>(null)
    val incomingMessages: StateFlow<WebSocketMessage?> = _incomingMessages.asStateFlow()
    
    private val _serverInfo = MutableStateFlow<ServerInfo?>(null)
    val serverInfo: StateFlow<ServerInfo?> = _serverInfo.asStateFlow()
    
    override fun onBind(intent: Intent): IBinder = binder
    
    override fun onCreate() {
        super.onCreate()
        val createTime = PerformanceTracker.measureStage("websocket_service_create") {
            Log.i(TAG, "🔧 WebSocketService created")
        }
        PerformanceTracker.logMemoryUsage("WebSocketService created")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        val destroyTime = PerformanceTracker.measureStage("websocket_service_destroy") {
            disconnect()
            serviceScope.cancel()
            Log.i(TAG, "🔌 WebSocketService destroyed")
        }
    }
    
    /**
     * Connect to LLMyTranslate server WebSocket.
     */
    fun connect(serverUrl: String, sessionSettings: SessionSettings? = null) {
        if (_connectionState.value == ConnectionState.CONNECTED && currentServerUrl == serverUrl) {
            Log.i(TAG, "Already connected to $serverUrl")
            return
        }
        
        val connectionStartTime = System.currentTimeMillis()
        currentServerUrl = serverUrl
        _connectionState.value = ConnectionState.CONNECTING
        
        Log.i(TAG, "🔗 Starting WebSocket connection to: $serverUrl")
        
        serviceScope.launch {
            try {
                val uri = URI(serverUrl)
                Log.i(TAG, "Connecting to WebSocket: $uri")
                
                webSocketClient = object : WebSocketClient(uri) {
                    override fun onOpen(handshake: ServerHandshake?) {
                        val connectionDuration = System.currentTimeMillis() - connectionStartTime
                        Log.i(TAG, "✅ WebSocket connected in ${connectionDuration}ms")
                        
                        PerformanceTracker.logNetworkOperation(
                            NetworkOperation.WEBSOCKET_CONNECT, 
                            connectionDuration
                        )
                        
                        _connectionState.value = ConnectionState.CONNECTED
                        reconnectAttempts = 0
                        isReconnecting = false
                        
                        // Start session immediately
                        startSession(sessionSettings)
                    }
                    
                    override fun onMessage(message: String?) {
                        val messageStartTime = System.currentTimeMillis()
                        message?.let { 
                            val processTime = PerformanceTracker.measureStage("websocket_message_process") {
                                handleIncomingMessage(it)
                            }
                            
                            PerformanceTracker.logNetworkOperation(
                                NetworkOperation.MESSAGE_RECEIVE, 
                                System.currentTimeMillis() - messageStartTime
                            )
                        }
                    }
                    
                    override fun onClose(code: Int, reason: String?, remote: Boolean) {
                        Log.i(TAG, "🔌 WebSocket closed: code=$code, reason=$reason, remote=$remote")
                        _connectionState.value = ConnectionState.DISCONNECTED
                    
                        // Attempt reconnection if not manually disconnected
                        if (remote && !isReconnecting && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                            attemptReconnect()
                        }
                    }
                    
                    override fun onError(ex: Exception?) {
                        Log.e(TAG, "WebSocket error", ex)
                        _connectionState.value = ConnectionState.ERROR
                    }
                }
                
                webSocketClient?.connect()
                
            } catch (e: Exception) {
                Log.e(TAG, "Error connecting to WebSocket", e)
                _connectionState.value = ConnectionState.ERROR
            }
        }
    }
    
    /**
     * Disconnect from server.
     */
    fun disconnect() {
        val disconnectTime = measureTimeMillis {
            webSocketClient?.close()
            webSocketClient = null
            currentServerUrl = null
            currentSessionId = null
            
            _connectionState.value = ConnectionState.DISCONNECTED
            Log.i(TAG, "🔌 WebSocket disconnected")
        }
        PerformanceTracker.logNetworkOperation(NetworkOperation.WEBSOCKET_DISCONNECT, disconnectTime)
    }
    
    /**
     * Send text message to server (from Android STT).
     */
    fun sendTextMessage(text: String) {
        currentSessionId?.let { sessionId ->
            val sendTime = measureTimeMillis {
                val message = WebSocketMessage(
                    type = "text_input",
                    sessionId = sessionId,
                    text = text
                )
                sendMessage(message)
                Log.d(TAG, "📤 Sent text message: ${text.take(50)}...")
            }
            
            PerformanceTracker.logNetworkOperation(NetworkOperation.MESSAGE_SEND, sendTime)
        }
    }
    
    /**
     * Update session settings.
     */
    fun updateSettings(settings: SessionSettings) {
        currentSessionId?.let { sessionId ->
            val updateTime = measureTimeMillis {
                val message = WebSocketMessage(
                    type = "settings_update",
                    sessionId = sessionId,
                    settings = settings
                )
                sendMessage(message)
                Log.d(TAG, "⚙️ Updated session settings")
            }
            PerformanceTracker.logNetworkOperation(NetworkOperation.SETTINGS_UPDATE, updateTime)
        }
    }
    
    /**
     * Start a new session with the server.
     */
    private fun startSession(settings: SessionSettings?) {
        val sessionId = "android_${UUID.randomUUID().toString().take(8)}"
        currentSessionId = sessionId
        
        val message = WebSocketMessage(
            type = "session_start",
            sessionId = sessionId,
            settings = settings ?: SessionSettings()
        )
        
        sendMessage(message)
        Log.i(TAG, "Started session: $sessionId")
    }
    
    /**
     * End the current session.
     */
    private fun endSession(sessionId: String) {
        val message = WebSocketMessage(
            type = "session_end",
            sessionId = sessionId
        )
        sendMessage(message)
        Log.i(TAG, "Ended session: $sessionId")
    }
    
    /**
     * Send WebSocket message to server.
     */
    private fun sendMessage(message: WebSocketMessage) {
        val sendTime = measureTimeMillis {
            try {
                val jsonMessage = messageAdapter.toJson(message)
                webSocketClient?.send(jsonMessage)
                Log.d(TAG, "📤 Sent message: ${message.type}")
            } catch (e: Exception) {
                Log.e(TAG, "❌ Error sending message", e)
            }
        }
        PerformanceTracker.logNetworkOperation(NetworkOperation.MESSAGE_SEND, sendTime)
    }
    
    /**
     * Handle incoming WebSocket messages.
     */
    private fun handleIncomingMessage(messageJson: String) {
        val handleTime = measureTimeMillis {
            try {
                val message = messageAdapter.fromJson(messageJson)
                message?.let {
                    Log.d(TAG, "Received message: ${it.type}")
                    
                    // Handle special message types
                    when (it.type) {
                        "session_started" -> {
                            it.serverInfo?.let { serverInfo -> _serverInfo.value = serverInfo }
                            Log.i(TAG, "Session started with server info")
                        }
                        "ai_response" -> {
                            Log.i(TAG, "Received AI response: ${it.text?.take(50)}...")
                        }
                        "streaming_audio_chunk" -> {
                            Log.d(TAG, "🎵 Received streaming audio chunk ${it.chunkIndex}/${it.totalChunks}")
                            handleStreamingAudioChunk(it)
                        }
                        "tts_streaming_started" -> {
                            Log.i(TAG, "🚀 Streaming TTS started")
                        }
                        "tts_streaming_completed" -> {
                            Log.i(TAG, "✅ Streaming TTS completed")
                        }
                        "tts_streaming_error" -> {
                            Log.w(TAG, "❌ Streaming TTS error: ${it.message}")
                        }
                        "error" -> {
                            Log.w(TAG, "Server error: ${it.message}")
                        }
                    }
                    
                    // Emit message to UI
                    _incomingMessages.value = it
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error parsing incoming message", e)
            }
        }
        PerformanceTracker.logNetworkOperation(NetworkOperation.MESSAGE_RECEIVE, handleTime)
    }
    
    /**
     * Handle streaming audio chunks for immediate playback.
     */
    private fun handleStreamingAudioChunk(message: WebSocketMessage) {
        // Emit the audio chunk for immediate processing by TTS service
        serviceScope.launch {
            message.audioChunk?.let { audioData ->
                message.text?.let { text ->
                    Log.d(TAG, "🎵 Processing audio chunk: '$text' (${audioData.length} chars)")
                    // The TTSService will handle immediate playback
                    _incomingMessages.value = message
                }
            }
        }
    }
    
    /**
     * Attempt to reconnect to the server.
     */
    private fun attemptReconnect() {
        if (isReconnecting || currentServerUrl == null) return
        
        isReconnecting = true
        reconnectAttempts++
        _connectionState.value = ConnectionState.RECONNECTING
        
        Log.i(TAG, "Attempting reconnection $reconnectAttempts/$MAX_RECONNECT_ATTEMPTS")
        
        serviceScope.launch {
            delay(RECONNECT_DELAY_MS)
            
            if (isReconnecting && currentServerUrl != null) {
                connect(currentServerUrl!!)
            }
        }
    }
    
    /**
     * Get current connection statistics.
     */
    fun getConnectionStats(): ConnectionStats {
        return ConnectionStats(
            isConnected = _connectionState.value == ConnectionState.CONNECTED,
            serverUrl = currentServerUrl,
            sessionId = currentSessionId,
            reconnectAttempts = reconnectAttempts
        )
    }
    
    inner class WebSocketBinder : Binder() {
        fun getService(): WebSocketService = this@WebSocketService
    }
}

/**
 * Connection statistics for debugging and monitoring.
 */
data class ConnectionStats(
    val isConnected: Boolean,
    val serverUrl: String?,
    val sessionId: String?,
    val reconnectAttempts: Int
)
