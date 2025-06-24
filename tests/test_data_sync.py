import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Ensure backend code is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Provide a dummy firecrawl module so importing DataSyncService succeeds
sys.modules['firecrawl'] = MagicMock()

# Provide minimal Flask-SQLAlchemy and SQLAlchemy mocks
sys.modules.setdefault('flask_sqlalchemy', MagicMock(SQLAlchemy=MagicMock(return_value=MagicMock())))
dummy_sqlalchemy = SimpleNamespace(
    exc=SimpleNamespace(IntegrityError=Exception),
    Index=lambda *a, **k: None,
)
sys.modules.setdefault('sqlalchemy', dummy_sqlalchemy)
sys.modules.setdefault('sqlalchemy.exc', dummy_sqlalchemy.exc)

# Stub database and models used by DataSyncService
dummy_db = MagicMock()
sys.modules.setdefault('src.database', SimpleNamespace(db=dummy_db))
sys.modules.setdefault(
    'src.models.opportunity',
    SimpleNamespace(
        Opportunity=type('Opportunity', (), {'created_at': None, 'due_date': None}),
        DataSource=MagicMock(),
        SyncLog=MagicMock(),
        db=dummy_db,
    ),
)

# Other external dependencies used by API clients
sys.modules.setdefault('requests', MagicMock())
sys.modules.setdefault('dateutil', SimpleNamespace(parser=MagicMock()))
sys.modules.setdefault('dateutil.parser', MagicMock())
sys.modules.setdefault('fuzzywuzzy', MagicMock(fuzz=MagicMock()))

from src.services.data_sync_service import DataSyncService


def test_data_sync():
    """DataSyncService integrates API data correctly using mocked clients."""
    mock_client = MagicMock()
    mock_client.fetch_opportunities.return_value = {}
    mock_client.transform_data.return_value = [
        {
            'source_id': '1',
            'title': 'Test Opportunity',
            'source_type': 'api',
            'source_name': 'sam_gov',
        }
    ]

    with patch('src.services.data_sync_service.APIClientFactory.get_all_clients', return_value={'sam_gov': mock_client}), \
         patch('src.services.data_sync_service.db'), \
         patch('src.services.data_sync_service.SyncLog'), \
         patch('src.services.data_sync_service.DataSyncService.process_opportunities', return_value=(1, 0)):
        service = DataSyncService()
        result = service.sync_source('sam_gov', mock_client)

    assert result['status'] == 'completed'
    assert result['processed'] == 1
    assert result['added'] == 1
    assert result['updated'] == 0

