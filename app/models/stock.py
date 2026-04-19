from pydantic import BaseModel


class Stock(BaseModel):
    symbol: str
    quantity: int
    price: float
