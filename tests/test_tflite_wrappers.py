import os
from pathlib import Path
import numpy as np
import pytest

from src.utils.tflite_backend import get_tflite_interpreter


@pytest.mark.skipif(get_tflite_interpreter()[0] is None, reason="No TFLite backend available")
class TestTFLiteWrappers:
    def test_tinyllama_smoke(self):
        from src.services.tflite_llm import TinyLlamaTFLite

        model_path = Path(__file__).parents[1] / "models" / "real_tinyllama.tflite"
        if not model_path.exists():
            pytest.skip("real_tinyllama.tflite not present")

        llm = TinyLlamaTFLite(model_path)
        x = np.zeros((1, 8), dtype=np.int32)  # small sequence
        y = llm.logits(x)
        assert y.shape[0] == 1
        assert y.shape[1] == 8
        assert y.ndim == 3

    def test_speecht5_smoke(self):
        from src.services.tflite_tts import SpeechT5TFLite

        model_path = Path(__file__).parents[1] / "models" / "real_speecht5.tflite"
        if not model_path.exists():
            pytest.skip("real_speecht5.tflite not present")

        tts = SpeechT5TFLite(model_path)
        # Minimal dummy input – assumes model expects [1, T, D] or [1, N]
        x = np.zeros((1, 64), dtype=np.float32)
        y = tts.forward(x)
        assert y.shape[0] == 1
        assert y.ndim >= 2
