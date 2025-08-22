/**
 * TensorFlow Lite GPU Service - Production Implementation
 * High-performance mobile AI inference using GPU acceleration
 * Target: Samsung S24 Ultra Adreno 750 GPU
 */

#include "tflite_gpu_service.h"
#include <android/log.h>
#include <android/asset_manager.h>
#include <chrono>
#include <random>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <thread>
#include <iomanip>

#define LOG_TAG "TFLiteGPU"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)

namespace mobile_ai {

TFLiteGPUService::TFLiteGPUService() : 
    initialized_(false), 
    model_loaded_(false),
    interpreter_(nullptr), 
    model_(nullptr),
    gpu_delegate_(nullptr),
    asset_manager_(nullptr) {
    LOGI("TFLiteGPUService constructor - Production Implementation");
}

TFLiteGPUService::~TFLiteGPUService() {
    cleanup();
}

bool TFLiteGPUService::initialize(const std::string& model_path) {
    LOGI("Initializing TensorFlow Lite GPU service with model: %s", model_path.c_str());
    
    if (initialized_) {
        LOGI("Service already initialized");
        return true;
    }
    
    model_path_ = model_path;
    
    try {
        // Load model from file
        if (!loadModelFromFile()) {
            LOGE("Failed to load model from file");
            return false;
        }
        
        // Initialize GPU delegate
        if (!initializeGPUDelegate()) {
            LOGE("Failed to initialize GPU delegate, falling back to CPU");
        }
        
        // Build interpreter
        if (!buildInterpreter()) {
            LOGE("Failed to build interpreter");
            return false;
        }
        
        // Warm up the model
        warmUpModel();
        
        initialized_ = true;
        LOGI("✅ TensorFlow Lite GPU service initialized successfully");
        return true;
        
    } catch (const std::exception& e) {
        LOGE("Exception during initialization: %s", e.what());
        return false;
    }
}

bool TFLiteGPUService::initializeWithAssets(AAssetManager* asset_manager) {
    LOGI("Initializing TensorFlow Lite GPU service with Android assets");
    
    if (initialized_) {
        LOGI("Service already initialized");
        return true;
    }
    
    if (!asset_manager) {
        LOGE("Asset manager is null");
        return false;
    }
    
    asset_manager_ = asset_manager;
    
    try {
        // Load model from assets
        if (!loadModelFromAssets()) {
            LOGE("Failed to load model from assets");
            return false;
        }
        
        // Initialize GPU delegate
        if (!initializeGPUDelegate()) {
            LOGE("Failed to initialize GPU delegate, falling back to CPU");
        }
        
        // Build interpreter
        if (!buildInterpreter()) {
            LOGE("Failed to build interpreter");
            return false;
        }
        
        // Warm up the model
        warmUpModel();
        
        initialized_ = true;
        LOGI("✅ TensorFlow Lite GPU service initialized successfully with assets");
        return true;
        
    } catch (const std::exception& e) {
        LOGE("Exception during asset initialization: %s", e.what());
        return false;
    }
}

std::string TFLiteGPUService::processInference(const std::string& input_text) {
    if (!initialized_ || !interpreter_) {
        LOGE("Service not initialized");
        return "Error: Service not initialized";
    }
    
    LOGI("Processing inference for input: %.50s%s", 
         input_text.c_str(), 
         input_text.length() > 50 ? "..." : "");
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Tokenize input
        std::vector<int32_t> tokens = tokenizeInput(input_text);
        
        // Set input tensor
        if (!setInputTensor(tokens)) {
            LOGE("Failed to set input tensor");
            return generateFallbackResponse(input_text);
        }
        
        // Run inference
        TfLiteStatus status = interpreter_->Invoke();
        if (status != kTfLiteOk) {
            LOGE("Inference failed with status: %d", status);
            return generateFallbackResponse(input_text);
        }
        
        // Decode output
        std::string result = decodeOutput();
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        
        LOGI("Inference completed in %lld ms", duration.count());
        return result;
        
    } catch (const std::exception& e) {
        LOGE("Inference failed: %s", e.what());
        return generateFallbackResponse(input_text);
    }
}

