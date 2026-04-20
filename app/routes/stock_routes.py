from fastapi import APIRouter, Depends, Query
from typing import Dict
from app.models.stock import Stock, StockListResponse, StockCreateRequest, StockUpdateRequest, StockResponse
from app.controllers.stock_controller import StockController

router = APIRouter(prefix="/stocks", tags=["stocks"])

stock_controller = StockController()


@router.post("/addStock", response_model=StockResponse, status_code=201)
def create_stock(request: StockCreateRequest):
    return stock_controller.create_stock_db(request)


@router.get("")
def get_stocks() -> StockListResponse:
    return stock_controller.get_all_stocks()


@router.get("/{ticker}", response_model=StockResponse)
def get_stock(ticker: str):
    return stock_controller.get_stock_by_ticker(ticker)


@router.put("/{stock_id}", response_model=StockResponse)
def update_stock(stock_id: int, request: StockUpdateRequest):
    return stock_controller.update_stock_db(stock_id, request)
