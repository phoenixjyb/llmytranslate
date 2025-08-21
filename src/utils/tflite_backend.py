"""
Utility to provide a TFLite Interpreter from either tensorflow or tflite_runtime.
This allows running on environments without full TensorFlow installed.
"""

from __future__ import annotations

from typing import Optional, Tuple, Any


def get_tflite_interpreter() -> Tuple[Optional[Any], str]:
    """Return the TFLite Interpreter class and the backend string.

    Tries tensorflow.lite.Interpreter first, then tflite_runtime.Interpreter.
    Returns (InterpreterClass or None, backend_name).
    """
    # Try full TensorFlow first
    try:
        import tensorflow as tf  # type: ignore
        return tf.lite.Interpreter, "tensorflow"
    except Exception:
        pass

    # Fallback to tflite_runtime (lightweight runtime)
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore

        return Interpreter, "tflite_runtime"
    except Exception:
        pass

    return None, "unavailable"


def get_tflite_support_details() -> str:
    """Human-readable info string about available TFLite backend."""
    _, backend = get_tflite_interpreter()
    return backend
