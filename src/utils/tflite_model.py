from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import numpy as np

from .tflite_backend import get_tflite_interpreter


class TFLiteModel:
    """Tiny helper to load and invoke a TFLite model safely."""

    def __init__(self, model_path: Path) -> None:
        Interpreter, backend = get_tflite_interpreter()
        if Interpreter is None:
            raise RuntimeError("No TFLite backend available (tensorflow or tflite_runtime)")
        if not model_path.exists():
            raise FileNotFoundError(f"TFLite model not found: {model_path}")

        self.backend = backend
        self.model_path = model_path
        self.interpreter = Interpreter(model_path=str(model_path))  # type: ignore[call-arg]
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def set_input(self, array: np.ndarray, index: int = 0) -> None:
        detail = self.input_details[index]
        # Ensure dtype matches
        expected_dtype = np.dtype(detail.get("dtype", array.dtype))
        if array.dtype != expected_dtype:
            try:
                array = array.astype(expected_dtype)
            except Exception:
                # Fallback: leave as-is; set_tensor may raise a clearer error
                pass

        # Ensure shape matches; resize if needed
        expected_shape = tuple(detail.get("shape", array.shape))
        if tuple(array.shape) != expected_shape and all(dim != 0 for dim in expected_shape):
            try:
                # Try interpreter resize then re-allocate
                self.interpreter.resize_tensor_input(detail["index"], array.shape, strict=False)
                self.interpreter.allocate_tensors()
                # Refresh details after allocation
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                detail = self.input_details[index]
            except Exception:
                # As a last resort, attempt to reshape array to expected shape if size matches
                if np.prod(array.shape) == np.prod(expected_shape):
                    array = array.reshape(expected_shape)

        self.interpreter.set_tensor(detail["index"], array)

    def invoke(self) -> None:
        self.interpreter.invoke()

    def get_output(self, index: int = 0) -> np.ndarray:
        return self.interpreter.get_tensor(self.output_details[index]["index"])  # type: ignore[no-any-return]
