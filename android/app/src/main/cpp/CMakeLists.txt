cmake_minimum_required(VERSION 3.22.1)
project(mobile_ai_native)

# Multi-Backend Mobile AI Configuration
# Primary: TensorFlow Lite GPU for high performance (70% QNN performance)
# Secondary: ONNX Runtime Mobile for compatibility (50% QNN performance)

# TensorFlow Lite GPU (Primary backend - best available performance)
set(TFLITE_GPU_AVAILABLE TRUE)

# Enable real TensorFlow Lite native integration when prebuilt headers & libs are available.
# By default this is OFF to keep builds working without large binaries.
option(REAL_TFLITE_AVAILABLE "Use real TensorFlow Lite native backend" OFF)

# Expected location for prebuilt headers and libs when REAL_TFLITE_AVAILABLE=ON
set(TFLITE_PREBUILT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/third_party/tflite")
set(TFLITE_PREBUILT_INCLUDE "${TFLITE_PREBUILT_ROOT}/include")
set(TFLITE_PREBUILT_LIBS_ARM64 "${TFLITE_PREBUILT_ROOT}/libs/arm64-v8a")

# ONNX Runtime Mobile (Fallback backend - broad compatibility)
set(ONNX_MOBILE_AVAILABLE TRUE)

# QNN SDK Configuration (Optional - requires Windows/Linux development)
set(QNN_SDK_ROOT "/Users/yanbo/QNN-SDK")
set(QNN_LIB_PATH "${QNN_SDK_ROOT}/lib/aarch64-android")
set(QNN_INCLUDE_PATH "${QNN_SDK_ROOT}/include")

# Check if QNN SDK is available (Windows/Linux cross-compilation)
if(EXISTS "${QNN_INCLUDE_PATH}/QNN/QnnInterface.h")
    message(STATUS "QNN SDK found at: ${QNN_SDK_ROOT}")
    set(QNN_AVAILABLE TRUE)
else()
    message(STATUS "QNN SDK not available (expected on macOS). Using alternative backends.")
    set(QNN_AVAILABLE FALSE)
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
if(QNN_AVAILABLE)
    include_directories(${QNN_INCLUDE_PATH})
    include_directories(${QNN_INCLUDE_PATH}/QNN)
endif()

# Source files
set(NATIVE_SOURCES
    jni/mobile_ai_jni_bridge.cpp
    mobile_ai/onnx_mobile_service.cpp
)

if(REAL_TFLITE_AVAILABLE)
    message(STATUS "Real TensorFlow Lite native backend: ENABLED")
    list(APPEND NATIVE_SOURCES mobile_ai/tflite_gpu_service_prod.cpp)
    add_definitions(-DREAL_TFLITE_AVAILABLE=1)
else()
    message(STATUS "Real TensorFlow Lite native backend: DISABLED (using mock)")
    list(APPEND NATIVE_SOURCES mobile_ai/tflite_gpu_service.cpp)
    add_definitions(-DREAL_TFLITE_AVAILABLE=0)
endif()

# Add QNN sources if available
if(QNN_AVAILABLE)
    list(APPEND NATIVE_SOURCES
        qnn/qnn_llm_service.cpp
        qnn/qnn_model_manager.cpp
        qnn/qnn_utils.cpp
    )
endif()

# Create shared library
add_library(mobile_ai_native SHARED ${NATIVE_SOURCES})

# Link libraries
target_link_libraries(mobile_ai_native
    log                     # Android logging
    android                 # Android NDK
)

# Link TensorFlow Lite GPU libraries (Primary backend)
if(TFLITE_GPU_AVAILABLE)
    # Note: TensorFlow Lite libraries will be linked automatically via Gradle dependency
    # The actual .so files will be packaged by the Android build system
    target_compile_definitions(mobile_ai_native PRIVATE TFLITE_GPU_AVAILABLE=1)
    message(STATUS "TensorFlow Lite GPU backend enabled")
endif()

# Link ONNX Runtime Mobile libraries (Fallback backend)
if(ONNX_MOBILE_AVAILABLE)
    # Note: ONNX Runtime libraries will be linked automatically via Gradle dependency
    # The actual .so files will be packaged by the Android build system
    target_compile_definitions(mobile_ai_native PRIVATE ONNX_MOBILE_AVAILABLE=1)
    message(STATUS "ONNX Runtime Mobile backend enabled")
endif()

# Link QNN libraries (when available - Windows/Linux development)
if(QNN_AVAILABLE)
    target_link_libraries(mobile_ai_native
        ${QNN_LIB_PATH}/libQnnHtp.so           # HTP (NPU) backend
        ${QNN_LIB_PATH}/libQnnSystem.so        # System interface
        ${QNN_LIB_PATH}/libQnnCpuBackend.so    # CPU fallback
    )
    target_compile_definitions(mobile_ai_native PRIVATE QNN_AVAILABLE=1)
else()
    target_compile_definitions(mobile_ai_native PRIVATE QNN_AVAILABLE=0)
endif()

# Compiler flags
target_compile_options(mobile_ai_native PRIVATE
    -std=c++17
    -O3
    -ffast-math
    -Wall
    -Wextra
)

# Additional compiler definitions
target_compile_definitions(mobile_ai_native PRIVATE
    ANDROID
    __ANDROID_API__=26
)

# When REAL_TFLITE_AVAILABLE, add include dirs, import and link TFLite + GPU delegate + EGL/GLESv2.
if(REAL_TFLITE_AVAILABLE)
    if(EXISTS "${TFLITE_PREBUILT_INCLUDE}" AND EXISTS "${TFLITE_PREBUILT_LIBS_ARM64}")
        include_directories(${TFLITE_PREBUILT_INCLUDE})

        # Prefer canonical library names; fall back to JNI .so names from AARs
        set(TFLITE_SO "${TFLITE_PREBUILT_LIBS_ARM64}/libtensorflowlite.so")
        if(NOT EXISTS "${TFLITE_SO}")
            set(TFLITE_SO "${TFLITE_PREBUILT_LIBS_ARM64}/jni/arm64-v8a/libtensorflowlite_jni.so")
        endif()

        set(TFLITE_GPU_SO "${TFLITE_PREBUILT_LIBS_ARM64}/libtensorflowlite_gpu_delegate.so")
        if(NOT EXISTS "${TFLITE_GPU_SO}")
            set(TFLITE_GPU_SO "${TFLITE_PREBUILT_LIBS_ARM64}/jni/arm64-v8a/libtensorflowlite_gpu_jni.so")
        endif()

        if(NOT EXISTS "${TFLITE_SO}")
            message(FATAL_ERROR "TensorFlow Lite C++ library not found at ${TFLITE_SO}. See BUILDING_NATIVE_TFLITE.md and run scripts/android/place_tflite_prebuilt.sh after building libtensorflowlite.so.")
        endif()

        add_library(tensorflowlite SHARED IMPORTED)
        set_target_properties(tensorflowlite PROPERTIES IMPORTED_LOCATION "${TFLITE_SO}")

        # GPU library is optional; link if present
        if(EXISTS "${TFLITE_GPU_SO}")
            add_library(tensorflowlite_gpu_delegate SHARED IMPORTED)
            set_target_properties(tensorflowlite_gpu_delegate PROPERTIES IMPORTED_LOCATION "${TFLITE_GPU_SO}")
            set(LINK_TFLITE_GPU tensorflowlite_gpu_delegate)
        else()
            set(LINK_TFLITE_GPU "")
        endif()

        # Link GLES/EGL for GPU delegate
        find_library(GLESv2_LIB GLESv2)
        find_library(EGL_LIB EGL)

        target_link_libraries(mobile_ai_native
            tensorflowlite
            ${LINK_TFLITE_GPU}
            ${GLESv2_LIB}
            ${EGL_LIB}
        )
    else()
        message(FATAL_ERROR "REAL_TFLITE_AVAILABLE=ON but prebuilt headers/libs not found at ${TFLITE_PREBUILT_ROOT}. See README.md for setup.")
    endif()
endif()
