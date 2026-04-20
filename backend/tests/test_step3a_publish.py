"""
Step 3a — Publish a fake article to Kafka news_stream topic.
Run AFTER starting the consumer in another terminal:
    terminal 1: python -m app.ingestion.streaming.news_kafka_consumer
    terminal 2: python tests/test_step3a_publish.py
    terminal 3: python tests/test_step3b_read.py

Run from backend/:
    python tests/test_step3a_publish.py
"""

import json
from kafka import KafkaProducer

print("\n" + "="*70)
print("STEP 3a — Publish fake article to Kafka")
print("="*70 + "\n")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: v.encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

article = {
    "symbol":         "BTC/USD",
    "display_symbol": "BTC/USD",
    "market_type":    "crypto",
    "source":         "finnhub_ws",
    "news_id":        "test001",
    "timestamp":      "2026-04-20T10:00:00+00:00",
    "title":          "Bitcoin ETF sees record inflows as price breaks 100k",
    "summary":        "Wall Street demand for Bitcoin exposure hits new highs.",
    "url":            "https://example.com",
    "source_name":    "Bloomberg",
    "ingestion_time": "2026-04-20T10:00:01+00:00",
}

producer.send("news_stream", key="BTC/USD", value=json.dumps(article))
producer.flush()
producer.close()

print("  Article sent to Kafka topic: news_stream")
print(f"  title  : {article['title']}")
print(f"  symbol : {article['symbol']}")
print("\n✅ Step 3a done — now wait ~60s for the consumer to flush, then run test_step3b_read.py\n")