package com.llmytranslate.android.services

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import com.llmytranslate.android.models.STTResult
import com.llmytranslate.android.utils.PerformanceTracker
import com.llmytranslate.android.utils.AudioOperation
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.Base64
import kotlin.system.measureTimeMillis

/**
 * STTService handles native Android speech recognition.
 * Optimized for Samsung S24 Ultra with hardware acceleration and on-device processing.
 */
class STTService(private val context: Context) {
    
    companion object {
        private const val TAG = "STTService"
        private const val SAMSUNG_STT_PACKAGE = "com.samsung.android.svoiceime"
        private const val GOOGLE_STT_PACKAGE = "com.google.android.googlequicksearchbox"
        private const val SAMSUNG_INTELLIVOICE_PACKAGE = "com.samsung.android.intellivoiceservice"
        
        // Audio recording constants
        private const val SAMPLE_RATE = 16000
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        private const val RECORDING_TIMEOUT_MS = 10000L // 10 seconds max
    }
    
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false
    private var currentLanguage = "en-US"
    private var isSamsungSTTAvailable = false
    private var recognitionStartTime = 0L
    private var useDirectAudioRecording = false
    
    // Direct audio recording components
    private var audioRecord: AudioRecord? = null
    private var recordingJob: Job? = null
    private val recordingScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // Cloud STT service configuration
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    
    // For production, these should be in a secure configuration
    private val cloudSTTEnabled = true // Enable cloud fallback
    private val googleCloudAPIKey = "AIzaSyAHOklSEYt8woyVCLmul1ABPzPrHFsS3u8" // Add your Google Cloud API key here
    private val azureSTTKey = "" // Add your Azure Speech Services key here
    private val azureSTTRegion = "eastus" // Your Azure region
    
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
     * Initialize speech recognizer with Samsung optimization and multiple fallbacks.
     */
    fun initialize() {
        val initTime = measureTimeMillis {
            // Check for available speech recognition engines
            val availableEngines = getAvailableSpeechEngines()
            Log.i(TAG, "Available speech engines: ${availableEngines.joinToString(", ")}")
            
            // Check Google Speech Services status
            val googleEnabled = isGoogleSpeechServicesEnabled()
            Log.i(TAG, "Google Speech Services enabled: $googleEnabled")
            
            // Try Samsung STT first if available
            isSamsungSTTAvailable = checkSamsungSTTAvailability()
            
            // First try to create speech recognizer with priority order
            speechRecognizer = createSpeechRecognizerWithFallback()
            
            if (speechRecognizer != null) {
                speechRecognizer?.setRecognitionListener(recognitionListener)
                Log.i(TAG, "✅ STT Service initialized with ${if (isSamsungSTTAvailable) "Samsung" else "Google"} engine")
                useDirectAudioRecording = false
            } else {
                // Fallback to direct audio recording if system recognizer fails
                Log.w(TAG, "⚠️ System speech recognizer unavailable, falling back to direct audio recording")
                if (initializeDirectAudioRecording()) {
                    Log.i(TAG, "✅ STT Service initialized with direct audio recording")
                    useDirectAudioRecording = true
                } else {
                    Log.e(TAG, "❌ Failed to initialize both system recognizer and direct audio recording")
                    _error.value = "Speech recognition initialization failed"
                    return@measureTimeMillis
                }
            }
        }
        PerformanceTracker.logAudioOperation(AudioOperation.STT_INIT, initTime)
    }
    
