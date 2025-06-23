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
# Load environment from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

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
    
    def query_perplexity(self, prompt: str, max_tokens: int = 500, model: str = None, 
                         domain_filter: List[str] = None, reasoning_effort: str = None,
                         response_format: Dict[str, Any] = None, search_recency: str = None) -> Dict[str, Any]:
        """Enhanced Perplexity AI query with advanced Sonar capabilities"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Default to sonar-pro for enhanced intelligence
        model = model or 'sonar-pro'
        
        # Enhanced domain filtering for government contracts (max 10)
        default_domains = [
            'sam.gov',
            'usaspending.gov', 
            'grants.gov',
            'defense.gov',
            'gsa.gov',
            'fpds.gov',
            'acquisition.gov',
            'gao.gov',
            'cbo.gov',
            'whitehouse.gov'
        ]
        
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.1,
            'search_domain_filter': domain_filter or default_domains,
            'return_citations': True
        }
        
        # Add advanced features for deeper analysis
        if reasoning_effort:
            payload['reasoning_effort'] = reasoning_effort
            
        if response_format:
            payload['response_format'] = response_format
            
        if search_recency:
            payload['search_recency_filter'] = search_recency
        
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
    
    def enrich_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich opportunity with comprehensive intelligence using Sonar Pro"""
        print(f"🔍 Enriching opportunity: {opportunity.get('title', 'Unknown')[:50]}...")
        
        agency = opportunity.get('agency_name', '')
        title = opportunity.get('title', '')
        value = opportunity.get('estimated_value', 0)
        
        # Structured response format for consistent parsing
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "opportunity_enrichment",
                "schema": {
                    "type": "object",
                    "properties": {
                        "historical_context": {
                            "type": "object",
                            "properties": {
                                "similar_contracts": {"type": "array", "items": {"type": "string"}},
                                "typical_award_amounts": {"type": "string"},
                                "historical_winners": {"type": "array", "items": {"type": "string"}},
                                "award_patterns": {"type": "string"}
                            }
                        },
                        "competitive_analysis": {
                            "type": "object", 
                            "properties": {
                                "competition_level": {"type": "string", "enum": ["Low", "Medium", "High", "Very High"]},
                                "key_competitors": {"type": "array", "items": {"type": "string"}},
                                "winning_strategies": {"type": "array", "items": {"type": "string"}},
                                "barriers_to_entry": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "strategic_insights": {
                            "type": "object",
                            "properties": {
                                "success_probability": {"type": "string"},
                                "key_requirements": {"type": "array", "items": {"type": "string"}},
                                "differentiators": {"type": "array", "items": {"type": "string"}},
                                "risk_factors": {"type": "array", "items": {"type": "string"}},
                                "preparation_checklist": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "market_intelligence": {
                            "type": "object",
                            "properties": {
                                "agency_priorities": {"type": "string"},
                                "budget_trends": {"type": "string"},
                                "upcoming_related_opportunities": {"type": "array", "items": {"type": "string"}},
                                "industry_outlook": {"type": "string"}
                            }
                        }
                    },
                    "required": ["historical_context", "competitive_analysis", "strategic_insights", "market_intelligence"]
                }
            }
        }
        
        prompt = f"""
        Provide comprehensive intelligence analysis for this government contract opportunity:
        
        OPPORTUNITY DETAILS:
        - Title: {title}
        - Agency: {agency} 
        - Estimated Value: ${value:,.0f} if value else 'TBD'
        - Opportunity ID: {opportunity.get('opportunity_number', 'N/A')}
        
        ANALYSIS REQUIRED:
        
        1. HISTORICAL CONTEXT:
        - Find similar contracts from this agency in past 2 years
        - Typical award amounts for this type of work
        - Historical winning contractors and their profiles
        - Award timing and patterns
        
        2. COMPETITIVE ANALYSIS:
        - Assess competition level (consider barriers, complexity, requirements)
        - Identify likely key competitors based on past awards
        - Analyze winning strategies from similar contracts
        - List barriers to entry for new bidders
        
        3. STRATEGIC INSIGHTS:
        - Estimate success probability for different contractor types
        - Identify key technical/business requirements
        - Suggest differentiation strategies
        - Highlight major risk factors
        - Create actionable preparation checklist
        
        4. MARKET INTELLIGENCE:
        - Current agency priorities and initiatives
        - Budget trends affecting this opportunity
        - Related upcoming opportunities to watch
        - Industry outlook for this sector
        
        Base analysis on real data from government spending databases, contract awards, and agency announcements.
        Provide specific, actionable insights rather than generic advice.
        """
        
        result = self.query_perplexity(
            prompt=prompt,
            max_tokens=1500,
            model='sonar-pro',
            reasoning_effort='high',
            response_format=response_format,
            search_recency='month'
        )
        
        if result.get('choices'):
            try:
                content = result['choices'][0]['message']['content']
                # Try to parse as JSON first
                import json
                enrichment_data = json.loads(content)
                
                return {
                    'enrichment': enrichment_data,
                    'citations': result.get('citations', []),
                    'enriched_at': datetime.now().isoformat(),
                    'model_used': 'sonar-pro',
                    'analysis_type': 'comprehensive_opportunity_enrichment'
                }
            except json.JSONDecodeError:
                # Fallback to text analysis
                return {
                    'enrichment': {'analysis': content},
                    'citations': result.get('citations', []),
                    'enriched_at': datetime.now().isoformat(),
                    'model_used': 'sonar-pro',
                    'analysis_type': 'text_opportunity_enrichment'
                }
        else:
            return {'error': 'No enrichment data available'}
    
    def score_opportunity_with_ai(self, opportunity: Dict[str, Any], user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced AI-powered opportunity scoring using Sonar reasoning"""
        print(f"🎯 AI scoring opportunity: {opportunity.get('title', 'Unknown')[:50]}...")
        
        # Response format for structured scoring
        response_format = {
            "type": "json_schema", 
            "json_schema": {
                "name": "opportunity_score",
                "schema": {
                    "type": "object",
                    "properties": {
                        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "score_breakdown": {
                            "type": "object",
                            "properties": {
                                "strategic_fit": {"type": "number", "minimum": 0, "maximum": 100},
                                "competition_level": {"type": "number", "minimum": 0, "maximum": 100},
                                "win_probability": {"type": "number", "minimum": 0, "maximum": 100},
                                "financial_attractiveness": {"type": "number", "minimum": 0, "maximum": 100},
                                "execution_feasibility": {"type": "number", "minimum": 0, "maximum": 100}
                            }
                        },
                        "key_factors": {"type": "array", "items": {"type": "string"}},
                        "risk_assessment": {"type": "string"},
                        "recommendation": {"type": "string", "enum": ["Pursue Aggressively", "Pursue", "Consider", "Monitor", "Pass"]},
                        "reasoning": {"type": "string"},
                        "next_steps": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["overall_score", "score_breakdown", "recommendation", "reasoning"]
                }
            }
        }
        
        user_context = ""
        if user_profile:
            user_context = f"""
            USER/COMPANY PROFILE:
            - Company Size: {user_profile.get('company_size', 'Not specified')}
            - Industry Focus: {user_profile.get('industry_focus', 'Not specified')}
            - Past Performance: {user_profile.get('past_performance', 'Not specified')}
            - Capabilities: {user_profile.get('capabilities', 'Not specified')}
            - Geographic Presence: {user_profile.get('geographic_presence', 'Not specified')}
            """
        
        prompt = f"""
        You are an expert government contract analyst. Score this opportunity based on multiple factors.
        
        OPPORTUNITY TO ANALYZE:
        - Title: {opportunity.get('title', '')}
        - Agency: {opportunity.get('agency_name', '')}
        - Value: ${opportunity.get('estimated_value', 0):,.0f}
        - Due Date: {opportunity.get('due_date', 'Not specified')}
        - Description: {opportunity.get('description', '')[:500]}
        - Location: {opportunity.get('location', 'Not specified')}
        
        {user_context}
        
        SCORING CRITERIA (0-100 scale):
        
        1. STRATEGIC FIT (25%):
        - Alignment with company capabilities and focus areas
        - Market positioning benefits
        - Portfolio diversification value
        - Long-term relationship potential
        
        2. COMPETITION LEVEL (20%):
        - Number of likely qualified bidders
        - Incumbent advantage factors
        - Barriers to entry
        - Market concentration
        
        3. WIN PROBABILITY (25%):
        - Past performance relevance
        - Technical capability match
        - Relationship factors
        - Proposal competitiveness
        
        4. FINANCIAL ATTRACTIVENESS (20%):
        - Contract value vs effort required
        - Profit margin potential
        - Payment terms and cash flow
        - Follow-on opportunity value
        
        5. EXECUTION FEASIBILITY (10%):
        - Resource availability
        - Timeline reasonableness
        - Technical complexity
        - Risk management
        
        Provide detailed analysis based on real market data and government contracting patterns.
        Consider current market conditions, agency priorities, and competitive landscape.
        Give specific, actionable recommendations.
        """
        
        result = self.query_perplexity(
            prompt=prompt,
            max_tokens=1200,
            model='sonar-reasoning-pro',
            reasoning_effort='high',
            response_format=response_format,
            search_recency='month'
        )
        
        if result.get('choices'):
            try:
                content = result['choices'][0]['message']['content']
                import json
                scoring_data = json.loads(content)
                
                return {
                    'ai_score': scoring_data,
                    'citations': result.get('citations', []),
                    'scored_at': datetime.now().isoformat(),
                    'model_used': 'sonar-reasoning-pro',
                    'analysis_type': 'ai_opportunity_scoring'
                }
            except json.JSONDecodeError:
                # Extract numeric score from text if JSON fails
                import re
                score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:out of 100|/100|%)', content)
                fallback_score = float(score_match.group(1)) if score_match else 75
                
                return {
                    'ai_score': {
                        'overall_score': fallback_score,
                        'reasoning': content,
                        'recommendation': 'Consider'
                    },
                    'citations': result.get('citations', []),
                    'scored_at': datetime.now().isoformat(),
                    'model_used': 'sonar-reasoning-pro',
                    'analysis_type': 'text_opportunity_scoring'
                }
        else:
            return {'error': 'No scoring data available'}
    
    def analyze_competitive_landscape(self, naics_codes: List[str], agency: str, timeframe: str = "2years") -> Dict[str, Any]:
        """Analyze competitive landscape for specific market segment"""
        print(f"🏆 Analyzing competitive landscape for {agency} - NAICS: {naics_codes}")
        
        naics_list = ', '.join(naics_codes) if isinstance(naics_codes, list) else str(naics_codes)
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "competitive_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "market_overview": {
                            "type": "object",
                            "properties": {
                                "total_market_size": {"type": "string"},
                                "number_of_contracts": {"type": "string"},
                                "growth_trend": {"type": "string"},
                                "market_concentration": {"type": "string"}
                            }
                        },
                        "top_contractors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "company_name": {"type": "string"},
                                    "market_share": {"type": "string"},
                                    "total_awards": {"type": "string"},
                                    "average_contract_size": {"type": "string"},
                                    "win_rate": {"type": "string"},
                                    "key_strengths": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "maxItems": 10
                        },
                        "market_dynamics": {
                            "type": "object",
                            "properties": {
                                "competitive_intensity": {"type": "string", "enum": ["Low", "Medium", "High", "Very High"]},
                                "barriers_to_entry": {"type": "array", "items": {"type": "string"}},
                                "success_factors": {"type": "array", "items": {"type": "string"}},
                                "emerging_trends": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "opportunities": {
                            "type": "object",
                            "properties": {
                                "market_gaps": {"type": "array", "items": {"type": "string"}},
                                "emerging_niches": {"type": "array", "items": {"type": "string"}},
                                "disruption_potential": {"type": "array", "items": {"type": "string"}},
                                "partnership_opportunities": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "required": ["market_overview", "top_contractors", "market_dynamics", "opportunities"]
                }
            }
        }
        
        prompt = f"""
        Provide comprehensive competitive landscape analysis for government contracting market:
        
        MARKET PARAMETERS:
        - Agency: {agency}
        - NAICS Codes: {naics_list}
        - Analysis Period: Last {timeframe}
        - Focus: Government contract awards and competitive dynamics
        
        ANALYSIS REQUIREMENTS:
        
        1. MARKET OVERVIEW:
        - Total contract value in this market segment
        - Number of contracts awarded
        - Market growth/decline trends
        - Market concentration (is it dominated by few players?)
        
        2. TOP CONTRACTORS (Top 10):
        - Company names and market share
        - Total award amounts
        - Average contract sizes
        - Win rates and bidding patterns
        - Key competitive strengths
        
        3. MARKET DYNAMICS:
        - Competitive intensity assessment
        - Main barriers to entry
        - Critical success factors
        - Emerging trends and disruptions
        
        4. STRATEGIC OPPORTUNITIES:
        - Underserved market segments
        - Emerging technology niches
        - Potential disruption areas
        - Partnership and teaming opportunities
        
        Base analysis on actual USASpending.gov data, SAM.gov awards, and FPDS contract records.
        Focus on actionable competitive intelligence for market entry strategies.
        """
        
        result = self.query_perplexity(
            prompt=prompt,
            max_tokens=1800,
            model='sonar-deep-research',
            reasoning_effort='high',
            response_format=response_format,
            search_recency='month'
        )
        
        if result.get('choices'):
            try:
                content = result['choices'][0]['message']['content']
                import json
                competitive_data = json.loads(content)
                
                return {
                    'competitive_analysis': competitive_data,
                    'citations': result.get('citations', []),
                    'analyzed_at': datetime.now().isoformat(),
                    'parameters': {
                        'agency': agency,
                        'naics_codes': naics_codes,
                        'timeframe': timeframe
                    },
                    'model_used': 'sonar-deep-research',
                    'analysis_type': 'competitive_landscape'
                }
            except json.JSONDecodeError:
                return {
                    'competitive_analysis': {'analysis': content},
                    'citations': result.get('citations', []),
                    'analyzed_at': datetime.now().isoformat(),
                    'parameters': {
                        'agency': agency,
                        'naics_codes': naics_codes,
                        'timeframe': timeframe
                    },
                    'model_used': 'sonar-deep-research',
                    'analysis_type': 'text_competitive_landscape'
                }
        else:
            return {'error': 'No competitive analysis available'}
    
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
    
    def analyze_compliance_requirements(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Automated compliance and requirements analysis for opportunities"""
        title = opportunity.get('title', '')
        agency = opportunity.get('agency_name', '')
        description = opportunity.get('description', '')
        value = opportunity.get('estimated_value', 0)
        
        prompt = f"""
        Analyze compliance and requirements for this government opportunity:
        
        Title: {title}
        Agency: {agency}
        Description: {description[:1000]}
        Estimated Value: ${value:,.0f}
        
        Provide comprehensive compliance analysis:
        
        1. Regulatory Requirements:
           - Federal Acquisition Regulation (FAR) clauses likely to apply
           - Agency-specific requirements and regulations
           - Security clearance requirements (if any)
           - Certification requirements (ISO, CMMI, etc.)
           
        2. Technical Compliance:
           - Technical standards and specifications
           - Performance requirements and metrics
           - Interoperability and integration requirements
           - Documentation and deliverable standards
           
        3. Business Requirements:
           - Small business set-aside eligibility
           - Past performance requirements
           - Financial capacity requirements
           - Bonding and insurance requirements
           
        4. Compliance Checklist:
           - Key deadlines and submission requirements
           - Required certifications and registrations
           - Mandatory pre-proposal activities
           - Risk factors and compliance challenges
           
        5. Preparation Recommendations:
           - Critical compliance preparation steps
           - Timeline for compliance activities
           - Resources needed for compliance
           - Potential compliance risks to mitigate
        
        Focus on actionable compliance guidance with specific regulatory references.
        """
        
        try:
            result = self.query_perplexity(
                prompt,
                max_tokens=1200,
                model='sonar-reasoning-pro',
                domain_filter=['acquisition.gov', 'far.gov', 'sam.gov', 'sba.gov', 'gsa.gov'],
                reasoning_effort='thorough'
            )
            
            if result.get('choices'):
                analysis = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'compliance_analysis': {
                        'regulatory_requirements': {
                            'far_clauses': [],  # Would be extracted from analysis
                            'agency_specific': [],
                            'security_clearance': 'Extracted from analysis',
                            'certifications': []
                        },
                        'technical_compliance': {
                            'standards': [],
                            'performance_metrics': [],
                            'interoperability': 'Extracted from analysis',
                            'documentation': []
                        },
                        'business_requirements': {
                            'set_aside_eligibility': 'Extracted from analysis',
                            'past_performance': 'Extracted from analysis',
                            'financial_capacity': 'Extracted from analysis',
                            'bonding_insurance': 'Extracted from analysis'
                        },
                        'compliance_checklist': [],  # Would be extracted as actionable items
                        'preparation_timeline': {
                            'critical_steps': [],
                            'estimated_timeline': 'Extracted from analysis',
                            'resources_needed': [],
                            'risk_factors': []
                        },
                        'full_analysis': analysis
                    },
                    'citations': citations,
                    'analyzed_at': datetime.now().isoformat(),
                    'model_used': 'sonar-reasoning-pro',
                    'analysis_type': 'compliance_requirements',
                    'opportunity_id': opportunity.get('id')
                }
            else:
                return {'error': 'No compliance analysis available'}
                
        except Exception as e:
            return {'error': f'Compliance analysis failed: {str(e)}'}
    
    def generate_smart_alerts(self, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate smart opportunity alerts with context and reasoning"""
        user_capabilities = user_profile.get('capabilities', []) if user_profile else []
        user_focus = user_profile.get('industry_focus', []) if user_profile else []
        
        capabilities_str = ", ".join(user_capabilities) if user_capabilities else "technology services"
        focus_str = ", ".join(user_focus) if user_focus else "government contracting"
        
        prompt = f"""
        Generate smart opportunity alerts for a contractor with:
        Capabilities: {capabilities_str}
        Focus Areas: {focus_str}
        
        Based on current market intelligence, identify:
        
        1. High-Priority Alerts:
           - Imminent opportunities matching capabilities
           - Time-sensitive pre-solicitation activities
           - Industry day announcements
           - Draft RFP releases requiring early engagement
           
        2. Strategic Opportunities:
           - Large upcoming procurements in focus areas
           - Multi-year contract vehicles opening
           - New agency initiatives creating opportunities
           - Market shifts creating competitive advantages
           
        3. Competitive Intelligence:
           - Incumbent contract expirations
           - Protest outcomes affecting recompetes
           - New entrant opportunities
           - Partnership and teaming opportunities
           
        4. Market Trends:
           - Budget allocation shifts
           - Policy changes affecting procurement
           - Technology trends driving requirements
           - Emerging opportunity categories
           
        5. Action Items:
           - Specific actions to take this week
           - Capability development recommendations
           - Relationship building priorities
           - Proposal preparation activities
        
        Include specific opportunity titles, agencies, values, and deadlines where available.
        Prioritize by urgency and strategic value.
        """
        
        try:
            result = self.query_perplexity(
                prompt,
                max_tokens=1000,
                model='sonar-pro',
                search_recency='week'
            )
            
            if result.get('choices'):
                alerts = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'smart_alerts': {
                        'user_profile': user_profile,
                        'alert_content': alerts,
                        'high_priority_count': 0,  # Would be extracted from analysis
                        'strategic_count': 0,
                        'intelligence_updates': 0,
                        'action_items': []  # Would be extracted as actionable items
                    },
                    'citations': citations,
                    'generated_at': datetime.now().isoformat(),
                    'model_used': 'sonar-pro',
                    'alert_type': 'smart_contextual',
                    'recency': 'week'
                }
            else:
                return {'error': 'No alerts available'}
                
        except Exception as e:
            return {'error': f'Smart alerts failed: {str(e)}'}
    
    def analyze_market_trends(self, timeframe: str = "6months", focus_areas: List[str] = None) -> Dict[str, Any]:
        """Advanced trend analysis and market intelligence"""
        focus_str = ", ".join(focus_areas) if focus_areas else "government contracting"
        
        prompt = f"""
        Conduct comprehensive trend analysis for government contracting markets over the {timeframe} period.
        
        Focus Areas: {focus_str}
        
        Provide detailed analysis covering:
        
        1. SPENDING TRENDS:
           - Budget allocation shifts by agency and category
           - Contract value trends (average, median, growth rates)
           - Emerging spending priorities and initiatives
           - Seasonal patterns and budget cycle impacts
           
        2. TECHNOLOGY TRENDS:
           - Fastest growing technology categories
           - Digital transformation initiatives
           - Cloud adoption and modernization trends
           - AI/ML, cybersecurity, and emerging tech spending
           
        3. MARKET DYNAMICS:
           - Small business participation trends
           - Competition intensity changes
           - New entrant success patterns
           - Geographic distribution shifts
           
        4. REGULATORY CHANGES:
           - New procurement policies and their impact
           - Compliance requirement evolution
           - Set-aside program changes
           - Security and clearance requirement trends
           
        5. OPPORTUNITY PATTERNS:
           - Contract vehicle utilization trends
           - Award timing and cycle patterns
           - Protest and recompete frequency
           - Multi-award vs single-award trends
           
        6. FORECASTING:
           - Predicted growth areas for next 12 months
           - Emerging opportunity categories
           - Market risks and challenges ahead
           - Strategic recommendations for contractors
        
        Include specific data points, percentages, and concrete examples.
        Focus on actionable insights and forward-looking intelligence.
        """
        
        try:
            result = self.query_perplexity(
                prompt,
                max_tokens=1500,
                model='sonar-deep-research',
                domain_filter=['usaspending.gov', 'sam.gov', 'cbo.gov', 'whitehouse.gov', 'gao.gov'],
                reasoning_effort='thorough',
                search_recency='month'
            )
            
            if result.get('choices'):
                analysis = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'trend_analysis': {
                        'timeframe': timeframe,
                        'focus_areas': focus_areas,
                        'spending_trends': {
                            'analysis': analysis,
                            'budget_shifts': [],  # Would be extracted from analysis
                            'value_trends': {},
                            'emerging_priorities': []
                        },
                        'technology_trends': {
                            'fastest_growing': [],
                            'digital_transformation': 'Extracted from analysis',
                            'cloud_adoption': 'Extracted from analysis',
                            'emerging_tech': []
                        },
                        'market_dynamics': {
                            'small_business_trends': 'Extracted from analysis',
                            'competition_changes': 'Extracted from analysis',
                            'geographic_shifts': [],
                            'new_entrant_patterns': []
                        },
                        'regulatory_impact': {
                            'policy_changes': [],
                            'compliance_evolution': 'Extracted from analysis',
                            'security_trends': 'Extracted from analysis'
                        },
                        'opportunity_patterns': {
                            'contract_vehicles': [],
                            'award_timing': 'Extracted from analysis',
                            'protest_trends': 'Extracted from analysis'
                        },
                        'market_forecast': {
                            'growth_predictions': [],
                            'emerging_categories': [],
                            'market_risks': [],
                            'strategic_recommendations': []
                        },
                        'full_analysis': analysis
                    },
                    'citations': citations,
                    'analyzed_at': datetime.now().isoformat(),
                    'model_used': 'sonar-deep-research',
                    'analysis_type': 'comprehensive_trend_analysis'
                }
            else:
                return {'error': 'No trend analysis available'}
                
        except Exception as e:
            return {'error': f'Trend analysis failed: {str(e)}'}
    
    def forecast_market_conditions(self, horizon: str = "12months") -> Dict[str, Any]:
        """AI-powered market forecasting and condition prediction"""
        current_date = datetime.now().strftime('%B %Y')
        
        prompt = f"""
        Provide AI-powered market forecasting for government contracting over the next {horizon}.
        Current date: {current_date}
        
        Generate comprehensive forecast covering:
        
        1. MARKET CONDITIONS FORECAST:
           - Overall market size and growth projections
           - Economic factors affecting government spending
           - Budget outlook and appropriations forecasts
           - Political and policy impacts on contracting
           
        2. AGENCY-SPECIFIC PREDICTIONS:
           - Department of Defense modernization priorities
           - Civilian agency digital transformation plans
           - Infrastructure and climate spending patterns
           - Healthcare and social services contracting trends
           
        3. TECHNOLOGY ADOPTION FORECAST:
           - AI/ML integration acceleration timeline
           - Cloud migration completion phases
           - Cybersecurity investment priorities
           - Emerging technology adoption curves
           
        4. COMPETITIVE LANDSCAPE EVOLUTION:
           - Market concentration changes
           - New player entry predictions
           - Partnership and acquisition trends
           - Small business opportunity evolution
           
        5. OPPORTUNITY PIPELINE FORECAST:
           - High-value contract recompetes scheduled
           - New program launches and initiatives
           - IDIQ and contract vehicle refreshes
           - Set-aside and small business trends
           
        6. RISK FACTORS AND MITIGATION:
           - Budget uncertainty impacts
           - Protest and delay predictions
           - Supply chain and vendor risks
           - Compliance and regulatory challenges
           
        7. STRATEGIC RECOMMENDATIONS:
           - Positioning strategies for different contractor types
           - Capability development priorities
           - Partnership and teaming recommendations
           - Investment and resource allocation guidance
        
        Base forecasts on historical patterns, current indicators, and announced government initiatives.
        Provide confidence levels and scenario planning where appropriate.
        """
        
        try:
            result = self.query_perplexity(
                prompt,
                max_tokens=1400,
                model='sonar-reasoning-pro',
                reasoning_effort='thorough',
                search_recency='week'
            )
            
            if result.get('choices'):
                forecast = result['choices'][0]['message']['content']
                citations = result.get('citations', [])
                
                return {
                    'market_forecast': {
                        'forecast_horizon': horizon,
                        'current_period': current_date,
                        'market_conditions': {
                            'growth_projections': 'Extracted from forecast',
                            'economic_factors': [],
                            'budget_outlook': 'Extracted from forecast',
                            'policy_impacts': []
                        },
                        'agency_predictions': {
                            'defense_priorities': [],
                            'civilian_plans': [],
                            'infrastructure_spending': 'Extracted from forecast',
                            'healthcare_trends': []
                        },
                        'technology_adoption': {
                            'ai_ml_timeline': 'Extracted from forecast',
                            'cloud_migration': 'Extracted from forecast',
                            'cybersecurity_priorities': [],
                            'emerging_tech_curves': []
                        },
                        'competitive_evolution': {
                            'concentration_changes': 'Extracted from forecast',
                            'new_entrants': [],
                            'partnership_trends': [],
                            'small_business_evolution': 'Extracted from forecast'
                        },
                        'opportunity_pipeline': {
                            'high_value_recompetes': [],
                            'new_programs': [],
                            'contract_vehicles': [],
                            'set_aside_trends': 'Extracted from forecast'
                        },
                        'risk_factors': {
                            'budget_uncertainty': 'Extracted from forecast',
                            'protest_predictions': [],
                            'supply_chain_risks': [],
                            'compliance_challenges': []
                        },
                        'strategic_recommendations': {
                            'positioning_strategies': [],
                            'capability_priorities': [],
                            'partnership_recommendations': [],
                            'investment_guidance': []
                        },
                        'full_forecast': forecast
                    },
                    'citations': citations,
                    'generated_at': datetime.now().isoformat(),
                    'model_used': 'sonar-reasoning-pro',
                    'forecast_type': 'comprehensive_market_forecast',
                    'confidence_level': 'high'
                }
            else:
                return {'error': 'No market forecast available'}
                
        except Exception as e:
            return {'error': f'Market forecasting failed: {str(e)}'}

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