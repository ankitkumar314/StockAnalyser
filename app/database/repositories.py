from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database.models import Document, Query, BatchJob, BatchQuestion, AgentRun, CostTracking, Stock
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document operations."""
    
    @staticmethod
    def create(session: Session, doc_id: str, pdf_url: str, chunks_count: int, 
               pdf_filename: Optional[str] = None, vectorstore_path: Optional[str] = None,
               doc_metadata: Optional[Dict] = None) -> Document:
        """Create a new document record."""
        try:
            document = Document(
                doc_id=doc_id,
                pdf_url=pdf_url,
                pdf_filename=pdf_filename,
                chunks_count=chunks_count,
                vectorstore_path=vectorstore_path,
                doc_metadata=doc_metadata
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            return document
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise
    
    @staticmethod
    def get_by_doc_id(session: Session, doc_id: str) -> Optional[Document]:
        """Get document by external doc_id."""
        try:
            return session.query(Document).filter(Document.doc_id == doc_id).first()
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    @staticmethod
    def get_all(session: Session, status: Optional[str] = None, limit: int = 100) -> List[Document]:
        """Get all documents with optional status filter."""
        try:
            query = session.query(Document)
            if status:
                query = query.filter(Document.status == status)
            return query.order_by(Document.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
    
    @staticmethod
    def update_status(session: Session, doc_id: str, status: str) -> bool:
        """Update document status."""
        try:
            document = DocumentRepository.get_by_doc_id(session, doc_id)
            if document:
                document.status = status
                document.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating document status: {str(e)}")
            return False


class QueryRepository:
    """Repository for query operations."""
    
    @staticmethod
    def create(session: Session, document_id: str, query_text: str, 
               max_iterations: int = 3) -> Query:
        """Create a new query record."""
        try:
            query = Query(
                document_id=document_id,
                query_text=query_text,
                max_iterations=max_iterations
            )
            session.add(query)
            session.commit()
            session.refresh(query)
            return query
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating query: {str(e)}")
            raise
    
    @staticmethod
    def update_result(session: Session, query_id: str, result: Dict[str, Any]) -> bool:
        """Update query with result data."""
        try:
            query = session.query(Query).filter(Query.id == query_id).first()
            if not query:
                return False
            
            query.refined_query = result.get("refined_query")
            query.answer = result.get("answer")
            query.final_answer = result.get("final_answer")
            query.iteration_count = result.get("iteration_count", 0)
            query.is_answer_correct = result.get("is_answer_correct", False)
            query.is_sufficient = result.get("is_sufficient", False)
            
            query.retrieval_metadata = result.get("retrieval_metadata")
            query.answer_metadata = result.get("answer_metadata")
            query.evaluation_metadata = result.get("evaluation_metadata")
            
            query.total_tokens = result.get("total_tokens", 0)
            query.input_tokens = result.get("input_tokens", 0)
            query.output_tokens = result.get("output_tokens", 0)
            query.cache_tokens = result.get("cache_tokens", 0)
            query.estimated_cost = result.get("estimated_cost", 0.0)
            
            query.processing_time_ms = result.get("processing_time_ms")
            query.completed_at = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating query result: {str(e)}")
            return False
    
    @staticmethod
    def get_by_document(session: Session, doc_id: str, limit: int = 50) -> List[Query]:
        """Get queries for a document."""
        try:
            document = DocumentRepository.get_by_doc_id(session, doc_id)
            if not document:
                return []
            
            return session.query(Query)\
                .filter(Query.document_id == document.id)\
                .order_by(Query.created_at.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error getting queries: {str(e)}")
            return []


class BatchJobRepository:
    """Repository for batch job operations."""
    
    @staticmethod
    def create(session: Session, job_id: str, document_id: str, 
               total_questions: int) -> BatchJob:
        """Create a new batch job record."""
        try:
            batch_job = BatchJob(
                job_id=job_id,
                document_id=document_id,
                total_questions=total_questions,
                status='pending'
            )
            session.add(batch_job)
            session.commit()
            session.refresh(batch_job)
            return batch_job
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating batch job: {str(e)}")
            raise
    
    @staticmethod
    def get_by_job_id(session: Session, job_id: str) -> Optional[BatchJob]:
        """Get batch job by job_id."""
        try:
            return session.query(BatchJob).filter(BatchJob.job_id == job_id).first()
        except Exception as e:
            logger.error(f"Error getting batch job: {str(e)}")
            return None
    
    @staticmethod
    def update_status(session: Session, job_id: str, status: str, 
                     progress: Optional[str] = None, error_message: Optional[str] = None) -> bool:
        """Update batch job status."""
        try:
            batch_job = BatchJobRepository.get_by_job_id(session, job_id)
            if not batch_job:
                return False
            
            batch_job.status = status
            if progress:
                batch_job.progress = progress
            if error_message:
                batch_job.error_message = error_message
            
            if status == 'processing' and not batch_job.started_at:
                batch_job.started_at = datetime.utcnow()
            
            if status in ['completed', 'failed']:
                batch_job.completed_at = datetime.utcnow()
                if batch_job.started_at:
                    delta = batch_job.completed_at - batch_job.started_at
                    batch_job.processing_time_ms = int(delta.total_seconds() * 1000)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating batch job status: {str(e)}")
            return False
    
    @staticmethod
    def get_all(session: Session, status: Optional[str] = None, limit: int = 100) -> List[BatchJob]:
        """Get all batch jobs with optional status filter."""
        try:
            query = session.query(BatchJob)
            if status:
                query = query.filter(BatchJob.status == status)
            return query.order_by(BatchJob.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting batch jobs: {str(e)}")
            return []


class BatchQuestionRepository:
    """Repository for batch question operations."""
    
    @staticmethod
    def create(session: Session, batch_job_id: str, question_index: int, 
               question_text: str) -> BatchQuestion:
        """Create a new batch question record."""
        try:
            question = BatchQuestion(
                batch_job_id=batch_job_id,
                question_index=question_index,
                question_text=question_text,
                status='pending'
            )
            session.add(question)
            session.commit()
            session.refresh(question)
            return question
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating batch question: {str(e)}")
            raise
    
    @staticmethod
    def update_result(session: Session, question_id: str, result: Dict[str, Any]) -> bool:
        """Update batch question with result data."""
        try:
            question = session.query(BatchQuestion).filter(BatchQuestion.id == question_id).first()
            if not question:
                return False
            
            question.answer = result.get("answer")
            question.iteration_count = result.get("iteration_count", 0)
            question.status = result.get("status", "completed")
            question.error_message = result.get("error_message")
            
            question.is_grounded = result.get("is_grounded")
            question.is_insightful = result.get("is_insightful")
            question.is_useful = result.get("is_useful")
            question.has_hallucination = result.get("has_hallucination")
            question.coverage = result.get("coverage")
            
            question.total_tokens = result.get("total_tokens", 0)
            question.estimated_cost = result.get("estimated_cost", 0.0)
            question.completed_at = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating batch question result: {str(e)}")
            return False
    
    @staticmethod
    def get_by_batch_job(session: Session, job_id: str) -> List[BatchQuestion]:
        """Get all questions for a batch job."""
        try:
            batch_job = BatchJobRepository.get_by_job_id(session, job_id)
            if not batch_job:
                return []
            
            return session.query(BatchQuestion)\
                .filter(BatchQuestion.batch_job_id == batch_job.id)\
                .order_by(BatchQuestion.question_index)\
                .all()
        except Exception as e:
            logger.error(f"Error getting batch questions: {str(e)}")
            return []


class AgentRunRepository:
    """Repository for agent run operations."""
    
    @staticmethod
    def create(session: Session, agent_type: str, iteration: int,
               query_id: Optional[str] = None, batch_question_id: Optional[str] = None,
               input_data: Optional[Dict] = None, output_data: Optional[Dict] = None,
               execution_time_ms: Optional[int] = None, tokens_used: int = 0,
               cost: float = 0.0, status: str = 'success',
               error_message: Optional[str] = None) -> AgentRun:
        """Create a new agent run record."""
        try:
            agent_run = AgentRun(
                query_id=query_id,
                batch_question_id=batch_question_id,
                agent_type=agent_type,
                iteration=iteration,
                input_data=input_data,
                output_data=output_data,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                cost=cost,
                status=status,
                error_message=error_message
            )
            session.add(agent_run)
            session.commit()
            session.refresh(agent_run)
            return agent_run
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating agent run: {str(e)}")
            raise


class CostTrackingRepository:
    """Repository for cost tracking operations."""
    
    @staticmethod
    def update_daily_stats(session: Session, tracking_date: date, agent_type: Optional[str],
                          model_name: str, tokens: Dict[str, int], cost: float) -> bool:
        """Update or create daily cost tracking stats."""
        try:
            record = session.query(CostTracking).filter(
                and_(
                    CostTracking.date == tracking_date,
                    CostTracking.agent_type == agent_type,
                    CostTracking.model_name == model_name
                )
            ).first()
            
            if record:
                record.total_runs += 1
                record.total_tokens += tokens.get('total', 0)
                record.input_tokens += tokens.get('input', 0)
                record.output_tokens += tokens.get('output', 0)
                record.cache_tokens += tokens.get('cache', 0)
                record.total_cost += cost
                
                record.avg_tokens_per_run = record.total_tokens / record.total_runs
                record.avg_cost_per_run = record.total_cost / record.total_runs
                record.updated_at = datetime.utcnow()
            else:
                record = CostTracking(
                    date=tracking_date,
                    agent_type=agent_type,
                    model_name=model_name,
                    total_runs=1,
                    total_tokens=tokens.get('total', 0),
                    input_tokens=tokens.get('input', 0),
                    output_tokens=tokens.get('output', 0),
                    cache_tokens=tokens.get('cache', 0),
                    total_cost=cost,
                    avg_tokens_per_run=tokens.get('total', 0),
                    avg_cost_per_run=cost
                )
                session.add(record)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating cost tracking: {str(e)}")
            return False
    
    @staticmethod
    def get_summary(session: Session, start_date: Optional[date] = None,
                   end_date: Optional[date] = None, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Get cost summary with optional filters."""
        try:
            query = session.query(
                func.sum(CostTracking.total_runs).label('total_runs'),
                func.sum(CostTracking.total_tokens).label('total_tokens'),
                func.sum(CostTracking.input_tokens).label('input_tokens'),
                func.sum(CostTracking.output_tokens).label('output_tokens'),
                func.sum(CostTracking.cache_tokens).label('cache_tokens'),
                func.sum(CostTracking.total_cost).label('total_cost')
            )
            
            if start_date:
                query = query.filter(CostTracking.date >= start_date)
            if end_date:
                query = query.filter(CostTracking.date <= end_date)
            if agent_type:
                query = query.filter(CostTracking.agent_type == agent_type)
            
            result = query.first()
            
            if not result or result.total_runs is None:
                return {
                    "total_runs": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_tokens": 0,
                    "total_cost": 0.0,
                    "avg_cost_per_run": 0.0
                }
            
            return {
                "total_runs": int(result.total_runs or 0),
                "total_tokens": int(result.total_tokens or 0),
                "input_tokens": int(result.input_tokens or 0),
                "output_tokens": int(result.output_tokens or 0),
                "cache_tokens": int(result.cache_tokens or 0),
                "total_cost": float(result.total_cost or 0.0),
                "avg_cost_per_run": float(result.total_cost / result.total_runs) if result.total_runs > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"Error getting cost summary: {str(e)}")
            return {}


