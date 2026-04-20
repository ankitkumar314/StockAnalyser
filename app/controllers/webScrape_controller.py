from typing import Dict
from fastapi import HTTPException
from app.models.web_scrape import WebScrapeData, WebScrapeRequest
from app.models.stock_scrape import StockScrapeDataResponse
from app.services.Scraper_service import ScraperService
from app.services.webScrape_service import WebScrapeService
from app.services.stock_scrape_data_service import StockScrapeDataService
from app.controllers.stock_controller import StockController
import logging

logger = logging.getLogger(__name__)


class WebScrapeController:
    def __init__(self, service: WebScrapeService):
        self.service = service
        self.stock_controller = StockController()

    
    def scrape_url(self, request: WebScrapeRequest) -> WebScrapeData:
        try:
            if request is None:
                raise HTTPException(status_code=400, detail="Request cannot be None")
            if request.url is None or request.url.strip() == "":
                raise HTTPException(status_code=400, detail="URL cannot be empty")
            
            return self.service.scrape_url(request)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_scrapes(self) -> Dict[str, WebScrapeData]:
        try:
            if self.service.repository is None:
                raise HTTPException(status_code=501, detail="Repository not configured")
            return self.service.repository.get_all()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_scrape_by_ticker(self, ticker: str) -> StockScrapeDataResponse:
        try:
            if ticker is None or ticker.strip() == "":
                raise HTTPException(status_code=400, detail="Ticker cannot be empty")
            
            scrape_data = StockScrapeDataService.get_latest_scrape_data(ticker)
            if scrape_data is None:
                raise HTTPException(status_code=404, detail=f"Scrape data not found for ticker: {ticker}")
            
            return StockScrapeDataResponse(
                quarter_result=scrape_data.quarter_result,
                growth_sales=scrape_data.growth_sales,
                growth_net_profit=scrape_data.growth_net_profit,
                growth_operating_profit=scrape_data.growth_operating_profit,
                shareholding_pattern=scrape_data.shareholding_pattern,
                profit_loss=scrape_data.profit_loss,
                quarter_date=scrape_data.quarter_date,
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting scrape data by ticker: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def scrape_for_financial_data(self, ticker: str) -> WebScrapeData:
        try:
            stock = self.stock_controller.get_stock_by_ticker(ticker)
            if not stock:
                raise HTTPException(status_code=404, detail=f"Stock with ticker {ticker} not found")
            
            tickerUrl = stock.screener_link
            if not tickerUrl:
                raise HTTPException(status_code=400, detail=f"No screener link found for ticker {ticker}")
            
            service = ScraperService(tickerUrl)
            result = service.scrape()
            
            if not result or not result.get('success'):
                raise HTTPException(status_code=500, detail="Failed to scrape financial data")
            
            try:
                saved_data = StockScrapeDataService.save_scrape_result(
                    stock_id=stock.id,
                    scrape_result=result
                )
                
                if saved_data:
                    logger.info(f"Successfully persisted scrape data for ticker: {ticker}, stock_id: {stock.id}")
                else:
                    logger.warning(f"Failed to persist scrape data for ticker: {ticker}")
                    
            except Exception as persist_error:
                logger.error(f"Error persisting scrape data: {str(persist_error)}")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in scrape_for_financial_data: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
