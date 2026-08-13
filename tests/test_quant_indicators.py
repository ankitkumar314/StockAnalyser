import numpy as np
import pandas as pd
import pytest

from app.quant.indicators import ADX, ATR, MACD, RSI, BollingerBands, Renko


def _ohlcv(closes, highs=None, lows=None, opens=None):
    closes = pd.Series(closes, dtype=float)
    highs = pd.Series(highs, dtype=float) if highs is not None else closes + 1
    lows = pd.Series(lows, dtype=float) if lows is not None else closes - 1
    opens = pd.Series(opens, dtype=float) if opens is not None else closes
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {"Open": opens.values, "High": highs.values, "Low": lows.values, "Close": closes.values},
        index=dates,
    )


# ---------------------------------------------------------------------------
# RSI - cross-checked against an independent, loop-based Wilder RSI reference
# ---------------------------------------------------------------------------

def _reference_rsi(closes, period=14):
    """
    Independent (non-pandas) re-implementation of Wilder RSI, matching pandas'
    ewm(alpha=1/period, adjust=False, min_periods=period) semantics: the EWM
    recursion is seeded at the first valid gain/loss observation and updated on
    every subsequent bar, but outputs stay NaN until `period` valid observations
    have been folded in.
    """
    n = len(closes)
    gains = [np.nan] * n
    losses = [np.nan] * n
    for i in range(1, n):
        change = closes[i] - closes[i - 1]
        gains[i] = max(change, 0.0)
        losses[i] = max(-change, 0.0)

    alpha = 1 / period
    avg_gain = [np.nan] * n
    avg_loss = [np.nan] * n
    prev_gain = prev_loss = None
    valid_count = 0
    for i in range(n):
        if np.isnan(gains[i]):
            continue
        valid_count += 1
        if prev_gain is None:
            prev_gain, prev_loss = gains[i], losses[i]
        else:
            prev_gain = (1 - alpha) * prev_gain + alpha * gains[i]
            prev_loss = (1 - alpha) * prev_loss + alpha * losses[i]
        if valid_count >= period:
            avg_gain[i], avg_loss[i] = prev_gain, prev_loss

    rsi = [np.nan] * n
    for i in range(n):
        if np.isnan(avg_gain[i]):
            continue
        rsi[i] = 100.0 if avg_loss[i] == 0 else 100 - 100 / (1 + avg_gain[i] / avg_loss[i])
    return rsi


def test_rsi_matches_independent_reference_implementation():
    rng = np.random.default_rng(42)
    closes = 100 + np.cumsum(rng.normal(0, 1.5, size=60))
    df = _ohlcv(closes)

    result = RSI(period=14).compute(df)["RSI"].tolist()
    expected = _reference_rsi(list(closes), period=14)

    for actual, exp in zip(result, expected):
        if np.isnan(exp):
            assert np.isnan(actual)
        else:
            assert actual == pytest.approx(exp, abs=1e-9)


def test_rsi_pure_uptrend_saturates_at_100():
    closes = list(range(1, 31))  # strictly increasing, no losses at all
    df = _ohlcv(closes)
    rsi = RSI(period=14).compute(df)["RSI"]
    assert rsi.iloc[15:].eq(100.0).all()


def test_rsi_stays_within_bounds():
    rng = np.random.default_rng(7)
    closes = 50 + np.cumsum(rng.normal(0, 2, size=100))
    df = _ohlcv(closes)
    rsi = RSI(period=14).compute(df)["RSI"].dropna()
    assert (rsi >= 0).all() and (rsi <= 100).all()


# ---------------------------------------------------------------------------
# Bollinger Bands - hand-computable small example
# ---------------------------------------------------------------------------

def test_bollinger_bands_manual_calculation():
    closes = [10, 12, 11, 13, 15]  # period=5, one window -> deterministic by hand
    df = _ohlcv(closes)
    bb = BollingerBands(period=5, num_std=2).compute(df)

    mean = sum(closes) / 5
    variance = sum((c - mean) ** 2 for c in closes) / 5  # ddof=0
    std = variance**0.5

    assert bb["MiddleBand"].iloc[-1] == pytest.approx(mean)
    assert bb["UpperBand"].iloc[-1] == pytest.approx(mean + 2 * std)
    assert bb["LowerBand"].iloc[-1] == pytest.approx(mean - 2 * std)


def test_bollinger_upper_always_above_lower():
    rng = np.random.default_rng(3)
    closes = 100 + np.cumsum(rng.normal(0, 1, size=50))
    df = _ohlcv(closes)
    bb = BollingerBands(period=20).compute(df).dropna()
    assert (bb["UpperBand"] >= bb["LowerBand"]).all()


