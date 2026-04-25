"""
ML Backtester — Walk-Forward Strategy Simulation
=================================================
Simulates trading the BUY / SELL / HOLD signals on historical data
and produces an equity curve, trade log, and performance metrics.

Strategy:
    - Long-only (buy on BUY signal, exit on SELL or HOLD)
    - No leverage, no short selling
    - Transaction cost: 0.1% per trade (configurable)
    - Position sizing: 100% of capital per trade

Run from backend/:
    python -m app.ml.direction.backtest
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import GOLD_PATH
from app.ml.direction.trainer import (
    LABEL_MAP,
    ML_MODELS_DIR,
    GOLD_ML_FILE,
    GOLD_MARKET_FILE,
    add_technical_features,
    make_labels,
    get_feature_names,
)

logger = get_logger(__name__)

BACKTEST_RESULTS_DIR = ML_MODELS_DIR / "backtest"
BACKTEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRANSACTION_COST = 0.001   # 0.1 % per trade
INITIAL_CAPITAL  = 10_000.0


# ---------------------------------------------------------------------------
# Scaler helper (same NumpyScaler from predictor)
# ---------------------------------------------------------------------------

class NumpyScaler:
    """
    Scaler compatible with both old (mean_/scale_) and new (center_/scale_)
    artifact formats produced by v2/v3 trainer.
    """
    def __init__(self, center: list, scale: list) -> None:
        self.center_ = np.array(center, dtype=np.float32)
        self.scale_  = np.array(scale,  dtype=np.float32)

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.center_) / (self.scale_ + 1e-9)

    @classmethod
    def from_json(cls, path: Path) -> "NumpyScaler":
        import json
        data = json.loads(path.read_text())
        # Support both v2 (center_) and legacy (mean_) key names
        center = data.get("center_") or data.get("mean_", [])
        scale  = data.get("scale_", [])
        return cls(center, scale)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _compute_metrics(equity: pd.Series, returns: pd.Series) -> dict[str, float]:
    """Compute Sharpe, Max Drawdown, Win Rate, CAGR from equity curve."""
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1

    # Annualised Sharpe (daily returns, 252 trading days)
    daily_ret = equity.pct_change().dropna()
    sharpe = (
        float(daily_ret.mean() / (daily_ret.std() + 1e-9) * np.sqrt(252))
        if len(daily_ret) > 1 else 0.0
    )

    # Max drawdown
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / (roll_max + 1e-9)
    max_dd = float(drawdown.min())

    # Win rate on trades
    positive = (returns > 0).sum()
    total_trades = (returns != 0).sum()
    win_rate = float(positive / total_trades) if total_trades > 0 else 0.0

    # Approximate CAGR (assume daily bars)
    n_days = len(equity)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (252 / max(n_days, 1)) - 1)

    return {
        "total_return": round(float(total_return), 4),
        "cagr": round(cagr, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "win_rate": round(win_rate, 4),
        "n_trades": int(total_trades),
    }


# ---------------------------------------------------------------------------
# Per-symbol backtest
# ---------------------------------------------------------------------------

def backtest_symbol(
    symbol: str,
    df: pd.DataFrame,
    transaction_cost: float = TRANSACTION_COST,
    initial_capital: float = INITIAL_CAPITAL,
) -> dict[str, Any] | None:
    """
    Run a walk-forward backtest for one symbol.
    Uses the trained model to generate signals out-of-sample.
    """
    try:
        import json
        from xgboost import XGBClassifier
    except ImportError:
        logger.error("xgboost not installed")
        return None

    safe = symbol.replace("/", "_")
    model_path = ML_MODELS_DIR / f"{safe}_model.json"
    scaler_path = ML_MODELS_DIR / f"{safe}_scaler.json"

    if not model_path.exists():
        logger.warning(f"No model for {symbol}")
        return None

    import json
    model = XGBClassifier()
    model.load_model(str(model_path))
    scaler = NumpyScaler.from_json(scaler_path)

    # Load selected feature indices from scaler artifact
    scaler_meta = json.loads(scaler_path.read_text())
    sel_idx  = scaler_meta.get("selected_idx",  None)
    all_feat = scaler_meta.get("feature_names", None)

    # Feature engineering (v3 API)
    df = add_technical_features(df)
    df = make_labels(df)
    feat_names = all_feat if all_feat else get_feature_names(df)
    feat_names = [f for f in feat_names if f in df.columns]
    df = df.dropna(subset=feat_names + ["label"]).reset_index(drop=True)

    if len(df) < 30:
        return None

    # Out-of-sample: start from 20% mark
    oos_start = int(len(df) * 0.8)

    # --- Simulate trading ---------------------------------------------------
    capital = initial_capital
    in_position = False
    entry_price = 0.0
    equity_curve = []
    trade_returns = []
    signals_out = []

    for i in range(len(df)):
        row = df.iloc[[i]]
        X = row[feat_names].values.astype(np.float32)
        X_s = scaler.transform(X)
        # Apply feature selection if model was trained with subset
        if sel_idx is not None:
            X_s = X_s[:, sel_idx]

        proba = model.predict_proba(X_s)[0]
        pred = int(np.argmax(proba))
        signal = LABEL_MAP[pred]
        price = float(row["close"].iloc[0])

        trade_ret = 0.0

        if i >= oos_start:
            if signal == "BUY" and not in_position:
                # Enter long
                entry_price = price * (1 + transaction_cost)
                in_position = True

            elif signal == "SELL" and in_position:
                # Exit long
                exit_price = price * (1 - transaction_cost)
                trade_ret = (exit_price / entry_price) - 1
                capital *= (1 + trade_ret)
                in_position = False
                trade_returns.append(trade_ret)

            elif signal == "HOLD" and in_position:
                # Mark-to-market (no action)
                unrealised = (price / entry_price) - 1
                pass

        equity_curve.append(capital)
        signals_out.append(
            {
                "timestamp": str(df.iloc[i].get("timestamp", "")),
                "close": price,
                "signal": signal,
                "prob_buy": round(float(proba[2]), 4),
                "prob_hold": round(float(proba[1]), 4),
                "prob_sell": round(float(proba[0]), 4),
            }
        )

    # Close open position at end
    if in_position and len(df) > 0:
        last_price = float(df.iloc[-1]["close"]) * (1 - transaction_cost)
        trade_ret = (last_price / entry_price) - 1
        capital *= (1 + trade_ret)
        trade_returns.append(trade_ret)
        equity_curve[-1] = capital

    equity_series = pd.Series(equity_curve[oos_start:], dtype=float)
    returns_series = pd.Series(trade_returns, dtype=float)

    # Buy-and-hold baseline
    oos_df = df.iloc[oos_start:]
    if not oos_df.empty:
        bh_start = float(oos_df.iloc[0]["close"])
        bh_end = float(oos_df.iloc[-1]["close"])
        bh_return = (bh_end / bh_start) - 1
    else:
        bh_return = 0.0

    metrics = _compute_metrics(
        equity_series + 1e-9,
        returns_series,
    )
    metrics["buy_and_hold_return"] = round(bh_return, 4)
    metrics["alpha"] = round(metrics["total_return"] - bh_return, 4)

    result = {
        "symbol": symbol,
        "metrics": metrics,
        "equity_curve": equity_curve[oos_start:],   # oos only
        "signals": signals_out[oos_start:],
        "n_oos_bars": len(oos_df),
    }

    # Save
    out_path = BACKTEST_RESULTS_DIR / f"{safe}_backtest.json"
    import json
    out_path.write_text(json.dumps(result, indent=2, default=str))

    logger.info(
        f"Backtest complete for {symbol}",
        extra={
            "total_return": metrics["total_return"],
            "sharpe": metrics["sharpe"],
            "max_dd": metrics["max_drawdown"],
            "alpha": metrics["alpha"],
        },
    )
    return result


def backtest_all_crypto(gold_path: Path | None = None) -> dict[str, Any]:
    """Run backtests for all available crypto models."""
    if gold_path is None:
        gold_path = GOLD_ML_FILE if GOLD_ML_FILE.exists() else GOLD_MARKET_FILE

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold features not found: {gold_path}")

    df = pd.read_parquet(gold_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    crypto_df = df[df["market_type"] == "crypto"]

    results = {}
    for symbol in crypto_df["symbol"].unique():
        sym_df = crypto_df[crypto_df["symbol"] == symbol].copy()
        res = backtest_symbol(symbol, sym_df)
        if res:
            results[symbol] = res

    return results


def load_backtest_result(symbol: str) -> dict[str, Any] | None:
    """Load saved backtest result from disk."""
    import json
    safe = symbol.replace("/", "_")
    path = BACKTEST_RESULTS_DIR / f"{safe}_backtest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ML Backtester — Walk-Forward Strategy Simulation")
    print("=" * 70 + "\n")

    results = backtest_all_crypto()

    for symbol, res in results.items():
        m = res["metrics"]
        print(f"\n  📊 {symbol}")
        print(f"     Total Return    : {m['total_return']:+.2%}")
        print(f"     Buy-and-Hold    : {m['buy_and_hold_return']:+.2%}")
        print(f"     Alpha           : {m['alpha']:+.2%}")
        print(f"     Sharpe Ratio    : {m['sharpe']:.2f}")
        print(f"     Max Drawdown    : {m['max_drawdown']:.2%}")
        print(f"     Win Rate        : {m['win_rate']:.2%}")
        print(f"     Trades          : {m['n_trades']}")