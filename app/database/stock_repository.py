from sqlalchemy.orm import Session
from app.database.models import Stock
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StockRepository:
    """Repository for stock operations."""
    
    @staticmethod
    def create(session: Session, stock_name: str, ticker: str, 
               screener_link: Optional[str] = None, market_size: Optional[str] = None,
               last_stock_price: Optional[int] = None) -> Stock:
        """Create a new stock record."""
        try:
            stock = Stock(
                stock_name=stock_name,
                ticker=ticker,
                screener_link=screener_link,
                market_size=market_size,
                last_stock_price=last_stock_price
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)
            return stock
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating stock: {str(e)}")
            raise
    

    @staticmethod
    def get_by_ticker(session: Session, ticker: str) -> Optional[Stock]:
        """Get stock by ticker symbol."""
        try:
            return session.query(Stock).filter(Stock.ticker == ticker).first()
        except Exception as e:
            logger.error(f"Error getting stock by ticker: {str(e)}")
            return None
    
    @staticmethod
    def get_all(session: Session, limit: int = 100, offset: int = 0) -> List[Stock]:
        """Get all stocks with pagination."""
        try:
            return session.query(Stock)\
                .order_by(Stock.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
        except Exception as e:
            logger.error(f"Error getting stocks: {str(e)}")
            return []
    
    @staticmethod
    def update(session: Session, stock_id: int, **kwargs) -> bool:
        """Update stock record."""
        try:
            stock = StockRepository.get_by_id(session, stock_id)
            if not stock:
                return False
            
            for key, value in kwargs.items():
                if hasattr(stock, key) and value is not None:
                    setattr(stock, key, value)
            
            stock.update_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stock: {str(e)}")
            return False
    
    @staticmethod
    def delete(session: Session, stock_id: int) -> bool:
        """Delete stock record."""
        try:
            stock = StockRepository.get_by_id(session, stock_id)
            if not stock:
                return False
            
            session.delete(stock)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting stock: {str(e)}")
            return False
    
    @staticmethod
    def search_by_name(session: Session, search_term: str, limit: int = 50) -> List[Stock]:
        """Search stocks by name (case-insensitive)."""
        try:
            return session.query(Stock)\
                .filter(Stock.stock_name.ilike(f"%{search_term}%"))\
                .order_by(Stock.stock_name)\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []
