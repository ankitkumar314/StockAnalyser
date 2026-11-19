"""
ScreenerPEService — fetches P/E time-series data from screener.in chart API.

API shape:
  GET https://www.screener.in/api/company/{company_id}/chart/
      ?q=Price+to+Earning-Median+PE-EPS&days=1825&consolidated=true

Response:
  {
    "datasets": [
      {"metric": "Price to Earning", "label": "PE",
       "values": [["2024-01-05", 42.0], ...]},
      {"metric": "Median PE", "label": "Median PE",
       "values": [["2024-01-05", 36.0], ...]},
      {"metric": "EPS", "label": "TTM EPS",
       "values": [["2024-07-26", 41.02], ...]}
    ]
  }

For index PE (Nifty 50 / Nifty 500):
  GET /api/company/{company_id}/chart/?q=Index+PE-Median+Index+PE&days=1825

Known screener company IDs for indices:
  Nifty 50   : 1272594  → https://www.screener.in/company/NIFTY/
  Nifty 500  : 1272615  → https://www.screener.in/company/NIFTY500/
"""
import logging
import os
import re
from typing import Dict, Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BASE_URL = "https://www.screener.in"
_CHART_URL = _BASE_URL + "/api/company/{company_id}/chart/"

_NIFTY50_ID  = "1272594"
_NIFTY500_ID = "1272615"

_DEFAULT_DAYS = 1825   # 5 years

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.screener.in/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


