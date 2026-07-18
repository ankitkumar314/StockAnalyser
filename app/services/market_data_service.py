import yfinance as yf
import logging
from typing import Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MarketDataService:
    """Fetches live market data (quotes, historical OHLC) from Yahoo Finance via yfinance."""

    @staticmethod
    def get_quote(ticker: str) -> Optional[Dict]:
        """Fetch a live quote snapshot for a ticker. Returns None if the ticker is unknown."""
        info = yf.Ticker(ticker).info
        price = info.get("currentPrice", info.get("regularMarketPrice"))
        if price is None:
            return None

        previous_close = info.get("previousClose", info.get("regularMarketPreviousClose"))
        day_change = None
        day_change_percent = None
        if previous_close:
            day_change = price - previous_close
            day_change_percent = (day_change / previous_close) * 100

        return {
            "ticker": ticker.upper(),
            "price": price,
            "previous_close": previous_close,
            "day_change": day_change,
            "day_change_percent": day_change_percent,
            "day_high": info.get("dayHigh", info.get("regularMarketDayHigh")),
            "day_low": info.get("dayLow", info.get("regularMarketDayLow")),
            "volume": info.get("volume", info.get("regularMarketVolume")),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
            "fetched_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def get_history(ticker: str, period: str = "1mo", interval: str = "1d") -> Optional[Dict]:
        """Fetch historical OHLC bars for a ticker. Returns None if no data is found."""
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        if df is None or df.empty:
            return None

        bars = []
        for index, row in df.iterrows():
            bars.append({
                "date": index.to_pydatetime(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })
        return {"ticker": ticker.upper(), "bars": bars}