float TFLiteGPUService::getPerformanceScore() {
    if (!initialized_) {
        return 0.0f;
    }
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Run a simple benchmark
    std::string test_input = "This is a performance test input for TensorFlow Lite GPU benchmarking";
    processInference(test_input);
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    // Calculate performance score based on response time
    // Target: <200ms for GPU, <500ms for CPU
    float base_score = gpu_delegate_ ? 0.8f : 0.6f; // GPU gets higher base score
    float time_penalty = std::min(1.0f, duration.count() / 1000.0f); // Penalty for slow responses
    float score = base_score * (1.0f - time_penalty * 0.5f);
    
    score = std::min(1.0f, std::max(0.0f, score)); // Clamp between 0 and 1
    
    LOGI("Performance score: %.2f (response time: %lld ms) [%s]", 
         score, duration.count(), gpu_delegate_ ? "GPU" : "CPU");
    return score;
}

void TFLiteGPUService::cleanup() {
    if (initialized_) {
        LOGI("Cleaning up TensorFlow Lite GPU service");
        
        // Clean up GPU delegate
        if (gpu_delegate_) {
            TfLiteGpuDelegateV2Delete(gpu_delegate_);
            gpu_delegate_ = nullptr;
        }
        
        // Clean up interpreter and model
        interpreter_.reset();
        model_.reset();
        
        // Clear model buffer
        model_buffer_.clear();
        
        initialized_ = false;
        model_loaded_ = false;
        
        LOGI("TensorFlow Lite GPU service cleanup complete");
    }
}

bool TFLiteGPUService::loadModelFromFile() {
    LOGI("Loading model from file: %s", model_path_.c_str());
    
    // Load the model
    model_ = tflite::FlatBufferModel::BuildFromFile(model_path_.c_str());
    if (!model_) {
        LOGE("Failed to load model from file: %s", model_path_.c_str());
        return false;
    }
    
    model_loaded_ = true;
    LOGI("✅ Model loaded successfully from file");
    return true;
}

bool TFLiteGPUService::loadModelFromAssets() {
    LOGI("Loading model from Android assets");
    
    // Priority list of models to try (prefer real models if packaged)
    std::vector<std::string> model_files = {
        "models/real_tinyllama.tflite",
        // Note: real_speecht5.tflite has different IO; enable only if decode/IO adapted
        // "models/real_speecht5.tflite",
        "models/tiny_transformer.tflite",
        "models/numeric_model.tflite",
        "models/simple_text_model.tflite"
    };
    
    for (const auto& model_file : model_files) {
        LOGI("Trying to load model: %s", model_file.c_str());
        
        AAsset* asset = AAssetManager_open(asset_manager_, model_file.c_str(), AASSET_MODE_BUFFER);
        if (!asset) {
            LOGD("Model not found: %s", model_file.c_str());
            continue;
        }
        
        // Get asset size
        off_t asset_size = AAsset_getLength(asset);
        if (asset_size <= 0) {
            LOGE("Invalid asset size for %s: %ld", model_file.c_str(), asset_size);
            AAsset_close(asset);
            continue;
        }
        
        // Read asset data
        model_buffer_.resize(asset_size);
        int bytes_read = AAsset_read(asset, model_buffer_.data(), asset_size);
        AAsset_close(asset);
        
        if (bytes_read != asset_size) {
            LOGE("Failed to read complete asset %s: %d/%ld bytes", 
                 model_file.c_str(), bytes_read, asset_size);
            continue;
        }
        
        // Build model from buffer
        model_ = tflite::FlatBufferModel::BuildFromBuffer(
            model_buffer_.data(), model_buffer_.size());
        
        if (!model_) {
            LOGE("Failed to build model from asset: %s", model_file.c_str());
            continue;
        }
        
        model_loaded_ = true;
        LOGI("✅ Model loaded successfully from asset: %s (%ld bytes)", 
             model_file.c_str(), asset_size);
        return true;
    }
    
    LOGE("Failed to load any model from assets");
    return false;
}

