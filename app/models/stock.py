from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Stock(BaseModel):
    stock_name: str
    ticker: str
    screener_link: Optional[str] = None
    market_size: Optional[str] = None
    last_stock_price: Optional[int] = None

class StockCreateRequest(BaseModel):
    stock_name: str
    ticker: str
    screener_link: Optional[str] = None
    market_size: Optional[str] = None
    last_stock_price: Optional[int] = None


class StockUpdateRequest(BaseModel):
    stock_name: Optional[str] = None
    ticker: Optional[str] = None
    screener_link: Optional[str] = None
    market_size: Optional[str] = None
    last_stock_price: Optional[int] = None


class StockResponse(BaseModel):
    id: int
    stock_name: str
    ticker: str
    screener_link: Optional[str] = None
    market_size: Optional[str] = None
    last_stock_price: Optional[int] = None
    created_at: datetime
    update_at: datetime
    
    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    total: int
    stocks: list[StockResponse]
