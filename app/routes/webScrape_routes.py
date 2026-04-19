from fastapi import APIRouter
from typing import Dict
from app.models.web_scrape import WebScrapeData, WebScrapeRequest
from app.controllers.webScrape_controller import WebScrapeController
from app.services.webScrape_service import WebScrapeService
from app.repositories.webScrape_repository import WebScrapeRepository
from app.services.Scraper_service import ScraperService


router = APIRouter(prefix="/scrape", tags=["web-scraping"])

scrape_repository = WebScrapeRepository()
scrape_service = WebScrapeService(scrape_repository)
scrape_controller = WebScrapeController(scrape_service)

@router.post("/get-financial-data")
def scrape_data(request: WebScrapeRequest):
    try:
        return scrape_controller.scrape_for_financial_data(request.ticker)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def scrape_url(request: WebScrapeRequest) -> WebScrapeData:
    return scrape_controller.scrape_url(request)


@router.get("")
def get_all_scrapes() -> Dict[str, WebScrapeData]:
    return scrape_controller.get_all_scrapes()


@router.get("/{url:path}")
def get_scrape_by_url(url: str) -> WebScrapeData:
    return scrape_controller.get_scrape_by_url(url)


@router.delete("/{url:path}")
def delete_scrape(url: str) -> Dict[str, str]:
    return scrape_controller.delete_scrape(url)

