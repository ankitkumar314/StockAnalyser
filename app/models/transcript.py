from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class TranscriptCreateRequest(BaseModel):
    """Request model for creating a transcript."""
    ticker: str
    transcript_url: Optional[str] = None
    quarter_date: Optional[date] = None


class TranscriptResponse(BaseModel):
    """Response model for transcript."""
    id: int
    stock_id: int
    quarter_date: Optional[date] = None
    transcript_url: Optional[str] = None
    status: Optional[str] = None
    summary_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    """Response model for concall summary."""
    id: int
    stockid: int
    quarter_date: Optional[date] = None
    answer1: Optional[str] = None
    answer2: Optional[str] = None
    answer3: Optional[str] = None
    answer4: Optional[str] = None
    answer5: Optional[str] = None
    prev_concall_hisotry: Optional[str] = None
    concall_url: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SummaryGenerationRequest(BaseModel):
    """Request model for generating summary."""
    transcript_id: int


class BatchProcessRequest(BaseModel):
    """Request model for batch processing pending transcripts."""
    max_count: int = 10


class BatchProcessResponse(BaseModel):
    """Response model for batch processing."""
    processed: int
    success: int
    failed: int
    message: str
