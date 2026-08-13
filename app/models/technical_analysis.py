from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MACDSeries(BaseModel):
    macd: List[Optional[float]]
    signal: List[Optional[float]]
    histogram: List[Optional[float]]


class RSISeries(BaseModel):
    rsi: List[Optional[float]]


class ATRSeries(BaseModel):
    atr: List[Optional[float]]


class BollingerBandsSeries(BaseModel):
    middle_band: List[Optional[float]]
    upper_band: List[Optional[float]]
    lower_band: List[Optional[float]]
    bandwidth: List[Optional[float]]
    percent_b: List[Optional[float]]


class ADXSeries(BaseModel):
    adx: List[Optional[float]]
    plus_di: List[Optional[float]]
    minus_di: List[Optional[float]]


class TechnicalSeries(BaseModel):
    dates: List[datetime]
    close: List[float]
    macd: MACDSeries
    rsi: RSISeries
    atr: ATRSeries
    bollinger_bands: BollingerBandsSeries
    adx: ADXSeries


class RenkoBrick(BaseModel):
    date: datetime
    open: float
    close: float
    direction: int
    bar_num: int


class RenkoSummary(BaseModel):
    brick_size: Optional[float] = None
    bricks: List[RenkoBrick] = []


class TechnicalAnalysisResponse(BaseModel):
    ticker: str
    period: str
    interval: str
    bars_used: int
    as_of: datetime
    latest: Dict[str, Any]
    series: TechnicalSeries
    renko: RenkoSummary
    chart_png_base64: Optional[str] = None
    chart_saved_path: Optional[str] = None
    renko_chart_png_base64: Optional[str] = None
    renko_chart_saved_path: Optional[str] = None
