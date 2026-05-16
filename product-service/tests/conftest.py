"""
Pytest configuration and fixtures for product service tests.
Mocks all external AWS services (DynamoDB) for unit testing.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# In-memory storage for test data (module-level to persist across imports)
_test_data = {
    'products': {
        'id1': {'id': 'id1', 'title': 'Oranges', 'description': 'Oranges Product Description', 'price': Decimal('24')},
        'id2': {'id': 'id2', 'title': 'Bananas', 'description': 'Bananas Product Description', 'price': Decimal('15')},
        'id3': {'id': 'id3', 'title': 'Apples', 'description': 'Apples Product Description', 'price': Decimal('32')},
        'id4': {'id': 'id4', 'title': 'Pineapples', 'description': 'Pineapples Product Description', 'price': Decimal('12')},
        'id5': {'id': 'id5', 'title': 'Pears', 'description': 'Pears Product Description', 'price': Decimal('11')},
        'id6': {'id': 'id6', 'title': 'Grapes', 'description': 'Grapes Product Description', 'price': Decimal('31')},
    },
    'stocks': {
        'id1': {'product_id': 'id1', 'count': 1},
        'id2': {'product_id': 'id2', 'count': 2},
        'id3': {'product_id': 'id3', 'count': 3},
        'id4': {'product_id': 'id4', 'count': 4},
        'id5': {'product_id': 'id5', 'count': 5},
        'id6': {'product_id': 'id6', 'count': 6},
    }
}


def create_mock_table(table_name):
    """Create a mock DynamoDB table"""
    mock_table = MagicMock()

    def put_item(Item):
        """Mock put_item"""
        if table_name == 'products':
            _test_data['products'][Item['id']] = Item
        elif table_name == 'stocks':
            _test_data['stocks'][Item['product_id']] = Item
        return {}

    def get_item(Key):
        """Mock get_item"""
        if table_name == 'products':
            item = _test_data['products'].get(Key['id'])
        elif table_name == 'stocks':
            item = _test_data['stocks'].get(Key['product_id'])
        else:
            item = None
        return {'Item': item} if item else {}

    def scan():
        """Mock scan"""
        if table_name == 'products':
            items = list(_test_data['products'].values())
        elif table_name == 'stocks':
            items = list(_test_data['stocks'].values())
        else:
            items = []
        return {'Items': items}

    def delete_item(Key):
        """Mock delete_item"""
        if table_name == 'products':
            _test_data['products'].pop(Key['id'], None)
        elif table_name == 'stocks':
            _test_data['stocks'].pop(Key['product_id'], None)
        return {}

    def update_item(Key, AttributeUpdates):
        """Mock update_item"""
        if table_name == 'products':
            item_id = Key['id']
            if item_id in _test_data['products']:
                item = _test_data['products'][item_id]
                for attr, update_spec in AttributeUpdates.items():
                    item[attr] = update_spec.get('Value', update_spec)
            return {'Attributes': _test_data['products'].get(item_id, {})}
        elif table_name == 'stocks':
            product_id = Key['product_id']
            if product_id in _test_data['stocks']:
                item = _test_data['stocks'][product_id]
                for attr, update_spec in AttributeUpdates.items():
                    item[attr] = update_spec.get('Value', update_spec)
            return {'Attributes': _test_data['stocks'].get(product_id, {})}
        return {}

    mock_table.put_item.side_effect = put_item
    mock_table.get_item.side_effect = get_item
    mock_table.scan.side_effect = scan
    mock_table.delete_item.side_effect = delete_item
    mock_table.update_item.side_effect = update_item

    return mock_table


# Patch boto3 BEFORE any modules are imported
patcher = patch('boto3.resource')
mock_boto3_resource = patcher.start()

def mock_resource_factory(service_name, **kwargs):
    """Factory for mocking AWS resource creation"""
    if service_name == 'dynamodb':
        mock_resource = MagicMock()
        mock_resource.Table.side_effect = create_mock_table
        return mock_resource
    return MagicMock()

mock_boto3_resource.side_effect = mock_resource_factory


@pytest.fixture(autouse=True)
def reset_test_data():
    """Reset test data before each test"""
    # Clear created items but keep initial seed data
    _test_data['products'] = {
        'id1': {'id': 'id1', 'title': 'Oranges', 'description': 'Oranges Product Description', 'price': Decimal('24')},
        'id2': {'id': 'id2', 'title': 'Bananas', 'description': 'Bananas Product Description', 'price': Decimal('15')},
        'id3': {'id': 'id3', 'title': 'Apples', 'description': 'Apples Product Description', 'price': Decimal('32')},
        'id4': {'id': 'id4', 'title': 'Pineapples', 'description': 'Pineapples Product Description', 'price': Decimal('12')},
        'id5': {'id': 'id5', 'title': 'Pears', 'description': 'Pears Product Description', 'price': Decimal('11')},
        'id6': {'id': 'id6', 'title': 'Grapes', 'description': 'Grapes Product Description', 'price': Decimal('31')},
    }
    _test_data['stocks'] = {
        'id1': {'product_id': 'id1', 'count': 1},
        'id2': {'product_id': 'id2', 'count': 2},
        'id3': {'product_id': 'id3', 'count': 3},
        'id4': {'product_id': 'id4', 'count': 4},
        'id5': {'product_id': 'id5', 'count': 5},
        'id6': {'product_id': 'id6', 'count': 6},
    }
    yield
    # No cleanup needed - test data is isolated per test


@pytest.fixture(scope="session", autouse=True)
def cleanup_patcher():
    """Clean up patcher after all tests"""
    yield
    patcher.stop()






