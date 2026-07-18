from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class TechnicalIndicators(BaseModel):
    macd: float
    macd_signal: float
    macd_trend: str
    dma_50: float
    dma_200: float
    dma_crossover: str
    is_dummy: bool = True


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