# ---------------------------------------------------------------------------
# Helper: resolve numeric company ID from a screener URL or ticker
# ---------------------------------------------------------------------------
def _resolve_company_id(screener_url: str) -> Optional[str]:
    """
    Fetch the screener company page and extract `data-company-id` from the HTML.

    screener_url examples:
      https://www.screener.in/company/KALYANKJIL/
      https://www.screener.in/company/KALYANKJIL/consolidated/
    """
    try:
        resp = requests.get(screener_url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        m = re.search(r'data-company-id=["\'](\d+)["\']', resp.text)
        if m:
            return m.group(1)
        # Fallback: look for company_id in a JSON block
        m2 = re.search(r'"company_id"\s*:\s*(\d+)', resp.text)
        if m2:
            return m2.group(1)
        logger.warning(f"Could not find company ID in {screener_url}")
        return None
    except Exception as e:
        logger.error(f"Error resolving screener company ID from {screener_url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Core: call the chart API and parse into a dict of DataFrames
# ---------------------------------------------------------------------------
def _fetch_chart(
    company_id: str,
    q: str,
    days: int = _DEFAULT_DAYS,
    consolidated: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Call screener chart API and return a dict mapping metric label → DataFrame.

    Each DataFrame has:
      - DatetimeIndex (date, tz-naive)
      - single column "value"
    """
    params: Dict = {"q": q, "days": days}
    if consolidated:
        params["consolidated"] = "true"

    url = _CHART_URL.format(company_id=company_id)
    try:
        resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"ScreenerPEService: chart API failed for company_id={company_id}: {e}")
        return {}

    result: Dict[str, pd.DataFrame] = {}
    for dataset in data.get("datasets", []):
        metric = dataset.get("metric", "")
        values = dataset.get("values", [])
        if not values:
            continue
        try:
            df = pd.DataFrame(values, columns=["date", "value"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            result[metric] = df
        except Exception as e:
            logger.warning(f"Could not parse dataset '{metric}': {e}")

    return result


# ---------------------------------------------------------------------------
# Public service class
# ---------------------------------------------------------------------------
class ScreenerPEService:
    """
    Fetches P/E time-series from screener.in for a stock and for the
    Nifty 50 / Nifty 500 indices.

    Usage:
        svc = ScreenerPEService(screener_url="https://www.screener.in/company/KALYANKJIL/")
        stock_pe_df  = svc.get_stock_pe()     # DatetimeIndex, column "stock_pe"
        nifty_pe_df  = svc.get_nifty_pe()     # DatetimeIndex, column "nifty_pe"
        nifty500_df  = svc.get_nifty500_pe()  # DatetimeIndex, column "nifty500_pe"
    """

    def __init__(
        self,
        screener_url: Optional[str] = None,
        company_id: Optional[str] = None,
        days: int = _DEFAULT_DAYS,
        consolidated: bool = True,
    ):
        """
        Provide either a full screener_url (company page URL) or a resolved
        numeric company_id directly.
        """
        self._company_id: Optional[str] = company_id
        self._screener_url = screener_url
        self._days = days
        self._consolidated = consolidated
        self._stock_cache: Optional[Dict[str, pd.DataFrame]] = None
        self._pb_cache: Optional[Dict[str, pd.DataFrame]] = None

    def _ensure_company_id(self) -> Optional[str]:
        if self._company_id:
            return self._company_id
        if self._screener_url:
            self._company_id = _resolve_company_id(self._screener_url)
            return self._company_id
        logger.error("ScreenerPEService: no screener_url or company_id provided")
        return None

    def _stock_charts(self) -> Dict[str, pd.DataFrame]:
        if self._stock_cache is not None:
            return self._stock_cache
        cid = self._ensure_company_id()
        if not cid:
            self._stock_cache = {}
            return {}
        self._stock_cache = _fetch_chart(
            cid,
            q="Price to Earning-Median PE-EPS",
            days=self._days,
            consolidated=self._consolidated,
        )
        return self._stock_cache

    def _stock_pb_charts(self) -> Dict[str, pd.DataFrame]:
        if self._pb_cache is not None:
            return self._pb_cache
        cid = self._ensure_company_id()
        if not cid:
            self._pb_cache = {}
            return {}
        self._pb_cache = _fetch_chart(
            cid,
            q="Price to book value",
            days=self._days,
            consolidated=self._consolidated,
        )
        return self._pb_cache

    # -- public ----------------------------------------------------------------

    def get_stock_pe(self) -> pd.DataFrame:
        """
        Returns weekly stock P/E as a DataFrame with column "stock_pe",
        indexed by date (DatetimeIndex, tz-naive).
        """
        charts = self._stock_charts()
        df = charts.get("Price to Earning", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "stock_pe"})

    def get_stock_median_pe(self) -> pd.DataFrame:
        """Returns the screener Median PE series with column "median_pe"."""
        charts = self._stock_charts()
        df = charts.get("Median PE", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "median_pe"})

    def get_stock_eps(self) -> pd.DataFrame:
        """Returns the TTM EPS series with column "ttm_eps"."""
        charts = self._stock_charts()
        df = charts.get("EPS", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "ttm_eps"})

    def get_stock_pb(self) -> pd.DataFrame:
        """
        Returns daily stock Price-to-Book as a DataFrame with column
        "stock_pb", indexed by date (DatetimeIndex, tz-naive).

        Not available for index pages (Nifty 50 / Nifty 500 return null) —
        this is a stock-only metric.
        """
        charts = self._stock_pb_charts()
        df = charts.get("Price to book value", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "stock_pb"})

    @staticmethod
    def get_nifty_pe(days: int = _DEFAULT_DAYS) -> pd.DataFrame:
        """
        Returns Nifty 50 P/E series with column "nifty_pe".
        Uses screener company ID 1272594 (https://www.screener.in/company/NIFTY/).
        """
        charts = _fetch_chart(
            _NIFTY50_ID,
            q="Index PE-Median Index PE",
            days=days,
            consolidated=False,
        )
        df = charts.get("Index PE", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "nifty_pe"})

    @staticmethod
    def get_nifty500_pe(days: int = _DEFAULT_DAYS) -> pd.DataFrame:
        """
        Returns Nifty 500 P/E series with column "nifty500_pe".
        Uses screener company ID 1272615 (https://www.screener.in/company/NIFTY500/).
        """
        charts = _fetch_chart(
            _NIFTY500_ID,
            q="Index PE-Median Index PE",
            days=days,
            consolidated=False,
        )
        df = charts.get("Index PE", pd.DataFrame())
        if df.empty:
            return pd.DataFrame()
        return df.rename(columns={"value": "nifty500_pe"})

    def get_all(self) -> Dict[str, pd.DataFrame]:
        """
        Convenience: fetch stock PE, stock PB, Nifty PE, and Nifty500 PE in
        one call.

        Returns dict with keys: "stock_pe", "stock_pb", "nifty_pe", "nifty500_pe"
        each a DataFrame with a single value column and DatetimeIndex.
        """
        return {
            "stock_pe":   self.get_stock_pe(),
            "stock_pb":   self.get_stock_pb(),
            "nifty_pe":   self.get_nifty_pe(self._days),
            "nifty500_pe": self.get_nifty500_pe(self._days),
        }

    def get_current_pe(self) -> Optional[float]:
        """Return the latest available stock P/E as a scalar."""
        df = self.get_stock_pe()
        if df.empty:
            return None
        vals = df["stock_pe"].dropna()
        return float(vals.iloc[-1]) if not vals.empty else None
