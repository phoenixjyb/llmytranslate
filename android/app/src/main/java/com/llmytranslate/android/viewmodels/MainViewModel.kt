package com.llmytranslate.android.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.llmytranslate.android.models.ChatMessage
import com.llmytranslate.android.models.ConnectionState
import com.llmytranslate.android.services.STTService
import com.llmytranslate.android.services.TTSService
import com.llmytranslate.android.services.WebSocketService
import com.llmytranslate.android.utils.PerformanceTracker
import com.llmytranslate.android.utils.AudioOperation
import com.llmytranslate.android.utils.NetworkOperation
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import android.util.Log
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class MainViewModel @Inject constructor(
    private val sttService: STTService,
    private val ttsService: TTSService,
    private val webSocketService: WebSocketService
) : ViewModel() {

    companion object {
        private const val TAG = "MainViewModel"
    }

    // UI State
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _inputText = MutableStateFlow("")
    val inputText: StateFlow<String> = _inputText.asStateFlow()

    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening.asStateFlow()

    private val _isSpeaking = MutableStateFlow(false)
    val isSpeaking: StateFlow<Boolean> = _isSpeaking.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    private val _currentLanguage = MutableStateFlow("en-US")
    val currentLanguage: StateFlow<String> = _currentLanguage.asStateFlow()

    init {
        Log.i(TAG, "🚀 MainViewModel initialized with services")
        observeServiceStates()
    }

    private fun observeServiceStates() {
        viewModelScope.launch {
            // Observe STT state
            sttService.isListeningState.collect { listening ->
                _isListening.value = listening
            }
        }

        viewModelScope.launch {
            // Observe STT results
            sttService.finalResults.collect { result ->
                result?.let { sttResult ->
                    _inputText.value = sttResult.text
                    Log.i(TAG, "📝 Speech recognition result: ${sttResult.text}")
                }
            }
        }

        viewModelScope.launch {
            // Observe TTS state
            ttsService.isSpeakingState.collect { speaking ->
                _isSpeaking.value = speaking
            }
        }

        viewModelScope.launch {
            // Observe WebSocket connection
            webSocketService.connectionState.collect { state ->
                _isConnected.value = state == ConnectionState.CONNECTED
            }
        }

        viewModelScope.launch {
            // Observe errors from all services
            launch {
                sttService.error.collect { error ->
                    error?.let { _error.value = "STT: $it" }
                }
            }
            launch {
                ttsService.error.collect { error ->
                    error?.let { _error.value = "TTS: $it" }
                }
            }
        }
    }

    fun updateInputText(text: String) {
        _inputText.value = text
    }

    fun startListening() {
        Log.i(TAG, "🎤 Starting speech recognition")
        val startTime = System.currentTimeMillis()
        
        sttService.startListening(_currentLanguage.value)
        
        val duration = System.currentTimeMillis() - startTime
        PerformanceTracker.logAudioOperation(
            AudioOperation.STT_START,
            duration
        )
    }

    fun stopListening() {
        Log.i(TAG, "⏹️ Stopping speech recognition")
        sttService.stopListening()
    }

    fun toggleListening() {
        if (_isListening.value) {
            stopListening()
        } else {
            startListening()
        }
    }

    fun stopSpeaking() {
        Log.i(TAG, "🔇 Stopping text-to-speech")
        ttsService.stop()
    }

    fun sendMessage() {
        val messageText = _inputText.value.trim()
        if (messageText.isEmpty()) return

        Log.i(TAG, "📤 Sending message: $messageText")
        val startTime = System.currentTimeMillis()

        val userMessage = ChatMessage(
            id = System.currentTimeMillis().toString(),
            text = messageText,
            isUser = true,
            timestamp = System.currentTimeMillis()
        )

        _messages.value = _messages.value + userMessage
        _inputText.value = ""

        viewModelScope.launch {
            try {
                webSocketService.sendTextMessage(messageText)
                
                val duration = System.currentTimeMillis() - startTime
                PerformanceTracker.logNetworkOperation(
                    NetworkOperation.MESSAGE_SEND,
                    duration
                )
            } catch (e: Exception) {
                Log.e(TAG, "❌ Failed to send message", e)
                _error.value = "Failed to send message: ${e.message}"
            }
        }
    }

    fun clearError() {
        _error.value = null
    }

    fun changeLanguage(language: String) {
        _currentLanguage.value = language
        Log.i(TAG, "🌐 Language changed to: $language")
    }

    override fun onCleared() {
        super.onCleared()
        Log.i(TAG, "🧹 MainViewModel cleared")
    }
}
