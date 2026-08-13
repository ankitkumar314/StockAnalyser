from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class TechnicalIndicators(BaseModel):
    """v3: real values computed from OHLC history; any field can be None when
    there is insufficient price history. Extended v3 fields (RSI, ATR, 52w
    range, volatility, support/resistance) are allowed via extra."""
    model_config = {"extra": "allow"}

    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_trend: Optional[str] = None
    dma_50: Optional[float] = None
    dma_200: Optional[float] = None
    dma_crossover: Optional[str] = None
    is_dummy: bool = False


class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    quantity: int
    current_value: float
    profit_loss: float
    profit_loss_percent: float
    portfolio_concentration: float
    indicators: TechnicalIndicators
    concall_available: bool
    concall_quarter_date: Optional[date] = None
    summary_generated_now: bool = False
    short_view: Optional[str] = None


class PortfolioAnalysisResponse(BaseModel):
    portfolio_value: float
    total_investment: float
    total_pnl: float
    total_pnl_percent: float
    overall_view: Optional[str] = None
    stocks: List[StockAnalysis]
    not_tracked: List[str]
    missing_summaries: List[str]
