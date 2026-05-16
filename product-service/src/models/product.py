"""Product model definition"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Product data model"""
    id: str
    title: str
    description: str
    price: float
    count: Optional[int] = None

    def to_dict(self):
        """Convert product to dictionary"""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
        }
        if self.count is not None:
            result["count"] = self.count
        return result
