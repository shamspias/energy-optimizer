from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class OptimizeRequest(BaseModel):
    kwh_flexible: float = Field(gt=0, description="Flexible load in kWh")
    max_shift_hours: int = Field(ge=1, le=24, default=3)
    objective: str = Field(default="min_cost", description="Optimization objective")
    zone_eic: str = Field(default="10YNL----------L")
    date_utc: str


class ShiftHour(BaseModel):
    hour_utc: datetime
    shift_kwh: float
    price_eur_kwh: float


class OptimizeResponse(BaseModel):
    baseline_cost_eur: float
    optimized_cost_eur: float
    savings_eur: float
    savings_percent: float
    schedule: List[ShiftHour]
    price_curve: Optional[List[dict]] = None


class AgentAdviseRequest(BaseModel):
    user_id: str
    zone_eic: str = Field(default="10YNL----------L")
    date_utc: str
    context: Optional[str] = None
    kwh_flexible: float = Field(default=6.0)


class AgentAdviseResponse(BaseModel):
    advice: str
    reasoning: str
    plan: Dict[str, Any]
    confidence: float
