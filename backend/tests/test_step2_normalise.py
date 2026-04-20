"""
Step 2 — Test article normalisation + sentiment scoring without Kafka.
Run from backend/:
    python tests/test_step2_normalise.py
"""

from app.ingestion.streaming.news_kafka_consumer import _normalise_article

print("\n" + "="*70)
print("STEP 2 — _normalise_article() with FinBERT (no Kafka needed)")
print("="*70 + "\n")

fake_article = {
    "symbol":         "BTC/USD",
    "display_symbol": "BTC/USD",
    "market_type":    "crypto",
    "source":         "finnhub_ws",
    "news_id":        "abc123",
    "timestamp":      "2026-04-20T10:00:00+00:00",
    "title":          "Bitcoin hits record high as ETF inflows surge",
    "summary":        "Institutional investors poured billions into Bitcoin ETFs.",
    "url":            "https://example.com",
    "source_name":    "Reuters",
    "ingestion_time": "2026-04-20T10:00:01+00:00",
}

result = _normalise_article(fake_article)

print(f"  title             : {result['title']}")
print(f"  sentiment_label   : {result['sentiment_label']}")
print(f"  sentiment_score   : {result['sentiment_score']}")
print(f"  sentiment_compound: {result['sentiment_compound']:+.4f}")
print(f"  sentiment_model   : {result['sentiment_model']}")

assert result["sentiment_label"] in ("positive", "neutral", "negative"), "label must be one of the 3 values"
assert 0.0 <= result["sentiment_score"] <= 1.0, "score must be between 0 and 1"
assert -1.0 <= result["sentiment_compound"] <= 1.0, "compound must be between -1 and +1"
assert result["sentiment_model"] == "finbert", "model must be finbert"

print("\n✅ Step 2 passed — normalise + sentiment works correctly.\n")