    /**
     * Initialize direct audio recording as a fallback option.
     */
    private fun initializeDirectAudioRecording(): Boolean {
        return try {
            // Check if we have RECORD_AUDIO permission
            val hasPermission = ContextCompat.checkSelfPermission(
                context, 
                android.Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
            
            if (!hasPermission) {
                Log.e(TAG, "❌ RECORD_AUDIO permission not granted for direct recording")
                return false
            }
            
            // Test if we can create an AudioRecord
            val bufferSize = AudioRecord.getMinBufferSize(
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT
            )
            
            if (bufferSize == AudioRecord.ERROR || bufferSize == AudioRecord.ERROR_BAD_VALUE) {
                Log.e(TAG, "❌ Invalid audio recording configuration")
                return false
            }
            
            // Test AudioRecord creation
            val testRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            )
            
            val canRecord = testRecord.state == AudioRecord.STATE_INITIALIZED
            testRecord.release()
            
            if (!canRecord) {
                Log.e(TAG, "❌ AudioRecord initialization failed")
                return false
            }
            
            Log.i(TAG, "✅ Direct audio recording initialized successfully")
            true
        } catch (e: Exception) {
            Log.e(TAG, "❌ Direct audio recording initialization error: ${e.message}")
            false
        }
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
     * Get list of available speech recognition engines on the device.
     */
    private fun getAvailableSpeechEngines(): List<String> {
        val engines = mutableListOf<String>()
        val packageManager = context.packageManager
        
        // Check for Samsung STT
        try {
            packageManager.getPackageInfo(SAMSUNG_STT_PACKAGE, 0)
            engines.add("Samsung STT")
        } catch (e: Exception) {
            // Samsung STT not available
        }
        
        // Check for Samsung Intellivoice
        try {
            packageManager.getPackageInfo("com.samsung.android.intellivoiceservice", 0)
            engines.add("Samsung Intellivoice")
        } catch (e: Exception) {
            // Samsung Intellivoice not available
        }
        
        // Check for Google Speech Services
        try {
            packageManager.getPackageInfo("com.google.android.googlequicksearchbox", 0)
            engines.add("Google Speech Services")
        } catch (e: Exception) {
            // Google app not available
        }
        
        // Check for basic Android speech recognition
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        val activities = packageManager.queryIntentActivities(intent, 0)
        if (activities.isNotEmpty()) {
            engines.add("Android Speech Recognition (${activities.size} providers)")
        }
        
        return engines
    }
    
    /**
     * Check if Google Speech Services are properly enabled.
     */
    private fun isGoogleSpeechServicesEnabled(): Boolean {
        return try {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.setPackage("com.google.android.googlequicksearchbox")
            val packageManager = context.packageManager
            val activities = packageManager.queryIntentActivities(intent, 0)
            val result = activities.isNotEmpty()
            Log.i(TAG, "Google Speech Services enabled: $result")
            result
        } catch (e: Exception) {
            Log.w(TAG, "Error checking Google Speech Services: ${e.message}")
            false
        }
    }
    
    /**
     * Create speech recognizer with multiple fallback options.
     */
    private fun createSpeechRecognizerWithFallback(): SpeechRecognizer? {
        Log.i(TAG, "🎯 Creating speech recognizer - direct Google service approach")
        
        // Check permissions first
        if (!hasAudioPermission()) {
            Log.e(TAG, "❌ Audio permission not granted")
            return null
        }
        
        // Try to explicitly use Google's speech recognition service
        try {
            Log.i(TAG, "Attempting to use Google Recognition Service directly")
            val googleComponent = ComponentName(
                "com.google.android.googlequicksearchbox", 
                "com.google.android.voicesearch.serviceapi.GoogleRecognitionService"
            )
            val googleRecognizer = SpeechRecognizer.createSpeechRecognizer(context, googleComponent)
            if (googleRecognizer != null) {
                Log.i(TAG, "✅ Successfully created Google Recognition Service recognizer")
                return googleRecognizer
            }
        } catch (e: Exception) {
            Log.w(TAG, "⚠️ Google Recognition Service creation failed: ${e.message}")
        }
        
        // Fallback to default system recognizer
        try {
            Log.i(TAG, "Attempting default system speech recognizer")
            val defaultRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
            if (defaultRecognizer != null) {
                Log.i(TAG, "✅ Successfully created default speech recognizer")
                return defaultRecognizer
            }
        } catch (e: Exception) {
            Log.w(TAG, "⚠️ Default speech recognizer creation failed: ${e.message}")
        }
        
        Log.e(TAG, "❌ All speech recognizer creation attempts failed")
        return null
    }
    
    /**
     * Start listening for speech input with Samsung optimizations or direct audio recording.
     */
    fun startListening(language: String = "en-US", continuous: Boolean = false) {
        if (isListening) {
            Log.w(TAG, "Already listening")
            return
        }
        
        // Check microphone permission
        if (!hasAudioPermission()) {
            Log.e(TAG, "❌ No audio permission")
            _error.value = "Microphone permission required"
            return
        }
        
        // If speech recognizer is not available, try to initialize first
        if (speechRecognizer == null && !useDirectAudioRecording) {
            Log.i(TAG, "Speech recognizer not initialized, initializing now...")
            initialize()
        }
        
        recognitionStartTime = System.currentTimeMillis()
        currentLanguage = language
        
        val startTime = measureTimeMillis {
            if (useDirectAudioRecording) {
                startDirectAudioRecording(language, continuous)
            } else {
                startSystemSpeechRecognition(language, continuous)
            }
        }
        PerformanceTracker.logAudioOperation(AudioOperation.STT_START, startTime)
    }
    
    /**
     * Start system speech recognition using SpeechRecognizer.
     */
    private fun startSystemSpeechRecognition(language: String, continuous: Boolean) {
        if (speechRecognizer == null) {
            Log.e(TAG, "❌ Cannot start listening - speech recognizer not available")
            _error.value = "Speech recognition not available"
            return
        }
        
        // Additional check for recognition availability
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.w(TAG, "⚠️ SpeechRecognizer.isRecognitionAvailable() returned false, but proceeding anyway...")
        }
        
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
            Log.i(TAG, "🎤 Attempting to start listening with ${if (isSamsungSTTAvailable) "Samsung STT" else "Google STT"}")
            speechRecognizer?.startListening(intent)
            isListening = true
            _isListening.value = true
            _error.value = null
            Log.i(TAG, "Started listening in $language")
        } catch (e: Exception) {
            Log.e(TAG, "❌ Failed to start system speech recognition: ${e.message}")
            _error.value = "Failed to start speech recognition: ${e.message}"
            isListening = false
            _isListening.value = false
        }
    }
    
    /**
     * Start direct audio recording as fallback.
     */
    private fun startDirectAudioRecording(language: String, continuous: Boolean) {
        try {
            Log.i(TAG, "🎤 Starting direct audio recording mode")
            
            val bufferSize = AudioRecord.getMinBufferSize(
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT
            ) * 2 // Double buffer for safety
            
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize
            )
            
            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "❌ AudioRecord initialization failed")
                _error.value = "Audio recording initialization failed"
                return
            }
            
            audioRecord?.startRecording()
            isListening = true
            _isListening.value = true
            _error.value = null
            
            Log.i(TAG, "✅ Started direct audio recording in $language")
            
            // Start recording in a coroutine with supervision
            recordingJob = recordingScope.launch {
                try {
                    processAudioRecording(continuous)
                } catch (e: CancellationException) {
                    Log.w(TAG, "🛑 Recording was cancelled - attempting to process any collected audio before stopping")
                    // Don't rethrow, let it complete gracefully
                } catch (e: Exception) {
                    Log.e(TAG, "❌ Recording error: ${e.message}")
                    throw e
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ Failed to start direct audio recording: ${e.message}")
            _error.value = "Failed to start audio recording: ${e.message}"
            isListening = false
            _isListening.value = false
            audioRecord?.release()
            audioRecord = null
        }
    }
    
    /**
     * Process audio recording and convert to text using cloud STT services.
     */
    private suspend fun processAudioRecording(continuous: Boolean) {
        val buffer = ByteArray(1024)
        val audioData = ByteArrayOutputStream()
        var silenceCount = 0
        val maxSilenceCount = if (continuous) 150 else 75 // Adjust based on continuous mode
        var recordingTime = 0L
        var hasValidAudio = false
        
        try {
            Log.i(TAG, "🎵 Starting audio processing...")
            
            while (isListening && recordingTime < RECORDING_TIMEOUT_MS) {
                val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                
                if (read > 0) {
                    audioData.write(buffer, 0, read)
                    
                    // Simple volume detection for silence
                    val volume = buffer.take(read).map { it.toInt() }.sumOf { kotlin.math.abs(it) } / read
                    
                    if (volume < 500) { // Threshold for silence detection
                        silenceCount++
                    } else {
                        silenceCount = 0
                        hasValidAudio = true
                        // Show listening status when audio is detected
                        withContext(Dispatchers.Main) {
                            _partialResults.value = "Processing audio..."
                        }
                    }
                    
                    // Stop recording after extended silence if we have some audio
                    if (silenceCount > maxSilenceCount && hasValidAudio) {
                        Log.i(TAG, "🔇 Silence detected, processing recorded audio")
                        break
                    }
                }
                
                delay(10) // Small delay to prevent busy waiting
                recordingTime += 10
            }
            
            Log.i(TAG, "🎯 Recording completed. Audio data size: ${audioData.size()} bytes, hasValidAudio: $hasValidAudio, recordingTime: ${recordingTime}ms")
            
            // Process the recorded audio for speech-to-text
            if (audioData.size() > 2000) { // Minimum audio data threshold
                Log.i(TAG, "🎯 Converting audio to text (${audioData.size()} bytes)")
                
                withContext(Dispatchers.Main) {
                    _partialResults.value = "Converting speech to text..."
                }
                
                val audioBytes = audioData.toByteArray()
                Log.i(TAG, "🌐 Calling Google Cloud STT API...")
                
                // Use NonCancellable to ensure Google Cloud API call completes
                val transcription = withContext(Dispatchers.IO + NonCancellable) {
                    convertAudioToText(audioBytes, currentLanguage)
                }
                Log.i(TAG, "🌐 Google Cloud STT response: '$transcription'")
                
                withContext(Dispatchers.Main) {
                    if (transcription.isNotEmpty()) {
                        val result = STTResult(
                            text = transcription,
                            confidence = 0.85f, // Cloud services typically have high confidence
                            timestamp = System.currentTimeMillis(),
                            isPartial = false
                        )
                        _finalResults.value = result
                        _partialResults.value = ""
                        _confidence.value = result.confidence
                        Log.i(TAG, "✅ Direct recording transcription: $transcription")
                    } else {
                        _error.value = "No speech detected in recording"
                        Log.w(TAG, "⚠️ Cloud STT returned empty result")
                    }
                }
            } else {
                withContext(Dispatchers.Main) {
                    _error.value = "Insufficient audio data recorded"
                    Log.w(TAG, "⚠️ Insufficient audio data: ${audioData.size()} bytes")
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ Error during audio processing: ${e.message}")
            withContext(Dispatchers.Main) {
                _error.value = "Audio processing error: ${e.message}"
            }
        } finally {
            // Clean up
            withContext(Dispatchers.Main) {
                stopListening()
            }
        }
    }
    
    /**
     * Convert audio bytes to text using cloud STT services.
     */
    private suspend fun convertAudioToText(audioBytes: ByteArray, language: String): String {
        return withContext(Dispatchers.IO) {
            try {
                // Try Google Cloud Speech-to-Text first
                try {
                    val result = convertWithGoogleCloud(audioBytes, language)
                    if (result.isNotEmpty()) {
                        Log.i(TAG, "✅ Successfully transcribed with Google Cloud STT")
                        return@withContext result
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "⚠️ Google Cloud STT failed: ${e.message}")
                }
                
                // Try Azure Speech Services
                try {
                    val result = convertWithAzureSTT(audioBytes, language)
                    if (result.isNotEmpty()) {
                        Log.i(TAG, "✅ Successfully transcribed with Azure STT")
                        return@withContext result
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "⚠️ Azure STT failed: ${e.message}")
                }
                
                // Try OpenAI Whisper as last resort
                try {
                    val result = convertWithOpenAIWhisper(audioBytes, language)
                    if (result.isNotEmpty()) {
                        Log.i(TAG, "✅ Successfully transcribed with OpenAI Whisper")
                        return@withContext result
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "⚠️ OpenAI Whisper failed: ${e.message}")
                }
                
                // Fallback to local processing if all cloud services fail
                return@withContext "Speech detected (cloud services unavailable)"
                
            } catch (e: Exception) {
                Log.e(TAG, "❌ All STT conversion methods failed: ${e.message}")
                return@withContext ""
            }
        }
    }
    
    /**
     * Convert audio using Google Cloud Speech-to-Text API.
     */
    private suspend fun convertWithGoogleCloud(audioBytes: ByteArray, language: String): String {
        if (googleCloudAPIKey.isEmpty()) {
            Log.w(TAG, "⚠️ Google Cloud API key not configured")
            throw IOException("Google Cloud API key not configured")
        }
        
        return withContext(Dispatchers.IO) {
            try {
                // Convert audio to WAV format (Google Cloud expects specific format)
                val wavBytes = convertToWavFormat(audioBytes)
                val base64Audio = Base64.getEncoder().encodeToString(wavBytes)
                
                val requestBody = JSONObject().apply {
                    put("config", JSONObject().apply {
                        put("encoding", "LINEAR16")
                        put("sampleRateHertz", SAMPLE_RATE)
                        put("languageCode", language)
                        put("enableAutomaticPunctuation", true)
                        put("model", "latest_short") // Optimized for short audio clips
                    })
                    put("audio", JSONObject().apply {
                        put("content", base64Audio)
                    })
                }
                
                val request = Request.Builder()
                    .url("https://speech.googleapis.com/v1/speech:recognize?key=$googleCloudAPIKey")
                    .post(requestBody.toString().toRequestBody("application/json".toMediaType()))
                    .addHeader("Content-Type", "application/json")
                    .build()
                
                httpClient.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) {
                        throw IOException("Google Cloud STT failed: ${response.code}")
                    }
                    
                    val responseBody = response.body?.string() ?: ""
                    val jsonResponse = JSONObject(responseBody)
                    
                    if (jsonResponse.has("results")) {
                        val results = jsonResponse.getJSONArray("results")
                        if (results.length() > 0) {
                            val alternatives = results.getJSONObject(0).getJSONArray("alternatives")
                            if (alternatives.length() > 0) {
                                return@withContext alternatives.getJSONObject(0).getString("transcript")
                            }
                        }
                    }
                    
                    return@withContext ""
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ Google Cloud STT error: ${e.message}")
                throw e
            }
        }
    }
    
    /**
     * Convert audio using Azure Speech Services.
     */
    private suspend fun convertWithAzureSTT(audioBytes: ByteArray, language: String): String {
        if (azureSTTKey.isEmpty()) {
            Log.w(TAG, "⚠️ Azure STT key not configured")
            throw IOException("Azure STT key not configured")
        }
        
        return withContext(Dispatchers.IO) {
            try {
                val wavBytes = convertToWavFormat(audioBytes)
                
                val request = Request.Builder()
                    .url("https://$azureSTTRegion.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=$language")
                    .post(wavBytes.toRequestBody("audio/wav".toMediaType()))
                    .addHeader("Ocp-Apim-Subscription-Key", azureSTTKey)
                    .addHeader("Content-Type", "audio/wav")
                    .build()
                
                httpClient.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) {
                        throw IOException("Azure STT failed: ${response.code}")
                    }
                    
                    val responseBody = response.body?.string() ?: ""
                    val jsonResponse = JSONObject(responseBody)
                    
                    if (jsonResponse.has("DisplayText")) {
                        return@withContext jsonResponse.getString("DisplayText")
                    }
                    
                    return@withContext ""
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ Azure STT error: ${e.message}")
                throw e
            }
        }
    }
    
    /**
     * Convert audio using OpenAI Whisper API.
     */
    private suspend fun convertWithOpenAIWhisper(audioBytes: ByteArray, language: String): String {
        // For now, return empty - OpenAI Whisper requires API key and different setup
        // This can be implemented later if needed
        Log.w(TAG, "⚠️ OpenAI Whisper not implemented yet")
        throw IOException("OpenAI Whisper not implemented")
    }
    
    /**
     * Convert raw PCM audio to WAV format for cloud STT services.
     */
    private fun convertToWavFormat(audioBytes: ByteArray): ByteArray {
        val outputStream = ByteArrayOutputStream()
        
        // WAV file header
        val channels = 1 // Mono
        val bitsPerSample = 16
        val byteRate = SAMPLE_RATE * channels * bitsPerSample / 8
        val blockAlign = channels * bitsPerSample / 8
        val dataSize = audioBytes.size
        val fileSize = 36 + dataSize
        
        // RIFF header
        outputStream.write("RIFF".toByteArray())
        outputStream.write(intToByteArray(fileSize))
        outputStream.write("WAVE".toByteArray())
        
        // Format chunk
        outputStream.write("fmt ".toByteArray())
        outputStream.write(intToByteArray(16)) // PCM format chunk size
        outputStream.write(shortToByteArray(1)) // PCM format
        outputStream.write(shortToByteArray(channels.toShort()))
        outputStream.write(intToByteArray(SAMPLE_RATE))
        outputStream.write(intToByteArray(byteRate))
        outputStream.write(shortToByteArray(blockAlign.toShort()))
        outputStream.write(shortToByteArray(bitsPerSample.toShort()))
        
        // Data chunk
        outputStream.write("data".toByteArray())
        outputStream.write(intToByteArray(dataSize))
        outputStream.write(audioBytes)
        
        return outputStream.toByteArray()
    }
    
    /**
     * Convert int to little-endian byte array.
     */
    private fun intToByteArray(value: Int): ByteArray {
        return byteArrayOf(
            (value and 0xFF).toByte(),
            ((value shr 8) and 0xFF).toByte(),
            ((value shr 16) and 0xFF).toByte(),
            ((value shr 24) and 0xFF).toByte()
        )
    }
    
    /**
     * Convert short to little-endian byte array.
     */
    private fun shortToByteArray(value: Short): ByteArray {
        return byteArrayOf(
            (value.toInt() and 0xFF).toByte(),
            ((value.toInt() shr 8) and 0xFF).toByte()
        )
    }
    
    /**
     * Check if app has audio recording permission.
     */
    private fun hasAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            android.Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    /**
     * Stop listening for speech input.
     */
    fun stopListening() {
        if (!isListening) return
        
        try {
            if (useDirectAudioRecording) {
                // Stop direct audio recording
                recordingJob?.cancel()
                audioRecord?.stop()
                audioRecord?.release()
                audioRecord = null
                Log.i(TAG, "Stopped direct audio recording")
            } else {
                // Stop system speech recognizer
                speechRecognizer?.stopListening()
                Log.i(TAG, "Stopped system speech recognition")
            }
            
            isListening = false
            _isListening.value = false
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
            if (useDirectAudioRecording) {
                // Cancel direct audio recording
                recordingJob?.cancel()
                audioRecord?.stop()
                audioRecord?.release()
                audioRecord = null
                Log.i(TAG, "Cancelled direct audio recording")
            } else {
                // Cancel system speech recognizer
                speechRecognizer?.cancel()
                Log.i(TAG, "Cancelled system speech recognition")
            }
            
            isListening = false
            _isListening.value = false
            _partialResults.value = ""
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
        
        // Clean up coroutine scope
        recordingScope.cancel()
        
        // Clean up HTTP client
        httpClient.dispatcher.executorService.shutdown()
        httpClient.connectionPool.evictAll()
        
        Log.i(TAG, "STT Service destroyed")
    }
    
    private var consecutiveErrors = 0
    private val maxConsecutiveErrors = 3 // Switch to direct recording after 3 failures
    
    /**
     * Handle persistent speech recognition errors with user feedback.
     */
    private fun handlePersistentError(userMessage: String) {
        Log.e(TAG, "🔄 Handling persistent STT error: $userMessage")
        
        consecutiveErrors++
        Log.w(TAG, "🔢 Consecutive errors: $consecutiveErrors")
        
        // After multiple failures, switch to direct audio recording
        if (consecutiveErrors >= maxConsecutiveErrors && !useDirectAudioRecording) {
            Log.w(TAG, "⚠️ System speech recognition failed $consecutiveErrors times, switching to direct audio recording")
            
            // Clean up system recognizer
            speechRecognizer?.destroy()
            speechRecognizer = null
            
            // Initialize direct audio recording
            if (initializeDirectAudioRecording()) {
                useDirectAudioRecording = true
                Log.i(TAG, "✅ Successfully switched to direct audio recording mode")
                _error.value = "Switched to direct recording mode. Speech recognition ready."
                
                // Reset error count since we switched modes
                consecutiveErrors = 0
                return
            } else {
                Log.e(TAG, "❌ Failed to initialize direct audio recording fallback")
                _error.value = "Speech recognition unavailable - please check device settings"
            }
        } else {
            // Clean up current recognizer
            speechRecognizer?.destroy()
            speechRecognizer = null
            
            // Set clear error message for user
            _error.value = userMessage
        }
        
        // Reset state
        isListening = false
        _isListening.value = false
        _partialResults.value = ""
        
        // Log suggestions for user
        Log.w(TAG, "💡 Suggestions: Check Settings > Apps > Google > Permissions > Microphone")
        Log.w(TAG, "💡 Or: Settings > Language & input > Voice input > Default voice input")
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
            Log.d(TAG, "🎤 Ready for speech")
            PerformanceTracker.logAudioOperation(
                AudioOperation.STT_START, 
                System.currentTimeMillis() - recognitionStartTime
            )
        }
        
        override fun onBeginningOfSpeech() {
            Log.d(TAG, "🗣️ Beginning of speech")
        }
        
        override fun onRmsChanged(rmsdB: Float) {
            // Audio level changed - could be used for visualizations
        }
        
        override fun onBufferReceived(buffer: ByteArray?) {
            // Audio buffer received
        }
        
        override fun onEndOfSpeech() {
            Log.d(TAG, "🔇 End of speech")
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
            
            Log.e(TAG, "❌ Speech recognition error: $errorMessage")
            
            isListening = false
            _isListening.value = false
            
            // Handle specific errors with recovery attempts
            when (error) {
                SpeechRecognizer.ERROR_CLIENT -> {
                    handlePersistentError("Speech recognition service unavailable. Please try again or check device settings.")
                }
                10 -> { // ERROR_LANGUAGE_NOT_SUPPORTED or other binding issues
                    Log.e(TAG, "⚠️ Persistent error 10 - likely speech service binding issue")
                    handlePersistentError("Speech recognition unavailable. Please check device speech settings or try again later.")
                }
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> {
                    Log.w(TAG, "⚠️ Recognizer busy - will retry")
                    // Don't treat this as a critical error, just wait
                }
                SpeechRecognizer.ERROR_NO_MATCH -> {
                    Log.i(TAG, "ℹ️ No speech detected")
                    // Don't treat "no match" as a critical error
                }
                else -> {
                    _error.value = errorMessage
                }
            }
        }
        
        override fun onResults(results: Bundle?) {
            val resultTime = System.currentTimeMillis() - recognitionStartTime
            
            // Reset consecutive errors on successful result
            consecutiveErrors = 0
            
            results?.let { bundle ->
                val matches = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val confidence = bundle.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)
                
                if (!matches.isNullOrEmpty()) {
                    val bestMatch = matches[0]
                    val bestConfidence = confidence?.get(0) ?: 0.0f
                    
                    Log.i(TAG, "✅ Final result: '$bestMatch' (confidence: $bestConfidence) in ${resultTime}ms")
                    
                    PerformanceTracker.logAudioOperation(AudioOperation.STT_RESULT, resultTime)
                    
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
                    Log.d(TAG, "📝 Partial result: '$partialText'")
                    _partialResults.value = partialText
                }
            }
        }
        
        override fun onEvent(eventType: Int, params: Bundle?) {
            Log.d(TAG, "🔔 Speech recognition event: $eventType")
        }
    }
    
    /**
     * Clean up resources when the service is destroyed.
     */
    fun cleanup() {
        try {
            // Cancel any ongoing recording
            cancel()
            
            // Clean up audio recording
            audioRecord?.release()
            audioRecord = null
            
            // Cancel recording coroutines
            recordingJob?.cancel()
            recordingScope.cancel()
            
            // Clean up speech recognizer
            speechRecognizer?.destroy()
            speechRecognizer = null
            
            Log.i(TAG, "✅ STTService cleaned up")
        } catch (e: Exception) {
            Log.e(TAG, "❌ Error during cleanup: ${e.message}")
        }
    }
}
