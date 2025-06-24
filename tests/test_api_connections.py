import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Ensure backend code is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Provide dummy requests module for API client imports
sys.modules.setdefault('requests', MagicMock())
sys.modules.setdefault('dateutil', SimpleNamespace(parser=MagicMock()))
sys.modules.setdefault('dateutil.parser', MagicMock())

from src.services import api_clients


def test_api_connections():
    """APIClientFactory creates clients that fetch and transform data."""
    sam_client = MagicMock()
    sam_client.fetch_opportunities.return_value = {}
    sam_client.transform_data.return_value = [{'source_id': 's1', 'title': 'SAM'}]

    grants_client = MagicMock()
    grants_client.fetch_opportunities.return_value = {}
    grants_client.transform_data.return_value = [{'source_id': 'g1', 'title': 'Grant'}]

    spending_client = MagicMock()
    spending_client.fetch_recent_awards.return_value = {}
    spending_client.transform_award_data.return_value = [{'source_id': 'u1', 'title': 'Award'}]

    with patch.object(api_clients.APIClientFactory, 'create_sam_gov_client', return_value=sam_client), \
         patch.object(api_clients.APIClientFactory, 'create_grants_gov_client', return_value=grants_client), \
         patch.object(api_clients.APIClientFactory, 'create_usa_spending_client', return_value=spending_client):
        sc = api_clients.APIClientFactory.create_sam_gov_client()
        gc = api_clients.APIClientFactory.create_grants_gov_client()
        uc = api_clients.APIClientFactory.create_usa_spending_client()

        assert sc.transform_data(sc.fetch_opportunities()) == [{'source_id': 's1', 'title': 'SAM'}]
        assert gc.transform_data(gc.fetch_opportunities()) == [{'source_id': 'g1', 'title': 'Grant'}]
        assert uc.transform_award_data(uc.fetch_recent_awards({})) == [{'source_id': 'u1', 'title': 'Award'}]


