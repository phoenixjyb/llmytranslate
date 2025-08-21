from __future__ import annotations

"""Lightweight TinyLlama TFLite inference wrapper.

Loads models/real_tinyllama.tflite and exposes a simple logits() call.
Assumes input_ids shape [1, seq_len] int32; output [1, seq_len, vocab].
"""

from pathlib import Path
from typing import Optional
import numpy as np

from src.utils.tflite_model import TFLiteModel


class TinyLlamaTFLite:
    def __init__(self, model_path: Optional[Path] = None) -> None:
        if model_path is None:
            model_path = Path(__file__).parents[2] / "models" / "real_tinyllama.tflite"
        self.model_path = model_path
        if not self.model_path.exists():
            raise FileNotFoundError(f"TFLite model not found: {self.model_path}")
    self.model = TFLiteModel(self.model_path)

    def logits(self, input_ids: np.ndarray) -> np.ndarray:
        if input_ids.dtype != np.int32:
            input_ids = input_ids.astype(np.int32)
    self.model.set_input(input_ids, 0)
    self.model.invoke()
    return self.model.get_output(0)
