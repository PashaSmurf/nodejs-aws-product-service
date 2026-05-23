import json
import os
import sys
import pytest
import csv
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from decimal import Decimal

# Add src directory to path so we can import handlers
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# ============================================================================
# TESTS FOR importProductsFile LAMBDA FUNCTION
# ============================================================================

class TestImportProductsFile:
    """Test suite for importProductsFile Lambda function"""

    @patch('handlers.import_products_file.s3_client')
    def test_missing_name_parameter(self, mock_s3):
        """Test that missing 'name' parameter returns 400 error"""
        from handlers.import_products_file import lambda_handler

        event = {'queryStringParameters': {}}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'name' in body['error'].lower()

    @patch('handlers.import_products_file.s3_client')
    def test_none_query_parameters(self, mock_s3):
        """Test handling of None queryStringParameters"""
        from handlers.import_products_file import lambda_handler

        event = {'queryStringParameters': None}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 400

    @patch('handlers.import_products_file.s3_client')
    def test_invalid_filename_path_traversal(self, mock_s3):
        """Test that path traversal attempts are rejected"""
        from handlers.import_products_file import lambda_handler

        invalid_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32',
            'folder/../../../etc/passwd',
            './../../etc/passwd'
        ]

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            for invalid_name in invalid_names:
                event = {'queryStringParameters': {'name': invalid_name}}
                response = lambda_handler(event, None)
                assert response['statusCode'] == 400
                body = json.loads(response['body'])
                assert 'Invalid' in body['error']

    @patch('handlers.import_products_file.s3_client')
    def test_valid_filename_returns_signed_url(self, mock_s3):
        """Test that valid filename returns a signed URL"""
        from handlers.import_products_file import lambda_handler

        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/bucket/signed-url'

        event = {'queryStringParameters': {'name': 'products.csv'}}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            assert 'https://' in response['body']
            assert 's3' in response['body']

        # Verify S3 mock was called correctly
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == 'put_object'
        assert call_args[1]['Params']['Key'] == 'uploaded/products.csv'

    @patch('handlers.import_products_file.s3_client')
    def test_url_encoded_filename(self, mock_s3):
        """Test that URL-encoded filenames are decoded correctly"""
        from handlers.import_products_file import lambda_handler

        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/signed'

        event = {'queryStringParameters': {'name': 'my%20file%20name.csv'}}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

        # Verify filename was decoded
        call_args = mock_s3.generate_presigned_url.call_args
        assert 'my file name.csv' in call_args[1]['Params']['Key']

    @patch('handlers.import_products_file.s3_client')
    def test_cors_headers_present(self, mock_s3):
        """Test that CORS headers are included in response"""
        from handlers.import_products_file import lambda_handler

        mock_s3.generate_presigned_url.return_value = 'https://s3.test'
        event = {'queryStringParameters': {'name': 'test.csv'}}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, None)
            assert 'headers' in response
            assert 'Access-Control-Allow-Origin' in response['headers']
            assert response['headers']['Access-Control-Allow-Origin'] == '*'

    @patch('handlers.import_products_file.s3_client')
    def test_missing_bucket_env_var(self, mock_s3):
        """Test handling when IMPORT_BUCKET_NAME env var is missing"""
        from handlers.import_products_file import lambda_handler

        event = {'queryStringParameters': {'name': 'test.csv'}}

        with patch.dict(os.environ, {}, clear=True):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body

# ============================================================================
# TESTS FOR importFileParser LAMBDA FUNCTION
# ============================================================================

