from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import SEED_DATA_PATH
from app.config.assets import METALS_ASSETS
from app.ingestion.batch.base_ingestor import BaseIngestor
from app.etl.bronze.write_bronze import write_bronze_table

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Where to put your CSV files
# ------------------------------------------------------------------
METALS_CSV_DIR = Path(SEED_DATA_PATH) / "metals"

# Map display_symbol → CSV filename (no extension)
SYMBOL_TO_CSV: dict[str, str] = {
    "XAU/USD": "XAU_USD",
    "XAG/USD": "XAG_USD",
}

# Flexible column aliases → our standard name
_COL_ALIASES: dict[str, list[str]] = {
    "timestamp": ["date", "datetime", "time", "timestamp"],
    "open":      ["open"],
    "high":      ["high"],
    "low":       ["low"],
    "close":     ["close", "price", "adj close", "adj_close"],
    "volume":    ["volume", "vol"],
}


def _sniff_csv_sep(csv_path: Path) -> str:
    """Use ``;`` when the header is semicolon-separated (common in EU exports)."""
    with csv_path.open(encoding="utf-8", errors="replace") as f:
        first = f.readline()
    if not first.strip():
        return ","
    return ";" if first.count(";") > first.count(",") else ","


def _read_metals_csv(csv_path: Path) -> pd.DataFrame:
    sep = _sniff_csv_sep(csv_path)
    return pd.read_csv(csv_path, sep=sep, encoding="utf-8", encoding_errors="replace")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw CSV columns to our standard names (case-insensitive)."""
    lower_map = {c.lower().strip(): c for c in df.columns}
    rename: dict[str, str] = {}
    for standard, aliases in _COL_ALIASES.items():
        for alias in aliases:
            if alias in lower_map and standard not in rename.values():
                rename[lower_map[alias]] = standard
                break
    return df.rename(columns=rename)


def _validate_columns(df: pd.DataFrame, symbol: str) -> bool:
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        logger.warning(
            "CSV missing required columns",
            extra={"symbol": symbol, "missing": list(missing)},
        )
        return False
    return True


class MetalsCsvIngestor(BaseIngestor):
    """
    Loads metals OHLCV data from local CSV files into Bronze.

    Raises FileNotFoundError if a CSV is missing — no silent fallback,
    as per project requirements (CSV-only, no API fallback).
    """

    def __init__(self, csv_dir: Optional[Path] = None) -> None:
        super().__init__(source_name="metals_csv")
        self.csv_dir = Path(csv_dir) if csv_dir else METALS_CSV_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> pd.DataFrame:
        """
        Load all metals assets defined in assets.py from CSV.
        Returns a combined DataFrame ready for Bronze.
        """
        frames: list[pd.DataFrame] = []

        for asset in METALS_ASSETS:
            display_symbol: str = asset["display_symbol"]
            df = self._load_single(asset)
            if df is not None and not df.empty:
                frames.append(df)
            else:
                logger.warning(
                    "No data loaded for symbol",
                    extra={"display_symbol": display_symbol},
                )

        if not frames:
            raise RuntimeError(
                "No metals data loaded. Check CSV files in: " + str(self.csv_dir)
            )

        combined = pd.concat(frames, ignore_index=True)
        self.logger.info(
            "Metals CSV ingestion complete",
            extra={"total_rows": len(combined)},
        )
        return combined

    def ingest(self, mode: str = "overwrite") -> None:
        """Fetch → write to Bronze metals_prices table."""
        df = self.fetch()
        write_bronze_table(df, dataset_name="metals_prices", mode=mode)  # type: ignore[arg-type]
        self.logger.info(
            "Metals data written to Bronze",
            extra={"rows": len(df), "mode": mode},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_single(self, asset: dict) -> Optional[pd.DataFrame]:
        display_symbol: str = asset["display_symbol"]
        symbol: str = asset["symbol"]
        market_type: str = asset["market_type"]
        source: str = asset["source"]

        csv_stem = SYMBOL_TO_CSV.get(display_symbol)
        if csv_stem is None:
            logger.warning(
                "No CSV mapping for symbol",
                extra={"display_symbol": display_symbol},
            )
            return None

        csv_path = self.csv_dir / f"{csv_stem}.csv"

        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV not found for {display_symbol}: {csv_path}\n"
                f"Place your file at: {csv_path}"
            )

        self.logger.info(
            "Reading metals CSV",
            extra={"symbol": display_symbol, "path": str(csv_path)},
        )

        try:
            raw = _read_metals_csv(csv_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to read CSV for {display_symbol}: {exc}"
            ) from exc

        df = _normalize_columns(raw)

        if not _validate_columns(df, display_symbol):
            raise ValueError(
                f"CSV for {display_symbol} is missing required columns. "
                f"Found: {list(df.columns)}"
            )

        # Parse timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        invalid_ts = df["timestamp"].isna().sum()
        if invalid_ts > 0:
            logger.warning(
                "Dropping rows with unparseable timestamps",
                extra={"symbol": display_symbol, "count": int(invalid_ts)},
            )
            df = df[df["timestamp"].notna()].copy()

        # Cast OHLCV to float
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if "volume" not in df.columns:
            df["volume"] = None  # allowed for metals per settings.py

        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        # Add standard metadata columns
        df["symbol"] = symbol
        df["display_symbol"] = display_symbol
        df["market_type"] = market_type
        df["source"] = source
        df["ingestion_time"] = self.get_ingestion_time().isoformat()

        # Keep only Bronze schema columns (in order)
        bronze_cols = [
            "symbol", "display_symbol", "market_type", "source",
            "timestamp", "open", "high", "low", "close", "volume",
            "ingestion_time",
        ]
        df = df[[c for c in bronze_cols if c in df.columns]]

        # Drop rows with null OHLC
        before = len(df)
        df = df.dropna(subset=["open", "high", "low", "close"])
        dropped = before - len(df)
        if dropped:
            logger.warning(
                "Dropped rows with null OHLC",
                extra={"symbol": display_symbol, "dropped": dropped},
            )

        self.logger.info(
            "Metals CSV loaded",
            extra={"symbol": display_symbol, "rows": len(df)},
        )
        return df


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    ingestor = MetalsCsvIngestor()
    ingestor.ingest(mode="overwrite")