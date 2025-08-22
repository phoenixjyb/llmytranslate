# QNN Implementation Guide

## Overview
This guide details implementing Qualcomm Neural Networks (QNN) SDK for optimal mobile AI performance, replacing TensorFlow Lite for better hardware acceleration.

## Why QNN Over TensorFlow Lite

### Performance Advantages
- **NPU Acceleration**: Direct Neural Processing Unit utilization
- **GPU Compute**: Adreno GPU shader optimization  
- **Memory Efficiency**: Mobile-optimized memory management
- **Power Efficiency**: Hardware-aware power optimization
- **Latency**: Lower inference latency than generic TensorFlow

### Development Advantages
- **Simpler Build**: Less complex than TensorFlow cross-compilation
- **Better Tooling**: Mobile-first development tools
- **Documentation**: Comprehensive Android integration guides
- **Support**: Active Qualcomm developer community

## QNN SDK Setup

### 1. Download QNN SDK
```bash
# Visit Qualcomm Developer Network
# https://developer.qualcomm.com/software/qualcomm-neural-processing-sdk
# Download QNN SDK v2.x for Windows/Linux
```

### 2. Environment Setup
```bash
export QNN_SDK_ROOT=/path/to/qnn-sdk
export PATH=$QNN_SDK_ROOT/bin:$PATH
export LD_LIBRARY_PATH=$QNN_SDK_ROOT/lib:$LD_LIBRARY_PATH
```

### 3. Android NDK Integration
```cmake
# In CMakeLists.txt
set(QNN_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../qnn-sdk)
include_directories(${QNN_ROOT}/include)
link_directories(${QNN_ROOT}/lib/android/arm64-v8a)
```

## Model Conversion Pipeline

### Current Models to Convert
1. **TinyLlama (1.1B)**: `models/real_tinyllama.tflite` → `tinyllama.qnn`
2. **SpeechT5**: `models/real_speecht5.tflite` → `speecht5.qnn` 
3. **DeepSpeech**: `models/deepspeech_lite.tflite` → `deepspeech.qnn`

### Conversion Commands
```bash
# TensorFlow Lite to QNN conversion
qnn-model-converter \
    --input_network models/real_tinyllama.tflite \
    --output_path models/tinyllama.qnn \
    --input_dim "input" 1,512 \
    --input_dtype "input" float32 \
    --quantization_overrides "models/quantization_config.json"

# For SpeechT5 TTS model
qnn-model-converter \
    --input_network models/real_speecht5.tflite \
    --output_path models/speecht5.qnn \
    --input_dim "input_ids" 1,256 \
    --input_dim "speaker_embeddings" 1,512 \
    --input_dtype "input_ids" int32 \
    --input_dtype "speaker_embeddings" float32

# For DeepSpeech STT model  
qnn-model-converter \
    --input_network models/deepspeech_lite.tflite \
    --output_path models/deepspeech.qnn \
    --input_dim "input" 1,16000 \
    --input_dtype "input" float32
```

### Quantization Configuration
```json
// models/quantization_config.json
{
  "activation_quantization": "int8",
  "weight_quantization": "int8", 
  "bias_quantization": "int32",
  "quantization_overrides": {
    "embedding_layers": "int16",
    "attention_layers": "int16"
  }
}
```

## Android CMake Integration

### Updated CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.22.1)
project("llmytranslate")

# QNN SDK Configuration
set(QNN_SDK_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../qnn-sdk)
set(QNN_TARGET_ARCH "aarch64-android")

# Include QNN headers
include_directories(${QNN_SDK_ROOT}/include/QNN)

# QNN Libraries
find_library(QNN_LIB QNN 
    PATHS ${QNN_SDK_ROOT}/lib/${QNN_TARGET_ARCH}
    NO_DEFAULT_PATH)

find_library(QNN_CPU_LIB QnnCpu
    PATHS ${QNN_SDK_ROOT}/lib/${QNN_TARGET_ARCH}  
    NO_DEFAULT_PATH)

find_library(QNN_GPU_LIB QnnGpu
    PATHS ${QNN_SDK_ROOT}/lib/${QNN_TARGET_ARCH}
    NO_DEFAULT_PATH)

find_library(QNN_HTP_LIB QnnHtp  
    PATHS ${QNN_SDK_ROOT}/lib/${QNN_TARGET_ARCH}
    NO_DEFAULT_PATH)

# Native library
add_library(llmytranslate SHARED
    src/main/cpp/native-lib.cpp
    src/main/cpp/qnn_inference.cpp
    src/main/cpp/audio_processing.cpp
    src/main/cpp/model_manager.cpp
)

# Link QNN libraries
target_link_libraries(llmytranslate
    ${QNN_LIB}
    ${QNN_CPU_LIB}
    ${QNN_GPU_LIB}
    ${QNN_HTP_LIB}
    log
    android
)

# Copy QNN models to assets
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../models/tinyllama.qnn
    ${CMAKE_CURRENT_SOURCE_DIR}/../assets/models/tinyllama.qnn
    COPYONLY
)
```

## QNN Inference Implementation

### C++ Inference Engine
```cpp
// src/main/cpp/qnn_inference.h
#pragma once
#include "QNN/QnnInterface.h"
#include "QNN/QnnTypes.h"
#include <memory>
#include <vector>

class QNNInference {
private:
    QnnInterface_t* m_qnnInterface;
    QnnContext_Handle_t m_context;
    QnnBackend_Handle_t m_backend;
    QnnGraph_Handle_t m_graph;
    
public:
    QNNInference();
    ~QNNInference();
    
