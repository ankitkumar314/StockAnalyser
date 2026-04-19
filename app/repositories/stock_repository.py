from typing import Dict, Optional
from app.models.stock import Stock


class StockRepository:
    def __init__(self):
        self._stocks: Dict[int, Stock] = {}
    
    def create(self, stock_id: int, stock: Stock) -> Stock:
        try:
            if stock_id is None:
                raise ValueError("Stock ID cannot be None")
            if stock_id in self._stocks:
                raise ValueError("Stock already exists")
            self._stocks[stock_id] = stock
            return stock
        except Exception as e:
            raise e
    
    def get_all(self) -> Dict[int, Stock]:
        try:
            return self._stocks
        except Exception as e:
            raise e
    
    def get_by_id(self, stock_id: int) -> Optional[Stock]:
        try:
            if stock_id is None:
                return None
            return self._stocks.get(stock_id)
        except Exception as e:
            raise e
    
    def update(self, stock_id: int, stock: Stock) -> Optional[Stock]:
        try:
            if stock_id is None or stock_id not in self._stocks:
                return None
            self._stocks[stock_id] = stock
            return stock
        except Exception as e:
            raise e
    
    def delete(self, stock_id: int) -> bool:
        try:
            if stock_id is None or stock_id not in self._stocks:
                return False
            del self._stocks[stock_id]
            return True
        except Exception as e:
            raise e
