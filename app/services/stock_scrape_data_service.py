from typing import Dict, Optional
from datetime import datetime, date
from app.database.connection import DatabaseConnection
from app.database.stock_scrap_data_repository import StockScrapeDataRepository
from app.database.models import StockScrapeData
from app.database.stock_repository import StockRepository
import logging

from app.models.stock import Stock

logger = logging.getLogger(__name__)


class StockScrapeDataService:
    """Service layer for stock scrape data operations."""
    
    @staticmethod
    def _extract_quarter_date(quarter_data: Optional[Dict]) -> Optional[date]:
        """
        Extract quarter date from current date.
        Calculates the quarter (Q1-Q4) based on current month and returns
        the last day of that quarter.
        
        Quarter mapping:
        - Q1: Jan-Mar → March 31
        - Q2: Apr-Jun → June 30
        - Q3: Jul-Sep → September 30
        - Q4: Oct-Dec → December 31
        
        Args:
            quarter_data: Dictionary containing quarter financial data (optional)
            
        Returns:
            date object representing the last day of the current quarter
        """
        try:
            today = date.today()
            year = today.year
            month = today.month
            
            # Determine quarter and last day of quarter
            if month <= 3:  # Q1: Jan-Mar
                quarter_end = date(year, 3, 31)
            elif month <= 6:  # Q2: Apr-Jun
                quarter_end = date(year, 6, 30)
            elif month <= 9:  # Q3: Jul-Sep
                quarter_end = date(year, 9, 30)
            else:  # Q4: Oct-Dec
                quarter_end = date(year, 12, 31)
            
            logger.info(f"Extracted quarter date: {quarter_end} (Q{(month-1)//3 + 1}-{year})")
            return quarter_end
            
        except Exception as e:
            logger.error(f"Error extracting quarter date: {str(e)}")
            return None
    
    @staticmethod
    def save_scrape_result(stock_id: int, scrape_result: Dict) -> Optional[StockScrapeData]:
        """
        Save scraped financial data to the database.
        If data for the same quarter already exists, update it instead of creating a new record.
        
        Args:
            stock_id: ID of the stock
            scrape_result: Dictionary containing scraped data with keys:
                - 'data': Financial data with sections like 'quarters', 'profit-loss', etc.
                - 'growth': Growth metrics (sales, net_profit, operating_profit)
                - 'concalls': Conference call data
        
        Returns:
            StockScrapeData object if successful, None otherwise
        """
        try:
            if not DatabaseConnection.is_enabled():
                logger.warning("Database not configured, cannot save scrape data")
                return None
            
            session = DatabaseConnection.get_session()
            if not session:
                logger.error("Failed to get database session")
                return None
            
            try:
                data = scrape_result.get('data', {})
                growth = scrape_result.get('growth', {})
                
                quarter_data = data.get('quarters')
                growth_sales_data = growth.get('sales')
                growth_net_profit_data = growth.get('net_profit')
                growth_operating_profit_data = growth.get('operating_profit')
                shareholding_data = data.get('shareholding')
                profit_loss_data = data.get('profit-loss')
                
                # Extract quarter date from the scraped data
                quarter_date = StockScrapeDataService._extract_quarter_date(quarter_data)
                
                if not quarter_date:
                    logger.warning(f"Could not extract quarter date, using current date for stock_id: {stock_id}")
                    quarter_date = date.today()
                
                # Check if data already exists for this stock and quarter
                existing_record = StockScrapeDataRepository.find_by_stock_and_quarter_date(
                    session=session,
                    stock_id=stock_id,
                    quarter_date=quarter_date
                )
                
                if existing_record:
                    logger.info(f"Found existing scrape data for quarter {quarter_date}, updating record ID: {existing_record.id}")
                    
                    success = StockScrapeDataRepository.update(
                        session=session,
                        scrape_id=existing_record.id,
                        quarter_result=quarter_data,
                        growth_sales=growth_sales_data,
                        growth_net_profit=growth_net_profit_data,
                        growth_operating_profit=growth_operating_profit_data,
                        shareholding_pattern=shareholding_data,
                        profit_loss=profit_loss_data,
                        quarter_date=quarter_date
                    )
                    
                    if success:
                        updated_record = StockScrapeDataRepository.get_by_id(session, existing_record.id)
                        logger.info(f"Successfully updated scrape data for stock_id: {stock_id}, quarter: {quarter_date}")
                        return updated_record
                    else:
                        logger.error(f"Failed to update existing scrape data for stock_id: {stock_id}")
                        return None
                else:
                    logger.info(f"No existing data for quarter {quarter_date}, creating new record for stock_id: {stock_id}")
                    
                    scrape_data = StockScrapeDataRepository.create(
                        session=session,
                        stock_id=stock_id,
                        quarter_result=quarter_data,
                        growth_sales=growth_sales_data,
                        growth_net_profit=growth_net_profit_data,
                        growth_operating_profit=growth_operating_profit_data,
                        shareholding_pattern=shareholding_data,
                        profit_loss=profit_loss_data,
                        quarter_date=quarter_date
                    )
                    
                    logger.info(f"Successfully created new scrape data for stock_id: {stock_id}, quarter: {quarter_date}")
                    return scrape_data
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error saving scrape data: {str(e)}")
            return None
    
    @staticmethod
    def get_latest_scrape_data(ticker: str) -> Optional[StockScrapeData]:
        """Get the most recent scrape data for a stock."""
        try:
            if not DatabaseConnection.is_enabled():
                return None
            
            session = DatabaseConnection.get_session()
            if not session:
                return None
            
            try:
                stock = StockRepository.get_by_ticker(session, ticker)
                if not stock:
                    logger.warning(f"Stock not found for ticker: {ticker}")
                    return None
                return StockScrapeDataRepository.get_latest_by_stock_id(session, stock.id)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting latest scrape data: {str(e)}")
            return None
    
    @staticmethod
    def get_scrape_history(stock_id: int, limit: int = 10) -> list:
        """Get scrape history for a stock."""
        try:
            if not DatabaseConnection.is_enabled():
                return []
            
            session = DatabaseConnection.get_session()
            if not session:
                return []
            
            try:
                return StockScrapeDataRepository.get_by_stock_id(session, stock_id, limit)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting scrape history: {str(e)}")
            return []
