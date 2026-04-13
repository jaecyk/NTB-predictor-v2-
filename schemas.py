from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class SnapshotIn(BaseModel):
    """
    The 14 features your GTI v5 model was trained on.
    tenor_days is optional — if omitted the API predicts all 3 tenors.
    """
    auction_date:     date
    tenor_days:       Optional[int] = None    # 91 / 182 / 364 — None = predict all

    # Rate lags (last 3 auction stop rates for this tenor)
    lag1_stop:        float = Field(..., description="Most recent stop rate")
    lag2_stop:        float = Field(..., description="2nd most recent stop rate")
    lag3_stop:        float = Field(..., description="3rd most recent stop rate")

    # Auction supply
    offer_amt:        float = Field(..., description="This auction offer size ₦bn")
    prev_offer:       float = Field(..., description="Previous auction offer size ₦bn")
    prev_bid_cover:   float = Field(..., description="Previous auction bid-to-cover ratio")

    # Secondary market
    sec_rate:         float = Field(..., description="Current secondary market yield %")
    sec_rate_5d_ago:  float = Field(..., description="Secondary market yield 5 days ago %")

    # Macro
    system_liquidity: float = Field(..., description="System liquidity ₦ trillion")
    mpr:              float = Field(..., description="CBN Monetary Policy Rate %")
    inflation:        float = Field(..., description="CPI inflation rate %")

    source:           Optional[str] = "dashboard"

    class Config:
        json_schema_extra = {
            "example": {
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
                "inflation": 15.06,
                "source": "dashboard"
            }
        }


class SnapshotOut(SnapshotIn):
    id:         int
    created_at: datetime
    class Config:
        from_attributes = True


class PredictionOut(BaseModel):
    tenor_days:          int
    predicted_stop_rate: Optional[float]
    status:              str
    confidence:          Optional[float]
    model_name:          Optional[str]

    class Config:
        from_attributes = True


class PredictionHistoryOut(BaseModel):
    id:                  int
    auction_date:        date
    tenor_days:          int
    predicted_stop_rate: Optional[float]
    model_name:          Optional[str]
    status:              str
    confidence:          Optional[float]
    created_at:          datetime

    class Config:
        from_attributes = True
