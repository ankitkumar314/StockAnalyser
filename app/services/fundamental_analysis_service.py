"""
Deterministic fundamental analysis over screener.in scrape data (v3).

Input is the same JSON shape produced by ScraperService / stored in
stock_scrape_data ("quarters", "profit-loss", "balance-sheet", "cash-flow",
"ratios", "shareholding" sections; values in INR crores, percentages as
strings like "26%"). All functions are pure and stdlib-only so they can be
unit-tested and run offline without a database.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _pct(value) -> Optional[float]:
    """Parse '26%' / '26.5%' / 26 into a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def _last(values: Optional[List], default=None):
    return values[-1] if values else default


def _cagr(series: Optional[List[float]], years: int) -> Optional[float]:
    """CAGR in percent over the trailing `years` using annual series."""
    if not series or len(series) < years + 1:
        return None
    start, end = series[-(years + 1)], series[-1]
    if start is None or end is None or start <= 0 or end <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def _ttm(series: Optional[List[float]]) -> Optional[float]:
    if not series or len(series) < 4:
        return None
    return sum(series[-4:])


def _prev_ttm(series: Optional[List[float]]) -> Optional[float]:
    if not series or len(series) < 8:
        return None
    return sum(series[-8:-4])


def _growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous <= 0:
        return None
    return (current / previous - 1) * 100


