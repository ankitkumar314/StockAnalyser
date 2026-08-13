import numpy as np
import pandas as pd

from app.quant.indicators.base import Indicator


class RSI(Indicator):
    """
    Relative Strength Index (Wilder).

    Average gain/loss are smoothed with Wilder's moving average (EWM, alpha=1/period).
    When average loss is exactly zero (pure uptrend within the lookback), RSI is
    defined as 100 rather than left as NaN/inf from a zero-division.
    """

    REQUIRED_COLUMNS = {"Close"}

    def __init__(self, period: int = 14):
        super().__init__(period)

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        close = df["Close"]
        change = close.diff()
        gain = change.clip(lower=0)
        loss = -change.clip(upper=0)

        alpha = 1 / self.period
        avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=self.period).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=self.period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss != 0, 100.0)
        rsi = rsi.where(avg_gain.notna(), np.nan)

        return pd.DataFrame({"RSI": rsi}, index=df.index)
