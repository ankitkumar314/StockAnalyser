from typing import Dict, Optional, List
from app.models.web_scrape import WebScrapeData


class WebScrapeRepository:
    def __init__(self):
        self._scrapes: Dict[str, WebScrapeData] = {}
    
    def save(self, scrape_data: WebScrapeData) -> WebScrapeData:
        try:
            if scrape_data is None:
                raise ValueError("Scrape data cannot be None")
            if scrape_data.url is None:
                raise ValueError("URL cannot be None")
            
            self._scrapes[scrape_data.url] = scrape_data
            return scrape_data
        except Exception as e:
            raise e
    
    def get_all(self) -> Dict[str, WebScrapeData]:
        try:
            return self._scrapes
        except Exception as e:
            raise e
    
    def get_by_url(self, url: str) -> Optional[WebScrapeData]:
        try:
            if url is None:
                return None
            return self._scrapes.get(url)
        except Exception as e:
            raise e
    
    def delete(self, url: str) -> bool:
        try:
            if url is None or url not in self._scrapes:
                return False
            del self._scrapes[url]
            return True
        except Exception as e:
            raise e
