import json
import os

import pytest

from app.services.fundamental_analysis_service import FundamentalAnalysisService

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "kalyan_scrape.json")


@pytest.fixture(scope="module")
def scrape_data():
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        return json.load(f)["data"]


class TestGrowthProfile:
    def test_ttm_sums(self, scrape_data):
        g = FundamentalAnalysisService.growth_profile(scrape_data)
        assert g["sales_ttm"] == pytest.approx(6142 + 6843 + 9048 + 8994)
        assert g["net_profit_ttm"] == pytest.approx(256 + 262 + 401 + 366)
        assert g["eps_ttm"] == pytest.approx(2.49 + 2.54 + 3.88 + 3.54)

    def test_ttm_growth(self, scrape_data):
        g = FundamentalAnalysisService.growth_profile(scrape_data)
        prev = 4687 + 5227 + 6386 + 5350
        expected = ((6142 + 6843 + 9048 + 8994) / prev - 1) * 100
        assert g["sales_ttm_growth_percent"] == pytest.approx(expected, rel=1e-3)

    def test_cagr(self, scrape_data):
        g = FundamentalAnalysisService.growth_profile(scrape_data)
        # annual sales: ... 11584 (3y ago) -> 31027 (latest)
        assert g["sales_cagr_3y"] == pytest.approx(((31027 / 11584) ** (1 / 3) - 1) * 100, rel=1e-3)
        assert g["profit_cagr_3y"] == pytest.approx(((1285 / 390) ** (1 / 3) - 1) * 100, rel=1e-3)

    def test_latest_quarter_yoy(self, scrape_data):
        g = FundamentalAnalysisService.growth_profile(scrape_data)
        assert g["latest_quarter_np_yoy_percent"] == pytest.approx((366 / 185 - 1) * 100, rel=1e-3)


class TestQualityProfile:
    def test_cfo_to_pat(self, scrape_data):
        q = FundamentalAnalysisService.quality_profile(scrape_data)
        assert q["cfo_to_pat_percent"] == pytest.approx(1587 / 1285 * 100, abs=1)

    def test_roce(self, scrape_data):
        q = FundamentalAnalysisService.quality_profile(scrape_data)
        assert q["roce_latest_percent"] == 24.0

    def test_debt_to_equity(self, scrape_data):
        q = FundamentalAnalysisService.quality_profile(scrape_data)
        assert q["debt_to_equity"] == pytest.approx(3232 / (1033 + 5088), abs=0.01)


class TestShareholding:
    def test_fii_exit_detected(self, scrape_data):
        sh = FundamentalAnalysisService.shareholding_profile(scrape_data)
        assert sh["fii_latest_percent"] == pytest.approx(10.82)
        assert sh["fii_change_full_window_pp"] == pytest.approx(10.82 - 26.56, abs=0.01)


class TestValuation:
    def test_pe_and_peg(self, scrape_data):
        v = FundamentalAnalysisService.valuation_profile(scrape_data, current_price=574.4)
        eps_ttm = 2.49 + 2.54 + 3.88 + 3.54
        assert v["pe_ttm"] == pytest.approx(574.4 / eps_ttm, rel=1e-2)
        assert v["peg"] is not None and v["peg"] > 0

    def test_no_price_degrades(self, scrape_data):
        v = FundamentalAnalysisService.valuation_profile(scrape_data, current_price=None)
        assert v["pe_ttm"] is None
        assert v["eps_ttm"] is not None


class TestFlags:
    def test_flags_generated(self, scrape_data):
        flags = FundamentalAnalysisService.flags(scrape_data)
        assert any("FII" in f for f in flags["red_flags"])
        assert any("ROCE" in p for p in flags["positives"])
        assert any("net profit growth" in p for p in flags["positives"])

    def test_empty_data_no_crash(self):
        result = FundamentalAnalysisService.analyze({}, current_price=100.0)
        assert result["growth"]["sales_ttm"] is None
        assert result["red_flags"] == []
