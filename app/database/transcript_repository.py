from sqlalchemy.orm import Session
from app.database.models import ConcallTranscript
from typing import Optional, List
from datetime import date
import logging

logger = logging.getLogger(__name__)


class TranscriptRepository:
    """Repository for conference call transcript operations."""
    
    @staticmethod
    def create(
        session: Session,
        stock_id: int,
        quarter_date: date,
        transcript_url: Optional[str] = None,
        status: str = 'pending'
    ) -> ConcallTranscript:
        """Create a new transcript record."""
        try:
            transcript = ConcallTranscript(
                stock_id=stock_id,
                quarter_date=quarter_date,
                transcript_url=transcript_url,
                status=status
            )
            session.add(transcript)
            session.commit()
            session.refresh(transcript)
            return transcript
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating transcript: {str(e)}")
            raise
    
    @staticmethod
    def get_by_id(session: Session, transcript_id: int) -> Optional[ConcallTranscript]:
        """Get transcript by ID."""
        try:
            return session.query(ConcallTranscript).filter(
                ConcallTranscript.id == transcript_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting transcript by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_by_stock_and_quarter(
        session: Session,
        stock_id: int,
        quarter_date: date
    ) -> Optional[ConcallTranscript]:
        """Get transcript by stock ID and quarter date."""
        try:
            return session.query(ConcallTranscript).filter(
                ConcallTranscript.stock_id == stock_id,
                ConcallTranscript.quarter_date == quarter_date
            ).first()
        except Exception as e:
            logger.error(f"Error getting transcript by stock and quarter: {str(e)}")
            return None
    
    @staticmethod
    def get_by_stock_id(
        session: Session,
        stock_id: int,
        limit: int = 10
    ) -> List[ConcallTranscript]:
        """Get all transcripts for a stock."""
        try:
            return session.query(ConcallTranscript)\
                .filter(ConcallTranscript.stock_id == stock_id)\
                .order_by(ConcallTranscript.quarter_date.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting transcripts by stock ID: {str(e)}")
            return []
    
    @staticmethod
    def get_pending_transcripts(session: Session, limit: int = 50) -> List[ConcallTranscript]:
        """Get all pending transcripts that need summary generation."""
        try:
            return session.query(ConcallTranscript)\
                .filter(ConcallTranscript.status == 'pending')\
                .order_by(ConcallTranscript.created_at.asc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting pending transcripts: {str(e)}")
            return []
    
    @staticmethod
    def update(session: Session, transcript_id: int, **kwargs) -> bool:
        """Update transcript record."""
        try:
            transcript = TranscriptRepository.get_by_id(session, transcript_id)
            if not transcript:
                return False
            
            for key, value in kwargs.items():
                if hasattr(transcript, key) and value is not None:
                    setattr(transcript, key, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating transcript: {str(e)}")
            return False
    
    @staticmethod
    def update_status(
        session: Session,
        transcript_id: int,
        status: str,
        summary_id: Optional[int] = None
    ) -> bool:
        """Update transcript status and optionally link to summary."""
        try:
            transcript = TranscriptRepository.get_by_id(session, transcript_id)
            if not transcript:
                return False
            
            transcript.status = status
            if summary_id is not None:
                transcript.summary_id = summary_id
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating transcript status: {str(e)}")
            return False
    
    @staticmethod
    def delete(session: Session, transcript_id: int) -> bool:
        """Delete transcript record."""
        try:
            transcript = TranscriptRepository.get_by_id(session, transcript_id)
            if not transcript:
                return False
            
            session.delete(transcript)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting transcript: {str(e)}")
            return False
