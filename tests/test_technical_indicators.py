import math

import pytest

from app.services.technicalIndicator_service import TechnicalIndicatorService


def make_bars(n=260, start=100.0, drift=0.4, wobble=3.0):
    """Synthetic rising daily series with mild oscillation."""
    bars = []
    price = start
    for i in range(n):
        price = start + drift * i + wobble * math.sin(i / 7)
        bars.append({
            "date": f"day-{i}",
            "open": price * 0.995,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 100000 + (i % 10) * 1000,
        })
    return bars


class TestComputeIndicators:
    def setup_method(self):
        self.bars = make_bars()
        self.ind = TechnicalIndicatorService.compute_indicators(self.bars)

    def test_v2_compatible_keys_present(self):
        for key in ("macd", "macd_signal", "macd_trend", "dma_50", "dma_200",
                    "dma_crossover", "is_dummy"):
            assert key in self.ind
        assert self.ind["is_dummy"] is False

    def test_uptrend_reads_bullish(self):
        assert self.ind["dma_50"] > self.ind["dma_200"]
        assert self.ind["dma_crossover"] == "golden_cross"
        assert self.ind["price_vs_dma200_percent"] > 0

    def test_sma_math(self):
        closes = [b["close"] for b in self.bars]
        assert self.ind["dma_50"] == pytest.approx(sum(closes[-50:]) / 50, rel=1e-3)
        assert self.ind["dma_200"] == pytest.approx(sum(closes[-200:]) / 200, rel=1e-3)

    def test_rsi_in_range(self):
        assert 0 <= self.ind["rsi_14"] <= 100

    def test_52w_range(self):
        assert self.ind["low_52w"] <= self.ind["last_close"] * 1.01
        assert self.ind["high_52w"] >= self.ind["last_close"] * 0.99
        assert self.ind["percent_from_52w_high"] <= 0.5

    def test_max_drawdown_non_positive(self):
        assert self.ind["max_drawdown_percent"] <= 0

    def test_atr_positive(self):
        assert self.ind["atr_14"] > 0
        assert self.ind["atr_percent"] > 0

    def test_downtrend_reads_bearish(self):
        bars = make_bars(drift=-0.4, start=250.0)
        ind = TechnicalIndicatorService.compute_indicators(bars)
        assert ind["dma_crossover"] == "death_cross"
        assert ind["price_vs_dma200_percent"] < 0

    def test_short_series_degrades_gracefully(self):
        ind = TechnicalIndicatorService.compute_indicators(make_bars(n=40))
        assert ind["dma_200"] is None
        assert ind["dma_crossover"] is None
        assert ind["macd"] is not None  # 40 bars is enough for MACD

    def test_too_few_bars_raises(self):
        with pytest.raises(ValueError):
            TechnicalIndicatorService.compute_indicators(make_bars(n=1))
