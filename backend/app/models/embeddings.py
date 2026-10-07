from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

class EmbeddingModel:
    _instance: Optional["EmbeddingModel"] = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.device = settings.get_torch_device()
        self.model: Optional[SentenceTransformer] = None

    @classmethod
    def get_instance(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        if self.model is None:
            print(f"[EmbeddingModel] Loading {self.model_name} on device: {self.device}...")
            try:
                self.model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                print(f"[EmbeddingModel] Fallback to CPU due to: {e}")
                self.device = "cpu"
                self.model = SentenceTransformer(self.model_name, device="cpu")
            print("[EmbeddingModel] Loaded successfully.")

    def encode(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        """
        Generates normalized sentence embeddings.
        Returns:
            np.ndarray of shape (len(texts), 384) dtype float32
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        self.load_model()
        batch_size = batch_size or settings.BATCH_SIZE
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.astype(np.float32)

    @staticmethod
    def serialize_vector(vector: np.ndarray) -> bytes:
        """Serializes 1D float32 numpy vector to raw bytes for SQLite BLOB storage."""
        return vector.astype(np.float32).tobytes()

    @staticmethod
    def deserialize_vector(blob: bytes, dim: int = 384) -> np.ndarray:
        """Deserializes raw bytes back to 1D float32 numpy vector."""
        return np.frombuffer(blob, dtype=np.float32)

embedding_model = EmbeddingModel.get_instance()
