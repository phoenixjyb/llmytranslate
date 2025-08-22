package com.llmytranslate.android.services

import android.content.Context
import android.content.res.AssetManager
import android.util.Log
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.support.common.FileUtil
import java.nio.MappedByteBuffer

/**
 * Simple TensorFlow Lite (Java) service that loads a model from assets and runs a basic inference.
 * This is CPU-only and intended for quick demos/smoke tests.
 */
class TFLiteLocalService(private val context: Context) {
    companion object {
        private const val TAG = "TFLiteLocal"
        private val MODEL_CANDIDATES = listOf(
            "models/simple_text_model.tflite",
            "models/numeric_model.tflite",
            "models/tiny_transformer.tflite",
            "models/real_tinyllama.tflite",
            "models/asr_placeholder.tflite"
        )
    }

    private var interpreter: Interpreter? = null
    private var modelPath: String? = null

    fun initializeFromAssets(): Boolean {
        try {
            val assets = context.assets
            val found = MODEL_CANDIDATES.firstOrNull { existsInAssets(assets, it) }
            if (found == null) {
                Log.w(TAG, "No .tflite model found in assets/models; using zeros-only demo mode")
                return false
            }
            val modelBuffer: MappedByteBuffer = FileUtil.loadMappedFile(context, found)
            interpreter = Interpreter(modelBuffer)
            modelPath = found
            Log.i(TAG, "Loaded TFLite model: $found")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize TFLite: ${e.message}")
            interpreter = null
            return false
        }
    }

    fun isReady(): Boolean = interpreter != null

    fun backendInfo(): String {
        val t = interpreter ?: return "TFLite(Java): Not initialized"
        val inputs = t.getInputTensor(0)
        val outputs = t.getOutputTensor(0)
        return "TFLite(Java) | in=${inputs.dataType()} ${inputs.shape().contentToString()} out=${outputs.dataType()} ${outputs.shape().contentToString()}"
    }

    fun runText(input: String): String {
        val t = interpreter ?: return "Error: TFLite not initialized"
        return try {
            // Prepare input based on tensor type/shape
            val inTensor = t.getInputTensor(0)
            val inShape = inTensor.shape()
            val inType = inTensor.dataType().toString()
            val batch = if (inShape.isNotEmpty()) inShape[0] else 1
            val dim = if (inShape.size >= 2 && inShape[1] > 0) inShape[1] else 64

            // Build a simple vector from input text (ASCII-normalized)
            val ascii = input.take(dim).map { it.code and 0x7F }
            val padded = IntArray(dim) { i -> if (i < ascii.size) ascii[i] else 0 }

            val outputs = t.getOutputTensor(0)
            val outShape = outputs.shape()

            val outputMap = HashMap<Int, Any>()
            val inputArray: Array<Any>

            when (inType) {
                "INT32" -> {
                    val buf = Array(batch) { IntArray(dim) }
                    buf[0] = padded
                    inputArray = arrayOf(buf)
                }
                "FLOAT32" -> {
                    val buf = Array(batch) { FloatArray(dim) }
                    buf[0] = FloatArray(dim) { i -> padded[i] / 127.0f }
                    inputArray = arrayOf(buf)
                }
                else -> {
                    // Fallback: zeros float
                    val buf = Array(batch) { FloatArray(dim) }
                    inputArray = arrayOf(buf)
                }
            }

            // Prepare an output buffer exactly matching the tensor shape (no flattening)
            val outType = outputs.dataType().toString()
            val outAny: Any = when (outType) {
                "INT32" -> createIntBuffer(outShape)
                "FLOAT32" -> createFloatBuffer(outShape)
                else -> createFloatBuffer(outShape)
            }
            outputMap[0] = outAny

            t.runForMultipleInputsOutputs(inputArray, outputMap)

            // Summarize output
            val preview = when (outAny) {
                is IntArray -> outAny.take(8).joinToString(", ")
                is FloatArray -> outAny.take(8).joinToString(", ") { String.format("%.3f", it) }
                is Array<*> -> summarizeNested(outAny)
                else -> outType
            }
            "OK: ran ${modelPath ?: "(asset)"} → outShape=${outShape.contentToString()} sample=[${preview}]"
        } catch (e: Exception) {
            Log.e(TAG, "TFLite inference failed: ${e.message}")
            "Error: ${e.message}"
        }
    }

    fun cleanup() {
        try {
            interpreter?.close()
        } catch (_: Exception) {}
        interpreter = null
    }

    private fun existsInAssets(assets: AssetManager, path: String): Boolean = try {
        assets.open(path).use { }
        true
    } catch (_: Exception) {
        false
    }
}

// Helpers to build output buffers matching tensor shapes (supports up to 4D)
private fun createFloatBuffer(shape: IntArray): Any = when (shape.size) {
    0 -> FloatArray(1)
    1 -> FloatArray(shape[0])
    2 -> Array(shape[0]) { FloatArray(shape[1]) }
    3 -> Array(shape[0]) { Array(shape[1]) { FloatArray(shape[2]) } }
    else -> Array(shape[0]) { Array(shape[1]) { Array(shape[2]) { FloatArray(shape[3]) } } }
}

private fun createIntBuffer(shape: IntArray): Any = when (shape.size) {
    0 -> IntArray(1)
    1 -> IntArray(shape[0])
    2 -> Array(shape[0]) { IntArray(shape[1]) }
    3 -> Array(shape[0]) { Array(shape[1]) { IntArray(shape[2]) } }
    else -> Array(shape[0]) { Array(shape[1]) { Array(shape[2]) { IntArray(shape[3]) } } }
}

private fun summarizeNested(any: Any): String = when (any) {
    is Array<*> -> any.firstOrNull()?.let { summarizeNested(it) } ?: "[]"
    is FloatArray -> any.take(8).joinToString(", ") { String.format("%.3f", it) }
    is IntArray -> any.take(8).joinToString(", ")
    else -> any.toString()
}
