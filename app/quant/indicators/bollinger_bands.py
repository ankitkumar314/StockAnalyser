import numpy as np
import pandas as pd

from app.quant.indicators.base import Indicator


class BollingerBands(Indicator):
    """
    Bollinger Bands: middle band = SMA(period), upper/lower = middle +/- num_std
    population standard deviations (ddof=0, matching the standard Bollinger Band
    definition).
    """

    REQUIRED_COLUMNS = {"Close"}

    def __init__(self, period: int = 20, num_std: float = 2.0):
        if num_std <= 0:
            raise ValueError("num_std must be > 0")
        super().__init__(period)
        self.num_std = num_std

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        close = df["Close"]

        middle = close.rolling(self.period).mean()
        std = close.rolling(self.period).std(ddof=0)
        upper = middle + self.num_std * std
        lower = middle - self.num_std * std
        bandwidth = upper - lower
        percent_b = (close - lower) / bandwidth.replace(0, np.nan)

        return pd.DataFrame(
            {
                "MiddleBand": middle,
                "UpperBand": upper,
                "LowerBand": lower,
                "Bandwidth": bandwidth,
                "PercentB": percent_b,
            },
            index=df.index,
        )
