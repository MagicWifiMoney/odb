#!/usr/bin/env python3
"""
Perplexity Budget Tracker - Manages $10/month budget with cost controls
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

class PerplexityBudgetTracker:
    """Tracks and controls Perplexity API spending within $10/month budget"""
    
    def __init__(self, monthly_budget: float = 10.0):
        self.monthly_budget = monthly_budget
        self.emergency_reserve = 1.0  # Keep $1 for critical discoveries
        self.daily_limit = 25  # Maximum queries per day
        
        # Cost estimates for Sonar Small model
        self.cost_per_query = {
            'base_request': 0.005,  # $5 per 1000 requests
            'per_token': 0.0000002,  # $0.2 per 1M tokens
            'estimated_total': 0.007  # Conservative estimate per query
        }
        
        # Initialize Flask app for database access
        self.app = None
        self._init_flask_app()
        
        print("💰 Perplexity Budget Tracker initialized")
        print(f"   Monthly Budget: ${monthly_budget}")
        print(f"   Emergency Reserve: ${self.emergency_reserve}")
        print(f"   Daily Query Limit: {self.daily_limit}")
    
    def _init_flask_app(self):
        """Initialize Flask app for database context"""
        try:
            from flask import Flask
            from src.database import db
            
            self.app = Flask(__name__)
            
            # Database configuration
            database_url = os.getenv('DATABASE_URL', 'sqlite:///opportunities.db')
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            self.app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            db.init_app(self.app)
            print("✅ Flask app initialized for budget tracking")
            
        except Exception as e:
            print(f"⚠️ Flask app initialization failed: {e}")
            self.app = None
    
    def get_current_spending(self) -> Dict[str, float]:
        """Get current month's Perplexity spending"""
        if not self.app:
            return {'monthly_total': 0, 'daily_total': 0, 'queries_today': 0}
        
        try:
            with self.app.app_context():
                from src.config.supabase import get_supabase_admin_client
                supabase = get_supabase_admin_client()
                
                # Get current month start
                now = datetime.now()
                month_start = datetime(now.year, now.month, 1).isoformat()
                
                # Get today start
                today_start = datetime(now.year, now.month, now.day).isoformat()
                
                # Query monthly spending
                monthly_logs = supabase.table('sync_logs')\
                    .select('*')\
                    .eq('source_name', 'PerplexityAI')\
                    .gte('started_at', month_start)\
                    .execute()
                
                # Query daily spending
                daily_logs = supabase.table('sync_logs')\
                    .select('*')\
                    .eq('source_name', 'PerplexityAI')\
                    .gte('started_at', today_start)\
                    .execute()
                
                # Calculate costs (stored in records_processed field as cost in cents)
                monthly_total = sum(log.get('records_processed', 0) for log in monthly_logs.data) / 100.0
                daily_total = sum(log.get('records_processed', 0) for log in daily_logs.data) / 100.0
                queries_today = len(daily_logs.data)
                
                return {
                    'monthly_total': monthly_total,
                    'daily_total': daily_total,
                    'queries_today': queries_today,
                    'budget_remaining': self.monthly_budget - monthly_total,
                    'daily_limit_remaining': self.daily_limit - queries_today
                }
                
        except Exception as e:
            print(f"⚠️ Error getting spending data: {e}")
            return {'monthly_total': 0, 'daily_total': 0, 'queries_today': 0}
    
    def can_make_query(self, priority: str = 'medium') -> Dict[str, Any]:
        """Check if we can make a Perplexity query within budget"""
        spending = self.get_current_spending()
        
        # Check monthly budget (reserve $1 for emergencies)
        budget_limit = self.monthly_budget - self.emergency_reserve
        if priority != 'emergency':
            budget_limit = self.monthly_budget - self.emergency_reserve
        else:
            budget_limit = self.monthly_budget  # Can use emergency reserve
        
        monthly_available = budget_limit - spending['monthly_total']
        daily_available = self.daily_limit - spending['queries_today']
        
        can_query = (
            monthly_available >= self.cost_per_query['estimated_total'] and
            daily_available > 0
        )
        
        return {
            'can_query': can_query,
            'reason': self._get_block_reason(monthly_available, daily_available, priority),
            'spending': spending,
            'estimated_cost': self.cost_per_query['estimated_total']
        }
    
    def _get_block_reason(self, monthly_available: float, daily_available: int, priority: str) -> Optional[str]:
        """Get reason why query is blocked"""
        if monthly_available < self.cost_per_query['estimated_total']:
            if priority == 'emergency':
                if monthly_available < 0:
                    return 'monthly_budget_exceeded_completely'
                return None  # Emergency can proceed
            else:
                return 'monthly_budget_insufficient'
        
        if daily_available <= 0:
            return 'daily_limit_exceeded'
        
        return None
    
    def record_query(self, cost: float, query_type: str, tokens_used: int = 0, 
                     success: bool = True, error_message: str = None) -> bool:
        """Record a Perplexity query and its cost"""
        if not self.app:
            print("⚠️ Cannot record query - Flask app not initialized")
            return False
        
        try:
            with self.app.app_context():
                from src.config.supabase import get_supabase_admin_client
                supabase = get_supabase_admin_client()
                
                # Log the query cost (store cost in cents as integer)
                log_data = {
                    'source_name': 'PerplexityAI',
                    'sync_type': query_type,
                    'records_processed': int(cost * 100),  # Store cost in cents
                    'records_added': tokens_used,
                    'records_updated': 1 if success else 0,
                    'error_message': error_message,
                    'started_at': datetime.now().isoformat(),
                    'completed_at': datetime.now().isoformat()
                }
                
                result = supabase.table('sync_logs').insert(log_data).execute()
                
                if success:
                    print(f"💰 Recorded Perplexity query: ${cost:.3f} for {query_type}")
                else:
                    print(f"❌ Recorded failed Perplexity query: ${cost:.3f} for {query_type}")
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to record query cost: {e}")
            return False
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get comprehensive budget status"""
        spending = self.get_current_spending()
        
        return {
            'budget': {
                'monthly_limit': self.monthly_budget,
                'emergency_reserve': self.emergency_reserve,
                'available_for_regular': self.monthly_budget - self.emergency_reserve,
                'spent_this_month': spending['monthly_total'],
                'remaining_this_month': self.monthly_budget - spending['monthly_total'],
                'percentage_used': (spending['monthly_total'] / self.monthly_budget) * 100
            },
            'daily': {
                'query_limit': self.daily_limit,
                'queries_used': spending['queries_today'],
                'queries_remaining': self.daily_limit - spending['queries_today'],
                'estimated_daily_cost': spending['daily_total']
            },
            'recommendations': self._get_budget_recommendations(spending)
        }
    
    def _get_budget_recommendations(self, spending: Dict[str, float]) -> Dict[str, str]:
        """Get budget recommendations based on current spending"""
        recommendations = {}
        
        # Monthly budget analysis
        monthly_usage = (spending['monthly_total'] / self.monthly_budget) * 100
        
        if monthly_usage > 90:
            recommendations['monthly'] = 'CRITICAL: Over 90% budget used. Emergency queries only.'
        elif monthly_usage > 75:
            recommendations['monthly'] = 'WARNING: Over 75% budget used. High-priority queries only.'
        elif monthly_usage > 50:
            recommendations['monthly'] = 'CAUTION: Over 50% budget used. Monitor spending carefully.'
        else:
            recommendations['monthly'] = 'HEALTHY: Budget usage within normal range.'
        
        # Daily quota analysis
        daily_usage = (spending['queries_today'] / self.daily_limit) * 100
        
        if daily_usage > 80:
            recommendations['daily'] = 'Approaching daily limit. Prioritize essential queries.'
        elif daily_usage > 60:
            recommendations['daily'] = 'Moderate daily usage. Continue monitoring.'
        else:
            recommendations['daily'] = 'Daily usage within healthy range.'
        
        return recommendations

def test_budget_tracker():
    """Test the budget tracking system"""
    print("🧪 Testing Perplexity Budget Tracker")
    print("=" * 40)
    
    tracker = PerplexityBudgetTracker()
    
    # Test budget check
    can_query = tracker.can_make_query('medium')
    print(f"Can make medium priority query: {can_query['can_query']}")
    
    # Test budget status
    status = tracker.get_budget_status()
    print(f"Monthly budget used: {status['budget']['percentage_used']:.1f}%")
    print(f"Daily queries used: {status['daily']['queries_used']}/{status['daily']['query_limit']}")
    
    # Test recording a query
    success = tracker.record_query(0.007, 'test_query', tokens_used=100, success=True)
    print(f"Query recording successful: {success}")

if __name__ == "__main__":
    test_budget_tracker()