from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class DataCoverage(BaseModel):
    price_history: bool
    screener_fundamentals: bool
    concall_summary: bool


class StockReport(BaseModel):
    symbol: str
    company_name: str
    generated_at: str
    holding: Dict[str, Any]
    technicals: Optional[Dict[str, Any]] = None
    fundamentals: Optional[Dict[str, Any]] = None
    concall: Optional[Dict[str, Any]] = None
    scorecard: Dict[str, Any]
    data_coverage: DataCoverage
    llm_narrative: Optional[str] = None
    markdown: Optional[str] = None
    markdown_path: Optional[str] = None


class PortfolioReportResponse(BaseModel):
    portfolio_value: float
    total_investment: float
    total_pnl: float
    total_pnl_percent: float
    overall_narrative: Optional[str] = None
    reports: List[StockReport]
    not_tracked: List[str]
    rollup_markdown: Optional[str] = None
    rollup_markdown_path: Optional[str] = None
