from pydantic import BaseModel
from typing import Optional, List


class PDFIngestRequest(BaseModel):
    """Request model for creating a transcript."""
    pdf_url: str
    ticker: str


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
