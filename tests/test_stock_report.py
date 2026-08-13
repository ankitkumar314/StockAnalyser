import json
import os

import pytest

from app.services.stock_report_service import StockReportService
from tests.test_technical_indicators import make_bars

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


def _load(name):
    with open(os.path.join(SAMPLE_DIR, name), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def full_report():
    holding = _load("kalyan_holding.json")
    scrape = _load("kalyan_scrape.json")["data"]
    answers = _load("kalyan_concall_summary.json")
    return StockReportService.build_report_data(
        holding, bars=make_bars(), scrape_data=scrape, concall_answers=answers)


class TestBuildReportData:
    def test_all_sections_present(self, full_report):
        assert full_report["technicals"] is not None
        assert full_report["fundamentals"] is not None
        assert full_report["concall"] is not None
        assert full_report["scorecard"]["composite_score"] is not None
        assert full_report["data_coverage"] == {
            "price_history": True, "screener_fundamentals": True, "concall_summary": True}

    def test_concall_key_insights_extracted(self, full_report):
        sections = full_report["concall"]["sections"]
        assert len(sections) == 3
        assert all(s["key_insights"] for s in sections)
        assert any("66%" in line for line in sections[0]["key_insights"])

    def test_partial_data_degrades(self):
        holding = _load("nuvama_holding.json")
        report = StockReportService.build_report_data(holding)
        assert report["technicals"] is None
        assert report["fundamentals"] is None
        assert report["concall"] is None
        # position risk still works from the holding alone
        assert report["scorecard"]["position_risk"]["gain_erased_by_fall_percent"] is not None


class TestRenderMarkdown:
    def test_sections_rendered(self, full_report):
        md = StockReportService.render_markdown(full_report)
        for heading in ("# Kalyan Jewellers India Ltd (KALYANKJIL)", "## Position",
                        "## Scorecard", "## Technical Setup", "## Fundamentals",
                        "### Valuation", "## Latest Concall Insights", "## Watch Triggers"):
            assert heading in md, heading
        assert "not investment advice" in md

    def test_llm_narrative_included_when_given(self, full_report):
        md = StockReportService.render_markdown(full_report, llm_narrative="Test narrative here.")
        assert "## Analyst View (AI)" in md
        assert "Test narrative here." in md

    def test_minimal_report_renders(self):
        holding = _load("nuvama_holding.json")
        report = StockReportService.build_report_data(holding)
        md = StockReportService.render_markdown(report)
        assert "# Nuvama Wealth Management Ltd (NUVAMA)" in md
        assert "## Position" in md


class TestPortfolioRollup:
    def test_rollup_renders(self, full_report):
        totals = {"portfolio_value": 1276578.0, "total_investment": 1000000.0,
                  "total_pnl": 276578.0, "total_pnl_percent": 27.66}
        md = StockReportService.render_portfolio_markdown(totals, [full_report], ["XYZ"])
        assert "# Portfolio Intelligence Report" in md
        assert "KALYANKJIL" in md
        assert "## Concentration" in md
        assert "XYZ" in md
