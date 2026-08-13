from fastapi import APIRouter, Query

from app.controllers.technical_analysis_controller import TechnicalAnalysisController
from app.models.technical_analysis import TechnicalAnalysisResponse

router = APIRouter(prefix="/technical-analysis", tags=["technical-analysis"])

technical_analysis_controller = TechnicalAnalysisController()


@router.get("/{ticker}", response_model=TechnicalAnalysisResponse)
def get_technical_analysis(
    ticker: str,
    period: str = "6mo",
    interval: str = "1d",
    include_chart: bool = Query(True, description="Include base64-encoded PNG chart(s) in the response"),
    save_chart: bool = Query(True, description="Save chart PNG(s) under static/technical_charts/"),
):
    return technical_analysis_controller.get_technical_analysis(
        ticker,
        period=period,
        interval=interval,
        include_chart=include_chart,
        save_chart=save_chart,
    )
