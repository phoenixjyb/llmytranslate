# TensorFlow Lite Native (Prebuilt) Integration

This app can link a real native TensorFlow Lite backend (C++) when prebuilt headers and libraries are provided here.

Place the following files in this folder structure:

third_party/tflite/
├── include/
│   ├── tensorflow/lite/** (headers)
│   ├── tensorflow/lite/delegates/gpu/** (GPU headers)
│   └── flatbuffers/** (if required by your headers)
└── libs/
    └── arm64-v8a/
        ├── libtensorflowlite.so
        ├── libtensorflowlite_gpu_delegate.so
        └── libc++_shared.so (if not provided by the NDK on your device)

How to enable
- Set CMake option REAL_TFLITE_AVAILABLE=ON (e.g., in Gradle externalNativeBuild.cmake.arguments or via local.properties/CI).
- Build the app; CMake will import the .so and link EGL/GLESv2 for the GPU delegate.

Notes
- Min SDK 26, ABI arm64-v8a.
- Ensure your headers match the .so version (e.g., TF Lite 2.14.x).
- If GPU delegate creation fails, the interpreter will fall back to CPU automatically.
- If this folder is empty and REAL_TFLITE_AVAILABLE=ON, the build will fail with a clear message.
