#!/usr/bin/env python3
"""
Budget-Aware Perplexity Integration - $10/month controlled AI intelligence
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

from perplexity_budget_tracker import PerplexityBudgetTracker
from perplexity_live_discovery import PerplexityLiveDiscovery

class BudgetAwarePerplexity:
    """Budget-controlled Perplexity integration for federal opportunity intelligence"""
    
    def __init__(self):
        self.budget_tracker = PerplexityBudgetTracker()
        self.perplexity = None
        
        # Initialize Perplexity service if API key available
        try:
            if os.getenv('PERPLEXITY_API_KEY'):
                self.perplexity = PerplexityLiveDiscovery()
                print("✅ Perplexity AI service initialized")
            else:
                print("⚠️ PERPLEXITY_API_KEY not found - AI features disabled")
        except Exception as e:
            print(f"⚠️ Perplexity service initialization failed: {e}")
        
        # Query templates optimized for cost efficiency
        self.query_templates = {
            'daily_brief': self._get_daily_brief_template(),
            'agency_deep_dive': self._get_agency_template(),
            'market_trends': self._get_market_trends_template(),
            'urgent_contracts': self._get_urgent_contracts_template(),
            'high_value_analysis': self._get_high_value_template(),
            'competitive_intel': self._get_competitive_intel_template()
        }
        
        print("🎯 Budget-Aware Perplexity Intelligence initialized")
    
    def _get_daily_brief_template(self) -> str:
        """Optimized template for daily intelligence brief"""
        return """
        Search for new federal contract opportunities from the last 24 hours. Focus on:
        1. Urgent or emergency contracts with tight deadlines
        2. High-value opportunities over $5 million
        3. New technology initiatives (AI, cybersecurity, cloud)
        4. Changes in agency procurement priorities
        5. Time-sensitive announcements requiring immediate attention
        
        Return findings in this format:
        - Title: [Contract title]
        - Agency: [Issuing agency]
        - Value: [Estimated value]
        - Deadline: [Response deadline]
        - Urgency: [Why this is time-sensitive]
        """
    
    def _get_agency_template(self) -> str:
        """Template for agency-specific deep dives"""
        return """
        Analyze recent contract activity for {agency}. Research:
        1. New procurement announcements in last 7 days
        2. Shifts in spending priorities or focus areas
        3. Upcoming solicitations or RFPs mentioned in news
        4. Policy changes affecting contracting approach
        5. Major contract awards that indicate future opportunities
        
        Provide actionable intelligence about where {agency} is heading with procurement.
        """
    
    def _get_market_trends_template(self) -> str:
        """Template for market trend analysis"""
        return """
        Analyze current federal contracting market trends for {timeframe}:
        1. Hottest sectors receiving increased funding
        2. Agencies with largest new contract activity
        3. Emerging technologies being prioritized by government
        4. Small business set-aside trends and opportunities
        5. Policy changes impacting procurement landscape
        
        Focus on actionable insights for contract opportunity discovery.
        """
    
    def _get_urgent_contracts_template(self) -> str:
        """Template for urgent contract discovery"""
        return """
        Find federal contracts with urgent deadlines or emergency procurement:
        1. Contracts with responses due within 14 days
        2. Emergency procurement authorizations
        3. Sole-source justifications posted recently
        4. Amendments extending or shortening deadlines
        5. Critical infrastructure or national security contracts
        
        Prioritize high-value, time-sensitive opportunities.
        """
    
    def _get_high_value_template(self) -> str:
        """Template for high-value contract analysis"""
        return """
        Research federal contracts over $10 million from last 30 days:
        1. Major system acquisitions and technology upgrades
        2. Multi-year IDIQ contracts and GSA schedules
        3. Defense and homeland security large procurements
        4. Infrastructure and construction mega-projects
        5. Professional services contracts with high ceilings
        
        Include competitive landscape and incumbent analysis where possible.
        """
    
    def _get_competitive_intel_template(self) -> str:
        """Template for competitive intelligence"""
        return """
        Analyze competitive landscape for {contract_type} contracts:
        1. Major incumbent contractors and their contract histories
        2. Recent protest activity and award patterns
        3. Small business competition and teaming opportunities
        4. Government preferences and evaluation criteria trends
        5. Pricing and capability expectations based on recent awards
        
        Focus on actionable competitive positioning insights.
        """
    
    def run_daily_intelligence_brief(self) -> Dict[str, Any]:
        """Run daily 5-query intelligence brief"""
        print(f"\n🌅 Daily Intelligence Brief - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.perplexity:
            return {'status': 'skipped', 'reason': 'perplexity_not_available'}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'queries_executed': 0,
            'total_cost': 0.0,
            'intelligence': {}
        }
        
        # Define daily intelligence queries
        daily_queries = [
            ('urgent_today', 'urgent_contracts', 'high'),
            ('high_value_new', 'high_value_analysis', 'high'),
            ('agency_focus', 'agency_deep_dive', 'medium'),
            ('market_pulse', 'market_trends', 'medium'),
            ('competitive_edge', 'competitive_intel', 'low')
        ]
        
        for query_name, template_key, priority in daily_queries:
            # Check budget before each query
            budget_check = self.budget_tracker.can_make_query(priority)
            
            if not budget_check['can_query']:
                print(f"   💰 Skipping {query_name}: {budget_check['reason']}")
                results['intelligence'][query_name] = {
                    'status': 'skipped',
                    'reason': budget_check['reason']
                }
                continue
            
            # Execute query
            try:
                query_result = self._execute_templated_query(
                    template_key, 
                    query_name,
                    priority=priority
                )
                
                results['intelligence'][query_name] = query_result
                results['queries_executed'] += 1
                results['total_cost'] += query_result.get('cost', 0)
                
                # Brief delay between queries
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Query {query_name} failed: {e}")
                results['intelligence'][query_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        print(f"\n📊 Daily Brief Complete:")
        print(f"   Queries Executed: {results['queries_executed']}/5")
        print(f"   Total Cost: ${results['total_cost']:.3f}")
        
        return results
    
    def run_weekly_deep_dive(self, focus_agency: str = None) -> Dict[str, Any]:
        """Run weekly deep intelligence analysis"""
        print(f"\n📊 Weekly Deep Dive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.perplexity:
            return {'status': 'skipped', 'reason': 'perplexity_not_available'}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'focus_agency': focus_agency,
            'queries_executed': 0,
            'total_cost': 0.0,
            'analysis': {}
        }
        
        # Rotate through major agencies if none specified
        agencies = ['Department of Defense', 'Department of Homeland Security', 
                   'General Services Administration', 'Department of Veterans Affairs',
                   'Department of Health and Human Services']
        
        if not focus_agency:
            # Rotate based on week of year
            week_num = datetime.now().isocalendar()[1]
            focus_agency = agencies[week_num % len(agencies)]
            results['focus_agency'] = focus_agency
        
        # Weekly analysis queries
        weekly_queries = [
            ('comprehensive_trends', 'market_trends', 'medium'),
            ('agency_intelligence', 'agency_deep_dive', 'high'),
            ('pipeline_analysis', 'high_value_analysis', 'medium')
        ]
        
        for query_name, template_key, priority in weekly_queries:
            budget_check = self.budget_tracker.can_make_query(priority)
            
            if not budget_check['can_query']:
                print(f"   💰 Skipping {query_name}: {budget_check['reason']}")
                results['analysis'][query_name] = {
                    'status': 'skipped',
                    'reason': budget_check['reason']
                }
                continue
            
            try:
                # Customize query for agency focus
                template_vars = {'agency': focus_agency, 'timeframe': 'this month'}
                
                query_result = self._execute_templated_query(
                    template_key,
                    f"{query_name}_{focus_agency.lower().replace(' ', '_')}",
                    template_vars=template_vars,
                    priority=priority
                )
                
                results['analysis'][query_name] = query_result
                results['queries_executed'] += 1
                results['total_cost'] += query_result.get('cost', 0)
                
                time.sleep(3)  # Longer delay for deep analysis
                
            except Exception as e:
                print(f"   ❌ Analysis {query_name} failed: {e}")
                results['analysis'][query_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        print(f"\n📈 Weekly Deep Dive Complete:")
        print(f"   Focus Agency: {focus_agency}")
        print(f"   Queries Executed: {results['queries_executed']}/3")
        print(f"   Total Cost: ${results['total_cost']:.3f}")
        
        return results
    
    def run_emergency_intelligence(self, query_focus: str) -> Dict[str, Any]:
        """Run emergency/high-priority intelligence query"""
        print(f"\n🚨 Emergency Intelligence Query - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.perplexity:
            return {'status': 'skipped', 'reason': 'perplexity_not_available'}
        
        # Check emergency budget allowance
        budget_check = self.budget_tracker.can_make_query('emergency')
        
        if not budget_check['can_query']:
            print(f"   💰 Emergency query blocked: {budget_check['reason']}")
            return {
                'status': 'blocked',
                'reason': budget_check['reason'],
                'budget_status': budget_check['spending']
            }
        
        try:
            # Execute emergency query with custom prompt
            emergency_prompt = f"""
            URGENT: Research federal contract opportunities related to: {query_focus}
            
            Focus on:
            1. Immediate opportunities with tight deadlines
            2. Emergency procurement authorizations
            3. High-value contracts in this area
            4. Recent policy changes or funding announcements
            5. Competitive intelligence and incumbent analysis
            
            Provide actionable intelligence for immediate opportunity pursuit.
            """
            
            result = self._execute_custom_query(
                emergency_prompt,
                f"emergency_{query_focus.lower().replace(' ', '_')}",
                priority='emergency'
            )
            
            print(f"🎯 Emergency intelligence gathered: ${result.get('cost', 0):.3f}")
            return result
            
        except Exception as e:
            print(f"❌ Emergency query failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _execute_templated_query(self, template_key: str, query_id: str, 
                                template_vars: Dict[str, str] = None, 
                                priority: str = 'medium') -> Dict[str, Any]:
        """Execute a query using predefined template"""
        if template_key not in self.query_templates:
            raise ValueError(f"Unknown template: {template_key}")
        
        template = self.query_templates[template_key]
        
        # Apply template variables if provided
        if template_vars:
            template = template.format(**template_vars)
        
        return self._execute_custom_query(template, query_id, priority)
    
    def _execute_custom_query(self, prompt: str, query_id: str, 
                            priority: str = 'medium') -> Dict[str, Any]:
        """Execute a custom Perplexity query with budget tracking"""
        start_time = datetime.now()
        estimated_cost = self.budget_tracker.cost_per_query['estimated_total']
        
        try:
            print(f"   🤖 Executing {query_id} (priority: {priority})")
            
            # Execute Perplexity query with optimized settings
            response = self.perplexity.query_perplexity(
                prompt=prompt,
                max_tokens=400,  # Limit tokens to control costs
                model='llama-3.1-sonar-small-128k-online',  # Cheapest model
                domain_filter=['sam.gov', 'usaspending.gov', 'grants.gov', 
                             'defense.gov', 'gsa.gov', 'fpds.gov'],
                search_recency='7d'  # Focus on recent data
            )
            
            # Extract intelligence from response
            intelligence = self._extract_intelligence(response)
            
            # Calculate actual cost (simplified)
            actual_cost = estimated_cost  # Use estimate for now
            
            # Record successful query
            self.budget_tracker.record_query(
                cost=actual_cost,
                query_type=query_id,
                tokens_used=len(response.get('content', '')),
                success=True
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'success',
                'query_id': query_id,
                'cost': actual_cost,
                'duration': duration,
                'intelligence': intelligence,
                'raw_response': response
            }
            
        except Exception as e:
            # Record failed query
            self.budget_tracker.record_query(
                cost=estimated_cost,
                query_type=query_id,
                success=False,
                error_message=str(e)
            )
            
            raise e
    
    def _extract_intelligence(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured intelligence from Perplexity response"""
        content = response.get('content', '')
        
        # Simple intelligence extraction
        intelligence = {
            'summary': content[:500] + '...' if len(content) > 500 else content,
            'key_findings': [],
            'opportunities_found': 0,
            'actionable_items': []
        }
        
        # Basic parsing for opportunities and findings
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('opportunity' in line.lower() or 'contract' in line.lower()):
                intelligence['key_findings'].append(line)
            if '$' in line and any(word in line.lower() for word in ['million', 'billion', 'value']):
                intelligence['opportunities_found'] += 1
            if any(word in line.lower() for word in ['deadline', 'due', 'urgent', 'immediate']):
                intelligence['actionable_items'].append(line)
        
        return intelligence
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and recommendations"""
        return self.budget_tracker.get_budget_status()

def test_budget_aware_perplexity():
    """Test the budget-aware Perplexity system"""
    print("🧪 Testing Budget-Aware Perplexity Integration")
    print("=" * 50)
    
    ai = BudgetAwarePerplexity()
    
    # Test budget status
    status = ai.get_budget_status()
    print(f"Budget Status: {status['budget']['percentage_used']:.1f}% used")
    
    # Test if we can make queries
    budget_check = ai.budget_tracker.can_make_query('medium')
    print(f"Can make medium priority query: {budget_check['can_query']}")
    
    if budget_check['can_query'] and ai.perplexity:
        print("Running test emergency query...")
        result = ai.run_emergency_intelligence("cybersecurity contracts")
        print(f"Emergency query result: {result.get('status', 'unknown')}")

if __name__ == "__main__":
    test_budget_aware_perplexity()