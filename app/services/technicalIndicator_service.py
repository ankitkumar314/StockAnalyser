import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TechnicalIndicatorService:
    """
    PLACEHOLDER implementation. Returns static dummy values for MACD, 50/200 DMA
    and DMA crossover so the portfolio analysis pipeline can be built end-to-end.
    Replace get_indicators() with real calculations (e.g. over yfinance OHLC history
    from MarketDataService.get_history) without changing its return shape.
    """

    @staticmethod
    def get_indicators(ticker: str) -> Dict:
        logger.info(f"Returning dummy technical indicators for {ticker}")
        return {
            "macd": 12.5,
            "macd_signal": 10.2,
            "macd_trend": "bullish",
            "dma_50": 540.0,
            "dma_200": 480.0,
            "dma_crossover": "golden_cross",
            "is_dummy": True,
        }
