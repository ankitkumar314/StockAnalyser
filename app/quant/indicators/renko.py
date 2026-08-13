from typing import Dict, Optional

import pandas as pd

from app.quant.indicators.atr import ATR
from app.quant.indicators.base import Indicator


class Renko(Indicator):
    """
    Renko brick chart built from closing prices.

    Bricks are a fixed price size; a new brick (or several) is added whenever
    price has moved by at least one brick_size from the last brick's close.
    Unlike price/time bar charts, Renko bricks are indexed by brick number, not
    by the original OHLCV index, so compute() returns its own DataFrame shape
    (one row per brick) rather than one aligned to the input index.

    If brick_size is not given, it defaults to the latest ATR(atr_period) value,
    which is the standard way to size Renko bricks to a stock's own volatility.
    """

    REQUIRED_COLUMNS = {"High", "Low", "Close"}

    def __init__(self, brick_size: Optional[float] = None, atr_period: int = 14):
        super().__init__(atr_period)
        self.brick_size_override = brick_size
        self.atr_period = atr_period

    def _validate(self, df: pd.DataFrame) -> None:
        # An explicit brick_size only needs two closes to diff; the atr_period
        # minimum only applies when brick size must be derived from ATR.
        if self.brick_size_override is not None:
            missing = self.REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(
                    f"{self.__class__.__name__} requires column(s) {sorted(missing)} in OHLCV data"
                )
            if len(df) < 2:
                raise ValueError(f"{self.__class__.__name__} needs at least 2 bars of history, got {len(df)}")
            return
        super()._validate(df)

    def _resolve_brick_size(self, df: pd.DataFrame) -> float:
        if self.brick_size_override is not None:
            if self.brick_size_override <= 0:
                raise ValueError("brick_size must be > 0")
            return float(self.brick_size_override)

        atr_value = ATR(self.atr_period).compute(df)["ATR"].iloc[-1]
        if pd.isna(atr_value) or atr_value <= 0:
            raise ValueError(
                "Unable to derive a Renko brick size from ATR (insufficient/flat data); "
                "pass brick_size explicitly"
            )
        return float(atr_value)

    @staticmethod
    def _running_bar_numbers(directions):
        bar_numbers = []
        running = 0
        for direction in directions:
            if running == 0 or (running > 0) == (direction > 0):
                running += direction
            else:
                running = direction
            bar_numbers.append(running)
        return bar_numbers

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate(df)
        brick_size = self._resolve_brick_size(df)

        closes = df["Close"]
        bricks = []
        base_price = float(closes.iloc[0])

        for date, price in closes.iloc[1:].items():
            price = float(price)
            diff = price - base_price
            n_bricks = int(abs(diff) // brick_size)
            if n_bricks == 0:
                continue
            step = brick_size if diff > 0 else -brick_size
            direction = 1 if diff > 0 else -1
            for _ in range(n_bricks):
                open_price = base_price
                base_price += step
                bricks.append(
                    {"date": date, "open": open_price, "close": base_price, "direction": direction}
                )

        renko_df = pd.DataFrame(bricks, columns=["date", "open", "close", "direction"])
        if renko_df.empty:
            renko_df["bar_num"] = pd.Series(dtype=int)
        else:
            renko_df["bar_num"] = self._running_bar_numbers(renko_df["direction"].tolist())
        renko_df.attrs["brick_size"] = brick_size
        return renko_df

    def latest(self, df: pd.DataFrame) -> Optional[Dict]:
        renko_df = self.compute(df)
        if renko_df.empty:
            return {"brick_size": renko_df.attrs.get("brick_size"), "trend": None, "bar_num": None}
        last = renko_df.iloc[-1]
        return {
            "brick_size": renko_df.attrs.get("brick_size"),
            "trend": "up" if last["direction"] > 0 else "down",
            "bar_num": int(last["bar_num"]),
        }
