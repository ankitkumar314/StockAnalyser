import logging
from typing import List, Optional

import pandas as pd
from fastapi import HTTPException

from app.database.connection import DatabaseConnection
from app.database.stock_repository import StockRepository
from app.models.fundamental_analysis import FundamentalAnalysisResponse
from app.quant.fundamental import (
    NiftyPE,
    Nifty500PE,
    NetProfitGrowth,
    OperatingProfitGrowth,
    SalesGrowth,
    Shareholding,
    StockPE,
    StockPB,
)
from app.quant.fundamental.base import quarter_labels
from app.services.stock_scrape_data_service import StockScrapeDataService
from app.services.technical_analysis_service import TechnicalAnalysisService

logger = logging.getLogger(__name__)

DEFAULT_PERIOD = "5y"
DEFAULT_INTERVAL = "1d"
VALID_GRANULARITIES = {"daily", "monthly"}


def _last_non_none(series: pd.Series) -> Optional[float]:
    vals = series.dropna()
    return float(vals.iloc[-1]) if not vals.empty else None


def _resample_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Downsample the daily frame to one row per calendar month. Pure response
    reshaping — the daily frame it's built from is untouched.

    OHLC is aggregated (open=first, high=max, low=min, close=last,
    volume=sum); every other column (fundamentals — already ffilled onto
    the daily grain) is taken as its last known value in the month.
    """
    ohlc_agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    agg = {**ohlc_agg, **{c: "last" for c in df.columns if c not in ohlc_agg}}
    monthly = df.resample("ME").agg(agg)
    return monthly.dropna(how="all")


def _yfinance_ticker(ticker: str) -> str:
    """Bare NSE tickers (e.g. "KALYANKJIL") get ".NS"; anything with a dot
    already (e.g. "AAPL" has none, "RELIANCE.BO") is passed through as-is."""
    ticker = ticker.strip().upper()
    return ticker if "." in ticker else f"{ticker}.NS"


class FundamentalAnalysisController:
    """
    Orchestrates the fundamental data computers and assembles a daily
    DataFrame-ready response — same shape/grain as
    TechnicalAnalysisService._fetch_ohlcv (one row per trading day), with
    the quarterly fundamentals forward-filled onto that daily index so it
    can be joined directly to technical-indicator columns for ML feature
    building.
    """

    @classmethod
    def get_fundamental_analysis(
        cls,
        ticker: str,
        period: str = DEFAULT_PERIOD,
        interval: str = DEFAULT_INTERVAL,
        granularity: str = "daily",
    ) -> FundamentalAnalysisResponse:

        if granularity not in VALID_GRANULARITIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid granularity '{granularity}'; expected one of {sorted(VALID_GRANULARITIES)}.",
            )

        # ── 1. Load DB scrape data ─────────────────────────────────────────
        scrape = StockScrapeDataService.get_latest_scrape_data(ticker.upper())
        if scrape is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No scrape data found for ticker '{ticker}'. "
                    "Run POST /scrape/get-financial-data first."
                ),
            )

        months: List[str] = scrape.months or []
        if not months:
            raise HTTPException(
                status_code=422,
                detail=f"Scrape data for '{ticker}' has no months list.",
            )

        # ── 2. Daily price index — same fetch TechnicalAnalysisService uses ─
        yf_ticker = _yfinance_ticker(ticker)
        price_df = TechnicalAnalysisService._fetch_ohlcv(yf_ticker, period, interval)
        if price_df is None:
            raise HTTPException(
                status_code=404,
                detail=f"No price history found for ticker '{ticker}' ({yf_ticker}).",
            )

        # ── 3. Instantiate computers (mirrors: macd = MACD() etc.) ─────────
        sales_growth      = SalesGrowth()
        op_growth         = OperatingProfitGrowth()
        net_profit_growth = NetProfitGrowth()
        shareholding      = Shareholding()

        # Resolve screener URL from the stocks table so StockPE can call
        # the screener chart API (no yfinance needed for PE).
        screener_url: Optional[str] = None
        try:
            if DatabaseConnection.is_enabled():
                session = DatabaseConnection.get_session()
                if session:
                    try:
                        stock = StockRepository.get_by_ticker(session, ticker.upper())
                        if stock:
                            screener_url = stock.screener_link
                    finally:
                        session.close()
        except Exception as e:
            logger.warning(f"Could not resolve screener_url for {ticker}: {e}")

        stock_pe    = StockPE(screener_url=screener_url)
        stock_pb    = StockPB(screener_url=screener_url)
        nifty_pe    = NiftyPE()
        nifty500_pe = Nifty500PE()

        # ── 4. Compute quarterly series (mirrors: macd_df = macd.compute(df)) ─
        sales_df = sales_growth.compute(months,      scrape.growth_sales or {})
        op_df    = op_growth.compute(months,         scrape.growth_operating_profit or {})
        np_df    = net_profit_growth.compute(months, scrape.growth_net_profit or {})
        sh_df    = shareholding.compute(months,      scrape.shareholding_pattern or {})

        stock_pe_df = stock_pe.compute()
        stock_pb_df = stock_pb.compute()
        nifty_pe_df = nifty_pe.compute()
        nifty500_df = nifty500_pe.compute()

        quarterly = pd.concat([sales_df, op_df, np_df, sh_df], axis=1)
        quarterly.columns = [
            "sales_growth_qoq", "sales_growth_yoy",
            "op_growth_qoq",    "op_growth_yoy",
            "np_growth_qoq",    "np_growth_yoy",
            "promoter_pct",     "dii_pct", "fii_pct", "public_pct",
        ]
        quarterly.insert(0, "quarter", quarter_labels(months))
        quarterly = quarterly.sort_index()

        # Some series (notably shareholding) are filed later than quarterly
        # results, so the latest quarter(s) can be genuinely missing (None)
        # in a column while earlier quarters have values. Ffill across
        # quarters first so a not-yet-filed quarter inherits the last known
        # value instead of leaving a hole that the daily reindex below would
        # otherwise just propagate forward as None.
        quarterly = quarterly.ffill()

        # ── 5. Forward-fill everything onto the daily price index ──────────
        # Each quarter's figures hold until the next quarter's are known —
        # exactly the "most recently available" view an ML feature needs.
        daily_fundamentals = quarterly.reindex(price_df.index, method="ffill")

        for pe_df, col in [
            (stock_pe_df, "stock_pe"),
            (stock_pb_df, "stock_pb"),
            (nifty_pe_df, "nifty_pe"),
            (nifty500_df, "nifty500_pe"),
        ]:
            if not pe_df.empty:
                daily_fundamentals[col] = (
                    pe_df.sort_index().reindex(price_df.index, method="ffill")[pe_df.columns[0]]
                )
            else:
                daily_fundamentals[col] = None

        # ── 6. Join onto the price DataFrame (Open/High/Low/Close/Volume) ──
        result_df = price_df.join(daily_fundamentals)

        # ── 6b. Optional response-only reshape — the daily frame above is
        # the single source of truth; "monthly" just downsamples it for
        # callers that don't need day-level granularity.
        if granularity == "monthly":
            result_df = _resample_monthly(result_df)

        result_df.insert(0, "date", result_df.index.strftime("%Y-%m-%d"))

        # ── 7. Build flat records list (DataFrame-ready) ───────────────────
        records_df = result_df.reset_index(drop=True)
        records_df = records_df.astype(object).where(pd.notnull(records_df), None)
        records = records_df.to_dict("records")

        # ── 8. Latest snapshot values ───────────────────────────────────────
        def _latest(col):
            if col in result_df.columns:
                return _last_non_none(result_df[col])
            return None

        current_pe = _latest("stock_pe")
        if current_pe is None:
            # Fallback: ask the service directly (uses latest cached fetch)
            current_pe = stock_pe.latest() and stock_pe.latest().get("stock_pe")

        current_pb = _latest("stock_pb")
        if current_pb is None:
            current_pb = stock_pb.latest() and stock_pb.latest().get("stock_pb")

        return FundamentalAnalysisResponse(
            ticker=ticker.upper(),
            records=records,
            current_pe=current_pe,
            current_pb=current_pb,
            latest_nifty_pe=_latest("nifty_pe"),
            latest_nifty500_pe=_latest("nifty500_pe"),
            latest_promoter_pct=_latest("promoter_pct"),
            latest_dii_pct=_latest("dii_pct"),
            latest_fii_pct=_latest("fii_pct"),
        )
