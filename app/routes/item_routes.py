from fastapi import APIRouter, Depends
from typing import Dict
from app.models.item import Item
from app.controllers.item_controller import ItemController
from app.services.item_service import ItemService
from app.repositories.item_repository import ItemRepository

router = APIRouter(prefix="/items", tags=["items"])

item_repository = ItemRepository()
item_service = ItemService(item_repository)
item_controller = ItemController(item_service)


@router.post("/{item_id}")
def create_item(item_id: int, item: Item):
    return item_controller.create_item(item_id, item)


@router.get("")
def get_items() -> Dict[int, Item]:
    return item_controller.get_all_items()


@router.get("/{item_id}")
def get_item(item_id: int):
    return item_controller.get_item_by_id(item_id)


@router.put("/{item_id}")
def update_item(item_id: int, item: Item):
    return item_controller.update_item(item_id, item)


@router.delete("/{item_id}")
def delete_item(item_id: int):
    return item_controller.delete_item(item_id)
