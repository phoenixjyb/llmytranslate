#!/usr/bin/env bash
set -euo pipefail

# Fetch TensorFlow Lite C++ headers into android/app/src/main/cpp/third_party/tflite/include
# Strategy:
# Download TensorFlow source tarball for the selected version and copy the
# public TensorFlow Lite headers into the project's third_party include folder.
# Also fetch FlatBuffers headers which are required by many TFLite headers.

ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
INCLUDE_DIR="$ROOT_DIR/android/app/src/main/cpp/third_party/tflite/include"
TMP_DIR="$(mktemp -d)"
TF_VERSION="2.14.0"
FLATBUFFERS_VERSION="v23.5.26"

mkdir -p "$INCLUDE_DIR"

echo "Preparing to fetch TFLite headers into: $INCLUDE_DIR"

# Download TensorFlow source tarball for the given version
TF_TARBALL_URL="https://github.com/tensorflow/tensorflow/archive/refs/tags/v${TF_VERSION}.tar.gz"
echo "Downloading TensorFlow sources: $TF_TARBALL_URL"
curl -fsSL "$TF_TARBALL_URL" -o "$TMP_DIR/tensorflow.tgz"
mkdir -p "$TMP_DIR/tensorflow"
tar -xzf "$TMP_DIR/tensorflow.tgz" -C "$TMP_DIR/tensorflow" --strip-components=1

# Copy the TensorFlow Lite headers (entire lite tree for robustness)
echo "Copying TensorFlow Lite headers..."
mkdir -p "$INCLUDE_DIR/tensorflow"
rsync -a "$TMP_DIR/tensorflow/tensorflow/lite" "$INCLUDE_DIR/tensorflow/"

# Ensure GPU delegate headers are present
if [ -d "$TMP_DIR/tensorflow/tensorflow/lite/delegates/gpu" ]; then
  echo "GPU delegate headers found."
fi

# FlatBuffers headers (required by many TFLite public headers)
echo "Fetching FlatBuffers headers ($FLATBUFFERS_VERSION)"
FB_TARBALL_URL="https://github.com/google/flatbuffers/archive/refs/tags/${FLATBUFFERS_VERSION}.tar.gz"
for i in {1..3}; do
  if curl -fsSL "$FB_TARBALL_URL" -o "$TMP_DIR/flatbuffers.tgz"; then
    break
  fi
  echo "Retry $i/3 downloading FlatBuffers..."
  sleep 2
done
test -s "$TMP_DIR/flatbuffers.tgz" || { echo "Failed to download FlatBuffers after retries"; exit 1; }
mkdir -p "$TMP_DIR/flatbuffers"
tar -xzf "$TMP_DIR/flatbuffers.tgz" -C "$TMP_DIR/flatbuffers" --strip-components=1
mkdir -p "$INCLUDE_DIR/flatbuffers"
rsync -a "$TMP_DIR/flatbuffers/include/flatbuffers/" "$INCLUDE_DIR/flatbuffers/"

cat > "$INCLUDE_DIR/README.local.txt" <<EOF
This folder contains a minimal set of TensorFlow Lite public headers fetched by scripts/android/fetch_tflite_headers.sh
Version: $TF_VERSION
Sources:
- TensorFlow: https://github.com/tensorflow/tensorflow (tag v$TF_VERSION)
- FlatBuffers: https://github.com/google/flatbuffers (tag $FLATBUFFERS_VERSION)
Note: For production or if build errors reference missing headers, replace this minimal copy with the full TensorFlow include tree matching TF ${TF_VERSION}.
EOF

echo "Done. Headers ready at: $INCLUDE_DIR"
