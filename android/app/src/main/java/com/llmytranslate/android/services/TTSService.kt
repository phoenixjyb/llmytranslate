package com.llmytranslate.android.services

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*

/**
 * TTSService handles native Android text-to-speech functionality.
 * Optimized for Samsung S24 Ultra with Samsung TTS engine.
 * Enhanced with streaming TTS support for real-time conversation.
 */
class TTSService(private val context: Context) : TextToSpeech.OnInitListener {
    
    companion object {
        private const val TAG = "TTSService"
        private const val SAMSUNG_TTS_PACKAGE = "com.samsung.android.speech.tts"
        private const val GOOGLE_TTS_PACKAGE = "com.google.android.tts"
    }
    
    private var textToSpeech: TextToSpeech? = null
    private var isInitialized = false
    private var currentLanguage = Locale.US
    private var speechRate = 1.0f
    private var pitch = 1.0f
    
    // Streaming TTS support
    private val audioQueue = mutableListOf<String>()
    private var isStreamingActive = false
    private var currentStreamSessionId: String? = null
    
    // State flows for UI updates
    private val _isInitialized = MutableStateFlow(false)
    val isInitializedState: StateFlow<Boolean> = _isInitialized.asStateFlow()
    
    private val _isSpeaking = MutableStateFlow(false)
    val isSpeakingState: StateFlow<Boolean> = _isSpeaking.asStateFlow()
    
    private val _isStreaming = MutableStateFlow(false)
    val isStreamingState: StateFlow<Boolean> = _isStreaming.asStateFlow()
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    init {
        initializeTTS()
    }
    
    private fun initializeTTS() {
        try {
            textToSpeech = TextToSpeech(context, this)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize TTS", e)
            _error.value = "Failed to initialize text-to-speech: ${e.message}"
        }
    }
    
    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            textToSpeech?.let { tts ->
                val result = tts.setLanguage(currentLanguage)
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    Log.w(TAG, "Language not supported: $currentLanguage")
                    _error.value = "Language not supported: $currentLanguage"
                } else {
                    isInitialized = true
                    _isInitialized.value = true
                    setupProgressListener()
                    Log.d(TAG, "TTS initialized successfully")
                }
            }
        } else {
            Log.e(TAG, "TTS initialization failed with status: $status")
            _error.value = "Text-to-speech initialization failed"
        }
    }
    
    private fun setupProgressListener() {
        textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                _isSpeaking.value = true
            }
            
            override fun onDone(utteranceId: String?) {
                _isSpeaking.value = false
                
                // Process next chunk in queue if streaming
                if (isStreamingActive && audioQueue.isNotEmpty()) {
                    val nextText = audioQueue.removeAt(0)
                    Log.d(TAG, "🎵 Playing next streaming chunk: '${nextText.take(30)}...'")
                    speak(nextText, TextToSpeech.QUEUE_FLUSH)
                } else if (isStreamingActive && audioQueue.isEmpty()) {
                    Log.d(TAG, "🎵 Streaming queue empty, waiting for next chunk...")
                }
            }
            
            override fun onError(utteranceId: String?) {
                _isSpeaking.value = false
                _error.value = "Speech synthesis error"
                Log.e(TAG, "TTS error for utterance: $utteranceId")
                
                // Continue with next chunk even on error
                if (isStreamingActive && audioQueue.isNotEmpty()) {
                    val nextText = audioQueue.removeAt(0)
                    speak(nextText, TextToSpeech.QUEUE_FLUSH)
                }
            }
        })
    }
    
    /**
     * Start streaming TTS session.
     */
    fun startStreaming(sessionId: String) {
        Log.i(TAG, "🚀 Starting streaming TTS session: $sessionId")
        currentStreamSessionId = sessionId
        isStreamingActive = true
        _isStreaming.value = true
        audioQueue.clear()
    }
    
    /**
     * Add text chunk to streaming queue and play immediately if not speaking.
     */
    fun addStreamingChunk(text: String, chunkIndex: Int, isFirstChunk: Boolean = false) {
        if (!isInitialized) {
            Log.w(TAG, "TTS not initialized, cannot add streaming chunk")
            return
        }
        
        Log.d(TAG, "🎵 Adding streaming chunk $chunkIndex: '${text.take(50)}...'")
        
        if (isFirstChunk || !_isSpeaking.value) {
            // Speak immediately if first chunk or not currently speaking
            Log.d(TAG, "🎵 Speaking chunk immediately (first: $isFirstChunk, speaking: ${_isSpeaking.value})")
            speak(text, TextToSpeech.QUEUE_FLUSH)
        } else {
            // Add to queue for sequential playback
            audioQueue.add(text)
            Log.d(TAG, "🎵 Added to queue (queue size: ${audioQueue.size})")
        }
    }
    
    /**
     * Complete streaming session.
     */
    fun completeStreaming() {
        Log.i(TAG, "✅ Completing streaming TTS session: $currentStreamSessionId")
        isStreamingActive = false
        _isStreaming.value = false
        currentStreamSessionId = null
        // Don't clear queue - let remaining chunks finish playing
    }
    
    /**
     * Stop streaming and clear queue.
     */
    fun stopStreaming() {
        Log.i(TAG, "🛑 Stopping streaming TTS session: $currentStreamSessionId")
        isStreamingActive = false
        _isStreaming.value = false
        currentStreamSessionId = null
        audioQueue.clear()
        textToSpeech?.stop()
        _isSpeaking.value = false
    }
    
    fun speak(text: String, queueMode: Int = TextToSpeech.QUEUE_FLUSH): Boolean {
        if (!isInitialized) {
            _error.value = "TTS not initialized"
            return false
        }
        
        return try {
            val utteranceId = "utterance_${System.currentTimeMillis()}"
            Log.d(TAG, "🔊 Speaking: '${text.take(50)}...' (mode: $queueMode)")
            textToSpeech?.speak(text, queueMode, null, utteranceId)
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to speak text", e)
            _error.value = "Failed to speak: ${e.message}"
            false
        }
    }
    
    // Backward compatibility
    fun speak(text: String): Boolean = speak(text, TextToSpeech.QUEUE_FLUSH)
            _error.value = "Failed to speak: ${e.message}"
            false
        }
    }
    
    fun stop() {
        textToSpeech?.stop()
        _isSpeaking.value = false
    }
    
    fun setLanguage(locale: Locale): Boolean {
        return textToSpeech?.let { tts ->
            val result = tts.setLanguage(locale)
            if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                currentLanguage = locale
                true
            } else {
                _error.value = "Language not supported: $locale"
                false
            }
        } ?: false
    }
    
    fun setSpeechRate(rate: Float) {
        speechRate = rate.coerceIn(0.1f, 3.0f)
        textToSpeech?.setSpeechRate(speechRate)
    }
    
    fun setPitch(pitchValue: Float) {
        pitch = pitchValue.coerceIn(0.1f, 2.0f)
        textToSpeech?.setPitch(pitch)
    }
    
    fun getAvailableLanguages(): Set<Locale>? {
        return textToSpeech?.availableLanguages
    }
    
    fun cleanup() {
        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null
        isInitialized = false
        _isInitialized.value = false
        _isSpeaking.value = false
    }
}
