import logging
from typing import Dict, List, Optional, Tuple
from datetime import date

from app.database.connection import DatabaseConnection
from app.database.stock_repository import StockRepository
from app.database.summary_repository import SummaryRepository
from app.services.kite_service import KiteService
from app.services.technicalIndicator_service import TechnicalIndicatorService
from app.services.transcript_service import TranscriptService
from app.agenticAI.llm_Model import LLMFactory

logger = logging.getLogger(__name__)

ANSWER_TRUNCATE_CHARS = 2500


def pick_latest_transcript_url(concalls: Dict) -> Optional[str]:
    """
    Pick the newest concall transcript URL from ScraperService's concalls dict
    ({date: [{ppt/transcript/rec: url}]}). Screener lists newest first, and dict
    insertion order preserves that, so the first transcript found is the latest.
    """
    for _, docs in (concalls or {}).items():
        for doc in docs:
            if doc.get("transcript"):
                return doc["transcript"]
    return None


class PortfolioAnalysisService:
    """
    Combines the Kite portfolio, cached/generated concall summaries and technical
    indicators (dummy for now) into an LLM-written short view per stock plus an
    overall portfolio view.
    """

    def __init__(self):
        self.kite_service = KiteService()
        self._agent_controller = None
        self._scrape_controller = None

    # AgentController construction loads the embedding model, and WebScrapeController
    # pulls in the whole stock controller chain — only pay for them if a summary
    # actually needs generating.
    def _get_agent_controller(self):
        if self._agent_controller is None:
            from app.controllers.agent_controller import AgentController
            self._agent_controller = AgentController()
        return self._agent_controller

    def _get_scrape_controller(self):
        if self._scrape_controller is None:
            from app.controllers.webScrape_controller import WebScrapeController
            self._scrape_controller = WebScrapeController()
        return self._scrape_controller

    @staticmethod
    def _get_cached_summary(session, stock_id: int) -> Optional[Tuple[List[str], Optional[date]]]:
        summaries = SummaryRepository.get_by_stock_id(session, stock_id, limit=1)
        if not summaries:
            return None
        summary = summaries[0]
        answers = [a for a in [summary.answer1, summary.answer2, summary.answer3,
                               summary.answer4, summary.answer5] if a]
        if not answers:
            return None
        return answers, summary.quarter_date

    def _generate_summary(self, ticker: str) -> Optional[List[str]]:
        """Scrape latest concall transcript URL, ingest it, run batch-evaluate.
        batch_evaluate persists the answers to concall_summary via SummaryCacheService."""
        from app.models.agent import PDFIngestRequest, BatchQuestionRequest

        scrape_result = self._get_scrape_controller().scrape_for_financial_data(ticker)
        transcript_url = pick_latest_transcript_url(scrape_result.get("concalls"))
        if not transcript_url:
            logger.warning(f"No concall transcript found in scrape data for {ticker}")
            return None

        agent = self._get_agent_controller()
        ingest = agent.ingest_pdf(PDFIngestRequest(pdf_url=transcript_url, ticker=ticker))
        batch = agent.batch_evaluate(BatchQuestionRequest(
            doc_id=ingest.doc_id,
            ticker=ticker,
            quarter_date=TranscriptService._calculate_quarter_date(),
            concall_url=transcript_url,
        ))
        return [r.answer for r in batch.results]

    @staticmethod
    def _stock_short_view(llm, holding: Dict, indicators: Dict,
                          answers: Optional[List[str]]) -> Optional[str]:
        concall_section = "No concall summary available for this stock."
        if answers:
            concall_section = "\n\n".join(a[:ANSWER_TRUNCATE_CHARS] for a in answers)

        prompt = f"""You are an equity analyst reviewing one holding in a personal portfolio.

Stock: {holding['company_name']} ({holding['symbol']})
Position: {holding['quantity']} shares, current value {holding['current_value']:.2f}, P&L {holding['profit_loss']:.2f} ({holding['profit_loss_percent']:.2f}%), {holding['portfolio_concentration']:.2f}% of portfolio.

Technical indicators: MACD {indicators.get('macd')} vs signal {indicators.get('macd_signal')} ({indicators.get('macd_trend')}), 50-DMA {indicators.get('dma_50')}, 200-DMA {indicators.get('dma_200')}, crossover: {indicators.get('dma_crossover')}, RSI-14 {indicators.get('rsi_14')}, {indicators.get('percent_from_52w_high')}% from 52-week high.

Latest earnings call summary:
{concall_section}

Write a concise 3-4 sentence view of this holding covering business momentum from the call, the technical setup, and one thing to watch. Plain text, no headers, no disclaimers."""

        try:
            result = llm.invoke(prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"LLM short view failed for {holding['symbol']}: {str(e)}")
            return None

    @staticmethod
    def _overall_view(llm, totals: Dict, stock_views: List[Dict]) -> Optional[str]:
        if not stock_views:
            return None

        lines = []
        for sv in stock_views:
            view = sv["short_view"] or "(no view generated)"
            lines.append(
                f"- {sv['symbol']} ({sv['portfolio_concentration']:.1f}% of portfolio, "
                f"P&L {sv['profit_loss_percent']:.1f}%): {view}"
            )

        prompt = f"""You are an equity analyst reviewing an entire personal portfolio.

Portfolio value: {totals['portfolio_value']:.2f}, total P&L: {totals['total_pnl']:.2f} ({totals['total_pnl_percent']:.2f}%).

Per-stock views:
{chr(10).join(lines)}

Write a short overall portfolio view (5-7 sentences): overall health, concentration risks, the strongest and weakest holdings, and what to watch next quarter. Plain text, no headers, no disclaimers."""

        try:
            result = llm.invoke(prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"LLM overall view failed: {str(e)}")
            return None

    def analyze(self, generate_missing: bool = False, max_generate: int = 2) -> Dict:
        portfolio = self.kite_service.get_portfolio()

        llm = LLMFactory.get_deepseek(metadata={"endpoint": "portfolio_analysis"})

        db_enabled = DatabaseConnection.is_enabled()
        session = DatabaseConnection.get_session() if db_enabled else None

        stocks: List[Dict] = []
        not_tracked: List[str] = []
        missing_summaries: List[str] = []
        generated_count = 0

        try:
            for holding in portfolio["holdings"]:
                symbol = holding["symbol"]

                stock = StockRepository.get_by_ticker(session, symbol) if session else None
                if stock is None:
                    not_tracked.append(symbol)
                    continue

                cached = self._get_cached_summary(session, stock.id)
                answers = cached[0] if cached else None
                quarter_date = cached[1] if cached else None
                generated_now = False

                if answers is None and generate_missing and generated_count < max_generate:
                    try:
                        answers = self._generate_summary(symbol)
                        if answers:
                            generated_now = True
                            generated_count += 1
                            quarter_date = TranscriptService._calculate_quarter_date()
                    except Exception as e:
                        logger.error(f"Summary generation failed for {symbol}: {str(e)}")

                if answers is None:
                    missing_summaries.append(symbol)

                indicators = TechnicalIndicatorService.get_indicators(symbol)
                short_view = self._stock_short_view(llm, holding, indicators, answers)

                stocks.append({
                    "symbol": symbol,
                    "company_name": holding["company_name"],
                    "quantity": holding["quantity"],
                    "current_value": holding["current_value"],
                    "profit_loss": holding["profit_loss"],
                    "profit_loss_percent": holding["profit_loss_percent"],
                    "portfolio_concentration": holding["portfolio_concentration"],
                    "indicators": indicators,
                    "concall_available": answers is not None,
                    "concall_quarter_date": quarter_date,
                    "summary_generated_now": generated_now,
                    "short_view": short_view,
                })
        finally:
            if session is not None:
                session.close()

        totals = {
            "portfolio_value": portfolio["portfolio_value"],
            "total_investment": portfolio["total_investment"],
            "total_pnl": portfolio["total_pnl"],
            "total_pnl_percent": portfolio["total_pnl_percent"],
        }

        overall_view = self._overall_view(llm, totals, stocks)

        return {
            **totals,
            "overall_view": overall_view,
            "stocks": stocks,
            "not_tracked": not_tracked,
            "missing_summaries": missing_summaries,
        }
