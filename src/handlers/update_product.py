"""Lambda handler for PUT /products/{productId} endpoint"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import update_product


def validate_product_update(data):
    """Validate product update data"""
    errors = []

    # At least one field must be provided
    if not any(k in data for k in ['title', 'description', 'price', 'count']):
        errors.append('At least one field (title, description, price, or count) must be provided')

    if 'title' in data and not isinstance(data['title'], str):
        errors.append('title must be a string')

    if 'description' in data and not isinstance(data['description'], str):
        errors.append('description must be a string')

    if 'price' in data:
        if not isinstance(data['price'], (int, float)) or data['price'] < 0:
            errors.append('price must be a non-negative number')

    if 'count' in data:
        if not isinstance(data['count'], int) or data['count'] < 0:
            errors.append('count must be a non-negative integer')

    return errors


def lambda_handler(event, context):
    """
    Update a product in DynamoDB.

    Args:
        event: Lambda event with pathParameters containing productId
        context: Lambda context

    Returns:
        API Gateway response with updated product or error
    """
    print(f"Received request: {json.dumps(event)}")

    try:
        # Get productId from path parameters
        product_id = event.get("pathParameters", {}).get("productId")
        print(f"Updating product with ID: {product_id}")

        if not product_id:
            print("Product ID is required")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Product ID is required"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        # Parse request body
        body = json.loads(event.get('body', '{}'))
        print(f"Update data: {json.dumps(body)}")

        # Validate input
        validation_errors = validate_product_update(body)
        if validation_errors:
            print(f"Validation errors: {validation_errors}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid update data", "details": validation_errors}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        # Update product
        product = update_product(
            product_id=product_id,
            title=body.get('title'),
            description=body.get('description'),
            price=body.get('price'),
            count=body.get('count')
        )

        if not product:
            print(f"Product not found: {product_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Product not found"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        print(f"Product updated: {json.dumps(product)}")
        return {
            "statusCode": 200,
            "body": json.dumps(product),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON format"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