bool TFLiteGPUService::initializeGPUDelegate() {
    LOGI("Initializing GPU delegate for Adreno 750");
    
    // Configure GPU delegate for optimal Adreno 750 performance
    TfLiteGpuDelegateOptionsV2 options = TfLiteGpuDelegateOptionsV2Default();
    options.inference_preference = TFLITE_GPU_INFERENCE_PREFERENCE_FAST_SINGLE_ANSWER;
    options.inference_priority1 = TFLITE_GPU_INFERENCE_PRIORITY_MIN_LATENCY;
    options.inference_priority2 = TFLITE_GPU_INFERENCE_PRIORITY_AUTO;
    options.inference_priority3 = TFLITE_GPU_INFERENCE_PRIORITY_AUTO;
    
    // Adreno 750 specific optimizations
    options.experimental_flags = TFLITE_GPU_EXPERIMENTAL_FLAGS_ENABLE_QUANT;
    options.model_token = nullptr; // Use default token
    
    // Create GPU delegate
    gpu_delegate_ = TfLiteGpuDelegateV2Create(&options);
    if (!gpu_delegate_) {
        LOGE("Failed to create GPU delegate");
        return false;
    }
    
    LOGI("✅ GPU delegate initialized for Adreno 750");
    return true;
}

bool TFLiteGPUService::buildInterpreter() {
    LOGI("Building TensorFlow Lite interpreter");
    
    if (!model_) {
        LOGE("Model not loaded");
        return false;
    }
    
    // Build the interpreter
    tflite::ops::builtin::BuiltinOpResolver resolver;
    tflite::InterpreterBuilder builder(*model_, resolver);
    
    if (builder(&interpreter_) != kTfLiteOk) {
        LOGE("Failed to build interpreter");
        return false;
    }
    
    if (!interpreter_) {
        LOGE("Interpreter is null");
        return false;
    }
    
    // Apply GPU delegate if available
    if (gpu_delegate_) {
        if (interpreter_->ModifyGraphWithDelegate(gpu_delegate_) != kTfLiteOk) {
            LOGE("Failed to apply GPU delegate, falling back to CPU");
            // Continue with CPU execution
        } else {
            LOGI("✅ GPU delegate applied successfully");
        }
    }
    
    // Heuristic: set a small sequence length for smoke tests if dynamic
    if (!interpreter_->inputs().empty()) {
        int input_index = interpreter_->inputs()[0];
        TfLiteTensor* t = interpreter_->tensor(input_index);
        if (t && t->dims && t->dims->size == 2) {
            int dim1 = t->dims->data[1];
            if (dim1 <= 0) {
                std::vector<int> new_shape = {1, 8};
                interpreter_->ResizeInputTensor(input_index, new_shape);
            }
        }
    }

    // Set number of threads for CPU fallback
    interpreter_->SetNumThreads(4); // Optimal for Samsung S24 Ultra
    
    // Allocate tensors
    if (interpreter_->AllocateTensors() != kTfLiteOk) {
        LOGE("Failed to allocate tensors");
        return false;
    }
    
    // Log input/output tensor info
    LOGI("Interpreter built successfully:");
    LOGI("  Input tensors: %zu", interpreter_->inputs().size());
    LOGI("  Output tensors: %zu", interpreter_->outputs().size());
    
    for (size_t i = 0; i < interpreter_->inputs().size(); i++) {
        TfLiteTensor* tensor = interpreter_->input_tensor(i);
        int d0 = tensor && tensor->dims && tensor->dims->size > 0 ? tensor->dims->data[0] : -1;
        int d1 = tensor && tensor->dims && tensor->dims->size > 1 ? tensor->dims->data[1] : -1;
        int d2 = tensor && tensor->dims && tensor->dims->size > 2 ? tensor->dims->data[2] : -1;
        int d3 = tensor && tensor->dims && tensor->dims->size > 3 ? tensor->dims->data[3] : -1;
        LOGI("  Input[%zu]: %s, type: %d, dims: [%d,%d,%d,%d] (rank=%d)", i, tensor->name ? tensor->name : "unnamed", tensor->type, d0, d1, d2, d3, tensor->dims ? tensor->dims->size : 0);
    }
    
    return true;
}

void TFLiteGPUService::warmUpModel() {
    LOGI("Warming up TensorFlow Lite model");
    
    if (!interpreter_) {
        LOGE("Interpreter not available for warm-up");
        return;
    }
    
    // Run a dummy inference to warm up the model
    try {
        std::string dummy_input = "warm up";
        std::vector<int32_t> tokens = tokenizeInput(dummy_input);
        setInputTensor(tokens);
        interpreter_->Invoke();
        
        LOGI("✅ Model warm-up completed");
    } catch (const std::exception& e) {
        LOGE("Model warm-up failed: %s", e.what());
    }
}

