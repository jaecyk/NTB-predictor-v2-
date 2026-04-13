# NTB Rate Predictor — v2

**Nigerian Treasury Bill stop rate prediction API using trained GTI v5 gradient-boosted models.**

Deployed on Railway with PostgreSQL. Called by the Cloudflare dashboard at `nga-auction.jkoroye.workers.dev`.

---

## What this does

- Accepts 14 pre-auction market features (rate lags, supply, secondary market, macro)
- Runs 3 trained scikit-learn models — one per tenor (91d / 182d / 364d)
- Returns predicted NTB stop rate + confidence score
- Stores every snapshot and prediction to PostgreSQL for history tracking

---

## Repo structure

```
app.py          ← FastAPI routes (main entry point)
predictor.py    ← loads .pkl models and runs inference
database.py     ← SQLAlchemy engine (Railway PostgreSQL or SQLite local)
models.py       ← DB table definitions
schemas.py      ← Pydantic request/response types
requirements.txt
Procfile        ← Railway start command
railway.json    ← Railway deployment config
runtime.txt     ← Python 3.11

gti_ntb_v5_91D.pkl    ← Copy from v1 repo
gti_ntb_v5_182D.pkl   ← Copy from v1 repo
gti_ntb_v5_364D.pkl   ← Copy from v1 repo

frontend/
  index.html    ← Cloudflare Worker dashboard (deploy to nga-auction worker)
```

---

## Setup — copy pkl files first

Copy these 3 files from your v1 repo (`jaecyk/NTB-predictor`) into this repo root:
- `gti_ntb_v5_91D.pkl`
- `gti_ntb_v5_182D.pkl`
- `gti_ntb_v5_364D.pkl`

---

## Deploy on Railway

1. Push this repo to GitHub
2. Go to `railway.app` → New Project → Deploy from GitHub → select this repo
3. Add plugin: **PostgreSQL** (Railway auto-sets `DATABASE_URL`)
4. Add environment variable: `ALLOWED_ORIGINS` = `*`
5. Wait ~2 min — check `https://your-url/health`

---

## API Endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/health` | Check API status and loaded models |
| POST | `/predict` | Submit 14 features → get prediction(s) |
| GET | `/predictions/latest` | Latest prediction per tenor |
| GET | `/predictions/history` | Full prediction log (limit=50) |
| DELETE | `/predictions/clear` | Clear all records (dev only) |

### POST /predict — example request body

```json
{
  "auction_date": "2026-04-22",
  "lag1_stop": 16.20,
  "lag2_stop": 16.43,
  "lag3_stop": 16.72,
  "offer_amt": 750,
  "prev_offer": 500,
  "prev_bid_cover": 4.2,
  "sec_rate": 16.11,
  "sec_rate_5d_ago": 16.20,
  "system_liquidity": 8.5,
  "mpr": 26.50,
  "inflation": 15.06
}
```

### Response

```json
[
  {
    "tenor_days": 91,
    "predicted_stop_rate": 15.9812,
    "status": "ok",
    "confidence": 82.5,
    "model_name": "gti_ntb_v5_91D.pkl"
  },
  {
    "tenor_days": 182,
    "predicted_stop_rate": 16.0341,
    "status": "ok",
    "confidence": 82.5,
    "model_name": "gti_ntb_v5_182D.pkl"
  },
  {
    "tenor_days": 364,
    "predicted_stop_rate": 15.8924,
    "status": "ok",
    "confidence": 82.5,
    "model_name": "gti_ntb_v5_364D.pkl"
  }
]
```

---

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

## Connect to Cloudflare dashboard

Deploy `frontend/index.html` to your `nga-auction` Cloudflare Worker.
Open the dashboard → API Setup tab → paste your Railway URL → click Test.

---

*v1 repo: jaecyk/NTB-predictor — Streamlit app, no persistent backend*  
*v2 repo: this — FastAPI + Railway PostgreSQL + Cloudflare frontend*
