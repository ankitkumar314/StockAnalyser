from fastapi import FastAPI
from app.routes import item_router, stock_router, scrape_router, agent_router
from app.routes.transcript_routes import router as transcript_router
from app.database.connection import DatabaseConnection
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Stock Analyser API", version="1.0.0")

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

app.include_router(item_router)
app.include_router(stock_router)    
app.include_router(scrape_router)
app.include_router(agent_router)
app.include_router(transcript_router)