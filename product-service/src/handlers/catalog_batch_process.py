"""Lambda handler for processing catalog batch from SQS"""

import json
import sys
import os
import uuid
import logging
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from utils.db import create_product

# Note: Decimal is required by DynamoDB for numeric types

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')

def lambda_handler(event, context):
    """
    Process batch of catalog items from SQS queue and create products.
    Triggered by SQS with batch size of 5.
    After processing, publishes notification to SNS topic.

    Args:
        event: SQS event with Records containing product data
        context: Lambda context

    Returns:
        API Gateway response with result
    """
    logger.info(f"Received SQS event: {json.dumps(event)}")

    try:
        records = event.get('Records', [])
        logger.info(f"Processing {len(records)} SQS records")

        if not records:
            logger.warning("No records in SQS event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No SQS records found'})
            }

        created_products = []
        failed_records = []

        for idx, record in enumerate(records):
            try:
                logger.info(f"Processing record {idx + 1}/{len(records)}")

                # Parse SQS message body
                message_body = record.get('body', '{}')
                if isinstance(message_body, str):
                    product_data = json.loads(message_body)
                else:
                    product_data = message_body

                logger.info(f"Product data: {json.dumps(product_data)}")

                # Validate required fields
                product_id = product_data.get('id', '')
                if not product_id or not str(product_id).strip():
                    product_id = str(uuid.uuid4())
                    logger.info(f"Generated new product ID: {product_id}")

                title = product_data.get('title', '').strip()
                if not title:
                    logger.warning(f"Skipping record with missing title: {product_data}")
                    failed_records.append({
                        'messageId': record.get('messageId'),
                        'reason': 'Missing or empty title',
                        'data': product_data
                    })
                    continue

                description = product_data.get('description', '').strip()

                # Parse price
                try:
                    price = Decimal(str(product_data.get('price', 0)))
                except (ValueError, TypeError):
                    price = Decimal(0)
                    logger.warning(f"Invalid price for product {title}, setting to 0")

                # Parse count
                try:
                    count = int(product_data.get('count', 0))
                except (ValueError, TypeError):
                    count = 0
                    logger.warning(f"Invalid count for product {title}, setting to 0")

                # Create product using utility function
                product = create_product(
                    product_id=product_id,
                    title=title,
                    description=description,
                    price=price,
                    count=count
                )

                logger.info(f"✓ Product created: {product_id} - {title}")
                created_products.append(product)

            except Exception as record_error:
                logger.error(f"Error processing record {idx}: {str(record_error)}", exc_info=True)
                failed_records.append({
                    'messageId': record.get('messageId'),
                    'reason': str(record_error),
                    'data': record.get('body')
                })
                # Continue processing other records

        # Publish notification to SNS
        try:
            publish_sns_notification(created_products, failed_records)
        except Exception as sns_error:
            logger.error(f"Error publishing to SNS: {str(sns_error)}", exc_info=True)
            # Don't fail the entire batch if SNS publish fails

        logger.info(f"Batch processing complete. Created: {len(created_products)}, Failed: {len(failed_records)}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Batch processed successfully',
                'created': len(created_products),
                'failed': len(failed_records),
                'products': created_products,
                'errors': failed_records if failed_records else None
            })
        }

    except Exception as e:
        logger.error(f"Error in catalog batch process: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Batch processing failed'})
        }


def publish_sns_notification(created_products, failed_records):
    """
    Publish notification to SNS topic about created products.

    Args:
        created_products: List of created product dictionaries
        failed_records: List of failed records
    """
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not set, skipping notification")
        return

    # Build notification message
    message_lines = [
        "=== Catalog Batch Process Notification ===",
        f"\nProducts Created: {len(created_products)}",
    ]

    if created_products:
        message_lines.append("\nCreated Products:")
        for i, product in enumerate(created_products, 1):
            message_lines.append(
                f"\n{i}. {product.get('title', 'Unknown')}"
                f"\n   ID: {product.get('id')}"
                f"\n   Price: ${product.get('price', 0)}"
                f"\n   Count: {product.get('count', 0)}"
            )

    if failed_records:
        message_lines.append(f"\n\nFailed Records: {len(failed_records)}")
        for i, record in enumerate(failed_records, 1):
            message_lines.append(
                f"\n{i}. Message ID: {record.get('messageId')}"
                f"\n   Reason: {record.get('reason')}"
            )

    message = "\n".join(message_lines)

    logger.info(f"Publishing SNS notification with {len(created_products)} products created")

    # Publish to SNS
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject='Catalog Batch Process - Product Creation Report',
        Message=message
    )

    logger.info("✓ SNS notification published")

