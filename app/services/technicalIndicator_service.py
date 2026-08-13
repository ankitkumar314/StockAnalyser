import logging
import math
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# All compute_* helpers are pure functions over a list of OHLC bars
# ({date, open, high, low, close, volume}) so they are unit-testable offline.
# get_indicators() is the online wrapper that fetches 1y daily history from
# MarketDataService (yfinance) and runs the computation.


def _sma(values: List[float], n: int) -> Optional[float]:
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def _ema_series(values: List[float], n: int) -> List[float]:
    if not values:
        return []
    k = 2 / (n + 1)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema


def _rsi(closes: List[float], n: int = 14) -> Optional[float]:
    if len(closes) < n + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    # Wilder smoothing
    avg_gain = sum(gains[:n]) / n
    avg_loss = sum(losses[:n]) / n
    for i in range(n, len(gains)):
        avg_gain = (avg_gain * (n - 1) + gains[i]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i]) / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _atr(bars: List[Dict], n: int = 14) -> Optional[float]:
    if len(bars) < n + 1:
        return None
    trs = []
    for i in range(1, len(bars)):
        high, low = bars[i]["high"], bars[i]["low"]
        prev_close = bars[i - 1]["close"]
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    atr = sum(trs[:n]) / n
    for i in range(n, len(trs)):
        atr = (atr * (n - 1) + trs[i]) / n
    return atr


def _max_drawdown(closes: List[float]) -> Optional[float]:
    """Max peak-to-trough drawdown in percent (negative number)."""
    if len(closes) < 2:
        return None
    peak = closes[0]
    max_dd = 0.0
    for c in closes:
        peak = max(peak, c)
        max_dd = min(max_dd, (c - peak) / peak * 100)
    return max_dd


def _annualized_volatility(closes: List[float]) -> Optional[float]:
    if len(closes) < 30:
        return None
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))
            if closes[i - 1] > 0]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252) * 100


def _swing_levels(bars: List[Dict], window: int = 5) -> Dict[str, Optional[float]]:
    """Nearest swing-low support below price and swing-high resistance above."""
    closes = [b["close"] for b in bars]
    if not closes:
        return {"support": None, "resistance": None}
    price = closes[-1]
    lows = [b["low"] for b in bars]
    highs = [b["high"] for b in bars]
    supports, resistances = [], []
    for i in range(window, len(bars) - window):
        if lows[i] == min(lows[i - window:i + window + 1]):
            supports.append(lows[i])
        if highs[i] == max(highs[i - window:i + window + 1]):
            resistances.append(highs[i])
    below = [s for s in supports if s < price]
    above = [r for r in resistances if r > price]
    return {
        "support": max(below) if below else (min(lows) if lows else None),
        "resistance": min(above) if above else (max(highs) if highs else None),
    }


class TechnicalIndicatorService:
    """
    Real technical indicators (v3) computed from daily OHLC history.
    compute_indicators() is pure; get_indicators() fetches history via
    MarketDataService (Yahoo Finance) and keeps the v2 return shape
    (macd, macd_signal, macd_trend, dma_50, dma_200, dma_crossover) with
    additional fields; is_dummy is now always False.
    """

    @staticmethod
    def compute_indicators(bars: List[Dict]) -> Dict:
        closes = [b["close"] for b in bars]
        if len(closes) < 2:
            raise ValueError("Need at least 2 bars to compute indicators")

        last_close = closes[-1]
        sma50 = _sma(closes, 50)
        sma200 = _sma(closes, 200)

        macd_line = None
        macd_signal = None
        macd_hist = None
        if len(closes) >= 35:  # 26 for slow EMA + 9 for signal
            ema12 = _ema_series(closes, 12)
            ema26 = _ema_series(closes, 26)
            macd_series = [a - b for a, b in zip(ema12, ema26)]
            signal_series = _ema_series(macd_series, 9)
            macd_line = macd_series[-1]
            macd_signal = signal_series[-1]
            macd_hist = macd_line - macd_signal

        macd_trend = None
        if macd_line is not None:
            macd_trend = "bullish" if macd_line >= macd_signal else "bearish"

        dma_crossover = None
        if sma50 is not None and sma200 is not None:
            dma_crossover = "golden_cross" if sma50 >= sma200 else "death_cross"

        high_52w = max(b["high"] for b in bars)
        low_52w = min(b["low"] for b in bars)
        rsi = _rsi(closes)
        atr = _atr(bars)
        levels = _swing_levels(bars)

        volumes = [b.get("volume", 0) for b in bars]
        avg_volume_20 = (sum(volumes[-20:]) / min(len(volumes), 20)) if volumes else None

        pct = lambda a, b: ((a - b) / b * 100) if (a is not None and b) else None
        ann_vol = _annualized_volatility(closes)
        max_dd = _max_drawdown(closes)

        return {
            # v2-compatible keys
            "macd": round(macd_line, 2) if macd_line is not None else None,
            "macd_signal": round(macd_signal, 2) if macd_signal is not None else None,
            "macd_trend": macd_trend,
            "dma_50": round(sma50, 2) if sma50 is not None else None,
            "dma_200": round(sma200, 2) if sma200 is not None else None,
            "dma_crossover": dma_crossover,
            "is_dummy": False,
            # v3 extended keys
            "last_close": round(last_close, 2),
            "macd_histogram": round(macd_hist, 2) if macd_hist is not None else None,
            "rsi_14": round(rsi, 1) if rsi is not None else None,
            "atr_14": round(atr, 2) if atr is not None else None,
            "atr_percent": round(atr / last_close * 100, 2) if atr else None,
            "price_vs_dma50_percent": round(pct(last_close, sma50), 2) if sma50 else None,
            "price_vs_dma200_percent": round(pct(last_close, sma200), 2) if sma200 else None,
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "percent_from_52w_high": round(pct(last_close, high_52w), 2),
            "percent_from_52w_low": round(pct(last_close, low_52w), 2),
            "annualized_volatility_percent": round(ann_vol, 1) if ann_vol is not None else None,
            "max_drawdown_percent": round(max_dd, 1) if max_dd is not None else None,
            "support": round(levels["support"], 2) if levels["support"] else None,
            "resistance": round(levels["resistance"], 2) if levels["resistance"] else None,
            "avg_volume_20d": int(avg_volume_20) if avg_volume_20 else None,
            "bars_used": len(bars),
        }

    @staticmethod
    def get_indicators(ticker: str, exchange: str = "NSE",
                       period: str = "1y") -> Dict:
        """Fetch 1y daily OHLC from Yahoo Finance and compute real indicators.
        `ticker` is the NSE/BSE symbol without suffix (e.g. NUVAMA)."""
        from app.services.market_data_service import MarketDataService

        suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
        yahoo_ticker = ticker.upper() if ticker.upper().endswith((".NS", ".BO")) \
            else f"{ticker.upper()}{suffix}"

        history = MarketDataService.get_history(yahoo_ticker, period=period, interval="1d")
        if not history or not history.get("bars"):
            logger.warning(f"No price history for {yahoo_ticker}; indicators unavailable")
            return {"macd": None, "macd_signal": None, "macd_trend": None,
                    "dma_50": None, "dma_200": None, "dma_crossover": None,
                    "is_dummy": False, "error": f"no history for {yahoo_ticker}"}

        indicators = TechnicalIndicatorService.compute_indicators(history["bars"])
        indicators["yahoo_ticker"] = yahoo_ticker
        return indicators
