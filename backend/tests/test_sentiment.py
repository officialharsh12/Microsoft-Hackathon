from app.models.sentiment import SentimentModel

def test_sentiment_model_batch():
    model = SentimentModel.get_instance()
    texts = [
        "This app is absolutely amazing, fast and delightful to use!",
        "Terrible experience, payments fail and customer service is nonexistent."
    ]
    results = model.predict_batch(texts, batch_size=2)
    assert len(results) == 2
    assert results[0]["sentiment"] == "POSITIVE"
    assert results[0]["sentiment_score"] > 0.8
    assert results[1]["sentiment"] == "NEGATIVE"
    assert results[1]["sentiment_score"] > 0.8
