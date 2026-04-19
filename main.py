from fastapi import FastAPI
from app.routes import item_router, stock_router, scrape_router, agent_router

app = FastAPI()

app.include_router(item_router)
app.include_router(stock_router)    
app.include_router(scrape_router)
app.include_router(agent_router)