"""
Response model for GET /fundamental-analysis/{ticker}.

Returns a flat list of daily records (DataFrame-ready JSON) — one row per
trading day, same grain as TechnicalAnalysisService._fetch_ohlcv — so the
fundamentals here can be merged column-wise with a technical-indicator
DataFrame keyed on the same daily date index for ML feature building.

Quarterly/weekly source series (growth, shareholding, P/E) are forward-filled
onto that daily index: a quarter's figures hold constant for every trading
day until the next quarter's figures are known.

Shape returned:
  {
    "ticker": "KALYANKJIL",
    "records": [
      {
        "date": "2023-07-03",
        "Open": 560.1, "High": 565.4, "Low": 558.0, "Close": 562.3, "Volume": 1234567,
        "quarter": "Sep2023",
        "sales_growth_qoq": null,
        "sales_growth_yoy": null,
        "op_growth_qoq": null,
        "op_growth_yoy": null,
        "np_growth_qoq": null,
        "np_growth_yoy": null,
        "promoter_pct": 65.5,
        "dii_pct": 12.1,
        "fii_pct": 8.3,
        "public_pct": 14.1,
        "stock_pe": null,
        "stock_pb": null,
        "nifty_pe": null,
        "nifty500_pe": null
      },
      ...
    ]
  }

Usage in Python:
  import pandas as pd, requests
  r = requests.get("http://localhost:8000/fundamental-analysis/KALYANKJIL")
  df = pd.DataFrame(r.json()["records"])
  df["date"] = pd.to_datetime(df["date"])
  df = df.set_index("date")
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FundamentalRecord(BaseModel):
    """One row in the flat DataFrame-ready output (one trading day)."""
    date: str                            # "YYYY-MM-DD"
    Open: Optional[float] = None
    High: Optional[float] = None
    Low: Optional[float] = None
    Close: Optional[float] = None
    Volume: Optional[float] = None
    quarter: Optional[str] = None        # most recently known quarter label, e.g. "Sep2023"

    # Growth (QoQ / YoY %) — held constant through the quarter, ffilled daily
    sales_growth_qoq: Optional[float] = None
    sales_growth_yoy: Optional[float] = None
    op_growth_qoq: Optional[float] = None
    op_growth_yoy: Optional[float] = None
    np_growth_qoq: Optional[float] = None
    np_growth_yoy: Optional[float] = None

    # Shareholding % — held constant through the quarter, ffilled daily
    promoter_pct: Optional[float] = None
    dii_pct: Optional[float] = None
    fii_pct: Optional[float] = None
    public_pct: Optional[float] = None

    # P/E and P/B ratios — screener.in weekly (PE) / daily (PB), ffilled daily
    stock_pe: Optional[float] = None
    stock_pb: Optional[float] = None
    nifty_pe: Optional[float] = None
    nifty500_pe: Optional[float] = None


class FundamentalAnalysisResponse(BaseModel):
    ticker: str
    records: List[Dict[str, Any]]   # list of FundamentalRecord dicts

    # Convenience snapshot (latest available values)
    current_pe: Optional[float] = None
    current_pb: Optional[float] = None
    latest_nifty_pe: Optional[float] = None
    latest_nifty500_pe: Optional[float] = None
    latest_promoter_pct: Optional[float] = None
    latest_dii_pct: Optional[float] = None
    latest_fii_pct: Optional[float] = None
