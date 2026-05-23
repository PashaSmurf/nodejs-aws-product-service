import json
import boto3
import logging
import csv
import uuid
import os
from io import StringIO

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler triggered by S3 ObjectCreated event
    Parses CSV file from S3 'uploaded' folder and sends each record to SQS

    Event:
        S3 event with bucket and key information

    Behavior:
        1. Downloads the CSV file from S3
        2. Parses it using csv module
        3. Sends each record to SQS queue
        4. Moves file from 'uploaded' to 'parsed' folder
    """
    try:
        logger.info(f"Event: {json.dumps(event)}")

        # Extract bucket and key from the S3 event
        records = event.get('Records', [])
        if not records:
            logger.warning("No records in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No S3 records found'})
            }

        for record in records:
            logger.info(f"Processing record: {json.dumps(record)}")

            if record.get('eventName', '').startswith('ObjectCreated:'):
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']

                # Only process files from 'uploaded' folder
                if not object_key.startswith('uploaded/'):
                    logger.info(f"Skipping file not in 'uploaded' folder: {object_key}")
                    continue

                logger.info(f"Processing file: {bucket_name}/{object_key}")

                try:
                    # Download file from S3
                    logger.info(f"Downloading file from S3: {bucket_name}/{object_key}")
                    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                    # Use utf-8-sig to automatically strip BOM if present
                    file_content = response['Body'].read().decode('utf-8-sig')
                    logger.info(f"File downloaded, size: {len(file_content)} bytes")

                    # Parse CSV
                    logger.info("Parsing CSV file")
                    csv_file = StringIO(file_content)
                    csv_reader = csv.DictReader(csv_file)

                    # Log CSV fieldnames for debugging
                    fieldnames = csv_reader.fieldnames
                    logger.info(f"CSV fieldnames: {fieldnames}")

                    record_count = 0
                    sent_count = 0

                    for row in csv_reader:
                        record_count += 1

                        # Send record to SQS
                        try:
                            if send_record_to_sqs(row):
                                sent_count += 1
                        except Exception as sqs_error:
                            logger.error(f"Error sending record {record_count} to SQS: {str(sqs_error)}", exc_info=True)
                            # Continue processing other records even if one fails

                    logger.info(f"Successfully processed {record_count} records from {object_key}. Sent to SQS: {sent_count}")

                    # Optional: Move file from 'uploaded' to 'parsed' folder
                    try:
                        logger.info(f"Moving file to parsed folder: {object_key}")
                        move_file_to_parsed(bucket_name, object_key)
                        logger.info(f"✓ Successfully moved file to parsed folder")
                    except Exception as move_error:
                        logger.error(f"Error moving file to parsed folder: {str(move_error)}", exc_info=True)
                        # Continue even if move fails

                except csv.Error as csv_error:
                    logger.error(f"CSV parsing error for {object_key}: {str(csv_error)}", exc_info=True)
                    raise
                except Exception as file_error:
                    logger.error(f"Error processing file {object_key}: {str(file_error)}", exc_info=True)
                    raise

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'File processed successfully'})
        }

    except Exception as e:
        logger.error(f"Error in import file parser: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'File processing failed'})
        }


def send_record_to_sqs(product_row):
    """
    Send a product record from CSV to SQS queue

    Args:
        product_row: Dictionary with keys: id, title, description, price, count

    Returns:
        True if record was sent, False otherwise
    """
    try:
        # Get SQS queue URL from environment
        queue_url = os.environ.get('CATALOG_ITEMS_QUEUE_URL')
        if not queue_url:
            logger.error("CATALOG_ITEMS_QUEUE_URL not set")
            raise ValueError("CATALOG_ITEMS_QUEUE_URL environment variable not set")

        # Prepare product data
        product_id = product_row.get('id', '').strip()
        if not product_id:
            product_id = str(uuid.uuid4())

        title = product_row.get('title', '').strip()
        description = product_row.get('description', '').strip()

        try:
            price = float(product_row.get('price', 0))
        except (ValueError, TypeError):
            price = 0.0

        try:
            count = int(product_row.get('count', 0))
        except (ValueError, TypeError):
            count = 0

        # Build message for SQS
        message_body = {
            'id': product_id,
            'title': title,
            'description': description,
            'price': price,
            'count': count,
        }

        logger.info(f"Sending record to SQS: {json.dumps(message_body)}")

        # Send to SQS
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )

        logger.info(f"✓ Record sent to SQS: {product_id} - {title}")
        return True

    except Exception as e:
        logger.error(f"Error sending record to SQS: {str(e)}", exc_info=True)
        raise


def move_file_to_parsed(bucket_name, object_key):
    """
    Move file from 'uploaded' folder to 'parsed' folder
    This effectively copies the file and deletes the original
    """
    if not object_key.startswith('uploaded/'):
        logger.warning(f"File {object_key} is not in uploaded folder, skipping move")
        return

    # Create new key in 'parsed' folder
    file_name = object_key.replace('uploaded/', '', 1)
    parsed_key = f'parsed/{file_name}'

    try:
        # Copy file to 'parsed' folder
        logger.info(f"Copying file from {object_key} to {parsed_key}")
        copy_source = {'Bucket': bucket_name, 'Key': object_key}
        s3_client.copy_object(
            CopySource=copy_source,
            Bucket=bucket_name,
            Key=parsed_key
        )
        logger.info(f"✓ Copied file to {parsed_key}")

        # Delete original file from 'uploaded' folder
        logger.info(f"Deleting original file from {object_key}")
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"✓ Deleted original file from {object_key}")

    except Exception as e:
        logger.error(f"Error moving file from {object_key} to {parsed_key}: {str(e)}", exc_info=True)
        raise