std::vector<int32_t> TFLiteGPUService::tokenizeInput(const std::string& input) {
    // Simple tokenization - in production, use proper tokenizer
    std::vector<int32_t> tokens;
    
    // Convert characters to token IDs (simplified)
    for (char c : input) {
        tokens.push_back(static_cast<int32_t>(c));
    }
    
    // Pad or truncate to fixed length (e.g., 128 tokens)
    const size_t max_tokens = 128;
    if (tokens.size() > max_tokens) {
        tokens.resize(max_tokens);
    } else {
        tokens.resize(max_tokens, 0); // Pad with zeros
    }
    
    return tokens;
}

bool TFLiteGPUService::setInputTensor(const std::vector<int32_t>& tokens) {
    if (!interpreter_ || interpreter_->inputs().empty()) {
        LOGE("No input tensors available");
        return false;
    }
    
    // Get input tensor
    TfLiteTensor* input_tensor = interpreter_->input_tensor(0);
    if (!input_tensor) {
        LOGE("Failed to get input tensor");
        return false;
    }
    
    // Check tensor type and copy data
    if (input_tensor->type == kTfLiteInt32) {
        std::memcpy(input_tensor->data.i32, tokens.data(), 
                   std::min(tokens.size() * sizeof(int32_t), 
                           static_cast<size_t>(input_tensor->bytes)));
    } else if (input_tensor->type == kTfLiteFloat32) {
        // Convert int32 to float32
        float* data = input_tensor->data.f;
        for (size_t i = 0; i < tokens.size() && i < input_tensor->bytes / sizeof(float); i++) {
            data[i] = static_cast<float>(tokens[i]);
        }
    } else {
        LOGE("Unsupported input tensor type: %d", input_tensor->type);
        return false;
    }
    
    return true;
}

std::string TFLiteGPUService::decodeOutput() {
    if (!interpreter_ || interpreter_->outputs().empty()) {
        LOGE("No output tensors available");
        return "Error: No output tensors";
    }
    
    // Get output tensor
    TfLiteTensor* output_tensor = interpreter_->output_tensor(0);
    if (!output_tensor) {
        LOGE("Failed to get output tensor");
        return "Error: Failed to get output tensor";
    }
    
    std::ostringstream result;
    
    // Decode based on tensor type; support 3D logits [1, T, V]
    if (output_tensor->type == kTfLiteFloat32) {
        float* data = output_tensor->data.f;
        int rank = output_tensor->dims ? output_tensor->dims->size : 0;
        if (rank == 3) {
            int b = output_tensor->dims->data[0];
            int t = output_tensor->dims->data[1];
            int v = output_tensor->dims->data[2];
            if (b >= 1 && t >= 1 && v > 0) {
                size_t offset = static_cast<size_t>((t - 1) * v);
                const float* logits = data + offset;
                int best = 0; float best_score = logits[0];
                for (int i = 1; i < v; ++i) if (logits[i] > best_score) { best_score = logits[i]; best = i; }
                result << "TensorFlow Lite response (next token " << best
                       << ", score: " << std::fixed << std::setprecision(3) << best_score << ")";
                return result.str();
            }
        }
        size_t elements = output_tensor->bytes / sizeof(float);
        size_t best_token = 0; float best_score = data[0];
        for (size_t i = 1; i < elements; i++) if (data[i] > best_score) { best_score = data[i]; best_token = i; }
        result << "TensorFlow Lite response (token " << best_token 
               << ", score: " << std::fixed << std::setprecision(3) << best_score << ")";
        
    } else if (output_tensor->type == kTfLiteInt32) {
        int32_t* data = output_tensor->data.i32;
        size_t elements = output_tensor->bytes / sizeof(int32_t);
        
        result << "TensorFlow Lite response: ";
        for (size_t i = 0; i < std::min(elements, static_cast<size_t>(10)); i++) {
            if (data[i] > 0 && data[i] < 128) { // Valid ASCII
                result << static_cast<char>(data[i]);
            }
        }
    } else {
        result << "TensorFlow Lite response (unsupported output type: " << output_tensor->type << ")";
    }
    
    return result.str();
}

std::string TFLiteGPUService::generateFallbackResponse(const std::string& input) {
    // Generate a contextual fallback response
    std::ostringstream response;
    response << "TensorFlow Lite processed: '" << input.substr(0, 50);
    if (input.length() > 50) response << "...";
    response << "' [Fallback mode]";
    
    return response.str();
}

} // namespace mobile_ai