    bool initialize(const std::string& modelPath);
    bool loadModel(const char* modelBuffer, size_t modelSize);
    std::vector<float> infer(const std::vector<float>& input);
    void cleanup();
    
private:
    bool initializeBackend();
    bool createContext();
    bool setupInputOutput();
};

// src/main/cpp/qnn_inference.cpp
#include "qnn_inference.h"
#include <android/log.h>
#include <android/asset_manager.h>

#define LOG_TAG "QNNInference"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

QNNInference::QNNInference() 
    : m_qnnInterface(nullptr), m_context(nullptr), 
      m_backend(nullptr), m_graph(nullptr) {
}

bool QNNInference::initialize(const std::string& modelPath) {
    // Initialize QNN backend (GPU preferred, CPU fallback)
    if (!initializeBackend()) {
        LOGE("Failed to initialize QNN backend");
        return false;
    }
    
    // Create QNN context
    if (!createContext()) {
        LOGE("Failed to create QNN context");
        return false;
    }
    
    // Load model from assets
    // Implementation for loading .qnn model file
    
    return true;
}

bool QNNInference::initializeBackend() {
    // Try GPU backend first
    QnnBackend_Config_t backendConfig = QNN_BACKEND_CONFIG_INIT;
    
    Qnn_ErrorHandle_t error = m_qnnInterface->backendCreate(
        &backendConfig, &m_backend);
    
    if (error != QNN_SUCCESS) {
        LOGE("GPU backend creation failed, trying CPU");
        // Fallback to CPU backend
    }
    
    return error == QNN_SUCCESS;
}

std::vector<float> QNNInference::infer(const std::vector<float>& input) {
    // QNN inference implementation
    std::vector<float> output;
    
    // Set input tensors
    // Execute graph
    // Get output tensors
    
    return output;
}
```

### Java/Kotlin Interface
```kotlin
// ModelManager.kt
package com.phoenix.llmytranslate

class ModelManager {
    companion object {
        init {
            System.loadLibrary("llmytranslate")
        }
    }
    
    private external fun initializeQNN(modelPath: String): Boolean
    private external fun inferenceText(input: String): String
    private external fun inferenceAudio(audioData: FloatArray): FloatArray
    private external fun cleanup()
    
    fun loadModels(context: Context): Boolean {
        val assetManager = context.assets
        
        // Load TinyLlama for text generation
        val llamaModel = "models/tinyllama.qnn"
        if (!initializeQNN(llamaModel)) {
            Log.e("ModelManager", "Failed to load TinyLlama model")
            return false
        }
        
        return true
    }
    
    fun translateText(text: String): String {
        return inferenceText(text)
    }
    
    fun synthesizeSpeech(text: String): FloatArray {
        // Text → Audio via SpeechT5 QNN model
        return inferenceAudio(text.toFloatArray())
    }
}
```

## Performance Optimizations

### Backend Selection Priority
1. **HTP (Hexagon)**: Best performance on newer Snapdragon
2. **GPU (Adreno)**: Good for parallel compute workloads  
3. **CPU**: Fallback for compatibility

### Memory Management
```cpp
// Use QNN memory pools for optimal performance
QnnMem_Config_t memConfig = QNN_MEM_CONFIG_INIT;
memConfig.memType = QNN_MEM_TYPE_ION;
memConfig.size = modelSize;
```

### Model Caching
```cpp
// Cache compiled models for faster startup
bool cacheCompiledModel(const std::string& modelPath, 
                       const std::string& cachePath) {
    // QNN graph serialization for caching
}
```

## Testing & Validation

### Performance Benchmarks
```bash
# QNN vs TensorFlow Lite comparison
adb shell am start -n com.phoenix.llmytranslate/.BenchmarkActivity
```

### Device Compatibility
- **Snapdragon 8+ Gen 1**: Full HTP acceleration
- **Snapdragon 888**: GPU + CPU acceleration  
- **Snapdragon 7+ Gen 3**: Balanced performance
- **Other SoCs**: CPU fallback mode

### Debug Tools
```bash
# QNN profiling
qnn-profile-viewer --input profile.log --output profile.html

# Memory analysis
qnn-model-analyzer --model tinyllama.qnn --backend gpu
```

## Integration Timeline

### Phase 1: Basic QNN Setup (Week 1)
- [ ] Download and configure QNN SDK
- [ ] Convert one model (TinyLlama) to QNN format
- [ ] Basic CMake integration
- [ ] Simple inference test

### Phase 2: Full Model Pipeline (Week 2)  
- [ ] Convert all three models to QNN
- [ ] Complete C++ inference engine
- [ ] Java/Kotlin interface implementation
- [ ] Asset management for models

### Phase 3: Optimization (Week 3)
- [ ] Backend selection logic
- [ ] Memory pool optimization  
- [ ] Model caching implementation
- [ ] Performance benchmarking

### Phase 4: Integration Testing (Week 4)
- [ ] End-to-end translation pipeline
- [ ] Real-time audio processing
- [ ] Device compatibility testing
- [ ] Performance validation

## Expected Performance Gains

### Latency Improvements
- **Text Generation**: 40-60% faster than TensorFlow Lite
- **Speech Synthesis**: 30-50% faster inference
- **Speech Recognition**: 25-40% latency reduction

### Memory Efficiency  
- **Peak Memory**: 20-30% lower memory usage
- **Model Loading**: 2-3x faster model initialization
- **Runtime Memory**: Better memory pool management

### Power Efficiency
- **NPU Utilization**: 50-70% lower power consumption
- **Thermal Management**: Better heat distribution
- **Battery Life**: Extended inference runtime

This QNN implementation should provide significantly better performance than the TensorFlow Lite approach while being easier to build and maintain on Windows! 🚀
