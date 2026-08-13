import pandas as pd

from app.quant.indicators.base import Indicator


class MACD(Indicator):
    """
    Moving Average Convergence Divergence.

    MACD line = EMA(fast) - EMA(slow); Signal = EMA(MACD line, signal_period);
    Histogram = MACD - Signal. EMAs use adjust=False (the standard recursive
    formula used by charting platforms), not pandas' default adjust=True.
    """

    REQUIRED_COLUMNS = {"Close"}

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if signal_period < 1:
            raise ValueError("signal_period must be >= 1")
        super().__init__(slow_period)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        close = df["Close"]

        ema_fast = close.ewm(span=self.fast_period, adjust=False, min_periods=self.fast_period).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False, min_periods=self.slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(
            span=self.signal_period, adjust=False, min_periods=self.signal_period
        ).mean()
        histogram = macd_line - signal_line

        return pd.DataFrame(
            {"MACD": macd_line, "Signal": signal_line, "Histogram": histogram}, index=df.index
        )
