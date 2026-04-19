from typing import Dict
from fastapi import HTTPException
from app.models.item import Item
from app.services.item_service import ItemService


class ItemController:
    def __init__(self, service: ItemService):
        self.service = service
    
    def create_item(self, item_id: int, item: Item) -> Item:
        try:
            if item_id is None:
                raise HTTPException(status_code=400, detail="Item ID cannot be None")
            if item is None:
                raise HTTPException(status_code=400, detail="Item cannot be None")
            return self.service.create_item(item_id, item)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_items(self) -> Dict[int, Item]:
        try:
            return self.service.get_all_items()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_item_by_id(self, item_id: int) -> Item:
        try:
            if item_id is None:
                raise HTTPException(status_code=400, detail="Item ID cannot be None")
            item = self.service.get_item_by_id(item_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Item not found")
            return item
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_item(self, item_id: int, item: Item) -> Item:
        try:
            if item_id is None:
                raise HTTPException(status_code=400, detail="Item ID cannot be None")
            if item is None:
                raise HTTPException(status_code=400, detail="Item cannot be None")
            updated_item = self.service.update_item(item_id, item)
            if updated_item is None:
                raise HTTPException(status_code=404, detail="Item not found")
            return updated_item
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_item(self, item_id: int) -> Dict[str, str]:
        try:
            if item_id is None:
                raise HTTPException(status_code=400, detail="Item ID cannot be None")
            deleted = self.service.delete_item(item_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Item not found")
            return {"message": "Deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
