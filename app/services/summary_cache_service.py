from typing import Optional, List
from datetime import date
from app.database.connection import DatabaseConnection
from app.database.summary_repository import SummaryRepository
from app.database.stock_repository import StockRepository
import logging

logger = logging.getLogger(__name__)

ANSWER_FIELDS = ["answer1", "answer2", "answer3", "answer4", "answer5"]


class SummaryCacheService:
    """Caches batch-evaluate Q&A answers in concall_summary, keyed by document_id (RAG doc_id)."""

    @staticmethod
    def get_cached_answers(document_id: str) -> Optional[List[str]]:
        """Return cached answer1..5 for a doc_id, or None if uncached / incomplete / DB disabled."""
        if not DatabaseConnection.is_enabled():
            return None

        session = DatabaseConnection.get_session()
        if not session:
            return None

        try:
            summary = SummaryRepository.get_by_document_id(session, document_id)
            if not summary:
                return None

            answers = [getattr(summary, field) for field in ANSWER_FIELDS]
            if any(answer is None for answer in answers):
                return None

            return answers
        finally:
            session.close()

    @staticmethod
    def save_answers(
        document_id: str,
        answers: List[str],
        ticker: Optional[str] = None,
        quarter_date: Optional[date] = None,
        concall_url: Optional[str] = None
    ) -> None:
        """Persist batch-evaluate answers for a doc_id. No-ops if DB is not configured."""
        if not DatabaseConnection.is_enabled():
            return

        session = DatabaseConnection.get_session()
        if not session:
            return

        try:
            stock_id = None
            if ticker:
                stock = StockRepository.get_by_ticker(session, ticker)
                if stock:
                    stock_id = stock.id
                else:
                    logger.warning(f"Stock not found for ticker: {ticker}")

            answer_kwargs = {field: answers[i] for i, field in enumerate(ANSWER_FIELDS)}

            existing = SummaryRepository.get_by_document_id(session, document_id)
            if existing:
                SummaryRepository.update(session, existing.id, concall_url=concall_url, **answer_kwargs)
            else:
                SummaryRepository.create(
                    session=session,
                    stock_id=stock_id,
                    quarter_date=quarter_date,
                    concall_url=concall_url,
                    document_id=document_id,
                    **answer_kwargs
                )
        except Exception as e:
            logger.error(f"Error saving cached summary answers for doc_id {document_id}: {str(e)}")
        finally:
            session.close()
