# 🚀 QNN SDK Setup Guide
## Qualcomm Neural Network SDK Integration for Android

### **Objective**: Hardware-accelerated LLM inference on Samsung S24 Ultra (Snapdragon 8 Gen 3)
### **Target**: <1 second response time (vs current 3-8s Termux)

---

## 📋 **Phase 1: Environment Setup**

### **1.1 Prerequisites Check**
```bash
# Check current environment
echo "Current Android SDK: $(ls $ANDROID_HOME/platforms)"
echo "Current NDK: $(ls $ANDROID_HOME/ndk)"
echo "Current CMake: $(which cmake)"
```

### **1.2 Required Components**
```bash
# Install/Update components
# Android SDK Platform 34 (already have)
# Android NDK 25.2.9519653 (for QNN compatibility)
# CMake 3.22.1+ (for native builds)
```

### **1.3 QNN SDK Download**
```bash
# Qualcomm QNN SDK 2.24.0 (latest stable)
# Download from: https://developer.qualcomm.com/software/qualcomm-neural-processing-sdk
# License: Developer license required
# Size: ~2.5GB
```

---

## 🔧 **Phase 2: Project Structure**

### **2.1 Create QNN Module Structure**
```
android/app/src/main/
├── cpp/
│   ├── qnn/
│   │   ├── qnn_llm_service.cpp        # Main QNN inference service
│   │   ├── qnn_model_manager.cpp      # Model loading/management
│   │   ├── qnn_context_manager.cpp    # QNN context handling
│   │   └── qnn_utils.cpp              # Helper utilities
│   ├── jni/
│   │   └── qnn_jni_bridge.cpp         # JNI interface
│   └── CMakeLists.txt                 # Native build configuration
├── java/com/llmytranslate/android/
│   ├── services/
│   │   ├── QNNLLMService.kt           # Main QNN service
│   │   ├── QNNModelManager.kt         # Model management
│   │   └── QNNPerformanceMonitor.kt   # Performance tracking
│   └── jni/
│       └── QNNNativeBridge.kt         # JNI wrapper
```

### **2.2 Update build.gradle.kts**
```kotlin
android {
    // Enable native builds
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
    
    defaultConfig {
        // Add ABI filters for Snapdragon
        ndk {
            abiFilters += listOf("arm64-v8a")
        }
        
        // QNN specific cmake arguments
        externalNativeBuild {
            cmake {
                cppFlags += listOf("-std=c++17", "-frtti", "-fexceptions")
                arguments += listOf(
                    "-DANDROID_STL=c++_shared",
                    "-DQNN_ENABLE_LOGGING=ON"
                )
            }
        }
    }
}

dependencies {
    // ONNX Runtime with QNN EP
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.18.0")
    
    // QNN specific JNI
    implementation(files("libs/qnn-android.aar"))
}
```

---

## 📱 **Phase 3: QNN Service Implementation**

### **3.1 Core QNN Service**
```kotlin
// QNNLLMService.kt
@Singleton
class QNNLLMService @Inject constructor(
    private val performanceMonitor: QNNPerformanceMonitor
) {
    private external fun initializeQNN(): Boolean
    private external fun loadModel(modelPath: String): Long
    private external fun runInference(
        contextId: Long, 
        input: ByteArray
    ): ByteArray
    private external fun releaseModel(contextId: Long)
    
    suspend fun translate(
        text: String,
        targetLanguage: String
    ): Result<String> = withContext(Dispatchers.Default) {
        performanceMonitor.startMeasurement("qnn_inference")
        
        try {
            val tokenizedInput = tokenizeText(text)
            val result = runInference(activeModelContext, tokenizedInput)
            val translatedText = detokenizeOutput(result)
            
            performanceMonitor.endMeasurement("qnn_inference")
            Result.success(translatedText)
        } catch (e: Exception) {
            performanceMonitor.recordError("qnn_inference", e)
            Result.failure(e)
        }
    }
    
    companion object {
        init {
            System.loadLibrary("qnn_llm_native")
        }
    }
}
```

