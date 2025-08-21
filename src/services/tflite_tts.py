from __future__ import annotations

"""Lightweight SpeechT5 TFLite wrapper.

Loads models/real_speecht5.tflite and exposes a forward() that returns model output.
The demo model is expected to emit a mel-like tensor, e.g., shape [1, 64, 80].
"""

from pathlib import Path
from typing import Optional
import numpy as np

from src.utils.tflite_model import TFLiteModel


class SpeechT5TFLite:
    def __init__(self, model_path: Optional[Path] = None) -> None:
        if model_path is None:
            model_path = Path(__file__).parents[2] / "models" / "real_speecht5.tflite"
        self.model_path = model_path
        if not self.model_path.exists():
            raise FileNotFoundError(f"TFLite model not found: {self.model_path}")
        self.model = TFLiteModel(self.model_path)

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        if inputs.dtype != np.float32:
            inputs = inputs.astype(np.float32)
        self.model.set_input(inputs, 0)
        self.model.invoke()
        return self.model.get_output(0)
