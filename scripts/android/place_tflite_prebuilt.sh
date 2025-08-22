#!/usr/bin/env bash
set -euo pipefail

# Copy prebuilt TensorFlow Lite C++ libs into the expected project location.
# Usage:
#   TFLITE_SRC_DIR=/path/to/output/libs ./scripts/android/place_tflite_prebuilt.sh
#
# Expects the following files in TFLITE_SRC_DIR (any missing are skipped):
#   - libtensorflowlite.so
#   - libtensorflowlite_gpu_delegate.so (optional)
#
# Copies into:
#   android/app/src/main/cpp/third_party/tflite/libs/arm64-v8a/

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST_DIR="$ROOT_DIR/android/app/src/main/cpp/third_party/tflite/libs/arm64-v8a"

: "${TFLITE_SRC_DIR:?Set TFLITE_SRC_DIR to the folder containing libtensorflowlite.so}"

mkdir -p "$DEST_DIR"

function copy_if_exists() {
  local name="$1"
  if [[ -f "$TFLITE_SRC_DIR/$name" ]]; then
    echo "Copying $name → $DEST_DIR"
    cp -f "$TFLITE_SRC_DIR/$name" "$DEST_DIR/"
  else
    echo "Note: $name not found in $TFLITE_SRC_DIR (skipping)"
  fi
}

copy_if_exists libtensorflowlite.so
copy_if_exists libtensorflowlite_gpu_delegate.so

echo "Done. Placed prebuilt TensorFlow Lite libs into: $DEST_DIR"
echo "Next: enable REAL_TFLITE_AVAILABLE and rebuild."
