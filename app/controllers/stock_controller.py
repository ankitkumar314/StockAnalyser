from typing import Dict
from fastapi import HTTPException
from app.models.stock import Stock
from app.services.stock_service import StockService


class StockController:
    def __init__(self, service: StockService):
        self.service = service
    
    def create_stock(self, stock_id: int, stock: Stock) -> Stock:
        try:
            if stock_id is None:
                raise HTTPException(status_code=400, detail="Stock ID cannot be None")
            if stock is None:
                raise HTTPException(status_code=400, detail="Stock cannot be None")
            return self.service.create_stock(stock_id, stock)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_stocks(self) -> Dict[int, Stock]:
        try:
            return self.service.get_all_stocks()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_stock_by_id(self, stock_id: int) -> Stock:
        try:
            if stock_id is None:
                raise HTTPException(status_code=400, detail="Stock ID cannot be None")
            stock = self.service.get_stock_by_id(stock_id)
            if stock is None:
                raise HTTPException(status_code=404, detail="Stock not found")
            return stock
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_stock(self, stock_id: int, stock: Stock) -> Stock:
        try:
            if stock_id is None:
                raise HTTPException(status_code=400, detail="Stock ID cannot be None")
            if stock is None:
                raise HTTPException(status_code=400, detail="Stock cannot be None")
            updated_stock = self.service.update_stock(stock_id, stock)
            if updated_stock is None:
                raise HTTPException(status_code=404, detail="Stock not found")
            return updated_stock
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_stock(self, stock_id: int) -> Dict[str, str]:
        try:
            if stock_id is None:
                raise HTTPException(status_code=400, detail="Stock ID cannot be None")
            deleted = self.service.delete_stock(stock_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Stock not found")
            return {"message": "Deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
