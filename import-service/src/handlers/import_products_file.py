import json
import boto3
import logging
import os
from urllib.parse import unquote

s3_client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for GET /import
    Generates a signed URL for uploading a CSV file to S3 bucket

    Query parameters:
        name: The name of the CSV file to upload

    Returns:
        Signed URL as a string with CORS headers
    """
    try:
        logger.info(f"Event: {json.dumps(event)}")

        # Get bucket name from environment variables
        bucket_name = os.environ.get('IMPORT_BUCKET_NAME')
        if not bucket_name:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Import bucket not configured'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
                }
            }

        # Extract file name from query parameters
        query_params = event.get('queryStringParameters', {})
        if not query_params or 'name' not in query_params:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'File name parameter "name" is required'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
                }
            }

        file_name = unquote(query_params['name'])
        logger.info(f"Generating signed URL for file: {file_name}")

        # Validate file name (basic validation - no path traversal)
        if '/' in file_name or '\\' in file_name or '..' in file_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid file name'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
                }
            }

        # Create the S3 key with 'uploaded' prefix
        s3_key = f'uploaded/{file_name}'

        # Generate signed URL (valid for 1 hour)
        signed_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600,
            HttpMethod='PUT'
        )

        logger.info(f"Successfully generated signed URL for {s3_key}")

        return {
            'statusCode': 200,
            'body': signed_url,
            'headers': {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
            }
        }

    except Exception as e:
        logger.error(f"Error generating signed URL: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate signed URL'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
            }
        }

