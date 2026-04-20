"""
Step 3b — Read the Bronze parquet and verify sentiment columns are present.
Run AFTER test_step3a_publish.py and waiting ~60s for the consumer to flush.

Run from backend/:
    python tests/test_step3b_read.py
"""

from app.ingestion.streaming.news_kafka_consumer import read_all_news

print("\n" + "="*70)
print("STEP 3b — Read Bronze parquet and check sentiment columns")
print("="*70 + "\n")

df = read_all_news()

if df.empty:
    print("❌ No data found. Make sure:")
    print("   1. The consumer is running  (python -m app.ingestion.streaming.news_kafka_consumer)")
    print("   2. You ran test_step3a_publish.py")
    print("   3. You waited ~60 seconds for the flush interval\n")
else:
    print(f"  Total articles in parquet : {len(df)}")
    print(f"  Columns                   : {list(df.columns)}\n")

    sentiment_cols = ["symbol", "title", "sentiment_label", "sentiment_compound", "sentiment_model"]
    print(df[sentiment_cols].to_string(index=False))

    # basic assertions
    assert "sentiment_label"    in df.columns, "missing sentiment_label"
    assert "sentiment_score"    in df.columns, "missing sentiment_score"
    assert "sentiment_compound" in df.columns, "missing sentiment_compound"
    assert "sentiment_model"    in df.columns, "missing sentiment_model"
    assert df["sentiment_model"].iloc[0] == "finbert", "model should be finbert"

    print("\n✅ Step 3b passed — parquet contains sentiment columns correctly.\n")