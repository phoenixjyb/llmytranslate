/**
 * ONNX Runtime Mobile Service Header
 * Cross-platform mobile AI inference with NNAPI acceleration
 */

#ifndef ONNX_MOBILE_SERVICE_H
#define ONNX_MOBILE_SERVICE_H

#include <string>
#include <memory>

namespace mobile_ai {

class ONNXMobileService {
public:
    ONNXMobileService();
    ~ONNXMobileService();
    
    /**
     * Initialize the ONNX Runtime Mobile service with a model
     * @param model_path Path to the .onnx model file
     * @return true if initialization successful
     */
    bool initialize(const std::string& model_path);
    
    /**
     * Process text input through ONNX Runtime Mobile inference
     * @param input_text Input text for processing
     * @return Generated response text
     */
    std::string processInference(const std::string& input_text);
    
    /**
     * Check if NNAPI acceleration is available
     * @return true if NNAPI provider is working
     */
    bool isNNAPIAvailable();
    
    /**
     * Get performance score (0.0-1.0, where 1.0 = QNN performance)
     * @return Performance score relative to QNN
     */
    float getPerformanceScore();
    
    /**
     * Clean up resources
     */
    void cleanup();

private:
    bool initialized_;
    std::string model_path_;
    
    // TODO: Add ONNX Runtime specific members
    // std::unique_ptr<Ort::Session> session_;
    // std::unique_ptr<Ort::Env> env_;
    // Ort::SessionOptions session_options_;
};

} // namespace mobile_ai

#endif // ONNX_MOBILE_SERVICE_H
