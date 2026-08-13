import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.quant.chart_builder import TechnicalChartBuilder
from app.quant.indicators import ADX, ATR, MACD, RSI, BollingerBands, Renko
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

CHARTS_DIR = Path("static/technical_charts")

# (period, interval) below is Wilder/EMA-period-aware: with the default indicator
# settings (MACD 12/26/9, ATR/ADX/RSI/BB period 14-20) a 6mo daily history gives the
# smoothed series enough bars to converge well past their min_periods warm-up.
DEFAULT_PERIOD = "6mo"
DEFAULT_INTERVAL = "1d"


def _clean_list(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(v) else float(v) for v in series]


class TechnicalAnalysisService:
    """
    Fetches OHLCV history for a ticker and computes MACD, RSI, ATR, Bollinger Bands,
    ADX and a Renko view using the app.quant indicator classes, plus renders the
    accompanying chart(s) via TechnicalChartBuilder.
    """

    @staticmethod
    def _fetch_ohlcv(ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        history = MarketDataService.get_history(ticker, period, interval)
        if history is None or not history["bars"]:
            return None

        df = pd.DataFrame(history["bars"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        df.rename(
            columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
            inplace=True,
        )
        return df

    @classmethod
    def analyze(
        cls,
        ticker: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
        include_chart: bool = True,
        save_chart: bool = True,
    ) -> Optional[Dict]:
        df = cls._fetch_ohlcv(ticker, period, interval)
        if df is None:
            return None

        macd = MACD()
        rsi = RSI()
        atr = ATR()
        bollinger = BollingerBands()
        adx = ADX()
        renko = Renko()

        macd_df = macd.compute(df)
        rsi_df = rsi.compute(df)
        atr_df = atr.compute(df)
        bb_df = bollinger.compute(df)
        adx_df = adx.compute(df)
        renko_df = renko.compute(df)

        latest: Dict[str, Optional[Dict]] = {
            "macd": {
                "macd": macd_df["MACD"].iloc[-1],
                "signal": macd_df["Signal"].iloc[-1],
                "histogram": macd_df["Histogram"].iloc[-1],
            },
            "rsi": {"rsi": rsi_df["RSI"].iloc[-1]},
            "atr": {"atr": atr_df["ATR"].iloc[-1]},
            "bollinger_bands": {
                "middle_band": bb_df["MiddleBand"].iloc[-1],
                "upper_band": bb_df["UpperBand"].iloc[-1],
                "lower_band": bb_df["LowerBand"].iloc[-1],
                "bandwidth": bb_df["Bandwidth"].iloc[-1],
                "percent_b": bb_df["PercentB"].iloc[-1],
            },
            "adx": {
                "adx": adx_df["ADX"].iloc[-1],
                "plus_di": adx_df["+DI"].iloc[-1],
                "minus_di": adx_df["-DI"].iloc[-1],
            },
            "renko": renko.latest(df),
        }
        # Replace NaN scalars with None so the response is valid, unambiguous JSON.
        for block in ("macd", "rsi", "atr", "bollinger_bands", "adx"):
            latest[block] = {k: (None if pd.isna(v) else float(v)) for k, v in latest[block].items()}

        series = {
            "dates": df.index.tolist(),
            "close": df["Close"].astype(float).tolist(),
            "macd": {
                "macd": _clean_list(macd_df["MACD"]),
                "signal": _clean_list(macd_df["Signal"]),
                "histogram": _clean_list(macd_df["Histogram"]),
            },
            "rsi": {"rsi": _clean_list(rsi_df["RSI"])},
            "atr": {"atr": _clean_list(atr_df["ATR"])},
            "bollinger_bands": {
                "middle_band": _clean_list(bb_df["MiddleBand"]),
                "upper_band": _clean_list(bb_df["UpperBand"]),
                "lower_band": _clean_list(bb_df["LowerBand"]),
                "bandwidth": _clean_list(bb_df["Bandwidth"]),
                "percent_b": _clean_list(bb_df["PercentB"]),
            },
            "adx": {
                "adx": _clean_list(adx_df["ADX"]),
                "plus_di": _clean_list(adx_df["+DI"]),
                "minus_di": _clean_list(adx_df["-DI"]),
            },
        }

        renko_summary = {
            "brick_size": renko_df.attrs.get("brick_size"),
            "bricks": renko_df.to_dict("records") if not renko_df.empty else [],
        }

        result = {
            "ticker": ticker.upper(),
            "period": period,
            "interval": interval,
            "bars_used": len(df),
            "as_of": df.index[-1],
            "latest": latest,
            "series": series,
            "renko": renko_summary,
        }

        if include_chart or save_chart:
            indicators_for_chart = {
                "macd": macd_df,
                "rsi": rsi_df,
                "bollinger_bands": bb_df,
                "adx": adx_df,
            }
            builder = TechnicalChartBuilder(ticker, df, indicators_for_chart)
            chart_result = builder.render(
                renko_df=renko_df,
                include_base64=include_chart,
                save_dir=CHARTS_DIR if save_chart else None,
            )
            result.update(chart_result)

        return result
