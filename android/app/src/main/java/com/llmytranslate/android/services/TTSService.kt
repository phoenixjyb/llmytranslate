package com.llmytranslate.android.services

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * TTSService handles native Android text-to-speech synthesis.
 * Optimized for Samsung S24 Ultra with high-quality neural voices.
 */
@Singleton
class TTSService @Inject constructor(
    private val context: Context
) {
    
    companion object {
        private const val TAG = "TTSService"
        private const val UTTERANCE_ID_PREFIX = "llmytranslate_"
    }
    
    private var textToSpeech: TextToSpeech? = null
    private var isInitialized = false
    private var isSpeaking = false
    private var currentLanguage = "en-US"
    private var speechRate = 1.0f
    private var speechPitch = 1.0f
    
    // State flows for UI updates
    private val _isInitialized = MutableStateFlow(false)
    val isInitializedState: StateFlow<Boolean> = _isInitialized.asStateFlow()
    
    private val _isSpeaking = MutableStateFlow(false)
    val isSpeakingState: StateFlow<Boolean> = _isSpeaking.asStateFlow()
    
    private val _currentUtterance = MutableStateFlow<String>("")
    val currentUtterance: StateFlow<String> = _currentUtterance.asStateFlow()
    
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    private val _availableVoices = MutableStateFlow<List<VoiceInfo>>(emptyList())
    val availableVoices: StateFlow<List<VoiceInfo>> = _availableVoices.asStateFlow()
    
    /**
     * Initialize text-to-speech engine.
     */
    fun initialize() {
        if (isInitialized) {
            Log.w(TAG, "TTS already initialized")
            return
        }
        
        textToSpeech = TextToSpeech(context) { status ->
            when (status) {
                TextToSpeech.SUCCESS -> {
                    isInitialized = true
                    _isInitialized.value = true
                    _error.value = null
                    
                    setupTTS()
                    loadAvailableVoices()
                    
                    Log.i(TAG, "TTS initialized successfully")
                }
                else -> {
                    isInitialized = false
                    _isInitialized.value = false
                    _error.value = "TTS initialization failed"
                    Log.e(TAG, "TTS initialization failed with status: $status")
                }
            }
        }
    }
    
    /**
     * Set up TTS with progress listener and default settings.
     */
    private fun setupTTS() {
        textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                isSpeaking = true
                _isSpeaking.value = true
                Log.d(TAG, "TTS started: $utteranceId")
            }
            
            override fun onDone(utteranceId: String?) {
                isSpeaking = false
                _isSpeaking.value = false
                _currentUtterance.value = ""
                Log.d(TAG, "TTS completed: $utteranceId")
            }
            
            override fun onError(utteranceId: String?) {
                isSpeaking = false
                _isSpeaking.value = false
                _currentUtterance.value = ""
                _error.value = "TTS playback error"
                Log.e(TAG, "TTS error: $utteranceId")
            }
            
            override fun onStop(utteranceId: String?, interrupted: Boolean) {
                isSpeaking = false
                _isSpeaking.value = false
                _currentUtterance.value = ""
                Log.d(TAG, "TTS stopped: $utteranceId, interrupted: $interrupted")
            }
        })
        
        // Set default language
        setLanguage(currentLanguage)
        setSpeechRate(speechRate)
        setPitch(speechPitch)
    }
    
    /**
     * Speak text using Android TTS.
     */
    fun speak(
        text: String,
        language: String = currentLanguage,
        rate: Float = speechRate,
        pitch: Float = speechPitch,
        queueMode: Int = TextToSpeech.QUEUE_FLUSH
    ) {
        if (!isInitialized || textToSpeech == null) {
            Log.e(TAG, "TTS not initialized")
            _error.value = "TTS not ready"
            return
        }
        
        if (text.isBlank()) {
            Log.w(TAG, "Empty text provided for TTS")
            return
        }
        
        // Update settings if changed
        if (language != currentLanguage) {
            setLanguage(language)
        }
        if (rate != speechRate) {
            setSpeechRate(rate)
        }
        if (pitch != speechPitch) {
            setPitch(pitch)
        }
        
        val utteranceId = "${UTTERANCE_ID_PREFIX}${System.currentTimeMillis()}"
        val params = Bundle().apply {
            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
            
            // Samsung TTS specific optimizations
            putString(TextToSpeech.Engine.KEY_PARAM_STREAM, "STREAM_MUSIC")
            putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f)
        }
        
        try {
            val result = textToSpeech?.speak(text, queueMode, params, utteranceId)
            
            when (result) {
                TextToSpeech.SUCCESS -> {
                    _currentUtterance.value = text
                    _error.value = null
                    Log.i(TAG, "TTS started for: ${text.take(50)}...")
                }
                TextToSpeech.ERROR -> {
                    _error.value = "TTS speak failed"
                    Log.e(TAG, "TTS speak failed")
                }
                else -> {
                    _error.value = "TTS unknown error"
                    Log.e(TAG, "TTS unknown result: $result")
                }
            }
        } catch (e: Exception) {
            _error.value = "TTS exception: ${e.message}"
            Log.e(TAG, "TTS exception", e)
        }
    }
    
    /**
     * Stop current TTS playback.
     */
    fun stop() {
        try {
            textToSpeech?.stop()
            isSpeaking = false
            _isSpeaking.value = false
            _currentUtterance.value = ""
            Log.i(TAG, "TTS stopped")
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping TTS", e)
        }
    }
    
    /**
     * Set TTS language.
     */
    fun setLanguage(language: String): Boolean {
        if (!isInitialized || textToSpeech == null) return false
        
        try {
            val locale = Locale.forLanguageTag(language)
            val result = textToSpeech?.setLanguage(locale)
            
            when (result) {
                TextToSpeech.LANG_AVAILABLE,
                TextToSpeech.LANG_COUNTRY_AVAILABLE,
                TextToSpeech.LANG_COUNTRY_VAR_AVAILABLE -> {
                    currentLanguage = language
                    Log.i(TAG, "TTS language set to: $language")
                    return true
                }
                TextToSpeech.LANG_MISSING_DATA -> {
                    _error.value = "Language data missing for: $language"
                    Log.e(TAG, "Language data missing for: $language")
                    return false
                }
                TextToSpeech.LANG_NOT_SUPPORTED -> {
                    _error.value = "Language not supported: $language"
                    Log.e(TAG, "Language not supported: $language")
                    return false
                }
                else -> {
                    _error.value = "Unknown language error: $result"
                    Log.e(TAG, "Unknown language result: $result")
                    return false
                }
            }
        } catch (e: Exception) {
            _error.value = "Error setting language: ${e.message}"
            Log.e(TAG, "Error setting language", e)
            return false
        }
    }
    
    /**
     * Set TTS speech rate.
     */
    fun setSpeechRate(rate: Float): Boolean {
        if (!isInitialized || textToSpeech == null) return false
        
        try {
            val result = textToSpeech?.setSpeechRate(rate)
            if (result == TextToSpeech.SUCCESS) {
                speechRate = rate
                Log.i(TAG, "TTS speech rate set to: $rate")
                return true
            } else {
                Log.e(TAG, "Failed to set speech rate: $result")
                return false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting speech rate", e)
            return false
        }
    }
    
    /**
     * Set TTS pitch.
     */
    fun setPitch(pitch: Float): Boolean {
        if (!isInitialized || textToSpeech == null) return false
        
        try {
            val result = textToSpeech?.setPitch(pitch)
            if (result == TextToSpeech.SUCCESS) {
                speechPitch = pitch
                Log.i(TAG, "TTS pitch set to: $pitch")
                return true
            } else {
                Log.e(TAG, "Failed to set pitch: $result")
                return false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting pitch", e)
            return false
        }
    }
    
    /**
     * Load available voices for current TTS engine.
     */
    private fun loadAvailableVoices() {
        if (!isInitialized || textToSpeech == null) return
        
        try {
            val voices = textToSpeech?.voices
            val voiceInfoList = voices?.map { voice ->
                VoiceInfo(
                    name = voice.name,
                    locale = voice.locale.toString(),
                    quality = when (voice.quality) {
                        android.speech.tts.Voice.QUALITY_VERY_HIGH -> "Very High"
                        android.speech.tts.Voice.QUALITY_HIGH -> "High"
                        android.speech.tts.Voice.QUALITY_NORMAL -> "Normal"
                        android.speech.tts.Voice.QUALITY_LOW -> "Low"
                        android.speech.tts.Voice.QUALITY_VERY_LOW -> "Very Low"
                        else -> "Unknown"
                    },
                    isNetworkConnectionRequired = voice.isNetworkConnectionRequired,
                    features = voice.features?.toList() ?: emptyList()
                )
            } ?: emptyList()
            
            _availableVoices.value = voiceInfoList
            Log.i(TAG, "Loaded ${voiceInfoList.size} voices")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error loading voices", e)
        }
    }
    
    /**
     * Get supported languages for TTS.
     */
    fun getSupportedLanguages(): List<String> {
        return listOf(
            "en-US", "en-GB", "en-AU", "en-CA", "en-IN",
            "zh-CN", "zh-TW", "zh-HK",
            "es-ES", "es-US", "es-MX",
            "fr-FR", "fr-CA",
            "de-DE", "de-AT",
            "it-IT", "pt-BR", "pt-PT",
            "ja-JP", "ko-KR",
            "ru-RU", "ar-SA",
            "hi-IN", "th-TH",
            "nl-NL", "sv-SE", "da-DK",
            "no-NO", "fi-FI", "pl-PL"
        )
    }
    
    /**
     * Check if TTS is currently speaking.
     */
    fun isSpeaking(): Boolean = isSpeaking
    
    /**
     * Check if TTS engine supports Samsung Neural voices.
     */
    fun supportsSamsungNeural(): Boolean {
        return android.os.Build.MANUFACTURER.equals("samsung", ignoreCase = true) &&
               android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S
    }
    
    /**
     * Destroy TTS engine and clean up resources.
     */
    fun destroy() {
        stop()
        textToSpeech?.shutdown()
        textToSpeech = null
        isInitialized = false
        _isInitialized.value = false
        Log.i(TAG, "TTS Service destroyed")
    }
}

/**
 * Voice information data class.
 */
data class VoiceInfo(
    val name: String,
    val locale: String,
    val quality: String,
    val isNetworkConnectionRequired: Boolean,
    val features: List<String>
)
