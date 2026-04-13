import pandas as pd


def build_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a 1-year cross-asset correlation matrix using daily close prices.
    Returns unique long format:
    symbol_1 | symbol_2 | correlation_value
    """

    df = df[["symbol", "timestamp", "close"]].copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    df = df.dropna(subset=["symbol", "timestamp", "close"])

    max_ts = df["timestamp"].max()
    start_ts = max_ts - pd.Timedelta(days=365)
    df = df[df["timestamp"] >= start_ts].copy()

    df["date"] = df["timestamp"].dt.date
    df = (
        df.sort_values("timestamp")
        .groupby(["symbol", "date"], as_index=False)
        .last()
    )

    pivot_df = df.pivot_table(
        index="date",
        columns="symbol",
        values="close",
        aggfunc="mean",
    )

    corr_matrix = pivot_df.corr()

    records = []
    symbols = list(corr_matrix.columns)

    for i, symbol_1 in enumerate(symbols):
        for j, symbol_2 in enumerate(symbols):
            if i < j:
                records.append(
                    {
                        "symbol_1": symbol_1,
                        "symbol_2": symbol_2,
                        "correlation_value": corr_matrix.loc[symbol_1, symbol_2],
                    }
                )

    result = pd.DataFrame(records)
    result["abs_corr"] = result["correlation_value"].abs()
    result = result.sort_values("abs_corr", ascending=False).drop(columns=["abs_corr"])

    return result