from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class PDFIngestRequest(BaseModel):
    pdf_url: str


class PDFIngestResponse(BaseModel):
    doc_id: str
    message: str
    chunks_count: int


class QueryRequest(BaseModel):
    query: str
    doc_id: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    doc_id: str


class QuestionAnswer(BaseModel):
    question: str
    answer: str
    iteration_count: int


class BatchQuestionRequest(BaseModel):
    doc_id: str


class BatchQuestionResponse(BaseModel):
    doc_id: str
    total_questions: int
    results: List[QuestionAnswer]


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    doc_id: str
    message: str
    created_at: str


class BatchJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    doc_id: str
    progress: Optional[str] = None
    result: Optional[BatchQuestionResponse] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
