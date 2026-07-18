import os
import logging
from typing import Dict, List, Optional

from kiteconnect import KiteConnect
from kiteconnect.exceptions import TokenException, NetworkException, KiteException

from app.database.connection import DatabaseConnection
from app.database.stock_repository import StockRepository
from app.services.kite_token_store import KiteTokenStore

logger = logging.getLogger(__name__)

TOKEN_EXPIRED_MESSAGE = "Kite access token expired. Reconnect your Zerodha account."


class KiteTokenExpiredError(Exception):
    """Raised when the stored Kite access token is missing, invalid, or expired."""


class KiteNetworkError(Exception):
    """Raised when Kite Connect cannot be reached (network failure)."""


class KiteAPIError(Exception):
    """Raised for any other Kite Connect API failure."""


def calculate_holding_metrics(holdings: List[Dict]) -> List[Dict]:
    """
    Pure calculation step over already-fetched holdings (symbol, company_name, exchange,
    quantity, average_price, current_price). Kept free of any Kite/DB I/O so it can be
    unit tested directly. Returns holdings sorted by current_value descending, each
    enriched with invested_value, current_value, profit_loss, profit_loss_percent and
    portfolio_concentration.
    """
    enriched = []
    for holding in holdings:
        quantity = holding["quantity"]
        average_price = holding["average_price"]
        current_price = holding["current_price"]

        invested_value = average_price * quantity
        current_value = current_price * quantity
        profit_loss = current_value - invested_value
        profit_loss_percent = (profit_loss / invested_value * 100) if invested_value else 0.0

        enriched.append({
            **holding,
            "invested_value": round(invested_value, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percent": round(profit_loss_percent, 2),
        })

    total_current_value = sum(item["current_value"] for item in enriched)
    for item in enriched:
        concentration = (item["current_value"] / total_current_value * 100) if total_current_value else 0.0
        item["portfolio_concentration"] = round(concentration, 2)

    enriched.sort(key=lambda item: item["current_value"], reverse=True)
    return enriched


def calculate_portfolio_totals(holdings: List[Dict]) -> Dict:
    """Pure calculation of portfolio-level totals from already-computed holdings."""
    total_investment = sum(holding["invested_value"] for holding in holdings)
    portfolio_value = sum(holding["current_value"] for holding in holdings)
    total_pnl = portfolio_value - total_investment
    total_pnl_percent = (total_pnl / total_investment * 100) if total_investment else 0.0

    return {
        "portfolio_value": round(portfolio_value, 2),
        "total_investment": round(total_investment, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percent": round(total_pnl_percent, 2),
    }


class KiteService:
    """
    Read-only Zerodha Kite Connect integration. Uses a pre-existing access_token
    (no OAuth login flow here) to fetch delivery holdings and compute portfolio metrics.
    """


# logging.basicConfig(level=logging.DEBUG)

# kite = KiteConnect(api_key="your_api_key")

# # Redirect the user to the login url obtained
# # from kite.login_url(), and receive the request_token
# # from the registered redirect url after the login flow.
# # Once you have the request_token, obtain the access_token
# # as follows.

# data = kite.generate_session("request_token_here", api_secret="your_secret")
# kite.set_access_token(data["access_token"])

    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")

    def _get_client(self) -> KiteConnect:
        # Token resolved per-call via KiteTokenStore so a login through
        # /redirect/zerodha takes effect immediately, without a server restart.
        access_token = KiteTokenStore.get_token()
        if not self.api_key or not access_token:
            raise KiteTokenExpiredError(TOKEN_EXPIRED_MESSAGE)

        kite = KiteConnect(api_key=self.api_key)
        #  data = kite.generate_session("request_token_here", api_secret="your_secret")
        # kite.set_access_token(data["access_token"])
        kite.set_access_token(access_token)
        return kite

    @staticmethod
    def _resolve_company_name(session, tradingsymbol: str) -> str:
        if session is None:
            return tradingsymbol
        stock = StockRepository.get_by_ticker(session, tradingsymbol)
        return stock.stock_name if stock else tradingsymbol

    def get_portfolio(self) -> Dict:
        """Fetch holdings from Kite Connect and return a fully computed portfolio DTO."""
        logger.info("Kite portfolio request started")

        kite = self._get_client()

        try:
            raw_holdings = kite.holdings()
        except TokenException as e:
            logger.warning("Kite access token invalid/expired")
            raise KiteTokenExpiredError(TOKEN_EXPIRED_MESSAGE) from e
        except NetworkException as e:
            logger.error(f"Kite network failure: {str(e)}")
            raise KiteNetworkError("Unable to reach Zerodha Kite API") from e
        except KiteException as e:
            logger.error(f"Kite API failure: {str(e)}")
            raise KiteAPIError(str(e)) from e

        logger.info(f"Kite API success, {len(raw_holdings)} holdings returned")

        db_enabled = DatabaseConnection.is_enabled()
        session = DatabaseConnection.get_session() if db_enabled else None
        try:
            holdings = [
                {
                    "symbol": h["tradingsymbol"],
                    "company_name": self._resolve_company_name(session, h["tradingsymbol"]),
                    "exchange": h["exchange"],
                    "quantity": h["quantity"],
                    "average_price": h["average_price"],
                    "current_price": h["last_price"],
                }
                for h in raw_holdings
                if h.get("quantity", 0) > 0
            ]
        finally:
            if session is not None:
                session.close()

        holdings = calculate_holding_metrics(holdings)
        totals = calculate_portfolio_totals(holdings)

        return {**totals, "holdings": holdings}
