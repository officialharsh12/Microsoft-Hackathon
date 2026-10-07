from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import settings

class SentimentModel:
    _instance: Optional["SentimentModel"] = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.SENTIMENT_MODEL_NAME
        self.device = settings.get_torch_device()
        self.tokenizer = None
        self.model = None

    @classmethod
    def get_instance(cls) -> "SentimentModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        if self.model is None or self.tokenizer is None:
            print(f"[SentimentModel] Loading {self.model_name} on device: {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
            except Exception as e:
                print(f"[SentimentModel] Fallback to CPU due to: {e}")
                self.device = "cpu"
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to("cpu")
            self.model.eval()
            print("[SentimentModel] Loaded successfully.")

    def predict_batch(self, texts: List[str], batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs batched sentiment inference.
        Returns:
            [{"sentiment": "POSITIVE" | "NEGATIVE", "sentiment_score": float}, ...]
        """
        if not texts:
            return []
        
        self.load_model()
        batch_size = batch_size or settings.BATCH_SIZE
        results: List[Dict[str, Any]] = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

            with torch.no_grad():
                outputs = self.model(**encoded)
                probs = torch.softmax(outputs.logits, dim=1)
                predicted_classes = torch.argmax(probs, dim=1).cpu().tolist()
                confidence_scores = probs.max(dim=1).values.cpu().tolist()

            for pred_cls, score in zip(predicted_classes, confidence_scores):
                # SST-2 label 0: NEGATIVE, 1: POSITIVE
                label = self.model.config.id2label.get(pred_cls, "POSITIVE" if pred_cls == 1 else "NEGATIVE").upper()
                results.append({
                    "sentiment": label,
                    "sentiment_score": round(float(score), 4)
                })

        return results

sentiment_model = SentimentModel.get_instance()
