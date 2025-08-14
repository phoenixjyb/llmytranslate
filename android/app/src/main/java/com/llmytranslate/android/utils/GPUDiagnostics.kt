package com.llmytranslate.android.utils

import android.content.Context
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/**
 * GPU diagnostics and optimization utilities for Android devices.
 * Specifically optimized for Samsung S24 Ultra with Adreno GPU.
 */
object GPUDiagnostics {
    private const val TAG = "GPUDiagnostics"
    
    /**
     * Check GPU capabilities and availability for ML acceleration.
     */
    suspend fun checkGPUCapabilities(context: Context): GPUInfo = withContext(Dispatchers.IO) {
        val gpuInfo = GPUInfo()
        
        try {
            // Check OpenGL ES capabilities
            val glInfo = getOpenGLInfo()
            gpuInfo.openGLVersion = glInfo.version
            gpuInfo.gpuRenderer = glInfo.renderer
            gpuInfo.gpuVendor = glInfo.vendor
            
            // Check for Vulkan support (better for ML)
            gpuInfo.vulkanSupported = checkVulkanSupport()
            
            // Check for GPU compute capabilities
            gpuInfo.openCLSupported = checkOpenCLSupport()
            
            // Check device-specific optimizations
            gpuInfo.isAdrenoGPU = glInfo.renderer.contains("Adreno", ignoreCase = true)
            gpuInfo.isMaliGPU = glInfo.renderer.contains("Mali", ignoreCase = true)
            
            // Samsung S24 Ultra specific checks
            if (gpuInfo.isAdrenoGPU) {
                gpuInfo.adrenoVersion = extractAdrenoVersion(glInfo.renderer)
                gpuInfo.supportsFloat16 = checkFloat16Support()
                gpuInfo.supportsInt8 = checkInt8Support()
            }
            
            Log.i(TAG, "GPU Info: $gpuInfo")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error checking GPU capabilities: ${e.message}")
            gpuInfo.error = e.message
        }
        
        gpuInfo
    }
    
    /**
     * Generate Ollama GPU configuration for optimal performance.
     */
    fun generateOllamaGPUConfig(gpuInfo: GPUInfo): OllamaGPUConfig {
        val config = OllamaGPUConfig()
        
        if (gpuInfo.isAdrenoGPU && gpuInfo.adrenoVersion >= 740) {
            // Samsung S24 Ultra has Adreno 750, which is excellent for ML
            config.enableGPU = true
            config.gpuLayers = -1 // Use all layers on GPU
            config.enableFloat16 = gpuInfo.supportsFloat16
            config.enableVulkan = gpuInfo.vulkanSupported
            config.recommendedMemory = "4GB" // S24 Ultra has plenty of RAM
            config.optimizationLevel = "high"
            
            // Adreno-specific optimizations
            config.adrenoOptimizations = mapOf(
                "ADRENO_GPU_MEMORY_OPTIMIZATION" to "true",
                "ADRENO_SHADER_OPTIMIZATION" to "true",
                "VULKAN_MEMORY_BUDGET" to "3072", // 3GB for GPU
                "GPU_THREAD_COUNT" to "8"
            )
            
        } else if (gpuInfo.isAdrenoGPU) {
            // Older Adreno GPUs
            config.enableGPU = true
            config.gpuLayers = 20 // Partial GPU acceleration
            config.enableFloat16 = false // May not be stable
            config.optimizationLevel = "medium"
            
        } else {
            // Fallback for other GPUs
            config.enableGPU = false
            config.reason = "GPU not recognized or insufficient capabilities"
        }
        
        return config
    }
    
    /**
     * Generate environment variables for Ollama GPU acceleration.
     */
    fun generateOllamaEnvVars(config: OllamaGPUConfig): Map<String, String> {
        val envVars = mutableMapOf<String, String>()
        
        if (config.enableGPU) {
            envVars["OLLAMA_GPU"] = "1"
            envVars["OLLAMA_GPU_LAYERS"] = config.gpuLayers.toString()
            
            if (config.enableVulkan) {
                envVars["OLLAMA_VULKAN"] = "1"
                envVars["VK_INSTANCE_LAYERS"] = "VK_LAYER_KHRONOS_validation"
            }
            
            if (config.enableFloat16) {
                envVars["OLLAMA_FLOAT16"] = "1"
            }
            
            // Memory optimizations
            envVars["OLLAMA_GPU_MEMORY"] = config.recommendedMemory
            envVars["OLLAMA_MAX_LOADED_MODELS"] = "1" // Mobile optimization
            
            // Adreno-specific environment variables
            config.adrenoOptimizations?.forEach { (key, value) ->
                envVars[key] = value
            }
        } else {
            envVars["OLLAMA_GPU"] = "0"
            envVars["OLLAMA_CPU_THREADS"] = "4" // Optimize CPU fallback
        }
        
        return envVars
    }
    
    private fun getOpenGLInfo(): OpenGLInfo {
        // This would typically require an OpenGL context
        // For now, return system properties
        return OpenGLInfo(
            version = android.os.Build.VERSION.RELEASE,
            renderer = getSystemProperty("ro.hardware.gpu", "Unknown GPU"),
            vendor = getSystemProperty("ro.product.manufacturer", "Unknown")
        )
    }
    
    private fun getSystemProperty(key: String, default: String): String {
        return try {
            val process = Runtime.getRuntime().exec("getprop $key")
            val result = process.inputStream.bufferedReader().readText().trim()
            if (result.isNotEmpty()) result else default
        } catch (e: Exception) {
            default
        }
    }
    
    private fun checkVulkanSupport(): Boolean {
        // Check if Vulkan is available (API 24+)
        return android.os.Build.VERSION.SDK_INT >= 24
    }
    
    private fun checkOpenCLSupport(): Boolean {
        // Basic check for OpenCL availability
        return try {
            val process = Runtime.getRuntime().exec("ls /system/vendor/lib*/libOpenCL.so")
            process.waitFor() == 0
        } catch (e: Exception) {
            false
        }
    }
    
    private fun extractAdrenoVersion(renderer: String): Int {
        return try {
            val regex = Regex("Adreno \\(TM\\) (\\d+)")
            regex.find(renderer)?.groupValues?.get(1)?.toInt() ?: 0
        } catch (e: Exception) {
            0
        }
    }
    
    private fun checkFloat16Support(): Boolean {
        return android.os.Build.VERSION.SDK_INT >= 28
    }
    
    private fun checkInt8Support(): Boolean {
        return android.os.Build.VERSION.SDK_INT >= 29
    }
    
    data class GPUInfo(
        var openGLVersion: String = "",
        var gpuRenderer: String = "",
        var gpuVendor: String = "",
        var vulkanSupported: Boolean = false,
        var openCLSupported: Boolean = false,
        var isAdrenoGPU: Boolean = false,
        var isMaliGPU: Boolean = false,
        var adrenoVersion: Int = 0,
        var supportsFloat16: Boolean = false,
        var supportsInt8: Boolean = false,
        var error: String? = null
    )
    
    data class OpenGLInfo(
        val version: String,
        val renderer: String,
        val vendor: String
    )
    
    data class OllamaGPUConfig(
        var enableGPU: Boolean = false,
        var gpuLayers: Int = 0,
        var enableFloat16: Boolean = false,
        var enableVulkan: Boolean = false,
        var recommendedMemory: String = "2GB",
        var optimizationLevel: String = "low",
        var adrenoOptimizations: Map<String, String>? = null,
        var reason: String = ""
    )
}
