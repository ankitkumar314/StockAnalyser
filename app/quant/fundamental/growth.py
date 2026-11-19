"""
SalesGrowth, OperatingProfitGrowth, NetProfitGrowth computers.

Each reads {qoq: [...], yoy: [...]} from the raw JSONB column and returns a
quarter-end-dated DataFrame with columns [qoq, yoy] (one row per quarter).
"""
from typing import List

import pandas as pd

from app.quant.fundamental.base import (
    FundamentalComputer,
    _align,
    quarter_end_dates,
)


class _GrowthComputer(FundamentalComputer):
    """Base for QoQ/YoY growth series from a growth JSONB column."""

    def compute(self, months: List[str], raw: dict) -> pd.DataFrame:
        dates = quarter_end_dates(months)
        qoq = _align(months, raw, "qoq")
        yoy = _align(months, raw, "yoy")

        df = pd.DataFrame({"qoq": qoq, "yoy": yoy}, index=dates)
        df.index.name = "date"
        return df.sort_index()


class SalesGrowth(_GrowthComputer):
    """QoQ / YoY sales growth (%) from growth_sales JSONB."""
    pass


class OperatingProfitGrowth(_GrowthComputer):
    """QoQ / YoY operating-profit growth (%) from growth_operating_profit JSONB."""
    pass


class NetProfitGrowth(_GrowthComputer):
    """QoQ / YoY net-profit growth (%) from growth_net_profit JSONB."""
    pass
