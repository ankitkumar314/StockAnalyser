import numpy as np
import pandas as pd

from app.quant.indicators.atr import ATR
from app.quant.indicators.base import Indicator


class ADX(Indicator):
    """
    Average Directional Index (Wilder).

    +DM/-DM are smoothed with Wilder's moving average, divided by Wilder-smoothed
    True Range to get +DI/-DI, and ADX is the Wilder-smoothed average of DX =
    100 * |+DI - -DI| / (+DI + -DI). Division-by-zero on flat bars (zero range or
    +DI == -DI == 0) is guarded and yields NaN rather than inf, since a flat bar
    carries no directional signal.
    """

    REQUIRED_COLUMNS = {"High", "Low", "Close"}

    def __init__(self, period: int = 14):
        super().__init__(period)
        self._atr = ATR(period)

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        high, low = df["High"], df["Low"]

        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index
        )
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index
        )

        atr = self._atr.compute(df)["ATR"].replace(0, np.nan)
        alpha = 1 / self.period

        smoothed_plus_dm = plus_dm.ewm(alpha=alpha, adjust=False, min_periods=self.period).mean()
        smoothed_minus_dm = minus_dm.ewm(alpha=alpha, adjust=False, min_periods=self.period).mean()

        plus_di = 100 * (smoothed_plus_dm / atr)
        minus_di = 100 * (smoothed_minus_dm / atr)

        di_sum = (plus_di + minus_di).replace(0, np.nan)
        dx = 100 * (plus_di - minus_di).abs() / di_sum
        adx = dx.ewm(alpha=alpha, adjust=False, min_periods=self.period).mean()

        return pd.DataFrame({"ADX": adx, "+DI": plus_di, "-DI": minus_di}, index=df.index)
