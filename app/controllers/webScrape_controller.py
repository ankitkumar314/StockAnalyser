from typing import Dict
from fastapi import HTTPException
from app.models.web_scrape import WebScrapeData, WebScrapeRequest
from app.services.webScrape_service import WebScrapeService


class WebScrapeController:
    def __init__(self, service: WebScrapeService):
        self.service = service
    
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
    
    def get_scrape_by_url(self, url: str) -> WebScrapeData:
        try:
            if url is None or url.strip() == "":
                raise HTTPException(status_code=400, detail="URL cannot be empty")
            
            if self.service.repository is None:
                raise HTTPException(status_code=501, detail="Repository not configured")
            
            scrape_data = self.service.repository.get_by_url(url)
            if scrape_data is None:
                raise HTTPException(status_code=404, detail="Scrape data not found for this URL")
            
            return scrape_data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_scrape(self, url: str) -> Dict[str, str]:
        try:
            if url is None or url.strip() == "":
                raise HTTPException(status_code=400, detail="URL cannot be empty")
            
            if self.service.repository is None:
                raise HTTPException(status_code=501, detail="Repository not configured")
            
            deleted = self.service.repository.delete(url)
            if not deleted:
                raise HTTPException(status_code=404, detail="Scrape data not found for this URL")
            
            return {"message": "Deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
