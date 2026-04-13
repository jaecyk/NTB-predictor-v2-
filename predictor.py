from pathlib import Path
import joblib
import pandas as pd

# ── Feature order must match exactly how models were trained ──────────────
FEATURE_ORDER = [
    "lag1_stop",
    "lag2_stop",
    "lag3_stop",
    "ma3_stop",          # auto-calculated: mean of lag1/2/3
    "delta_stop_1",      # auto-calculated: lag1 - lag2
    "offer_amt",
    "offer_change",      # auto-calculated: offer_amt - prev_offer
    "prev_bid_cover",
    "sec_rate",
    "sec_rate_change_5d", # auto-calculated: sec_rate - sec_rate_5d_ago
    "sec_minus_lag1",    # auto-calculated: sec_rate - lag1_stop
    "system_liquidity",
    "mpr",
    "inflation",
]

MODEL_FILES = {
    91:  "gti_ntb_v5_91D.pkl",
    182: "gti_ntb_v5_182D.pkl",
    364: "gti_ntb_v5_364D.pkl",
}


def load_models() -> dict:
    """Load all available PKL model files from the repo root."""
    loaded = {}
    for tenor, fname in MODEL_FILES.items():
        path = Path(fname)
        if path.exists():
            try:
                loaded[tenor] = joblib.load(path)
                print(f"Loaded model: {fname}")
            except Exception as e:
                print(f"Failed to load {fname}: {e}")
        else:
            print(f"Model file not found: {fname}")
    return loaded


def _build_features(snapshot) -> dict:
    """Convert a Snapshot ORM object into the 14-feature dict the model expects."""
    l1 = float(snapshot.lag1_stop)
    l2 = float(snapshot.lag2_stop)
    l3 = float(snapshot.lag3_stop)
    sec = float(snapshot.sec_rate)
    sec5d = float(snapshot.sec_rate_5d_ago)
    offer = float(snapshot.offer_amt)
    prev_offer = float(snapshot.prev_offer)

    return {
        "lag1_stop":         l1,
        "lag2_stop":         l2,
        "lag3_stop":         l3,
        "ma3_stop":          round((l1 + l2 + l3) / 3.0, 6),
        "delta_stop_1":      round(l1 - l2, 6),
        "offer_amt":         offer,
        "offer_change":      round(offer - prev_offer, 6),
        "prev_bid_cover":    float(snapshot.prev_bid_cover),
        "sec_rate":          sec,
        "sec_rate_change_5d": round(sec - sec5d, 6),
        "sec_minus_lag1":    round(sec - l1, 6),
        "system_liquidity":  float(snapshot.system_liquidity),
        "mpr":               float(snapshot.mpr),
        "inflation":         float(snapshot.inflation),
    }


def run_prediction(snapshot, models: dict) -> tuple[float | None, str, float | None]:
    """
    Run prediction for a given snapshot.
    Returns (predicted_rate, status_message, confidence_score)
    """
    tenor = int(snapshot.tenor_days)

    if tenor not in models:
        return None, f"model not loaded for {tenor}D", None

    try:
        features = _build_features(snapshot)
        X = pd.DataFrame([features])[FEATURE_ORDER]
        value = float(models[tenor].predict(X)[0])

        # Confidence: estimate from model type
        # GradientBoosting has staged_predict — use a simple heuristic
        conf = None
        try:
            model = models[tenor]
            # For ensemble models, use n_estimators as proxy for maturity
            if hasattr(model, 'n_estimators'):
                conf = min(95, 60 + model.n_estimators * 0.05)
        except Exception:
            conf = 75.0

        return round(value, 4), "ok", conf

    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}", None
