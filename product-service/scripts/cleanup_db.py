#!/usr/bin/env python3
"""
Cleanup script to remove test data from DynamoDB
Runs after tests to reset the database to a clean state
"""

import boto3
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')

# Table names
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'products')
STOCKS_TABLE = os.environ.get('STOCKS_TABLE', 'stocks')


def cleanup_db():
    """Delete all items from DynamoDB tables"""
    try:
        products_table = dynamodb.Table(PRODUCTS_TABLE)
        stocks_table = dynamodb.Table(STOCKS_TABLE)

        print("Starting database cleanup...")
        print(f"Using tables: {PRODUCTS_TABLE}, {STOCKS_TABLE}")

        # Delete all products
        print("\nCleaning products table...")
        response = products_table.scan()
        items = response.get('Items', [])

        deleted_count = 0
        for item in items:
            try:
                products_table.delete_item(Key={'id': item['id']})
                deleted_count += 1
            except Exception as e:
                print(f"  Error deleting product {item['id']}: {e}")

        print(f"  ✓ Deleted {deleted_count} products")

        # Delete all stocks
        print("\nCleaning stocks table...")
        response = stocks_table.scan()
        items = response.get('Items', [])

        deleted_count = 0
        for item in items:
            try:
                stocks_table.delete_item(Key={'product_id': item['product_id']})
                deleted_count += 1
            except Exception as e:
                print(f"  Error deleting stock {item['product_id']}: {e}")

        print(f"  ✓ Deleted {deleted_count} stock records")

        print("\n✓ Database cleanup completed successfully!")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        raise


if __name__ == '__main__':
    cleanup_db()

