"""Mock product data"""

from models.product import Product

PRODUCTS = [
    Product(
        id="id1",
        title="Oranges",
        description="Oranges Product Description",
        price=24,
        count=1,
    ),
    Product(
        id="id2",
        title="Bananas",
        description="Bananas Product Description",
        price=15,
        count=2,
    ),
    Product(
        id="id3",
        title="Apples",
        description="Apples Product Description",
        price=23,
        count=3,
    ),
    Product(
        id="id4",
        title="Grapes",
        description="Grapes Product Description",
        price=15,
        count=4,
    ),
    Product(
        id="id5",
        title="Pineapples",
        description="Pineapples Product Description",
        price=23,
        count=5,
    ),
    Product(
        id="id6",
        title="Mangoes",
        description="Mangoes Product Description",
        price=15,
        count=6,
    ),
]
