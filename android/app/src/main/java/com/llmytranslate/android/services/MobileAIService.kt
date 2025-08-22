package com.llmytranslate.android.services

import android.content.Context
import android.util.Log
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Mobile AI Service using TensorFlow Lite GPU acceleration
 * Provides high-performance mobile AI inference with automatic backend selection
 * Primary: TensorFlow Lite GPU (70% QNN performance)
 * Fallback: ONNX Runtime Mobile (50% QNN performance)
 */
@Singleton
class MobileAIService @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        private const val TAG = "MobileAI"
        
        // Load native library
        init {
            try {
                System.loadLibrary("mobile_ai_native")
                Log.i(TAG, "✅ Mobile AI native library loaded successfully")
            } catch (e: UnsatisfiedLinkError) {
                Log.e(TAG, "❌ Failed to load native library: ${e.message}")
            }
        }
    }

    private var isInitialized = false
    
    /**
     * Initialize the mobile AI service with a model
     * @param modelPath Path to the model file (supports .tflite and .onnx)
     * @return true if initialization successful
     */
    suspend fun initialize(modelPath: String): Boolean = withContext(Dispatchers.IO) {
        Log.i(TAG, "Initializing Mobile AI with model: $modelPath")
        
        try {
            isInitialized = initializeNative(modelPath)
            
            if (isInitialized) {
                val backendInfo = getBackendInfoNative()
                Log.i(TAG, "🚀 Mobile AI initialized successfully - $backendInfo")
            } else {
                Log.e(TAG, "❌ Mobile AI initialization failed with model: $modelPath")
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Exception during initialization: ${e.message}")
            isInitialized = false
        }
        
        isInitialized
    }
    
    /**
     * Initialize with bundled models from Android assets
     * @return true if initialization successful
     */
    suspend fun initializeWithAssets(): Boolean = withContext(Dispatchers.IO) {
        Log.i(TAG, "Initializing Mobile AI with bundled assets...")
        
        try {
            isInitialized = initializeWithAssetsNative(context.assets)
            
            if (isInitialized) {
                val backendInfo = getBackendInfoNative()
                Log.i(TAG, "🚀 Mobile AI initialized successfully with assets - $backendInfo")
            } else {
                Log.e(TAG, "❌ Mobile AI initialization failed")
            }
            
            isInitialized
        } catch (e: Exception) {
            Log.e(TAG, "Exception during initialization: ${e.message}")
            false
        }
    }
    
    /**
     * Process text inference using the mobile AI backend
     * @param inputText Input text for processing
     * @return Generated response text
     */
    suspend fun processInference(inputText: String): String = withContext(Dispatchers.IO) {
        if (!isInitialized) {
            Log.w(TAG, "Mobile AI service not initialized")
            return@withContext "Error: Mobile AI service not initialized"
        }
        
        if (inputText.isBlank()) {
            return@withContext "Error: Input text is empty"
        }
        
        Log.d(TAG, "Processing inference for: ${inputText.take(50)}...")
        
        try {
            val startTime = System.currentTimeMillis()
        val result = try {
                // Guard against native stalls
                withTimeout(4_000) {
            val r = processInferenceNative(inputText)
            Log.d(TAG, "Native returned: ${r.take(60)}${if (r.length > 60) "..." else ""}")
            r
                }
            } catch (te: TimeoutCancellationException) {
                Log.e(TAG, "Inference timeout after 4000ms")
                "Error: Inference timed out after 4000ms"
            }
            val duration = System.currentTimeMillis() - startTime
            
            Log.i(TAG, "✅ Inference completed in ${duration}ms")
            result
        } catch (e: Exception) {
            Log.e(TAG, "Inference failed: ${e.message}")
            "Error: Inference failed - ${e.message}"
        }
    }
    
    /**
     * Get information about the current AI backend
     * @return Backend information string
     */
    suspend fun getBackendInfo(): String = withContext(Dispatchers.IO) {
        if (!isInitialized) {
            return@withContext "Backend: Not initialized"
        }
        
        try {
            getBackendInfoNative()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get backend info: ${e.message}")
            "Backend: Error getting info"
        }
    }
    
    /**
     * Check if the service is ready for inference
     */
    fun isReady(): Boolean = isInitialized
    
    /**
     * Cleanup native resources
     */
    fun cleanup() {
        if (isInitialized) {
            Log.i(TAG, "Cleaning up Mobile AI service")
            try {
                cleanupNative()
                isInitialized = false
                Log.i(TAG, "✅ Mobile AI cleanup complete")
            } catch (e: Exception) {
                Log.e(TAG, "Error during cleanup: ${e.message}")
            }
        }
    }
    
    // Native method declarations
    private external fun initializeNative(modelPath: String): Boolean
    private external fun initializeWithAssetsNative(assetManager: android.content.res.AssetManager): Boolean
    private external fun processInferenceNative(inputText: String): String
    private external fun getBackendInfoNative(): String
    private external fun cleanupNative()
}
