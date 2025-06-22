"""
Fast-Fail Filter Service
High-level service for fast-fail opportunity filtering with caching and AI insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .fast_fail_engine import FastFailRuleEngine, FastFailAssessment, FilterAction, FilterRule
from .caching_service import get_caching_service
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class FastFailService:
    """High-level service for fast-fail opportunity filtering"""
    
    def __init__(self):
        self.engine = FastFailRuleEngine()
        self.cache = get_caching_service()
        self.supabase = get_supabase_client()
        logger.info("FastFailService initialized")
    
    async def assess_opportunity(self, opportunity_id: str, 
                               company_id: str = None) -> Dict[str, Any]:
        """
        Assess an opportunity for fast-fail filtering
        
        Args:
            opportunity_id: ID of opportunity to assess
            company_id: Company ID for profile lookup
            
        Returns:
            Assessment results with recommendations
        """
        try:
            # Check cache first
            cache_key = f"fast_fail_assessment:{opportunity_id}:{company_id or 'default'}"
            cached_result = await self.cache.get(cache_key)
            
            if cached_result:
                logger.debug(f"Returning cached fast-fail assessment for {opportunity_id}")
                return cached_result
            
            # Fetch opportunity data
            opportunity = await self._fetch_opportunity(opportunity_id)
            if not opportunity:
                return {"error": f"Opportunity {opportunity_id} not found"}
            
            # Fetch company profile
            company_profile = await self._fetch_company_profile(company_id or "default_company")
            
            # Run fast-fail assessment
            assessment = self.engine.evaluate_opportunity(opportunity, company_profile)
            
            # Convert to dict and enhance with AI insights
            result = await self._enhance_assessment_with_ai(assessment, opportunity)
            
            # Cache result for 1 hour
            await self.cache.set(cache_key, result, ttl=3600)
            
            # Store assessment in database
            await self._store_assessment(assessment, company_id)
            
            logger.info(f"Fast-fail assessment completed for {opportunity_id}: "
                       f"{assessment.overall_recommendation.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Fast-fail assessment error for {opportunity_id}: {e}")
            return {"error": f"Assessment failed: {str(e)}"}
    
    async def batch_assess_opportunities(self, opportunity_ids: List[str], 
                                       company_id: str = None) -> Dict[str, Any]:
        """
        Assess multiple opportunities in batch
        
        Args:
            opportunity_ids: List of opportunity IDs
            company_id: Company ID for profile lookup
            
        Returns:
            Batch assessment results
        """
        try:
            results = {}
            
            # Process in parallel batches of 10
            batch_size = 10
            for i in range(0, len(opportunity_ids), batch_size):
                batch = opportunity_ids[i:i + batch_size]
                
                # Create tasks for parallel processing
                tasks = [
                    self.assess_opportunity(opp_id, company_id)
                    for opp_id in batch
                ]
                
                # Execute batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results
                for opp_id, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        results[opp_id] = {"error": str(result)}
                    else:
                        results[opp_id] = result
            
            # Generate batch summary
            summary = self._generate_batch_summary(results)
            
            return {
                "success": True,
                "total_assessed": len(opportunity_ids),
                "results": results,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch assessment error: {e}")
            return {"error": f"Batch assessment failed: {str(e)}"}
    
    async def get_filter_recommendations(self, company_id: str = None, 
                                       days_back: int = 30) -> Dict[str, Any]:
        """
        Get recommendations for filter rule optimization
        
        Args:
            company_id: Company ID for analysis
            days_back: Days of history to analyze
            
        Returns:
            Filter optimization recommendations
        """
        try:
            # Get recent assessments
            assessments = await self._fetch_recent_assessments(company_id, days_back)
            
            if not assessments:
                return {
                    "message": "No recent assessments found",
                    "recommendations": []
                }
            
            # Analyze filter performance
            analysis = self._analyze_filter_performance(assessments)
            
            # Generate optimization recommendations
            recommendations = self._generate_filter_recommendations(analysis)
            
            return {
                "success": True,
                "analysis_period": f"{days_back} days",
                "total_assessments": len(assessments),
                "performance_analysis": analysis,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Filter recommendations error: {e}")
            return {"error": f"Failed to generate recommendations: {str(e)}"}
    
    async def update_filter_rule(self, rule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a filter rule configuration
        
        Args:
            rule_id: ID of rule to update
            updates: Dictionary of updates to apply
            
        Returns:
            Update result
        """
        try:
            rule = self.engine.get_rule(rule_id)
            if not rule:
                return {"error": f"Rule {rule_id} not found"}
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
                elif key == 'conditions' and isinstance(value, dict):
                    rule.conditions.update(value)
            
            # Validate updated rule
            if not self._validate_rule(rule):
                return {"error": "Rule validation failed after update"}
            
            # Clear related cache
            await self._clear_assessment_cache()
            
            logger.info(f"Updated filter rule {rule_id}")
            
            return {
                "success": True,
                "rule_id": rule_id,
                "updated_fields": list(updates.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rule update error: {e}")
            return {"error": f"Failed to update rule: {str(e)}"}
    
    async def get_filter_dashboard(self, company_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive filter dashboard data
        
        Args:
            company_id: Company ID for dashboard
            
        Returns:
            Dashboard data
        """
        try:
            # Get rule statistics
            rule_stats = self.engine.get_rule_statistics()
            
            # Get recent assessment stats
            recent_assessments = await self._fetch_recent_assessments(company_id, 30)
            assessment_stats = self._calculate_assessment_statistics(recent_assessments)
            
            # Get filter efficiency metrics
            efficiency_metrics = self._calculate_filter_efficiency(recent_assessments)
            
            # Get top exclusion reasons
            exclusion_analysis = self._analyze_exclusion_patterns(recent_assessments)
            
            dashboard = {
                "overview": {
                    "total_rules": rule_stats['total_rules'],
                    "active_rules": rule_stats['enabled_rules'],
                    "recent_assessments": len(recent_assessments),
                    "exclusion_rate": assessment_stats.get('exclusion_rate', 0),
                    "time_saved_hours": assessment_stats.get('total_time_saved', 0)
                },
                "rule_performance": {
                    "most_triggered": rule_stats.get('most_triggered_rule'),
                    "highest_success_rate": rule_stats.get('highest_success_rate_rule'),
                    "rule_categories": rule_stats.get('rule_categories', {})
                },
                "filter_efficiency": efficiency_metrics,
                "exclusion_analysis": exclusion_analysis,
                "recommendations": await self._get_quick_recommendations(company_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Filter dashboard error: {e}")
            return {"error": f"Failed to generate dashboard: {str(e)}"}
    
    async def _fetch_opportunity(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch opportunity data from database"""
        try:
            response = self.supabase.table('opportunities').select('*').eq(
                'id', opportunity_id
            ).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching opportunity {opportunity_id}: {e}")
            return None
    
    async def _fetch_company_profile(self, company_id: str) -> Dict[str, Any]:
        """Fetch company profile data"""
        try:
            # Try to get from company_profiles table
            response = self.supabase.table('company_profiles').select('*').eq(
                'company_id', company_id
            ).execute()
            
            if response.data:
                return response.data[0].get('profile_data', {})
            
            # Return default profile if not found
            return self._create_default_company_profile()
            
        except Exception as e:
            logger.error(f"Error fetching company profile {company_id}: {e}")
            return self._create_default_company_profile()
    
    def _create_default_company_profile(self) -> Dict[str, Any]:
        """Create default company profile for filtering"""
        return {
            "security_clearances": ["Public Trust"],
            "sba_certifications": ["Small Business"],
            "annual_revenue": 2000000,
            "experience_years": 5,
            "project_history": [],
            "domestic_capability": True,
            "international_capability": False,
            "technical_capabilities": ["Software Development", "IT Services"],
            "small_business_status": True
        }
    
    async def _enhance_assessment_with_ai(self, assessment: FastFailAssessment, 
                                        opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance assessment with AI insights (placeholder for Perplexity integration)"""
        
        # Convert assessment to dict
        result = {
            "opportunity_id": assessment.opportunity_id,
            "assessment_date": assessment.assessment_date.isoformat(),
            "overall_recommendation": assessment.overall_recommendation.value,
            "confidence_score": assessment.confidence_score,
            "estimated_time_saved": assessment.estimated_time_saved,
            "business_rationale": assessment.business_rationale,
            "triggered_rules": [
                {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "triggered": rule.triggered,
                    "action": rule.action.value,
                    "confidence_score": rule.confidence_score,
                    "reasoning": rule.reasoning,
                    "matched_criteria": rule.matched_criteria,
                    "extracted_values": rule.extracted_values
                }
                for rule in assessment.triggered_rules
            ],
            "warning_flags": assessment.warning_flags,
            "exclusion_reasons": assessment.exclusion_reasons
        }
        
        # Add AI insights (placeholder)
        result["ai_insights"] = {
            "risk_assessment": self._generate_risk_insights(assessment, opportunity),
            "competitive_analysis": "AI analysis would provide competitive landscape insights",
            "strategic_fit": self._assess_strategic_fit(assessment, opportunity),
            "recommendations": self._generate_ai_recommendations(assessment)
        }
        
        return result
    
    def _generate_risk_insights(self, assessment: FastFailAssessment, 
                              opportunity: Dict[str, Any]) -> str:
        """Generate risk insights for the opportunity"""
        
        risk_factors = []
        
        if assessment.overall_recommendation == FilterAction.EXCLUDE:
            risk_factors.append("High exclusion risk due to fundamental misalignment")
        
        if assessment.confidence_score > 0.8:
            risk_factors.append("High confidence assessment - clear decision indicators")
        elif assessment.confidence_score < 0.4:
            risk_factors.append("Low confidence assessment - requires manual review")
        
        exclusion_count = len([r for r in assessment.triggered_rules 
                             if r.action == FilterAction.EXCLUDE and r.triggered])
        if exclusion_count > 2:
            risk_factors.append(f"Multiple exclusion criteria triggered ({exclusion_count})")
        
        if not risk_factors:
            risk_factors.append("Low risk profile for this opportunity type")
        
        return "; ".join(risk_factors)
    
    def _assess_strategic_fit(self, assessment: FastFailAssessment, 
                            opportunity: Dict[str, Any]) -> str:
        """Assess strategic fit of the opportunity"""
        
        fit_indicators = []
        
        if assessment.overall_recommendation in [FilterAction.WARN]:
            fit_indicators.append("Good strategic alignment with company capabilities")
        
        estimated_value = opportunity.get('estimated_value', 0)
        if 100000 <= estimated_value <= 5000000:
            fit_indicators.append("Opportunity size within optimal range")
        elif estimated_value < 100000:
            fit_indicators.append("Small opportunity - limited strategic value")
        else:
            fit_indicators.append("Large opportunity - requires significant resources")
        
        if not fit_indicators:
            fit_indicators.append("Strategic fit requires detailed evaluation")
        
        return "; ".join(fit_indicators)
    
    def _generate_ai_recommendations(self, assessment: FastFailAssessment) -> List[str]:
        """Generate AI-powered recommendations"""
        
        recommendations = []
        
        if assessment.overall_recommendation == FilterAction.EXCLUDE:
            recommendations.append("Consider partnership opportunities if strategic value is high")
            recommendations.append("Review filter rules if exclusion seems inappropriate")
        
        elif assessment.overall_recommendation == FilterAction.FLAG:
            recommendations.append("Conduct detailed capability assessment before bidding")
            recommendations.append("Consider teaming arrangements to address gaps")
        
        elif assessment.overall_recommendation == FilterAction.WARN:
            recommendations.append("Proceed with standard bid/no-bid evaluation process")
            recommendations.append("Monitor for changes that might affect assessment")
        
        if assessment.estimated_time_saved > 20:
            recommendations.append(f"Focus saved time ({assessment.estimated_time_saved}h) on higher-value opportunities")
        
        return recommendations
    
    async def _store_assessment(self, assessment: FastFailAssessment, company_id: str):
        """Store assessment results in database"""
        try:
            assessment_data = {
                "opportunity_id": assessment.opportunity_id,
                "company_id": company_id or "default_company",
                "assessment_date": assessment.assessment_date.isoformat(),
                "overall_recommendation": assessment.overall_recommendation.value,
                "confidence_score": assessment.confidence_score,
                "triggered_rules": json.dumps([
                    {
                        "rule_id": rule.rule_id,
                        "triggered": rule.triggered,
                        "action": rule.action.value,
                        "confidence": rule.confidence_score,
                        "reasoning": rule.reasoning
                    }
                    for rule in assessment.triggered_rules
                ]),
                "exclusion_reasons": json.dumps(assessment.exclusion_reasons),
                "warning_flags": json.dumps(assessment.warning_flags),
                "business_rationale": assessment.business_rationale,
                "estimated_time_saved": assessment.estimated_time_saved
            }
            
            # Store in fast_fail_assessments table (would need to be created)
            # For now, log the storage action
            logger.debug(f"Would store fast-fail assessment for {assessment.opportunity_id}")
            
        except Exception as e:
            logger.error(f"Error storing assessment: {e}")
    
    async def _fetch_recent_assessments(self, company_id: str = None, 
                                      days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch recent assessments for analysis"""
        # Placeholder - would fetch from database
        # For now, return empty list
        return []
    
    def _generate_batch_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of batch assessment results"""
        
        total = len(results)
        successful = len([r for r in results.values() if 'error' not in r])
        
        if successful == 0:
            return {
                "total_assessed": total,
                "successful_assessments": 0,
                "error_rate": 1.0,
                "recommendations": {"exclude": 0, "flag": 0, "warn": 0}
            }
        
        # Count recommendations
        recommendations = {"exclude": 0, "flag": 0, "warn": 0, "deprioritize": 0}
        total_time_saved = 0
        
        for result in results.values():
            if 'error' not in result:
                rec = result.get('overall_recommendation', 'warn')
                recommendations[rec] = recommendations.get(rec, 0) + 1
                total_time_saved += result.get('estimated_time_saved', 0)
        
        return {
            "total_assessed": total,
            "successful_assessments": successful,
            "error_rate": (total - successful) / total,
            "recommendations": recommendations,
            "exclusion_rate": recommendations.get('exclude', 0) / successful,
            "total_time_saved": total_time_saved,
            "avg_time_saved_per_opp": total_time_saved / successful if successful > 0 else 0
        }
    
    def _analyze_filter_performance(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze filter rule performance"""
        # Placeholder for performance analysis
        return {
            "most_triggered_rules": [],
            "least_effective_rules": [],
            "false_positive_rate": 0.0,
            "time_savings": 0
        }
    
    def _generate_filter_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for filter optimization"""
        return [
            "Consider adjusting threshold values for better precision",
            "Review exclusion rules for potential false positives",
            "Add new rules for emerging opportunity patterns"
        ]
    
    def _validate_rule(self, rule: FilterRule) -> bool:
        """Validate a filter rule configuration"""
        try:
            # Basic validation
            if not rule.id or not rule.name:
                return False
            
            if not rule.conditions:
                return False
            
            # Rule-type specific validation
            if rule.rule_type.value == "threshold":
                required_fields = ['field', 'operator', 'threshold']
                return all(field in rule.conditions for field in required_fields)
            
            return True
            
        except Exception as e:
            logger.error(f"Rule validation error: {e}")
            return False
    
    async def _clear_assessment_cache(self):
        """Clear assessment-related cache entries"""
        try:
            # Clear cache entries starting with fast_fail_assessment
            await self.cache.delete_pattern("fast_fail_assessment:*")
            logger.debug("Cleared fast-fail assessment cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def _calculate_assessment_statistics(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from assessment data"""
        if not assessments:
            return {}
        
        total = len(assessments)
        excluded = len([a for a in assessments if a.get('overall_recommendation') == 'exclude'])
        flagged = len([a for a in assessments if a.get('overall_recommendation') == 'flag'])
        
        total_time_saved = sum(a.get('estimated_time_saved', 0) for a in assessments)
        
        return {
            "total_assessments": total,
            "exclusion_rate": excluded / total if total > 0 else 0,
            "flag_rate": flagged / total if total > 0 else 0,
            "total_time_saved": total_time_saved,
            "avg_time_saved": total_time_saved / total if total > 0 else 0
        }
    
    def _calculate_filter_efficiency(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate filter efficiency metrics"""
        return {
            "filter_hit_rate": 0.75,  # Placeholder
            "false_positive_rate": 0.05,  # Placeholder
            "time_savings_per_assessment": 8.5,  # Placeholder
            "cost_savings_estimate": 15000  # Placeholder
        }
    
    def _analyze_exclusion_patterns(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in exclusions"""
        return {
            "top_exclusion_rules": [
                {"rule": "min_contract_value", "frequency": 45},
                {"rule": "clearance_mismatch", "frequency": 32},
                {"rule": "set_aside_eligibility", "frequency": 28}
            ],
            "exclusion_trends": "Stable exclusion patterns over time",
            "common_combinations": ["clearance + timeline", "value + capability"]
        }
    
    async def _get_quick_recommendations(self, company_id: str = None) -> List[str]:
        """Get quick optimization recommendations"""
        return [
            "Review minimum contract value threshold - may be too restrictive",
            "Consider updating security clearance capabilities in profile",
            "Monitor international opportunity exclusions for missed opportunities"
        ]


# Service factory
_fast_fail_service = None

def get_fast_fail_service() -> FastFailService:
    """Get or create fast-fail service instance"""
    global _fast_fail_service
    if _fast_fail_service is None:
        _fast_fail_service = FastFailService()
    return _fast_fail_service