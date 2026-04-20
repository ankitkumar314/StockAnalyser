from sqlalchemy.orm import Session
from app.database.models import StockScrapeData
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class StockScrapeDataRepository:
    """Repository for stock scrape data operations."""
    
    @staticmethod
    def create(
        session: Session,
        stock_id: int,
        quarter_result: Optional[Dict] = None,
        growth_sales: Optional[Dict] = None,
        growth_net_profit: Optional[Dict] = None,
        growth_operating_profit: Optional[Dict] = None,
        shareholding_pattern: Optional[Dict] = None,
        profit_loss: Optional[Dict] = None,
        quarter_date = None
    ) -> StockScrapeData:
        """Create a new stock scrape data record."""
        try:
            scrape_data = StockScrapeData(
                stockId=stock_id,
                quarter_result=quarter_result,
                growth_sales=growth_sales,
                growth_net_profit=growth_net_profit,
                growth_operating_profit=growth_operating_profit,
                shareholding_pattern=shareholding_pattern,
                profit_loss=profit_loss,
                quarter_date=quarter_date
            )
            session.add(scrape_data)
            session.commit()
            session.refresh(scrape_data)
            return scrape_data
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating stock scrape data: {str(e)}")
            raise
    
    @staticmethod
    def get_by_id(session: Session, scrape_id: int) -> Optional[StockScrapeData]:
        """Get stock scrape data by ID."""
        try:
            return session.query(StockScrapeData).filter(StockScrapeData.id == scrape_id).first()
        except Exception as e:
            logger.error(f"Error getting stock scrape data by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_by_stock_id(session: Session, stock_id: int, limit: int = 10) -> List[StockScrapeData]:
        """Get all scrape data for a specific stock."""
        try:
            return session.query(StockScrapeData)\
                .filter(StockScrapeData.stockId == stock_id)\
                .order_by(StockScrapeData.created_at.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting stock scrape data by stock ID: {str(e)}")
            return []
    
    @staticmethod
    def find_by_stock_and_quarter_date(session: Session, stock_id: int, quarter_date) -> Optional[StockScrapeData]:
        """
        Find existing scrape data for the same quarter using quarter_date.
        """
        try:
            if not quarter_date:
                return None
            
            return session.query(StockScrapeData)\
                .filter(
                    StockScrapeData.stockId == stock_id,
                    StockScrapeData.quarter_date == quarter_date
                )\
                .first()
        except Exception as e:
            logger.error(f"Error finding scrape data by quarter date: {str(e)}")
            return None
    
    @staticmethod
    def get_latest_by_stock_id(session: Session, stock_id: int) -> Optional[StockScrapeData]:
        """Get the most recent scrape data for a specific stock."""
        try:
            return session.query(StockScrapeData)\
                .filter(StockScrapeData.stockId == stock_id)\
                .order_by(StockScrapeData.created_at.desc())\
                .first()
        except Exception as e:
            logger.error(f"Error getting latest stock scrape data: {str(e)}")
            return None
    
    @staticmethod
    def get_all(session: Session, limit: int = 100, offset: int = 0) -> List[StockScrapeData]:
        """Get all stock scrape data with pagination."""
        try:
            return session.query(StockScrapeData)\
                .order_by(StockScrapeData.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
        except Exception as e:
            logger.error(f"Error getting all stock scrape data: {str(e)}")
            return []
    
    @staticmethod
    def update(session: Session, scrape_id: int, **kwargs) -> bool:
        """Update stock scrape data record."""
        try:
            scrape_data = StockScrapeDataRepository.get_by_id(session, scrape_id)
            if not scrape_data:
                return False
            
            for key, value in kwargs.items():
                if hasattr(scrape_data, key) and value is not None:
                    setattr(scrape_data, key, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stock scrape data: {str(e)}")
            return False
    
