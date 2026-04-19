from fastapi import APIRouter
from app.models.agent import PDFIngestRequest, PDFIngestResponse, QueryRequest, QueryResponse, BatchQuestionRequest, BatchQuestionResponse
from app.controllers.agent_controller import AgentController

router = APIRouter(prefix="/agent", tags=["agent"])

agent_controller = AgentController()


@router.post("/ingest-pdf")
def ingest_pdf(request: PDFIngestRequest) -> PDFIngestResponse:
    return agent_controller.ingest_pdf(request)

@router.post("/query")
def query(request: QueryRequest) -> QueryResponse:
    return agent_controller.query(request)

@router.post("/batch-evaluate")
def batch_evaluate(request: BatchQuestionRequest) -> BatchQuestionResponse:
    return agent_controller.batch_evaluate(request)

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


