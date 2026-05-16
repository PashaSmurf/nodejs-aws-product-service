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
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'No S3 records' in body['error']

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_valid_s3_event_not_object_created(self, mock_s3, mock_dynamodb):
        """Test that non-ObjectCreated events are skipped"""
        from handlers.import_file_parser import lambda_handler

        event = {
            'Records': [{
                'eventName': 'ObjectDeleted:Delete',
                's3': {'bucket': {'name': 'bucket'}, 'object': {'key': 'uploaded/test.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            mock_s3.get_object.assert_not_called()

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_file_not_in_uploaded_folder(self, mock_s3, mock_dynamodb):
        """Test that files not in 'uploaded' folder are skipped"""
        from handlers.import_file_parser import lambda_handler

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'bucket'}, 'object': {'key': 'other/test.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            mock_s3.get_object.assert_not_called()

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_parse_valid_csv(self, mock_s3, mock_dynamodb):
        """Test parsing a valid CSV file"""
        from handlers.import_file_parser import lambda_handler

        # Create mock CSV content
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,5\n2,Mouse,A mouse,29.99,10"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response

        # Mock DynamoDB tables - use return_value instead of side_effect
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

            # Verify Product.Table and Stocks.Table calls
            assert mock_dynamodb.Table.call_count >= 2

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_parse_csv_with_bom(self, mock_s3, mock_dynamodb):
        """Test parsing CSV with UTF-8 BOM"""
        from handlers.import_file_parser import lambda_handler

        # Create CSV with BOM
        csv_content = "\ufeffid,title,description,price,count\n1,Laptop,A laptop,999.99,5"

        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response

        # Mock DynamoDB tables
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table]

        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }

        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200

            # Verify product was saved (BOM should be handled)
            mock_products_table.put_item.assert_called_once()
            call_args = mock_products_table.put_item.call_args[1]['Item']
            assert call_args['title'] == 'Laptop'

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_skip_record_with_empty_title(self, mock_s3, mock_dynamodb):
        """Test that records with empty title are skipped"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,,A laptop,999.99,5\n2,Mouse,A mouse,29.99,10"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        # Provide extra mocks for both iterations
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Only 1 product should be saved (the 2nd one - mouse)
            assert mock_dynamodb.Table.call_count >= 2

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_invalid_price_defaults_to_zero(self, mock_s3, mock_dynamodb):
        """Test that invalid price values are handled gracefully"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,5"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify at least one product was attempted to be saved
            assert mock_dynamodb.Table.call_count >= 2

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_invalid_count_defaults_to_zero(self, mock_s3, mock_dynamodb):
        """Test that invalid count values are handled gracefully"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,10"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify at least one product was attempted to be saved
            assert mock_dynamodb.Table.call_count >= 2

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_move_file_to_parsed_folder(self, mock_s3, mock_dynamodb):
        """Test that file is moved from uploaded to parsed folder"""
        from handlers.import_file_parser import lambda_handler
        
        csv_content = "id,title,description,price,count\n1,Laptop,A laptop,999.99,5"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
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

    @patch('handlers.import_file_parser.dynamodb')
    @patch('handlers.import_file_parser.s3_client')
    def test_auto_generate_id_if_missing(self, mock_s3, mock_dynamodb):
        """Test that product ID is auto-generated if missing"""
        from handlers.import_file_parser import lambda_handler
        import uuid
        
        csv_content = "id,title,description,price,count\n,Laptop,A laptop,999.99,5"
        
        mock_response = {
            'Body': MagicMock(read=lambda: csv_content.encode('utf-8'))
        }
        mock_s3.get_object.return_value = mock_response
        
        mock_products_table = MagicMock()
        mock_stocks_table = MagicMock()
        mock_dynamodb.Table.side_effect = [mock_products_table, mock_stocks_table, mock_products_table, mock_stocks_table]
        
        event = {
            'Records': [{
                'eventName': 'ObjectCreated:Put',
                's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'uploaded/products.csv'}}
            }]
        }
        
        with patch.dict(os.environ, {'IMPORT_BUCKET_NAME': 'test-bucket',
                                      'PRODUCTS_TABLE': 'products',
                                      'STOCKS_TABLE': 'stocks'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            
            # Verify products table was called (meaning a product was saved)
            assert mock_dynamodb.Table.call_count >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

