import os
import json
from typing import Dict, Any

class FeatureFlags:
    """Simple feature flag system for controlling feature rollouts"""
    
    def __init__(self):
        self.flags = {
            # Performance optimization features
            'redis_cache_enabled': os.getenv('FEATURE_REDIS_CACHE', 'true').lower() == 'true',
            'performance_monitoring': os.getenv('FEATURE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
            'query_optimization': os.getenv('FEATURE_QUERY_OPTIMIZATION', 'true').lower() == 'true',
            'cache_warming': os.getenv('FEATURE_CACHE_WARMING', 'false').lower() == 'true',
            
            # API optimization features  
            'response_compression': os.getenv('FEATURE_RESPONSE_COMPRESSION', 'true').lower() == 'true',
            'request_batching': os.getenv('FEATURE_REQUEST_BATCHING', 'false').lower() == 'true',
            'intelligent_caching': os.getenv('FEATURE_INTELLIGENT_CACHING', 'true').lower() == 'true',
            
            # Monitoring and analytics
            'detailed_analytics': os.getenv('FEATURE_DETAILED_ANALYTICS', 'false').lower() == 'true',
            'performance_alerts': os.getenv('FEATURE_PERFORMANCE_ALERTS', 'false').lower() == 'true',
            'cost_tracking': os.getenv('FEATURE_COST_TRACKING', 'true').lower() == 'true',
            
            # Safety features
            'circuit_breaker': os.getenv('FEATURE_CIRCUIT_BREAKER', 'true').lower() == 'true',
            'graceful_degradation': os.getenv('FEATURE_GRACEFUL_DEGRADATION', 'true').lower() == 'true',
            'auto_scaling': os.getenv('FEATURE_AUTO_SCALING', 'false').lower() == 'true',
        }
        
        # Load additional flags from JSON file if it exists
        self._load_json_flags()
    
    def _load_json_flags(self):
        """Load feature flags from JSON configuration file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'feature_flags.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    json_flags = json.load(f)
                    self.flags.update(json_flags)
        except Exception as e:
            print(f"Warning: Could not load feature flags from JSON: {e}")
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.flags.get(flag_name, False)
    
    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a feature flag value with default"""
        return self.flags.get(flag_name, default)
    
    def set_flag(self, flag_name: str, value: bool):
        """Set a feature flag value (runtime only)"""
        self.flags[flag_name] = value
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()
    
    def get_enabled_flags(self) -> Dict[str, bool]:
        """Get only enabled feature flags"""
        return {k: v for k, v in self.flags.items() if v}
    
    def to_dict(self) -> Dict[str, Any]:
        """Export flags as dictionary for API responses"""
        return {
            'flags': self.flags,
            'enabled_count': len(self.get_enabled_flags()),
            'total_count': len(self.flags)
        }

# Global feature flags instance
feature_flags = FeatureFlags()

# Convenience functions
def is_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled"""
    return feature_flags.is_enabled(flag_name)

def get_flag(flag_name: str, default: bool = False) -> bool:
    """Get a feature flag value with default"""
    return feature_flags.get_flag(flag_name, default) 