from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import onnxruntime as ort

from transformers import AutoTokenizer


@dataclass(frozen=True)
class IntentPrediction:
    intent: str
    confidence: float
    alternatives: list[dict]


class MiniLMIntentClassifier:

    def __init__(
        self,
        model_dir: str | Path,
        intra_op_threads: int = 2,
    ):
        self.model_dir = Path(model_dir).resolve()

        with open(
            self.model_dir / "config.json",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

        self.id2label = {
            int(index): label
            for index, label in config["id2label"].items()
        }

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_dir,
            local_files_only=True,
        )

        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = intra_op_threads
        session_options.inter_op_num_threads = 1
        session_options.execution_mode = (
            ort.ExecutionMode.ORT_SEQUENTIAL
        )

        self.session = ort.InferenceSession(
            str(self.model_dir / "model.onnx"),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )

        self.input_names = {
            item.name
            for item in self.session.get_inputs()
        }

    def predict(self, query: str) -> IntentPrediction:

        query = query.strip()

        if not query:
            return IntentPrediction(
                intent="unknown",
                confidence=1.0,
                alternatives=[],
            )

        encoded = self.tokenizer(
            query,
            return_tensors="np",
            truncation=True,
            padding="max_length",
            max_length=128,
        )

        inputs = {
            name: encoded[name].astype(np.int64)
            for name in self.input_names
        }

        logits = self.session.run(
            None,
            inputs,
        )[0][0]

        logits = logits - np.max(logits)

        probabilities = np.exp(logits)
        probabilities /= probabilities.sum()

        top_indices = np.argsort(
            probabilities
        )[::-1][:3]

        top_index = int(top_indices[0])

        return IntentPrediction(
            intent=self.id2label[top_index],
            confidence=float(probabilities[top_index]),
            alternatives=[
                {
                    "intent": self.id2label[int(index)],
                    "confidence": float(probabilities[index]),
                }
                for index in top_indices[1:]
            ],
        )