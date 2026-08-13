import pandas as pd

from app.quant.indicators.base import Indicator


class ATR(Indicator):
    """
    Average True Range (Wilder).

    True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|), smoothed with
    Wilder's moving average (equivalent to an EWM with alpha=1/period).
    """

    REQUIRED_COLUMNS = {"High", "Low", "Close"}

    def __init__(self, period: int = 14):
        super().__init__(period)

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        high, low, close = df["High"], df["Low"], df["Close"]
        prev_close = close.shift(1)

        true_range = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1, skipna=False)

        atr = true_range.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        return pd.DataFrame({"ATR": atr}, index=df.index)
