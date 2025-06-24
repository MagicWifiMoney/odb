"""
Supabase configuration and client setup for Opportunity Dashboard
"""
import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseConfig:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get Supabase client for normal operations"""
        if not self._client:
            if not self.url or not self.key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
            self._client = create_client(self.url, self.key)
        return self._client
    
    @property
    def admin_client(self) -> Client:
        """Get Supabase admin client for service operations"""
        if not self._admin_client:
            if not self.url or not self.service_role_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
            self._admin_client = create_client(self.url, self.service_role_key)
        return self._admin_client
    
    def test_connection(self) -> bool:
        """Test connection to Supabase"""
        try:
            response = self.client.table('data_sources').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error("Supabase connection test failed: %s", e)
            return False

# Global instance
supabase_config = SupabaseConfig()

def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    return supabase_config.client

def get_supabase_admin_client() -> Client:
    """Get the Supabase admin client instance"""
    return supabase_config.admin_client
