from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import stock_router, scrape_router, agent_router
from app.routes.transcript_routes import router as transcript_router
from app.routes.market_data_routes import router as market_data_router
from app.routes.portfolio_routes import router as portfolio_router
from app.routes.portfolio_analysis_routes import router as portfolio_analysis_router
from app.routes.kite_redirect_routes import router as kite_redirect_router
from app.routes.technical_analysis_routes import router as technical_analysis_router
from app.routes.stock_report_routes import router as stock_report_router
from app.database.connection import DatabaseConnection
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Analyser API", version="1.0.0")

# static/ is gitignored (generated output), so it may not exist on a fresh clone;
# StaticFiles requires the directory to exist at mount time.
Path("static").mkdir(exist_ok=True)

# Serves saved chart PNGs (and other files under static/) directly over HTTP, e.g.
# http://localhost:8000/static/technical_charts/AAPL_technical_chart.png
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    if DatabaseConnection.is_enabled():
        try:
            DatabaseConnection.initialize()
            logger.info("✅ Database enabled and initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.warning("⚠️  Falling back to in-memory storage")
    else:
        logger.info("⚠️  DATABASE_URL not set, using in-memory storage")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    DatabaseConnection.close_all()
    logger.info("Database connections closed")

app.include_router(stock_router)    
app.include_router(scrape_router)
app.include_router(agent_router)
app.include_router(transcript_router)
app.include_router(market_data_router)
app.include_router(portfolio_router)
app.include_router(portfolio_analysis_router)
app.include_router(kite_redirect_router)
app.include_router(technical_analysis_router)
app.include_router(stock_report_router)