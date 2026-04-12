from pathlib import Path
import pandas as pd

from app.features.correlation import build_correlation_matrix

SILVER_MARKET_PATH = "lakehouse/silver/market_data/data.parquet"
OUTPUT_DIR = "lakehouse/gold/correlation_matrix"
OUTPUT_FILE = "lakehouse/gold/correlation_matrix/data.parquet"


def main():
    df = pd.read_parquet(SILVER_MARKET_PATH)

    corr_df = build_correlation_matrix(df)

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    corr_df.to_parquet(OUTPUT_FILE, index=False)

    print("Correlation matrix saved to:", OUTPUT_FILE)
    print(corr_df.head(20))


if __name__ == "__main__":
    main()