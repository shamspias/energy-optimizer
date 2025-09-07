from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class EntsoeIngestRequest(BaseModel):
    zone_eic: str = Field(default="10YNL----------L")
    date_utc: str = Field(description="Date in YYYY-MM-DD format")
    fetch: List[str] = Field(default=["day_ahead_prices", "actual_load"])


class EntsoeIngestResponse(BaseModel):
    zone_eic: str
    hours: int
    has_prices: bool
    has_load: bool
    data: Optional[Dict[str, Any]] = None


class PricePoint(BaseModel):
    hour_utc: datetime
    price_eur_mwh: float
    price_eur_kwh: float


class LoadPoint(BaseModel):
    hour_utc: datetime
    load_mw: float
