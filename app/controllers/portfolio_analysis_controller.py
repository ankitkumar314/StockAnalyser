from fastapi import HTTPException
from app.models.portfolio_analysis import PortfolioAnalysisResponse, StockAnalysis, TechnicalIndicators
from app.services.portfolio_analysis_service import PortfolioAnalysisService
from app.services.kite_service import KiteTokenExpiredError, KiteNetworkError, KiteAPIError
import logging

logger = logging.getLogger(__name__)


class PortfolioAnalysisController:
    def __init__(self):
        self.analysis_service = PortfolioAnalysisService()

    def analyze(self, generate_missing: bool = False, max_generate: int = 2) -> PortfolioAnalysisResponse:
        try:
            if max_generate < 0:
                raise HTTPException(status_code=400, detail="max_generate cannot be negative")

            data = self.analysis_service.analyze(
                generate_missing=generate_missing,
                max_generate=max_generate
            )

            return PortfolioAnalysisResponse(
                portfolio_value=data["portfolio_value"],
                total_investment=data["total_investment"],
                total_pnl=data["total_pnl"],
                total_pnl_percent=data["total_pnl_percent"],
                overall_view=data["overall_view"],
                stocks=[
                    StockAnalysis(
                        **{**stock, "indicators": TechnicalIndicators(**stock["indicators"])}
                    )
                    for stock in data["stocks"]
                ],
                not_tracked=data["not_tracked"],
                missing_summaries=data["missing_summaries"],
            )

        except KiteTokenExpiredError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except KiteNetworkError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except KiteAPIError as e:
            raise HTTPException(status_code=502, detail=f"Zerodha API failure: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze portfolio")
