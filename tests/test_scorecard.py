import json
import os

import pytest

from app.services.fundamental_analysis_service import FundamentalAnalysisService
from app.services.scorecard_service import ScorecardService
from tests.test_technical_indicators import make_bars
from app.services.technicalIndicator_service import TechnicalIndicatorService

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


@pytest.fixture(scope="module")
def fundamentals():
    with open(os.path.join(SAMPLE_DIR, "kalyan_scrape.json"), encoding="utf-8") as f:
        data = json.load(f)["data"]
    return FundamentalAnalysisService.analyze(data, current_price=574.4)


@pytest.fixture(scope="module")
def holding():
    with open(os.path.join(SAMPLE_DIR, "nuvama_holding.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def indicators():
    return TechnicalIndicatorService.compute_indicators(make_bars())


class TestScorecard:
    def test_pillars_in_range(self, holding, indicators, fundamentals):
        sc = ScorecardService.build(holding, indicators, fundamentals)
        for name, score in sc["pillar_scores"].items():
            assert score is None or 0 <= score <= 10, name
        assert 0 <= sc["composite_score"] <= 10
        assert sc["stance"]

    def test_strong_growth_scores_high(self, fundamentals):
        # Kalyan sample: TTM profit growth ~60%+, sales CAGR ~39% -> high growth score
        score = ScorecardService.growth_score(fundamentals["growth"])
        assert score >= 8

    def test_gain_cushion_math(self, holding, indicators):
        risk = ScorecardService.position_risk(holding, indicators)
        # 46.79% gain is erased by a fall of 46.79/146.79 = ~31.9%
        assert risk["gain_erased_by_fall_percent"] == pytest.approx(31.9, abs=0.1)

    def test_concentration_note(self, holding, indicators):
        risk = ScorecardService.position_risk(holding, indicators)
        assert any("concentration" in n.lower() for n in risk["notes"])

    def test_triggers_reference_dma(self, holding, indicators, fundamentals):
        triggers = ScorecardService.watch_triggers(holding, indicators, fundamentals)
        assert any("200-DMA" in t for t in triggers)

    def test_missing_everything_degrades(self):
        sc = ScorecardService.build({"symbol": "X"}, {}, {})
        assert sc["pillar_scores"]["growth"] is None
        assert sc["composite_score"] is None or 0 <= sc["composite_score"] <= 10
