"""
Citation Accuracy Validator for academic research validation.

This module imports and uses the real citation validator implementation.
"""

# Import the real implementation
from .real_citation_validator import RealCitationValidator

# Create alias for backward compatibility
class CitationAccuracyValidator(RealCitationValidator):
    """
    Validates citation accuracy, formatting, and completeness.
    
    Supports multiple citation styles (APA, MLA, Chicago, IEEE, Harvard, etc.)
    and validates against academic standards.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="Citation_Accuracy_Validator",
            description="Validates citation formatting, accuracy, and completeness",
            version="1.0.0",
            config=config or {}
        )
        
        # Citation style patterns
        self.citation_patterns = {
            "APA": {
                "journal": r"(\w+,\s*\w+\.\s*\w*\.?\s*)\((\d{4})\)\.\s*(.*?)\.\s*(.*?),\s*(\d+).*",
                "book": r"(\w+,\s*\w+\.\s*\w*\.?\s*)\((\d{4})\)\.\s*(.*?)\.\s*(.*?):\s*(.*?)\.",
                "web": r"(\w+,\s*\w+\.\s*\w*\.?\s*)\((\d{4})\)\.\s*(.*?)\.\s*Retrieved from (.*?)"
            },
            "MLA": {
                "journal": r"(\w+,\s*\w+).\s*\"(.*?)\"\s*(.*?)\s*(\d+)\s*\((\d{4})\):\s*(\d+-?\d*)\.",
                "book": r"(\w+,\s*\w+).\s*(.*?)\.\s*(.*?):\s*(.*?),\s*(\d{4})\.",
                "web": r"(\w+,\s*\w+).\s*\"(.*?)\"\s*(.*?)\.\s*Web\.\s*(\d+\s*\w+\s*\d{4})\."
            },
            "IEEE": {
                "journal": r"\[(\d+)\]\s*(\w+\.\s*\w+).*,\s*\"(.*?)\",\s*(.*?),\s*vol\.\s*(\d+),.*pp\.\s*(\d+-?\d*),\s*(\d{4})\.",
                "book": r"\[(\d+)\]\s*(\w+\.\s*\w+).*,\s*(.*?)\.\s*(.*?):\s*(.*?),\s*(\d{4})\.",
                "web": r"\[(\d+)\]\s*(.*?)\.\s*\[Online\]\.\s*Available:\s*(.*?)\."
            },
            "Chicago": {
                "journal": r"(\w+,\s*\w+).\s*\"(.*?)\"\s*(.*?)\s*(\d+),\s*no\.\s*(\d+)\s*\((\d{4})\):\s*(\d+-?\d*)\.",
                "book": r"(\w+,\s*\w+).\s*(.*?)\.\s*(.*?):\s*(.*?),\s*(\d{4})\.",
                "web": r"(\w+,\s*\w+).\s*\"(.*?)\"\s*Accessed\s*(.*?)\.\s*(.*?)\."
            }
        }
        
        # Required citation elements
        self.required_elements = {
            "journal": ["author", "year", "title", "journal", "volume"],
            "book": ["author", "year", "title", "publisher"],
            "web": ["author", "year", "title", "url"],
            "conference": ["author", "year", "title", "conference", "location"]
        }
        
        # Citation quality metrics
        self.quality_metrics = {
            "format_accuracy": 0.25,
            "completeness": 0.25,
            "consistency": 0.20,
            "recency": 0.15,
            "relevance": 0.15
        }
    
    async def _initialize_validator(self) -> None:
        """Initialize citation validator."""
        pass
    
    async def validate(
        self,
        research_output: Any,
        context: Optional[ValidationContext] = None,
        **kwargs: Any
    ) -> List[ValidationResult]:
        """
        Validate citation accuracy and formatting.
        
        Returns multiple validation results for different citation aspects.
        """
        citations = self._extract_citations(research_output)
        text_content = self._extract_text_content(research_output)
        citation_style = self._detect_citation_style(citations, context)
        
        results = []
        
        # Validate overall citation accuracy
        overall_result = await self._validate_overall_accuracy(citations, citation_style)
        results.append(overall_result)
        
        # Validate citation formatting
        format_result = await self._validate_formatting(citations, citation_style)
        results.append(format_result)
        
        # Validate citation completeness
        completeness_result = await self._validate_completeness(citations)
        results.append(completeness_result)
        
        # Validate citation consistency
        consistency_result = await self._validate_consistency(citations, citation_style)
        results.append(consistency_result)
        
        # Validate citation recency and relevance
        quality_result = await self._validate_citation_quality(citations, text_content)
        results.append(quality_result)
        
        # Validate in-text citations
        intext_result = await self._validate_intext_citations(text_content, citations, citation_style)
        results.append(intext_result)
        
        return results
    
    def _detect_citation_style(
        self, 
        citations: List[Dict[str, Any]], 
        context: Optional[ValidationContext] = None
    ) -> str:
        """Detect the citation style used."""
        if context and context.citation_style:
            return context.citation_style
        
        # Try to detect style from citation patterns
        style_scores = {}
        
        for style, patterns in self.citation_patterns.items():
            score = 0
            for citation in citations[:10]:  # Check first 10 citations
                citation_text = citation.get("text", "")
                for pattern_type, pattern in patterns.items():
                    if re.search(pattern, citation_text):
                        score += 1
                        break
            style_scores[style] = score
        
        # Return style with highest score, default to APA
        if style_scores:
            detected_style = max(style_scores, key=style_scores.get)
            if style_scores[detected_style] > 0:
                return detected_style
        
        return "APA"  # Default to APA
    
    async def _validate_overall_accuracy(
        self, 
        citations: List[Dict[str, Any]], 
        citation_style: str
    ) -> ValidationResult:
        """Validate overall citation accuracy."""
        
        if not citations:
            return self._create_result(
                test_name="citation_overall_accuracy",
                status="failed",
                score=0.0,
                details={"error": "No citations found"},
                metadata={"citation_count": 0}
            )
        
        accuracy_scores = {}
        
        # Format accuracy
        format_score = self._calculate_format_accuracy(citations, citation_style)
        accuracy_scores["format"] = format_score
        
        # Completeness score
        completeness_score = self._calculate_completeness_score(citations)
        accuracy_scores["completeness"] = completeness_score
        
        # Consistency score
        consistency_score = self._calculate_consistency_score(citations, citation_style)
        accuracy_scores["consistency"] = consistency_score
        
        # Calculate overall score
        overall_score = self._calculate_composite_score(accuracy_scores, self.quality_metrics)
        
        status = "passed" if overall_score >= 0.80 else "failed"
        
        return self._create_result(
            test_name="citation_overall_accuracy",
            status=status,
            score=overall_score,
            details={
                "citation_style": citation_style,
                "accuracy_breakdown": accuracy_scores,
                "total_citations": len(citations),
                "recommendations": self._generate_accuracy_recommendations(accuracy_scores)
            },
            metadata={
                "citation_count": len(citations),
                "style_detected": citation_style,
                "quality_threshold": 0.80
            }
        )
    
    async def _validate_formatting(
        self, 
        citations: List[Dict[str, Any]], 
        citation_style: str
    ) -> ValidationResult:
        """Validate citation formatting according to style guide."""
        
        format_score = self._calculate_format_accuracy(citations, citation_style)
        
        # Analyze formatting issues
        formatting_issues = []
        well_formatted_citations = 0
        
        patterns = self.citation_patterns.get(citation_style, {})
        
        for i, citation in enumerate(citations):
            citation_text = citation.get("text", "")
            citation_formatted = False
            
            for pattern_type, pattern in patterns.items():
                if re.search(pattern, citation_text):
                    citation_formatted = True
                    well_formatted_citations += 1
                    break
            
            if not citation_formatted:
                formatting_issues.append({
                    "citation_index": i,
                    "citation_text": citation_text[:100] + "..." if len(citation_text) > 100 else citation_text,
                    "issue": "Does not match standard formatting pattern"
                })
        
        status = "passed" if format_score >= 0.85 else "failed"
        
        return self._create_result(
            test_name="citation_formatting",
            status=status,
            score=format_score,
            details={
                "citation_style": citation_style,
                "well_formatted_count": well_formatted_citations,
                "formatting_issues": formatting_issues[:10],  # Limit to first 10 issues
                "formatting_patterns_checked": len(patterns),
                "recommendations": self._generate_formatting_recommendations(citation_style, formatting_issues)
            },
            metadata={
                "total_citations": len(citations),
                "issues_found": len(formatting_issues)
            }
        )
    
    async def _validate_completeness(self, citations: List[Dict[str, Any]]) -> ValidationResult:
        """Validate citation completeness."""
        
        completeness_score = self._calculate_completeness_score(citations)
        
        # Analyze missing elements
        incomplete_citations = []
        element_counts = {element: 0 for element_type in self.required_elements.values() 
                         for element in element_type}
        
        for i, citation in enumerate(citations):
            citation_text = citation.get("text", "")
            missing_elements = []
            
            # Detect citation type
            citation_type = self._detect_citation_type(citation_text)
            required = self.required_elements.get(citation_type, self.required_elements["journal"])
            
            for element in required:
                if self._has_element(citation_text, element):
                    element_counts[element] += 1
                else:
                    missing_elements.append(element)
            
            if missing_elements:
                incomplete_citations.append({
                    "citation_index": i,
                    "citation_type": citation_type,
                    "missing_elements": missing_elements,
                    "citation_preview": citation_text[:100] + "..." if len(citation_text) > 100 else citation_text
                })
        
        status = "passed" if completeness_score >= 0.80 else "failed"
        
        return self._create_result(
            test_name="citation_completeness",
            status=status,
            score=completeness_score,
            details={
                "element_presence": element_counts,
                "incomplete_citations": incomplete_citations[:10],
                "completeness_by_element": {
                    element: count / len(citations) if citations else 0
                    for element, count in element_counts.items()
                },
                "recommendations": self._generate_completeness_recommendations(element_counts, len(citations))
            },
            metadata={
                "total_citations": len(citations),
                "incomplete_count": len(incomplete_citations)
            }
        )
    
    async def _validate_consistency(
        self, 
        citations: List[Dict[str, Any]], 
        citation_style: str
    ) -> ValidationResult:
        """Validate citation consistency across the document."""
        
        consistency_score = self._calculate_consistency_score(citations, citation_style)
        
        # Analyze consistency issues
        consistency_issues = []
        
        # Check author name formatting consistency
        author_formats = []
        for citation in citations:
            citation_text = citation.get("text", "")
            author_format = self._extract_author_format(citation_text)
            if author_format:
                author_formats.append(author_format)
        
        author_format_consistency = len(set(author_formats)) <= 1 if author_formats else True
        
        if not author_format_consistency:
            consistency_issues.append({
                "issue": "Inconsistent author name formatting",
                "formats_found": list(set(author_formats))
            })
        
        # Check date formatting consistency
        date_formats = []
        for citation in citations:
            citation_text = citation.get("text", "")
            date_format = self._extract_date_format(citation_text)
            if date_format:
                date_formats.append(date_format)
        
        date_format_consistency = len(set(date_formats)) <= 1 if date_formats else True
        
        if not date_format_consistency:
            consistency_issues.append({
                "issue": "Inconsistent date formatting",
                "formats_found": list(set(date_formats))
            })
        
        status = "passed" if consistency_score >= 0.75 else "failed"
        
        return self._create_result(
            test_name="citation_consistency",
            status=status,
            score=consistency_score,
            details={
                "citation_style": citation_style,
                "consistency_issues": consistency_issues,
                "author_format_consistency": author_format_consistency,
                "date_format_consistency": date_format_consistency,
                "recommendations": self._generate_consistency_recommendations(consistency_issues)
            },
            metadata={
                "total_citations": len(citations),
                "issues_found": len(consistency_issues)
            }
        )
    
    async def _validate_citation_quality(
        self, 
        citations: List[Dict[str, Any]], 
        text_content: str
    ) -> ValidationResult:
        """Validate citation quality (recency, relevance, diversity)."""
        
        # Analyze citation years
        citation_years = []
        for citation in citations:
            year = self._extract_year(citation.get("text", ""))
            if year:
                citation_years.append(year)
        
        current_year = datetime.now().year
        recent_citations = sum(1 for year in citation_years if current_year - year <= 5)
        recency_score = recent_citations / len(citation_years) if citation_years else 0.0
        
        # Analyze source diversity
        source_types = {"journal": 0, "book": 0, "web": 0, "conference": 0}
        for citation in citations:
            citation_type = self._detect_citation_type(citation.get("text", ""))
            source_types[citation_type] = source_types.get(citation_type, 0) + 1
        
        diversity_score = len([count for count in source_types.values() if count > 0]) / len(source_types)
        
        # Analyze relevance (basic keyword matching)
        relevance_score = self._calculate_relevance_score(citations, text_content)
        
        # Calculate overall quality score
        quality_scores = {
            "recency": recency_score,
            "diversity": diversity_score,
            "relevance": relevance_score
        }
        
        overall_quality = sum(quality_scores.values()) / len(quality_scores)
        
        status = "passed" if overall_quality >= 0.70 else "failed"
        
        return self._create_result(
            test_name="citation_quality",
            status=status,
            score=overall_quality,
            details={
                "quality_metrics": quality_scores,
                "citation_years": citation_years,
                "year_distribution": self._analyze_year_distribution(citation_years),
                "source_distribution": source_types,
                "recent_citations_count": recent_citations,
                "recommendations": self._generate_quality_recommendations(quality_scores, source_types)
            },
            metadata={
                "total_citations": len(citations),
                "years_analyzed": len(citation_years),
                "current_year": current_year
            }
        )
    
    async def _validate_intext_citations(
        self, 
        text_content: str, 
        citations: List[Dict[str, Any]], 
        citation_style: str
    ) -> ValidationResult:
        """Validate in-text citations match reference list."""
        
        # Extract in-text citations based on style
        intext_citations = self._extract_intext_citations(text_content, citation_style)
        
        # Compare with reference list
        reference_authors = []
        for citation in citations:
            authors = self._extract_authors(citation.get("text", ""))
            reference_authors.extend(authors)
        
        matched_citations = 0
        unmatched_intext = []
        
        for intext in intext_citations:
            if any(author.lower() in intext.lower() for author in reference_authors):
                matched_citations += 1
            else:
                unmatched_intext.append(intext)
        
        match_score = matched_citations / len(intext_citations) if intext_citations else 1.0
        
        status = "passed" if match_score >= 0.90 else "failed"
        
        return self._create_result(
            test_name="intext_citation_matching",
            status=status,
            score=match_score,
            details={
                "citation_style": citation_style,
                "intext_citations_found": len(intext_citations),
                "matched_citations": matched_citations,
                "unmatched_intext": unmatched_intext[:10],
                "match_rate": match_score,
                "recommendations": self._generate_intext_recommendations(match_score, unmatched_intext)
            },
            metadata={
                "total_intext": len(intext_citations),
                "total_references": len(citations)
            }
        )
    
    # Helper methods for citation analysis
    
    def _calculate_format_accuracy(self, citations: List[Dict[str, Any]], style: str) -> float:
        """Calculate formatting accuracy score."""
        if not citations:
            return 0.0
        
        patterns = self.citation_patterns.get(style, {})
        if not patterns:
            return 0.5  # Neutral score if style not recognized
        
        accurate_count = 0
        for citation in citations:
            citation_text = citation.get("text", "")
            for pattern in patterns.values():
                if re.search(pattern, citation_text):
                    accurate_count += 1
                    break
        
        return accurate_count / len(citations)
    
    def _calculate_completeness_score(self, citations: List[Dict[str, Any]]) -> float:
        """Calculate citation completeness score."""
        if not citations:
            return 0.0
        
        total_score = 0.0
        for citation in citations:
            citation_text = citation.get("text", "")
            citation_type = self._detect_citation_type(citation_text)
            required = self.required_elements.get(citation_type, self.required_elements["journal"])
            
            present_count = sum(1 for element in required if self._has_element(citation_text, element))
            citation_score = present_count / len(required)
            total_score += citation_score
        
        return total_score / len(citations)
    
    def _calculate_consistency_score(self, citations: List[Dict[str, Any]], style: str) -> float:
        """Calculate citation consistency score."""
        if len(citations) <= 1:
            return 1.0
        
        # Check various consistency aspects
        consistency_checks = []
        
        # Author format consistency
        author_formats = [self._extract_author_format(c.get("text", "")) for c in citations]
        author_formats = [f for f in author_formats if f]
        author_consistency = len(set(author_formats)) <= 1 if author_formats else True
        consistency_checks.append(author_consistency)
        
        # Date format consistency
        date_formats = [self._extract_date_format(c.get("text", "")) for c in citations]
        date_formats = [f for f in date_formats if f]
        date_consistency = len(set(date_formats)) <= 1 if date_formats else True
        consistency_checks.append(date_consistency)
        
        return sum(consistency_checks) / len(consistency_checks)
    
    def _detect_citation_type(self, citation_text: str) -> str:
        """Detect the type of citation (journal, book, web, etc.)."""
        citation_lower = citation_text.lower()
        
        # Journal indicators
        if any(indicator in citation_lower for indicator in 
               ["journal", "vol.", "volume", "pp.", "pages", "issue"]):
            return "journal"
        
        # Book indicators
        elif any(indicator in citation_lower for indicator in 
                ["publisher", "press", "edition", "isbn"]):
            return "book"
        
        # Web indicators
        elif any(indicator in citation_lower for indicator in 
                ["http", "www", "url", "retrieved", "accessed", "available"]):
            return "web"
        
        # Conference indicators
        elif any(indicator in citation_lower for indicator in 
                ["conference", "proceedings", "symposium", "workshop"]):
            return "conference"
        
        return "journal"  # Default to journal
    
    def _has_element(self, citation_text: str, element: str) -> bool:
        """Check if citation has required element."""
        patterns = {
            "author": r"\b[A-Z][a-z]+,\s*[A-Z]",
            "year": r"\b(19|20)\d{2}\b",
            "title": r'["\'](.*?)["\']',
            "journal": r'\b[A-Z][a-z]+.*Journal\b|\b[A-Z][a-z]+.*Review\b',
            "volume": r'\bvol\.?\s*\d+\b|\bvolume\s*\d+\b',
            "publisher": r'\b[A-Z][a-z]+\s+(Press|Publishers?)\b',
            "url": r'https?://\S+',
            "conference": r'\b(Conference|Proceedings|Symposium)\b'
        }
        
        pattern = patterns.get(element)
        if pattern:
            return bool(re.search(pattern, citation_text, re.IGNORECASE))
        
        return element.lower() in citation_text.lower()
    
    def _extract_year(self, citation_text: str) -> Optional[int]:
        """Extract publication year from citation."""
        year_match = re.search(r'\b(19|20)(\d{2})\b', citation_text)
        if year_match:
            return int(year_match.group(0))
        return None
    
    def _extract_authors(self, citation_text: str) -> List[str]:
        """Extract author names from citation."""
        # Simple extraction - look for lastname, firstname patterns
        author_pattern = r'\b([A-Z][a-z]+),\s*([A-Z]\.?\s*)+\b'
        matches = re.findall(author_pattern, citation_text)
        return [f"{match[0]}, {match[1].strip()}" for match in matches]
    
    def _extract_author_format(self, citation_text: str) -> Optional[str]:
        """Extract author formatting pattern."""
        # Lastname, F. format
        if re.search(r'\b[A-Z][a-z]+,\s*[A-Z]\.\b', citation_text):
            return "lastname_initial"
        # Lastname, Firstname format
        elif re.search(r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b', citation_text):
            return "lastname_firstname"
        # F. Lastname format
        elif re.search(r'\b[A-Z]\.\s*[A-Z][a-z]+\b', citation_text):
            return "initial_lastname"
        return None
    
    def _extract_date_format(self, citation_text: str) -> Optional[str]:
        """Extract date formatting pattern."""
        if re.search(r'\(\d{4}\)', citation_text):
            return "parentheses"
        elif re.search(r'\b\d{4}\b', citation_text):
            return "plain"
        return None
    
    def _extract_intext_citations(self, text_content: str, citation_style: str) -> List[str]:
        """Extract in-text citations from text."""
        intext_patterns = {
            "APA": r'\([A-Z][a-z]+(?:\s*&\s*[A-Z][a-z]+)?,\s*\d{4}\)',
            "MLA": r'\([A-Z][a-z]+(?:\s+\d+)?\)',
            "Chicago": r'\([A-Z][a-z]+\s+\d{4}\)',
            "IEEE": r'\[\d+\]'
        }
        
        pattern = intext_patterns.get(citation_style, intext_patterns["APA"])
        return re.findall(pattern, text_content)
    
    def _calculate_relevance_score(self, citations: List[Dict[str, Any]], text_content: str) -> float:
        """Calculate citation relevance score based on keyword overlap."""
        if not citations or not text_content:
            return 0.0
        
        # Extract key terms from main text (simplified)
        text_words = set(re.findall(r'\b[a-z]{4,}\b', text_content.lower()))
        
        relevance_scores = []
        for citation in citations:
            citation_text = citation.get("text", "").lower()
            citation_words = set(re.findall(r'\b[a-z]{4,}\b', citation_text))
            
            if citation_words:
                overlap = len(text_words.intersection(citation_words))
                relevance = overlap / len(citation_words)
                relevance_scores.append(relevance)
        
        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    
    def _analyze_year_distribution(self, years: List[int]) -> Dict[str, int]:
        """Analyze distribution of publication years."""
        if not years:
            return {}
        
        current_year = datetime.now().year
        distribution = {
            "last_5_years": sum(1 for y in years if current_year - y <= 5),
            "6_10_years": sum(1 for y in years if 5 < current_year - y <= 10),
            "older_than_10": sum(1 for y in years if current_year - y > 10)
        }
        
        return distribution
    
    # Recommendation generation methods
    
    def _generate_accuracy_recommendations(self, accuracy_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving citation accuracy."""
        recommendations = []
        
        if accuracy_scores.get("format", 0) < 0.8:
            recommendations.append("Review citation style guide and ensure consistent formatting")
        
        if accuracy_scores.get("completeness", 0) < 0.8:
            recommendations.append("Include all required elements (author, year, title, source)")
        
        if accuracy_scores.get("consistency", 0) < 0.8:
            recommendations.append("Maintain consistent formatting across all citations")
        
        return recommendations
    
    def _generate_formatting_recommendations(
        self, 
        citation_style: str, 
        formatting_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate formatting-specific recommendations."""
        recommendations = []
        
        if formatting_issues:
            recommendations.append(f"Review {citation_style} style guide for proper formatting")
            recommendations.append("Use citation management software for consistent formatting")
        
        if len(formatting_issues) > len(formatting_issues) * 0.5:
            recommendations.append("Consider professional proofreading for citation formatting")
        
        return recommendations
    
    def _generate_completeness_recommendations(
        self, 
        element_counts: Dict[str, int], 
        total_citations: int
    ) -> List[str]:
        """Generate completeness recommendations."""
        recommendations = []
        
        low_presence_elements = [
            element for element, count in element_counts.items()
            if count / total_citations < 0.8 if total_citations > 0
        ]
        
        if "author" in low_presence_elements:
            recommendations.append("Ensure all citations include author information")
        
        if "year" in low_presence_elements:
            recommendations.append("Include publication year for all sources")
        
        if "title" in low_presence_elements:
            recommendations.append("Include full titles for all cited works")
        
        return recommendations
    
    def _generate_consistency_recommendations(self, consistency_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate consistency recommendations."""
        recommendations = []
        
        for issue in consistency_issues:
            if "author" in issue["issue"]:
                recommendations.append("Standardize author name formatting (e.g., 'Smith, J.' or 'Smith, John')")
            elif "date" in issue["issue"]:
                recommendations.append("Use consistent date formatting throughout")
        
        if consistency_issues:
            recommendations.append("Use citation management software to ensure consistency")
        
        return recommendations
    
    def _generate_quality_recommendations(
        self, 
        quality_scores: Dict[str, float], 
        source_types: Dict[str, int]
    ) -> List[str]:
        """Generate quality recommendations."""
        recommendations = []
        
        if quality_scores.get("recency", 0) < 0.6:
            recommendations.append("Include more recent sources (within last 5 years)")
        
        if quality_scores.get("diversity", 0) < 0.5:
            recommendations.append("Diversify source types (journals, books, conferences)")
        
        if source_types.get("journal", 0) < source_types.get("web", 0):
            recommendations.append("Prioritize peer-reviewed journal articles over web sources")
        
        return recommendations
    
    def _generate_intext_recommendations(
        self, 
        match_score: float, 
        unmatched: List[str]
    ) -> List[str]:
        """Generate in-text citation recommendations."""
        recommendations = []
        
        if match_score < 0.9:
            recommendations.append("Ensure all in-text citations have corresponding references")
        
        if unmatched:
            recommendations.append("Review unmatched in-text citations for accuracy")
            recommendations.append("Check for missing references in bibliography")
        
        return recommendations