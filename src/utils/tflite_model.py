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
        self.interpreter.set_tensor(self.input_details[index]["index"], array)

    def invoke(self) -> None:
        self.interpreter.invoke()

    def get_output(self, index: int = 0) -> np.ndarray:
        return self.interpreter.get_tensor(self.output_details[index]["index"])  # type: ignore[no-any-return]