# ---------------------------------------------------------------------------
# MACD - internal consistency (histogram = macd - signal) and EMA crossover sign
# ---------------------------------------------------------------------------

def test_macd_histogram_equals_macd_minus_signal():
    rng = np.random.default_rng(1)
    closes = 200 + np.cumsum(rng.normal(0, 3, size=80))
    df = _ohlcv(closes)
    macd_df = MACD().compute(df).dropna()
    assert np.allclose(macd_df["Histogram"], macd_df["MACD"] - macd_df["Signal"])


def test_macd_rejects_fast_not_less_than_slow():
    with pytest.raises(ValueError):
        MACD(fast_period=26, slow_period=12)


# ---------------------------------------------------------------------------
# ATR - non-negative, and a hand-computed first couple of true range values
# ---------------------------------------------------------------------------

def test_atr_true_range_matches_manual_first_bars():
    highs = [105, 106, 104]
    lows = [95, 101, 99]
    closes = [100, 105, 100]
    df = _ohlcv(closes, highs=highs, lows=lows)
    atr = ATR(period=2).compute(df)

    # bar 0 has no previous close so True Range (and hence ATR) is NaN there
    assert pd.isna(atr["ATR"].iloc[0])
    # bar 1: TR = max(106-101, |106-100|, |101-100|) = max(5,6,1) = 6
    # bar 2: TR = max(104-99, |104-105|, |99-105|) = max(5,1,6) = 6
    # both true-range values equal 6, so any weighted average of them is 6 too,
    # independent of the exact Wilder smoothing weights used
    assert atr["ATR"].iloc[2] == pytest.approx(6.0)


def test_atr_is_never_negative():
    rng = np.random.default_rng(5)
    closes = 50 + np.cumsum(rng.normal(0, 1, size=60))
    df = _ohlcv(closes)
    atr = ATR(period=14).compute(df)["ATR"].dropna()
    assert (atr >= 0).all()


# ---------------------------------------------------------------------------
# ADX - bounded 0-100 (where defined)
# ---------------------------------------------------------------------------

def test_adx_and_di_stay_within_bounds():
    rng = np.random.default_rng(11)
    closes = 100 + np.cumsum(rng.normal(0, 2, size=120))
    highs = closes + np.abs(rng.normal(0, 1, size=120))
    lows = closes - np.abs(rng.normal(0, 1, size=120))
    df = _ohlcv(closes, highs=highs, lows=lows)

    adx_df = ADX(period=14).compute(df).dropna()
    for col in ("ADX", "+DI", "-DI"):
        assert (adx_df[col] >= 0).all()
        assert (adx_df[col] <= 100).all()


def test_adx_trending_market_scores_higher_than_choppy_market():
    trending_closes = np.arange(1, 121, dtype=float)  # steady uptrend
    trending_df = _ohlcv(trending_closes)

    rng = np.random.default_rng(9)
    choppy_closes = 100 + np.cumsum(rng.normal(0, 1, size=120))
    choppy_df = _ohlcv(choppy_closes)

    trending_adx = ADX(period=14).compute(trending_df)["ADX"].iloc[-1]
    choppy_adx = ADX(period=14).compute(choppy_df)["ADX"].iloc[-1]

    assert trending_adx > choppy_adx


# ---------------------------------------------------------------------------
# Renko - brick geometry must be internally consistent
# ---------------------------------------------------------------------------

def test_renko_bricks_use_fixed_brick_size_and_correct_direction():
    closes = [100, 100, 103, 103, 106, 106, 103, 103, 100]
    df = _ohlcv(closes)
    renko_df = Renko(brick_size=2.0).compute(df)

    assert not renko_df.empty
    diffs = (renko_df["close"] - renko_df["open"]).abs()
    assert np.allclose(diffs, 2.0)
    assert (renko_df.loc[renko_df["direction"] == 1, "close"] > renko_df.loc[renko_df["direction"] == 1, "open"]).all()
    assert (renko_df.loc[renko_df["direction"] == -1, "close"] < renko_df.loc[renko_df["direction"] == -1, "open"]).all()


def test_renko_rejects_non_positive_brick_size():
    df = _ohlcv([100, 101, 102])
    with pytest.raises(ValueError):
        Renko(brick_size=0).compute(df)


# ---------------------------------------------------------------------------
# Shared base-class behaviour
# ---------------------------------------------------------------------------

def test_indicator_raises_on_insufficient_history():
    df = _ohlcv([100, 101, 102])
    with pytest.raises(ValueError):
        RSI(period=14).compute(df)


def test_indicator_raises_on_missing_columns():
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError):
        ATR(period=2).compute(df)
