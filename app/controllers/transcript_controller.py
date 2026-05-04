from typing import List
from fastapi import HTTPException, BackgroundTasks
from app.models.transcript import (
    TranscriptCreateRequest,
    TranscriptResponse,
    SummaryResponse,
    SummaryGenerationRequest,
    BatchProcessRequest,
    BatchProcessResponse
)
from app.services.transcript_service import TranscriptService
from app.services.summary_generation_service import SummaryGenerationService
import logging

logger = logging.getLogger(__name__)


class TranscriptController:
    """Controller for conference call transcript operations."""
    
    def __init__(self):
        self.summary_service = SummaryGenerationService()
    
    def create_transcript(self, request: TranscriptCreateRequest) -> TranscriptResponse:
        """Create a new transcript record."""
        try:
            transcript = TranscriptService.create_transcript(
                ticker=request.ticker,
                transcript_url=request.transcript_url,
                doc_id=request.doc_id,
                quarter_date=request.quarter_date
            )
            
            if not transcript:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create transcript"
                )
            
            return TranscriptResponse(
                id=transcript.id,
                stock_id=transcript.stock_id,
                quarter_date=transcript.quarter_date,
                transcript_url=transcript.transcript_url,
                status=transcript.status,
                summary_id=transcript.summary_id,
                created_at=transcript.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating transcript: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_transcript_by_id(self, transcript_id: int) -> TranscriptResponse:
        """Get transcript by ID."""
        try:
            transcript = TranscriptService.get_transcript_by_id(transcript_id)
            
            if not transcript:
                raise HTTPException(
                    status_code=404,
                    detail=f"Transcript not found: {transcript_id}"
                )
            
            return TranscriptResponse(
                id=transcript.id,
                stock_id=transcript.stock_id,
                quarter_date=transcript.quarter_date,
                transcript_url=transcript.transcript_url,
                status=transcript.status,
                summary_id=transcript.summary_id,
                created_at=transcript.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_transcripts_by_ticker(self, ticker: str, limit: int = 10) -> List[TranscriptResponse]:
        """Get all transcripts for a ticker."""
        try:
            transcripts = TranscriptService.get_transcripts_by_ticker(ticker, limit)
            
            return [
                TranscriptResponse(
                    id=t.id,
                    stock_id=t.stock_id,
                    quarter_date=t.quarter_date,
                    transcript_url=t.transcript_url,
                    status=t.status,
                    summary_id=t.summary_id,
                    created_at=t.created_at
                )
                for t in transcripts
            ]
            
        except Exception as e:
            logger.error(f"Error getting transcripts: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def generate_summary(
        self,
        request: SummaryGenerationRequest,
        background_tasks: BackgroundTasks
    ) -> dict:
        """Generate summary for a transcript in background."""
        try:
            transcript = TranscriptService.get_transcript_by_id(request.transcript_id)
            
            if not transcript:
                raise HTTPException(
                    status_code=404,
                    detail=f"Transcript not found: {request.transcript_id}"
                )
            
            if transcript.status == 'completed':
                return {
                    "message": "Summary already exists",
                    "transcript_id": request.transcript_id,
                    "summary_id": transcript.summary_id,
                    "status": "completed"
                }
            
            if transcript.status == 'processing':
                return {
                    "message": "Summary generation already in progress",
                    "transcript_id": request.transcript_id,
                    "status": "processing"
                }
            
            # Add to background tasks
            background_tasks.add_task(
                self.summary_service.generate_summary_sync,
                request.transcript_id
            )
            
            return {
                "message": "Summary generation started",
                "transcript_id": request.transcript_id,
                "status": "processing"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting summary generation: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_summary_by_ticker(self, ticker: str) -> SummaryResponse:
        """Get latest summary for a ticker."""
        try:
            summary = TranscriptService.get_summary_by_ticker(ticker)
            
            if not summary:
                raise HTTPException(
                    status_code=404,
                    detail=f"No summary found for ticker: {ticker}"
                )
            
            return SummaryResponse(
                id=summary.id,
                stockid=summary.stockid,
                quarter_date=summary.quarter_date,
                answer1=summary.answer1,
                answer2=summary.answer2,
                answer3=summary.answer3,
                answer4=summary.answer4,
                answer5=summary.answer5,
                prev_concall_hisotry=summary.prev_concall_hisotry,
                concall_url=summary.concall_url,
                document_id=summary.document_id,
                created_at=summary.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def process_pending_transcripts(
        self,
        request: BatchProcessRequest,
        background_tasks: BackgroundTasks
    ) -> BatchProcessResponse:
        """Process pending transcripts in background."""
        try:
            # Add to background tasks
            background_tasks.add_task(
                self.summary_service.process_pending_transcripts,
                request.max_count
            )
            
            return BatchProcessResponse(
                processed=0,
                success=0,
                failed=0,
                message=f"Batch processing started for up to {request.max_count} transcripts"
            )
            
        except Exception as e:
            logger.error(f"Error starting batch processing: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
