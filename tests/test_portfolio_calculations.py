from app.services.kite_service import calculate_holding_metrics, calculate_portfolio_totals


def _holding(symbol, quantity, average_price, current_price, company_name=None, exchange="NSE"):
    return {
        "symbol": symbol,
        "company_name": company_name or symbol,
        "exchange": exchange,
        "quantity": quantity,
        "average_price": average_price,
        "current_price": current_price,
    }


def test_calculate_holding_metrics_basic_values():
    holdings = [_holding("RELIANCE", 15, 2475.50, 2860.30, "Reliance Industries Ltd")]

    result = calculate_holding_metrics(holdings)

    assert len(result) == 1
    holding = result[0]
    assert holding["invested_value"] == 37132.5
    assert holding["current_value"] == 42904.5
    assert holding["profit_loss"] == 5772.0
    assert round(holding["profit_loss_percent"], 2) == 15.54
    assert holding["portfolio_concentration"] == 100.0


def test_calculate_holding_metrics_concentration_matches_spec_example():
    holdings = [
        _holding("RELIANCE", 1, 100000, 120000),
        _holding("TCS", 1, 100000, 80000),
    ]

    result = calculate_holding_metrics(holdings)

    by_symbol = {h["symbol"]: h for h in result}
    assert by_symbol["RELIANCE"]["portfolio_concentration"] == 60.0
    assert by_symbol["TCS"]["portfolio_concentration"] == 40.0


def test_calculate_holding_metrics_sorted_by_current_value_desc():
    holdings = [
        _holding("SMALL", 1, 100, 150),
        _holding("BIG", 1, 100, 5000),
        _holding("MID", 1, 100, 1000),
    ]

    result = calculate_holding_metrics(holdings)

    assert [h["symbol"] for h in result] == ["BIG", "MID", "SMALL"]


def test_calculate_holding_metrics_handles_zero_invested_value():
    holdings = [_holding("FREEBIE", 10, 0, 50)]

    result = calculate_holding_metrics(holdings)

    assert result[0]["profit_loss_percent"] == 0.0


def test_calculate_portfolio_totals_aggregates_correctly():
    holdings = calculate_holding_metrics([
        _holding("RELIANCE", 15, 2475.50, 2860.30),
        _holding("TCS", 10, 3000, 3200),
    ])

    totals = calculate_portfolio_totals(holdings)

    assert totals["portfolio_value"] == round(42904.5 + 32000, 2)
    assert totals["total_investment"] == round(37132.5 + 30000, 2)
    assert totals["total_pnl"] == round(totals["portfolio_value"] - totals["total_investment"], 2)


def test_calculate_portfolio_totals_empty_holdings():
    totals = calculate_portfolio_totals([])

    assert totals == {
        "portfolio_value": 0,
        "total_investment": 0,
        "total_pnl": 0,
        "total_pnl_percent": 0.0,
    }
