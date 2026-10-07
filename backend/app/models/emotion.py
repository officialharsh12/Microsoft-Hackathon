from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import settings

class EmotionModel:
    _instance: Optional["EmotionModel"] = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMOTION_MODEL_NAME
        self.device = settings.get_torch_device()
        self.tokenizer = None
        self.model = None

    @classmethod
    def get_instance(cls) -> "EmotionModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        if self.model is None or self.tokenizer is None:
            print(f"[EmotionModel] Loading {self.model_name} on device: {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
            except Exception as e:
                print(f"[EmotionModel] Fallback to CPU due to: {e}")
                self.device = "cpu"
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to("cpu")
            self.model.eval()
            print("[EmotionModel] Loaded successfully.")

    def predict_batch(self, texts: List[str], batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs batched emotion inference.
        Returns:
            [
              {
                "emotion": "anger",
                "emotion_score": 0.82,
                "top_emotions": [{"emotion": "anger", "score": 0.82}, ...]
              },
              ...
            ]
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
                # GoEmotions uses multi-label or single-label softmax/sigmoid.
                # Standard classification head provides logits. Softmax or Sigmoid can be used.
                probs = torch.sigmoid(outputs.logits)

            id2label = self.model.config.id2label

            for row_probs in probs:
                # Get top 3 emotions
                topk = torch.topk(row_probs, k=min(3, len(id2label)))
                top_emotions = [
                    {
                        "emotion": id2label[idx.item()],
                        "score": round(float(val.item()), 4)
                    }
                    for val, idx in zip(topk.values, topk.indices)
                ]
                top_emotion = top_emotions[0]["emotion"]
                top_score = top_emotions[0]["score"]

                results.append({
                    "emotion": top_emotion,
                    "emotion_score": top_score,
                    "top_emotions": top_emotions
                })

        return results

emotion_model = EmotionModel.get_instance()
