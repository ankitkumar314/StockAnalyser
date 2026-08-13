import logging

from fastapi import HTTPException

from app.models.technical_analysis import TechnicalAnalysisResponse
from app.services.technical_analysis_service import TechnicalAnalysisService

logger = logging.getLogger(__name__)


class TechnicalAnalysisController:
    def get_technical_analysis(
        self,
        ticker: str,
        period: str = "6mo",
        interval: str = "1d",
        include_chart: bool = True,
        save_chart: bool = True,
    ) -> TechnicalAnalysisResponse:
        try:
            if not ticker or not ticker.strip():
                raise HTTPException(status_code=400, detail="Ticker cannot be empty")

            result = TechnicalAnalysisService.analyze(
                ticker,
                period=period,
                interval=interval,
                include_chart=include_chart,
                save_chart=save_chart,
            )
            if result is None:
                raise HTTPException(status_code=404, detail=f"No historical data found for ticker: {ticker}")

            return TechnicalAnalysisResponse(**result)

        except HTTPException:
            raise
        except ValueError as e:
            # Insufficient history for the requested indicators/period, bad brick size, etc.
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error computing technical analysis for {ticker}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error computing technical analysis: {str(e)}")
