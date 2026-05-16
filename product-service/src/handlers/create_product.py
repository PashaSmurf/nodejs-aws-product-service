"""Lambda handler for POST /products endpoint"""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import create_product


def validate_product_data(data):
    """Validate product data"""
    errors = []

    if not data.get('title'):
        errors.append('title is required')
    if not isinstance(data.get('title'), str):
        errors.append('title must be a string')

    if 'description' in data and not isinstance(data['description'], str):
        errors.append('description must be a string')

    if 'price' not in data:
        errors.append('price is required')
    if not isinstance(data.get('price'), (int, float)) or data.get('price', -1) < 0:
        errors.append('price must be a non-negative number')

    if 'count' not in data:
        errors.append('count is required')
    if not isinstance(data.get('count'), int) or data.get('count', -1) < 0:
        errors.append('count must be a non-negative integer')

    return errors


def lambda_handler(event, context):
    """
    Create a new product in DynamoDB.

    Args:
        event: Lambda event with request body
        context: Lambda context

    Returns:
        API Gateway response with created product or error
    """
    print(f"Received request: {json.dumps(event)}")

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        print(f"Request body: {json.dumps(body)}")

        # Validate input
        validation_errors = validate_product_data(body)
        if validation_errors:
            print(f"Validation errors: {validation_errors}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid product data", "details": validation_errors}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        # Generate product ID
        product_id = str(uuid.uuid4())
        print(f"Generated product ID: {product_id}")

        # Create product
        product = create_product(
            product_id=product_id,
            title=body['title'],
            description=body.get('description', ''),
            price=body['price'],
            count=body['count']
        )
        print(f"Product created: {json.dumps(product)}")

        return {
            "statusCode": 201,
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
