from fastapi import APIRouter, BackgroundTasks
from typing import List
from app.models.transcript import (
    TranscriptCreateRequest,
    TranscriptResponse,
    SummaryResponse,
    SummaryGenerationRequest,
    BatchProcessRequest,
    BatchProcessResponse
)
from app.controllers.transcript_controller import TranscriptController

router = APIRouter(prefix="/transcripts", tags=["transcripts"])
transcript_controller = TranscriptController()


@router.post("", response_model=TranscriptResponse)
def create_transcript(request: TranscriptCreateRequest):
    """
    Create a new conference call transcript.
    
    - Checks for existing transcript for the same quarter
    - If exists, returns existing record
    - If not, creates new record with 'pending' status
    """
    return transcript_controller.create_transcript(request)


@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(transcript_id: int):
    """Get transcript by ID."""
    return transcript_controller.get_transcript_by_id(transcript_id)


@router.get("/ticker/{ticker}", response_model=List[TranscriptResponse])
def get_transcripts_by_ticker(ticker: str, limit: int = 10):
    """Get all transcripts for a ticker."""
    return transcript_controller.get_transcripts_by_ticker(ticker, limit)


# @router.post("/generate-summary")
# def generate_summary(request: SummaryGenerationRequest, background_tasks: BackgroundTasks):
#     """
#     Generate summary for a transcript using RAG system.
    
#     - Runs in background
#     - Ingests PDF if doc_id not present
#     - Queries RAG system with predefined questions
#     - Creates structured summary
#     - Updates transcript with summary_id and status
#     """
#     return transcript_controller.generate_summary(request, background_tasks)


# @router.get("/summary/{ticker}", response_model=SummaryResponse)
# def get_summary_by_ticker(ticker: str):
#     """Get latest summary for a ticker."""
#     return transcript_controller.get_summary_by_ticker(ticker)


# @router.post("/batch-process", response_model=BatchProcessResponse)
# def process_pending_transcripts(
#     request: BatchProcessRequest,
#     background_tasks: BackgroundTasks
# ):
#     """
#     Process pending transcripts in batch.
    
#     - Finds all transcripts with status='pending'
#     - Generates summaries for each in background
#     - Returns immediately with processing status
#     """
#     return transcript_controller.process_pending_transcripts(request, background_tasks)
