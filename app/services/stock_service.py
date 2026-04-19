from typing import Dict, Optional
from app.models.stock import Stock
from app.repositories.stock_repository import StockRepository


class StockService:
    def __init__(self, repository: StockRepository):
        self.repository = repository
    
    def create_stock(self, stock_id: int, stock: Stock) -> Stock:
        try:
            if stock_id is None:
                raise ValueError("Stock ID cannot be None")
            if stock is None:
                raise ValueError("Stock cannot be None")
            return self.repository.create(stock_id, stock)
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error creating stock: {str(e)}")
    
    def get_all_stocks(self) -> Dict[int, Stock]:
        try:
            return self.repository.get_all()
        except Exception as e:
            raise Exception(f"Error retrieving stocks: {str(e)}")
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        try:
            if stock_id is None:
                return None
            return self.repository.get_by_id(stock_id)
        except Exception as e:
            raise Exception(f"Error retrieving stock: {str(e)}")
    
    def update_stock(self, stock_id: int, stock: Stock) -> Optional[Stock]:
        try:
            if stock_id is None:
                raise ValueError("Stock ID cannot be None")
            if stock is None:
                raise ValueError("Stock cannot be None")
            return self.repository.update(stock_id, stock)
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error updating stock: {str(e)}")
    
    def delete_stock(self, stock_id: int) -> bool:
        try:
            if stock_id is None:
                return False
            return self.repository.delete(stock_id)
        except Exception as e:
            raise Exception(f"Error deleting stock: {str(e)}")
