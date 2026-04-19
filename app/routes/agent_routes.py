from fastapi import APIRouter
from app.models.agent import (
    PDFIngestRequest, PDFIngestResponse, QueryRequest, QueryResponse, 
    BatchQuestionRequest, BatchQuestionResponse,
    BatchJobResponse, BatchJobStatusResponse
)
from app.controllers.agent_controller import AgentController

router = APIRouter(prefix="/agent", tags=["agent"])

agent_controller = AgentController()


@router.post("/ingest-pdf")
def ingest_pdf(request: PDFIngestRequest) -> PDFIngestResponse:
    return agent_controller.ingest_pdf(request)

@router.post("/query")
def query(request: QueryRequest) -> QueryResponse:
    return agent_controller.query(request)

@router.post("/batch-evaluate-async")
def batch_evaluate_async(request: BatchQuestionRequest) -> BatchJobResponse:
    """
    Start batch evaluation as a background job.
    Returns immediately with job_id for status tracking.
    
    The job will process 6 comprehensive questions about the earnings call:
    - Business performance highlights
    - Management commentary insights
    - Future outlook and guidance
    - Risks and challenges
    - Strategic announcements
    - Supporting evidence
    
    Returns:
        BatchJobResponse with job_id to track progress
    """
    return agent_controller.batch_evaluate_async(request)

@router.get("/batch-job/{job_id}")
def get_batch_job_status(job_id: str) -> BatchJobStatusResponse:
    """
    Get the status of a batch evaluation job.
    
    Args:
        job_id: The job ID returned from batch-evaluate-async
        
    Returns:
        BatchJobStatusResponse with current status, progress, and results (if completed)
    """
    return agent_controller.get_batch_job_status(job_id)

@router.get("/batch-jobs")
def list_batch_jobs():
    """
    List all batch evaluation jobs.
    
    Returns:
        List of all jobs with their status and metadata
    """
    return agent_controller.list_batch_jobs()

@router.get("/graph-visualization")
def get_graph_visualization():
    return agent_controller.get_graph_visualization()

@router.get("/cost-summary")
def get_cost_summary():
    """
    Get summary of LLM costs and token usage.
    
    Returns:
        Cost and usage statistics including:
        - Total runs
        - Total tokens (input/output/cache)
        - Total cost in USD
        - Average cost per run
        - Recent runs
    """
    return agent_controller.get_cost_summary()

@router.get("/cost-predict")
def predict_cost(query: str, doc_id: str):
    """
    Predict cost for a query before execution.
    
    Args:
        query: The query string
        doc_id: Document ID
        
    Returns:
        Predicted cost breakdown by agent
    """
    return agent_controller.predict_query_cost(query, doc_id)

@router.post("/cost-reset")
def reset_cost_tracking():
    """
    Reset cost tracking data.
    
    Returns:
        Success message
    """
    return agent_controller.reset_cost_tracking()


