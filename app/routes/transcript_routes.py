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

