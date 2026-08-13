from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd


class Indicator(ABC):
    """
    Base class for a technical indicator computed from an OHLCV DataFrame.

    Subclasses must define REQUIRED_COLUMNS and implement compute(), which
    returns a DataFrame indexed like the input with one column per output
    series (e.g. MACD/Signal/Histogram).
    """

    REQUIRED_COLUMNS: set = {"Close"}

    def __init__(self, period: int):
        if period < 1:
            raise ValueError(f"{self.__class__.__name__} period must be >= 1, got {period}")
        self.period = period

    def _validate(self, df: pd.DataFrame) -> None:
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} requires column(s) {sorted(missing)} in OHLCV data"
            )
        if len(df) < self.period:
            raise ValueError(
                f"{self.__class__.__name__} needs at least {self.period} bars of history, "
                f"got {len(df)}"
            )

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame indexed like df with this indicator's output column(s)."""
        raise NotImplementedError

    def latest(self, df: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Return the most recent indicator values as plain python floats (NaN -> None)."""
        result = self.compute(df)
        if result.empty:
            return None
        last_row = result.iloc[-1]
        return {
            column: (None if pd.isna(value) else float(value))
            for column, value in last_row.items()
        }
