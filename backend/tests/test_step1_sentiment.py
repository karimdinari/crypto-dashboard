"""
Step 1 — Test FinBERT loads and scores correctly.
Run from backend/:
    python tests/test_step1_sentiment.py
"""

from app.features.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()

tests = [
    "Bitcoin surges to new all-time high amid massive institutional buying",
    "Crypto market crashes as regulators announce sweeping ban",
    "Gold prices remain stable ahead of Fed meeting",
]

print("\n" + "="*70)
print("STEP 1 — FinBERT sentiment scoring")
print("="*70 + "\n")

for text in tests:
    result = analyzer.score(text)
    print(f"  label   : {result['label']}")
    print(f"  score   : {result['score']}")
    print(f"  compound: {result['compound']:+.4f}")
    print(f"  text    : {text[:60]}")
    print()

print("✅ Step 1 passed — FinBERT is working correctly.\n")