from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from database import Base, engine, get_db
from models import Snapshot, Prediction
from schemas import SnapshotIn, PredictionOut, PredictionHistoryOut
from predictor import load_models, run_prediction

app = FastAPI(title="NTB Rate Predictor API v2", version="2.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()] or ["*"]
allow_all = origins == ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins,
    allow_credentials=not allow_all, allow_methods=["*"], allow_headers=["*"])

models = load_models()
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0",
            "available_models": sorted(list(models.keys())),
            "models_loaded": len(models)}


@app.post("/predict", response_model=list[PredictionOut])
def predict(payload: SnapshotIn, db: Session = Depends(get_db)):
    tenors = [payload.tenor_days] if payload.tenor_days else [91, 182, 364]
    results = []

    # FIX: pop tenor_days so it doesn't conflict when we set it per tenor
    snap_data = payload.model_dump()
    snap_data.pop("tenor_days", None)

    for tenor in tenors:
        try:
            snap = Snapshot(**snap_data, tenor_days=tenor)
            db.add(snap)
            db.commit()
            db.refresh(snap)

            predicted_rate, status, confidence = run_prediction(snap, models)

            pred = Prediction(snapshot_id=snap.id, auction_date=snap.auction_date,
                tenor_days=tenor, predicted_stop_rate=predicted_rate,
                model_name=f"gti_ntb_v5_{tenor}D.pkl", status=status, confidence=confidence)
            db.add(pred)
            db.commit()

            results.append(PredictionOut(tenor_days=tenor,
                predicted_stop_rate=predicted_rate, status=status,
                confidence=confidence, model_name=f"gti_ntb_v5_{tenor}D.pkl"))

        except Exception as e:
            db.rollback()
            results.append(PredictionOut(tenor_days=tenor, predicted_stop_rate=None,
                status=f"error: {str(e)}", confidence=None,
                model_name=f"gti_ntb_v5_{tenor}D.pkl"))

    return results


@app.get("/predictions/history", response_model=list[PredictionHistoryOut])
def history(limit: int = 50, tenor: int = None, db: Session = Depends(get_db)):
    q = db.query(Prediction).order_by(Prediction.created_at.desc())
    if tenor:
        q = q.filter(Prediction.tenor_days == tenor)
    return q.limit(limit).all()


@app.get("/predictions/latest", response_model=list[PredictionOut])
def latest_predictions(db: Session = Depends(get_db)):
    results = []
    for tenor in [91, 182, 364]:
        row = (db.query(Prediction).filter(Prediction.tenor_days == tenor)
               .order_by(Prediction.created_at.desc()).first())
        if row:
            results.append(PredictionOut(tenor_days=tenor,
                predicted_stop_rate=row.predicted_stop_rate, status=row.status,
                confidence=row.confidence, model_name=row.model_name))
    return results


@app.delete("/predictions/clear")
def clear_predictions(db: Session = Depends(get_db)):
    db.query(Prediction).delete()
    db.query(Snapshot).delete()
    db.commit()
    return {"message": "All records cleared"}
