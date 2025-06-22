"""
Compliance Matrix Engine
Automated compliance analysis and requirements checking for government contracts
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
import asyncio

# NLP imports for document analysis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# import spacy  # Optional - only used if available

logger = logging.getLogger(__name__)

class ComplianceCategory(Enum):
    """Categories of compliance requirements"""
    SECURITY_CLEARANCE = "security_clearance"
    CERTIFICATIONS = "certifications"
    EXPERIENCE = "experience"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    LEGAL = "legal"
    SMALL_BUSINESS = "small_business"
    PERFORMANCE = "performance"
    INSURANCE = "insurance"
    GEOGRAPHIC = "geographic"

class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"

class RequirementPriority(Enum):
    """Priority levels for requirements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ComplianceRequirement:
    """Individual compliance requirement"""
    id: str
    category: ComplianceCategory
    title: str
    description: str
    priority: RequirementPriority
    mandatory: bool
    source_section: str
    keywords: List[str] = field(default_factory=list)
    sub_requirements: List[str] = field(default_factory=list)
    verification_method: str = ""
    timeline_days: Optional[int] = None
    cost_estimate: Optional[float] = None

@dataclass
class ComplianceAssessment:
    """Assessment of compliance for a specific requirement"""
    requirement_id: str
    status: ComplianceStatus
    confidence_score: float
    evidence: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    effort_estimate: Optional[int] = None  # Hours
    cost_estimate: Optional[float] = None
    notes: str = ""

@dataclass
class ComplianceMatrix:
    """Complete compliance analysis for an opportunity"""
    opportunity_id: str
    analysis_date: datetime
    overall_compliance_score: float
    requirements: List[ComplianceRequirement]
    assessments: List[ComplianceAssessment]
    critical_gaps: List[str]
    quick_wins: List[str]
    total_effort_estimate: int
    total_cost_estimate: float
    risk_level: str
    recommendations: List[str]
    next_actions: List[str]

