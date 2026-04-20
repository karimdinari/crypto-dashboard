"""
Step 3a (extended) — Publish 3 fake articles to Kafka news_stream topic.
Run AFTER starting the consumer in another terminal:
    terminal 1: python -m app.ingestion.streaming.news_kafka_consumer
    terminal 2: python tests/test_step3a_publish_3articles.py
    terminal 3: python tests/test_step3b_read.py

Run from backend/:
    python tests/test_step3a_publish_3articles.py
"""

import json
from kafka import KafkaProducer

print("\n" + "="*70)
print("STEP 3a (extended) — Publish 3 fake articles to Kafka")
print("="*70 + "\n")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: v.encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

articles = [
    {
        "symbol":         "BTC/USD",
        "display_symbol": "BTC/USD",
        "market_type":    "crypto",
        "source":         "finnhub_ws",
        "news_id":        "test001",
        "timestamp":      "2026-04-21T10:00:00+00:00",
        "title":          "Bitcoin ETF sees record inflows as price breaks 100k",
        "summary":        "Institutional investors poured billions into Bitcoin ETFs as demand surges.",
        "url":            "https://example.com/1",
        "source_name":    "Bloomberg",
        "ingestion_time": "2026-04-21T10:00:01+00:00",
    },
    {
        "symbol":         "ETH/USD",
        "display_symbol": "ETH/USD",
        "market_type":    "crypto",
        "source":         "finnhub_ws",
        "news_id":        "test002",
        "timestamp":      "2026-04-21T10:01:00+00:00",
        "title":          "Ethereum network faces major congestion as gas fees spike",
        "summary":        "Users report failed transactions as network load hits all time high.",
        "url":            "https://example.com/2",
        "source_name":    "CoinDesk",
        "ingestion_time": "2026-04-21T10:01:01+00:00",
    },
    {
        "symbol":         "XAU/USD",
        "display_symbol": "XAU/USD",
        "market_type":    "metals",
        "source":         "finnhub_ws",
        "news_id":        "test003",
        "timestamp":      "2026-04-21T10:02:00+00:00",
        "title":          "Gold prices steady as investors await Fed decision on interest rates",
        "summary":        "Market participants remain cautious ahead of the Federal Reserve meeting.",
        "url":            "https://example.com/3",
        "source_name":    "Reuters",
        "ingestion_time": "2026-04-21T10:02:01+00:00",
    },
]

for article in articles:
    producer.send("news_stream", key=article["symbol"], value=json.dumps(article))
    print(f"  Sent [{article['symbol']}]: {article['title']}")

producer.flush()
producer.close()

print("\n✅ 3 articles sent to Kafka topic: news_stream")
print("   Now wait ~60s for the consumer to flush, then run test_step3b_read.py\n")