from typing import Dict, Optional
from app.models.item import Item


class ItemRepository:
    def __init__(self):
        self._items: Dict[int, Item] = {}
    
    def create(self, item_id: int, item: Item) -> Item:
        try:
            if item_id is None:
                raise ValueError("Item ID cannot be None")
            if item_id in self._items:
                raise ValueError("Item already exists")
            self._items[item_id] = item
            return item
        except Exception as e:
            raise e
    
    def get_all(self) -> Dict[int, Item]:
        try:
            return self._items
        except Exception as e:
            raise e
    
    def get_by_id(self, item_id: int) -> Optional[Item]:
        try:
            if item_id is None:
                return None
            return self._items.get(item_id)
        except Exception as e:
            raise e
    
    def update(self, item_id: int, item: Item) -> Optional[Item]:
        try:
            if item_id is None or item_id not in self._items:
                return None
            self._items[item_id] = item
            return item
        except Exception as e:
            raise e
    
    def delete(self, item_id: int) -> bool:
        try:
            if item_id is None or item_id not in self._items:
                return False
            del self._items[item_id]
            return True
        except Exception as e:
            raise e
