"""
Real PRISMA systematic review validation with actual implementation.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime
import logging

from ..interfaces import BaseValidator
from ..models import (
    ValidationResult, 
    ValidationStatus, 
    ResearchData,
    PRISMAResult
)
from ..utils.error_handler import (
    handle_validation_errors, 
    validate_input, 
    safe_get,
    DataError,
    ProcessingError,
    ErrorSeverity
)

logger = logging.getLogger(__name__)


class RealPRISMAValidator(BaseValidator):
    """Real implementation of PRISMA systematic review validation."""
    
    # PRISMA 2020 Checklist Items with detailed validation rules
    PRISMA_CHECKLIST = {
        # Title and Abstract
        "title": {
            "description": "Identify the report as a systematic review",
            "keywords": ["systematic review", "meta-analysis", "systematic literature review"],
            "patterns": [
                r"systematic\s+review",
                r"meta[\s-]?analysis",
                r"systematic\s+literature\s+review"
            ],
            "weight": 1.0,
            "section": "title_abstract"
        },
        "abstract": {
            "description": "Structured summary including objectives, methods, results, conclusions",
            "required_elements": ["background", "objectives", "methods", "results", "conclusions"],
            "min_elements": 3,
            "weight": 1.0,
            "section": "title_abstract"
        },
        
        # Introduction
        "rationale": {
            "description": "Describe rationale for the review",
            "keywords": ["rationale", "background", "importance", "why", "justification", "need for"],
            "min_keyword_density": 0.002,  # Keywords per total words
            "weight": 0.8,
            "section": "introduction"
        },
        "objectives": {
            "description": "Provide explicit statement of objectives or questions",
            "keywords": ["objective", "aim", "question", "hypothesis", "goal", "purpose", "seek to"],
            "patterns": [
                r"(aim|objective|purpose|goal)\s*(of|was|is|were|are)\s*to",
                r"research\s+question",
                r"we\s+(aimed|sought|intended)\s+to"
            ],
            "weight": 1.0,
            "section": "introduction"
        },
        
        # Methods
        "protocol": {
            "description": "Indicate if review protocol exists and where it can be accessed",
            "keywords": ["protocol", "PROSPERO", "registration", "registered", "CRD"],
            "patterns": [
                r"PROSPERO\s*(?:registration\s*)?(?:number\s*)?:?\s*CRD\d{9}",
                r"protocol\s+(?:was\s+)?registered",
                r"registration\s+(?:number|ID)\s*:?\s*\w+"
            ],
            "weight": 0.9,
            "section": "methods"
        },
        "eligibility_criteria": {
            "description": "Specify inclusion and exclusion criteria",
            "required_elements": ["inclusion", "exclusion"],
            "keywords": ["inclusion criteria", "exclusion criteria", "eligible", "eligibility", "included if", "excluded if"],
            "weight": 1.0,
            "section": "methods"
        },
        "information_sources": {
            "description": "Specify all databases, registers, and other sources searched",
            "required_databases": 2,  # Minimum number of databases
            "common_databases": ["PubMed", "MEDLINE", "Embase", "Cochrane", "Scopus", "Web of Science", "CINAHL", "PsycINFO"],
            "weight": 1.0,
            "section": "methods"
        },
        "search_strategy": {
            "description": "Present full search strategies for all databases",
            "required_elements": ["search terms", "Boolean operators", "truncation", "wildcards"],
            "patterns": [
                r"\bAND\b",
                r"\bOR\b",
                r"\bNOT\b",
                r"\*",
                r"\?",
                r"MeSH\s+terms?",
                r"keyword\*?"
            ],
            "weight": 1.0,
            "section": "methods"
        },
        "selection_process": {
            "description": "State the process for selecting studies",
            "keywords": ["selection", "screening", "reviewers", "independently", "duplicate", "two reviewers", "consensus"],
            "required_elements": ["independent review", "multiple reviewers"],
            "weight": 0.9,
            "section": "methods"
        },
        "data_extraction": {
            "description": "Specify methods for extracting data",
            "keywords": ["data extraction", "extracted", "data collection", "extraction form", "standardized form", "piloted"],
            "weight": 0.9,
            "section": "methods"
        },
        "quality_assessment": {
            "description": "Describe methods for assessing risk of bias",
            "keywords": ["risk of bias", "quality assessment", "validity", "critical appraisal", "Cochrane", "GRADE", "Newcastle-Ottawa", "Jadad"],
            "tools": ["Cochrane RoB", "ROBINS-I", "Newcastle-Ottawa Scale", "GRADE", "Jadad Scale", "CASP"],
            "weight": 0.9,
            "section": "methods"
        },
        "synthesis_methods": {
            "description": "Describe methods for synthesizing results",
            "keywords": ["synthesis", "meta-analysis", "pooled", "combined", "aggregated", "narrative synthesis", "statistical analysis"],
            "weight": 0.8,
            "section": "methods"
        },
        
        # Results
        "study_selection_flow": {
            "description": "Provide flow diagram of study selection",
            "keywords": ["flow diagram", "PRISMA diagram", "included", "excluded", "screened", "assessed for eligibility"],
            "patterns": [
                r"(\d+)\s+(?:studies|articles|papers)\s+(?:were\s+)?included",
                r"(\d+)\s+(?:studies|articles|papers)\s+(?:were\s+)?excluded",
                r"flow\s+(?:diagram|chart)"
            ],
            "weight": 0.9,
            "section": "results"
        },
        "study_characteristics": {
            "description": "Present characteristics of included studies",
            "keywords": ["characteristics", "study features", "participants", "interventions", "sample size", "demographics"],
            "weight": 0.8,
            "section": "results"
        },
        "risk_of_bias_results": {
            "description": "Present assessments of risk of bias",
            "keywords": ["bias assessment", "quality scores", "risk ratings", "methodological quality", "low risk", "high risk"],
            "weight": 0.8,
            "section": "results"
        },
        "synthesis_results": {
            "description": "Present results of all syntheses conducted",
            "keywords": ["results", "findings", "outcomes", "effect sizes", "confidence intervals", "p-value", "heterogeneity"],
            "patterns": [
                r"(?:95%\s*)?CI",
                r"p\s*[<=>]\s*0\.\d+",
                r"I[²2]\s*=\s*\d+%?",
                r"effect\s+size"
            ],
            "weight": 1.0,
            "section": "results"
        },
        
        # Discussion
        "summary_of_evidence": {
            "description": "Summarize the main findings",
            "keywords": ["summary", "main findings", "key results", "principal findings", "overall"],
            "weight": 0.9,
            "section": "discussion"
        },
        "limitations": {
            "description": "Discuss limitations of the evidence and review",
            "keywords": ["limitations", "weaknesses", "constraints", "shortcomings", "potential bias", "generalizability"],
            "weight": 0.8,
            "section": "discussion"
        },
        "conclusions": {
            "description": "Provide general interpretation and implications",
            "keywords": ["conclusion", "implications", "recommendations", "future research", "clinical practice"],
            "weight": 0.9,
            "section": "discussion"
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Real PRISMA Validator",
            version="2.0.0"
        )
        self._config = {
            "min_compliance_score": 0.7,
            "strict_mode": False,
            "check_registration": True,
            "min_word_count": 1000,
            "check_flow_diagram": True
        }
        
    @handle_validation_errors(exceptions=(Exception,), severity=ErrorSeverity.HIGH)
    @validate_input(required_fields=['title', 'abstract', 'methodology'], data_type=ResearchData)
    async def validate(self, data: ResearchData) -> ValidationResult:
        """
        Validate research data against PRISMA guidelines with real implementation.
        
        Args:
            data: Research data to validate
            
        Returns:
            Validation result with detailed PRISMA compliance analysis
        """
        try:
            # Extract and analyze text
            full_text = self._extract_full_text(data)
            word_count = len(full_text.split())
            
            # Check minimum length requirement
            if word_count < self._config["min_word_count"]:
                return self._create_low_quality_result(
                    f"Document too short ({word_count} words). Minimum {self._config['min_word_count']} words required for systematic review."
                )
            
            # Perform comprehensive PRISMA validation
            prisma_result = await self._perform_prisma_validation(data, full_text)
            
            # Create detailed validation result
            result = ValidationResult(
                validator_name=self.name,
                test_name="PRISMA 2020 Comprehensive Validation",
                status=ValidationStatus.PASSED if prisma_result.overall_compliance >= self._config["min_compliance_score"] else ValidationStatus.FAILED,
                score=prisma_result.overall_compliance,
                details={
                    "compliance_score": prisma_result.overall_compliance,
                    "protocol_registered": prisma_result.protocol_registered,
                    "section_scores": {
                        "search_strategy": prisma_result.search_strategy_score,
                        "selection_criteria": prisma_result.selection_criteria_score,
                        "data_extraction": prisma_result.data_extraction_score,
                        "bias_assessment": prisma_result.bias_assessment_score
                    },
                    "checklist_compliance": self._format_checklist_results(prisma_result.checklist_items),
                    "missing_critical_items": self._identify_critical_missing_items(prisma_result),
                    "quality_indicators": self._calculate_quality_indicators(data, full_text, prisma_result)
                },
                recommendations=self._generate_detailed_recommendations(prisma_result, data),
                metadata={
                    "prisma_version": "2020",
                    "word_count": word_count,
                    "items_evaluated": len(prisma_result.checklist_items),
                    "items_passed": sum(1 for v in prisma_result.checklist_items.values() if v),
                    "validation_timestamp": datetime.now().isoformat()
                }
            )
            
            return result
            
        except DataError as e:
            logger.error(f"PRISMA data error: {str(e)}")
            return self._create_error_result(str(e))
        except ProcessingError as e:
            logger.error(f"PRISMA processing error: {str(e)}")
            return self._create_error_result(str(e))
        except Exception as e:
            logger.error(f"Unexpected PRISMA validation error: {str(e)}", exc_info=True)
            raise ProcessingError(f"PRISMA validation failed: {str(e)}", severity=ErrorSeverity.HIGH)
    
    def _extract_full_text(self, data: ResearchData) -> str:
        """Extract and combine all text content for analysis."""
        text_parts = [
            safe_get(data, 'title', ''),
            safe_get(data, 'abstract', ''),
            safe_get(data, 'methodology', ''),
            safe_get(data, 'raw_content', '')
        ]
        
        # Add search terms and criteria
        search_terms = safe_get(data, 'search_terms', [])
        if search_terms:
            text_parts.append("Search terms: " + ", ".join(str(t) for t in search_terms))
        
        inclusion_criteria = safe_get(data, 'inclusion_criteria', [])
        if inclusion_criteria:
            text_parts.append("Inclusion criteria: " + "; ".join(str(c) for c in inclusion_criteria))
            
        exclusion_criteria = safe_get(data, 'exclusion_criteria', [])
        if exclusion_criteria:
            text_parts.append("Exclusion criteria: " + "; ".join(str(c) for c in exclusion_criteria))
        
        # Add paper information
        papers = safe_get(data, 'papers', [])
        if papers:
            try:
                paper_info = f"\n{len(papers)} studies included in review."
                # Sample first few paper abstracts
                for i, paper in enumerate(papers[:5]):
                    if isinstance(paper, dict):
                        title = safe_get(paper, 'title', 'Untitled')
                        abstract = safe_get(paper, 'abstract', '')
                        if abstract:
                            paper_info += f"\nStudy {i+1}: {title} - {abstract[:200]}..."
                text_parts.append(paper_info)
            except Exception as e:
                logger.warning(f"Error processing papers: {e}")
        
        return "\n\n".join(filter(None, text_parts))
    
    async def _perform_prisma_validation(self, data: ResearchData, full_text: str) -> PRISMAResult:
        """Perform comprehensive PRISMA validation with real logic."""
        checklist_results = {}
        missing_elements = []
        recommendations = []
        
        # Validate each PRISMA checklist item
        for item_id, item_config in self.PRISMA_CHECKLIST.items():
            is_compliant, confidence, details = self._validate_checklist_item(
                item_id, item_config, data, full_text
            )
            
            checklist_results[item_id] = is_compliant
            
            if not is_compliant:
                missing_elements.append(item_id)
                recommendations.append(
                    f"{item_config['description']} (Missing: {item_id})"
                )
                
                # Add specific guidance based on what's missing
                if item_id == "protocol" and self._config["check_registration"]:
                    recommendations.append(
                        "Register your protocol on PROSPERO (https://www.crd.york.ac.uk/prospero/)"
                    )
                elif item_id == "study_selection_flow" and self._config["check_flow_diagram"]:
                    recommendations.append(
                        "Create a PRISMA flow diagram using the template at http://prisma-statement.org/prismastatement/flowdiagram"
                    )
        
        # Calculate detailed scores
        protocol_registered = self._check_protocol_registration(data, full_text)
        search_strategy_score = self._calculate_search_strategy_score(data, full_text, checklist_results)
        selection_criteria_score = self._calculate_selection_criteria_score(data, checklist_results)
        data_extraction_score = self._calculate_data_extraction_score(data, full_text, checklist_results)
        bias_assessment_score = self._calculate_bias_assessment_score(full_text, checklist_results)
        
        # Calculate overall compliance
        overall_compliance = self._calculate_weighted_compliance(checklist_results)
        
        return PRISMAResult(
            protocol_registered=protocol_registered,
            search_strategy_score=search_strategy_score,
            selection_criteria_score=selection_criteria_score,
            data_extraction_score=data_extraction_score,
            bias_assessment_score=bias_assessment_score,
            overall_compliance=overall_compliance,
            checklist_items=checklist_results,
            missing_elements=missing_elements,
            recommendations=recommendations[:10]  # Top 10 most important
        )
    
    def _validate_checklist_item(
        self, 
        item_id: str, 
        item_config: Dict[str, Any],
        data: ResearchData,
        full_text: str
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Validate a single PRISMA checklist item with detailed analysis.
        
        Returns:
            Tuple of (is_compliant, confidence_score, details)
        """
        text_lower = full_text.lower()
        details = {"item": item_id}
        
        # Check patterns if defined
        if "patterns" in item_config:
            pattern_matches = []
            for pattern in item_config["patterns"]:
                matches = re.findall(pattern, text_lower)
                if matches:
                    pattern_matches.extend(matches)
            
            if pattern_matches:
                details["pattern_matches"] = pattern_matches[:5]  # First 5 matches
                return True, 0.9, details
        
        # Check keywords
        if "keywords" in item_config:
            keyword_hits = 0
            found_keywords = []
            
            for keyword in item_config["keywords"]:
                if keyword.lower() in text_lower:
                    keyword_hits += 1
                    found_keywords.append(keyword)
            
            if keyword_hits > 0:
                confidence = min(keyword_hits / len(item_config["keywords"]), 1.0)
                details["keywords_found"] = found_keywords
                details["keyword_coverage"] = confidence
                
                # Apply minimum keyword density check if specified
                if "min_keyword_density" in item_config:
                    word_count = len(full_text.split())
                    density = keyword_hits / word_count
                    if density >= item_config["min_keyword_density"]:
                        return True, confidence, details
                else:
                    return keyword_hits >= 2, confidence, details  # Need at least 2 keywords
        
        # Check required elements
        if "required_elements" in item_config:
            found_elements = []
            
            if item_id == "abstract":
                # Special handling for structured abstract
                abstract_lower = data.abstract.lower()
                for element in item_config["required_elements"]:
                    if element in abstract_lower or f"{element}:" in abstract_lower:
                        found_elements.append(element)
                
                min_required = item_config.get("min_elements", len(item_config["required_elements"]))
                is_compliant = len(found_elements) >= min_required
                confidence = len(found_elements) / len(item_config["required_elements"])
                details["elements_found"] = found_elements
                return is_compliant, confidence, details
                
            elif item_id == "eligibility_criteria":
                # Check for inclusion/exclusion criteria
                has_inclusion = bool(data.inclusion_criteria) or "inclusion criteria" in text_lower
                has_exclusion = bool(data.exclusion_criteria) or "exclusion criteria" in text_lower
                
                if has_inclusion:
                    found_elements.append("inclusion")
                if has_exclusion:
                    found_elements.append("exclusion")
                
                is_compliant = has_inclusion and has_exclusion
                confidence = len(found_elements) / 2
                details["has_inclusion"] = has_inclusion
                details["has_exclusion"] = has_exclusion
                return is_compliant, confidence, details
        
        # Check for databases (information_sources)
        if item_id == "information_sources":
            databases_found = []
            for db in item_config["common_databases"]:
                if db.lower() in text_lower:
                    databases_found.append(db)
            
            # Also check explicitly provided databases
            if data.databases_used:
                databases_found.extend(data.databases_used)
            
            databases_found = list(set(databases_found))  # Remove duplicates
            is_compliant = len(databases_found) >= item_config["required_databases"]
            confidence = min(len(databases_found) / 3, 1.0)  # 3+ databases is excellent
            details["databases_found"] = databases_found
            return is_compliant, confidence, details
        
        # Check for quality assessment tools
        if item_id == "quality_assessment":
            tools_found = []
            for tool in item_config.get("tools", []):
                if tool.lower() in text_lower:
                    tools_found.append(tool)
            
            has_keywords = any(kw in text_lower for kw in item_config["keywords"])
            is_compliant = len(tools_found) > 0 or has_keywords
            confidence = 0.9 if tools_found else (0.6 if has_keywords else 0.0)
            details["tools_found"] = tools_found
            return is_compliant, confidence, details
        
        # Default: item not found
        return False, 0.0, details
    
    def _check_protocol_registration(self, data: ResearchData, full_text: str) -> bool:
        """Check if the systematic review protocol is properly registered."""
        # Check explicit registration
        if safe_get(data, 'protocol_registration'):
            return True
        
        # Check for PROSPERO registration pattern
        prospero_pattern = r"PROSPERO\s*(?:registration\s*)?(?:number\s*)?:?\s*CRD\d{9}"
        if re.search(prospero_pattern, full_text, re.IGNORECASE):
            return True
        
        # Check for other registration mentions
        registration_keywords = [
            "protocol registered",
            "protocol was registered",
            "registered protocol",
            "registration number",
            "protocol registration"
        ]
        
        text_lower = full_text.lower()
        return any(keyword in text_lower for keyword in registration_keywords)
    
    def _calculate_search_strategy_score(
        self, 
        data: ResearchData, 
        full_text: str,
        checklist_results: Dict[str, bool]
    ) -> float:
        """Calculate comprehensive search strategy score."""
        scores = []
        
        # Database coverage (0-1)
        if data.databases_used:
            db_score = min(len(data.databases_used) / 3, 1.0)
            scores.append(db_score)
        else:
            # Check text for database mentions
            common_dbs = ["pubmed", "medline", "embase", "cochrane", "scopus", "web of science"]
            db_count = sum(1 for db in common_dbs if db in full_text.lower())
            scores.append(min(db_count / 3, 1.0))
        
        # Search terms complexity (0-1)
        if data.search_terms:
            # Check for Boolean operators
            has_boolean = any(
                term for term in data.search_terms 
                if any(op in term.upper() for op in ["AND", "OR", "NOT"])
            )
            term_score = min(len(data.search_terms) / 5, 0.8) + (0.2 if has_boolean else 0)
            scores.append(term_score)
        else:
            scores.append(0.0)
        
        # Date range specified (0-1)
        date_patterns = [
            r"\b\d{4}\s*-\s*\d{4}\b",
            r"from\s+\d{4}\s+to\s+\d{4}",
            r"between\s+\d{4}\s+and\s+\d{4}",
            r"since\s+\d{4}",
            r"last\s+\d+\s+years?"
        ]
        
        has_date_range = any(re.search(pattern, full_text.lower()) for pattern in date_patterns)
        if data.date_range or has_date_range:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        # PRISMA checklist items
        if checklist_results.get("search_strategy", False):
            scores.append(1.0)
        if checklist_results.get("information_sources", False):
            scores.append(1.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_selection_criteria_score(
        self, 
        data: ResearchData,
        checklist_results: Dict[str, bool]
    ) -> float:
        """Calculate selection criteria quality score."""
        scores = []
        
        # Inclusion criteria
        if data.inclusion_criteria:
            # Quality based on number and specificity
            inc_score = min(len(data.inclusion_criteria) / 5, 1.0)
            scores.append(inc_score)
        else:
            scores.append(0.0)
        
        # Exclusion criteria
        if data.exclusion_criteria:
            exc_score = min(len(data.exclusion_criteria) / 3, 1.0)
            scores.append(exc_score)
        else:
            scores.append(0.0)
        
        # PRISMA checklist compliance
        if checklist_results.get("eligibility_criteria", False):
            scores.append(1.0)
        
        if checklist_results.get("selection_process", False):
            scores.append(1.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_data_extraction_score(
        self, 
        data: ResearchData,
        full_text: str,
        checklist_results: Dict[str, bool]
    ) -> float:
        """Calculate data extraction methodology score."""
        scores = []
        
        # Extraction method specified
        if data.extraction_method:
            scores.append(1.0)
        else:
            # Check text for extraction methodology
            extraction_keywords = [
                "data extraction form",
                "extraction template",
                "standardized form",
                "piloted",
                "extracted data",
                "data were extracted"
            ]
            
            text_lower = full_text.lower()
            keyword_count = sum(1 for kw in extraction_keywords if kw in text_lower)
            scores.append(min(keyword_count / 2, 1.0))
        
        # Fields extracted
        if data.extracted_fields:
            field_score = min(len(data.extracted_fields) / 8, 1.0)  # 8+ fields is comprehensive
            scores.append(field_score)
        else:
            scores.append(0.0)
        
        # Independent extraction mentioned
        if "independent" in full_text.lower() and "extract" in full_text.lower():
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        # PRISMA checklist
        if checklist_results.get("data_extraction", False):
            scores.append(1.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_bias_assessment_score(
        self, 
        full_text: str,
        checklist_results: Dict[str, bool]
    ) -> float:
        """Calculate bias assessment quality score."""
        scores = []
        text_lower = full_text.lower()
        
        # Check for bias assessment tools
        bias_tools = [
            "cochrane risk of bias",
            "rob 2",
            "robins-i",
            "newcastle-ottawa",
            "jadad scale",
            "grade",
            "casp",
            "critical appraisal"
        ]
        
        tools_found = sum(1 for tool in bias_tools if tool in text_lower)
        if tools_found > 0:
            scores.append(min(tools_found / 2, 1.0))  # 2+ tools is excellent
        else:
            scores.append(0.0)
        
        # Check for bias-related terms
        bias_terms = [
            "risk of bias",
            "methodological quality",
            "quality assessment",
            "bias assessment",
            "study quality",
            "internal validity",
            "external validity"
        ]
        
        terms_found = sum(1 for term in bias_terms if term in text_lower)
        scores.append(min(terms_found / 3, 1.0))
        
        # Check for bias categories
        bias_categories = [
            "selection bias",
            "performance bias",
            "detection bias",
            "attrition bias",
            "reporting bias",
            "publication bias"
        ]
        
        categories_found = sum(1 for cat in bias_categories if cat in text_lower)
        if categories_found > 0:
            scores.append(min(categories_found / 3, 1.0))
        
        # PRISMA checklist
        if checklist_results.get("quality_assessment", False):
            scores.append(1.0)
        if checklist_results.get("risk_of_bias_results", False):
            scores.append(1.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_weighted_compliance(self, checklist_results: Dict[str, bool]) -> float:
        """Calculate overall PRISMA compliance with weighted scoring."""
        total_weight = 0.0
        weighted_score = 0.0
        
        for item_id, is_compliant in checklist_results.items():
            item_config = self.PRISMA_CHECKLIST.get(item_id, {})
            weight = item_config.get("weight", 1.0)
            
            total_weight += weight
            if is_compliant:
                weighted_score += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _format_checklist_results(self, checklist_items: Dict[str, bool]) -> Dict[str, Any]:
        """Format checklist results by section with detailed analysis."""
        sections = {
            "title_abstract": [],
            "introduction": [],
            "methods": [],
            "results": [],
            "discussion": []
        }
        
        # Group items by section
        for item_id, item_config in self.PRISMA_CHECKLIST.items():
            section = item_config.get("section", "other")
            if section in sections:
                sections[section].append({
                    "item": item_id,
                    "description": item_config["description"],
                    "compliant": checklist_items.get(item_id, False),
                    "weight": item_config.get("weight", 1.0)
                })
        
        # Calculate section compliance
        formatted_results = {}
        for section, items in sections.items():
            if items:
                compliant_items = sum(1 for item in items if item["compliant"])
                total_items = len(items)
                weighted_score = sum(
                    item["weight"] for item in items if item["compliant"]
                ) / sum(item["weight"] for item in items)
                
                formatted_results[section] = {
                    "compliant": compliant_items,
                    "total": total_items,
                    "percentage": (compliant_items / total_items * 100),
                    "weighted_score": weighted_score,
                    "items": items
                }
        
        return formatted_results
    
    def _identify_critical_missing_items(self, prisma_result: PRISMAResult) -> List[str]:
        """Identify critical missing PRISMA items."""
        critical_items = [
            "title", "objectives", "eligibility_criteria", 
            "information_sources", "search_strategy", "synthesis_results"
        ]
        
        critical_missing = []
        for item in critical_items:
            if item in prisma_result.missing_elements:
                item_config = self.PRISMA_CHECKLIST.get(item, {})
                critical_missing.append({
                    "item": item,
                    "description": item_config.get("description", ""),
                    "importance": "CRITICAL"
                })
        
        return critical_missing
    
    def _calculate_quality_indicators(
        self, 
        data: ResearchData, 
        full_text: str,
        prisma_result: PRISMAResult
    ) -> Dict[str, Any]:
        """Calculate additional quality indicators beyond PRISMA."""
        indicators = {}
        
        # Research scope
        indicators["paper_count"] = len(data.papers) if data.papers else 0
        indicators["database_count"] = len(data.databases_used) if data.databases_used else 0
        indicators["search_term_count"] = len(data.search_terms) if data.search_terms else 0
        
        # Transparency indicators
        text_lower = full_text.lower()
        indicators["has_limitations_section"] = "limitations" in prisma_result.checklist_items and prisma_result.checklist_items["limitations"]
        indicators["has_flow_diagram"] = "flow diagram" in text_lower or "prisma diagram" in text_lower
        indicators["has_supplementary_materials"] = any(
            term in text_lower 
            for term in ["supplementary", "appendix", "additional file", "online resource"]
        )
        
        # Methodological rigor
        indicators["uses_quality_assessment_tool"] = prisma_result.bias_assessment_score > 0.5
        indicators["has_protocol_registration"] = prisma_result.protocol_registered
        indicators["multiple_reviewers"] = "two reviewers" in text_lower or "independent" in text_lower
        
        # Calculate overall quality score
        quality_components = [
            indicators["paper_count"] >= 20,
            indicators["database_count"] >= 3,
            indicators["has_limitations_section"],
            indicators["uses_quality_assessment_tool"],
            indicators["has_protocol_registration"],
            indicators["multiple_reviewers"]
        ]
        
        indicators["overall_quality_score"] = sum(quality_components) / len(quality_components)
        
        return indicators
    
    def _generate_detailed_recommendations(
        self, 
        prisma_result: PRISMAResult,
        data: ResearchData
    ) -> List[str]:
        """Generate specific, actionable recommendations."""
        recommendations = []
        
        # Protocol registration
        if not prisma_result.protocol_registered:
            recommendations.append(
                "CRITICAL: Register your systematic review protocol on PROSPERO "
                "(https://www.crd.york.ac.uk/prospero/) before data extraction begins"
            )
        
        # Search strategy
        if prisma_result.search_strategy_score < 0.7:
            if not data.databases_used or len(data.databases_used) < 3:
                recommendations.append(
                    "Expand database coverage: Include at least 3 databases "
                    "(e.g., PubMed, Embase, Cochrane Library)"
                )
            
            if not data.search_terms or len(data.search_terms) < 5:
                recommendations.append(
                    "Develop comprehensive search strategy with Boolean operators, "
                    "MeSH terms, and synonyms for key concepts"
                )
        
        # Selection criteria
        if prisma_result.selection_criteria_score < 0.7:
            if not data.inclusion_criteria:
                recommendations.append(
                    "Define explicit inclusion criteria using PICOS framework "
                    "(Population, Intervention, Comparison, Outcome, Study design)"
                )
            
            if not data.exclusion_criteria:
                recommendations.append(
                    "Specify exclusion criteria to ensure reproducible study selection"
                )
        
        # Data extraction
        if prisma_result.data_extraction_score < 0.7:
            recommendations.append(
                "Develop standardized data extraction form and pilot it on 2-3 studies"
            )
            
            if not data.extraction_method:
                recommendations.append(
                    "Document data extraction process including independent extraction "
                    "by two reviewers and conflict resolution method"
                )
        
        # Bias assessment
        if prisma_result.bias_assessment_score < 0.7:
            recommendations.append(
                "Implement formal bias assessment using validated tools "
                "(e.g., Cochrane RoB 2 for RCTs, ROBINS-I for non-randomized studies)"
            )
        
        # Missing critical items
        critical_missing = self._identify_critical_missing_items(prisma_result)
        for item in critical_missing[:3]:  # Top 3 critical items
            recommendations.append(
                f"Add missing critical element: {item['description']}"
            )
        
        # Flow diagram
        if "study_selection_flow" in prisma_result.missing_elements:
            recommendations.append(
                "Create PRISMA flow diagram showing study selection process "
                "(template: http://prisma-statement.org/prismastatement/flowdiagram)"
            )
        
        # General quality improvements
        if len(data.papers) < 20:
            recommendations.append(
                "Consider expanding search to capture more relevant studies "
                "(current: {len(data.papers)} studies)"
            )
        
        return recommendations[:10]  # Return top 10 most important
    
    def _create_low_quality_result(self, message: str) -> ValidationResult:
        """Create result for low-quality input."""
        return ValidationResult(
            validator_name=self.name,
            test_name="PRISMA 2020 Compliance Check",
            status=ValidationStatus.FAILED,
            score=0.0,
            error_message=message,
            recommendations=[
                "Ensure document contains complete systematic review content",
                "Include all major sections: Introduction, Methods, Results, Discussion",
                "Provide detailed methodology following PRISMA guidelines"
            ]
        )
    
    def _create_error_result(self, error_message: str) -> ValidationResult:
        """Create error result."""
        return ValidationResult(
            validator_name=self.name,
            test_name="PRISMA 2020 Compliance Check",
            status=ValidationStatus.ERROR,
            score=0.0,
            error_message=f"Validation error: {error_message}",
            recommendations=[
                "Fix validation errors and retry",
                "Ensure research data is properly formatted",
                "Contact support if issue persists"
            ]
        )