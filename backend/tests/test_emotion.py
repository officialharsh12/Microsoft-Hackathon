from app.models.emotion import EmotionModel

def test_emotion_model_batch():
    model = EmotionModel.get_instance()
    texts = [
        "I am so furious! You charged me twice and locked my account!",
        "Thank you so much! This is the most delightful update yet!"
    ]
    results = model.predict_batch(texts, batch_size=2)
    assert len(results) == 2
    assert "emotion" in results[0]
    assert "emotion_score" in results[0]
    assert isinstance(results[0]["top_emotions"], list)
    # Check that emotions are valid go_emotions strings
    assert results[0]["emotion"] in ["anger", "annoyance", "disappointment", "disapproval", "frustration", "sadness"]
    assert results[1]["emotion"] in ["admiration", "joy", "gratitude", "love", "excitement", "optimism"]
