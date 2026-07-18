from fastapi import APIRouter
from app.models.portfolio import PortfolioResponse
from app.controllers.portfolio_controller import PortfolioController

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

portfolio_controller = PortfolioController()


@router.get("", response_model=PortfolioResponse)
def get_portfolio():
    return portfolio_controller.get_portfolio()
