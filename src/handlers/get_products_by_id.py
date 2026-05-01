"""Lambda handler for GET /products/{productId} endpoint"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.products import PRODUCTS


def lambda_handler(event, context):
    """
    Get a specific product by ID.
    
    Args:
        event: Lambda event with pathParameters containing productId
        context: Lambda context
    
    Returns:
        API Gateway response with product details or error
    """
    try:
        # Get productId from path parameters
        product_id = event.get("pathParameters", {}).get("productId")

        if not product_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Product ID is required"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        # Find product by ID
        product = None
        for p in PRODUCTS:
            if p.id == product_id:
                product = p
                break

        if not product:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Product not found"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        return {
            "statusCode": 200,
            "body": json.dumps(product.to_dict()),
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
