"""
Fast-Fail Filter Rule Engine
Automated filtering system to quickly identify opportunities to avoid/skip
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
import logging
import json
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class FilterRuleType(Enum):
    """Types of filter rules"""
    EXCLUSION = "exclusion"  # Rules that exclude opportunities
    REQUIREMENT = "requirement"  # Rules that require certain criteria
    THRESHOLD = "threshold"  # Rules based on numeric thresholds
    PATTERN = "pattern"  # Rules based on text patterns
    BUSINESS_LOGIC = "business_logic"  # Complex business rules

class FilterPriority(Enum):
    """Priority levels for filter rules"""
    CRITICAL = "critical"  # Must be applied, high confidence
    HIGH = "high"  # Important filters
    MEDIUM = "medium"  # Standard filters
    LOW = "low"  # Optional filters

class FilterAction(Enum):
    """Actions to take when filter is triggered"""
    EXCLUDE = "exclude"  # Completely exclude opportunity
    FLAG = "flag"  # Flag for review but don't exclude
    DEPRIORITIZE = "deprioritize"  # Lower priority in rankings
    WARN = "warn"  # Issue warning but continue

@dataclass
class FilterRule:
    """Individual filter rule definition"""
    id: str
    name: str
    description: str
    rule_type: FilterRuleType
    priority: FilterPriority
    action: FilterAction
    conditions: Dict[str, Any]
    enabled: bool = True
    created_date: datetime = field(default_factory=datetime.now)
    last_applied: Optional[datetime] = None
    success_count: int = 0
    total_applications: int = 0

@dataclass
class FilterResult:
    """Result of applying a filter rule"""
    rule_id: str
    rule_name: str
    triggered: bool
    action: FilterAction
    confidence_score: float
    reasoning: str
    matched_criteria: List[str] = field(default_factory=list)
    extracted_values: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FastFailAssessment:
    """Complete fast-fail assessment for an opportunity"""
    opportunity_id: str
    assessment_date: datetime
    overall_recommendation: FilterAction
    confidence_score: float
    triggered_rules: List[FilterResult]
    warning_flags: List[str]
    exclusion_reasons: List[str]
    business_rationale: str
    estimated_time_saved: int  # Hours
    next_review_date: Optional[datetime] = None

class FastFailRuleEngine:
    """Core engine for applying fast-fail filter rules"""
    
    def __init__(self):
        self.rules = {}
        self.load_default_rules()
        logger.info("FastFailRuleEngine initialized")
    
    def load_default_rules(self):
        """Load default set of fast-fail filter rules"""
        
        # Business Size Filters
        self.add_rule(FilterRule(
            id="min_contract_value",
            name="Minimum Contract Value",
            description="Exclude contracts below minimum viable value",
            rule_type=FilterRuleType.THRESHOLD,
            priority=FilterPriority.HIGH,
            action=FilterAction.EXCLUDE,
            conditions={
                "field": "estimated_value",
                "operator": "lt",
                "threshold": 50000,
                "currency": "USD"
            }
        ))
        
        self.add_rule(FilterRule(
            id="max_contract_value",
            name="Maximum Contract Value Capacity",
            description="Flag contracts above company capacity",
            rule_type=FilterRuleType.THRESHOLD,
            priority=FilterPriority.MEDIUM,
            action=FilterAction.FLAG,
            conditions={
                "field": "estimated_value",
                "operator": "gt",
                "threshold": 10000000,
                "currency": "USD"
            }
        ))
        
        # Geographic Restrictions
        self.add_rule(FilterRule(
            id="international_restriction",
            name="International Work Restriction",
            description="Exclude international contracts if not capable",
            rule_type=FilterRuleType.PATTERN,
            priority=FilterPriority.CRITICAL,
            action=FilterAction.EXCLUDE,
            conditions={
                "fields": ["description", "requirements", "location"],
                "exclude_patterns": [
                    r"international", r"overseas", r"outside\s+united\s+states",
                    r"oconus", r"foreign", r"embassy", r"consulate"
                ],
                "case_sensitive": False
            }
        ))
        
        # Security Clearance Requirements
        self.add_rule(FilterRule(
            id="clearance_mismatch",
            name="Security Clearance Mismatch",
            description="Exclude if security clearance requirements not met",
            rule_type=FilterRuleType.REQUIREMENT,
            priority=FilterPriority.CRITICAL,
            action=FilterAction.EXCLUDE,
            conditions={
                "fields": ["description", "requirements"],
                "clearance_patterns": [
                    r"top\s+secret", r"ts/sci", r"polygraph", r"special\s+access",
                    r"secret.*clearance.*polygraph", r"top.*secret.*clearance",
                    r"top\s+secret\s+security\s+clearance", r"active\s+top\s+secret"
                ],
                "required_clearance_levels": ["top secret", "ts/sci"]  # Required to trigger exclusion
            }
        ))
        
        # Industry/Domain Exclusions
        self.add_rule(FilterRule(
            id="excluded_industries",
            name="Excluded Industry Sectors",
            description="Exclude contracts in industries we don't serve",
            rule_type=FilterRuleType.EXCLUSION,
            priority=FilterPriority.HIGH,
            action=FilterAction.EXCLUDE,
            conditions={
                "excluded_keywords": [
                    "weapons", "munitions", "military hardware",
                    "tobacco", "gambling", "adult entertainment"
                ],
                "fields": ["description", "agency_name", "title"],
                "threshold": 0.16  # Single keyword match (1/6 = 0.16)
            }
        ))
        
        # Technical Capability Filters
        self.add_rule(FilterRule(
            id="technology_mismatch",
            name="Technology Stack Mismatch",
            description="Flag contracts requiring technologies we don't support",
            rule_type=FilterRuleType.PATTERN,
            priority=FilterPriority.MEDIUM,
            action=FilterAction.FLAG,
            conditions={
                "unsupported_tech": [
                    "cobol", "fortran", "mainframe", "as400",
                    "legacy system", "proprietary platform"
                ],
                "fields": ["description", "requirements", "technical_specs"],
                "match_threshold": 2  # Number of matches to trigger
            }
        ))
        
        # Timeline Filters
        self.add_rule(FilterRule(
            id="insufficient_timeline",
            name="Insufficient Response Timeline",
            description="Exclude if insufficient time to prepare quality response",
            rule_type=FilterRuleType.THRESHOLD,
            priority=FilterPriority.HIGH,
            action=FilterAction.EXCLUDE,
            conditions={
                "field": "days_until_due",
                "operator": "lt",
                "threshold": 7,
                "exceptions": ["incumbent", "existing_relationship"]
            }
        ))
        
        # Set-Aside Restrictions
        self.add_rule(FilterRule(
            id="set_aside_eligibility",
            name="Set-Aside Eligibility Check",
            description="Exclude set-asides we're not eligible for",
            rule_type=FilterRuleType.BUSINESS_LOGIC,
            priority=FilterPriority.CRITICAL,
            action=FilterAction.EXCLUDE,
            conditions={
                "company_certifications": ["small_business"],
                "excluded_set_asides": ["8a_only", "hubzone_only", "wosb_only"],
                "fields": ["set_aside_type", "description", "requirements"]
            }
        ))
        
        # Past Performance Filters
        self.add_rule(FilterRule(
            id="past_performance_requirement",
            name="Past Performance Requirements",
            description="Flag contracts requiring specific past performance",
            rule_type=FilterRuleType.REQUIREMENT,
            priority=FilterPriority.MEDIUM,
            action=FilterAction.FLAG,
            conditions={
                "required_experience": {
                    "minimum_contracts": 3,
                    "minimum_value": 1000000,
                    "domain_match": True
                },
                "evaluation_weight": 0.3,  # 30% or more weight on past performance
                "trigger_patterns": [  # Only check if these patterns are found
                    r"past\s+performance", r"prior\s+experience", r"similar\s+contracts",
                    r"reference\s+projects", r"demonstrated\s+experience", r"proven\s+track"
                ],
                "fields": ["description", "requirements", "evaluation_criteria"]
            }
        ))
        
        # Competition Level Filters
        self.add_rule(FilterRule(
            id="high_competition_warning",
            name="High Competition Warning",
            description="Flag opportunities with extremely high competition",
            rule_type=FilterRuleType.THRESHOLD,
            priority=FilterPriority.LOW,
            action=FilterAction.WARN,
            conditions={
                "competition_indicators": [
                    "broad_market_research", "industry_day", "multiple_awards",
                    "unrestricted_competition"
                ],
                "estimated_bidders": 20
            }
        ))
        
        logger.info(f"Loaded {len(self.rules)} default filter rules")
    
    def add_rule(self, rule: FilterRule):
        """Add or update a filter rule"""
        self.rules[rule.id] = rule
        logger.debug(f"Added filter rule: {rule.id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a filter rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.debug(f"Removed filter rule: {rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[FilterRule]:
        """Get a specific filter rule"""
        return self.rules.get(rule_id)
    
    def list_rules(self, enabled_only: bool = True) -> List[FilterRule]:
        """List all filter rules"""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        return sorted(rules, key=lambda r: (r.priority.value, r.name))
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any], 
                           company_profile: Dict[str, Any] = None) -> FastFailAssessment:
        """Evaluate an opportunity against all filter rules"""
        
        triggered_rules = []
        warning_flags = []
        exclusion_reasons = []
        
        # Apply each enabled rule
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            result = self._apply_rule(rule, opportunity, company_profile)
            
            # Update rule statistics
            rule.total_applications += 1
            rule.last_applied = datetime.now()
            
            if result.triggered:
                triggered_rules.append(result)
                rule.success_count += 1
                
                if result.action == FilterAction.EXCLUDE:
                    exclusion_reasons.append(f"{rule.name}: {result.reasoning}")
                elif result.action in [FilterAction.FLAG, FilterAction.WARN]:
                    warning_flags.append(f"{rule.name}: {result.reasoning}")
        
        # Determine overall recommendation
        overall_recommendation = self._determine_overall_recommendation(triggered_rules)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(triggered_rules)
        
        # Generate business rationale
        business_rationale = self._generate_business_rationale(
            triggered_rules, overall_recommendation
        )
        
        # Estimate time saved
        estimated_time_saved = self._estimate_time_saved(overall_recommendation, opportunity)
        
        assessment = FastFailAssessment(
            opportunity_id=opportunity.get('id', 'unknown'),
            assessment_date=datetime.now(),
            overall_recommendation=overall_recommendation,
            confidence_score=confidence_score,
            triggered_rules=triggered_rules,
            warning_flags=warning_flags,
            exclusion_reasons=exclusion_reasons,
            business_rationale=business_rationale,
            estimated_time_saved=estimated_time_saved
        )
        
        logger.info(f"Fast-fail assessment complete for {assessment.opportunity_id}: "
                   f"{overall_recommendation.value} (confidence: {confidence_score:.2f})")
        
        return assessment
    
    def _apply_rule(self, rule: FilterRule, opportunity: Dict[str, Any], 
                   company_profile: Dict[str, Any] = None) -> FilterResult:
        """Apply a specific rule to an opportunity"""
        
        try:
            if rule.rule_type == FilterRuleType.THRESHOLD:
                return self._apply_threshold_rule(rule, opportunity)
            
            elif rule.rule_type == FilterRuleType.PATTERN:
                return self._apply_pattern_rule(rule, opportunity)
            
            elif rule.rule_type == FilterRuleType.EXCLUSION:
                return self._apply_exclusion_rule(rule, opportunity)
            
            elif rule.rule_type == FilterRuleType.REQUIREMENT:
                return self._apply_requirement_rule(rule, opportunity, company_profile)
            
            elif rule.rule_type == FilterRuleType.BUSINESS_LOGIC:
                return self._apply_business_logic_rule(rule, opportunity, company_profile)
            
            else:
                logger.warning(f"Unknown rule type: {rule.rule_type}")
                return FilterResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    triggered=False,
                    action=rule.action,
                    confidence_score=0.0,
                    reasoning="Unknown rule type"
                )
        
        except Exception as e:
            logger.error(f"Error applying rule {rule.id}: {e}")
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning=f"Rule application error: {str(e)}"
            )
    
    def _apply_threshold_rule(self, rule: FilterRule, 
                            opportunity: Dict[str, Any]) -> FilterResult:
        """Apply threshold-based rule"""
        
        conditions = rule.conditions
        field = conditions.get('field')
        operator = conditions.get('operator')
        threshold = conditions.get('threshold')
        
        if not all([field, operator, threshold is not None]):
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning="Invalid threshold rule configuration"
            )
        
        # Get field value
        value = opportunity.get(field)
        if value is None:
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning=f"Field '{field}' not found in opportunity"
            )
        
        # Convert to numeric if needed
        try:
            if isinstance(value, str):
                value = float(re.sub(r'[^\d.]', '', value))
            else:
                value = float(value)
        except (ValueError, TypeError):
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning=f"Could not convert '{field}' to numeric value"
            )
        
        # Apply operator
        triggered = False
        if operator == 'lt':
            triggered = value < threshold
        elif operator == 'le':
            triggered = value <= threshold
        elif operator == 'gt':
            triggered = value > threshold
        elif operator == 'ge':
            triggered = value >= threshold
        elif operator == 'eq':
            triggered = value == threshold
        elif operator == 'ne':
            triggered = value != threshold
        
        reasoning = f"{field} ({value:,.0f}) {operator} {threshold:,.0f}"
        confidence_score = 0.95 if triggered else 0.0
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            extracted_values={field: value, 'threshold': threshold}
        )
    
    def _apply_pattern_rule(self, rule: FilterRule, 
                          opportunity: Dict[str, Any]) -> FilterResult:
        """Apply pattern matching rule"""
        
        conditions = rule.conditions
        fields = conditions.get('fields', [])
        patterns = conditions.get('exclude_patterns', [])
        case_sensitive = conditions.get('case_sensitive', False)
        match_threshold = conditions.get('match_threshold', 1)
        
        matched_patterns = []
        matched_fields = []
        
        # Combine text from specified fields
        text_content = ""
        for field in fields:
            field_value = opportunity.get(field, "")
            if field_value:
                text_content += f" {field_value}"
        
        if not text_content.strip():
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning="No text content found in specified fields"
            )
        
        # Apply patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        for pattern in patterns:
            if re.search(pattern, text_content, flags):
                matched_patterns.append(pattern)
                # Find which field(s) matched
                for field in fields:
                    field_value = opportunity.get(field, "")
                    if field_value and re.search(pattern, field_value, flags):
                        matched_fields.append(field)
        
        triggered = len(matched_patterns) >= match_threshold
        confidence_score = min(0.95, len(matched_patterns) * 0.3) if triggered else 0.0
        
        reasoning = f"Found {len(matched_patterns)} pattern matches"
        if matched_patterns:
            reasoning += f": {', '.join(matched_patterns[:3])}"
            if len(matched_patterns) > 3:
                reasoning += f" (and {len(matched_patterns) - 3} more)"
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            matched_criteria=matched_patterns,
            extracted_values={'matched_fields': list(set(matched_fields))}
        )
    
    def _apply_exclusion_rule(self, rule: FilterRule, 
                            opportunity: Dict[str, Any]) -> FilterResult:
        """Apply exclusion keyword rule"""
        
        conditions = rule.conditions
        excluded_keywords = conditions.get('excluded_keywords', [])
        fields = conditions.get('fields', ['description', 'title'])
        threshold = conditions.get('threshold', 0.5)
        
        # Combine text from specified fields
        text_content = ""
        for field in fields:
            field_value = opportunity.get(field, "")
            if field_value:
                text_content += f" {field_value}".lower()
        
        matches = []
        for keyword in excluded_keywords:
            if keyword.lower() in text_content:
                matches.append(keyword)
        
        match_score = len(matches) / len(excluded_keywords) if excluded_keywords else 0
        triggered = match_score >= threshold
        confidence_score = match_score if triggered else 0.0
        
        reasoning = f"Excluded keyword analysis: {len(matches)}/{len(excluded_keywords)} matches"
        if matches:
            reasoning += f" ({', '.join(matches[:3])})"
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            matched_criteria=matches
        )
    
    def _apply_requirement_rule(self, rule: FilterRule, opportunity: Dict[str, Any], 
                              company_profile: Dict[str, Any] = None) -> FilterResult:
        """Apply requirement-based rule"""
        
        conditions = rule.conditions
        
        # Security clearance requirements
        if 'required_clearances' in conditions:
            return self._check_clearance_requirements(rule, opportunity, company_profile)
        
        # Past performance requirements
        if 'required_experience' in conditions:
            return self._check_experience_requirements(rule, opportunity, company_profile)
        
        # Default fallback
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=False,
            action=rule.action,
            confidence_score=0.0,
            reasoning="Requirement rule type not implemented"
        )
    
    def _check_clearance_requirements(self, rule: FilterRule, opportunity: Dict[str, Any], 
                                   company_profile: Dict[str, Any] = None) -> FilterResult:
        """Check security clearance requirements"""
        
        conditions = rule.conditions
        required_clearance_levels = conditions.get('required_clearance_levels', [])
        fields = conditions.get('fields', ['description'])
        patterns = conditions.get('clearance_patterns', [])
        
        # Check if opportunity text mentions high-level clearances
        text_content = ""
        for field in fields:
            field_value = opportunity.get(field, "")
            if field_value:
                text_content += f" {field_value}".lower()
        
        high_clearance_mentioned = False
        mentioned_clearances = []
        
        for pattern in patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                high_clearance_mentioned = True
                mentioned_clearances.append(pattern)
        
        # Check company capability against actual profile
        company_has_clearance = False
        if company_profile and high_clearance_mentioned:
            profile_clearances = company_profile.get('security_clearances', [])
            profile_clearances = [c.lower().strip() for c in profile_clearances]
            
            # Check if company has any of the required high-level clearances
            for req_level in required_clearance_levels:
                req_level_lower = req_level.lower().strip()
                # Check for exact match or partial match
                for profile_clearance in profile_clearances:
                    if (req_level_lower in profile_clearance or 
                        profile_clearance in req_level_lower or
                        req_level_lower == profile_clearance):
                        company_has_clearance = True
                        break
                if company_has_clearance:
                    break
        
        # Determine if this is a mismatch
        triggered = high_clearance_mentioned and not company_has_clearance
        confidence_score = 0.9 if triggered else 0.0
        
        reasoning = "Clearance analysis: "
        if high_clearance_mentioned:
            reasoning += f"High clearance required ({', '.join(mentioned_clearances)})"
            if not company_has_clearance:
                reasoning += ", company lacks required clearance"
            else:
                reasoning += ", company has required clearance"
        else:
            reasoning += "No high-level clearance requirements detected"
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            matched_criteria=mentioned_clearances
        )
    
    def _check_experience_requirements(self, rule: FilterRule, opportunity: Dict[str, Any], 
                                     company_profile: Dict[str, Any] = None) -> FilterResult:
        """Check past performance/experience requirements"""
        
        conditions = rule.conditions
        required_exp = conditions.get('required_experience', {})
        min_contracts = required_exp.get('minimum_contracts', 3)
        min_value = required_exp.get('minimum_value', 1000000)
        trigger_patterns = conditions.get('trigger_patterns', [])
        fields = conditions.get('fields', ['description', 'requirements'])
        
        # First check if opportunity mentions past performance requirements
        text_content = ""
        for field in fields:
            field_value = opportunity.get(field, "")
            if field_value:
                text_content += f" {field_value}".lower()
        
        past_performance_mentioned = False
        mentioned_patterns = []
        
        for pattern in trigger_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                past_performance_mentioned = True
                mentioned_patterns.append(pattern)
        
        # If no past performance requirements mentioned, don't trigger
        if not past_performance_mentioned:
            return FilterResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=False,
                action=rule.action,
                confidence_score=0.0,
                reasoning="No past performance requirements detected",
                matched_criteria=[]
            )
        
        # Check company's past performance
        company_contracts = 0
        total_value = 0
        
        if company_profile:
            project_history = company_profile.get('project_history', [])
            company_contracts = len(project_history)
            total_value = sum(p.get('value', 0) for p in project_history)
        
        # Determine if requirements are met
        contracts_sufficient = company_contracts >= min_contracts
        value_sufficient = total_value >= min_value
        
        triggered = not (contracts_sufficient and value_sufficient)
        confidence_score = 0.7 if triggered else 0.0
        
        reasoning = f"Past performance required ({len(mentioned_patterns)} indicators). "
        reasoning += f"Company has {company_contracts} contracts (need {min_contracts}), "
        reasoning += f"${total_value:,.0f} total value (need ${min_value:,.0f})"
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            matched_criteria=mentioned_patterns,
            extracted_values={
                'company_contracts': company_contracts,
                'total_value': total_value,
                'min_contracts': min_contracts,
                'min_value': min_value
            }
        )
    
    def _apply_business_logic_rule(self, rule: FilterRule, opportunity: Dict[str, Any], 
                                 company_profile: Dict[str, Any] = None) -> FilterResult:
        """Apply complex business logic rule"""
        
        conditions = rule.conditions
        
        # Set-aside eligibility check
        if 'company_certifications' in conditions:
            return self._check_set_aside_eligibility(rule, opportunity, company_profile)
        
        # Default fallback
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=False,
            action=rule.action,
            confidence_score=0.0,
            reasoning="Business logic rule type not implemented"
        )
    
    def _check_set_aside_eligibility(self, rule: FilterRule, opportunity: Dict[str, Any], 
                                   company_profile: Dict[str, Any] = None) -> FilterResult:
        """Check set-aside eligibility"""
        
        conditions = rule.conditions
        company_certs = conditions.get('company_certifications', [])
        excluded_set_asides = conditions.get('excluded_set_asides', [])
        fields = conditions.get('fields', ['set_aside_type', 'description'])
        
        # Check opportunity for set-aside restrictions
        text_content = ""
        for field in fields:
            field_value = opportunity.get(field, "")
            if field_value:
                text_content += f" {field_value}".lower()
        
        # Look for restrictive set-aside language
        restrictive_set_asides = []
        set_aside_patterns = {
            '8a_only': [r'8\(a\)\s+only', r'8a\s+only', r'8\(a\)\s+restricted', r'8\(a\).*certified.*only', r'restricted.*8\(a\)'],
            'hubzone_only': [r'hubzone\s+only', r'hubzone\s+restricted', r'hubzone.*certified.*only', r'reserved.*hubzone'],
            'wosb_only': [r'wosb\s+only', r'women.*owned.*only', r'women.*owned.*restricted'],
            'vosb_only': [r'vosb\s+only', r'veteran.*owned.*only'],
            'sdvosb_only': [r'sdvosb\s+only', r'service.*disabled.*only']
        }
        
        for set_aside_type, patterns in set_aside_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_content, re.IGNORECASE):
                    restrictive_set_asides.append(set_aside_type)
                    break
        
        # Check company certifications
        company_has_required_cert = False
        if company_profile:
            sba_certs = company_profile.get('sba_certifications', [])
            sba_certs = [c.lower() for c in sba_certs]
            
            # Map set-aside types to certifications
            cert_mapping = {
                '8a_only': ['8(a)', '8a'],
                'hubzone_only': ['hubzone', 'hub zone'],
                'wosb_only': ['wosb', 'women-owned small business'],
                'sdvosb_only': ['sdvosb', 'service-disabled veteran-owned']
            }
            
            for set_aside in restrictive_set_asides:
                required_certs = cert_mapping.get(set_aside, [])
                for cert in required_certs:
                    if cert.lower() in sba_certs:
                        company_has_required_cert = True
                        break
        
        # Determine if this excludes the company
        triggered = bool(restrictive_set_asides) and not company_has_required_cert
        confidence_score = 0.95 if triggered else 0.0
        
        reasoning = "Set-aside eligibility: "
        if restrictive_set_asides:
            reasoning += f"Restricted to {', '.join(restrictive_set_asides)}"
            if not company_has_required_cert:
                reasoning += ", company lacks required certification"
            else:
                reasoning += ", company has required certification"
        else:
            reasoning += "No restrictive set-aside requirements detected"
        
        return FilterResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            action=rule.action,
            confidence_score=confidence_score,
            reasoning=reasoning,
            matched_criteria=restrictive_set_asides
        )
    
    def _determine_overall_recommendation(self, triggered_rules: List[FilterResult]) -> FilterAction:
        """Determine overall recommendation based on triggered rules with priority weighting"""
        
        if not triggered_rules:
            return FilterAction.WARN  # No rules triggered
        
        # Get only triggered rules
        active_rules = [result for result in triggered_rules if result.triggered]
        
        if not active_rules:
            return FilterAction.WARN  # No rules actually triggered
        
        # Weight by rule priority and confidence
        priority_weights = {
            FilterPriority.CRITICAL: 4,
            FilterPriority.HIGH: 3,
            FilterPriority.MEDIUM: 2,
            FilterPriority.LOW: 1
        }
        
        action_scores = {
            FilterAction.EXCLUDE: 0,
            FilterAction.FLAG: 0,
            FilterAction.DEPRIORITIZE: 0,
            FilterAction.WARN: 0
        }
        
        # Calculate weighted scores for each action
        for result in active_rules:
            rule = self.rules.get(result.rule_id)
            if rule:
                priority_weight = priority_weights.get(rule.priority, 1)
                confidence_weight = result.confidence_score
                combined_weight = priority_weight * confidence_weight
                
                action_scores[result.action] += combined_weight
        
        # Find the action with highest weighted score
        max_score = max(action_scores.values())
        
        if max_score == 0:
            return FilterAction.WARN
        
        # Return the highest-weighted action, with tiebreaker by severity
        for action in [FilterAction.EXCLUDE, FilterAction.FLAG, FilterAction.DEPRIORITIZE, FilterAction.WARN]:
            if action_scores[action] == max_score:
                return action
        
        return FilterAction.WARN  # Fallback
    
    def _calculate_confidence_score(self, triggered_rules: List[FilterResult]) -> float:
        """Calculate overall confidence score for the assessment"""
        
        if not triggered_rules:
            return 0.0
        
        # Weight by rule confidence and priority
        total_weight = 0
        weighted_confidence = 0
        
        priority_weights = {
            FilterPriority.CRITICAL: 1.0,
            FilterPriority.HIGH: 0.8,
            FilterPriority.MEDIUM: 0.6,
            FilterPriority.LOW: 0.4
        }
        
        for result in triggered_rules:
            if result.triggered:
                # Get rule priority from rules dict
                rule = self.rules.get(result.rule_id)
                if rule:
                    weight = priority_weights.get(rule.priority, 0.5)
                    total_weight += weight
                    weighted_confidence += result.confidence_score * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _generate_business_rationale(self, triggered_rules: List[FilterResult], 
                                   recommendation: FilterAction) -> str:
        """Generate business rationale for the recommendation"""
        
        if recommendation == FilterAction.EXCLUDE:
            exclusion_rules = [r for r in triggered_rules 
                             if r.triggered and r.action == FilterAction.EXCLUDE]
            if exclusion_rules:
                primary_reason = exclusion_rules[0].reasoning
                return f"Recommend EXCLUSION: {primary_reason}. " + \
                       f"This opportunity does not align with company capabilities " + \
                       f"or strategic priorities."
        
        elif recommendation == FilterAction.FLAG:
            flag_rules = [r for r in triggered_rules 
                         if r.triggered and r.action == FilterAction.FLAG]
            if flag_rules:
                return f"Recommend REVIEW: {flag_rules[0].reasoning}. " + \
                       f"This opportunity requires careful evaluation before bidding."
        
        elif recommendation == FilterAction.DEPRIORITIZE:
            return "Recommend DEPRIORITIZE: This opportunity has characteristics " + \
                   "that make it less attractive relative to other opportunities."
        
        elif recommendation == FilterAction.WARN:
            warn_rules = [r for r in triggered_rules 
                         if r.triggered and r.action == FilterAction.WARN]
            if warn_rules:
                return f"Proceed with CAUTION: {warn_rules[0].reasoning}. " + \
                       f"Monitor for additional risk factors."
            else:
                return "No significant filter concerns identified. " + \
                       "Opportunity passes initial screening criteria."
        
        return "Assessment complete. Review detailed filter results for decision guidance."
    
    def _estimate_time_saved(self, recommendation: FilterAction, 
                           opportunity: Dict[str, Any]) -> int:
        """Estimate time saved (in hours) by applying filters"""
        
        # Base time estimates for proposal development
        base_hours = {
            FilterAction.EXCLUDE: 40,  # Full proposal development time saved
            FilterAction.FLAG: 8,     # Initial analysis time saved until review
            FilterAction.DEPRIORITIZE: 4,  # Reduced priority planning time
            FilterAction.WARN: 2      # Minimal time impact
        }
        
        estimated_value = opportunity.get('estimated_value', 0)
        
        # Convert to numeric if needed (handle edge cases)
        try:
            if isinstance(estimated_value, str):
                estimated_value = float(re.sub(r'[^\d.]', '', estimated_value)) if estimated_value else 0
            estimated_value = float(estimated_value) if estimated_value else 0
        except (ValueError, TypeError):
            estimated_value = 0
        
        # Adjust based on opportunity size
        if estimated_value > 5000000:  # Large contracts
            multiplier = 2.0
        elif estimated_value > 1000000:  # Medium contracts
            multiplier = 1.5
        else:  # Small contracts
            multiplier = 1.0
        
        base_time = base_hours.get(recommendation, 0)
        return int(base_time * multiplier)

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule performance"""
        
        total_rules = len(self.rules)
        enabled_rules = len([r for r in self.rules.values() if r.enabled])
        
        # Rule performance
        most_triggered = None
        highest_success_rate = None
        
        for rule in self.rules.values():
            if rule.total_applications > 0:
                success_rate = rule.success_count / rule.total_applications
                
                if most_triggered is None or rule.success_count > most_triggered.success_count:
                    most_triggered = rule
                
                if highest_success_rate is None or success_rate > (highest_success_rate.success_count / highest_success_rate.total_applications):
                    highest_success_rate = rule
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'most_triggered_rule': {
                'id': most_triggered.id,
                'name': most_triggered.name,
                'trigger_count': most_triggered.success_count
            } if most_triggered else None,
            'highest_success_rate_rule': {
                'id': highest_success_rate.id,
                'name': highest_success_rate.name,
                'success_rate': highest_success_rate.success_count / highest_success_rate.total_applications
            } if highest_success_rate else None,
            'rule_categories': {
                rule_type.value: len([r for r in self.rules.values() if r.rule_type == rule_type])
                for rule_type in FilterRuleType
            }
        }