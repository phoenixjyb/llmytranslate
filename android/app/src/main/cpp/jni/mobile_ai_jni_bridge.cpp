/**
 * Mobile AI JNI Bridge
 * Smart backend selection: TensorFlow Lite GPU (primary) -> ONNX Runtime Mobile (fallback)
 * Optimized for Samsung S24 Ultra with Adreno 750 GPU
 */

#include <jni.h>
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <string>
#include <memory>

#ifdef TFLITE_GPU_AVAILABLE
#include "mobile_ai/tflite_gpu_service.h"
#endif

#ifdef ONNX_MOBILE_AVAILABLE
#include "mobile_ai/onnx_mobile_service.h"
#endif

#define LOG_TAG "MobileAI-JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

using namespace mobile_ai;

// Global service instances
#ifdef TFLITE_GPU_AVAILABLE
static std::unique_ptr<TFLiteGPUService> tflite_service;
#endif

#ifdef ONNX_MOBILE_AVAILABLE
static std::unique_ptr<ONNXMobileService> onnx_service;
#endif

static bool is_initialized = false;
static std::string active_backend = "none";

extern "C" {

/**
 * Initialize the mobile AI service with optimal backend selection
 */
JNIEXPORT jboolean JNICALL
Java_com_llmytranslate_android_services_MobileAIService_initializeNative(
    JNIEnv *env, jobject thiz, jstring model_path) {
    
    const char* path_chars = env->GetStringUTFChars(model_path, nullptr);
    std::string path(path_chars);
    env->ReleaseStringUTFChars(model_path, path_chars);
    
    LOGI("Initializing Mobile AI with model: %s", path.c_str());
    
    bool success = false;
    
#ifdef TFLITE_GPU_AVAILABLE
    // Try TensorFlow Lite GPU first (best performance)
    LOGI("Attempting TensorFlow Lite %s initialization...", REAL_TFLITE_AVAILABLE ? "(native)" : "(mock)");
    tflite_service = std::make_unique<TFLiteGPUService>();
    
    if (tflite_service->initialize(path)) {
        active_backend = "tflite_gpu";
        success = true;
        float performance = tflite_service->getPerformanceScore();
    LOGI("✅ TensorFlow Lite initialized successfully (score %.0f%%)", performance * 100);
    } else {
        LOGI("❌ TensorFlow Lite GPU initialization failed, trying fallback...");
        tflite_service.reset();
    }
#endif

#ifdef ONNX_MOBILE_AVAILABLE
    // Fallback to ONNX Runtime Mobile if TensorFlow Lite failed
    if (!success) {
        LOGI("Attempting ONNX Runtime Mobile initialization...");
        onnx_service = std::make_unique<ONNXMobileService>();
        
        if (onnx_service->initialize(path) && onnx_service->isNNAPIAvailable()) {
            active_backend = "onnx_mobile";
            success = true;
            LOGI("✅ ONNX Runtime Mobile initialized successfully (50%% QNN performance)");
        } else {
            LOGE("❌ ONNX Runtime Mobile initialization failed");
            onnx_service.reset();
        }
    }
#endif

    if (success) {
        is_initialized = true;
        LOGI("🚀 Mobile AI ready with backend: %s", active_backend.c_str());
    } else {
        LOGE("💥 All mobile AI backends failed to initialize");
    }
    
    return success;
}

/**
 * Initialize with Android Asset Manager for bundled models
 */
JNIEXPORT jboolean JNICALL
Java_com_llmytranslate_android_services_MobileAIService_initializeWithAssetsNative(
    JNIEnv *env, jobject thiz, jobject asset_manager) {
    
    LOGI("Initializing Mobile AI with Android assets...");
    
    // Get native asset manager
    AAssetManager* native_asset_manager = AAssetManager_fromJava(env, asset_manager);
    if (!native_asset_manager) {
        LOGE("Failed to get native asset manager");
        return false;
    }
    
    bool success = false;
    
#ifdef TFLITE_GPU_AVAILABLE
    // Try TensorFlow Lite GPU first with assets
    LOGI("Attempting TensorFlow Lite %s initialization with assets...", REAL_TFLITE_AVAILABLE ? "(native)" : "(mock)");
    tflite_service = std::make_unique<TFLiteGPUService>();
    
    if (tflite_service->initializeWithAssets(native_asset_manager)) {
        active_backend = "tflite_gpu";
        success = true;
        float performance = tflite_service->getPerformanceScore();
        bool gpu_available = tflite_service->isGPUAvailable();
        LOGI("✅ TensorFlow Lite %s initialized (%.0f%% performance)", 
             gpu_available ? "GPU" : "CPU", performance * 100);
    } else {
        LOGI("❌ TensorFlow Lite GPU asset initialization failed");
        tflite_service.reset();
    }
#endif

#ifdef ONNX_MOBILE_AVAILABLE
    // Fallback to ONNX Runtime Mobile if TensorFlow Lite failed
    if (!success) {
        LOGI("ONNX Runtime Mobile asset initialization not yet implemented");
        // TODO: Implement initializeWithAssets for ONNX service
    }
#endif

    if (success) {
        is_initialized = true;
        LOGI("🚀 Mobile AI ready with backend: %s", active_backend.c_str());
    } else {
        LOGE("💥 All mobile AI backends failed to initialize with assets");
    }
    
    return success;
}

/**
 * Process text inference using the active backend
 */
JNIEXPORT jstring JNICALL
Java_com_llmytranslate_android_services_MobileAIService_processInferenceNative(
    JNIEnv *env, jobject thiz, jstring input_text) {
    
    if (!is_initialized) {
        LOGE("Mobile AI service not initialized");
        return env->NewStringUTF("Error: Service not initialized");
    }
    
    const char* input_chars = env->GetStringUTFChars(input_text, nullptr);
    std::string input(input_chars);
    env->ReleaseStringUTFChars(input_text, input_chars);
    
    std::string result;
    
#ifdef TFLITE_GPU_AVAILABLE
    if (active_backend == "tflite_gpu" && tflite_service) {
        result = tflite_service->processInference(input);
    }
#endif

#ifdef ONNX_MOBILE_AVAILABLE
    if (active_backend == "onnx_mobile" && onnx_service) {
        result = onnx_service->processInference(input);
    }
#endif

    if (result.empty()) {
        result = "Error: No active backend available";
        LOGE("No active backend for inference");
    }
    
    return env->NewStringUTF(result.c_str());
}

/**
 * Get current backend information
 */
JNIEXPORT jstring JNICALL
Java_com_llmytranslate_android_services_MobileAIService_getBackendInfoNative(
    JNIEnv *env, jobject thiz) {
    
    if (!is_initialized) {
        return env->NewStringUTF("Backend: Not initialized");
    }
    
    std::string info = "Backend: " + active_backend;
#if REAL_TFLITE_AVAILABLE
    info += " [native]";
#endif
    
#ifdef TFLITE_GPU_AVAILABLE
    if (active_backend == "tflite_gpu" && tflite_service) {
        float score = tflite_service->getPerformanceScore();
        info += " (Performance: " + std::to_string((int)(score * 100)) + "% of QNN)";
    }
#endif

#ifdef ONNX_MOBILE_AVAILABLE
    if (active_backend == "onnx_mobile" && onnx_service) {
        float score = onnx_service->getPerformanceScore();
        info += " (Performance: " + std::to_string((int)(score * 100)) + "% of QNN)";
    }
#endif

    return env->NewStringUTF(info.c_str());
}

/**
 * Cleanup native resources
 */
JNIEXPORT void JNICALL
Java_com_llmytranslate_android_services_MobileAIService_cleanupNative(
    JNIEnv *env, jobject thiz) {
    
    LOGI("Cleaning up Mobile AI native resources");
    
#ifdef TFLITE_GPU_AVAILABLE
    if (tflite_service) {
        tflite_service->cleanup();
        tflite_service.reset();
    }
#endif

#ifdef ONNX_MOBILE_AVAILABLE
    if (onnx_service) {
        onnx_service->cleanup();
        onnx_service.reset();
    }
#endif

    is_initialized = false;
    active_backend = "none";
    
    LOGI("Mobile AI cleanup complete");
}

} // extern "C"
