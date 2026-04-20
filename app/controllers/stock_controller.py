from typing import Dict, Optional
from fastapi import HTTPException
from app.models.stock import Stock, StockListResponse, StockUpdateRequest, StockResponse
from app.database.connection import DatabaseConnection
from app.database.stock_repository import StockRepository as DBStockRepository
import logging

logger = logging.getLogger(__name__)


class StockController:
    def __init__(self):
        self.db_enabled = DatabaseConnection.is_enabled()
        if self.db_enabled:
            logger.info("Stock controller: Database persistence enabled")
        else:
            logger.info("Stock controller: Using in-memory storage")
    
    
    def create_stock_db(self, request: Stock) -> StockResponse:
        """Create stock in database."""
        try:
            if not self.db_enabled:
                raise HTTPException(status_code=503, detail="Database not configured")
            
            if not request.stock_name or not request.ticker:
                raise HTTPException(status_code=400, detail="stock_name and ticker are required")
            
            session = DatabaseConnection.get_session()
            if not session:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            try:
                existing = DBStockRepository.get_by_ticker(session, request.ticker)
                if existing:
                    raise HTTPException(status_code=409, detail=f"Stock with ticker {request.ticker} already exists")
                
                stock = DBStockRepository.create(
                    session=session,
                    stock_name=request.stock_name,
                    ticker=request.ticker,
                    screener_link=request.screener_link,
                    market_size=request.market_size,
                    last_stock_price=request.last_stock_price
                )
                return StockResponse.model_validate(stock)
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating stock in DB: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_stock_by_ticker(self, ticker: str) -> StockResponse:
        """Get stock by ticker from database."""
        try:
            if not self.db_enabled:
                raise HTTPException(status_code=503, detail="Database not configured")
            
            if not ticker:
                raise HTTPException(status_code=400, detail="Ticker cannot be empty")
            
            session = DatabaseConnection.get_session()
            if not session:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            try:
                stock = DBStockRepository.get_by_ticker(session, ticker.upper())
                if not stock:
                    raise HTTPException(status_code=404, detail=f"Stock with ticker {ticker} not found")
                return StockResponse.model_validate(stock)
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting stock by ticker: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_stocks(self, limit: int = 100, offset: int = 0) -> StockListResponse:
        """Get all stocks from database with pagination."""
        try:
            if not self.db_enabled:
                raise HTTPException(status_code=503, detail="Database not configured")
            
            session = DatabaseConnection.get_session()
            if not session:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            try:
                stocks = DBStockRepository.get_all(session, limit=limit, offset=offset)
                stock_responses = [StockResponse.model_validate(stock) for stock in stocks]
                return {"total": len(stock_responses), "stocks": stock_responses}
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting stocks from DB: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_stock(self, stock_id: int, request: StockUpdateRequest) -> StockResponse:
        """Update stock in database."""
        try:
            if not self.db_enabled:
                raise HTTPException(status_code=503, detail="Database not configured")
            
            if stock_id is None or stock_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid stock ID")
            
            session = DatabaseConnection.get_session()
            if not session:
                raise HTTPException(status_code=503, detail="Database connection failed")
            
            try:
                stock = DBStockRepository.get_by_id(session, stock_id)
                if not stock:
                    raise HTTPException(status_code=404, detail=f"Stock with ID {stock_id} not found")
                
                update_data = {}
                if request.stock_name is not None:
                    update_data['stock_name'] = request.stock_name
                if request.ticker is not None:
                    update_data['ticker'] = request.ticker
                if request.screener_link is not None:
                    update_data['screener_link'] = request.screener_link
                if request.market_size is not None:
                    update_data['market_size'] = request.market_size
                if request.last_stock_price is not None:
                    update_data['last_stock_price'] = request.last_stock_price
                
                if not update_data:
                    raise HTTPException(status_code=400, detail="No fields to update")
                
                DBStockRepository.update(session, stock_id, **update_data)
                updated_stock = DBStockRepository.get_by_id(session, stock_id)
                return StockResponse.model_validate(updated_stock)
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating stock in DB: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    