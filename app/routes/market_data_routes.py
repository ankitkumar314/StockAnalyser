from fastapi import APIRouter
from app.models.market_data import QuoteResponse, HistoryResponse
from app.controllers.market_data_controller import MarketDataController

router = APIRouter(prefix="/market-data", tags=["market-data"])

market_data_controller = MarketDataController()

##stale route 
@router.get("/quote/{ticker}", response_model=QuoteResponse)
def get_quote(ticker: str):
    return market_data_controller.get_quote(ticker)

## give history of data foreach ticker here 
@router.get("/history/{ticker}", response_model=HistoryResponse)
def get_history(ticker: str, period: str = "3y", interval: str = "1d"):
    return market_data_controller.get_history(ticker, period, interval)
