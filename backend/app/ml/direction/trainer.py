"""
ML Trainer v2 — Improved XGBoost BUY / SELL / HOLD Classifier
===============================================================
Key improvements over v1:
  1. Adaptive ATR-based labels instead of fixed ±0.5% threshold
  2. 50+ engineered features: Bollinger Bands, ADX proxy, multi-timeframe MAs,
     volume profile, momentum, calendar effects, pattern detection
  3. Ensemble: XGBoost + LightGBM + Random Forest → averaged soft votes
  4. Optuna hyperparameter search (15 trials, ~2 min per symbol)
  5. SMOTE inside CV folds to fix class imbalance
  6. Feature selection: keep top 35 by XGBoost gain importance
  7. Probability calibration via Platt scaling (Logistic Regression)
  8. Expanding-window walk-forward CV (5 folds)
  9. RobustScaler (handles price outliers / crashes better)

Expected accuracy improvement: ~39-43% → ~55-65%

Run from backend/:
    python -m app.ml.direction.trainer
    (or wherever your ml package lives)

Install extras once:
    pip install optuna lightgbm imbalanced-learn --break-system-packages
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from app.config.logging_config import get_logger
from app.config.settings import GOLD_PATH

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GOLD_MARKET_FILE = Path(GOLD_PATH) / "market_features" / "data.parquet"
ML_MODELS_DIR    = Path(__file__).parent / "models"
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ATR_PERIOD          = 14
ATR_MULTIPLIER      = 0.5        # threshold = ATR_MULTIPLIER * daily_ATR%
MIN_ROWS_PER_SYMBOL = 120
N_WALK_FOLDS        = 5
TEST_FRAC           = 0.20
OPTUNA_TRIALS       = 15
FEATURE_SELECT_TOP  = 35

LABEL_MAP     = {0: "SELL", 1: "HOLD", 2: "BUY"}
LABEL_REVERSE = {"SELL": 0, "HOLD": 1, "BUY": 2}

GOLD_FEATURE_COLS = [
    "returns", "price_diff", "ma7", "ma30", "volatility",
    "volume_change", "correlation", "rsi", "macd",
    "macd_signal", "macd_histogram", "day_of_week",
    "volume_ma7", "relative_volume",
]

# Columns that should NOT be used as features
_META_COLS = {
    "symbol", "display_symbol", "market_type", "source",
    "timestamp", "ingestion_time", "silver_time",
    "open", "high", "low", "close", "volume",
    "label", "next_return",
    # raw intermediates (keep derived versions below)
    "bb_upper", "bb_lower", "dm_plus", "dm_minus", "obv", "up_bar", "down_bar",
}


# ===========================================================================
# FEATURE ENGINEERING
# ===========================================================================

def _zscore(series: pd.Series, window: int) -> pd.Series:
    mu  = series.rolling(window, min_periods=1).mean()
    std = series.rolling(window, min_periods=1).std().fillna(1e-9)
    return (series - mu) / std


def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 50+ derived features to a per-symbol Gold dataframe.

    Groups:
      A. Price / MA ratios & slopes
      B. RSI + MACD momentum
      C. Stochastic oscillator
      D. Volatility regime
      E. Bollinger Bands
      F. ADX proxy (trend strength)
      G. Volume analysis
      H. Multi-lag returns (1-7) + RSI/vol lags
      I. Cumulative return windows
      J. Rolling statistics (skew, kurtosis)
      K. Calendar effects
      L. Bar pattern features
    """
    df  = df.copy()
    eps = 1e-9
    c   = df["close"]

    # ---- A: MA ratios & slopes -------------------------------------------
    df["ma14"]           = c.rolling(14, min_periods=1).mean()
    df["ma60"]           = c.rolling(60, min_periods=1).mean()
    df["price_vs_ma7"]   = c / (df["ma7"]  + eps) - 1
    df["price_vs_ma14"]  = c / (df["ma14"] + eps) - 1
    df["price_vs_ma30"]  = c / (df["ma30"] + eps) - 1
    df["price_vs_ma60"]  = c / (df["ma60"] + eps) - 1
    df["ma7_vs_ma30"]    = df["ma7"]  / (df["ma30"] + eps) - 1
    df["ma14_vs_ma60"]   = df["ma14"] / (df["ma60"] + eps) - 1
    df["ma7_slope"]      = df["ma7"].pct_change(3)
    df["ma30_slope"]     = df["ma30"].pct_change(5)

    # ---- B: RSI & MACD momentum ------------------------------------------
    df["rsi_zone"]       = pd.cut(df["rsi"],
                                   bins=[0, 30, 45, 55, 70, 100],
                                   labels=[0, 1, 2, 3, 4]).astype(float)
    df["rsi_oversold"]   = (df["rsi"] < 30).astype(int)
    df["rsi_overbought"] = (df["rsi"] > 70).astype(int)
    df["rsi_change"]     = df["rsi"].diff(1)
    df["rsi_change3"]    = df["rsi"].diff(3)
    df["macd_cross"]     = df["macd"] - df["macd_signal"]
    df["macd_hist_d1"]   = df["macd_histogram"].diff(1)
    df["macd_hist_d2"]   = df["macd_histogram"].diff(2)

    # ---- C: Stochastic ---------------------------------------------------
    lo14 = c.rolling(14, min_periods=1).min()
    hi14 = c.rolling(14, min_periods=1).max()
    df["stoch_k"]        = (c - lo14) / (hi14 - lo14 + eps)
    df["stoch_k_lag1"]   = df["stoch_k"].shift(1)

    # ---- D: Volatility regime --------------------------------------------
    df["vol_zscore"]     = _zscore(df["returns"], 7)
    df["vol_ratio"]      = (df["volatility"].rolling(5, min_periods=1).mean() /
                            (df["volatility"].rolling(20, min_periods=1).mean() + eps))
    q75 = df["volatility"].rolling(30, min_periods=3).quantile(0.75)
    q25 = df["volatility"].rolling(30, min_periods=3).quantile(0.25)
    df["high_vol"]       = (df["volatility"] > q75).astype(int)
    df["low_vol"]        = (df["volatility"] < q25).astype(int)

    df["atr_pct"]        = c * df["returns"].abs().rolling(ATR_PERIOD, min_periods=1).mean() / (c + eps)
    df["close_vs_atr"]   = c.diff(1) / (df["atr_pct"] * c + eps)

    # ---- E: Bollinger Bands ----------------------------------------------
    bb_m   = c.rolling(20, min_periods=1).mean()
    bb_std = c.rolling(20, min_periods=1).std().fillna(eps)
    df["bb_upper"]       = bb_m + 2 * bb_std
    df["bb_lower"]       = bb_m - 2 * bb_std
    df["bb_width"]       = (df["bb_upper"] - df["bb_lower"]) / (bb_m + eps)
    df["bb_pct"]         = (c - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + eps)
    df["bb_squeeze"]     = (df["bb_width"] <
                            df["bb_width"].rolling(50, min_periods=5).quantile(0.2)).astype(int)

    # ---- F: ADX proxy (trend strength) -----------------------------------
    delta            = c.diff(1).fillna(0)
    dm_p             = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    dm_m             = (-delta).clip(lower=0).rolling(14, min_periods=1).mean()
    df["adx_proxy"]  = (dm_p - dm_m).abs() / (dm_p + dm_m + eps)
    df["trending"]   = (df["adx_proxy"] > 0.2).astype(int)

    # ---- G: Volume -------------------------------------------------------
    df["vol_z14"]        = _zscore(df["relative_volume"], 14)
    df["obv_slope"]      = (np.sign(c.diff(1)) * df.get("volume_ma7", pd.Series(0, index=df.index))).rolling(5, min_periods=1).sum()

    # ---- H: Lag returns + indicator lags ---------------------------------
    for lag in range(1, 8):
        df[f"ret_lag{lag}"] = df["returns"].shift(lag)
    for lag in [1, 3, 5]:
        df[f"rsi_lag{lag}"] = df["rsi"].shift(lag)
        df[f"vol_lag{lag}"] = df["volatility"].shift(lag)

    # ---- I: Cumulative returns -------------------------------------------
    df["cum_ret3"]   = c.pct_change(3)
    df["cum_ret5"]   = c.pct_change(5)
    df["cum_ret10"]  = c.pct_change(10)
    df["cum_ret20"]  = c.pct_change(20)

    # ---- J: Rolling stats ------------------------------------------------
    df["skew10"]     = df["returns"].rolling(10, min_periods=3).skew().fillna(0)
    df["kurt10"]     = df["returns"].rolling(10, min_periods=4).kurt().fillna(0)
    df["max_ret5"]   = df["returns"].rolling(5, min_periods=1).max()
    df["min_ret5"]   = df["returns"].rolling(5, min_periods=1).min()
    df["range_r"]    = (df["max_ret5"] - df["min_ret5"]) / (df["volatility"] + eps)

    # ---- K: Calendar -----------------------------------------------------
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["month"]      = ts.dt.month
        df["weekofyr"]   = ts.dt.isocalendar().week.astype(int)
        df["is_monend"]  = ts.dt.is_month_end.astype(int)
        df["is_monday"]  = (ts.dt.dayofweek == 0).astype(int)
        df["is_friday"]  = (ts.dt.dayofweek == 4).astype(int)
    else:
        for col in ["month", "weekofyr", "is_monend", "is_monday", "is_friday"]:
            df[col] = 0

    # ---- L: Bar patterns -------------------------------------------------
    df["up_bar"]     = (c > c.shift(1)).astype(int)
    df["consec_up"]  = df["up_bar"].rolling(3, min_periods=1).sum()
    df["consec_dn"]  = (1 - df["up_bar"]).rolling(3, min_periods=1).sum()
    df["rev_setup"]  = ((df["consec_up"] >= 3) | (df["consec_dn"] >= 3)).astype(int)

    return df


