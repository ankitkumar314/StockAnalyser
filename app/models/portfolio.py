from pydantic import BaseModel
from typing import List


class PortfolioHolding(BaseModel):
    symbol: str
    company_name: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    invested_value: float
    current_value: float
    profit_loss: float
    profit_loss_percent: float
    portfolio_concentration: float


class PortfolioResponse(BaseModel):
    portfolio_value: float
    total_investment: float
    total_pnl: float
    total_pnl_percent: float
    holdings: List[PortfolioHolding]
