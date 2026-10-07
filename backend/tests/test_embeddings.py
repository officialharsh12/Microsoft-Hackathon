import numpy as np
from app.models.embeddings import EmbeddingModel

def test_embedding_model_encode():
    model = EmbeddingModel.get_instance()
    texts = [
        "Payment failed during checkout",
        "Checkout error processing credit card",
        "Great customer service"
    ]
    embeddings = model.encode(texts, batch_size=3)
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)
    # Cosine similarity between text 0 and 1 should be significantly higher than 0 and 2
    # Since embeddings are normalized, dot product equals cosine similarity
    sim_0_1 = np.dot(embeddings[0], embeddings[1])
    sim_0_2 = np.dot(embeddings[0], embeddings[2])
    assert sim_0_1 > sim_0_2
    assert sim_0_1 > 0.65

def test_vector_serialization():
    vec = np.random.randn(384).astype(np.float32)
    blob = EmbeddingModel.serialize_vector(vec)
    recovered = EmbeddingModel.deserialize_vector(blob)
    assert np.allclose(vec, recovered)
