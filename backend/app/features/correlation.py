import pandas as pd


def build_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build cross-asset correlation matrix using close prices.
    Returns a long-format dataframe:
    symbol_1 | symbol_2 | correlation_value
    """

    pivot_df = df.pivot_table(
        index="timestamp",
        columns="symbol",
        values="close",
        aggfunc="mean",
    )

    corr_matrix = pivot_df.corr()

    records = []
    for symbol_1 in corr_matrix.index:
        for symbol_2 in corr_matrix.columns:
            records.append(
                {
                    "symbol_1": symbol_1,
                    "symbol_2": symbol_2,
                    "correlation_value": corr_matrix.loc[symbol_1, symbol_2],
                }
            )

    return pd.DataFrame(records)