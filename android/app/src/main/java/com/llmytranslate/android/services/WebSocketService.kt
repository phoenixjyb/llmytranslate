package com.llmytranslate.android.services

import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import com.llmytranslate.android.models.*
import com.squareup.moshi.Moshi
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI
import java.util.*
import javax.inject.Inject

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
    
    @Inject
    lateinit var moshi: Moshi
    
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
        Log.i(TAG, "WebSocketService created")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        disconnect()
        serviceScope.cancel()
        Log.i(TAG, "WebSocketService destroyed")
    }
    
    /**
     * Connect to LLMyTranslate server WebSocket.
     */
    fun connect(serverUrl: String, sessionSettings: SessionSettings? = null) {
        if (_connectionState.value == ConnectionState.CONNECTED && currentServerUrl == serverUrl) {
            Log.i(TAG, "Already connected to $serverUrl")
            return
        }
        
        currentServerUrl = serverUrl
        _connectionState.value = ConnectionState.CONNECTING
        
        serviceScope.launch {
            try {
                val uri = URI(serverUrl)
                Log.i(TAG, "Connecting to WebSocket: $uri")
                
                webSocketClient = object : WebSocketClient(uri) {
                    override fun onOpen(handshake: ServerHandshake?) {
                        Log.i(TAG, "WebSocket connected")
                        _connectionState.value = ConnectionState.CONNECTED
                        reconnectAttempts = 0
                        isReconnecting = false
                        
                        // Start session immediately
                        startSession(sessionSettings)
                    }
                    
                    override fun onMessage(message: String?) {
                        message?.let { handleIncomingMessage(it) }
                    }
                    
                    override fun onClose(code: Int, reason: String?, remote: Boolean) {
                        Log.i(TAG, "WebSocket closed: code=$code, reason=$reason, remote=$remote")
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
     * Disconnect from WebSocket server.
     */
    fun disconnect() {
        isReconnecting = false
        currentSessionId?.let { endSession(it) }
        
        webSocketClient?.close()
        webSocketClient = null
        currentServerUrl = null
        currentSessionId = null
        
        _connectionState.value = ConnectionState.DISCONNECTED
        Log.i(TAG, "WebSocket disconnected")
    }
    
    /**
     * Send text message to server (from Android STT).
     */
    fun sendTextMessage(text: String) {
        currentSessionId?.let { sessionId ->
            val message = WebSocketMessage(
                type = "text_input",
                sessionId = sessionId,
                text = text
            )
            sendMessage(message)
        }
    }
    
    /**
     * Update session settings.
     */
    fun updateSettings(settings: SessionSettings) {
        currentSessionId?.let { sessionId ->
            val message = WebSocketMessage(
                type = "settings_update",
                sessionId = sessionId,
                settings = settings
            )
            sendMessage(message)
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
        try {
            val jsonMessage = messageAdapter.toJson(message)
            webSocketClient?.send(jsonMessage)
            Log.d(TAG, "Sent message: ${message.type}")
        } catch (e: Exception) {
            Log.e(TAG, "Error sending message", e)
        }
    }
    
    /**
     * Handle incoming WebSocket messages.
     */
    private fun handleIncomingMessage(messageJson: String) {
        try {
            val message = messageAdapter.fromJson(messageJson)
            if (message != null) {
                Log.d(TAG, "Received message: ${message.type}")
                
                // Handle special message types
                when (message.type) {
                    "session_started" -> {
                        message.serverInfo?.let { _serverInfo.value = it }
                        Log.i(TAG, "Session started with server info")
                    }
                    "ai_response" -> {
                        Log.i(TAG, "Received AI response: ${message.text?.take(50)}...")
                    }
                    "error" -> {
                        Log.w(TAG, "Server error: ${message.message}")
                    }
                }
                
                // Emit message to UI
                _incomingMessages.value = message
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing incoming message", e)
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