### **3.2 Model Manager**
```kotlin
// QNNModelManager.kt
@Singleton
class QNNModelManager @Inject constructor() {
    private val loadedModels = mutableMapOf<String, Long>()
    
    data class QNNModel(
        val name: String,
        val path: String,
        val targetLatency: Long, // milliseconds
        val memoryRequirement: Long, // bytes
        val supportedLanguages: Set<String>
    )
    
    private val availableModels = listOf(
        QNNModel(
            name = "gemma2-270m-qnn",
            path = "models/gemma2_270m_uint8.onnx",
            targetLatency = 200L, // <200ms
            memoryRequirement = 350L * 1024 * 1024, // 350MB
            supportedLanguages = setOf("en", "zh", "ja", "ko")
        ),
        QNNModel(
            name = "gemma2-2b-qnn", 
            path = "models/gemma2_2b_uint8.onnx",
            targetLatency = 800L, // <800ms
            memoryRequirement = 2L * 1024 * 1024 * 1024, // 2GB
            supportedLanguages = setOf("en", "zh", "ja", "ko", "es", "fr", "de")
        )
    )
    
    suspend fun selectOptimalModel(
        requirements: TranslationRequirements
    ): QNNModel = withContext(Dispatchers.Default) {
        availableModels
            .filter { it.supportedLanguages.contains(requirements.targetLanguage) }
            .filter { it.memoryRequirement <= getAvailableMemory() }
            .minByOrNull { 
                if (requirements.prioritizeSpeed) it.targetLatency 
                else it.memoryRequirement 
            } ?: availableModels.first()
    }
}
```

---

## 🔨 **Phase 4: Native Implementation**

### **4.1 CMakeLists.txt**
```cmake
cmake_minimum_required(VERSION 3.22.1)
project(qnn_llm_native)

# QNN SDK paths
set(QNN_SDK_ROOT "/path/to/qnn-sdk")
set(QNN_LIB_PATH "${QNN_SDK_ROOT}/lib/aarch64-android")
set(QNN_INCLUDE_PATH "${QNN_SDK_ROOT}/include")

# Include directories
include_directories(${QNN_INCLUDE_PATH})
include_directories(${QNN_INCLUDE_PATH}/QNN)

# Source files
file(GLOB_RECURSE QNN_SOURCES 
    "qnn/*.cpp"
    "jni/*.cpp"
)

# Create shared library
add_library(qnn_llm_native SHARED ${QNN_SOURCES})

# Link QNN libraries
target_link_libraries(qnn_llm_native
    ${QNN_LIB_PATH}/libQnnHtp.so           # HTP (NPU) backend
    ${QNN_LIB_PATH}/libQnnSystem.so        # System interface
    ${QNN_LIB_PATH}/libQnnCpuBackend.so    # CPU fallback
    log                                    # Android logging
    android                               # Android NDK
)

# Compiler flags
target_compile_options(qnn_llm_native PRIVATE
    -std=c++17
    -O3
    -ffast-math
    -DQNN_ENABLE_DEBUG_LOGGING
)
```

