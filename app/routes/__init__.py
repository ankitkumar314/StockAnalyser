from .stock_routes import router as stock_router
from .webScrape_routes import router as scrape_router
from .agent_routes import router as agent_router

__all__ = ["stock_router", "scrape_router", "agent_router"]
