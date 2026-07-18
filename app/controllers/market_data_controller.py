from fastapi import HTTPException
from app.models.market_data import QuoteResponse, HistoryResponse, OHLCBar
from app.services.market_data_service import MarketDataService
import logging

logger = logging.getLogger(__name__)


class MarketDataController:
    def get_quote(self, ticker: str) -> QuoteResponse:
        try:
            if not ticker or not ticker.strip():
                raise HTTPException(status_code=400, detail="Ticker cannot be empty")

            quote = MarketDataService.get_quote(ticker)
            if quote is None:
                raise HTTPException(status_code=404, detail=f"No quote data found for ticker: {ticker}")

            return QuoteResponse(**quote)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")

    def get_history(self, ticker: str, period: str = "1mo", interval: str = "1d") -> HistoryResponse:
        try:
            if not ticker or not ticker.strip():
                raise HTTPException(status_code=400, detail="Ticker cannot be empty")

            history = MarketDataService.get_history(ticker, period, interval)
            if history is None:
                raise HTTPException(status_code=404, detail=f"No historical data found for ticker: {ticker}")

            return HistoryResponse(
                ticker=history["ticker"],
                period=period,
                interval=interval,
                bars=[OHLCBar(**bar) for bar in history["bars"]]
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching history for {ticker}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")
