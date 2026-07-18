from fastapi import HTTPException
from app.models.portfolio import PortfolioResponse, PortfolioHolding
from app.services.kite_service import (
    KiteService,
    KiteTokenExpiredError,
    KiteNetworkError,
    KiteAPIError,
)
import logging

logger = logging.getLogger(__name__)


class PortfolioController:
    def __init__(self):
        self.kite_service = KiteService()

    def get_portfolio(self) -> PortfolioResponse:
        try:
            data = self.kite_service.get_portfolio()
            return PortfolioResponse(
                portfolio_value=data["portfolio_value"],
                total_investment=data["total_investment"],
                total_pnl=data["total_pnl"],
                total_pnl_percent=data["total_pnl_percent"],
                holdings=[PortfolioHolding(**holding) for holding in data["holdings"]]
            )

        except KiteTokenExpiredError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except KiteNetworkError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except KiteAPIError as e:
            raise HTTPException(status_code=502, detail=f"Zerodha API failure: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error building portfolio: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch portfolio")
