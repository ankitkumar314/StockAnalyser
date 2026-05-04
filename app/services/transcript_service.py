from typing import Optional, List
from datetime import date
from app.database.connection import DatabaseConnection
from app.database.transcript_repository import TranscriptRepository
from app.database.summary_repository import SummaryRepository
from app.database.stock_repository import StockRepository
from app.database.models import ConcallTranscript, ConcallSummary
import logging

logger = logging.getLogger(__name__)


class TranscriptService:
    """Service layer for conference call transcript management."""
    
    @staticmethod
    def _calculate_quarter_date(current_date: date = None) -> date:
        """Calculate quarter end date from current date."""
        try:
            if current_date is None:
                current_date = date.today()
            
            year = current_date.year
            month = current_date.month
            
            if month <= 3:
                return date(year, 3, 31)
            elif month <= 6:
                return date(year, 6, 30)
            elif month <= 9:
                return date(year, 9, 30)
            else:
                return date(year, 12, 31)
        except Exception as e:
            logger.error(f"Error calculating quarter date: {str(e)}")
            return date.today()
    
    @staticmethod
    def create_transcript(
        ticker: str,
        transcript_url: Optional[str] = None,
        quarter_date: Optional[date] = None
    ) -> Optional[ConcallTranscript]:
        """
        Create a new transcript record with quarter-based deduplication.
        If transcript exists for the same quarter, returns existing record.
        """
        try:
            if not DatabaseConnection.is_enabled():
                logger.warning("Database not configured")
                return None
            
            session = DatabaseConnection.get_session()
            if not session:
                return None
            
            try:
                stock = StockRepository.get_by_ticker(session, ticker)
                if not stock:
                    logger.error(f"Stock not found for ticker: {ticker}")
                    return None
                
                if quarter_date is None:
                    quarter_date = TranscriptService._calculate_quarter_date()
                
                existing = TranscriptRepository.get_by_stock_and_quarter(
                    session, stock.id, quarter_date
                )
                
                if existing:
                    logger.info(f"Transcript already exists for {ticker} Q{(quarter_date.month-1)//3 + 1}-{quarter_date.year}")
                    return existing
                
                transcript = TranscriptRepository.create(
                    session=session,
                    stock_id=stock.id,
                    quarter_date=quarter_date,
                    transcript_url=transcript_url,
                    status='pending'
                )
                
                logger.info(f"Created transcript for {ticker}, ID: {transcript.id}")
                return transcript
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error creating transcript: {str(e)}")
            return None
    
    @staticmethod
    def get_transcript_by_id(transcript_id: int) -> Optional[ConcallTranscript]:
        """Get transcript by ID."""
        try:
            if not DatabaseConnection.is_enabled():
                return None
            
            session = DatabaseConnection.get_session()
            if not session:
                return None
            
            try:
                return TranscriptRepository.get_by_id(session, transcript_id)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None
    
    @staticmethod
    def get_transcripts_by_ticker(ticker: str, limit: int = 10) -> List[ConcallTranscript]:
        """Get all transcripts for a ticker."""
        try:
            if not DatabaseConnection.is_enabled():
                return []
            
            session = DatabaseConnection.get_session()
            if not session:
                return []
            
            try:
                stock = StockRepository.get_by_ticker(session, ticker)
                if not stock:
                    return []
                
                return TranscriptRepository.get_by_stock_id(session, stock.id, limit)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting transcripts: {str(e)}")
            return []
    
    @staticmethod
    def get_pending_transcripts(limit: int = 50) -> List[ConcallTranscript]:
        """Get all pending transcripts that need summary generation."""
        try:
            if not DatabaseConnection.is_enabled():
                return []
            
            session = DatabaseConnection.get_session()
            if not session:
                return []
            
            try:
                return TranscriptRepository.get_pending_transcripts(session, limit)
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error getting pending transcripts: {str(e)}")
            return []
    
    @staticmethod
    def update_transcript_status(
        transcript_id: int,
        status: str,
        summary_id: Optional[int] = None
    ) -> bool:
        """Update transcript status and link to summary."""
        try:
            if not DatabaseConnection.is_enabled():
                return False
            
            session = DatabaseConnection.get_session()
            if not session:
                return False
            
            try:
                return TranscriptRepository.update_status(
                    session, transcript_id, status, summary_id
                )
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error updating transcript status: {str(e)}")
            return False
    
    # @staticmethod
    # def create_summary(
    #     stock_id: int,
    #     quarter_date: date,
    #     answer1: Optional[str] = None,
    #     answer2: Optional[str] = None,
    #     answer3: Optional[str] = None,
    #     answer4: Optional[str] = None,
    #     answer5: Optional[str] = None,
    #     prev_concall_hisotry: Optional[str] = None,
    #     concall_url: Optional[str] = None,
    #     document_id: Optional[str] = None
    # ) -> Optional[ConcallSummary]:
    #     """Create a summary for a transcript."""
    #     try:
    #         if not DatabaseConnection.is_enabled():
    #             return None
            
    #         session = DatabaseConnection.get_session()
    #         if not session:
    #             return None
            
    #         try:
    #             summary = SummaryRepository.create(
    #                 session=session,
    #                 stock_id=stock_id,
    #                 quarter_date=quarter_date,
    #                 answer1=answer1,
    #                 answer2=answer2,
    #                 answer3=answer3,
    #                 answer4=answer4,
    #                 answer5=answer5,
    #                 prev_concall_hisotry=prev_concall_hisotry,
    #                 concall_url=concall_url,
    #                 document_id=document_id
    #             )
                
    #             logger.info(f"Created summary for stock_id: {stock_id}, ID: {summary.id}")
    #             return summary
                
    #         finally:
    #             session.close()
                
    #     except Exception as e:
    #         logger.error(f"Error creating summary: {str(e)}")
    #         return None
    
    # @staticmethod
    # def get_summary_by_ticker(ticker: str, quarter_date: Optional[date] = None) -> Optional[ConcallSummary]:
    #     """Get summary for a ticker and quarter."""
    #     try:
    #         if not DatabaseConnection.is_enabled():
    #             return None
            
    #         session = DatabaseConnection.get_session()
    #         if not session:
    #             return None
            
    #         try:
    #             stock = StockRepository.get_by_ticker(session, ticker)
    #             if not stock:
    #                 return None
                
    #             if quarter_date:
    #                 return SummaryRepository.get_by_stock_and_quarter(
    #                     session, stock.id, quarter_date
    #                 )
    #             else:
    #                 summaries = SummaryRepository.get_by_stock_id(session, stock.id, limit=1)
    #                 return summaries[0] if summaries else None
                    
    #         finally:
    #             session.close()
                
    #     except Exception as e:
    #         logger.error(f"Error getting summary: {str(e)}")
    #         return None