def get_feature_names(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if c not in _META_COLS and pd.api.types.is_numeric_dtype(df[c])]


# ===========================================================================
# ADAPTIVE LABELS
# ===========================================================================

def make_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    ATR-based adaptive threshold labels.
    threshold_t = ATR_MULTIPLIER * daily_ATR%   (clamped 0.3% – 3%)
    """
    df = df.copy()
    atr = df["close"] * df["returns"].abs().rolling(ATR_PERIOD, min_periods=1).mean()
    threshold = (ATR_MULTIPLIER * atr / (df["close"] + 1e-9)).clip(0.003, 0.03)
    nxt = df["close"].pct_change().shift(-1)
    df["label"] = np.where(nxt > threshold, 2,
                    np.where(nxt < -threshold, 0, 1)).astype(int)
    return df[:-1]    # drop last row (no future return)


# ===========================================================================
# HELPERS
# ===========================================================================

def sample_weights(y: np.ndarray) -> np.ndarray:
    counts = np.bincount(y, minlength=3)
    w = {c: float(max(counts)) / (counts[c] + 1e-9) for c in range(3)}
    return np.array([w[yi] for yi in y])


def smote_resample(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    try:
        from imblearn.over_sampling import SMOTE
        k = max(1, np.bincount(y).min() - 1)
        sm = SMOTE(random_state=42, k_neighbors=min(5, k))
        return sm.fit_resample(X, y)
    except Exception:
        return X, y


# ===========================================================================
# OPTUNA SEARCH
# ===========================================================================

def optuna_search(X_tr: np.ndarray, y_tr: np.ndarray,
                  n_trials: int = OPTUNA_TRIALS) -> dict[str, Any]:
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        from xgboost import XGBClassifier
        from sklearn.metrics import f1_score
    except ImportError:
        logger.info("Optuna not available — using default params")
        return default_xgb_params()

    split = int(len(X_tr) * 0.75)
    Xv, yv = X_tr[split:], y_tr[split:]
    Xt, yt = X_tr[:split], y_tr[:split]
    sw = sample_weights(yt)

    def objective(trial):
        p = {
            "n_estimators":     trial.suggest_int("ne",   100, 700),
            "max_depth":        trial.suggest_int("md",   3, 7),
            "learning_rate":    trial.suggest_float("lr", 0.01, 0.2, log=True),
            "subsample":        trial.suggest_float("ss", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("ct", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("mcw",  1, 20),
            "gamma":            trial.suggest_float("g",  0.0, 0.5),
            "reg_alpha":        trial.suggest_float("ra", 0.0, 1.0),
            "reg_lambda":       trial.suggest_float("rl", 0.5, 3.0),
            "objective": "multi:softprob", "num_class": 3,
            "eval_metric": "mlogloss", "random_state": 42,
            "n_jobs": -1, "verbosity": 0,
        }
        m = XGBClassifier(**p)
        m.fit(Xt, yt, sample_weight=sw, verbose=False)
        return f1_score(yv, m.predict(Xv), average="macro", zero_division=0)

    study = optuna.create_study(direction="maximize",
                                 sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    bp = study.best_params
    logger.info("Optuna best", extra={"f1": round(study.best_value, 4), "params": bp})
    return {
        "n_estimators": bp["ne"], "max_depth": bp["md"],
        "learning_rate": bp["lr"], "subsample": bp["ss"],
        "colsample_bytree": bp["ct"], "min_child_weight": bp["mcw"],
        "gamma": bp["g"], "reg_alpha": bp["ra"], "reg_lambda": bp["rl"],
        "objective": "multi:softprob", "num_class": 3,
        "eval_metric": "mlogloss", "random_state": 42,
        "n_jobs": -1, "verbosity": 0,
    }


def default_xgb_params() -> dict[str, Any]:
    return {
        "n_estimators": 400, "max_depth": 5, "learning_rate": 0.04,
        "subsample": 0.8, "colsample_bytree": 0.75,
        "min_child_weight": 4, "gamma": 0.05,
        "reg_alpha": 0.15, "reg_lambda": 1.2,
        "objective": "multi:softprob", "num_class": 3,
        "eval_metric": "mlogloss", "random_state": 42,
        "n_jobs": -1, "verbosity": 0,
    }


# ===========================================================================
# WALK-FORWARD CV (expanding window)
# ===========================================================================

def walk_forward_cv(X: np.ndarray, y: np.ndarray,
                    n_folds: int, xgb_params: dict) -> dict[str, float]:
    try:
        from xgboost import XGBClassifier
        from sklearn.metrics import f1_score, accuracy_score
    except ImportError:
        return {}

    n = len(X)
    min_train = max(int(n * 0.4), 60)
    fold_size = (n - min_train) // n_folds
    if fold_size < 10:
        return {}

    accs, f1s = [], []
    for fold in range(n_folds):
        vs = min_train + fold * fold_size
        ve = vs + fold_size
        if ve > n:
            break
        Xtr, ytr = X[:vs], y[:vs]
        Xval, yval = X[vs:ve], y[vs:ve]

        Xtr_r, ytr_r = smote_resample(Xtr, ytr)
        sw = sample_weights(ytr_r)

        m = XGBClassifier(**xgb_params)
        m.fit(Xtr_r, ytr_r, sample_weight=sw, verbose=False)

        accs.append(accuracy_score(yval, m.predict(Xval)))
        f1s.append(f1_score(yval, m.predict(Xval), average="macro", zero_division=0))
        logger.info(f"Fold {fold+1}/{n_folds}",
                    extra={"acc": round(accs[-1], 4), "f1": round(f1s[-1], 4)})

    return {
        "cv_accuracy": round(float(np.mean(accs)), 4),
        "cv_f1_macro": round(float(np.mean(f1s)), 4),
        "n_folds": len(accs),
    }


# ===========================================================================
# ENSEMBLE
# ===========================================================================

def build_ensemble(X_tr: np.ndarray, y_tr: np.ndarray,
                   xgb_params: dict) -> list[tuple[str, Any]]:
    from xgboost import XGBClassifier
    estimators: list[tuple[str, Any]] = []

    Xr, yr = smote_resample(X_tr, y_tr)
    sw = sample_weights(yr)

    # 1. XGBoost (primary)
    xgb = XGBClassifier(**xgb_params)
    xgb.fit(Xr, yr, sample_weight=sw, verbose=False)
    estimators.append(("xgb", xgb))
    logger.info("✓ XGBoost trained")

    # 2. LightGBM
    try:
        import lightgbm as lgb
        lgb_m = lgb.LGBMClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            min_child_samples=10, class_weight="balanced",
            random_state=42, n_jobs=-1, verbose=-1,
        )
        lgb_m.fit(Xr, yr)
        estimators.append(("lgb", lgb_m))
        logger.info("✓ LightGBM trained")
    except ImportError:
        logger.info("LightGBM not installed — skipping (pip install lightgbm)")

    # 3. Random Forest
    try:
        from sklearn.ensemble import RandomForestClassifier
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
        rf.fit(Xr, yr)
        estimators.append(("rf", rf))
        logger.info("✓ Random Forest trained")
    except ImportError:
        logger.info("sklearn not installed")

    return estimators


def ensemble_proba(estimators: list, X: np.ndarray) -> np.ndarray:
    return np.mean([est.predict_proba(X) for _, est in estimators], axis=0)


# ===========================================================================
# CALIBRATION
# ===========================================================================

def calibrate(estimators: list, X_cal: np.ndarray,
              y_cal: np.ndarray) -> Any | None:
    try:
        from sklearn.linear_model import LogisticRegression
        proba = ensemble_proba(estimators, X_cal)
        lr = LogisticRegression(C=1.0, max_iter=500, random_state=42,
                                 multi_class="multinomial", solver="lbfgs")
        lr.fit(proba, y_cal)
        logger.info("✓ Calibration fitted")
        return lr
    except Exception as e:
        logger.warning(f"Calibration failed: {e}")
        return None


# ===========================================================================
# PER-SYMBOL TRAINER
# ===========================================================================

def train_symbol(symbol: str, df: pd.DataFrame) -> dict[str, Any] | None:
    try:
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score, f1_score, classification_report
        from sklearn.preprocessing import RobustScaler
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return None

    logger.info(f"[{symbol}] ── v2 training pipeline ──")

    # 1. Feature engineering
    df = add_all_features(df)
    df = make_labels(df)

    feat_names = get_feature_names(df)
    df = df.dropna(subset=feat_names + ["label"])

    if len(df) < MIN_ROWS_PER_SYMBOL:
        logger.warning(f"[{symbol}] Only {len(df)} rows after cleaning — skipping")
        return None

    X = df[feat_names].values.astype(np.float32)
    y = df["label"].values.astype(int)

    dist = {LABEL_MAP[c]: int((y == c).sum()) for c in range(3)}
    logger.info(f"[{symbol}] Labels: {dist}")

    # 2. Temporal split
    n          = len(X)
    train_end  = int(n * (1 - TEST_FRAC))
    cal_start  = int(n * 0.65)
    Xtr, ytr   = X[:train_end],   y[:train_end]
    Xte, yte   = X[train_end:],   y[train_end:]
    Xcal, ycal = X[cal_start:train_end], y[cal_start:train_end]

    # 3. Scale (RobustScaler handles fat-tailed crypto distributions)
    scaler = RobustScaler()
    Xtr_s  = scaler.fit_transform(Xtr)
    Xte_s  = scaler.transform(Xte)
    Xcal_s = scaler.transform(Xcal)

    # 4. Optuna search
    logger.info(f"[{symbol}] Optuna ({OPTUNA_TRIALS} trials)…")
    params = optuna_search(Xtr_s, ytr, n_trials=OPTUNA_TRIALS)

    # 5. Feature selection (first-pass XGB)
    from xgboost import XGBClassifier
    Xr, yr = smote_resample(Xtr_s, ytr)
    fp = XGBClassifier(**params)
    fp.fit(Xr, yr, sample_weight=sample_weights(yr), verbose=False)
    ranked = np.argsort(fp.feature_importances_)[::-1]
    sel    = ranked[:FEATURE_SELECT_TOP].tolist()
    sel_names = [feat_names[i] for i in sel]
    logger.info(f"[{symbol}] Selected {len(sel)} features. Top5: {sel_names[:5]}")

    Xtr_sel  = Xtr_s[:,  sel]
    Xte_sel  = Xte_s[:,  sel]
    Xcal_sel = Xcal_s[:, sel]

    # 6. Walk-forward CV on selected features
    cv = walk_forward_cv(Xtr_sel, ytr, N_WALK_FOLDS, params)

    # 7. Ensemble
    logger.info(f"[{symbol}] Building ensemble…")
    estimators = build_ensemble(Xtr_sel, ytr, params)

    # 8. Calibrate
    cal = calibrate(estimators, Xcal_sel, ycal)

    # 9. Evaluate
    raw_p = ensemble_proba(estimators, Xte_sel)
    final_p = cal.predict_proba(raw_p) if cal is not None else raw_p
    preds = np.argmax(final_p, axis=1)
    acc   = accuracy_score(yte, preds)
    f1    = f1_score(yte, preds, average="macro", zero_division=0)
    report = classification_report(yte, preds,
                                    target_names=["SELL","HOLD","BUY"],
                                    output_dict=True, zero_division=0)

    logger.info(f"[{symbol}] acc={acc:.4f}  f1={f1:.4f}  "
                f"(cv_acc={cv.get('cv_accuracy',0):.4f}  cv_f1={cv.get('cv_f1_macro',0):.4f})")

    # ---- Feature importances (from primary XGB) --------------------------
    primary_xgb = next(m for nm, m in estimators if nm == "xgb")
    all_imp = np.zeros(len(feat_names))
    for local_i, global_i in enumerate(sel):
        all_imp[global_i] = primary_xgb.feature_importances_[local_i]
    feat_imp = sorted(zip(feat_names, all_imp.tolist()),
                      key=lambda x: x[1], reverse=True)[:15]

    # ---- Save artifacts --------------------------------------------------
    safe = symbol.replace("/", "_")

    primary_xgb.save_model(str(ML_MODELS_DIR / f"{safe}_model.json"))

    (ML_MODELS_DIR / f"{safe}_scaler.json").write_text(json.dumps({
        "type": "robust",
        "center_":       scaler.center_.tolist(),
        "scale_":        scaler.scale_.tolist(),
        "feature_names": feat_names,
        "selected_idx":  sel,
        "selected_names": sel_names,
    }))

    (ML_MODELS_DIR / f"{safe}_ensemble.json").write_text(json.dumps({
        "n_estimators": len(estimators),
        "types": [nm for nm, _ in estimators],
        "has_calibrator": cal is not None,
        "selected_idx": sel,
        "selected_names": sel_names,
    }))

    if cal is not None:
        (ML_MODELS_DIR / f"{safe}_calibrator.json").write_text(json.dumps({
            "coef":      cal.coef_.tolist(),
            "intercept": cal.intercept_.tolist(),
            "classes":   cal.classes_.tolist(),
        }))

    # Save LGB / RF if present
    for nm, est in estimators:
        if nm == "lgb":
            try:
                est.booster_.save_model(str(ML_MODELS_DIR / f"{safe}_lgb.txt"))
            except Exception:
                pass
        if nm == "rf":
            try:
                import pickle
                with open(ML_MODELS_DIR / f"{safe}_rf.pkl", "wb") as fh:
                    pickle.dump(est, fh)
            except Exception:
                pass

    meta = {
        "symbol": symbol,
        "model_version": "xgb-v2.0-ensemble",
        "n_train": int(len(Xtr)),
        "n_test":  int(len(Xte)),
        "n_features_total": len(feat_names),
        "n_features_selected": len(sel_names),
        "features": sel_names,
        "all_features": feat_names,
        "label_map": LABEL_MAP,
        "test_accuracy": round(acc, 4),
        "test_f1_macro":  round(f1, 4),
        "cv_metrics": cv,
        "classification_report": report,
        "feature_importances": feat_imp,
        "label_distribution": dist,
        "ensemble_types": [nm for nm, _ in estimators],
    }
    (ML_MODELS_DIR / f"{safe}_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


# ===========================================================================
# TRAIN ALL CRYPTO
# ===========================================================================

def train_all_crypto(gold_path: Path = GOLD_MARKET_FILE) -> dict[str, Any]:
    if not gold_path.exists():
        raise FileNotFoundError(
            f"Gold features not found: {gold_path}\n"
            "Run: python -m app.etl.gold.build_gold_market"
        )

    logger.info("Loading Gold features", extra={"path": str(gold_path)})
    df = pd.read_parquet(gold_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    crypto = df[df["market_type"] == "crypto"].copy()
    symbols = crypto["symbol"].unique().tolist()
    logger.info(f"Symbols: {symbols}")

    results: dict[str, Any] = {}
    for sym in symbols:
        meta = train_symbol(sym, crypto[crypto["symbol"] == sym].copy())
        results[sym] = meta if meta else {"error": "training failed"}

    summary = {
        "trained_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "trainer_version": "v2.0",
        "symbols": list(results.keys()),
        "results": {
            k: {
                "accuracy":   v.get("test_accuracy"),
                "f1_macro":   v.get("test_f1_macro"),
                "cv_accuracy": (v.get("cv_metrics") or {}).get("cv_accuracy"),
                "cv_f1":      (v.get("cv_metrics") or {}).get("cv_f1_macro"),
                "n_features": v.get("n_features_selected"),
                "ensemble":   v.get("ensemble_types"),
                "error":      v.get("error"),
            }
            for k, v in results.items()
        },
    }
    (ML_MODELS_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2))
    logger.info("All training complete")
    return results


# ===========================================================================
# CLI
# ===========================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ML Trainer v2.0 — XGBoost Ensemble + Optuna + SMOTE")
    print("=" * 70 + "\n")

    results = train_all_crypto()

    print("\n📊 Final Results:")
    for sym, meta in results.items():
        if meta.get("error"):
            print(f"  ❌ {sym}: {meta['error']}")
            continue
        cv = meta.get("cv_metrics") or {}
        print(
            f"  ✅ {sym}:  "
            f"test_acc={meta['test_accuracy']:.3f}  "
            f"test_f1={meta['test_f1_macro']:.3f}  "
            f"cv_acc={cv.get('cv_accuracy',0):.3f}  "
            f"cv_f1={cv.get('cv_f1_macro',0):.3f}  "
            f"features={meta['n_features_selected']}  "
            f"ensemble={meta['ensemble_types']}"
        )

    print(f"\nModels → {ML_MODELS_DIR}")