class TestImportFileParser:
    """Test suite for importFileParser Lambda function"""

    def test_no_records_in_event(self):
        """Test that event with no records returns 400"""
        from handlers.import_file_parser import lambda_handler

        event = {'Records': []}

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'No S3 records' in body['error']

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_valid_s3_event_not_object_created(self, mock_s3, mock_sqs):
        """Test that non-ObjectCreated events are skipped"""
        from handlers.import_file_parser import lambda_handler

        event = {
            'Records': [{
                'eventName': 'ObjectDeleted:Delete',
                's3': {'bucket': {'name': 'bucket'}, 'object': {'key': 'uploaded/test.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            mock_s3.get_object.assert_not_called()
            mock_sqs.send_message.assert_not_called()

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_file_not_in_uploaded_folder(self, mock_s3, mock_sqs):
        """Test that files not in 'uploaded' folder are skipped"""
        from handlers.import_file_parser import lambda_handler

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'bucket'}, 'object': {'key': 'other/test.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            mock_s3.get_object.assert_not_called()
            mock_sqs.send_message.assert_not_called()

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_parse_valid_csv(self, mock_s3, mock_sqs):
        """Test parsing a valid CSV file and sending to SQS"""
        from handlers.import_file_parser import lambda_handler

        # Create mock CSV content
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,5\n2,Mouse,A mouse,29.99,10"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

            # Verify SQS send_message was called for each record
            assert mock_sqs.send_message.call_count == 2

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_parse_csv_with_bom(self, mock_s3, mock_sqs):
        """Test parsing CSV with UTF-8 BOM"""
        from handlers.import_file_parser import lambda_handler

        # Create CSV with BOM
        csv_content = "\ufeffid,title,description,price,count\n1,Laptop,A laptop,999.99,5"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

            # Verify product was sent to SQS (BOM should be handled)
            mock_sqs.send_message.assert_called_once()
            call_args = mock_sqs.send_message.call_args
            message_body = json.loads(call_args[1]['MessageBody'])
            assert message_body['title'] == 'Laptop'

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_skip_record_with_empty_title(self, mock_s3, mock_sqs):
        """Test that records with empty title are still sent to SQS (validation in catalogBatchProcess)"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,,A laptop,999.99,5\n2,Mouse,A mouse,29.99,10"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # SQS records are sent regardless of validation (validation happens in catalogBatchProcess)
            assert mock_sqs.send_message.call_count == 2

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_invalid_price_defaults_to_zero(self, mock_s3, mock_sqs):
        """Test that invalid price values are converted to 0"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,invalid,5"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify message was sent with price=0
            mock_sqs.send_message.assert_called_once()
            call_args = mock_sqs.send_message.call_args
            message_body = json.loads(call_args[1]['MessageBody'])
            assert message_body['price'] == 0.0

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_invalid_count_defaults_to_zero(self, mock_s3, mock_sqs):
        """Test that invalid count values are converted to 0"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,invalid"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify message was sent with count=0
            mock_sqs.send_message.assert_called_once()
            call_args = mock_sqs.send_message.call_args
            message_body = json.loads(call_args[1]['MessageBody'])
            assert message_body['count'] == 0

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_move_file_to_parsed_folder(self, mock_s3, mock_sqs):
        """Test that file is moved from uploaded to parsed folder"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,5"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify file was copied to parsed folder
            mock_s3.copy_object.assert_called_once()
            copy_call = mock_s3.copy_object.call_args
            assert 'parsed/products.csv' in copy_call[1]['Key']
            
            # Verify original file was deleted
            mock_s3.delete_object.assert_called_once()
            delete_call = mock_s3.delete_object.call_args
            assert 'uploaded/products.csv' in delete_call[1]['Key']

    @patch('handlers.import_file_parser.sqs_client')
    @patch('handlers.import_file_parser.s3_client')
    def test_auto_generate_id_if_missing(self, mock_s3, mock_sqs):
        """Test that product ID is auto-generated if missing"""
        from handlers.import_file_parser import lambda_handler
        import uuid
        
        csv_content = "id,title,description,price,count\n,Laptop,A laptop,999.99,5"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'CATALOG_ITEMS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123/catalogItemsQueue'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify message was sent with auto-generated ID
            mock_sqs.send_message.assert_called_once()
            call_args = mock_sqs.send_message.call_args
            message_body = json.loads(call_args[1]['MessageBody'])
            assert message_body['id']  # Should have some ID


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

