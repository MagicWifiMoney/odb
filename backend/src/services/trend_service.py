"""
Trend Analysis Service
High-level service for managing trend analysis and anomaly detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import json

from .trend_analysis_engine import (
    TimeSeriesAnalyzer, TrendAggregator, TrendAnalysisConfig,
    TrendResult, AnomalyResult, TrendType, AnomalyType
)
from .cache_service import get_cache, CacheStrategy
from .perplexity_client import get_perplexity_client, QueryType
from ..config.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class TrendAnalysisService:
    """Main service for trend analysis and anomaly detection"""
    
    def __init__(self, config: TrendAnalysisConfig = None):
        self.config = config or TrendAnalysisConfig()
        self.analyzer = TimeSeriesAnalyzer(self.config)
        self.aggregator = TrendAggregator()
        self.cache = get_cache()
        self.supabase = get_supabase_client()
        
    async def analyze_daily_trends(self, days_back: int = 90) -> Dict[str, Any]:
        """Analyze daily trends in opportunity data"""
        logger.info(f"Analyzing daily trends for last {days_back} days")
        
        try:
            # Get opportunity data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            opportunities = await self._fetch_opportunities(start_date, end_date)
            
            if not opportunities:
                return {"error": "No opportunities found in date range"}
            
            # Aggregate data
            daily_data = await self.aggregator.aggregate_opportunities(opportunities, "daily")
            
            if daily_data.empty:
                return {"error": "No aggregated data available"}
            
            # Analyze trends
            trends = {}
            anomalies = []
            
            # Analyze opportunity count trends
            if len(daily_data) >= self.config.min_data_points:
                count_trend = self.analyzer.detect_trend(
                    daily_data, 'analysis_date', 'opportunity_count'
                )
                trends['opportunity_count'] = count_trend.to_dict()
                
                # Detect anomalies in opportunity count
                count_anomalies = self.analyzer.detect_anomalies(
                    daily_data, 'analysis_date', 'opportunity_count'
                )
                anomalies.extend([a.to_dict() for a in count_anomalies])
            
            # Analyze value trends
            if 'total_value' in daily_data.columns and daily_data['total_value'].sum() > 0:
                value_trend = self.analyzer.detect_trend(
                    daily_data, 'analysis_date', 'total_value'
                )
                trends['total_value'] = value_trend.to_dict()
                
                # Detect anomalies in total value
                value_anomalies = self.analyzer.detect_anomalies(
                    daily_data, 'analysis_date', 'total_value'
                )
                anomalies.extend([a.to_dict() for a in value_anomalies])
            
            # Industry trend analysis
            industry_trends = await self._analyze_industry_trends(daily_data)
            
            # Store results in database
            await self._store_trend_analysis(daily_data, trends, anomalies)
            
            # Get AI insights
            ai_insights = await self._get_ai_insights(trends, anomalies, industry_trends)
            
            return {
                "analysis_type": "daily",
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "data_points": len(daily_data),
                "trends": trends,
                "anomalies": anomalies[:10],  # Top 10 anomalies
                "industry_trends": industry_trends,
                "ai_insights": ai_insights,
                "summary": {
                    "total_opportunities": len(opportunities),
                    "avg_daily_opportunities": daily_data['opportunity_count'].mean(),
                    "trend_strength": max([t.get('strength', 0) for t in trends.values()]) if trends else 0,
                    "anomaly_count": len(anomalies)
                }
            }
            
        except Exception as e:
            logger.error(f"Daily trend analysis failed: {e}")
            return {"error": str(e)}
    
    async def analyze_keyword_trends(self, keywords: List[str] = None, days_back: int = 30) -> Dict[str, Any]:
        """Analyze trending keywords and their patterns"""
        logger.info(f"Analyzing keyword trends for {days_back} days")
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            opportunities = await self._fetch_opportunities(start_date, end_date)
            
            if not opportunities:
                return {"error": "No opportunities found"}
            
            # Extract and analyze keywords
            keyword_analysis = await self._analyze_keyword_patterns(opportunities, keywords)
            
            # Get AI-powered keyword expansion
            if keywords:
                ai_keywords = await self._get_ai_keyword_insights(keywords, keyword_analysis)
                keyword_analysis['ai_suggestions'] = ai_keywords
            
            return keyword_analysis
            
        except Exception as e:
            logger.error(f"Keyword trend analysis failed: {e}")
            return {"error": str(e)}
    
    async def detect_anomalies(self, analysis_type: str = "daily", 
                             sensitivity: float = 2.5) -> Dict[str, Any]:
        """Detect anomalies in opportunity data"""
        logger.info(f"Detecting anomalies with sensitivity {sensitivity}")
        
        try:
            # Adjust analyzer sensitivity
            self.analyzer.config.anomaly_threshold = sensitivity
            
            # Get recent data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=60)  # 60 days for good anomaly detection
            
            opportunities = await self._fetch_opportunities(start_date, end_date)
            
            if not opportunities:
                return {"error": "No opportunities found"}
            
            # Aggregate data
            agg_data = await self.aggregator.aggregate_opportunities(opportunities, analysis_type)
            
            if agg_data.empty:
                return {"error": "No aggregated data available"}
            
            # Detect anomalies across different metrics
            all_anomalies = []
            
            for metric in ['opportunity_count', 'total_value', 'avg_value']:
                if metric in agg_data.columns and len(agg_data) >= 20:
                    anomalies = self.analyzer.detect_anomalies(
                        agg_data, 'analysis_date', metric
                    )
                    all_anomalies.extend([a.to_dict() for a in anomalies])
            
            # Sort by severity and recency
            all_anomalies.sort(key=lambda x: (x['severity'], x['timestamp']), reverse=True)
            
            # Get AI analysis of anomalies
            ai_analysis = await self._get_ai_anomaly_analysis(all_anomalies[:5])
            
            return {
                "analysis_type": analysis_type,
                "sensitivity": sensitivity,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "anomalies": all_anomalies[:20],  # Top 20 anomalies
                "ai_analysis": ai_analysis,
                "summary": {
                    "total_anomalies": len(all_anomalies),
                    "high_severity": len([a for a in all_anomalies if a['severity'] > 7]),
                    "recent_anomalies": len([a for a in all_anomalies 
                                           if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > 
                                           datetime.utcnow() - timedelta(days=7)])
                }
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"error": str(e)}
    
    async def get_trend_forecast(self, metric: str, days_ahead: int = 30) -> Dict[str, Any]:
        """Generate trend forecast using historical data"""
        logger.info(f"Generating {days_ahead}-day forecast for {metric}")
        
        try:
            # Get historical data (more data for better forecasting)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=180)
            
            opportunities = await self._fetch_opportunities(start_date, end_date)
            daily_data = await self.aggregator.aggregate_opportunities(opportunities, "daily")
            
            if daily_data.empty or metric not in daily_data.columns:
                return {"error": f"Insufficient data for {metric} forecast"}
            
            # Simple trend-based forecast (can be enhanced with more sophisticated models)
            historical_values = daily_data[metric].values
            
            if len(historical_values) < 30:
                return {"error": "Insufficient historical data for forecasting"}
            
            # Calculate trend
            trend_result = self.analyzer.detect_trend(daily_data, 'analysis_date', metric)
            
            # Generate forecast
            forecast_dates = pd.date_range(
                start=end_date + timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            # Simple linear projection
            last_value = historical_values[-1]
            daily_change = trend_result.slope
            
            forecast_values = []
            confidence_intervals = []
            
            for i in range(days_ahead):
                predicted_value = last_value + (daily_change * (i + 1))
                
                # Add some uncertainty that increases with time
                uncertainty = historical_values.std() * (1 + i * 0.1)
                
                forecast_values.append(predicted_value)
                confidence_intervals.append({
                    "lower": predicted_value - uncertainty,
                    "upper": predicted_value + uncertainty
                })
            
            return {
                "metric": metric,
                "forecast_period": days_ahead,
                "trend_info": trend_result.to_dict(),
                "forecast": {
                    "dates": [d.isoformat() for d in forecast_dates],
                    "values": forecast_values,
                    "confidence_intervals": confidence_intervals
                },
                "model_info": {
                    "type": "linear_trend",
                    "r_squared": trend_result.r_squared,
                    "confidence": trend_result.confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Trend forecasting failed: {e}")
            return {"error": str(e)}
    
    async def _fetch_opportunities(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch opportunities from database"""
        try:
            response = self.supabase.table('opportunities').select(
                'id, title, description, agency_name, estimated_value, posted_date, '
                'due_date, source_type, keywords, total_score'
            ).gte('posted_date', start_date.isoformat()).lte(
                'posted_date', end_date.isoformat()
            ).order('posted_date').execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            return []
    
    async def _analyze_industry_trends(self, daily_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends by industry"""
        industry_trends = {}
        
        for _, row in daily_data.iterrows():
            industry_breakdown = row.get('industry_breakdown', {})
            
            for industry, count in industry_breakdown.items():
                if industry not in industry_trends:
                    industry_trends[industry] = []
                
                industry_trends[industry].append({
                    'date': row['analysis_date'].isoformat(),
                    'count': count
                })
        
        # Analyze trend for each industry
        industry_analysis = {}
        for industry, data_points in industry_trends.items():
            if len(data_points) >= 10:  # Need minimum data for trend analysis
                df = pd.DataFrame(data_points)
                df['date'] = pd.to_datetime(df['date'])
                
                try:
                    trend = self.analyzer.detect_trend(df, 'date', 'count')
                    industry_analysis[industry] = {
                        'trend': trend.to_dict(),
                        'data_points': len(data_points),
                        'latest_count': data_points[-1]['count']
                    }
                except Exception as e:
                    logger.warning(f"Failed to analyze trend for {industry}: {e}")
        
        return industry_analysis
    
    async def _analyze_keyword_patterns(self, opportunities: List[Dict], 
                                      target_keywords: List[str] = None) -> Dict[str, Any]:
        """Analyze keyword patterns and trends"""
        keyword_counts = {}
        daily_keyword_counts = {}
        
        # Extract keywords from opportunities
        for opp in opportunities:
            posted_date = pd.to_datetime(opp['posted_date']).date()
            keywords = opp.get('keywords', [])
            
            if isinstance(keywords, str):
                try:
                    keywords = json.loads(keywords)
                except:
                    keywords = []
            
            if not isinstance(keywords, list):
                continue
            
            # Initialize daily count if needed
            if posted_date not in daily_keyword_counts:
                daily_keyword_counts[posted_date] = {}
            
            # Count keywords
            for keyword in keywords:
                if isinstance(keyword, str) and len(keyword) > 2:
                    keyword = keyword.lower().strip()
                    
                    # Overall count
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                    
                    # Daily count
                    daily_keyword_counts[posted_date][keyword] = \
                        daily_keyword_counts[posted_date].get(keyword, 0) + 1
        
        # Find trending keywords
        trending_keywords = []
        for keyword, total_count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
            if total_count >= 5:  # Minimum threshold
                # Calculate trend
                keyword_series = []
                for date in sorted(daily_keyword_counts.keys()):
                    count = daily_keyword_counts[date].get(keyword, 0)
                    keyword_series.append(count)
                
                if len(keyword_series) >= 7:  # Need at least a week of data
                    # Simple trend calculation
                    recent_avg = sum(keyword_series[-7:]) / 7
                    older_avg = sum(keyword_series[:-7]) / max(1, len(keyword_series) - 7)
                    
                    trend_ratio = recent_avg / max(older_avg, 0.1)
                    
                    trending_keywords.append({
                        'keyword': keyword,
                        'total_count': total_count,
                        'trend_ratio': trend_ratio,
                        'recent_avg': recent_avg,
                        'trend_direction': 'rising' if trend_ratio > 1.2 else 'declining' if trend_ratio < 0.8 else 'stable'
                    })
        
        # Sort by trend ratio
        trending_keywords.sort(key=lambda x: x['trend_ratio'], reverse=True)
        
        return {
            'total_keywords': len(keyword_counts),
            'trending_keywords': trending_keywords[:20],
            'keyword_distribution': dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:30])
        }
    
    async def _get_ai_insights(self, trends: Dict, anomalies: List, 
                              industry_trends: Dict) -> Dict[str, Any]:
        """Get AI-powered insights about trends and anomalies"""
        try:
            client = get_perplexity_client()
            
            # Prepare context for AI analysis
            context = {
                "trends": trends,
                "top_anomalies": anomalies[:5],
                "industry_trends": {k: v for k, v in list(industry_trends.items())[:5]}
            }
            
            query = """
            Analyze the following government opportunity trends and anomalies. Provide insights about:
            1. What the trends indicate about government spending patterns
            2. Significance of any anomalies detected
            3. Potential opportunities or risks for contractors
            4. Industry-specific observations
            5. Recommendations for opportunity tracking
            
            Focus on actionable insights for government contractors.
            """
            
            async with client:
                result = await client.analyze_trends(query, context)
                
                if result and 'choices' in result:
                    ai_text = result['choices'][0]['message']['content']
                    
                    return {
                        "analysis": ai_text,
                        "confidence": 0.8,
                        "model": result.get('model', 'unknown'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
        
        return {"analysis": "AI insights temporarily unavailable", "confidence": 0}
    
    async def _get_ai_keyword_insights(self, keywords: List[str], 
                                     keyword_analysis: Dict) -> Dict[str, Any]:
        """Get AI insights about keyword trends"""
        try:
            client = get_perplexity_client()
            
            context = {
                "target_keywords": keywords,
                "trending_analysis": keyword_analysis.get('trending_keywords', [])[:10]
            }
            
            query = f"""
            Analyze keyword trends in government contracting for: {', '.join(keywords)}
            
            Suggest:
            1. Related keywords to monitor
            2. Emerging trends in these areas
            3. Seasonal patterns to watch for
            4. Opportunities these trends might indicate
            """
            
            async with client:
                result = await client.expand_keywords(keywords, "government_contracting")
                
                if result and 'choices' in result:
                    return {
                        "suggestions": result['choices'][0]['message']['content'],
                        "confidence": 0.8
                    }
            
        except Exception as e:
            logger.warning(f"AI keyword insights failed: {e}")
        
        return {"suggestions": "AI keyword insights temporarily unavailable"}
    
    async def _get_ai_anomaly_analysis(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """Get AI analysis of detected anomalies"""
        try:
            if not anomalies:
                return {"analysis": "No significant anomalies detected"}
            
            client = get_perplexity_client()
            
            context = {"anomalies": anomalies}
            
            query = """
            Analyze these detected anomalies in government opportunity data. 
            Explain what might have caused them and what they might indicate for:
            1. Government spending patterns
            2. Market opportunities
            3. Seasonal or cyclical effects
            4. External factors (policy changes, emergencies, etc.)
            """
            
            async with client:
                result = await client.analyze_trends(query, context)
                
                if result and 'choices' in result:
                    return {
                        "analysis": result['choices'][0]['message']['content'],
                        "anomaly_count": len(anomalies),
                        "confidence": 0.8
                    }
            
        except Exception as e:
            logger.warning(f"AI anomaly analysis failed: {e}")
        
        return {"analysis": "AI anomaly analysis temporarily unavailable"}
    
    async def _store_trend_analysis(self, daily_data: pd.DataFrame, 
                                  trends: Dict, anomalies: List):
        """Store trend analysis results in database"""
        try:
            # Store aggregated daily data
            for _, row in daily_data.iterrows():
                trend_data = {
                    'analysis_date': row['analysis_date'].date(),
                    'analysis_type': 'daily',
                    'opportunity_count': int(row['opportunity_count']),
                    'total_value': float(row['total_value']),
                    'avg_value': float(row['avg_value']),
                    'industry_breakdown': row.get('industry_breakdown', {}),
                    'agency_breakdown': row.get('agency_breakdown', {}),
                    'trending_keywords': row.get('trending_keywords', []),
                    'data_quality_score': float(row.get('data_quality_score', 0))
                }
                
                # Check for anomalies on this date
                date_anomalies = [
                    a for a in anomalies 
                    if pd.to_datetime(a['timestamp']).date() == row['analysis_date'].date()
                ]
                
                if date_anomalies:
                    trend_data['is_anomaly'] = True
                    trend_data['anomaly_score'] = max([a['severity'] for a in date_anomalies])
                    trend_data['anomaly_type'] = date_anomalies[0]['anomaly_type']
                    trend_data['anomaly_description'] = date_anomalies[0]['description']
                
                # Insert or update
                self.supabase.table('trend_analysis').upsert(trend_data).execute()
            
            logger.info(f"Stored {len(daily_data)} trend analysis records")
            
        except Exception as e:
            logger.error(f"Failed to store trend analysis: {e}")

# Create global service instance
_trend_service: Optional[TrendAnalysisService] = None

def get_trend_service() -> TrendAnalysisService:
    """Get the global trend analysis service instance"""
    global _trend_service
    if _trend_service is None:
        _trend_service = TrendAnalysisService()
    return _trend_service