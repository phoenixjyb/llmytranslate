/**
 * TensorFlow Lite GPU Service Header - Hybrid Implementation
 * High-performance mobile AI inference using GPU acceleration
 * Target: Samsung S24 Ultra Adreno 750 GPU
 * 
 * Note: Mock C++ implementation + Real TensorFlow Lite Java bridge
 */

#ifndef TFLITE_GPU_SERVICE_H
#define TFLITE_GPU_SERVICE_H

#include <string>
#include <vector>
#include <memory>
#include <android/asset_manager.h>

#if REAL_TFLITE_AVAILABLE
// Real TensorFlow Lite headers
#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model.h"
#include "tensorflow/lite/delegates/gpu/delegate.h"
#else
// Lightweight forward declarations for mock builds
namespace tflite { class Interpreter; class FlatBufferModel; }
using TfLiteDelegate = void;
#endif

namespace mobile_ai {

class TFLiteGPUService {
public:
    TFLiteGPUService();
    ~TFLiteGPUService();
    
    /**
     * Initialize the TensorFlow Lite GPU service with a model file
     * @param model_path Path to the .tflite model file
     * @return true if initialization successful
     */
    bool initialize(const std::string& model_path);
    
    /**
     * Initialize with Android asset manager for bundled models
     * @param asset_manager Android asset manager
     * @return true if initialization successful
     */
    bool initializeWithAssets(AAssetManager* asset_manager);
    
    /**
     * Process text input through TensorFlow Lite GPU inference
     * @param input_text Input text for processing
     * @return Generated response text
     */
    std::string processInference(const std::string& input_text);
    
    /**
     * Check if GPU acceleration is available and working
     * @return true if GPU delegate is available
     */
    bool isGPUAvailable();
    
    /**
     * Get performance score (0.0-1.0, where 1.0 = best possible)
     * @return Performance score based on actual benchmarks
     */
    float getPerformanceScore();
    
    /**
     * Clean up all resources
     */
    void cleanup();

private:
    // Core state
    bool initialized_;
    bool model_loaded_;
    std::string model_path_;
    
    // TensorFlow Lite components
#if REAL_TFLITE_AVAILABLE
    std::unique_ptr<tflite::Interpreter> interpreter_;
    std::unique_ptr<tflite::FlatBufferModel> model_;
    TfLiteDelegate* gpu_delegate_;
#else
    void* interpreter_;
    void* model_;
    TfLiteDelegate* gpu_delegate_;
#endif
    
    // Android asset management
    AAssetManager* asset_manager_;
    std::vector<char> model_buffer_;
    
    // Private methods
    bool loadModel();
    bool loadModelFromAssets();
    bool loadModelFromFile();
    bool initializeGPUDelegate();
    bool buildInterpreter();
    
    // Inference pipeline
    std::vector<int32_t> tokenizeInput(const std::string& input);
    bool setInputTensor(const std::vector<int32_t>& tokens);
    std::string decodeOutput();
    
    // Utilities
    void warmUpModel();
    bool initializeFallbackMode();
    std::string generateFallbackResponse(const std::string& input);
};

} // namespace mobile_ai

#endif // TFLITE_GPU_SERVICE_H
