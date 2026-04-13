from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Snapshot(Base):
    """Stores the 14 input features submitted before each prediction."""
    __tablename__ = "snapshots"

    id              = Column(Integer, primary_key=True, index=True)
    auction_date    = Column(Date, nullable=False)
    tenor_days      = Column(Integer, nullable=False)      # 91 / 182 / 364

    # Rate lags
    lag1_stop       = Column(Float, nullable=False)
    lag2_stop       = Column(Float, nullable=False)
    lag3_stop       = Column(Float, nullable=False)

    # Auction supply
    offer_amt       = Column(Float, nullable=False)
    prev_offer      = Column(Float, nullable=False)
    prev_bid_cover  = Column(Float, nullable=False)

    # Secondary market
    sec_rate        = Column(Float, nullable=False)
    sec_rate_5d_ago = Column(Float, nullable=False)

    # Macro
    system_liquidity = Column(Float, nullable=False)
    mpr              = Column(Float, nullable=False)
    inflation        = Column(Float, nullable=False)

    source          = Column(String, default="dashboard")
    created_at      = Column(DateTime, default=datetime.utcnow)

    predictions     = relationship("Prediction", back_populates="snapshot")


class Prediction(Base):
    """Stores each model prediction result."""
    __tablename__ = "predictions"

    id                   = Column(Integer, primary_key=True, index=True)
    snapshot_id          = Column(Integer, ForeignKey("snapshots.id"), nullable=True)
    auction_date         = Column(Date, nullable=False)
    tenor_days           = Column(Integer, nullable=False)
    predicted_stop_rate  = Column(Float, nullable=True)
    model_name           = Column(String, default="gti_ntb_v5")
    status               = Column(String, default="ok")
    confidence           = Column(Float, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)

    snapshot             = relationship("Snapshot", back_populates="predictions")
