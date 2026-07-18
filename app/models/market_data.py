from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QuoteResponse(BaseModel):
    ticker: str
    price: Optional[float] = None
    previous_close: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    currency: Optional[str] = None
    fetched_at: datetime


class OHLCBar(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoryResponse(BaseModel):
    ticker: str
    period: str
    interval: str
    bars: List[OHLCBar]
