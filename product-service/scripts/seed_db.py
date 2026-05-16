"""Script to seed DynamoDB with test data"""

import os
import sys

import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Get table names from environment or use defaults
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'products')
STOCKS_TABLE = os.environ.get('STOCKS_TABLE', 'stocks')

# Test data
PRODUCTS_DATA = [
    {
        'id': 'id1',
        'title': 'Oranges',
        'description': 'Oranges Product Description',
        'price': 24,
    },
    {
        'id': 'id2',
        'title': 'Bananas',
        'description': 'Bananas Product Description',
        'price': 15,
    },
    {
        'id': 'id3',
        'title': 'Apples',
        'description': 'Apples Product Description',
        'price': 23,
    },
    {
        'id': 'id4',
        'title': 'Grapes',
        'description': 'Grapes Product Description',
        'price': 15,
    },
    {
        'id': 'id5',
        'title': 'Pineapples',
        'description': 'Pineapples Product Description',
        'price': 23,
    },
    {
        'id': 'id6',
        'title': 'Mangoes',
        'description': 'Mangoes Product Description',
        'price': 15,
    },
]

STOCKS_DATA = [
    {'product_id': 'id1', 'count': 1},
    {'product_id': 'id2', 'count': 2},
    {'product_id': 'id3', 'count': 3},
    {'product_id': 'id4', 'count': 4},
    {'product_id': 'id5', 'count': 5},
    {'product_id': 'id6', 'count': 6},
]


def seed_products_table():
    """Seed products table"""
    try:
        table = dynamodb.Table(PRODUCTS_TABLE)
        print(f"Seeding {PRODUCTS_TABLE} table...")

        for product in PRODUCTS_DATA:
            table.put_item(Item=product)
            print(f"  ✓ Created product: {product['title']} (ID: {product['id']})")

        print(f"✓ {PRODUCTS_TABLE} table seeded successfully!")
    except Exception as e:
        print(f"✗ Error seeding {PRODUCTS_TABLE}: {str(e)}")
        raise


def seed_stocks_table():
    """Seed stocks table"""
    try:
        table = dynamodb.Table(STOCKS_TABLE)
        print(f"Seeding {STOCKS_TABLE} table...")

        for stock in STOCKS_DATA:
            table.put_item(Item=stock)
            print(f"  ✓ Created stock for product: {stock['product_id']} (count: {stock['count']})")

        print(f"✓ {STOCKS_TABLE} table seeded successfully!")
    except Exception as e:
        print(f"✗ Error seeding {STOCKS_TABLE}: {str(e)}")
        raise


def main():
    """Main seed function"""
    print(f"Starting seed script...")
    print(f"Using tables: {PRODUCTS_TABLE}, {STOCKS_TABLE}")
    print(f"AWS Region: {os.environ.get('AWS_REGION', 'default')}")
    print()

    try:
        seed_products_table()
        seed_stocks_table()
        print()
        print("✓ Seeding completed successfully!")
    except Exception as e:
        print()
        print(f"✗ Seeding failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
