from fastapi import APIRouter, Depends
from typing import Dict
from app.models.stock import Stock
from app.controllers.stock_controller import StockController
from app.services.stock_service import StockService
from app.repositories.stock_repository import StockRepository

router = APIRouter(prefix="/stocks", tags=["stocks"])

stock_repository = StockRepository()
stock_service = StockService(stock_repository)
stock_controller = StockController(stock_service)


@router.post("/{stock_id}")
def create_stock(stock_id: int, stock: Stock):
    return stock_controller.create_stock(stock_id, stock)


@router.get("")
def get_stocks() -> Dict[int, Stock]:
    return stock_controller.get_all_stocks()


@router.get("/{stock_id}")
def get_stock(stock_id: int):
    return stock_controller.get_stock_by_id(stock_id)


@router.put("/{stock_id}")
def update_stock(stock_id: int, stock: Stock):
    return stock_controller.update_stock(stock_id, stock)


@router.delete("/{stock_id}")
def delete_stock(stock_id: int):
    return stock_controller.delete_stock(stock_id)
