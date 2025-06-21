#!/usr/bin/env python3
"""
Perplexity AI Live Contract Discovery System
Uses AI to find and analyze new government opportunities
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from src.config.supabase import get_supabase_admin_client

class PerplexityLiveDiscovery:
    """Perplexity AI for live contract discovery and intelligence"""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.supabase = get_supabase_admin_client()
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment")
    
    def query_perplexity(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:
        """Query Perplexity AI with search capabilities"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama-3.1-sonar-small-128k-online',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.1,
            'search_domain_filter': [
                'sam.gov',
                'usaspending.gov',
                'grants.gov',
                'defense.gov',
                'gsa.gov',
                'congress.gov',
                'whitehouse.gov'
            ],
            'return_citations': True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Perplexity error {response.status_code}: {response.text[:200]}")
                return {}
                
        except Exception as e:
            print(f"❌ Perplexity query failed: {e}")
            return {}
    
    def discover_new_contracts(self) -> List[Dict[str, Any]]:
        """Use AI to discover new government contracts"""
        print("🤖 Using Perplexity to discover new contracts...")
        
        today = datetime.now().strftime('%B %d, %Y')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%B %d, %Y')
        
        prompt = f"""
        Find NEW government contracts, RFPs, and procurement opportunities announced between {yesterday} and {today}.
        
        Search for:
        1. Latest contract awards on USASpending.gov
        2. New RFP postings on SAM.gov
        3. Recent defense contract announcements
        4. New grant opportunities on Grants.gov
        5. GSA schedule additions
        
        For each opportunity found, provide:
        - Contract/Opportunity title
        - Awarding agency
        - Contractor name (if awarded)
        - Value/amount
        - Date announced
        - Brief description
        - Source URL
        - Contract/solicitation number
        
        Format as JSON array with these fields:
        [{{"title": "", "agency": "", "contractor": "", "value": "", "date": "", "description": "", "source_url": "", "contract_number": ""}}]
        
        Focus on contracts over $100,000 and opportunities still open for bidding.
        """
        
        result = self.query_perplexity(prompt, max_tokens=800)
        
        if result.get('choices'):
            content = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            print(f"   ✅ AI discovery complete with {len(citations)} sources")
            
            # Try to extract JSON from response
            opportunities = self.extract_opportunities_from_ai_response(content)
            
            # Add citations as metadata
            for opp in opportunities:
                opp['ai_citations'] = citations
                opp['ai_generated'] = True
                opp['discovery_date'] = datetime.now().isoformat()
            
            return opportunities
        else:
            print("   ❌ No AI response received")
            return []
    
    def extract_opportunities_from_ai_response(self, content: str) -> List[Dict[str, Any]]:
        """Extract structured opportunities from AI response"""
        opportunities = []
        
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                parsed_opps = json.loads(json_str)
                
                for opp in parsed_opps:
                    if isinstance(opp, dict) and opp.get('title'):
                        opportunities.append(opp)
                        
            else:
                # Fallback: parse text manually
                opportunities = self.parse_text_opportunities(content)
                
        except json.JSONDecodeError:
            # Fallback to text parsing
            opportunities = self.parse_text_opportunities(content)
        
        print(f"   📊 Extracted {len(opportunities)} opportunities from AI response")
        return opportunities
    
    def parse_text_opportunities(self, content: str) -> List[Dict[str, Any]]:
        """Parse opportunities from plain text response"""
        opportunities = []
        
        # Split by common delimiters
        sections = content.split('\n\n')
        
        for section in sections:
            if any(keyword in section.lower() for keyword in ['contract', 'rfp', 'grant', 'opportunity', 'award']):
                # Extract basic info using patterns
                lines = section.split('\n')
                
                opp = {
                    'title': '',
                    'agency': '',
                    'contractor': '',
                    'value': '',
                    'date': '',
                    'description': section[:200],
                    'source_url': '',
                    'contract_number': ''
                }
                
                for line in lines:
                    line = line.strip()
                    if line:
                        # Try to identify what this line contains
                        if 'title:' in line.lower() or line.endswith(':'):
                            opp['title'] = line.replace('title:', '').strip()
                        elif '$' in line:
                            opp['value'] = line
                        elif any(agency in line.lower() for agency in ['department', 'agency', 'dod', 'navy', 'army']):
                            opp['agency'] = line
                        elif 'http' in line:
                            opp['source_url'] = line
                
                if opp['title'] or opp['value']:
                    opportunities.append(opp)
        
        return opportunities
    
    def analyze_market_trends(self) -> Dict[str, Any]:
        """Use AI to analyze current market trends"""
        print("📈 Analyzing government contracting market trends...")
        
        prompt = f"""
        Analyze current government contracting market trends for {datetime.now().strftime('%B %Y')}.
        
        Research and provide insights on:
        1. Hot sectors receiving increased funding
        2. Agencies with largest new contract activity
        3. Emerging technologies being prioritized
        4. Small business set-aside trends
        5. Geographic distribution of new awards
        6. Average contract values by sector
        7. Upcoming major solicitations to watch
        
        Include specific examples with dollar amounts and sources.
        Format as structured analysis with data points.
        """
        
        result = self.query_perplexity(prompt, max_tokens=600)
        
        if result.get('choices'):
            analysis = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'analysis': analysis,
                'citations': citations,
                'generated_at': datetime.now().isoformat(),
                'analysis_type': 'market_trends'
            }
        else:
            return {}
    
    def predict_upcoming_opportunities(self, industry: str = None) -> Dict[str, Any]:
        """Use AI to predict upcoming opportunities"""
        print(f"🔮 Predicting upcoming opportunities{f' in {industry}' if industry else ''}...")
        
        industry_filter = f" specifically in the {industry} industry" if industry else ""
        
        prompt = f"""
        Predict upcoming government contracting opportunities{industry_filter} for the next 30-90 days.
        
        Based on:
        1. Historical contract cycles and renewals
        2. Federal budget allocations and spending patterns
        3. Recent agency announcements and priorities
        4. Upcoming fiscal year transitions
        5. Policy initiatives requiring contractor support
        
        Provide:
        - Likely opportunity titles and descriptions
        - Estimated values and timelines
        - Agencies expected to issue solicitations
        - Key requirements and capabilities needed
        - Competitive landscape analysis
        
        Focus on high-value opportunities (>$1M) with strong probability.
        """
        
        result = self.query_perplexity(prompt, max_tokens=600)
        
        if result.get('choices'):
            predictions = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'predictions': predictions,
                'citations': citations,
                'industry_focus': industry,
                'prediction_horizon': '30-90 days',
                'generated_at': datetime.now().isoformat(),
                'analysis_type': 'opportunity_prediction'
            }
        else:
            return {}
    
    def enhance_existing_opportunities(self) -> int:
        """Add AI intelligence to existing opportunities"""
        print("🧠 Enhancing existing opportunities with AI intelligence...")
        
        # Get opportunities without AI intelligence
        opportunities = self.supabase.table('opportunities')\
            .select('*')\
            .is_('intelligence', 'null')\
            .limit(5)\
            .execute()
        
        enhanced_count = 0
        
        for opp in opportunities.data:
            try:
                intelligence = self.generate_opportunity_intelligence(opp)
                
                if intelligence:
                    # Update opportunity with AI intelligence
                    self.supabase.table('opportunities')\
                        .update({'intelligence': intelligence})\
                        .eq('id', opp['id'])\
                        .execute()
                    
                    enhanced_count += 1
                    print(f"   ✅ Enhanced: {opp['title'][:40]}...")
                    
            except Exception as e:
                print(f"   ❌ Failed to enhance {opp.get('id', 'unknown')}: {e}")
        
        return enhanced_count
    
    def generate_opportunity_intelligence(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI intelligence for a specific opportunity"""
        title = opportunity.get('title', '')
        agency = opportunity.get('agency_name', '')
        value = opportunity.get('estimated_value', 0)
        
        prompt = f"""
        Analyze this government opportunity for competitive intelligence:
        
        Title: {title}
        Agency: {agency}
        Value: ${value:,.0f} if value else 'TBD'
        
        Provide strategic analysis:
        1. Market competition level (High/Medium/Low)
        2. Key evaluation criteria likely to be used
        3. Typical incumbent advantages
        4. Small business competitiveness
        5. Past similar awards and patterns
        6. Bid/no-bid recommendation factors
        
        Keep response under 300 words with actionable insights.
        """
        
        result = self.query_perplexity(prompt, max_tokens=400)
        
        if result.get('choices'):
            analysis = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'ai_analysis': analysis,
                'citations': citations,
                'generated_at': datetime.now().isoformat(),
                'model_used': 'llama-3.1-sonar-small-128k-online',
                'analysis_type': 'competitive_intelligence'
            }
        else:
            return {}
    
    def save_ai_discoveries(self, discoveries: List[Dict[str, Any]]) -> int:
        """Save AI-discovered opportunities to database"""
        saved_count = 0
        
        for discovery in discoveries:
            try:
                # Convert AI discovery to opportunity format
                opportunity = {
                    'external_id': f"ai-discovery-{hash(str(discovery))}",
                    'title': discovery.get('title', 'AI Discovered Opportunity')[:500],
                    'description': discovery.get('description', '')[:2000],
                    'agency_name': discovery.get('agency', 'Federal Agency'),
                    'source_type': 'ai_discovery',
                    'source_name': 'Perplexity-AI',
                    'source_url': discovery.get('source_url', ''),
                    'opportunity_number': discovery.get('contract_number', ''),
                    'estimated_value': self.parse_value(discovery.get('value', '')),
                    'relevance_score': 0.9,  # High for AI discoveries
                    'data_quality_score': 0.85,  # Good but needs verification
                    'total_score': 90,
                    'status': 'discovered',
                    'intelligence': {
                        'ai_discovered': True,
                        'discovery_method': 'perplexity_search',
                        'citations': discovery.get('ai_citations', []),
                        'needs_verification': True
                    }
                }
                
                # Check if already exists
                existing = self.supabase.table('opportunities')\
                    .select('id')\
                    .eq('external_id', opportunity['external_id'])\
                    .execute()
                
                if not existing.data:
                    self.supabase.table('opportunities').insert(opportunity).execute()
                    saved_count += 1
                    print(f"   ✅ Saved AI discovery: {opportunity['title'][:50]}...")
                    
            except Exception as e:
                print(f"   ❌ Failed to save AI discovery: {e}")
        
        return saved_count
    
    def parse_value(self, value_str: str) -> float:
        """Parse monetary value from string"""
        if not value_str:
            return None
        
        try:
            import re
            # Extract number and multiplier
            match = re.search(r'[\$]?([0-9,\.]+)\s*(million|billion|M|B|k|thousand)?', value_str, re.IGNORECASE)
            
            if match:
                amount = float(match.group(1).replace(',', ''))
                multiplier = match.group(2)
                
                if multiplier:
                    multiplier = multiplier.lower()
                    if multiplier in ['million', 'm']:
                        amount *= 1000000
                    elif multiplier in ['billion', 'b']:
                        amount *= 1000000000
                    elif multiplier in ['thousand', 'k']:
                        amount *= 1000
                
                return amount
        except:
            pass
        
        return None
    
    def get_financial_market_data(self, query: str) -> Dict[str, Any]:
        """Get financial and market data for government contracting"""
        print(f"💰 Querying financial market data: {query}")
        
        prompt = f"""
        Provide current financial and market data for government contracting related to: {query}
        
        Focus on:
        - Current market trends and financial indicators
        - Government spending patterns and budget allocations
        - Contract award statistics and values
        - Economic factors affecting procurement
        - Industry-specific financial insights
        - Market competition and pricing trends
        
        Include specific numbers, percentages, dollar amounts, and recent data.
        Cite reliable sources like USASpending.gov, CBO, GAO, industry reports.
        
        Format response with clear sections and actionable insights.
        """
        
        result = self.query_perplexity(prompt, max_tokens=800)
        
        if result.get('choices'):
            content = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'query': query,
                'financial_data': content,
                'citations': citations,
                'generated_at': datetime.now().isoformat(),
                'data_type': 'financial_market_analysis'
            }
        else:
            return {'error': 'No financial data available'}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time financial metrics for government contracting"""
        print("📊 Fetching real-time financial metrics...")
        
        prompt = f"""
        Provide current real-time financial metrics for the government contracting market:
        
        1. Average federal contract value (last 30 days)
        2. Total contract awards this month vs last month (with percentage change)
        3. Small business set-aside participation rate
        4. Top 5 spending agencies by dollar volume
        5. Contract competition levels (average bidders per opportunity)
        6. Award processing times and delays
        7. Budget execution rates by major agencies
        8. Sector-wise spending distribution
        
        Include exact numbers with percentage changes where possible.
        Use recent data from USASpending.gov, SAM.gov, and official sources.
        Highlight any significant trends or anomalies.
        """
        
        result = self.query_perplexity(prompt, max_tokens=900)
        
        if result.get('choices'):
            content = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'metrics': content,
                'citations': citations,
                'timestamp': datetime.now().isoformat(),
                'metrics_type': 'real_time_financial'
            }
        else:
            return {'error': 'No real-time metrics available'}
    
    def analyze_sector_performance(self, sector: str = None) -> Dict[str, Any]:
        """Analyze financial performance of specific sectors"""
        sector_focus = f" for the {sector} sector" if sector else " across all sectors"
        print(f"📈 Analyzing sector performance{sector_focus}...")
        
        prompt = f"""
        Analyze current financial performance and trends{sector_focus} in government contracting:
        
        1. Total spending and growth rates (YoY and QoQ)
        2. Average contract values and deal sizes
        3. Market share by major contractors
        4. Profit margins and pricing trends
        5. Win rates and competition intensity
        6. Upcoming budget allocations and priorities
        7. Key financial risks and opportunities
        8. Strategic recommendations for market entry/expansion
        
        Provide specific financial data with sources.
        Include forward-looking insights and market predictions.
        Focus on actionable intelligence for business strategy.
        """
        
        result = self.query_perplexity(prompt, max_tokens=1000)
        
        if result.get('choices'):
            analysis = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'sector': sector or 'all_sectors',
                'performance_analysis': analysis,
                'citations': citations,
                'analysis_date': datetime.now().isoformat(),
                'analysis_type': 'sector_financial_performance'
            }
        else:
            return {'error': 'No sector analysis available'}
    
    def forecast_market_conditions(self, timeframe: str = "90 days") -> Dict[str, Any]:
        """Forecast market conditions and financial trends"""
        print(f"🔮 Forecasting market conditions for next {timeframe}...")
        
        prompt = f"""
        Forecast government contracting market conditions for the next {timeframe}:
        
        Economic Factors:
        - Federal budget outlook and appropriations
        - Interest rates and inflation impacts
        - Economic indicators affecting government spending
        - Political and policy changes affecting procurement
        
        Market Predictions:
        - Expected contract volume and values
        - Sector growth/decline forecasts
        - Competition level changes
        - Pricing trend predictions
        - New opportunity types emerging
        
        Financial Indicators:
        - Budget execution patterns
        - Agency spending velocity
        - Small business participation trends
        - International trade impacts
        
        Provide specific predictions with confidence levels and supporting rationale.
        Include risk factors and scenario analysis.
        """
        
        result = self.query_perplexity(prompt, max_tokens=1000)
        
        if result.get('choices'):
            forecast = result['choices'][0]['message']['content']
            citations = result.get('citations', [])
            
            return {
                'forecast_timeframe': timeframe,
                'market_forecast': forecast,
                'citations': citations,
                'forecast_date': datetime.now().isoformat(),
                'forecast_type': 'market_conditions'
            }
        else:
            return {'error': 'No market forecast available'}
    
    def run_full_ai_discovery(self) -> Dict[str, Any]:
        """Run complete AI-powered discovery session"""
        print("🤖 Starting Perplexity AI Discovery Session")
        print("=" * 50)
        
        results = {}
        
        try:
            # 1. Discover new contracts
            new_contracts = self.discover_new_contracts()
            saved_discoveries = self.save_ai_discoveries(new_contracts)
            results['new_contracts_found'] = len(new_contracts)
            results['new_contracts_saved'] = saved_discoveries
            
            # 2. Analyze market trends
            market_analysis = self.analyze_market_trends()
            results['market_analysis'] = bool(market_analysis)
            
            # 3. Predict upcoming opportunities
            predictions = self.predict_upcoming_opportunities()
            results['predictions_generated'] = bool(predictions)
            
            # 4. Enhance existing opportunities
            enhanced_count = self.enhance_existing_opportunities()
            results['opportunities_enhanced'] = enhanced_count
            
            # 5. Get financial metrics (new)
            financial_metrics = self.get_real_time_metrics()
            results['financial_metrics'] = bool(financial_metrics.get('metrics'))
            
            # 6. Market forecast (new)
            market_forecast = self.forecast_market_conditions()
            results['market_forecast'] = bool(market_forecast.get('market_forecast'))
            
            # Save market intelligence
            if market_analysis or predictions:
                intelligence_report = {
                    'market_trends': market_analysis,
                    'opportunity_predictions': predictions,
                    'financial_metrics': financial_metrics,
                    'market_forecast': market_forecast,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'ai_market_intelligence'
                }
                
                # Could save this to a separate intelligence table
                results['intelligence_report'] = intelligence_report
            
            print(f"\n🎯 AI Discovery Session Complete!")
            print(f"   📊 New contracts found: {results['new_contracts_found']}")
            print(f"   💾 Contracts saved: {results['new_contracts_saved']}")
            print(f"   📈 Market analysis: {'✅' if results['market_analysis'] else '❌'}")
            print(f"   🔮 Predictions: {'✅' if results['predictions_generated'] else '❌'}")
            print(f"   🧠 Enhanced opportunities: {results['opportunities_enhanced']}")
            print(f"   💰 Financial metrics: {'✅' if results['financial_metrics'] else '❌'}")
            print(f"   🔮 Market forecast: {'✅' if results['market_forecast'] else '❌'}")
            
        except Exception as e:
            print(f"❌ AI discovery session failed: {e}")
            results['error'] = str(e)
        
        return results

def main():
    """Test Perplexity live discovery"""
    try:
        discovery = PerplexityLiveDiscovery()
        results = discovery.run_full_ai_discovery()
        
        print(f"\n🤖 Perplexity AI Discovery Complete!")
        print(f"📈 Session results: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        print(f"❌ Perplexity setup failed: {e}")
        print("💡 Make sure PERPLEXITY_API_KEY is set in .env file")

if __name__ == '__main__':
    main()