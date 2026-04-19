from typing import Dict, Optional
from app.models.item import Item
from app.repositories.item_repository import ItemRepository


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository
    
    def create_item(self, item_id: int, item: Item) -> Item:
        try:
            if item_id is None:
                raise ValueError("Item ID cannot be None")
            if item is None:
                raise ValueError("Item cannot be None")
            return self.repository.create(item_id, item)
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error creating item: {str(e)}")
    
    def get_all_items(self) -> Dict[int, Item]:
        try:
            return self.repository.get_all()
        except Exception as e:
            raise Exception(f"Error retrieving items: {str(e)}")
    
    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        try:
            if item_id is None:
                return None
            return self.repository.get_by_id(item_id)
        except Exception as e:
            raise Exception(f"Error retrieving item: {str(e)}")
    
    def update_item(self, item_id: int, item: Item) -> Optional[Item]:
        try:
            if item_id is None:
                raise ValueError("Item ID cannot be None")
            if item is None:
                raise ValueError("Item cannot be None")
            return self.repository.update(item_id, item)
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error updating item: {str(e)}")
    
    def delete_item(self, item_id: int) -> bool:
        try:
            if item_id is None:
                return False
            return self.repository.delete(item_id)
        except Exception as e:
            raise Exception(f"Error deleting item: {str(e)}")