class FundamentalAnalysisService:
    """Turns raw screener scrape JSON into analyst-grade derived metrics."""

    # ------------------------------------------------------------------ growth
    @staticmethod
    def growth_profile(data: Dict) -> Dict:
        q = data.get("quarters", {}) or {}
        pl = data.get("profit-loss", {}) or {}

        sales_q = q.get("Sales")
        np_q = q.get("Net Profit")
        eps_q = q.get("EPS in Rs")

        sales_ttm = _ttm(sales_q)
        np_ttm = _ttm(np_q)

        return {
            "sales_ttm": sales_ttm,
            "net_profit_ttm": np_ttm,
            "eps_ttm": _ttm(eps_q),
            "sales_ttm_growth_percent": _growth(sales_ttm, _prev_ttm(sales_q)),
            "net_profit_ttm_growth_percent": _growth(np_ttm, _prev_ttm(np_q)),
            "latest_quarter_sales_yoy_percent": (
                _growth(sales_q[-1], sales_q[-5]) if sales_q and len(sales_q) >= 5 else None),
            "latest_quarter_np_yoy_percent": (
                _growth(np_q[-1], np_q[-5]) if np_q and len(np_q) >= 5 else None),
            "sales_cagr_3y": _cagr(pl.get("Sales"), 3),
            "sales_cagr_5y": _cagr(pl.get("Sales"), 5),
            "profit_cagr_3y": _cagr(pl.get("Net Profit"), 3),
            "profit_cagr_5y": _cagr(pl.get("Net Profit"), 5),
            "eps_cagr_3y": _cagr(pl.get("EPS in Rs"), 3),
        }

    # ----------------------------------------------------------------- quality
    @staticmethod
    def quality_profile(data: Dict) -> Dict:
        q = data.get("quarters", {}) or {}
        pl = data.get("profit-loss", {}) or {}
        bs = data.get("balance-sheet", {}) or {}
        cf = data.get("cash-flow", {}) or {}
        ratios = data.get("ratios", {}) or {}

        opm_q = [x for x in (_pct(v) for v in q.get("OPM %", [])) if x is not None]
        opm_recent = sum(opm_q[-4:]) / 4 if len(opm_q) >= 4 else None
        opm_prior = sum(opm_q[-8:-4]) / 4 if len(opm_q) >= 8 else None

        cfo = _last(cf.get("Cash from Operating Activity"))
        fcf = _last(cf.get("Free Cash Flow"))
        pat = _last(pl.get("Net Profit"))
        cfo_to_pat = (cfo / pat * 100) if (cfo is not None and pat) else None

        roce_series = [x for x in (_pct(v) for v in ratios.get("ROCE %", [])) if x is not None]
        borrowings = bs.get("Borrowings") or []
        equity = _last(bs.get("Equity Capital"))
        reserves = _last(bs.get("Reserves"))
        net_worth = (equity or 0) + (reserves or 0)
        debt = _last(borrowings)

        ccc = ratios.get("Cash Conversion Cycle") or []
        debtor_days = ratios.get("Debtor Days") or []

        return {
            "opm_recent_4q_percent": round(opm_recent, 1) if opm_recent is not None else None,
            "opm_prior_4q_percent": round(opm_prior, 1) if opm_prior is not None else None,
            "opm_trend_pp": (round(opm_recent - opm_prior, 1)
                             if opm_recent is not None and opm_prior is not None else None),
            "cfo_latest": cfo,
            "free_cash_flow_latest": fcf,
            "cfo_to_pat_percent": round(cfo_to_pat, 0) if cfo_to_pat is not None else None,
            "roce_latest_percent": _last(roce_series),
            "roce_3y_ago_percent": roce_series[-4] if len(roce_series) >= 4 else None,
            "debt_latest": debt,
            "debt_3y_ago": borrowings[-4] if len(borrowings) >= 4 else None,
            "debt_to_equity": round(debt / net_worth, 2) if (debt is not None and net_worth > 0) else None,
            "cash_conversion_cycle_latest": _last(ccc),
            "cash_conversion_cycle_3y_ago": ccc[-4] if len(ccc) >= 4 else None,
            "debtor_days_latest": _last(debtor_days),
            "dividend_payout_latest_percent": _pct(_last((data.get("profit-loss") or {}).get("Dividend Payout %"))),
        }

    # ------------------------------------------------------------ shareholding
    @staticmethod
    def shareholding_profile(data: Dict) -> Dict:
        sh = data.get("shareholding", {}) or {}

        def series(key):
            return [x for x in (_pct(v) for v in sh.get(key, [])) if x is not None]

        def change(values, n):
            return round(values[-1] - values[-(n + 1)], 2) if len(values) > n else None

        promoters, fiis, diis, public = (series(k) for k in ("Promoters", "FIIs", "DIIs", "Public"))
        holders = sh.get("No. of Shareholders") or []

        return {
            "promoter_latest_percent": _last(promoters),
            "promoter_change_4q_pp": change(promoters, 4),
            "fii_latest_percent": _last(fiis),
            "fii_change_4q_pp": change(fiis, 4),
            "fii_change_full_window_pp": (round(fiis[-1] - fiis[0], 2) if len(fiis) > 1 else None),
            "dii_latest_percent": _last(diis),
            "dii_change_4q_pp": change(diis, 4),
            "public_latest_percent": _last(public),
            "shareholders_latest": _last(holders),
            "shareholders_change_4q_percent": (
                round((holders[-1] / holders[-5] - 1) * 100, 1)
                if len(holders) >= 5 and holders[-5] else None),
        }

    # --------------------------------------------------------------- valuation
    @staticmethod
    def valuation_profile(data: Dict, current_price: Optional[float]) -> Dict:
        q = data.get("quarters", {}) or {}
        eps_ttm = _ttm(q.get("EPS in Rs"))
        growth = FundamentalAnalysisService.growth_profile(data)

        pe_ttm = (current_price / eps_ttm) if (current_price and eps_ttm and eps_ttm > 0) else None
        # PEG against 3y profit CAGR (fall back to TTM profit growth)
        g = growth.get("profit_cagr_3y") or growth.get("net_profit_ttm_growth_percent")
        peg = (pe_ttm / g) if (pe_ttm and g and g > 0) else None

        return {
            "current_price": current_price,
            "eps_ttm": round(eps_ttm, 2) if eps_ttm is not None else None,
            "pe_ttm": round(pe_ttm, 1) if pe_ttm is not None else None,
            "earnings_yield_percent": round(1 / pe_ttm * 100, 2) if pe_ttm else None,
            "growth_used_for_peg_percent": round(g, 1) if g is not None else None,
            "peg": round(peg, 2) if peg is not None else None,
        }

    # ------------------------------------------------------------------- flags
    @staticmethod
    def flags(data: Dict) -> Dict:
        """Rule-based red flags and positives with human-readable messages."""
        growth = FundamentalAnalysisService.growth_profile(data)
        quality = FundamentalAnalysisService.quality_profile(data)
        sh = FundamentalAnalysisService.shareholding_profile(data)

        red, positive = [], []

        g = growth.get("net_profit_ttm_growth_percent")
        if g is not None:
            if g > 15:
                positive.append(f"Strong TTM net profit growth: {g:.1f}% YoY")
            elif g <= 0:
                red.append(f"TTM net profit declining: {g:.1f}% YoY")

        opm_trend = quality.get("opm_trend_pp")
        if opm_trend is not None:
            if opm_trend <= -1.5:
                red.append(f"Operating margin compressed {abs(opm_trend):.1f}pp vs prior 4 quarters")
            elif opm_trend >= 1.0:
                positive.append(f"Operating margin expanded {opm_trend:.1f}pp vs prior 4 quarters")

        cfo_pat = quality.get("cfo_to_pat_percent")
        if cfo_pat is not None:
            if cfo_pat < 60:
                red.append(f"Weak cash conversion: CFO is only {cfo_pat:.0f}% of reported PAT")
            elif cfo_pat >= 80:
                positive.append(f"Strong cash conversion: CFO at {cfo_pat:.0f}% of PAT")

        roce, roce_prev = quality.get("roce_latest_percent"), quality.get("roce_3y_ago_percent")
        if roce is not None:
            if roce >= 18:
                positive.append(f"Healthy ROCE at {roce:.0f}%")
            elif roce < 10:
                red.append(f"Low ROCE at {roce:.0f}%")
            if roce_prev is not None and roce - roce_prev >= 3:
                positive.append(f"ROCE improving: {roce_prev:.0f}% → {roce:.0f}% over 3 years")
            elif roce_prev is not None and roce - roce_prev <= -3:
                red.append(f"ROCE deteriorating: {roce_prev:.0f}% → {roce:.0f}% over 3 years")

        debt, debt_prev = quality.get("debt_latest"), quality.get("debt_3y_ago")
        if debt is not None and debt_prev:
            chg = (debt / debt_prev - 1) * 100
            if chg <= -20:
                positive.append(f"Borrowings reduced {abs(chg):.0f}% over 3 years")
            elif chg >= 40:
                red.append(f"Borrowings up {chg:.0f}% over 3 years")

        ccc, ccc_prev = (quality.get("cash_conversion_cycle_latest"),
                         quality.get("cash_conversion_cycle_3y_ago"))
        if ccc is not None and ccc_prev is not None:
            if ccc - ccc_prev <= -20:
                positive.append(f"Cash conversion cycle improved {ccc_prev:.0f} → {ccc:.0f} days")
            elif ccc - ccc_prev >= 30:
                red.append(f"Cash conversion cycle worsened {ccc_prev:.0f} → {ccc:.0f} days")

        promoter_chg = sh.get("promoter_change_4q_pp")
        if promoter_chg is not None:
            if promoter_chg <= -1:
                red.append(f"Promoter stake down {abs(promoter_chg):.1f}pp over 4 quarters")
            elif promoter_chg >= 0.5:
                positive.append(f"Promoter stake up {promoter_chg:.1f}pp over 4 quarters")

        fii_chg = sh.get("fii_change_full_window_pp")
        if fii_chg is not None:
            if fii_chg <= -3:
                red.append(f"Sustained FII selling: stake down {abs(fii_chg):.1f}pp over reported window")
            elif fii_chg >= 3:
                positive.append(f"FII stake up {fii_chg:.1f}pp over reported window")

        dii_chg = sh.get("dii_change_4q_pp")
        if dii_chg is not None and dii_chg >= 1:
            positive.append(f"DIIs absorbing supply: stake up {dii_chg:.1f}pp over 4 quarters")

        return {"red_flags": red, "positives": positive}

    # ----------------------------------------------------------------- summary
    @staticmethod
    def analyze(data: Dict, current_price: Optional[float] = None) -> Dict:
        """Full deterministic fundamental view for one stock's scrape data."""
        return {
            "growth": FundamentalAnalysisService.growth_profile(data),
            "quality": FundamentalAnalysisService.quality_profile(data),
            "shareholding": FundamentalAnalysisService.shareholding_profile(data),
            "valuation": FundamentalAnalysisService.valuation_profile(data, current_price),
            **FundamentalAnalysisService.flags(data),
        }
