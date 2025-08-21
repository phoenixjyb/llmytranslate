# TensorFlow Lite Models for Mobile AI

This directory contains TensorFlow Lite models optimized for mobile inference on Android.

## Model Integration Status

The TensorFlow Lite GPU service will attempt to load models in the following priority order:

1. **phi3_mini_mobile.tflite** - Microsoft Phi-3 Mini optimized for mobile
2. **distilbert_mobile.tflite** - DistilBERT for text classification  
3. **text_generator_mobile.tflite** - General purpose text generation
4. **gemma_270m_mobile.tflite** - Google Gemma 270M mobile-optimized
5. **test_model.tflite** - Development test model

## Current Implementation

The Mobile AI service is configured with:

- **TensorFlow Lite GPU delegate** for Adreno 750 acceleration
- **Automatic fallback** to CPU if GPU fails
- **Asset-based loading** from Android APK
- **Smart tokenization** with configurable sequence lengths
- **Performance monitoring** and benchmarking

## Architecture Integration

```cpp
// C++ Service
TFLiteGPUService service;
service.initializeWithAssets(asset_manager);
std::string result = service.processInference(input_text);

// Kotlin Service  
val mobileAI = MobileAIService(context)
val success = mobileAI.initializeWithAssets()
val response = mobileAI.processInference("Hello world")
```

## Performance Targets

- **Response Time**: 1-2 seconds on Samsung S24 Ultra
- **GPU Acceleration**: 70% of QNN SDK performance
- **CPU Fallback**: 40% of QNN SDK performance  
- **Memory Usage**: Optimized for mobile constraints

## Model Requirements

To add actual TensorFlow Lite models:

1. Convert models using the download script: `python3 scripts/download_tflite_models.py`
2. Place .tflite files in this directory
3. Models will be automatically detected and loaded

## Development Status

✅ **Complete**: TensorFlow Lite architecture with GPU acceleration  
✅ **Complete**: Android asset integration and JNI bridge  
✅ **Complete**: Kotlin service layer with coroutines  
✅ **Complete**: Testing framework and UI  
📋 **Next**: Download and integrate actual mobile-optimized models  

The service will operate in fallback mode until actual models are added.
