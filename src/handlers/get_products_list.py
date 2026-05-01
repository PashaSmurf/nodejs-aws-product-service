"""Lambda handler for GET /products endpoint"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.products import PRODUCTS


def lambda_handler(event, context):
    """
    Get list of all products.
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response with product list
    """
    try:
        products = [product.to_dict() for product in PRODUCTS]

        return {
            "statusCode": 200,
            "body": json.dumps(products),
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
