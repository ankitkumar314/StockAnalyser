from fastapi import APIRouter
from app.models.portfolio_analysis import PortfolioAnalysisResponse
from app.controllers.portfolio_analysis_controller import PortfolioAnalysisController

router = APIRouter(prefix="/portfolio", tags=["portfolio-analysis"])

portfolio_analysis_controller = PortfolioAnalysisController()


@router.get("/analysis", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(generate_missing: bool = False, max_generate: int = 2):
    """
    Analyse the Kite portfolio: cached concall summaries + (dummy) technical
    indicators combined into an LLM short view per stock and an overall view.
    Set generate_missing=true to scrape+ingest+summarise up to max_generate
    stocks that have no cached concall summary (slow - minutes per stock).
    """
    return portfolio_analysis_controller.analyze(generate_missing, max_generate)
