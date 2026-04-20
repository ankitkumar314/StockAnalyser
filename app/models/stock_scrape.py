from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, date


class StockScrapeDataResponse(BaseModel):
    """Response model for stock scrape data."""
    quarter_result: Optional[Dict] = None
    growth_sales: Optional[Dict] = None
    growth_net_profit: Optional[Dict] = None
    growth_operating_profit: Optional[Dict] = None
    shareholding_pattern: Optional[Dict] = None
    profit_loss: Optional[Dict] = None
    quarter_date: Optional[date] = None
    class Config:
        from_attributes = True