### **4.2 Core QNN Service (C++)**
```cpp
// qnn_llm_service.cpp
#include <jni.h>
#include <android/log.h>
#include "QNN/QnnInterface.h"
#include "QNN/HTP/QnnHtpDevice.h"

#define LOG_TAG "QNN_LLM_Service"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

class QNNLLMService {
private:
    QNN_INTERFACE_VER_TYPE qnnInterface;
    Qnn_ContextHandle_t context;
    Qnn_DeviceHandle_t device;
    bool initialized = false;
    
public:
    bool initialize() {
        LOGI("Initializing QNN LLM Service...");
        
        // Load QNN HTP backend
        if (QNN_SUCCESS != QnnInterface_getProviders(
            nullptr, 0, &qnnInterface)) {
            LOGI("Failed to get QNN providers");
            return false;
        }
        
        // Create HTP device for Snapdragon NPU
        QnnHtpDevice_Infrastructure_t deviceInfra = QNN_HTP_DEVICE_INFRASTRUCTURE_INIT;
        deviceInfra.deviceId = 0; // Primary NPU
        deviceInfra.powerMode = QNN_HTP_DEVICE_POWER_MODE_PERFORMANCE;
        
        if (QNN_SUCCESS != qnnInterface.deviceCreate(
            nullptr, &deviceInfra, &device)) {
            LOGI("Failed to create QNN device");
            return false;
        }
        
        // Create context
        if (QNN_SUCCESS != qnnInterface.contextCreate(
            device, nullptr, &context)) {
            LOGI("Failed to create QNN context");
            return false;
        }
        
        initialized = true;
        LOGI("QNN LLM Service initialized successfully");
        return true;
    }
    
    long loadModel(const std::string& modelPath) {
        if (!initialized) return -1;
        
        LOGI("Loading model: %s", modelPath.c_str());
        
        // Model loading implementation
        // This will load ONNX model with QNN execution provider
        
        return reinterpret_cast<long>(context);
    }
    
    std::vector<uint8_t> runInference(
        long contextId, 
        const std::vector<uint8_t>& input
    ) {
        LOGI("Running QNN inference...");
        
        auto start = std::chrono::high_resolution_clock::now();
        
        // QNN inference implementation
        std::vector<uint8_t> output;
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            end - start).count();
            
        LOGI("QNN inference completed in %ld ms", duration);
        
        return output;
    }
};

// JNI exports
extern "C" {
    static QNNLLMService* service = nullptr;
    
    JNIEXPORT jboolean JNICALL
    Java_com_llmytranslate_android_services_QNNLLMService_initializeQNN(
        JNIEnv* env, jobject thiz) {
        if (!service) {
            service = new QNNLLMService();
        }
        return service->initialize();
    }
    
    JNIEXPORT jlong JNICALL
    Java_com_llmytranslate_android_services_QNNLLMService_loadModel(
        JNIEnv* env, jobject thiz, jstring modelPath) {
        if (!service) return -1;
        
        const char* path = env->GetStringUTFChars(modelPath, nullptr);
        long result = service->loadModel(std::string(path));
        env->ReleaseStringUTFChars(modelPath, path);
        
        return result;
    }
    
    JNIEXPORT jbyteArray JNICALL
    Java_com_llmytranslate_android_services_QNNLLMService_runInference(
        JNIEnv* env, jobject thiz, jlong contextId, jbyteArray input) {
        // Implementation
        return env->NewByteArray(0);
    }
}
```

---

## 📊 **Phase 5: Performance Optimization**

### **5.1 Performance Monitor**
```kotlin
// QNNPerformanceMonitor.kt
@Singleton
class QNNPerformanceMonitor @Inject constructor() {
    private val measurements = mutableMapOf<String, MutableList<Long>>()
    
    data class PerformanceMetrics(
        val averageLatency: Long,
        val p95Latency: Long,
        val throughput: Double,
        val memoryUsage: Long,
        val batteryImpact: Double
    )
    
    fun startMeasurement(operation: String) {
        // Start timing
    }
    
    fun endMeasurement(operation: String) {
        // End timing and record
    }
    
    fun getMetrics(): PerformanceMetrics {
        // Calculate and return performance metrics
        return PerformanceMetrics(
            averageLatency = 500L, // Target: <1000ms
            p95Latency = 800L,
            throughput = 2.5, // requests per second
            memoryUsage = 1024L * 1024 * 1024, // 1GB
            batteryImpact = 3.2 // %/hour
        )
    }
}
```

---

## 🎯 **Phase 6: Integration & Testing**

### **6.1 Update MainActivity**
```kotlin
// Add QNN service to dependency injection
@HiltAndroidApp
class LLMyTranslateApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // QNN service will be automatically injected
    }
}
```

### **6.2 Update MainViewModel**
```kotlin
class MainViewModel @Inject constructor(
    // ... existing services
    private val qnnService: QNNLLMService,
    private val termuxService: TermuxLLMService
) : ViewModel() {
    
    private val useQNN = MutableStateFlow(true)
    
    suspend fun translate(text: String): String {
        return if (useQNN.value && qnnService.isAvailable()) {
            qnnService.translate(text, targetLanguage).getOrElse {
                // Fallback to Termux
                termuxService.translate(text, targetLanguage)
            }
        } else {
            termuxService.translate(text, targetLanguage)
        }
    }
}
```

---

## 🏆 **Expected Results**

### **Performance Targets**
- **Latency**: <1 second (vs 3-8s Termux)
- **Battery**: <5% per hour (vs 25% Termux)
- **Memory**: <2GB peak usage
- **Accuracy**: Maintain 95%+ translation quality

### **Success Criteria**
- [ ] QNN service initializes successfully
- [ ] Model loads in <2 seconds
- [ ] Inference runs in <1 second
- [ ] Battery usage <5% per hour
- [ ] Graceful fallback to Termux

---

**🚀 Next: Begin with Phase 1 - Environment Setup**
