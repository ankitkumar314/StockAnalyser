"""
Base class for fundamental data computers.

Each subclass receives a raw dict from stock_scrape_data and a list of
quarter-label strings (months), and returns a tidy pandas DataFrame
indexed by the quarter-end calendar date (one row per quarter).

Callers align this quarterly DataFrame onto a daily price index (e.g. the
one produced by TechnicalAnalysisService._fetch_ohlcv) via
`df.reindex(daily_index, method="ffill")`, so every trading day carries the
most recently known fundamental values.
"""
import calendar
from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Quarter-label → quarter-end date
# ---------------------------------------------------------------------------
_MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def quarter_labels(months: List[str]) -> pd.Series:
    """
    Parse quarter-label strings like ["Sep2023", "Dec2023", ...] into a
    pd.Series of the original (stripped) labels, indexed by the quarter-end
    calendar date (e.g. "Sep2023" -> 2023-09-30), sorted ascending.
    """
    pairs = []
    for label in months:
        clean = label.strip()
        for abbr, month in _MONTH_ABBR.items():
            if clean.lower().startswith(abbr):
                try:
                    year = int(clean[len(abbr):])
                    day = calendar.monthrange(year, month)[1]
                    pairs.append((pd.Timestamp(year=year, month=month, day=day), clean))
                except ValueError:
                    pass
                break
    pairs.sort(key=lambda p: p[0])
    index = pd.DatetimeIndex([p[0] for p in pairs], name="date")
    return pd.Series([p[1] for p in pairs], index=index, name="quarter")


def quarter_end_dates(months: List[str]) -> pd.DatetimeIndex:
    """One quarter-end date per entry in `months`, sorted ascending."""
    return quarter_labels(months).index


def _safe_float(value) -> Optional[float]:
    """Coerce scrape-table values to float, tolerating "53.99%" / "1,234" strings."""
    if isinstance(value, str):
        value = value.strip().replace(",", "").rstrip("%")
        if not value or value in ("-", "NA", "N/A"):
            return None
    try:
        v = float(value)
        return None if (v != v) else v
    except (TypeError, ValueError):
        return None


def _align(months: List[str], raw: dict, key: str) -> List[Optional[float]]:
    """Extract `key` list from `raw`, aligned 1-to-1 with `months`."""
    if not raw:
        return [None] * len(months)
    values = raw.get(key)
    if not isinstance(values, list):
        return [None] * len(months)
    return [
        _safe_float(values[i]) if i < len(values) else None
        for i in range(len(months))
    ]


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class FundamentalComputer(ABC):
    """
    Mirror of app.quant.indicators.base.Indicator for fundamental data.

    compute(months, raw) → pd.DataFrame
        months : list of quarter label strings from stock_scrape_data.months
        raw    : the JSONB column value (dict) from stock_scrape_data

    The returned DataFrame is quarter-end-dated (one row per quarter), with
    one column per output series. Reindex it onto a daily index with
    `method="ffill"` to carry each quarter's values forward day-by-day.
    """

    @abstractmethod
    def compute(self, months: List[str], raw: dict) -> pd.DataFrame:
        raise NotImplementedError

    def latest(self, months: List[str], raw: dict) -> Optional[dict]:
        df = self.compute(months, raw)
        if df is None or df.empty:
            return None
        last = df.iloc[-1]
        return {
            col: (None if pd.isna(v) else float(v))
            for col, v in last.items()
        }
