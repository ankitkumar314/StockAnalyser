"""
StockPE, StockPB, NiftyPE, Nifty500PE computers — data from screener.in
chart API via ScreenerPEService (no yfinance dependency).

Each class follows the FundamentalComputer ABC:
  compute(months, raw) → pd.DataFrame   (date-indexed, native resolution)

The raw screener data is weekly (stock PE) or bi-weekly (index PE). We keep
it at that native resolution, tz-naive and sorted ascending, so callers can
reindex it directly onto a daily price index with `method="ffill"`.
"""
import logging
from typing import List, Optional

import pandas as pd

from app.quant.fundamental.base import FundamentalComputer
from app.services.screener_pe_service import ScreenerPEService

logger = logging.getLogger(__name__)


def _prepare(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Tz-naive, sorted, single-column DataFrame ready for ffill-reindexing."""
    if df.empty:
        return df
    df = df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df[[col]].sort_index()


class StockPE(FundamentalComputer):
    """
    Trailing P/E for a stock from screener.in chart API.

    Initialise with the screener URL stored in stocks.screener_link
    (e.g. "https://www.screener.in/company/KALYANKJIL/") OR a known
    numeric company_id.

    compute() returns a date-indexed DataFrame with column "stock_pe".
    """

    def __init__(
        self,
        screener_url: Optional[str] = None,
        company_id: Optional[str] = None,
        days: int = 1825,
        consolidated: bool = True,
    ):
        self._svc = ScreenerPEService(
            screener_url=screener_url,
            company_id=company_id,
            days=days,
            consolidated=consolidated,
        )

    def compute(self, months: List[str] = None, raw: dict = None) -> pd.DataFrame:  # type: ignore[override]
        """months / raw unused — data comes from screener.in."""
        raw_df = self._svc.get_stock_pe()
        return _prepare(raw_df, "stock_pe")

    def latest(self, months=None, raw=None) -> Optional[dict]:  # type: ignore[override]
        pe = self._svc.get_current_pe()
        return {"stock_pe": pe} if pe is not None else None


class StockPB(FundamentalComputer):
    """
    Trailing Price-to-Book for a stock from screener.in chart API.

    Daily resolution (unlike StockPE's weekly). Stock-only — screener's
    index pages (Nifty 50 / Nifty 500) don't expose a P/B series.

    Initialise with the screener URL stored in stocks.screener_link
    (e.g. "https://www.screener.in/company/KALYANKJIL/") OR a known
    numeric company_id.

    compute() returns a date-indexed DataFrame with column "stock_pb".
    """

    def __init__(
        self,
        screener_url: Optional[str] = None,
        company_id: Optional[str] = None,
        days: int = 1825,
        consolidated: bool = True,
    ):
        self._svc = ScreenerPEService(
            screener_url=screener_url,
            company_id=company_id,
            days=days,
            consolidated=consolidated,
        )

    def compute(self, months: List[str] = None, raw: dict = None) -> pd.DataFrame:  # type: ignore[override]
        """months / raw unused — data comes from screener.in."""
        raw_df = self._svc.get_stock_pb()
        return _prepare(raw_df, "stock_pb")

    def latest(self, months=None, raw=None) -> Optional[dict]:  # type: ignore[override]
        df = self.compute()
        if df.empty:
            return None
        vals = df["stock_pb"].dropna()
        return {"stock_pb": float(vals.iloc[-1])} if not vals.empty else None


class NiftyPE(FundamentalComputer):
    """
    Nifty 50 P/E from screener.in (company ID 1272594).
    compute() returns a date-indexed DataFrame with column "nifty_pe".
    """

    def __init__(self, days: int = 1825):
        self._days = days

    def compute(self, months: List[str] = None, raw: dict = None) -> pd.DataFrame:  # type: ignore[override]
        raw_df = ScreenerPEService.get_nifty_pe(self._days)
        return _prepare(raw_df, "nifty_pe")

    def latest(self, months=None, raw=None) -> Optional[dict]:  # type: ignore[override]
        df = self.compute()
        if df.empty:
            return None
        vals = df["nifty_pe"].dropna()
        return {"nifty_pe": float(vals.iloc[-1])} if not vals.empty else None


class Nifty500PE(FundamentalComputer):
    """
    Nifty 500 P/E from screener.in (company ID 1272615).
    compute() returns a date-indexed DataFrame with column "nifty500_pe".
    """

    def __init__(self, days: int = 1825):
        self._days = days

    def compute(self, months: List[str] = None, raw: dict = None) -> pd.DataFrame:  # type: ignore[override]
        raw_df = ScreenerPEService.get_nifty500_pe(self._days)
        return _prepare(raw_df, "nifty500_pe")

    def latest(self, months=None, raw=None) -> Optional[dict]:  # type: ignore[override]
        df = self.compute()
        if df.empty:
            return None
        vals = df["nifty500_pe"].dropna()
        return {"nifty500_pe": float(vals.iloc[-1])} if not vals.empty else None
