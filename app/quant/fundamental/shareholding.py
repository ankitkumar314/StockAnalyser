"""
Shareholding computer.

Reads shareholding_pattern JSONB and returns a quarter-end-dated DataFrame
with columns [promoter_pct, dii_pct, fii_pct, public_pct] (one row per
quarter).
"""
from typing import List, Optional

import pandas as pd

from app.quant.fundamental.base import (
    FundamentalComputer,
    _safe_float,
    quarter_end_dates,
)


def _extract(raw: dict, candidates: List[str], n: int) -> List[Optional[float]]:
    """Try each candidate key; return a list of floats aligned to `n` quarters."""
    for key in candidates:
        v = raw.get(key)
        if isinstance(v, list):
            return [
                _safe_float(v[i]) if i < len(v) else None
                for i in range(n)
            ]
        if isinstance(v, (int, float)):
            return [_safe_float(v)] * n
    return [None] * n


class Shareholding(FundamentalComputer):
    """
    Promoter / DII / FII / Public shareholding (%) from
    shareholding_pattern JSONB.

    Columns: promoter_pct, dii_pct, fii_pct, public_pct
    """

    def compute(self, months: List[str], raw: dict) -> pd.DataFrame:
        dates = quarter_end_dates(months)
        n = len(months)

        promoter = _extract(raw, ["Promoters", "Promoter", "promoter"], n)
        dii      = _extract(raw, ["DIIs", "DII", "dii"],               n)
        fii      = _extract(raw, ["FIIs", "FII", "fii"],               n)
        public   = _extract(raw, ["Public", "public"],                 n)

        df = pd.DataFrame(
            {
                "promoter_pct": promoter,
                "dii_pct":      dii,
                "fii_pct":      fii,
                "public_pct":   public,
            },
            index=dates,
        )
        df.index.name = "date"
        return df.sort_index()
