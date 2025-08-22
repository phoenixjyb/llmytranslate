Native TensorFlow Lite (C++) for Android — Getting libtensorflowlite.so

This project’s native backend needs the TensorFlow Lite C++ shared library (not the Java JNI .so from AARs) to run real TFLite in C++.

Goal
- Produce: libtensorflowlite.so (arm64-v8a)
- Optional: libtensorflowlite_gpu_delegate.so (arm64-v8a)
- Place them into: android/app/src/main/cpp/third_party/tflite/libs/arm64-v8a/

Option A: Build with Bazel (recommended)
1) Clone TensorFlow (matching your TFLite headers, 2.14.x works well):
   git clone https://github.com/tensorflow/tensorflow.git
   cd tensorflow
   git checkout v2.14.0

2) Install Bazelisk and Android NDK/SDK (NDK r25c+)

3) Configure TensorFlow build (you can skip full TF, we just use TFLite):
   ./configure
   - Disable CUDA/ROCM/TPU
   - Accept defaults for others

4) Build TFLite shared lib for Android arm64:
   bazel build -c opt \
     --config=android_arm64 \
     //tensorflow/lite:libtensorflowlite.so

5) (Optional) Build GPU delegate:
   bazel build -c opt \
     --config=android_arm64 \
     //tensorflow/lite/delegates/gpu:libtensorflowlite_gpu_delegate.so

6) Copy artifacts:
   export TFLITE_SRC_DIR=$(pwd)/bazel-bin/tensorflow/lite
   (or directory containing the .so files)
   From your repo root:
   TFLITE_SRC_DIR="$TFLITE_SRC_DIR" ./scripts/android/place_tflite_prebuilt.sh

Option B: Build with CMake (advanced)
- TensorFlow provides limited CMake support; results can vary by version. Prefer Bazel.
- If you pursue CMake, ensure you produce a real libtensorflowlite.so for arm64 and that symbols like tflite::Interpreter resolve.

Enable in this project
1) Confirm files are present:
   android/app/src/main/cpp/third_party/tflite/libs/arm64-v8a/libtensorflowlite.so
   android/app/src/main/cpp/third_party/tflite/libs/arm64-v8a/libtensorflowlite_gpu_delegate.so (optional)

2) Enable the native flag in Gradle:
   File: android/app/build.gradle.kts
   externalNativeBuild.cmake.arguments: add
     -DREAL_TFLITE_AVAILABLE=ON

3) Rebuild and install:
   ./gradlew app:assembleDebug app:installDebug

4) Verify logs:
   Look for “TFLiteGPUService constructor - Production Implementation” and no “Mock Implementation” lines.

Troubleshooting
- Undefined references to tflite:: symbols: your .so isn’t the C++ lib; ensure it’s libtensorflowlite.so from Bazel, not the JNI one from AAR.
- GPU delegate linking errors: the delegate .so is optional; CPU works fine for initial validation.
- Header mismatch: headers in include/ should align with the lib version you built.
