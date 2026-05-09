"""DynamoDB utility functions"""

import os
import boto3
from typing import Optional, List, Dict, Any
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'products')
STOCKS_TABLE = os.environ.get('STOCKS_TABLE', 'stocks')

products_table = dynamodb.Table(PRODUCTS_TABLE)
stocks_table = dynamodb.Table(STOCKS_TABLE)


def decimal_to_int(obj):
    """Convert Decimal objects to int/float for JSON serialization"""
    if isinstance(obj, list):
        return [decimal_to_int(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_int(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def get_all_products() -> List[Dict[str, Any]]:
    """Get all products from DynamoDB with their stock counts"""
    try:
        response = products_table.scan()
        products = response.get('Items', [])

        # Join with stocks table to get count
        result = []
        for product in products:
            product_id = product['id']
            stock_response = stocks_table.get_item(Key={'product_id': product_id})
            stock = stock_response.get('Item', {})

            product['count'] = int(stock.get('count', 0))
            result.append(decimal_to_int(product))

        return result
    except Exception as e:
        raise Exception(f"Error fetching products: {str(e)}")


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific product by ID with stock count"""
    try:
        response = products_table.get_item(Key={'id': product_id})
        product = response.get('Item')

        if not product:
            return None

        # Get stock count
        stock_response = stocks_table.get_item(Key={'product_id': product_id})
        stock = stock_response.get('Item', {})
        product['count'] = int(stock.get('count', 0))

        return decimal_to_int(product)
    except Exception as e:
        raise Exception(f"Error fetching product: {str(e)}")


def create_product(product_id: str, title: str, description: str, price: float, count: int) -> Dict[str, Any]:
    """Create a new product with stock in DynamoDB"""
    try:
        # Create product
        products_table.put_item(Item={
            'id': product_id,
            'title': title,
            'description': description,
            'price': price,
        })

        # Create stock
        stocks_table.put_item(Item={
            'product_id': product_id,
            'count': count,
        })

        result = {
            'id': product_id,
            'title': title,
            'description': description,
            'price': float(price),
            'count': int(count),
        }
        return decimal_to_int(result)
    except Exception as e:
        raise Exception(f"Error creating product: {str(e)}")


def update_product(product_id: str, title: Optional[str] = None, description: Optional[str] = None,
                   price: Optional[float] = None, count: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Update a product in DynamoDB"""
    try:
        # First check if product exists
        response = products_table.get_item(Key={'id': product_id})
        product = response.get('Item')

        if not product:
            return None

        # Update product fields if provided
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if price is not None:
            update_data['price'] = price

        # Update product table if there are updates
        if update_data:
            products_table.update_item(
                Key={'id': product_id},
                AttributeUpdates={k: {'Action': 'PUT', 'Value': v} for k, v in update_data.items()}
            )

        # Update stock count if provided
        if count is not None:
            stocks_table.update_item(
                Key={'product_id': product_id},
                AttributeUpdates={'count': {'Action': 'PUT', 'Value': count}}
            )

        # Return updated product with stock
        return get_product_by_id(product_id)
    except Exception as e:
        raise Exception(f"Error updating product: {str(e)}")


def delete_product(product_id: str) -> bool:
    """Delete a product and its stock from DynamoDB"""
    try:
        # Check if product exists
        response = products_table.get_item(Key={'id': product_id})
        product = response.get('Item')

        if not product:
            return False

        # Delete product
        products_table.delete_item(Key={'id': product_id})

        # Delete stock
        stocks_table.delete_item(Key={'product_id': product_id})

        return True
    except Exception as e:
        raise Exception(f"Error deleting product: {str(e)}")

