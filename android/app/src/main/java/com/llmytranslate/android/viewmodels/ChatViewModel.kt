package com.llmytranslate.android.viewmodels

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.llmytranslate.android.models.*
import com.llmytranslate.android.services.WebSocketService
import com.llmytranslate.android.utils.NetworkManager
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*

/**
 * ChatViewModel handles text-based chat functionality.
 */
class ChatViewModel(private val context: Context) : ViewModel() {
    
    // Initialize services
    private val networkManager = NetworkManager(context)
    
    // UI state
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()
    
    // Connection state
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    // WebSocket service reference
    private var webSocketService: WebSocketService? = null
    
    // Message history
    private val messages = mutableListOf<Message>()
    
    /**
     * Initialize chat functionality.
     */
    fun initialize() {
        viewModelScope.launch {
            // Try to discover and connect to server automatically
            discoverAndConnect()
        }
    }
    
    /**
     * Set WebSocket service reference.
     */
    fun setWebSocketService(service: WebSocketService) {
        webSocketService = service
        
        // Observe connection state
        viewModelScope.launch {
            service.connectionState.collect { state ->
                _connectionState.value = state
                _uiState.value = _uiState.value.copy(connectionState = state)
            }
        }
        
        // Observe incoming messages
        viewModelScope.launch {
            service.incomingMessages.collect { message ->
                message?.let { handleIncomingMessage(it) }
            }
        }
    }
    
    /**
     * Send a text message to the server.
     */
    fun sendMessage(text: String) {
        if (text.isBlank()) return
        
        // Add user message to UI immediately
        val userMessage = Message(
            id = System.currentTimeMillis().toString(),
            sessionId = getCurrentSessionId(),
            text = text,
            isUser = true,
            timestamp = System.currentTimeMillis()
        )
        
        messages.add(userMessage)
        updateMessagesInUI()
        
        // Set loading state
        _uiState.value = _uiState.value.copy(
            isLoading = true,
            errorMessage = null
        )
        
        // Send to server
        webSocketService?.sendTextMessage(text)
    }
    
    /**
     * Retry connection to server.
     */
    fun retryConnection() {
        viewModelScope.launch {
            discoverAndConnect()
        }
    }
    
    /**
     * Discover servers and connect to the best one.
     */
    private suspend fun discoverAndConnect() {
        _connectionState.value = ConnectionState.CONNECTING
        
        try {
            val servers = networkManager.discoverServers()
            
            if (servers.isNotEmpty()) {
                val bestServer = servers.minByOrNull { it.responseTime }
                bestServer?.let { server ->
                    webSocketService?.connect(
                        server.websocketUrl,
                        SessionSettings(
                            language = "en-US",
                            kidFriendly = false,
                            model = "gemma2:2b",
                            useNativeSTT = true,
                            useNativeTTS = true
                        )
                    )
                }
            } else {
                _connectionState.value = ConnectionState.ERROR
                _uiState.value = _uiState.value.copy(
                    errorMessage = "No LLMyTranslate servers found on the network"
                )
            }
        } catch (e: Exception) {
            _connectionState.value = ConnectionState.ERROR
            _uiState.value = _uiState.value.copy(
                errorMessage = "Network error: ${e.message}"
            )
        }
    }
    
    /**
     * Handle incoming WebSocket messages.
     */
    private fun handleIncomingMessage(message: WebSocketMessage) {
        when (message.type) {
            "ai_response" -> {
                message.text?.let { aiText ->
                    val aiMessage = Message(
                        id = System.currentTimeMillis().toString(),
                        sessionId = getCurrentSessionId(),
                        text = aiText,
                        isUser = false,
                        timestamp = System.currentTimeMillis(),
                        processingTime = message.timing?.totalProcessing
                    )
                    
                    messages.add(aiMessage)
                    updateMessagesInUI()
                }
                
                // Clear loading state
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = null
                )
            }
            
            "error" -> {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = message.message ?: "Unknown server error"
                )
            }
            
            "session_started" -> {
                // Connection successful
                _uiState.value = _uiState.value.copy(
                    errorMessage = null
                )
                
                // Add welcome message
                val welcomeMessage = Message(
                    id = System.currentTimeMillis().toString(),
                    sessionId = getCurrentSessionId(),
                    text = "Connected to LLMyTranslate! You can now chat with AI using your Samsung S24 Ultra.",
                    isUser = false,
                    timestamp = System.currentTimeMillis()
                )
                
                messages.add(welcomeMessage)
                updateMessagesInUI()
            }
        }
    }
    
    /**
     * Update messages in UI state.
     */
    private fun updateMessagesInUI() {
        _uiState.value = _uiState.value.copy(
            messages = messages.toList()
        )
    }
    
    /**
     * Get current session ID (placeholder).
     */
    private fun getCurrentSessionId(): String {
        return "chat_session_${System.currentTimeMillis()}"
    }
    
    /**
     * Clear chat history.
     */
    fun clearChat() {
        messages.clear()
        updateMessagesInUI()
    }
    
    override fun onCleared() {
        super.onCleared()
        webSocketService?.disconnect()
    }
}
