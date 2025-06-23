"""
Compliance Matrix Service
High-level service for managing compliance analysis and assessments
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .compliance_engine import (
    ComplianceMatrixEngine, ComplianceMatrix, ComplianceRequirement, 
    ComplianceAssessment, ComplianceStatus, ComplianceCategory
)
from .cache_service import get_cache, CacheStrategy
from .perplexity_client import get_perplexity_client
from ..config.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class ComplianceService:
    """Main service for compliance matrix analysis"""
    
    def __init__(self):
        self.compliance_engine = ComplianceMatrixEngine()
        self.cache = get_cache()
        self.supabase = get_supabase_client()
        
    async def analyze_opportunity_compliance(self, opportunity_id: str, 
                                           company_id: str = None) -> Dict[str, Any]:
        """Analyze compliance for a specific opportunity"""
        logger.info(f"Analyzing compliance for opportunity {opportunity_id}")
        
        try:
            # Get opportunity data
            opportunity = await self._fetch_opportunity(opportunity_id)
            if not opportunity:
                return {"error": f"Opportunity {opportunity_id} not found"}
            
            # Get company profile
            company_profile = await self._fetch_company_profile(company_id or "default_company")
            
            # Perform compliance analysis
            compliance_matrix = await self.compliance_engine.analyze_opportunity_compliance(
                opportunity, company_profile
            )
            
            # Store results in database
            await self._store_compliance_analysis(compliance_matrix)
            
            # Get AI insights
            ai_insights = await self._get_ai_compliance_insights(compliance_matrix, opportunity)
            
            # Convert to dict format
            result = self._matrix_to_dict(compliance_matrix)
            result['ai_insights'] = ai_insights
            
            return result
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return {"error": str(e)}
    
    async def get_compliance_summary(self, company_id: str = None, 
                                   days_back: int = 30) -> Dict[str, Any]:
        """Get compliance summary across multiple opportunities"""
        logger.info(f"Getting compliance summary for last {days_back} days")
        
        try:
            # Get recent compliance analyses
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            response = self.supabase.table('compliance_matrices').select('*').gte(
                'analysis_date', start_date.isoformat()
            ).lte('analysis_date', end_date.isoformat()).execute()
            
            analyses = response.data if response.data else []
            
            if not analyses:
                return {"error": "No compliance analyses found"}
            
            # Calculate summary statistics
            summary = self._calculate_compliance_summary(analyses)
            
            return summary
            
        except Exception as e:
            logger.error(f"Compliance summary failed: {e}")
            return {"error": str(e)}
    
    async def get_compliance_gaps_report(self, company_id: str = None) -> Dict[str, Any]:
        """Generate compliance gaps report"""
        logger.info("Generating compliance gaps report")
        
        try:
            # Get recent compliance data
            response = self.supabase.table('compliance_matrices').select('*').gte(
                'analysis_date', (datetime.utcnow() - timedelta(days=90)).isoformat()
            ).execute()
            
            analyses = response.data if response.data else []
            
            if not analyses:
                return {"error": "No compliance data available"}
            
            # Analyze gaps across opportunities
            gaps_analysis = self._analyze_compliance_gaps(analyses)
            
            # Get AI recommendations
            ai_recommendations = await self._get_ai_gap_recommendations(gaps_analysis)
            
            return {
                "gaps_analysis": gaps_analysis,
                "ai_recommendations": ai_recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gaps report generation failed: {e}")
            return {"error": str(e)}
    
    async def get_compliance_readiness_score(self, company_id: str = None) -> Dict[str, Any]:
        """Calculate overall compliance readiness score"""
        logger.info("Calculating compliance readiness score")
        
        try:
            # Get company profile
            company_profile = await self._fetch_company_profile(company_id or "default_company")
            
            # Calculate readiness by category
            readiness_scores = {}
            
            for category in ComplianceCategory:
                score = self._calculate_category_readiness(category, company_profile)
                readiness_scores[category.value] = score
            
            # Calculate overall score
            overall_score = sum(readiness_scores.values()) / len(readiness_scores)
            
            # Identify improvement areas
            improvement_areas = [
                category for category, score in readiness_scores.items() 
                if score < 0.6
            ]
            
            # Generate recommendations
            recommendations = self._generate_readiness_recommendations(
                readiness_scores, improvement_areas
            )
            
            return {
                "overall_readiness_score": overall_score,
                "category_scores": readiness_scores,
                "improvement_areas": improvement_areas,
                "recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Readiness score calculation failed: {e}")
            return {"error": str(e)}
    
    async def update_company_profile(self, company_id: str, 
                                   profile_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update company compliance profile"""
        logger.info(f"Updating company profile for {company_id}")
        
        try:
            # Validate profile updates
            validated_updates = self._validate_profile_updates(profile_updates)
            
            # Update database
            response = self.supabase.table('company_profiles').upsert({
                'company_id': company_id,
                'profile_data': validated_updates,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            # Clear cache
            cache_key = f"company_profile_{company_id}"
            await self.cache.delete(cache_key)
            
            return {
                "success": True,
                "message": "Company profile updated successfully",
                "updated_fields": list(validated_updates.keys())
            }
            
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return {"error": str(e)}
    
    async def _fetch_opportunity(self, opportunity_id: str) -> Optional[Dict]:
        """Fetch opportunity data from database"""
        try:
            response = self.supabase.table('opportunities').select('*').eq(
                'id', opportunity_id
            ).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to fetch opportunity {opportunity_id}: {e}")
            return None
    
    async def _fetch_company_profile(self, company_id: str) -> Dict[str, Any]:
        """Fetch company compliance profile"""
        try:
            # Check cache first
            cache_key = f"company_profile_{company_id}"
            cached_profile = await self.cache.get(cache_key, CacheStrategy.SESSION)
            
            if cached_profile:
                return cached_profile
            
            # Fetch from database
            response = self.supabase.table('company_profiles').select('*').eq(
                'company_id', company_id
            ).execute()
            
            if response.data:
                profile = response.data[0].get('profile_data', {})
            else:
                # Create default profile
                profile = self._create_default_company_profile()
            
            # Cache profile
            await self.cache.set(cache_key, profile, CacheStrategy.SESSION)
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to fetch company profile: {e}")
            return self._create_default_company_profile()
    
    def _create_default_company_profile(self) -> Dict[str, Any]:
        """Create default company profile"""
        return {
            "security_clearances": [],
            "certifications": [],
            "experience_years": 5,
            "project_history": [],
            "domain_expertise": [],
            "annual_revenue": 1000000,
            "bonding_capacity": 500000,
            "financial_strength": "good",
            "technical_capabilities": [],
            "technology_stack": [],
            "compliance_certifications": [],
            "regulatory_experience": [],
            "small_business_status": False,
            "sba_certifications": [],
            "performance_metrics": {},
            "sla_history": [],
            "insurance_coverage": [],
            "locations": [],
            "facilities": [],
            "geographic_presence": ["United States"],
            "domestic_capability": True
        }
    
    async def _store_compliance_analysis(self, matrix: ComplianceMatrix):
        """Store compliance analysis in database"""
        try:
            # Store main matrix
            matrix_data = {
                'opportunity_id': matrix.opportunity_id,
                'analysis_date': matrix.analysis_date.isoformat(),
                'overall_compliance_score': matrix.overall_compliance_score,
                'total_effort_estimate': matrix.total_effort_estimate,
                'total_cost_estimate': matrix.total_cost_estimate,
                'risk_level': matrix.risk_level,
                'critical_gaps': matrix.critical_gaps,
                'quick_wins': matrix.quick_wins,
                'recommendations': matrix.recommendations,
                'next_actions': matrix.next_actions,
                'requirements_count': len(matrix.requirements),
                'assessments_count': len(matrix.assessments)
            }
            
            self.supabase.table('compliance_matrices').upsert(matrix_data).execute()
            
            # Store detailed requirements and assessments
            for req in matrix.requirements:
                req_data = {
                    'opportunity_id': matrix.opportunity_id,
                    'requirement_id': req.id,
                    'category': req.category.value,
                    'title': req.title,
                    'description': req.description,
                    'priority': req.priority.value,
                    'mandatory': req.mandatory,
                    'keywords': req.keywords,
                    'verification_method': req.verification_method,
                    'timeline_days': req.timeline_days,
                    'cost_estimate': req.cost_estimate
                }
                
                self.supabase.table('compliance_requirements').upsert(req_data).execute()
            
            for assessment in matrix.assessments:
                assessment_data = {
                    'opportunity_id': matrix.opportunity_id,
                    'requirement_id': assessment.requirement_id,
                    'status': assessment.status.value,
                    'confidence_score': assessment.confidence_score,
                    'evidence': assessment.evidence,
                    'gaps': assessment.gaps,
                    'recommendations': assessment.recommendations,
                    'effort_estimate': assessment.effort_estimate,
                    'cost_estimate': assessment.cost_estimate,
                    'notes': assessment.notes
                }
                
                self.supabase.table('compliance_assessments').upsert(assessment_data).execute()
            
            logger.info(f"Stored compliance analysis for opportunity {matrix.opportunity_id}")
            
        except Exception as e:
            logger.error(f"Failed to store compliance analysis: {e}")
    
    def _matrix_to_dict(self, matrix: ComplianceMatrix) -> Dict[str, Any]:
        """Convert ComplianceMatrix to dictionary"""
        return {
            "opportunity_id": matrix.opportunity_id,
            "analysis_date": matrix.analysis_date.isoformat(),
            "overall_compliance_score": matrix.overall_compliance_score,
            "total_effort_estimate": matrix.total_effort_estimate,
            "total_cost_estimate": matrix.total_cost_estimate,
            "risk_level": matrix.risk_level,
            "critical_gaps": matrix.critical_gaps,
            "quick_wins": matrix.quick_wins,
            "recommendations": matrix.recommendations,
            "next_actions": matrix.next_actions,
            "requirements": [
                {
                    "id": req.id,
                    "category": req.category.value,
                    "title": req.title,
                    "description": req.description,
                    "priority": req.priority.value,
                    "mandatory": req.mandatory,
                    "keywords": req.keywords,
                    "verification_method": req.verification_method,
                    "timeline_days": req.timeline_days,
                    "cost_estimate": req.cost_estimate
                }
                for req in matrix.requirements
            ],
            "assessments": [
                {
                    "requirement_id": assess.requirement_id,
                    "status": assess.status.value,
                    "confidence_score": assess.confidence_score,
                    "evidence": assess.evidence,
                    "gaps": assess.gaps,
                    "recommendations": assess.recommendations,
                    "effort_estimate": assess.effort_estimate,
                    "cost_estimate": assess.cost_estimate
                }
                for assess in matrix.assessments
            ]
        }
    
    def _calculate_compliance_summary(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from multiple analyses"""
        if not analyses:
            return {}
        
        total_analyses = len(analyses)
        avg_compliance_score = sum(a.get('overall_compliance_score', 0) for a in analyses) / total_analyses
        
        # Risk level distribution
        risk_levels = {}
        for analysis in analyses:
            risk = analysis.get('risk_level', 'Unknown')
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        # Most common gaps
        all_gaps = []
        for analysis in analyses:
            all_gaps.extend(analysis.get('critical_gaps', []))
        
        from collections import Counter
        gap_counter = Counter(all_gaps)
        common_gaps = gap_counter.most_common(5)
        
        # Effort and cost totals
        total_effort = sum(a.get('total_effort_estimate', 0) for a in analyses)
        total_cost = sum(a.get('total_cost_estimate', 0) for a in analyses)
        
        return {
            "total_opportunities_analyzed": total_analyses,
            "average_compliance_score": avg_compliance_score,
            "risk_level_distribution": risk_levels,
            "most_common_gaps": common_gaps,
            "total_effort_estimate": total_effort,
            "total_cost_estimate": total_cost,
            "compliance_trend": "improving" if avg_compliance_score > 0.6 else "needs_attention"
        }
    
    def _analyze_compliance_gaps(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Analyze compliance gaps across opportunities"""
        # Category gap analysis
        category_gaps = {}
        
        for analysis in analyses:
            gaps = analysis.get('critical_gaps', [])
            for gap in gaps:
                # Extract category from gap description
                for category in ComplianceCategory:
                    if category.value.replace('_', ' ') in gap.lower():
                        if category.value not in category_gaps:
                            category_gaps[category.value] = 0
                        category_gaps[category.value] += 1
                        break
        
        # Priority gaps
        high_impact_gaps = [
            category for category, count in category_gaps.items() 
            if count >= len(analyses) * 0.3  # Appears in 30%+ of analyses
        ]
        
        return {
            "category_gap_frequency": category_gaps,
            "high_impact_gap_categories": high_impact_gaps,
            "total_gap_instances": sum(category_gaps.values()),
            "opportunities_with_gaps": len([a for a in analyses if a.get('critical_gaps')])
        }
    
    def _calculate_category_readiness(self, category: ComplianceCategory, 
                                    company_profile: Dict[str, Any]) -> float:
        """Calculate readiness score for a specific category"""
        category_fields = {
            ComplianceCategory.SECURITY_CLEARANCE: ["security_clearances", "cleared_personnel"],
            ComplianceCategory.CERTIFICATIONS: ["certifications", "accreditations"],
            ComplianceCategory.EXPERIENCE: ["experience_years", "project_history"],
            ComplianceCategory.FINANCIAL: ["annual_revenue", "bonding_capacity"],
            ComplianceCategory.TECHNICAL: ["technical_capabilities", "technology_stack"],
            ComplianceCategory.LEGAL: ["compliance_certifications", "regulatory_experience"],
            ComplianceCategory.SMALL_BUSINESS: ["small_business_status", "sba_certifications"],
            ComplianceCategory.PERFORMANCE: ["performance_metrics", "sla_history"],
            ComplianceCategory.INSURANCE: ["insurance_coverage"],
            ComplianceCategory.GEOGRAPHIC: ["locations", "facilities", "domestic_capability"]
        }
        
        fields = category_fields.get(category, [])
        field_scores = []
        
        for field in fields:
            value = company_profile.get(field)
            
            if isinstance(value, list):
                score = min(1.0, len(value) / 5)  # Up to 5 items = full score
            elif isinstance(value, bool):
                score = 1.0 if value else 0.0
            elif isinstance(value, (int, float)):
                if field == "experience_years":
                    score = min(1.0, value / 10)  # 10 years = full score
                elif field in ["annual_revenue", "bonding_capacity"]:
                    score = min(1.0, value / 1000000)  # $1M = full score
                else:
                    score = 1.0 if value > 0 else 0.0
            else:
                score = 0.5 if value else 0.0
            
            field_scores.append(score)
        
        return sum(field_scores) / len(field_scores) if field_scores else 0.0
    
    def _generate_readiness_recommendations(self, scores: Dict[str, float], 
                                          improvement_areas: List[str]) -> List[str]:
        """Generate recommendations for improving readiness"""
        recommendations = []
        
        for area in improvement_areas:
            area_recs = {
                "security_clearance": "Initiate security clearance process for key personnel",
                "certifications": "Pursue industry-standard certifications (ISO, CMMI, etc.)",
                "experience": "Document project history and build case studies",
                "financial": "Strengthen financial position and bonding capacity",
                "technical": "Expand technical capabilities and modernize technology stack",
                "legal": "Obtain compliance certifications for key regulations",
                "small_business": "Complete SBA certification process if eligible",
                "performance": "Establish performance metrics and SLA tracking",
                "insurance": "Ensure adequate insurance coverage",
                "geographic": "Establish domestic facilities and presence"
            }
            
            if area in area_recs:
                recommendations.append(area_recs[area])
        
        # Add general recommendations
        avg_score = sum(scores.values()) / len(scores)
        if avg_score < 0.5:
            recommendations.append("Consider comprehensive compliance audit")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _validate_profile_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize profile updates"""
        # Add validation logic here
        validated = {}
        
        for key, value in updates.items():
            if key in self._create_default_company_profile():
                validated[key] = value
        
        return validated
    
    async def _get_ai_compliance_insights(self, matrix: ComplianceMatrix, 
                                        opportunity: Dict) -> Dict[str, Any]:
        """Get AI-powered compliance insights"""
        try:
            client = get_perplexity_client()
            
            context = {
                "opportunity": {
                    "title": opportunity.get('title'),
                    "agency": opportunity.get('agency_name')
                },
                "compliance": {
                    "score": matrix.overall_compliance_score,
                    "risk_level": matrix.risk_level,
                    "critical_gaps": matrix.critical_gaps[:3],
                    "quick_wins": matrix.quick_wins[:3]
                }
            }
            
            query = f"""
            Analyze this government contract compliance assessment and provide strategic insights:
            
            Compliance Score: {matrix.overall_compliance_score:.1%}
            Risk Level: {matrix.risk_level}
            Critical Gaps: {', '.join(matrix.critical_gaps[:3])}
            Quick Wins: {', '.join(matrix.quick_wins[:3])}
            
            Provide:
            1. Compliance strategy recommendations
            2. Risk mitigation approaches
            3. Timeline for addressing critical gaps
            4. Cost-effective compliance improvements
            """
            
            async with client:
                result = await client.get_compliance_insights(query, context)
                
                if result and 'choices' in result:
                    return {
                        "analysis": result['choices'][0]['message']['content'],
                        "confidence": 0.8,
                        "generated_at": datetime.utcnow().isoformat()
                    }
            
        except Exception as e:
            logger.warning(f"AI compliance insights failed: {e}")
        
        return {"analysis": "AI insights temporarily unavailable"}
    
    async def _get_ai_gap_recommendations(self, gaps_analysis: Dict) -> Dict[str, Any]:
        """Get AI recommendations for addressing compliance gaps"""
        try:
            client = get_perplexity_client()
            
            query = f"""
            Based on this compliance gap analysis across multiple government opportunities:
            
            High Impact Gap Categories: {', '.join(gaps_analysis.get('high_impact_gap_categories', []))}
            Total Gap Instances: {gaps_analysis.get('total_gap_instances', 0)}
            
            Recommend a strategic compliance improvement plan focusing on:
            1. Highest impact gaps to address first
            2. Resource allocation priorities
            3. Timeline for implementation
            4. Expected ROI on compliance investments
            """
            
            async with client:
                result = await client.get_business_insights(query, gaps_analysis)
                
                if result and 'choices' in result:
                    return {
                        "recommendations": result['choices'][0]['message']['content'],
                        "confidence": 0.8
                    }
            
        except Exception as e:
            logger.warning(f"AI gap recommendations failed: {e}")
        
        return {"recommendations": "AI recommendations temporarily unavailable"}

# Global service instance
_compliance_service: Optional[ComplianceService] = None

def get_compliance_service() -> ComplianceService:
    """Get the global compliance service instance"""
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService()
    return _compliance_service