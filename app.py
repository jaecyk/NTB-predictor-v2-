from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from database import Base, engine, get_db
from models import Snapshot, Prediction
from schemas import SnapshotIn, SnapshotOut, PredictionOut, PredictionHistoryOut
from predictor import load_models, run_prediction

# ── App setup ────────────────────────────────────────────────────────────
app = FastAPI(
    title="NTB Rate Predictor API v2",
    description="GTI v5 trained models — 91d / 182d / 364d NTB stop rate prediction",
    version="2.0.0"
)

# ── CORS — allow Cloudflare Workers and any browser ──────────────────────
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()] or ["*"]
allow_all = origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models on startup ────────────────────────────────────────────────
models = load_models()

# ── Create DB tables ──────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# ─────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Check API is up and which models are loaded."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "available_models": sorted(list(models.keys())),
        "models_loaded": len(models),
    }


@app.post("/predict", response_model=list[PredictionOut])
def predict(payload: SnapshotIn, db: Session = Depends(get_db)):
    """
    Submit a market snapshot and get predictions for all 3 tenors
    (or just the requested tenor if tenor_days is specified).
    Saves snapshot + prediction to DB.
    """
    tenors = [payload.tenor_days] if payload.tenor_days else [91, 182, 364]
    results = []

    for tenor in tenors:
        # Save snapshot
        snap = Snapshot(**payload.model_dump(), tenor_days=tenor)
        db.add(snap)
        db.commit()
        db.refresh(snap)

        # Run prediction
        predicted_rate, status, confidence = run_prediction(snap, models)

        # Save prediction record
        pred_record = Prediction(
            snapshot_id=snap.id,
            auction_date=snap.auction_date,
            tenor_days=tenor,
            predicted_stop_rate=predicted_rate,
            model_name=f"gti_ntb_v5_{tenor}D.pkl",
            status=status,
            confidence=confidence,
        )
        db.add(pred_record)
        db.commit()

        results.append(PredictionOut(
            tenor_days=tenor,
            predicted_stop_rate=predicted_rate,
            status=status,
            confidence=confidence,
            model_name=f"gti_ntb_v5_{tenor}D.pkl",
        ))

    return results


@app.get("/predictions/history", response_model=list[PredictionHistoryOut])
def history(limit: int = 50, tenor: int = None, db: Session = Depends(get_db)):
    """Get past prediction history, optionally filtered by tenor."""
    q = db.query(Prediction).order_by(Prediction.created_at.desc())
    if tenor:
        q = q.filter(Prediction.tenor_days == tenor)
    return q.limit(limit).all()


@app.get("/predictions/latest", response_model=list[PredictionOut])
def latest_predictions(db: Session = Depends(get_db)):
    """Get the most recent prediction for each tenor."""
    results = []
    for tenor in [91, 182, 364]:
        row = (
            db.query(Prediction)
            .filter(Prediction.tenor_days == tenor)
            .order_by(Prediction.created_at.desc())
            .first()
        )
        if row:
            results.append(PredictionOut(
                tenor_days=tenor,
                predicted_stop_rate=row.predicted_stop_rate,
                status=row.status,
                confidence=row.confidence,
                model_name=row.model_name,
            ))
    return results


@app.delete("/predictions/clear")
def clear_predictions(db: Session = Depends(get_db)):
    """Clear all prediction history (dev use)."""
    db.query(Prediction).delete()
    db.query(Snapshot).delete()
    db.commit()
    return {"message": "All records cleared"}
