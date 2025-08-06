package com.llmytranslate.android.services

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import com.llmytranslate.android.models.STTResult

/**
 * STTService handles native Android speech recognition.
 * Optimized for Samsung S24 Ultra with hardware acceleration and on-device processing.
 */
class STTService(private val context: Context) {
    
    companion object {
        private const val TAG = "STTService"
        private const val SAMSUNG_STT_PACKAGE = "com.samsung.android.svoiceime"
        private const val GOOGLE_STT_PACKAGE = "com.google.android.googlequicksearchbox"
    }
    
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false
    private var currentLanguage = "en-US"
    private var isSamsungSTTAvailable = false
    
    // State flows for UI updates
    private val _isListening = MutableStateFlow(false)
    val isListeningState: StateFlow<Boolean> = _isListening.asStateFlow()
    
    private val _partialResults = MutableStateFlow<String>("")
    val partialResults: StateFlow<String> = _partialResults.asStateFlow()
    
    private val _finalResults = MutableStateFlow<STTResult?>(null)
    val finalResults: StateFlow<STTResult?> = _finalResults.asStateFlow()
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    private val _confidence = MutableStateFlow<Float>(0f)
    val confidence: StateFlow<Float> = _confidence.asStateFlow()
    
    /**
     * Initialize speech recognizer with Samsung optimization.
     */
    fun initialize() {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.e(TAG, "Speech recognition not available on this device")
            _error.value = "Speech recognition not available"
            return
        }
        
        // Check for Samsung STT availability
        isSamsungSTTAvailable = checkSamsungSTTAvailability()
        
        // Create speech recognizer with optimal engine
        speechRecognizer = if (isSamsungSTTAvailable) {
            Log.i(TAG, "Using Samsung STT for hardware acceleration")
            SpeechRecognizer.createSpeechRecognizer(context, ComponentName(SAMSUNG_STT_PACKAGE, ""))
        } else {
            Log.i(TAG, "Using Google STT as fallback")
            SpeechRecognizer.createSpeechRecognizer(context)
        }
        
