from fastapi import APIRouter
from typing import Dict
from app.models.web_scrape import WebScrapeData, WebScrapeRequest
from app.models.stock_scrape import StockScrapeDataResponse
from app.controllers.webScrape_controller import WebScrapeController


router = APIRouter(prefix="/scrape", tags=["web-scraping"])

scrape_controller = WebScrapeController()

@router.post("/get-financial-data")
def scrape_data(request: WebScrapeRequest):
    try:
        return scrape_controller.scrape_for_financial_data(request.ticker)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def get_all_scrapes() -> Dict[str, WebScrapeData]:
    return scrape_controller.get_all_scrapes()


@router.get("/{ticker}")
def get_scrape_by_ticker(ticker: str) -> StockScrapeDataResponse:
    return scrape_controller.get_scrape_by_ticker(ticker)
