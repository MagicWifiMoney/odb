#!/usr/bin/env python3
"""
Railway Worker Service for ODB Data Monitoring
Automated data collection from government APIs with intelligent scheduling
"""

import os
import sys
import time
import logging
import schedule
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Railway captures stdout
        logging.FileHandler('worker.log') if not os.getenv('RAILWAY_ENVIRONMENT') else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Railway Environment Detection
RAILWAY_ENV = os.getenv('RAILWAY_ENVIRONMENT')
IS_RAILWAY = RAILWAY_ENV is not None

# API Configuration
SAM_API_KEY = os.getenv('SAM_API_KEY')
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Backend API URL - use Railway internal URL if available
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5001')
if IS_RAILWAY:
    # Use Railway internal networking
    BACKEND_URL = os.getenv('BACKEND_INTERNAL_URL', BACKEND_URL)

logger.info(f"Worker starting - Railway: {IS_RAILWAY}, Backend: {BACKEND_URL}")

class APIMonitor:
    def __init__(self):
        self.last_run = {}
        self.api_rotation_index = 0
        self.apis = [
            {'name': 'SAM.gov', 'endpoint': '/sync', 'source': 'sam', 'requires_key': True, 'key': SAM_API_KEY},
            {'name': 'Grants.gov', 'endpoint': '/sync', 'source': 'grants', 'requires_key': False, 'key': None},
            {'name': 'USASpending', 'endpoint': '/sync', 'source': 'usaspending', 'requires_key': False, 'key': None},
        ]
        
        # Filter APIs based on available keys
        self.available_apis = [api for api in self.apis if not api['requires_key'] or api['key']]
        
        if not self.available_apis:
            logger.warning("No APIs available - missing required API keys")
        else:
            logger.info(f"Available APIs: {[api['name'] for api in self.available_apis]}")

    def make_api_call(self, endpoint, method='POST', data=None):
        """Make API call to backend with error handling"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            logger.info(f"Making {method} request to {url}")
            
            headers = {'Content-Type': 'application/json'}
            
            if method == 'POST':
                response = requests.post(url, json=data or {}, headers=headers, timeout=300)
            else:
                response = requests.get(url, headers=headers, timeout=300)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {endpoint}")
            return {'error': 'timeout'}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error calling {endpoint}")
            return {'error': 'connection_error'}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error calling {endpoint}: {e}")
            return {'error': f'http_error: {e}'}
        except Exception as e:
            logger.error(f"Unexpected error calling {endpoint}: {e}")
            return {'error': f'unexpected: {e}'}

    def sync_single_api(self):
        """Sync data from a single API (hourly rotation)"""
        if not self.available_apis:
            logger.warning("No APIs available for sync")
            return
            
        # Rotate through available APIs
        api = self.available_apis[self.api_rotation_index % len(self.available_apis)]
        self.api_rotation_index += 1
        
        logger.info(f"Syncing {api['name']} (rotation {self.api_rotation_index})")
        
        # Use general sync endpoint with source parameter
        data = {'source': api['source']} if api.get('source') else {}
        result = self.make_api_call(api['endpoint'], data=data)
        
        if 'error' not in result:
            logger.info(f"Successfully synced {api['name']}")
            self.last_run[api['name']] = datetime.now()
        else:
            logger.error(f"Failed to sync {api['name']}: {result.get('error')}")

    def sync_all_apis(self):
        """Sync all available APIs (daily)"""
        logger.info("Starting daily sync of all APIs")
        
        success_count = 0
        for api in self.available_apis:
            logger.info(f"Syncing {api['name']}")
            data = {'source': api['source']} if api.get('source') else {}
            result = self.make_api_call(api['endpoint'], data=data)
            
            if 'error' not in result:
                logger.info(f"Successfully synced {api['name']}")
                self.last_run[api['name']] = datetime.now()
                success_count += 1
            else:
                logger.error(f"Failed to sync {api['name']}: {result.get('error')}")
        
        logger.info(f"Daily sync completed: {success_count}/{len(self.available_apis)} APIs successful")

    def run_ai_intelligence(self):
        """Run AI intelligence analysis (daily with API sync)"""
        if not PERPLEXITY_API_KEY:
            logger.warning("Skipping AI intelligence - no Perplexity API key")
            return
            
        logger.info("Running AI intelligence analysis")
        
        # Get market analysis
        result = self.make_api_call('/perplexity/market-analysis')
        if 'error' not in result:
            logger.info("AI market analysis completed")
        else:
            logger.error(f"AI market analysis failed: {result.get('error')}")

    def run_weekly_analysis(self):
        """Run comprehensive weekly analysis"""
        logger.info("Starting weekly comprehensive analysis")
        
        # Sync all data first
        self.sync_all_apis()
        
        # Run AI analysis if available
        if PERPLEXITY_API_KEY:
            self.run_ai_intelligence()
            
            # Run predictive analysis
            result = self.make_api_call('/perplexity/predict-opportunities')
            if 'error' not in result:
                logger.info("Weekly predictive analysis completed")
            else:
                logger.error(f"Weekly predictive analysis failed: {result.get('error')}")
        
        logger.info("Weekly analysis completed")

    def get_status(self):
        """Get worker status"""
        return {
            'worker_status': 'running',
            'railway_env': IS_RAILWAY,
            'backend_url': BACKEND_URL,
            'available_apis': len(self.available_apis),
            'last_runs': {k: v.isoformat() for k, v in self.last_run.items()},
            'next_hourly': schedule.next_run(),
            'has_sam_key': bool(SAM_API_KEY),
            'has_perplexity_key': bool(PERPLEXITY_API_KEY),
            'has_firecrawl_key': bool(FIRECRAWL_API_KEY)
        }

def main():
    """Main worker function"""
    logger.info("=== ODB Data Monitor Worker Starting ===")
    
    # Initialize monitor
    monitor = APIMonitor()
    
    # Log configuration
    logger.info(f"Railway Environment: {IS_RAILWAY}")
    logger.info(f"Backend URL: {BACKEND_URL}")
    logger.info(f"Available APIs: {len(monitor.available_apis)}")
    
    # Schedule tasks
    schedule.every().hour.do(monitor.sync_single_api)
    schedule.every().day.at("02:00").do(monitor.sync_all_apis)
    schedule.every().day.at("02:30").do(monitor.run_ai_intelligence)
    schedule.every().sunday.at("03:00").do(monitor.run_weekly_analysis)
    
    logger.info("Scheduled tasks:")
    logger.info("- Hourly: Single API rotation")
    logger.info("- Daily 02:00: All APIs sync")
    logger.info("- Daily 02:30: AI intelligence")
    logger.info("- Sunday 03:00: Weekly analysis")
    
    # Initial sync if no recent data
    logger.info("Running initial sync check...")
    monitor.sync_single_api()
    
    # Main loop
    logger.info("Worker is running - waiting for scheduled tasks...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()