        speechRecognizer?.setRecognitionListener(recognitionListener)
        Log.i(TAG, "STT Service initialized with ${if (isSamsungSTTAvailable) "Samsung" else "Google"} engine")
    }
    
    /**
     * Check if Samsung STT is available for hardware acceleration.
     */
    private fun checkSamsungSTTAvailability(): Boolean {
        return try {
            val packageManager = context.packageManager
            packageManager.getPackageInfo(SAMSUNG_STT_PACKAGE, 0)
            Log.i(TAG, "Samsung STT package found - hardware acceleration available")
            true
        } catch (e: Exception) {
            Log.i(TAG, "Samsung STT not available, using standard Android STT")
            false
        }
    }
    
    /**
     * Start listening for speech input with Samsung optimizations.
     */
    fun startListening(language: String = "en-US", continuous: Boolean = false) {
        if (isListening) {
            Log.w(TAG, "Already listening")
            return
        }
        
        if (speechRecognizer == null) {
            initialize()
        }
        
        currentLanguage = language
        
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
            
            // Samsung S24 Ultra optimizations
            if (isSamsungSTTAvailable) {
                // Enable on-device processing for faster response
                putExtra("samsung.stt.ondevice", true)
                // Enable noise cancellation using hardware
                putExtra("samsung.stt.noise_cancellation", true)
                // Use hardware-accelerated VAD (Voice Activity Detection)
                putExtra("samsung.stt.vad_enabled", true)
                // Enable real-time partial results for better UX
                putExtra("samsung.stt.realtime_partial", true)
            }
            
            // Standard Android optimizations
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1500)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1500)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 500)
            
            // Samsung S24 Ultra specific optimizations
            putExtra("android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES", arrayOf(language))
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true) // Use on-device recognition
            
            // Continuous listening for conversation mode
            if (continuous) {
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 3000)
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 2000)
            }
        }
        
        try {
            speechRecognizer?.startListening(intent)
            isListening = true
            _isListening.value = true
            _error.value = null
            Log.i(TAG, "Started listening in $language")
        } catch (e: Exception) {
            Log.e(TAG, "Error starting speech recognition", e)
            _error.value = "Failed to start speech recognition: ${e.message}"
        }
    }
    
    /**
     * Stop listening for speech input.
     */
    fun stopListening() {
        if (!isListening) return
        
        try {
            speechRecognizer?.stopListening()
            isListening = false
            _isListening.value = false
            Log.i(TAG, "Stopped listening")
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping speech recognition", e)
        }
    }
    
    /**
     * Cancel current speech recognition.
     */
    fun cancel() {
        if (!isListening) return
        
        try {
            speechRecognizer?.cancel()
            isListening = false
            _isListening.value = false
            _partialResults.value = ""
            Log.i(TAG, "Cancelled speech recognition")
        } catch (e: Exception) {
            Log.e(TAG, "Error cancelling speech recognition", e)
        }
    }
    
    /**
     * Destroy speech recognizer and clean up resources.
     */
    fun destroy() {
        cancel()
        speechRecognizer?.destroy()
        speechRecognizer = null
        Log.i(TAG, "STT Service destroyed")
    }
    
    /**
     * Check if device supports offline speech recognition.
     */
    fun supportsOfflineRecognition(): Boolean {
        // Samsung S24 Ultra has excellent on-device speech recognition
        return android.os.Build.MANUFACTURER.equals("samsung", ignoreCase = true) &&
               android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S
    }
    
    /**
     * Get available languages for speech recognition.
     */
    fun getAvailableLanguages(): List<String> {
        return listOf(
            "en-US", "en-GB", "en-AU", "en-CA",
            "zh-CN", "zh-TW", "zh-HK",
            "es-ES", "es-US", "es-MX",
            "fr-FR", "fr-CA",
            "de-DE", "de-AT",
            "it-IT", "pt-BR", "pt-PT",
            "ja-JP", "ko-KR",
            "ru-RU", "ar-SA",
            "hi-IN", "th-TH"
        )
    }
    
    private val recognitionListener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            Log.d(TAG, "Ready for speech")
        }
        
        override fun onBeginningOfSpeech() {
            Log.d(TAG, "Beginning of speech")
        }
        
        override fun onRmsChanged(rmsdB: Float) {
            // Audio level changed - could be used for visualizations
        }
        
        override fun onBufferReceived(buffer: ByteArray?) {
            // Audio buffer received
        }
        
        override fun onEndOfSpeech() {
            Log.d(TAG, "End of speech")
            isListening = false
            _isListening.value = false
        }
        
        override fun onError(error: Int) {
            val errorMessage = when (error) {
                SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
                SpeechRecognizer.ERROR_NETWORK -> "Network error"
                SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                SpeechRecognizer.ERROR_NO_MATCH -> "No speech match found"
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognition service busy"
                SpeechRecognizer.ERROR_SERVER -> "Server error"
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech input timeout"
                else -> "Unknown error: $error"
            }
            
            Log.e(TAG, "Speech recognition error: $errorMessage")
            
            isListening = false
            _isListening.value = false
            
            // Don't treat "no match" as a critical error
            if (error != SpeechRecognizer.ERROR_NO_MATCH) {
                _error.value = errorMessage
            }
        }
        
        override fun onResults(results: Bundle?) {
            results?.let { bundle ->
                val matches = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val confidence = bundle.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)
                
                if (!matches.isNullOrEmpty()) {
                    val bestMatch = matches[0]
                    val bestConfidence = confidence?.get(0) ?: 0.0f
                    
                    Log.i(TAG, "Final result: '$bestMatch' (confidence: $bestConfidence)")
                    
                    _finalResults.value = STTResult(
                        text = bestMatch,
                        confidence = bestConfidence,
                        isPartial = false
                    )
                    
                    _partialResults.value = ""
                }
            }
            
            isListening = false
            _isListening.value = false
        }
        
        override fun onPartialResults(partialResults: Bundle?) {
            partialResults?.let { bundle ->
                val matches = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    val partialText = matches[0]
                    Log.d(TAG, "Partial result: '$partialText'")
                    _partialResults.value = partialText
                }
            }
        }
        
        override fun onEvent(eventType: Int, params: Bundle?) {
            Log.d(TAG, "Speech recognition event: $eventType")
        }
    }
}
