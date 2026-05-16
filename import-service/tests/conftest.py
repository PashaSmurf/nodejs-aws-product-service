"""
Pytest configuration for import-service tests
Mocks all external AWS services (S3, DynamoDB) for unit testing.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# In-memory storage for test data
_test_data = {
    'dynamodb': {
        'products': {},
        'stocks': {}
    },
    's3': {}
}


def create_mock_dynamodb_table(table_name):
    """Create a mock DynamoDB table"""
    mock_table = MagicMock()

    def put_item(Item):
        """Mock put_item"""
        if table_name == 'products':
            _test_data['dynamodb']['products'][Item['id']] = Item
        elif table_name == 'stocks':
            _test_data['dynamodb']['stocks'][Item['product_id']] = Item
        return {}

    def get_item(Key):
        """Mock get_item"""
        if table_name == 'products':
            item = _test_data['dynamodb']['products'].get(Key['id'])
        elif table_name == 'stocks':
            item = _test_data['dynamodb']['stocks'].get(Key['product_id'])
        else:
            item = None
        return {'Item': item} if item else {}

    def scan():
        """Mock scan"""
        if table_name == 'products':
            items = list(_test_data['dynamodb']['products'].values())
        elif table_name == 'stocks':
            items = list(_test_data['dynamodb']['stocks'].values())
        else:
            items = []
        return {'Items': items}

    mock_table.put_item.side_effect = put_item
    mock_table.get_item.side_effect = get_item
    mock_table.scan.side_effect = scan

    return mock_table


# Patch AWS services BEFORE any modules are imported
_dynamodb_patcher = patch('boto3.resource')
_mock_boto3_resource = _dynamodb_patcher.start()

def _mock_resource_factory(service_name, **kwargs):
    """Factory for mocking AWS resource creation"""
    if service_name == 'dynamodb':
        mock_resource = MagicMock()
        mock_resource.Table.side_effect = create_mock_dynamodb_table
        return mock_resource
    return MagicMock()

_mock_boto3_resource.side_effect = _mock_resource_factory


def pytest_configure(config):
    """pytest hook that runs before test collection"""
    pass


def pytest_unconfigure(config):
    """pytest hook that runs after all tests"""
    _dynamodb_patcher.stop()
