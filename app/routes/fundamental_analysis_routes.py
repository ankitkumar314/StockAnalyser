"""
Fundamental analysis routes.

GET /fundamental-analysis/{ticker}
    Returns a daily DataFrame-ready record list — one row per trading day,
    same grain as TechnicalAnalysisService._fetch_ohlcv (Open/High/Low/Close/
    Volume) plus growth (sales / operating-profit / net-profit), shareholding
    (promoter / DII / FII / public) and P/E columns, each forward-filled from
    its quarterly/weekly source so every trading day carries the most
    recently known fundamental values. Meant to be merged with technical
    indicators for downstream ML feature building.
"""
from fastapi import APIRouter, Query

from app.controllers.fundamental_analysis_controller import FundamentalAnalysisController
from app.models.fundamental_analysis import FundamentalAnalysisResponse

router = APIRouter(prefix="/fundamental-analysis", tags=["fundamental-analysis"])

_controller = FundamentalAnalysisController()


@router.get("/{ticker}", response_model=FundamentalAnalysisResponse)
def get_fundamental_analysis(
    ticker: str,
    period: str = Query("5y", description="yfinance history period, e.g. 1y, 5y, max"),
    interval: str = Query("1d", description="yfinance bar interval, e.g. 1d, 1wk"),
    granularity: str = Query(
        "daily",
        description=(
            "Response row granularity. 'daily' (default) — one row per trading "
            "day. 'monthly' — the same daily frame downsampled to one row per "
            "calendar month (OHLC aggregated, other columns last-known-value); "
            "the underlying daily computation is unchanged either way."
        ),
    ),
):
    """
    Return a fundamentals-on-price DataFrame for `ticker`, at daily or
    monthly granularity.

    **Data sources**
    - Price index (Open/High/Low/Close/Volume): yfinance, same fetch used by
      `GET /technical-analysis/{ticker}` — this is the daily grain every
      other column is forward-filled onto, before any `granularity` reshape.
    - Growth series (QoQ & YoY): `stock_scrape_data.growth_sales`,
      `growth_operating_profit`, `growth_net_profit`, one value per quarter,
      held constant until the next quarter's figure is known.
    - Shareholding: `stock_scrape_data.shareholding_pattern`, same quarterly
      hold-forward.
    - P/E series: screener.in weekly/bi-weekly P/E for the stock, Nifty 50
      and Nifty 500, forward-filled onto the daily index.
    - P/B: screener.in daily Price-to-Book for the stock (stock-only — not
      available for the Nifty 50/500 index pages), forward-filled onto the
      daily index.

    **Prerequisites**
    Run `POST /scrape/get-financial-data` for the ticker at least once so that
    scrape data is available in the database.

    **Indian tickers**
    Pass the bare NSE ticker (e.g. `KALYANKJIL`); the endpoint automatically
    appends `.NS` for Yahoo Finance lookups. Pass a full Yahoo Finance symbol
    (e.g. `AAPL`, `RELIANCE.BO`) for anything else.
    """
    return _controller.get_fundamental_analysis(
        ticker, period=period, interval=interval, granularity=granularity
    )