class RequirementExtractor:
    """Extracts compliance requirements from opportunity documents"""
    
    def __init__(self):
        self.nlp = None
        self._load_nlp_model()
        self.compliance_patterns = self._initialize_patterns()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            logger.info("spaCy model not available, using rule-based extraction only")
            self.nlp = None
    
    def _initialize_patterns(self) -> Dict[ComplianceCategory, List[Dict]]:
        """Initialize regex patterns for requirement extraction"""
        return {
            ComplianceCategory.SECURITY_CLEARANCE: [
                {
                    "pattern": r"(secret|top secret|confidential|public trust|security clearance|clearance level)",
                    "keywords": ["security clearance", "secret", "confidential", "investigation"],
                    "priority": RequirementPriority.CRITICAL
                },
                {
                    "pattern": r"(background investigation|polygraph|security screening)",
                    "keywords": ["background check", "investigation", "screening"],
                    "priority": RequirementPriority.HIGH
                }
            ],
            ComplianceCategory.CERTIFICATIONS: [
                {
                    "pattern": r"(certification|certified|accredited|accreditation|ISO|CMMI|SOC)",
                    "keywords": ["certification", "accreditation", "standards", "quality"],
                    "priority": RequirementPriority.HIGH
                },
                {
                    "pattern": r"(CISSP|CISM|PMP|ITIL|AWS|Azure|Google Cloud)",
                    "keywords": ["professional certification", "technical certification"],
                    "priority": RequirementPriority.MEDIUM
                }
            ],
            ComplianceCategory.EXPERIENCE: [
                {
                    "pattern": r"(\d+)\s+(years?|months?)\s+.*?(experience|expertise)",
                    "keywords": ["experience", "expertise", "background", "history"],
                    "priority": RequirementPriority.CRITICAL
                },
                {
                    "pattern": r"(demonstrated|proven|established).*?(capability|ability|experience)",
                    "keywords": ["demonstrated capability", "proven experience"],
                    "priority": RequirementPriority.HIGH
                }
            ],
            ComplianceCategory.FINANCIAL: [
                {
                    "pattern": r"(financial|revenue|bonding|insurance|liability)",
                    "keywords": ["financial capacity", "bonding", "insurance", "liability"],
                    "priority": RequirementPriority.HIGH
                },
                {
                    "pattern": r"(\$[\d,]+).*?(revenue|contract|bonding capacity)",
                    "keywords": ["revenue requirement", "financial threshold"],
                    "priority": RequirementPriority.CRITICAL
                }
            ],
            ComplianceCategory.TECHNICAL: [
                {
                    "pattern": r"(technical|technology|system|software|hardware|infrastructure)",
                    "keywords": ["technical capability", "technology", "systems"],
                    "priority": RequirementPriority.HIGH
                },
                {
                    "pattern": r"(cloud|cybersecurity|data|analytics|AI|machine learning)",
                    "keywords": ["cloud computing", "cybersecurity", "data analytics"],
                    "priority": RequirementPriority.MEDIUM
                }
            ],
            ComplianceCategory.SMALL_BUSINESS: [
                {
                    "pattern": r"(small business|SDB|8\(a\)|HUBZone|WOSB|VOSB|SDVOSB)",
                    "keywords": ["small business", "socioeconomic", "set-aside"],
                    "priority": RequirementPriority.CRITICAL
                },
                {
                    "pattern": r"(socioeconomic|disadvantaged|veteran|woman-owned|service-disabled)",
                    "keywords": ["socioeconomic status", "disadvantaged business"],
                    "priority": RequirementPriority.HIGH
                }
            ],
            ComplianceCategory.LEGAL: [
                {
                    "pattern": r"(compliance|regulatory|federal|state|local).*?(requirement|regulation|law)",
                    "keywords": ["regulatory compliance", "legal requirements"],
                    "priority": RequirementPriority.HIGH
                },
                {
                    "pattern": r"(FISMA|NIST|HIPAA|SOX|PCI|GDPR)",
                    "keywords": ["regulatory framework", "compliance standards"],
                    "priority": RequirementPriority.CRITICAL
                }
            ],
            ComplianceCategory.PERFORMANCE: [
                {
                    "pattern": r"(performance|SLA|service level|uptime|availability)",
                    "keywords": ["performance requirements", "service levels"],
                    "priority": RequirementPriority.HIGH
                },
                {
                    "pattern": r"(\d+)%.*?(uptime|availability|performance)",
                    "keywords": ["performance metrics", "availability requirements"],
                    "priority": RequirementPriority.MEDIUM
                }
            ],
            ComplianceCategory.GEOGRAPHIC: [
                {
                    "pattern": r"(location|geographic|onsite|on-site|facility|premises)",
                    "keywords": ["location requirements", "geographic restrictions"],
                    "priority": RequirementPriority.MEDIUM
                },
                {
                    "pattern": r"(domestic|US|United States|CONUS|offshore restrictions)",
                    "keywords": ["domestic requirements", "geographic limitations"],
                    "priority": RequirementPriority.HIGH
                }
            ]
        }
    
    def extract_requirements(self, opportunity: Dict[str, Any]) -> List[ComplianceRequirement]:
        """Extract compliance requirements from opportunity text"""
        logger.info(f"Extracting requirements for opportunity {opportunity.get('id', 'unknown')}")
        
        # Combine all text sources
        text_sources = [
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            opportunity.get('requirements', ''),
            opportunity.get('statement_of_work', ''),
            opportunity.get('evaluation_criteria', '')
        ]
        
        full_text = ' '.join(filter(None, text_sources)).lower()
        
        if not full_text.strip():
            logger.warning("No text content found for requirement extraction")
            return []
        
        requirements = []
        requirement_id = 0
        
        # Extract requirements for each category
        for category, patterns in self.compliance_patterns.items():
            category_requirements = self._extract_category_requirements(
                full_text, category, patterns, requirement_id
            )
            requirements.extend(category_requirements)
            requirement_id += len(category_requirements)
        
        # Enhanced extraction using NLP if available
        if self.nlp:
            nlp_requirements = self._extract_nlp_requirements(full_text, requirement_id)
            requirements.extend(nlp_requirements)
        
        logger.info(f"Extracted {len(requirements)} compliance requirements")
        return requirements
    
    def _extract_category_requirements(self, text: str, category: ComplianceCategory, 
                                     patterns: List[Dict], start_id: int) -> List[ComplianceRequirement]:
        """Extract requirements for a specific category"""
        requirements = []
        
        for i, pattern_info in enumerate(patterns):
            pattern = pattern_info["pattern"]
            keywords = pattern_info["keywords"]
            priority = pattern_info["priority"]
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                # Create requirement
                req_id = f"{category.value}_{start_id + len(requirements)}"
                
                requirement = ComplianceRequirement(
                    id=req_id,
                    category=category,
                    title=self._generate_requirement_title(match.group(), category),
                    description=context,
                    priority=priority,
                    mandatory=self._is_mandatory(context),
                    source_section=f"Pattern match: {pattern}",
                    keywords=keywords,
                    verification_method=self._suggest_verification_method(category),
                    timeline_days=self._estimate_timeline(category, priority),
                    cost_estimate=self._estimate_cost(category, priority)
                )
                
                requirements.append(requirement)
        
        return requirements
    
    def _extract_nlp_requirements(self, text: str, start_id: int) -> List[ComplianceRequirement]:
        """Extract requirements using NLP analysis"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        requirements = []
        
        # Look for sentences containing requirement indicators
        requirement_indicators = [
            "must", "shall", "required", "mandatory", "necessary",
            "needs to", "has to", "should", "expected to"
        ]
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            if any(indicator in sent_text for indicator in requirement_indicators):
                # Analyze the sentence for compliance categories
                category = self._classify_sentence_category(sent_text)
                
                if category:
                    req_id = f"nlp_{start_id + len(requirements)}"
                    
                    requirement = ComplianceRequirement(
                        id=req_id,
                        category=category,
                        title=self._generate_nlp_title(sent.text, category),
                        description=sent.text,
                        priority=self._determine_priority(sent_text),
                        mandatory=self._is_mandatory(sent_text),
                        source_section="NLP analysis",
                        keywords=self._extract_keywords(sent_text),
                        verification_method=self._suggest_verification_method(category)
                    )
                    
                    requirements.append(requirement)
        
        return requirements
    
    def _generate_requirement_title(self, match_text: str, category: ComplianceCategory) -> str:
        """Generate a descriptive title for the requirement"""
        category_titles = {
            ComplianceCategory.SECURITY_CLEARANCE: f"Security Clearance: {match_text.title()}",
            ComplianceCategory.CERTIFICATIONS: f"Certification: {match_text.title()}",
            ComplianceCategory.EXPERIENCE: f"Experience Requirement: {match_text}",
            ComplianceCategory.FINANCIAL: f"Financial Requirement: {match_text}",
            ComplianceCategory.TECHNICAL: f"Technical Capability: {match_text}",
            ComplianceCategory.LEGAL: f"Legal/Regulatory: {match_text}",
            ComplianceCategory.SMALL_BUSINESS: f"Small Business: {match_text}",
            ComplianceCategory.PERFORMANCE: f"Performance Standard: {match_text}",
            ComplianceCategory.INSURANCE: f"Insurance Requirement: {match_text}",
            ComplianceCategory.GEOGRAPHIC: f"Location Requirement: {match_text}"
        }
        
        return category_titles.get(category, f"{category.value.title()}: {match_text}")
    
    def _generate_nlp_title(self, sentence: str, category: ComplianceCategory) -> str:
        """Generate title from NLP-extracted sentence"""
        # Extract key phrases from the sentence
        words = sentence.split()[:8]  # First 8 words
        title = ' '.join(words)
        
        if len(sentence.split()) > 8:
            title += "..."
        
        return f"{category.value.title()}: {title}"
    
    def _classify_sentence_category(self, sentence: str) -> Optional[ComplianceCategory]:
        """Classify a sentence into a compliance category"""
        category_keywords = {
            ComplianceCategory.SECURITY_CLEARANCE: ["clearance", "security", "classified", "secret"],
            ComplianceCategory.CERTIFICATIONS: ["certified", "certification", "accredited", "ISO"],
            ComplianceCategory.EXPERIENCE: ["experience", "years", "expertise", "background"],
            ComplianceCategory.FINANCIAL: ["financial", "revenue", "bonding", "insurance"],
            ComplianceCategory.TECHNICAL: ["technical", "technology", "system", "software"],
            ComplianceCategory.LEGAL: ["compliance", "regulatory", "legal", "requirement"],
            ComplianceCategory.SMALL_BUSINESS: ["small business", "8(a)", "HUBZone", "veteran"],
            ComplianceCategory.PERFORMANCE: ["performance", "SLA", "uptime", "availability"],
            ComplianceCategory.GEOGRAPHIC: ["location", "onsite", "domestic", "facility"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in sentence for keyword in keywords):
                return category
        
        return None
    
    def _is_mandatory(self, text: str) -> bool:
        """Determine if a requirement is mandatory"""
        mandatory_indicators = [
            "must", "shall", "required", "mandatory", "necessary",
            "critical", "essential", "minimum requirement"
        ]
        
        return any(indicator in text.lower() for indicator in mandatory_indicators)
    
    def _determine_priority(self, text: str) -> RequirementPriority:
        """Determine priority based on text indicators"""
        critical_words = ["critical", "essential", "mandatory", "must", "shall"]
        high_words = ["important", "significant", "required", "necessary"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in critical_words):
            return RequirementPriority.CRITICAL
        elif any(word in text_lower for word in high_words):
            return RequirementPriority.HIGH
        else:
            return RequirementPriority.MEDIUM
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Simple keyword extraction - can be enhanced with more sophisticated NLP
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return most frequent keywords
        from collections import Counter
        counter = Counter(keywords)
        return [word for word, count in counter.most_common(5)]
    
    def _suggest_verification_method(self, category: ComplianceCategory) -> str:
        """Suggest verification method for each category"""
        methods = {
            ComplianceCategory.SECURITY_CLEARANCE: "Security clearance documentation/verification",
            ComplianceCategory.CERTIFICATIONS: "Certificate copies and verification",
            ComplianceCategory.EXPERIENCE: "Project references and case studies",
            ComplianceCategory.FINANCIAL: "Financial statements and bonding letters",
            ComplianceCategory.TECHNICAL: "Technical demonstrations and architecture",
            ComplianceCategory.LEGAL: "Compliance documentation and attestations",
            ComplianceCategory.SMALL_BUSINESS: "SBA certification and registration",
            ComplianceCategory.PERFORMANCE: "SLA documentation and monitoring plans",
            ComplianceCategory.INSURANCE: "Insurance certificates and coverage proof",
            ComplianceCategory.GEOGRAPHIC: "Facility documentation and location proof"
        }
        
        return methods.get(category, "Documentation and verification")
    
    def _estimate_timeline(self, category: ComplianceCategory, priority: RequirementPriority) -> int:
        """Estimate timeline in days for compliance"""
        base_days = {
            ComplianceCategory.SECURITY_CLEARANCE: 180,
            ComplianceCategory.CERTIFICATIONS: 90,
            ComplianceCategory.EXPERIENCE: 30,
            ComplianceCategory.FINANCIAL: 45,
            ComplianceCategory.TECHNICAL: 60,
            ComplianceCategory.LEGAL: 30,
            ComplianceCategory.SMALL_BUSINESS: 60,
            ComplianceCategory.PERFORMANCE: 45,
            ComplianceCategory.INSURANCE: 14,
            ComplianceCategory.GEOGRAPHIC: 30
        }
        
        days = base_days.get(category, 30)
        
        # Adjust based on priority
        if priority == RequirementPriority.CRITICAL:
            days = int(days * 1.5)
        elif priority == RequirementPriority.LOW:
            days = int(days * 0.7)
        
        return days
    
    def _estimate_cost(self, category: ComplianceCategory, priority: RequirementPriority) -> float:
        """Estimate cost for compliance"""
        base_costs = {
            ComplianceCategory.SECURITY_CLEARANCE: 25000,
            ComplianceCategory.CERTIFICATIONS: 10000,
            ComplianceCategory.EXPERIENCE: 5000,
            ComplianceCategory.FINANCIAL: 8000,
            ComplianceCategory.TECHNICAL: 15000,
            ComplianceCategory.LEGAL: 12000,
            ComplianceCategory.SMALL_BUSINESS: 5000,
            ComplianceCategory.PERFORMANCE: 8000,
            ComplianceCategory.INSURANCE: 3000,
            ComplianceCategory.GEOGRAPHIC: 6000
        }
        
        cost = base_costs.get(category, 5000)
        
        # Adjust based on priority
        if priority == RequirementPriority.CRITICAL:
            cost *= 1.8
        elif priority == RequirementPriority.HIGH:
            cost *= 1.4
        elif priority == RequirementPriority.LOW:
            cost *= 0.6
        
        return cost

class ComplianceAnalyzer:
    """Analyzes company compliance against requirements"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        
    def assess_compliance(self, requirements: List[ComplianceRequirement], 
                         company_profile: Dict[str, Any]) -> List[ComplianceAssessment]:
        """Assess company compliance against extracted requirements"""
        logger.info(f"Assessing compliance for {len(requirements)} requirements")
        
        assessments = []
        
        for requirement in requirements:
            assessment = self._assess_single_requirement(requirement, company_profile)
            assessments.append(assessment)
        
        return assessments
    
    def _assess_single_requirement(self, requirement: ComplianceRequirement, 
                                 company_profile: Dict[str, Any]) -> ComplianceAssessment:
        """Assess compliance for a single requirement"""
        
        # Get relevant company data for this category
        company_data = self._get_company_data_for_category(requirement.category, company_profile)
        
        # Determine compliance status
        status, confidence = self._determine_compliance_status(requirement, company_data)
        
        # Identify evidence and gaps
        evidence = self._identify_evidence(requirement, company_data)
        gaps = self._identify_gaps(requirement, company_data, status)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(requirement, status, gaps)
        
        # Estimate effort and cost
        effort_estimate = self._estimate_effort(requirement, status)
        cost_estimate = self._estimate_compliance_cost(requirement, status)
        
        return ComplianceAssessment(
            requirement_id=requirement.id,
            status=status,
            confidence_score=confidence,
            evidence=evidence,
            gaps=gaps,
            recommendations=recommendations,
            effort_estimate=effort_estimate,
            cost_estimate=cost_estimate,
            notes=f"Assessment for {requirement.category.value}"
        )
    
    def _get_company_data_for_category(self, category: ComplianceCategory, 
                                     company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant company data for a specific compliance category"""
        
        category_mappings = {
            ComplianceCategory.SECURITY_CLEARANCE: [
                "security_clearances", "clearance_levels", "cleared_personnel"
            ],
            ComplianceCategory.CERTIFICATIONS: [
                "certifications", "accreditations", "quality_certifications"
            ],
            ComplianceCategory.EXPERIENCE: [
                "project_history", "experience_years", "domain_expertise", "past_performance"
            ],
            ComplianceCategory.FINANCIAL: [
                "annual_revenue", "bonding_capacity", "financial_strength", "credit_rating"
            ],
            ComplianceCategory.TECHNICAL: [
                "technical_capabilities", "technology_stack", "infrastructure", "tools"
            ],
            ComplianceCategory.LEGAL: [
                "compliance_certifications", "regulatory_experience", "legal_team"
            ],
            ComplianceCategory.SMALL_BUSINESS: [
                "small_business_status", "socioeconomic_certifications", "sba_certifications"
            ],
            ComplianceCategory.PERFORMANCE: [
                "performance_metrics", "sla_history", "uptime_records", "quality_metrics"
            ],
            ComplianceCategory.INSURANCE: [
                "insurance_coverage", "liability_insurance", "professional_indemnity"
            ],
            ComplianceCategory.GEOGRAPHIC: [
                "locations", "facilities", "geographic_presence", "domestic_capability"
            ]
        }
        
        relevant_fields = category_mappings.get(category, [])
        
        extracted_data = {}
        for field in relevant_fields:
            if field in company_profile:
                extracted_data[field] = company_profile[field]
        
        return extracted_data
    
    def _determine_compliance_status(self, requirement: ComplianceRequirement, 
                                   company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Determine compliance status and confidence"""
        
        if not company_data:
            return ComplianceStatus.UNKNOWN, 0.2
        
        # Category-specific compliance logic
        status_checkers = {
            ComplianceCategory.SECURITY_CLEARANCE: self._check_security_clearance,
            ComplianceCategory.CERTIFICATIONS: self._check_certifications,
            ComplianceCategory.EXPERIENCE: self._check_experience,
            ComplianceCategory.FINANCIAL: self._check_financial,
            ComplianceCategory.TECHNICAL: self._check_technical,
            ComplianceCategory.LEGAL: self._check_legal,
            ComplianceCategory.SMALL_BUSINESS: self._check_small_business,
            ComplianceCategory.PERFORMANCE: self._check_performance,
            ComplianceCategory.INSURANCE: self._check_insurance,
            ComplianceCategory.GEOGRAPHIC: self._check_geographic
        }
        
        checker = status_checkers.get(requirement.category, self._check_generic)
        return checker(requirement, company_data)
    
    def _check_security_clearance(self, requirement: ComplianceRequirement, 
                                company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check security clearance compliance"""
        clearances = company_data.get("security_clearances", [])
        cleared_personnel = company_data.get("cleared_personnel", 0)
        
        if not clearances and cleared_personnel == 0:
            return ComplianceStatus.NON_COMPLIANT, 0.9
        
        # Check for specific clearance levels in requirement
        req_text = requirement.description.lower()
        
        if "top secret" in req_text:
            if any("top secret" in str(clearance).lower() for clearance in clearances):
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.8
        elif "secret" in req_text:
            if any("secret" in str(clearance).lower() for clearance in clearances):
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.PARTIAL, 0.7
        
        # General clearance requirement
        if clearances or cleared_personnel > 0:
            return ComplianceStatus.PARTIAL, 0.6
        
        return ComplianceStatus.NON_COMPLIANT, 0.8
    
    def _check_certifications(self, requirement: ComplianceRequirement, 
                            company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check certification compliance"""
        certifications = company_data.get("certifications", [])
        
        if not certifications:
            return ComplianceStatus.NON_COMPLIANT, 0.8
        
        # Check for specific certifications mentioned in requirement
        req_keywords = requirement.keywords + [requirement.title.lower()]
        cert_text = ' '.join(str(cert).lower() for cert in certifications)
        
        matches = sum(1 for keyword in req_keywords if keyword in cert_text)
        
        if matches >= len(req_keywords) * 0.8:
            return ComplianceStatus.COMPLIANT, 0.9
        elif matches >= len(req_keywords) * 0.4:
            return ComplianceStatus.PARTIAL, 0.7
        else:
            return ComplianceStatus.NON_COMPLIANT, 0.6
    
    def _check_experience(self, requirement: ComplianceRequirement, 
                        company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check experience compliance"""
        experience_years = company_data.get("experience_years", 0)
        project_history = company_data.get("project_history", [])
        domain_expertise = company_data.get("domain_expertise", [])
        
        # Extract years requirement from text
        years_match = re.search(r'(\d+)\s+years?', requirement.description.lower())
        required_years = int(years_match.group(1)) if years_match else 5
        
        if experience_years >= required_years:
            confidence = min(0.9, 0.6 + (experience_years - required_years) * 0.05)
            return ComplianceStatus.COMPLIANT, confidence
        elif experience_years >= required_years * 0.7:
            return ComplianceStatus.PARTIAL, 0.7
        else:
            return ComplianceStatus.NON_COMPLIANT, 0.8
    
    def _check_financial(self, requirement: ComplianceRequirement, 
                       company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check financial compliance"""
        annual_revenue = company_data.get("annual_revenue", 0)
        bonding_capacity = company_data.get("bonding_capacity", 0)
        
        # Extract financial requirements
        revenue_match = re.search(r'\$([0-9,]+)', requirement.description)
        required_amount = 0
        
        if revenue_match:
            required_amount = float(revenue_match.group(1).replace(',', ''))
        
        if required_amount > 0:
            if annual_revenue >= required_amount:
                return ComplianceStatus.COMPLIANT, 0.9
            elif annual_revenue >= required_amount * 0.7:
                return ComplianceStatus.PARTIAL, 0.7
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.8
        
        # General financial capability check
        if annual_revenue > 1000000 or bonding_capacity > 500000:
            return ComplianceStatus.COMPLIANT, 0.6
        elif annual_revenue > 500000:
            return ComplianceStatus.PARTIAL, 0.5
        else:
            return ComplianceStatus.NON_COMPLIANT, 0.7
    
    def _check_technical(self, requirement: ComplianceRequirement, 
                       company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check technical compliance"""
        capabilities = company_data.get("technical_capabilities", [])
        technology_stack = company_data.get("technology_stack", [])
        
        if not capabilities and not technology_stack:
            return ComplianceStatus.UNKNOWN, 0.3
        
        # Check keyword alignment
        all_tech = ' '.join(str(item).lower() for item in capabilities + technology_stack)
        req_keywords = requirement.keywords
        
        matches = sum(1 for keyword in req_keywords if keyword in all_tech)
        
        if matches >= len(req_keywords) * 0.8:
            return ComplianceStatus.COMPLIANT, 0.8
        elif matches >= len(req_keywords) * 0.4:
            return ComplianceStatus.PARTIAL, 0.6
        else:
            return ComplianceStatus.NON_COMPLIANT, 0.5
    
    def _check_small_business(self, requirement: ComplianceRequirement, 
                            company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check small business compliance"""
        sb_status = company_data.get("small_business_status", False)
        sba_certs = company_data.get("sba_certifications", [])
        
        if "small business" in requirement.description.lower():
            if sb_status or sba_certs:
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.9
        
        # Check for specific set-asides
        req_text = requirement.description.lower()
        if any(term in req_text for term in ["8(a)", "hubzone", "wosb", "vosb", "sdvosb"]):
            cert_text = ' '.join(str(cert).lower() for cert in sba_certs)
            
            if any(term in cert_text for term in ["8(a)", "hubzone", "wosb", "vosb", "sdvosb"]):
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.9
        
        return ComplianceStatus.NOT_APPLICABLE, 0.8
    
    def _check_legal(self, requirement: ComplianceRequirement, 
                   company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check legal/regulatory compliance"""
        compliance_certs = company_data.get("compliance_certifications", [])
        regulatory_exp = company_data.get("regulatory_experience", [])
        
        if not compliance_certs and not regulatory_exp:
            return ComplianceStatus.UNKNOWN, 0.4
        
        # Check for specific compliance frameworks
        frameworks = ["FISMA", "NIST", "HIPAA", "SOX", "PCI", "GDPR"]
        req_text = requirement.description.upper()
        
        for framework in frameworks:
            if framework in req_text:
                cert_text = ' '.join(str(cert).upper() for cert in compliance_certs)
                if framework in cert_text:
                    return ComplianceStatus.COMPLIANT, 0.9
                else:
                    return ComplianceStatus.NON_COMPLIANT, 0.8
        
        # General compliance capability
        if compliance_certs or regulatory_exp:
            return ComplianceStatus.PARTIAL, 0.6
        
        return ComplianceStatus.NON_COMPLIANT, 0.5
    
    def _check_performance(self, requirement: ComplianceRequirement, 
                         company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check performance compliance"""
        metrics = company_data.get("performance_metrics", {})
        sla_history = company_data.get("sla_history", [])
        
        if not metrics and not sla_history:
            return ComplianceStatus.UNKNOWN, 0.3
        
        # Extract performance requirements
        perf_match = re.search(r'(\d+)%.*?(uptime|availability)', requirement.description.lower())
        
        if perf_match:
            required_perf = float(perf_match.group(1))
            current_perf = metrics.get("uptime_percentage", 0)
            
            if current_perf >= required_perf:
                return ComplianceStatus.COMPLIANT, 0.9
            elif current_perf >= required_perf * 0.9:
                return ComplianceStatus.PARTIAL, 0.7
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.8
        
        # General performance capability
        if metrics or sla_history:
            return ComplianceStatus.PARTIAL, 0.6
        
        return ComplianceStatus.NON_COMPLIANT, 0.5
    
    def _check_insurance(self, requirement: ComplianceRequirement, 
                       company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check insurance compliance"""
        coverage = company_data.get("insurance_coverage", [])
        
        if not coverage:
            return ComplianceStatus.NON_COMPLIANT, 0.8
        
        # Check for specific insurance types
        req_text = requirement.description.lower()
        coverage_text = ' '.join(str(cov).lower() for cov in coverage)
        
        if any(ins_type in req_text for ins_type in ["liability", "professional", "cyber"]):
            if any(ins_type in coverage_text for ins_type in ["liability", "professional", "cyber"]):
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.PARTIAL, 0.6
        
        # General insurance coverage
        return ComplianceStatus.PARTIAL, 0.7
    
    def _check_geographic(self, requirement: ComplianceRequirement, 
                        company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Check geographic compliance"""
        locations = company_data.get("locations", [])
        facilities = company_data.get("facilities", [])
        
        if not locations and not facilities:
            return ComplianceStatus.UNKNOWN, 0.4
        
        req_text = requirement.description.lower()
        location_text = ' '.join(str(loc).lower() for loc in locations + facilities)
        
        # Check for onsite requirements
        if "onsite" in req_text or "on-site" in req_text:
            if "onsite" in location_text or "facility" in location_text:
                return ComplianceStatus.COMPLIANT, 0.8
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.7
        
        # Check for domestic requirements
        if "domestic" in req_text or "us" in req_text:
            if any(term in location_text for term in ["us", "usa", "united states", "domestic"]):
                return ComplianceStatus.COMPLIANT, 0.9
            else:
                return ComplianceStatus.NON_COMPLIANT, 0.8
        
        return ComplianceStatus.PARTIAL, 0.5
    
    def _check_generic(self, requirement: ComplianceRequirement, 
                     company_data: Dict[str, Any]) -> Tuple[ComplianceStatus, float]:
        """Generic compliance check"""
        if company_data:
            return ComplianceStatus.PARTIAL, 0.4
        else:
            return ComplianceStatus.UNKNOWN, 0.2
    
    def _identify_evidence(self, requirement: ComplianceRequirement, 
                          company_data: Dict[str, Any]) -> List[str]:
        """Identify evidence supporting compliance"""
        evidence = []
        
        for key, value in company_data.items():
            if value:
                if isinstance(value, list) and value:
                    evidence.append(f"{key.replace('_', ' ').title()}: {len(value)} items")
                elif isinstance(value, (int, float)) and value > 0:
                    evidence.append(f"{key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, str):
                    evidence.append(f"{key.replace('_', ' ').title()}: Available")
                elif isinstance(value, bool) and value:
                    evidence.append(f"{key.replace('_', ' ').title()}: Yes")
        
        return evidence[:5]  # Top 5 pieces of evidence
    
    def _identify_gaps(self, requirement: ComplianceRequirement, 
                      company_data: Dict[str, Any], 
                      status: ComplianceStatus) -> List[str]:
        """Identify compliance gaps"""
        gaps = []
        
        if status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]:
            if not company_data:
                gaps.append(f"No {requirement.category.value} information available")
            
            # Category-specific gap identification
            if requirement.category == ComplianceCategory.SECURITY_CLEARANCE:
                if "secret" in requirement.description.lower():
                    gaps.append("Security clearance required")
            elif requirement.category == ComplianceCategory.CERTIFICATIONS:
                gaps.append("Required certifications missing or expired")
            elif requirement.category == ComplianceCategory.EXPERIENCE:
                years_match = re.search(r'(\d+)\s+years?', requirement.description.lower())
                if years_match:
                    gaps.append(f"Minimum {years_match.group(1)} years experience required")
            elif requirement.category == ComplianceCategory.FINANCIAL:
                gaps.append("Financial capacity documentation needed")
            
            if requirement.mandatory:
                gaps.append("This is a mandatory requirement")
        
        return gaps
    
    def _generate_recommendations(self, requirement: ComplianceRequirement, 
                                status: ComplianceStatus, 
                                gaps: List[str]) -> List[str]:
        """Generate recommendations for achieving compliance"""
        recommendations = []
        
        if status == ComplianceStatus.COMPLIANT:
            recommendations.append("Document and highlight this compliance in your proposal")
        elif status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]:
            if requirement.category == ComplianceCategory.SECURITY_CLEARANCE:
                recommendations.append("Begin security clearance process immediately")
                recommendations.append("Consider partnering with cleared personnel")
            elif requirement.category == ComplianceCategory.CERTIFICATIONS:
                recommendations.append("Pursue required certifications")
                recommendations.append("Document timeline for obtaining certifications")
            elif requirement.category == ComplianceCategory.EXPERIENCE:
                recommendations.append("Highlight relevant project experience")
                recommendations.append("Consider teaming with experienced partners")
            elif requirement.category == ComplianceCategory.FINANCIAL:
                recommendations.append("Obtain bonding capacity documentation")
                recommendations.append("Prepare financial statements")
            
            if requirement.priority == RequirementPriority.CRITICAL:
                recommendations.append("CRITICAL: Address this requirement immediately")
        
        return recommendations
    
    def _estimate_effort(self, requirement: ComplianceRequirement, 
                        status: ComplianceStatus) -> int:
        """Estimate effort in hours to achieve compliance"""
        base_effort = {
            ComplianceCategory.SECURITY_CLEARANCE: 120,
            ComplianceCategory.CERTIFICATIONS: 80,
            ComplianceCategory.EXPERIENCE: 40,
            ComplianceCategory.FINANCIAL: 60,
            ComplianceCategory.TECHNICAL: 100,
            ComplianceCategory.LEGAL: 60,
            ComplianceCategory.SMALL_BUSINESS: 40,
            ComplianceCategory.PERFORMANCE: 60,
            ComplianceCategory.INSURANCE: 20,
            ComplianceCategory.GEOGRAPHIC: 30
        }
        
        effort = base_effort.get(requirement.category, 40)
        
        # Adjust based on status
        if status == ComplianceStatus.COMPLIANT:
            effort *= 0.2  # Just documentation
        elif status == ComplianceStatus.PARTIAL:
            effort *= 0.6  # Some work needed
        # NON_COMPLIANT uses full effort
        
        # Adjust based on priority
        if requirement.priority == RequirementPriority.CRITICAL:
            effort *= 1.5
        
        return int(effort)
    
    def _estimate_compliance_cost(self, requirement: ComplianceRequirement, 
                                status: ComplianceStatus) -> float:
        """Estimate cost to achieve compliance"""
        if status == ComplianceStatus.COMPLIANT:
            return requirement.cost_estimate * 0.1 if requirement.cost_estimate else 1000
        elif status == ComplianceStatus.PARTIAL:
            return requirement.cost_estimate * 0.5 if requirement.cost_estimate else 5000
        else:
            return requirement.cost_estimate if requirement.cost_estimate else 10000

class ComplianceMatrixEngine:
    """Main engine for compliance matrix analysis"""
    
    def __init__(self):
        self.requirement_extractor = RequirementExtractor()
        self.compliance_analyzer = ComplianceAnalyzer()
    
    async def analyze_opportunity_compliance(self, opportunity: Dict[str, Any], 
                                           company_profile: Dict[str, Any]) -> ComplianceMatrix:
        """Perform complete compliance analysis for an opportunity"""
        logger.info(f"Starting compliance analysis for opportunity {opportunity.get('id', 'unknown')}")
        
        # Extract requirements
        requirements = self.requirement_extractor.extract_requirements(opportunity)
        
        if not requirements:
            logger.warning("No compliance requirements extracted")
            return self._create_empty_matrix(opportunity.get('id', 'unknown'))
        
        # Assess compliance
        assessments = self.compliance_analyzer.assess_compliance(requirements, company_profile)
        
        # Calculate overall metrics
        overall_score = self._calculate_overall_score(assessments)
        critical_gaps = self._identify_critical_gaps(requirements, assessments)
        quick_wins = self._identify_quick_wins(requirements, assessments)
        
        # Calculate totals
        total_effort = sum(assessment.effort_estimate or 0 for assessment in assessments)
        total_cost = sum(assessment.cost_estimate or 0 for assessment in assessments)
        
        # Determine risk level
        risk_level = self._determine_risk_level(assessments, critical_gaps)
        
        # Generate recommendations
        recommendations = self._generate_overall_recommendations(requirements, assessments)
        next_actions = self._generate_next_actions(critical_gaps, quick_wins)
        
        matrix = ComplianceMatrix(
            opportunity_id=opportunity.get('id', 'unknown'),
            analysis_date=datetime.now(),
            overall_compliance_score=overall_score,
            requirements=requirements,
            assessments=assessments,
            critical_gaps=critical_gaps,
            quick_wins=quick_wins,
            total_effort_estimate=total_effort,
            total_cost_estimate=total_cost,
            risk_level=risk_level,
            recommendations=recommendations,
            next_actions=next_actions
        )
        
        logger.info(f"Compliance analysis completed: {overall_score:.1%} compliance, {len(critical_gaps)} critical gaps")
        
        return matrix
    
    def _create_empty_matrix(self, opportunity_id: str) -> ComplianceMatrix:
        """Create empty compliance matrix when no requirements found"""
        return ComplianceMatrix(
            opportunity_id=opportunity_id,
            analysis_date=datetime.now(),
            overall_compliance_score=0.0,
            requirements=[],
            assessments=[],
            critical_gaps=["No compliance requirements identified"],
            quick_wins=[],
            total_effort_estimate=0,
            total_cost_estimate=0.0,
            risk_level="Unknown",
            recommendations=["Review opportunity documentation for compliance requirements"],
            next_actions=["Request additional requirement details from opportunity owner"]
        )
    
    def _calculate_overall_score(self, assessments: List[ComplianceAssessment]) -> float:
        """Calculate overall compliance score"""
        if not assessments:
            return 0.0
        
        # Weight scores based on compliance status
        status_weights = {
            ComplianceStatus.COMPLIANT: 1.0,
            ComplianceStatus.PARTIAL: 0.6,
            ComplianceStatus.NON_COMPLIANT: 0.0,
            ComplianceStatus.UNKNOWN: 0.3,
            ComplianceStatus.NOT_APPLICABLE: 1.0
        }
        
        weighted_scores = []
        for assessment in assessments:
            status_weight = status_weights.get(assessment.status, 0.0)
            confidence_weight = assessment.confidence_score
            
            # Combine status and confidence
            combined_score = status_weight * confidence_weight
            weighted_scores.append(combined_score)
        
        return sum(weighted_scores) / len(weighted_scores)
    
    def _identify_critical_gaps(self, requirements: List[ComplianceRequirement], 
                              assessments: List[ComplianceAssessment]) -> List[str]:
        """Identify critical compliance gaps"""
        critical_gaps = []
        
        for req, assessment in zip(requirements, assessments):
            if (req.priority == RequirementPriority.CRITICAL and 
                assessment.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.UNKNOWN]):
                
                gap_description = f"{req.category.value.title()}: {req.title}"
                if req.mandatory:
                    gap_description += " (MANDATORY)"
                
                critical_gaps.append(gap_description)
        
        return critical_gaps
    
    def _identify_quick_wins(self, requirements: List[ComplianceRequirement], 
                           assessments: List[ComplianceAssessment]) -> List[str]:
        """Identify quick win opportunities"""
        quick_wins = []
        
        for req, assessment in zip(requirements, assessments):
            if (assessment.status == ComplianceStatus.PARTIAL and 
                (assessment.effort_estimate or 0) < 20):  # Less than 20 hours
                
                quick_wins.append(f"{req.category.value.title()}: {req.title}")
        
        return quick_wins
    
    def _determine_risk_level(self, assessments: List[ComplianceAssessment], 
                            critical_gaps: List[str]) -> str:
        """Determine overall risk level"""
        if len(critical_gaps) >= 3:
            return "Very High"
        elif len(critical_gaps) >= 2:
            return "High"
        elif len(critical_gaps) >= 1:
            return "Medium"
        else:
            non_compliant_count = sum(1 for a in assessments 
                                    if a.status == ComplianceStatus.NON_COMPLIANT)
            if non_compliant_count >= 5:
                return "Medium"
            elif non_compliant_count >= 2:
                return "Low"
            else:
                return "Very Low"
    
    def _generate_overall_recommendations(self, requirements: List[ComplianceRequirement], 
                                        assessments: List[ComplianceAssessment]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        # Priority-based recommendations
        critical_count = sum(1 for req in requirements if req.priority == RequirementPriority.CRITICAL)
        non_compliant_critical = sum(1 for req, assessment in zip(requirements, assessments) 
                                   if req.priority == RequirementPriority.CRITICAL and 
                                   assessment.status == ComplianceStatus.NON_COMPLIANT)
        
        if non_compliant_critical > 0:
            recommendations.append(f"Address {non_compliant_critical} critical compliance gaps before proposal submission")
        
        # Category-specific recommendations
        category_gaps = {}
        for req, assessment in zip(requirements, assessments):
            if assessment.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]:
                category = req.category
                if category not in category_gaps:
                    category_gaps[category] = 0
                category_gaps[category] += 1
        
        for category, gap_count in category_gaps.items():
            if gap_count >= 2:
                recommendations.append(f"Focus on {category.value.replace('_', ' ')} compliance ({gap_count} gaps identified)")
        
        # Effort-based recommendations
        total_effort = sum(assessment.effort_estimate or 0 for assessment in assessments)
        if total_effort > 200:
            recommendations.append("Consider phased compliance approach due to high effort requirements")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_next_actions(self, critical_gaps: List[str], quick_wins: List[str]) -> List[str]:
        """Generate immediate next actions"""
        actions = []
        
        if critical_gaps:
            actions.append(f"Immediately address {len(critical_gaps)} critical gaps")
            actions.append("Develop timeline for critical compliance items")
        
        if quick_wins:
            actions.append(f"Execute {len(quick_wins)} quick wins to improve compliance score")
        
        actions.extend([
            "Assign compliance responsibilities to team members",
            "Create compliance tracking dashboard",
            "Schedule regular compliance review meetings"
        ])
        
        return actions[:5]  # Top 5 actions