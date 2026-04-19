from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime


class WebScrapeRequest(BaseModel):
    url: str
    ticker: str


class WebScrapeData(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None
    links: List[str] = []
    images: List[str] = []
    meta_tags: Dict[str, str] = {}
    headers: Dict[str, str] = {}
    status_code: int
    scraped_at: str
    concall_data: Dict[str, List[Dict[str, str]]] = {}
    
