from sqlalchemy.orm import Session
from app.database.models import ConcallSummary
from typing import Optional, List
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SummaryRepository:
    """Repository for concall summary operations."""
    
    @staticmethod
    def create(
        session: Session,
        stock_id: int,
        quarter_date: date,
        answer1: Optional[str] = None,
        answer2: Optional[str] = None,
        answer3: Optional[str] = None,
        answer4: Optional[str] = None,
        answer5: Optional[str] = None,
        prev_concall_hisotry: Optional[str] = None,
        concall_url: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> ConcallSummary:
        """Create a new summary record."""
        try:
            summary = ConcallSummary(
                stockid=stock_id,
                quarter_date=quarter_date,
                answer1=answer1,
                answer2=answer2,
                answer3=answer3,
                answer4=answer4,
                answer5=answer5,
                prev_concall_hisotry=prev_concall_hisotry,
                concall_url=concall_url,
                document_id=document_id
            )
            session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating summary: {str(e)}")
            raise
    
    @staticmethod
    def get_by_id(session: Session, summary_id: int) -> Optional[ConcallSummary]:
        """Get summary by ID."""
        try:
            return session.query(ConcallSummary).filter(
                ConcallSummary.id == summary_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting summary by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_by_stock_and_quarter(
        session: Session,
        stock_id: int,
        quarter_date: date
    ) -> Optional[ConcallSummary]:
        """Get summary by stock ID and quarter date."""
        try:
            return session.query(ConcallSummary).filter(
                ConcallSummary.stockid == stock_id,
                ConcallSummary.quarter_date == quarter_date
            ).first()
        except Exception as e:
            logger.error(f"Error getting summary by stock and quarter: {str(e)}")
            return None
    
    @staticmethod
    def get_by_stock_id(
        session: Session,
        stock_id: int,
        limit: int = 10
    ) -> List[ConcallSummary]:
        """Get all summaries for a stock."""
        try:
            return session.query(ConcallSummary)\
                .filter(ConcallSummary.stockid == stock_id)\
                .order_by(ConcallSummary.quarter_date.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting summaries by stock ID: {str(e)}")
            return []
    
    @staticmethod
    def update(session: Session, summary_id: int, **kwargs) -> bool:
        """Update summary record."""
        try:
            summary = SummaryRepository.get_by_id(session, summary_id)
            if not summary:
                return False
            
            for key, value in kwargs.items():
                if hasattr(summary, key) and value is not None:
                    setattr(summary, key, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating summary: {str(e)}")
            return False
    
    @staticmethod
    def delete(session: Session, summary_id: int) -> bool:
        """Delete summary record."""
        try:
            summary = SummaryRepository.get_by_id(session, summary_id)
            if not summary:
                return False
            
            session.delete(summary)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting summary: {str(e)}")
            return False
