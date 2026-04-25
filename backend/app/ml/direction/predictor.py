"""
ML Predictor v3 — News-Aware Ensemble Inference
=================================================
Loads the full v3 artifact set (XGBoost + LightGBM + RandomForest + calibrator)
and generates BUY / SELL / HOLD predictions from the latest Gold ML dataset
(market features + news sentiment).

Falls back gracefully:
  - When optional models (LGB, RF, calibrator) are absent
  - When news data is missing (uses market-only features)
  - When gold ml_dataset not built (falls back to market-only gold)

Gold data is refreshed every 5 minutes in memory.

Usage:
    from app.ml.direction.predictor import get_predictor

    pred = get_predictor().predict("bitcoin")
    # {
    #   "symbol": "bitcoin",
    #   "signal": "BUY",
    #   "probUp": 0.65,
    #   "probHold": 0.20,
    #   "probDown": 0.15,
    #   "confidence": 0.65,
    #   "news_sentiment": 0.34,
    #   "news_signal": "bullish",
    #   ...
    # }
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import GOLD_PATH

# Single source of truth for feature engineering
from app.ml.direction.trainer import (
    add_technical_features,
    get_feature_names,
    LABEL_MAP,
    ML_MODELS_DIR,
    GOLD_ML_FILE,
    GOLD_MARKET_FILE,
    NEWS_FEATURE_COLS,
)

logger = get_logger(__name__)

GOLD_CACHE_TTL_S = 300   # re-read Gold Parquet every 5 minutes


# ---------------------------------------------------------------------------
# Scaler (RobustScaler replica — no joblib dependency)
# ---------------------------------------------------------------------------

class RobustScalerNumpy:
    """Minimal RobustScaler that loads from the JSON artifact."""

    def __init__(self, center: list[float], scale: list[float]) -> None:
        self.center_ = np.array(center, dtype=np.float32)
        self.scale_  = np.array(scale,  dtype=np.float32)

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.center_) / (self.scale_ + 1e-9)

    @classmethod
    def from_json(cls, path: Path) -> "RobustScalerNumpy":
        d = json.loads(path.read_text())
        return cls(d["center_"], d["scale_"])


# ---------------------------------------------------------------------------
# Calibrator replica (Logistic Regression softmax)
# ---------------------------------------------------------------------------

class LogisticCalibrator:
    """Softmax calibrator loaded from JSON (no sklearn dependency at inference)."""

    def __init__(self, coef: list, intercept: list, classes: list) -> None:
        self.coef_      = np.array(coef,      dtype=np.float64)
        self.intercept_ = np.array(intercept, dtype=np.float64)
        self.classes_   = classes

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        logits = X @ self.coef_.T + self.intercept_
        e = np.exp(logits - logits.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    @classmethod
    def from_json(cls, path: Path) -> "LogisticCalibrator":
        d = json.loads(path.read_text())
        return cls(d["coef"], d["intercept"], d["classes"])


# ---------------------------------------------------------------------------
# News signal interpretation
# ---------------------------------------------------------------------------

def _interpret_news(sentiment: float, count: int) -> str:
    """Convert numeric sentiment to human-readable label."""
    if count == 0:
        return "no_news"
    if sentiment > 0.3:
        return "very_bullish"
    if sentiment > 0.1:
        return "bullish"
    if sentiment < -0.3:
        return "very_bearish"
    if sentiment < -0.1:
        return "bearish"
    return "neutral"


# ---------------------------------------------------------------------------
# Predictor
# ---------------------------------------------------------------------------

class CryptoPredictor:
    """
    Loads v3 model artifacts and generates predictions from live Gold features.
    All artifacts are lazy-loaded and cached in memory.
    Supports both market-only and market+news gold datasets.
    """

    def __init__(self) -> None:
        self._xgb_cache:     dict[str, Any] = {}
        self._lgb_cache:     dict[str, Any] = {}
        self._rf_cache:      dict[str, Any] = {}
        self._scaler_cache:  dict[str, RobustScalerNumpy] = {}
        self._cal_cache:     dict[str, LogisticCalibrator | None] = {}
        self._ensemble_info: dict[str, dict] = {}
        self._meta_cache:    dict[str, dict] = {}
        self._gold_df:       pd.DataFrame | None = None
        self._gold_ts:       pd.Timestamp | None = None
        self._gold_path:     Path = self._resolve_gold_path()

    @staticmethod
    def _resolve_gold_path() -> Path:
        if GOLD_ML_FILE.exists():
            return GOLD_ML_FILE
        return GOLD_MARKET_FILE

    # ------------------------------------------------------------------
    # Gold data loading
    # ------------------------------------------------------------------

    def _load_gold(self) -> pd.DataFrame:
        now   = pd.Timestamp.now(tz="UTC")
        stale = (
            self._gold_df is None
            or self._gold_ts is None
            or (now - self._gold_ts).total_seconds() > GOLD_CACHE_TTL_S
        )
        if stale:
            path = self._resolve_gold_path()
            if not path.exists():
                raise FileNotFoundError(
                    f"Gold data not found: {path}\n"
                    "Run: python -m app.etl.gold.build_gold_market  (and optionally build_gold_ml_dataset)"
                )
            df = pd.read_parquet(path)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            self._gold_df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
            self._gold_ts = now
        return self._gold_df  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Artifact loading (lazy + cached)
    # ------------------------------------------------------------------

    def _load_artifacts(self, symbol: str) -> bool:
        """Load all model artifacts for symbol. Returns False if primary model missing."""
        if symbol in self._xgb_cache:
            return True

        safe = symbol.replace("/", "_")

        # Primary XGBoost (required)
        model_path = ML_MODELS_DIR / f"{safe}_model.json"
        if not model_path.exists():
            return False

        try:
            from xgboost import XGBClassifier
            xgb = XGBClassifier()
            xgb.load_model(str(model_path))
            self._xgb_cache[symbol] = xgb
        except Exception as e:
            logger.error(f"[{symbol}] Failed to load XGBoost: {e}")
            return False

        # Scaler (required)
        scaler_path = ML_MODELS_DIR / f"{safe}_scaler.json"
        if not scaler_path.exists():
            return False
        self._scaler_cache[symbol] = RobustScalerNumpy.from_json(scaler_path)

        # Ensemble info
        ens_path = ML_MODELS_DIR / f"{safe}_ensemble.json"
        self._ensemble_info[symbol] = (
            json.loads(ens_path.read_text()) if ens_path.exists() else {}
        )

        # LightGBM (optional)
        lgb_path = ML_MODELS_DIR / f"{safe}_lgb.txt"
        self._lgb_cache[symbol] = None
        if lgb_path.exists():
            try:
                import lightgbm as lgb
                self._lgb_cache[symbol] = lgb.Booster(model_file=str(lgb_path))
            except Exception:
                pass

        # Random Forest (optional)
        rf_path = ML_MODELS_DIR / f"{safe}_rf.pkl"
        self._rf_cache[symbol] = None
        if rf_path.exists():
            try:
                with open(rf_path, "rb") as fh:
                    self._rf_cache[symbol] = pickle.load(fh)
            except Exception:
                pass

        # Calibrator (optional)
        cal_path = ML_MODELS_DIR / f"{safe}_calibrator.json"
        self._cal_cache[symbol] = (
            LogisticCalibrator.from_json(cal_path) if cal_path.exists() else None
        )

        # Metadata
        meta_path = ML_MODELS_DIR / f"{safe}_meta.json"
        self._meta_cache[symbol] = (
            json.loads(meta_path.read_text()) if meta_path.exists() else {}
        )

        logger.info(
            f"[{symbol}] Artifacts loaded",
            extra={
                "lgb": self._lgb_cache[symbol] is not None,
                "rf":  self._rf_cache[symbol] is not None,
                "cal": self._cal_cache[symbol] is not None,
            },
        )
        return True

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, symbol: str, n_lookback: int = 60) -> dict[str, Any]:
        """
        Return BUY / SELL / HOLD prediction for one crypto symbol.

        Args:
            symbol:     lowercase CoinGecko id, e.g. "bitcoin"
            n_lookback: recent rows to keep for lag feature computation
        """
        if not self._load_artifacts(symbol):
            return self._fallback(symbol, "model_not_found")

        try:
            df_gold = self._load_gold()
            sym_df  = df_gold[df_gold["symbol"] == symbol].copy()
            if sym_df.empty:
                return self._fallback(symbol, "no_gold_data")

            # Use recent window + safety buffer for lag computation
            sym_df = sym_df.tail(n_lookback + 30).copy()
            sym_df = add_technical_features(sym_df)

            feat_names = get_feature_names(sym_df)
            sym_df = sym_df.dropna(subset=feat_names)
            if sym_df.empty:
                return self._fallback(symbol, "no_valid_features")

            latest     = sym_df.iloc[[-1]]
            scaler     = self._scaler_cache[symbol]
            ens_info   = self._ensemble_info.get(symbol, {})
            sel        = ens_info.get("selected_idx") or list(range(len(feat_names)))

            X_raw    = latest[feat_names].values.astype(np.float32)
            X_scaled = scaler.transform(X_raw)
            X_sel    = X_scaled[:, sel]

            # Collect probabilities from each available model
            probas: list[np.ndarray] = []

            # XGBoost
            xgb_p = self._xgb_cache[symbol].predict_proba(X_sel)
            probas.append(xgb_p)

            # LightGBM (raw booster)
            lgb_booster = self._lgb_cache.get(symbol)
            if lgb_booster is not None:
                try:
                    raw = lgb_booster.predict(X_sel)
                    if raw.ndim == 1:
                        raw = raw.reshape(1, -1)
                    probas.append(raw)
                except Exception:
                    pass

            # Random Forest
            rf = self._rf_cache.get(symbol)
            if rf is not None:
                try:
                    probas.append(rf.predict_proba(X_sel))
                except Exception:
                    pass

            # Average ensemble
            avg_proba = np.mean(probas, axis=0)   # shape (1, 3)

            # Calibrate
            cal = self._cal_cache.get(symbol)
            if cal is not None:
                try:
                    avg_proba = cal.predict_proba(avg_proba)
                except Exception:
                    pass

            proba    = avg_proba[0]   # [sell, hold, buy]
            pred_cls = int(np.argmax(proba))
            signal   = LABEL_MAP[pred_cls]
            conf     = float(proba[pred_cls])

            meta = self._meta_cache.get(symbol, {})
            top_features = [
                {"name": n, "weight": round(w, 4)}
                for n, w in (meta.get("feature_importances") or [])[:5]
            ]
            top_news_features = [
                {"name": n, "weight": round(w, 4)}
                for n, w in (meta.get("news_feature_importances") or [])[:5]
            ]

            # Extract latest news info for the response
            news_sentiment = self._get_latest_news_info(latest)

            return {
                # Core prediction
                "symbol":           symbol,
                "signal":           signal,
                "probUp":           round(float(proba[2]), 4),
                "probHold":         round(float(proba[1]), 4),
                "probDown":         round(float(proba[0]), 4),
                "confidence":       round(conf, 4),

                # Model metadata
                "model_version":    meta.get("model_version", "xgb-v3.0"),
                "ensemble_types":   meta.get("ensemble_types", ["xgb"]),
                "n_features":       meta.get("n_features_selected"),
                "test_accuracy":    meta.get("test_accuracy"),
                "test_f1_macro":    meta.get("test_f1_macro"),
                "cv_accuracy":      (meta.get("cv_metrics") or {}).get("cv_accuracy"),
                "cv_f1_macro":      (meta.get("cv_metrics") or {}).get("cv_f1_macro"),

                # Feature importances
                "top_features":          top_features,
                "top_news_features":     top_news_features,
                "n_news_features":       len(meta.get("news_features_selected") or []),

                # News signals
                "news_sentiment":   news_sentiment.get("score"),
                "news_signal":      news_sentiment.get("signal"),
                "news_count":       news_sentiment.get("count"),
                "news_sent_ma3":    news_sentiment.get("sent_ma3"),

                # Market snapshot
                "latest_timestamp": str(latest["timestamp"].iloc[0]),
                "latest_close":     float(latest["close"].iloc[0]),
                "latest_rsi":       round(float(latest["rsi"].iloc[0]), 2),
                "latest_macd":      round(float(latest["macd"].iloc[0]), 4),

                "error": None,
            }

        except Exception as exc:
            logger.error(f"[{symbol}] Prediction error", extra={"error": str(exc)})
            return self._fallback(symbol, str(exc))

    @staticmethod
    def _get_latest_news_info(latest: pd.DataFrame) -> dict:
        """Extract news-related values from the latest row."""
        score = float(latest["sentiment_score"].iloc[0]) if "sentiment_score" in latest.columns else 0.0
        count = int(latest["news_count"].iloc[0]) if "news_count" in latest.columns else 0
        ma3   = float(latest["sent_ma3"].iloc[0]) if "sent_ma3" in latest.columns else 0.0
        return {
            "score":    round(score, 4),
            "signal":   _interpret_news(score, count),
            "count":    count,
            "sent_ma3": round(ma3, 4),
        }

    def predict_all(self) -> list[dict[str, Any]]:
        return [self.predict(s) for s in self.list_available_models()]

    def list_available_models(self) -> list[str]:
        return [p.stem.replace("_model", "")
                for p in ML_MODELS_DIR.glob("*_model.json")]

    @staticmethod
    def _fallback(symbol: str, reason: str) -> dict[str, Any]:
        return {
            "symbol": symbol, "signal": "HOLD",
            "probUp": 0.33, "probHold": 0.34, "probDown": 0.33,
            "confidence": 0.34, "model_version": "fallback",
            "ensemble_types": [], "n_features": None,
            "test_accuracy": None, "test_f1_macro": None,
            "cv_accuracy": None, "cv_f1_macro": None,
            "top_features": [], "top_news_features": [], "n_news_features": 0,
            "news_sentiment": None, "news_signal": "no_news",
            "news_count": 0, "news_sent_ma3": None,
            "latest_timestamp": None, "latest_close": None,
            "latest_rsi": None, "latest_macd": None,
            "error": reason,
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_predictor: CryptoPredictor | None = None


def get_predictor() -> CryptoPredictor:
    global _predictor
    if _predictor is None:
        _predictor = CryptoPredictor()
    return _predictor


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ML Predictor v3 — News-Aware Ensemble Inference")
    print("=" * 70 + "\n")

    p = CryptoPredictor()
    for sym in p.list_available_models():
        r = p.predict(sym)
        if r["error"]:
            print(f"  ❌ {sym}: {r['error']}")
        else:
            print(
                f"  📈 {sym}: {r['signal']}  "
                f"conf={r['confidence']:.2%}  "
                f"up={r['probUp']:.2%}  hold={r['probHold']:.2%}  down={r['probDown']:.2%}  "
                f"news={r['news_signal']} ({r['news_sentiment']:+.3f})  "
                f"ensemble={r['ensemble_types']}"
            )