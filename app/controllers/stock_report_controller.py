import logging
from fastapi import HTTPException

from app.services.stock_report_service import StockReportService

logger = logging.getLogger(__name__)


class StockReportController:
    """v3: combined technical + fundamental + concall research reports."""

    @staticmethod
    def portfolio_report(period: str = "1y", llm: bool = False, save: bool = True):
        try:
            return StockReportService.generate_portfolio_report(
                period=period, use_llm=llm, save=save)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Portfolio report failed: {e}")
            raise HTTPException(status_code=502, detail=f"Portfolio report failed: {e}")

    @staticmethod
    def holding_report(symbol: str, period: str = "1y", llm: bool = False,
                       save: bool = True):
        from app.services.kite_service import KiteService
        try:
            portfolio = KiteService().get_portfolio()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Could not fetch portfolio: {e}")

        holding = next((h for h in portfolio["holdings"]
                        if h["symbol"].upper() == symbol.upper()), None)
        if holding is None:
            raise HTTPException(status_code=404,
                                detail=f"{symbol.upper()} not found in portfolio holdings")
        try:
            return StockReportService.generate_for_holding(
                holding, period=period, use_llm=llm, save=save)
        except Exception as e:
            logger.error(f"Report failed for {symbol}: {e}")
            raise HTTPException(status_code=502, detail=f"Report generation failed: {e}")
