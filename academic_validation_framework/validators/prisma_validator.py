"""
PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) Validator.

Validates systematic reviews against PRISMA guidelines for methodological rigor.
"""

import re
from typing import Any, Dict, List, Optional

from .base import BaseValidator, ValidationContext, ValidationResult


class PRISMAValidator(BaseValidator):
    """
    Validates research output against PRISMA systematic review guidelines.
    
    PRISMA is an evidence-based minimum set of items for reporting in systematic 
    reviews and meta-analyses. This validator checks for compliance with key 
    PRISMA requirements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="PRISMA_Validator",
            description="Validates systematic reviews against PRISMA guidelines",
            version="1.0.0",
            config=config or {}
        )
        
        # PRISMA checklist items and their weights
        self.prisma_items = {
            "title": {
                "weight": 0.05,
                "keywords": ["systematic review", "meta-analysis", "systematic", "review"],
                "required": True
            },
            "abstract": {
                "weight": 0.10,
                "keywords": ["objective", "method", "results", "conclusion", "background"],
                "required": True
            },
            "introduction": {
                "weight": 0.10,
                "keywords": ["rationale", "objective", "hypothesis", "research question"],
                "required": True
            },
            "methods": {
                "weight": 0.25,
                "keywords": ["protocol", "search strategy", "selection criteria", "data extraction"],
                "required": True
            },
            "search_strategy": {
                "weight": 0.15,
                "keywords": ["database", "search terms", "keywords", "search strategy", "pubmed", "medline"],
                "required": True
            },
            "selection_criteria": {
                "weight": 0.10,
                "keywords": ["inclusion", "exclusion", "criteria", "eligible", "eligibility"],
                "required": True
            },
            "data_extraction": {
                "weight": 0.10,
                "keywords": ["data extraction", "data collection", "extracted", "standardized form"],
                "required": True
            },
            "quality_assessment": {
                "weight": 0.10,
                "keywords": ["quality assessment", "risk of bias", "methodological quality", "bias"],
                "required": True
            },
            "results": {
                "weight": 0.15,
                "keywords": ["results", "findings", "studies identified", "characteristics"],
                "required": True
            }
        }
        
        # Thresholds for compliance scoring
        self.compliance_thresholds = {
            "excellent": 0.90,
            "good": 0.80,
            "acceptable": 0.70,
            "poor": 0.60
        }
    
    async def _initialize_validator(self) -> None:
        """Initialize PRISMA validator."""
        pass
    
    async def validate(
        self,
        research_output: Any,
        context: Optional[ValidationContext] = None,
        **kwargs: Any
    ) -> List[ValidationResult]:
        """
        Validate research output against PRISMA guidelines.
        
        Returns multiple validation results for different PRISMA components.
        """
        text_content = self._extract_text_content(research_output)
        metadata = self._extract_metadata(research_output)
        
        results = []
        
        # Validate overall PRISMA compliance
        overall_result = await self._validate_overall_compliance(text_content, metadata)
        results.append(overall_result)
        
        # Validate individual PRISMA items
        item_results = await self._validate_prisma_items(text_content)
        results.extend(item_results)
        
        # Validate search strategy specifically
        search_result = await self._validate_search_strategy(text_content)
        results.append(search_result)
        
        # Validate methodological rigor
        method_result = await self._validate_methodological_rigor(text_content)
        results.append(method_result)
        
        return results
    
    async def _validate_overall_compliance(
        self, 
        text_content: str, 
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Validate overall PRISMA compliance."""
        
        compliance_scores = {}
        total_weight = 0.0
        weighted_score = 0.0
        
        text_lower = text_content.lower()
        
        for item_name, item_config in self.prisma_items.items():
            keywords = item_config["keywords"]
            weight = item_config["weight"]
            
            # Calculate keyword presence score
            keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
            keyword_score = min(keyword_matches / len(keywords), 1.0)
            
            # Boost score if section structure is detected
            section_boost = self._detect_section_structure(text_content, item_name)
            final_score = min(keyword_score + section_boost, 1.0)
            
            compliance_scores[item_name] = final_score
            weighted_score += final_score * weight
            total_weight += weight
        
        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Determine compliance level
        compliance_level = "poor"
        for level, threshold in sorted(self.compliance_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                compliance_level = level
                break
        
        status = "passed" if overall_score >= 0.70 else "failed"
        
        return self._create_result(
            test_name="prisma_overall_compliance",
            status=status,
            score=overall_score,
            details={
                "compliance_level": compliance_level,
                "item_scores": compliance_scores,
                "missing_items": [
                    item for item, score in compliance_scores.items() 
                    if score < 0.5 and self.prisma_items[item]["required"]
                ],
                "recommendations": self._generate_compliance_recommendations(compliance_scores)
            },
            metadata={
                "prisma_version": "2020",
                "total_items_checked": len(self.prisma_items),
                "compliance_threshold": 0.70
            }
        )
    
    async def _validate_prisma_items(self, text_content: str) -> List[ValidationResult]:
        """Validate individual PRISMA checklist items."""
        results = []
        text_lower = text_content.lower()
        
        for item_name, item_config in self.prisma_items.items():
            keywords = item_config["keywords"]
            required = item_config["required"]
            
            # Calculate presence score
            keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
            presence_score = keyword_matches / len(keywords)
            
            # Check for section structure
            section_score = self._detect_section_structure(text_content, item_name)
            
            # Calculate final score
            final_score = min(presence_score + section_score, 1.0)
            
            # Determine status
            if required and final_score < 0.3:
                status = "failed"
            elif final_score < 0.5:
                status = "warning" 
            else:
                status = "passed"
            
            result = self._create_result(
                test_name=f"prisma_item_{item_name}",
                status=status,
                score=final_score,
                details={
                    "item_type": item_name,
                    "required": required,
                    "keywords_found": [kw for kw in keywords if kw in text_lower],
                    "keywords_missing": [kw for kw in keywords if kw not in text_lower],
                    "presence_score": presence_score,
                    "section_score": section_score,
                },
                metadata={
                    "total_keywords": len(keywords),
                    "matched_keywords": keyword_matches
                }
            )
            
            results.append(result)
        
        return results
    
    async def _validate_search_strategy(self, text_content: str) -> ValidationResult:
        """Validate search strategy comprehensiveness."""
        
        search_indicators = {
            "databases": ["pubmed", "medline", "embase", "cochrane", "scopus", "web of science"],
            "search_terms": ["search terms", "keywords", "mesh terms", "boolean", "truncation"],
            "date_limits": ["date", "year", "from", "to", "between", "since"],
            "language_limits": ["language", "english", "non-english", "translated"],
            "filters": ["filter", "limit", "restrict", "exclude", "include"]
        }
        
        text_lower = text_content.lower()
        search_scores = {}
        
        for category, indicators in search_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text_lower)
            score = min(matches / len(indicators), 1.0)
            search_scores[category] = score
        
        # Calculate comprehensive search score
        overall_search_score = sum(search_scores.values()) / len(search_scores)
        
        # Check for systematic search patterns
        systematic_patterns = [
            r'\b\d+\s+database',  # "5 databases"
            r'search\s+strateg[yi]',  # "search strategy"
            r'systematic\s+search',  # "systematic search"
            r'\(\w+\s+AND\s+\w+\)',  # Boolean operators
        ]
        
        pattern_matches = sum(1 for pattern in systematic_patterns 
                            if re.search(pattern, text_lower))
        pattern_score = pattern_matches / len(systematic_patterns)
        
        final_score = (overall_search_score + pattern_score) / 2
        
        status = "passed" if final_score >= 0.6 else "failed"
        
        return self._create_result(
            test_name="prisma_search_strategy",
            status=status,
            score=final_score,
            details={
                "category_scores": search_scores,
                "systematic_patterns_found": pattern_matches,
                "search_comprehensiveness": overall_search_score,
                "pattern_compliance": pattern_score,
                "recommendations": self._generate_search_recommendations(search_scores)
            },
            metadata={
                "search_categories_checked": len(search_indicators),
                "pattern_checks": len(systematic_patterns)
            }
        )
    
    async def _validate_methodological_rigor(self, text_content: str) -> ValidationResult:
        """Validate methodological rigor and transparency."""
        
        rigor_indicators = {
            "protocol_registration": ["protocol", "prospero", "registered", "registration"],
            "duplicate_screening": ["duplicate", "independent", "two reviewers", "inter-rater"],
            "quality_assessment": ["quality", "bias", "methodological", "assessment", "cochrane"],
            "data_synthesis": ["meta-analysis", "synthesis", "pooled", "forest plot", "heterogeneity"],
            "transparency": ["supplementary", "appendix", "additional", "available", "flow chart"]
        }
        
        text_lower = text_content.lower()
        rigor_scores = {}
        
        for category, indicators in rigor_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text_lower)
            score = min(matches / len(indicators), 1.0)
            rigor_scores[category] = score
        
        # Calculate methodological rigor score
        methodological_score = sum(rigor_scores.values()) / len(rigor_scores)
        
        # Check for PRISMA flow diagram mentions
        flow_patterns = [
            r'flow\s+diagram',
            r'prisma\s+flow',
            r'study\s+selection',
            r'screening\s+process'
        ]
        
        flow_matches = sum(1 for pattern in flow_patterns 
                          if re.search(pattern, text_lower))
        flow_score = min(flow_matches / len(flow_patterns), 1.0)
        
        final_score = (methodological_score + flow_score) / 2
        
        status = "passed" if final_score >= 0.65 else "failed"
        
        return self._create_result(
            test_name="prisma_methodological_rigor",
            status=status,
            score=final_score,
            details={
                "rigor_scores": rigor_scores,
                "flow_diagram_score": flow_score,
                "methodological_transparency": methodological_score,
                "missing_elements": [
                    category for category, score in rigor_scores.items() 
                    if score < 0.3
                ],
                "recommendations": self._generate_rigor_recommendations(rigor_scores)
            },
            metadata={
                "rigor_categories": len(rigor_indicators),
                "flow_patterns_checked": len(flow_patterns)
            }
        )
    
    def _detect_section_structure(self, text_content: str, item_name: str) -> float:
        """Detect if proper section structure exists for PRISMA item."""
        
        section_patterns = {
            "title": [r'^title', r'^.*systematic review.*$'],
            "abstract": [r'^abstract', r'^\s*abstract\s*$'],
            "introduction": [r'^introduction', r'^background', r'^\s*introduction\s*$'],
            "methods": [r'^methods', r'^methodology', r'^\s*methods\s*$'],
            "search_strategy": [r'^search strategy', r'^search methods', r'literature search'],
            "selection_criteria": [r'^selection criteria', r'^inclusion criteria', r'^eligibility'],
            "data_extraction": [r'^data extraction', r'^data collection'],
            "quality_assessment": [r'^quality assessment', r'^risk of bias', r'^methodological quality'],
            "results": [r'^results', r'^\s*results\s*$']
        }
        
        patterns = section_patterns.get(item_name, [])
        if not patterns:
            return 0.0
        
        text_lines = text_content.lower().split('\n')
        
        for pattern in patterns:
            for line in text_lines:
                if re.search(pattern, line.strip()):
                    return 0.3  # Boost score for proper section structure
        
        return 0.0
    
    def _generate_compliance_recommendations(self, compliance_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving PRISMA compliance."""
        recommendations = []
        
        low_scoring_items = [
            item for item, score in compliance_scores.items() 
            if score < 0.5
        ]
        
        if "search_strategy" in low_scoring_items:
            recommendations.append("Provide detailed search strategy including databases, keywords, and date limits")
        
        if "methods" in low_scoring_items:
            recommendations.append("Expand methodology section with clear protocol description")
        
        if "selection_criteria" in low_scoring_items:
            recommendations.append("Define explicit inclusion and exclusion criteria")
        
        if "quality_assessment" in low_scoring_items:
            recommendations.append("Include assessment of study quality and risk of bias")
        
        if "data_extraction" in low_scoring_items:
            recommendations.append("Describe data extraction process and tools used")
        
        if not recommendations:
            recommendations.append("Consider adding PRISMA flow diagram and checklist")
        
        return recommendations
    
    def _generate_search_recommendations(self, search_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving search strategy."""
        recommendations = []
        
        if search_scores["databases"] < 0.5:
            recommendations.append("Include multiple databases (PubMed, Embase, Cochrane Library)")
        
        if search_scores["search_terms"] < 0.5:
            recommendations.append("Provide detailed search terms and Boolean operators")
        
        if search_scores["date_limits"] < 0.5:
            recommendations.append("Specify date limits and justify the time frame")
        
        if search_scores["language_limits"] < 0.5:
            recommendations.append("State language restrictions and rationale")
        
        if search_scores["filters"] < 0.5:
            recommendations.append("Document all search filters and limitations applied")
        
        return recommendations
    
    def _generate_rigor_recommendations(self, rigor_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving methodological rigor."""
        recommendations = []
        
        if rigor_scores["protocol_registration"] < 0.5:
            recommendations.append("Register protocol in PROSPERO or similar registry")
        
        if rigor_scores["duplicate_screening"] < 0.5:
            recommendations.append("Implement duplicate screening by independent reviewers")
        
        if rigor_scores["quality_assessment"] < 0.5:
            recommendations.append("Use standardized quality assessment tools (e.g., Cochrane RoB)")
        
        if rigor_scores["data_synthesis"] < 0.5:
            recommendations.append("Provide clear data synthesis methodology")
        
        if rigor_scores["transparency"] < 0.5:
            recommendations.append("Include supplementary materials and PRISMA checklist")
        
        return recommendations