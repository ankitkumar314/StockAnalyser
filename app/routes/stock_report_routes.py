from fastapi import APIRouter, Query

from app.controllers.stock_report_controller import StockReportController
from app.models.stock_report import StockReport, PortfolioReportResponse

router = APIRouter(prefix="/portfolio/report", tags=["Portfolio Report (v3)"])


@router.get("", response_model=PortfolioReportResponse)
def get_portfolio_report(
    period: str = Query("1y", description="yfinance history period, e.g. 6mo, 1y, 2y"),
    llm: bool = Query(False, description="Layer DeepSeek-written narratives on top"),
    save: bool = Query(True, description="Write Markdown reports to the reports/ folder"),
):
    """Full portfolio intelligence report: per-holding research note (technicals +
    fundamentals + concall insights + scorecard) plus a portfolio-level rollup."""
    return StockReportController.portfolio_report(period=period, llm=llm, save=save)


@router.get("/{symbol}", response_model=StockReport)
def get_holding_report(
    symbol: str,
    period: str = Query("1y"),
    llm: bool = Query(False),
    save: bool = Query(True),
):
    """Research note for a single holding in the Kite portfolio."""
    return StockReportController.holding_report(symbol, period=period, llm=llm, save=save)
