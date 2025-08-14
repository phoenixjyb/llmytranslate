package com.llmytranslate.android.utils

import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Configuration for real-time testing with Termux Ollama.
 * Enables direct connection to phone's Termux instance.
 */
object TermuxStreamingConfig {
    private const val TAG = "TermuxStreamingConfig"
    
    // Termux connection settings
    const val TERMUX_SERVER_URL = "ws://127.0.0.1:8000"
    const val TERMUX_OLLAMA_URL = "http://127.0.0.1:11434"
    const val TEST_MODE_ENABLED = true
    
    // Streaming TTS settings for testing
    const val STREAMING_TTS_ENABLED = true
    const val QUICK_RESPONSE_MODE = true
    const val MAX_CHUNK_SIZE = 50 // Smaller chunks for real-time feel
    
    // Test messages for quick validation
    val TEST_MESSAGES = listOf(
        "Hello! Testing streaming TTS.",
        "How are you doing today?",
        "This is a real-time streaming test from Android to Termux.",
        "Can you hear the AI speaking as it thinks?"
    )
    
    data class StreamingTestState(
        val isTestMode: Boolean = TEST_MODE_ENABLED,
        val termuxConnected: Boolean = false,
        val streamingEnabled: Boolean = STREAMING_TTS_ENABLED,
        val lastTestMessage: String = "",
        val testResults: List<String> = emptyList()
    )
    
    private val _testState = MutableStateFlow(StreamingTestState())
    val testState: StateFlow<StreamingTestState> = _testState.asStateFlow()
    
    fun updateTermuxConnection(connected: Boolean) {
        _testState.value = _testState.value.copy(termuxConnected = connected)
        Log.i(TAG, "Termux connection: $connected")
    }
    
    fun logTestResult(message: String) {
        val currentResults = _testState.value.testResults.toMutableList()
        currentResults.add("[${System.currentTimeMillis()}] $message")
        
        // Keep only last 10 results
        if (currentResults.size > 10) {
            currentResults.removeAt(0)
        }
        
        _testState.value = _testState.value.copy(
            testResults = currentResults,
            lastTestMessage = message
        )
        
        Log.i(TAG, "Test result: $message")
    }
    
    fun getRandomTestMessage(): String {
        return TEST_MESSAGES.random()
    }
    
    fun enableQuickTest() {
        _testState.value = _testState.value.copy(
            isTestMode = true,
            streamingEnabled = true
        )
        Log.i(TAG, "Quick test mode enabled")
    }
}
