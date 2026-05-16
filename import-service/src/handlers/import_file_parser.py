import json
import boto3
import logging
import csv
import uuid
import os
from io import StringIO
from decimal import Decimal

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get DynamoDB table name from environment
PRODUCTS_TABLE_NAME = os.environ.get('PRODUCTS_TABLE', 'products')
STOCKS_TABLE_NAME = os.environ.get('STOCKS_TABLE', 'stocks')


def lambda_handler(event, context):
    """
    Lambda handler triggered by S3 ObjectCreated event
    Parses CSV file from S3 'uploaded' folder and logs each record

    Event:
        S3 event with bucket and key information

    Behavior:
        1. Downloads the CSV file from S3
        2. Parses it using csv module
        3. Logs each record to CloudWatch
        4. (Optional) Moves file from 'uploaded' to 'parsed' folder
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
                    skipped_count = 0
                    saved_count = 0

                    for row in csv_reader:
                        record_count += 1
                        logger.info(f"Product record {record_count}: {json.dumps(row)}")

                        # Save product to DynamoDB
                        try:
                            if save_product_to_dynamodb(row):
                                saved_count += 1
                            else:
                                skipped_count += 1
                        except Exception as save_error:
                            logger.error(f"Error saving product record {record_count}: {str(save_error)}", exc_info=True)
                            # Continue processing other records even if one fails

                    logger.info(f"Successfully processed {record_count} records from {object_key}. Saved: {saved_count}, Skipped: {skipped_count}")

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


def save_product_to_dynamodb(product_row):
    """
    Save a product record from CSV to DynamoDB

    Args:
        product_row: Dictionary with keys: id, title, description, price, count

    Returns:
        True if product was saved, False if skipped
    """
    try:
        # Generate ID if not provided
        product_id = product_row.get('id')
        if product_id is None:
            product_id = ''
        product_id = str(product_id).strip()
        if not product_id:
            product_id = str(uuid.uuid4())
            logger.info(f"Generated new product ID: {product_id}")

        products_table = dynamodb.Table(PRODUCTS_TABLE_NAME)
        stocks_table = dynamodb.Table(STOCKS_TABLE_NAME)

        # Extract and validate data
        title = product_row.get('title')
        if title is None:
            title = ''
        title = str(title).strip()

        if not title:
            logger.warning(f"Skipping record with missing/empty title. Row: {product_row}")
            return False

        description = product_row.get('description')
        if description is None:
            description = ''
        description = str(description).strip()

        try:
            price_val = product_row.get('price', 0)
            if price_val is None:
                price_val = 0
            price = Decimal(str(price_val))
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid price for product {title}: {product_row.get('price')}. Setting to 0. Error: {str(e)}")
            price = Decimal(0)

        try:
            count_val = product_row.get('count', 0)
            if count_val is None:
                count_val = 0
            count = int(count_val)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid count for product {title}: {product_row.get('count')}. Setting to 0. Error: {str(e)}")
            count = 0

        logger.info(f"Saving product: id={product_id}, title={title}, price={price}, count={count}")

        # Save to products table
        products_table.put_item(
            Item={
                'id': product_id,
                'title': title,
                'description': description,
                'price': price,
            }
        )
        logger.info(f"✓ Saved product to DynamoDB: {product_id} - {title}")

        # Save stock count to stocks table
        stocks_table.put_item(
            Item={
                'product_id': product_id,
                'count': count,
            }
        )
        logger.info(f"✓ Saved stock for product {product_id}: count={count}")

        return True

    except Exception as e:
        logger.error(f"Error saving product to DynamoDB: {str(e)}", exc_info=True)
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

