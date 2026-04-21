from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from app.config.assets import CRYPTO_ASSETS
from app.config.logging_config import get_logger
from app.config.settings import SEED_DATA_PATH
from app.ingestion.batch.base_ingestor import BaseIngestor

logger = get_logger(__name__)

CRYPTO_CSV_DIR = Path(SEED_DATA_PATH)

SYMBOL_TO_CSV: dict[str, Path] = {
    "bitcoin": Path("bitcoin") / "bitcoin.csv",
    "ethereum": Path("ethereum") / "ethereum.csv",
}

_REQUIRED_COLS = {"date", "price", "total_volume", "market_cap", "coin_name"}


class CryptoCsvIngestor(BaseIngestor):
    """Load static crypto history from local seed CSV files."""

    def __init__(self, csv_dir: Optional[Path] = None, symbols: Optional[list[str]] = None) -> None:
        super().__init__(source_name="crypto_csv")
        self.csv_dir = Path(csv_dir) if csv_dir else CRYPTO_CSV_DIR

        if symbols:
            wanted = {s.lower() for s in symbols}
            self.assets = [asset for asset in CRYPTO_ASSETS if asset.get("symbol", "").lower() in wanted]
        else:
            self.assets = CRYPTO_ASSETS

    def fetch(self) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []

        for asset in self.assets:
            df = self._load_single(asset)
            if df is not None and not df.empty:
                frames.append(df)

        if not frames:
            raise RuntimeError(f"No crypto CSV data loaded from: {self.csv_dir}")

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.drop_duplicates(subset=["symbol", "timestamp"], keep="last")
        combined = combined.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

        self.logger.info(
            "Crypto CSV ingestion complete",
            extra={"rows": len(combined), "symbols": [a["symbol"] for a in self.assets]},
        )
        return combined

    def _load_single(self, asset: dict) -> Optional[pd.DataFrame]:
        symbol = asset["symbol"]
        csv_rel_path = SYMBOL_TO_CSV.get(symbol)
        if csv_rel_path is None:
            logger.warning("No CSV mapping for crypto symbol", extra={"symbol": symbol})
            return None

        csv_path = self.csv_dir / csv_rel_path
        if not csv_path.exists():
            logger.warning("Crypto CSV file missing", extra={"symbol": symbol, "path": str(csv_path)})
            return None

        df = pd.read_csv(csv_path)
        missing = _REQUIRED_COLS - set(df.columns)
        if missing:
            logger.warning(
                "Crypto CSV missing required columns",
                extra={"symbol": symbol, "missing": sorted(missing), "path": str(csv_path)},
            )
            return None

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
        out["price"] = pd.to_numeric(df["price"], errors="coerce")
        out["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce")
        out["total_volume"] = pd.to_numeric(df["total_volume"], errors="coerce")

        out["symbol"] = symbol
        out["display_symbol"] = asset["display_symbol"]
        out["market_type"] = "crypto"
        out["source"] = self.source_name
        out["ingestion_time"] = self.get_ingestion_time().isoformat()

        out = out.dropna(subset=["timestamp", "price"])
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        out["timestamp"] = out["timestamp"].str.replace(r"([+-]\d{2})(\d{2})$", r"\1:\2", regex=True)

        bronze_cols = [
            "symbol",
            "display_symbol",
            "market_type",
            "timestamp",
            "source",
            "price",
            "market_cap",
            "total_volume",
            "ingestion_time",
        ]
        out = out[bronze_cols]

        self.logger.info(
            "Loaded crypto CSV",
            extra={"symbol": symbol, "rows": len(out), "path": str(csv_path)},
        )
        return out
