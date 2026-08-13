"""
Deterministic 0-10 pillar scorecard + position-risk assessment (v3).

Takes the outputs of FundamentalAnalysisService and TechnicalIndicatorService
plus the Kite holding dict, and produces pillar scores, a composite score, a
rule-based stance label and explicit watch triggers. Pure & stdlib-only.

The stance labels are informational signals derived from fixed rules —
not investment advice.
"""
from typing import Dict, List, Optional


def _clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def _scale(value: Optional[float], points: List[tuple]) -> Optional[float]:
    """Piecewise-linear map: points = [(threshold, score), ...] ascending by threshold."""
    if value is None:
        return None
    if value <= points[0][0]:
        return points[0][1]
    if value >= points[-1][0]:
        return points[-1][1]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 <= value <= x2:
            return y1 + (y2 - y1) * (value - x1) / (x2 - x1)
    return None


class ScorecardService:

    # ----------------------------------------------------------------- pillars
    @staticmethod
    def growth_score(growth: Dict) -> Optional[float]:
        parts = []
        s = _scale(growth.get("net_profit_ttm_growth_percent"),
                   [(-20, 0), (0, 3), (15, 6), (30, 8), (60, 10)])
        if s is not None:
            parts.append((s, 0.5))
        s = _scale(growth.get("sales_cagr_3y"), [(-5, 0), (0, 2), (10, 5), (20, 8), (35, 10)])
        if s is not None:
            parts.append((s, 0.3))
        s = _scale(growth.get("latest_quarter_np_yoy_percent"),
                   [(-30, 0), (0, 3), (20, 6), (50, 9), (100, 10)])
        if s is not None:
            parts.append((s, 0.2))
        if not parts:
            return None
        total_w = sum(w for _, w in parts)
        return round(_clamp(sum(s * w for s, w in parts) / total_w), 1)

    @staticmethod
    def quality_score(quality: Dict) -> Optional[float]:
        parts = []
        s = _scale(quality.get("roce_latest_percent"), [(5, 0), (10, 3), (15, 6), (20, 8), (30, 10)])
        if s is not None:
            parts.append((s, 0.4))
        s = _scale(quality.get("cfo_to_pat_percent"), [(20, 0), (50, 3), (70, 6), (90, 9), (110, 10)])
        if s is not None:
            parts.append((s, 0.35))
        de = quality.get("debt_to_equity")
        if de is not None:
            parts.append((_scale(de, [(0.0, 10), (0.3, 8), (0.7, 6), (1.5, 3), (3.0, 0)]), 0.25))
        if not parts:
            return None
        total_w = sum(w for _, w in parts)
        return round(_clamp(sum(s * w for s, w in parts) / total_w), 1)

    @staticmethod
    def technical_score(ind: Dict) -> Optional[float]:
        if not ind or ind.get("error"):
            return None
        score = 5.0
        if ind.get("dma_crossover") == "golden_cross":
            score += 1.5
        elif ind.get("dma_crossover") == "death_cross":
            score -= 1.5
        p200 = ind.get("price_vs_dma200_percent")
        if p200 is not None:
            score += 1.0 if p200 > 0 else -1.0
        if ind.get("macd_trend") == "bullish":
            score += 1.0
        elif ind.get("macd_trend") == "bearish":
            score -= 1.0
        rsi = ind.get("rsi_14")
        if rsi is not None:
            if rsi >= 75:
                score -= 1.0          # overbought
            elif rsi >= 55:
                score += 0.5          # healthy momentum
            elif rsi < 30:
                score -= 0.5          # weak / oversold
        pct_from_high = ind.get("percent_from_52w_high")
        if pct_from_high is not None and pct_from_high <= -25:
            score -= 1.0              # deep in a drawdown
        return round(_clamp(score), 1)

    @staticmethod
    def valuation_score(valuation: Dict) -> Optional[float]:
        pe = valuation.get("pe_ttm")
        peg = valuation.get("peg")
        if peg is not None:
            s = _scale(peg, [(0.5, 10), (1.0, 8), (1.5, 6), (2.5, 4), (4.0, 2), (6.0, 0)])
        elif pe is not None:
            s = _scale(pe, [(8, 9), (15, 7), (25, 5), (40, 3), (70, 1)])
        else:
            return None
        return round(_clamp(s), 1)

    # ----------------------------------------------------------- position risk
    @staticmethod
    def position_risk(holding: Dict, ind: Dict) -> Dict:
        conc = holding.get("portfolio_concentration")
        pnl_pct = holding.get("profit_loss_percent")
        current_value = holding.get("current_value")

        notes = []
        if conc is not None:
            if conc >= 12:
                notes.append(f"High concentration: {conc:.1f}% of portfolio in a single stock")
            elif conc >= 8:
                notes.append(f"Elevated concentration: {conc:.1f}% of portfolio")

        value_at_10pct_fall = round(current_value * 0.10, 0) if current_value else None
        atr_pct = (ind or {}).get("atr_percent")
        vol = (ind or {}).get("annualized_volatility_percent")
        max_dd = (ind or {}).get("max_drawdown_percent")

        gain_cushion = None
        if pnl_pct is not None and pnl_pct > 0:
            # fall (from current price) that would wipe out the unrealized gain
            gain_cushion = round(pnl_pct / (100 + pnl_pct) * 100, 1)
            notes.append(
                f"A {gain_cushion}% fall from here would erase the entire "
                f"{pnl_pct:.1f}% unrealized gain")
        if vol is not None and vol >= 40:
            notes.append(f"High volatility stock: {vol:.0f}% annualized")

        return {
            "portfolio_concentration_percent": conc,
            "unrealized_pnl_percent": pnl_pct,
            "gain_erased_by_fall_percent": gain_cushion,
            "value_at_risk_10pct_fall": value_at_10pct_fall,
            "atr_percent": atr_pct,
            "annualized_volatility_percent": vol,
            "max_drawdown_1y_percent": max_dd,
            "notes": notes,
        }

    # ---------------------------------------------------------------- triggers
    @staticmethod
    def watch_triggers(holding: Dict, ind: Dict, fundamentals: Dict) -> List[str]:
        triggers = []
        ind = ind or {}
        dma200 = ind.get("dma_200")
        if dma200:
            triggers.append(
                f"Trend check: a daily close below the 200-DMA (~{dma200:.0f}) "
                f"would break the long-term uptrend")
        support = ind.get("support")
        if support:
            triggers.append(f"Nearest support ~{support:.0f}; a break below it targets deeper retracement")
        conc = holding.get("portfolio_concentration")
        if conc is not None and conc >= 8:
            triggers.append(
                f"Position sizing: review trimming if concentration rises above "
                f"{max(12, round(conc + 2))}% of portfolio")
        rsi = ind.get("rsi_14")
        if rsi is not None and rsi >= 70:
            triggers.append(f"RSI {rsi:.0f} — overbought; avoid adding until momentum cools")
        val = (fundamentals or {}).get("valuation", {})
        if val.get("pe_ttm"):
            triggers.append(
                f"Valuation check each quarter: TTM P/E {val['pe_ttm']:.0f}x vs "
                f"growth {val.get('growth_used_for_peg_percent') or 'n/a'}% — "
                f"re-test the PEG after every result")
        triggers.append("Next quarterly result: verify guidance from the latest concall was delivered")
        sh = (fundamentals or {}).get("shareholding", {})
        if sh.get("fii_change_full_window_pp") is not None and sh["fii_change_full_window_pp"] < 0:
            triggers.append("Watch next shareholding filing: does FII selling continue or reverse?")
        return triggers

    # --------------------------------------------------------------- composite
    @staticmethod
    def build(holding: Dict, indicators: Dict, fundamentals: Dict) -> Dict:
        growth = (fundamentals or {}).get("growth", {})
        quality = (fundamentals or {}).get("quality", {})
        valuation = (fundamentals or {}).get("valuation", {})

        pillars = {
            "growth": ScorecardService.growth_score(growth),
            "quality": ScorecardService.quality_score(quality),
            "technicals": ScorecardService.technical_score(indicators),
            "valuation": ScorecardService.valuation_score(valuation),
        }
        weights = {"growth": 0.30, "quality": 0.25, "technicals": 0.20, "valuation": 0.25}
        scored = {k: v for k, v in pillars.items() if v is not None}
        composite = None
        if scored:
            total_w = sum(weights[k] for k in scored)
            composite = round(sum(pillars[k] * weights[k] for k in scored) / total_w, 1)

        stance = None
        if composite is not None:
            val_score = pillars.get("valuation")
            if composite >= 7.5:
                stance = "Strong — fundamentals and setup aligned"
            elif composite >= 6.0:
                stance = "Solid hold — monitor the weak pillar"
            elif composite >= 4.5:
                stance = "Mixed — thesis needs the next quarter to confirm"
            else:
                stance = "Weak — re-examine why this is in the portfolio"
            if val_score is not None and val_score <= 3 and composite >= 6.0:
                stance += " (valuation is the main risk)"

        return {
            "pillar_scores": pillars,
            "weights": weights,
            "composite_score": composite,
            "stance": stance,
            "position_risk": ScorecardService.position_risk(holding, indicators),
            "watch_triggers": ScorecardService.watch_triggers(holding, indicators, fundamentals),
        }
