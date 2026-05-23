"""Unit tests for catalog_batch_process handler"""

import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add src directory to path so we can import handlers
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestCatalogBatchProcess:
    """Test suite for catalogBatchProcess Lambda function"""

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_empty_records(self, mock_sns, mock_create_product):
        """Test that empty records list returns 400"""
        from handlers.catalog_batch_process import lambda_handler

        event = {'Records': []}

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'No SQS records' in body['error']

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_process_single_valid_record(self, mock_sns, mock_create_product):
        """Test processing a single valid SQS record"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 99.99,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'description': 'Test Description',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 1
            assert body['failed'] == 0
            mock_create_product.assert_called_once()

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_process_batch_of_five(self, mock_sns, mock_create_product):
        """Test processing a batch of 5 records"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }

        records = []
        for i in range(5):
            records.append({
                'messageId': f'msg-{i+1}',
                'body': json.dumps({
                    'id': f'test-id-{i+1}',
                    'title': f'Test Product {i+1}',
                    'description': 'Test Description',
                    'price': 99.99,
                    'count': 5
                })
            })

        event = {'Records': records}

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 5
            assert body['failed'] == 0
            assert mock_create_product.call_count == 5

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_skip_record_with_missing_title(self, mock_sns, mock_create_product):
        """Test that records with missing title are skipped"""
        from handlers.catalog_batch_process import lambda_handler

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': '',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 0
            assert body['failed'] == 1
            mock_create_product.assert_not_called()

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_auto_generate_id_if_missing(self, mock_sns, mock_create_product):
        """Test that product ID is auto-generated if missing"""
        from handlers.catalog_batch_process import lambda_handler
        import uuid

        mock_create_product.return_value = {
            'id': str(uuid.uuid4()),
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': '',
                        'title': 'Test Product',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 1

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_partial_batch_failure(self, mock_sns, mock_create_product):
        """Test partial batch failure - some records succeed, some fail"""
        from handlers.catalog_batch_process import lambda_handler

        def side_effect(*args, **kwargs):
            title = kwargs.get('title')
            if title == 'Good Product':
                return {'id': 'id-1', 'title': 'Good Product', 'price': 99.99, 'count': 5}
            else:
                raise Exception("Database error")

        mock_create_product.side_effect = side_effect

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'id-1',
                        'title': 'Good Product',
                        'price': 99.99,
                        'count': 5
                    })
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'id': 'id-2',
                        'title': 'Bad Product',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 1
            assert body['failed'] == 1

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_invalid_price_defaults_to_zero(self, mock_sns, mock_create_product):
        """Test that invalid price values are handled"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 0.0,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'price': 'invalid',
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            # Verify create_product was called with price=0.0
            call_args = mock_create_product.call_args
            assert call_args[1]['price'] == 0.0

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_invalid_count_defaults_to_zero(self, mock_sns, mock_create_product):
        """Test that invalid count values are handled"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 0
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'price': 99.99,
                        'count': 'invalid'
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            # Verify create_product was called with count=0
            call_args = mock_create_product.call_args
            assert call_args[1]['count'] == 0

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_sns_notification_published(self, mock_sns, mock_create_product):
        """Test that SNS notification is published after processing"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            # Verify SNS publish was called
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            assert 'Catalog Batch Process' in call_args[1]['Subject']

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_sns_notification_includes_product_details(self, mock_sns, mock_create_product):
        """Test that SNS notification includes created product details"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            mock_sns.publish.assert_called_once()
            call_args = mock_sns.publish.call_args
            message = call_args[1]['Message']
            assert 'Test Product' in message
            assert '99.99' in message or '99' in message

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_sns_notification_failure_does_not_fail_batch(self, mock_sns, mock_create_product):
        """Test that SNS publication failure doesn't fail the entire batch"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }
        mock_sns.publish.side_effect = Exception("SNS error")

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            # Should still return 200 success
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 1

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_all_records_fail(self, mock_sns, mock_create_product):
        """Test batch where all records fail"""
        from handlers.catalog_batch_process import lambda_handler

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id-1',
                        'title': '',  # Empty title
                        'price': 99.99,
                        'count': 5
                    })
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'id': 'test-id-2',
                        'title': '',  # Empty title
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['created'] == 0
            assert body['failed'] == 2
            mock_create_product.assert_not_called()

    @patch('handlers.catalog_batch_process.create_product')
    @patch('handlers.catalog_batch_process.sns_client')
    def test_parse_sqs_body_as_json(self, mock_sns, mock_create_product):
        """Test that SQS body is correctly parsed as JSON"""
        from handlers.catalog_batch_process import lambda_handler

        mock_create_product.return_value = {
            'id': 'test-id',
            'title': 'Test Product',
            'price': 99.99,
            'count': 5
        }

        event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'id': 'test-id',
                        'title': 'Test Product',
                        'description': 'Test Description',
                        'price': 99.99,
                        'count': 5
                    })
                }
            ]
        }

        with patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:createProductTopic'}):
            response = lambda_handler(event, None)
            assert response['statusCode'] == 200
            # Verify create_product was called with correct data
            call_args = mock_create_product.call_args
            assert call_args[1]['title'] == 'Test Product'
            assert call_args[1]['description'] == 'Test Description'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


