"""
Integrity Checker

Orchestrates fabrication detection using specialized pattern detectors.
Coordinates multiple detection strategies for comprehensive analysis.
"""

from typing import List, Dict
from .models import Citation
from .pattern_detectors import (
    TitlePatternDetector, AuthorPatternDetector, 
    JournalPatternDetector, DOIPatternDetector
)


class IntegrityChecker:
    """
    Orchestrates fabrication detection using pattern analysis.
    
    Coordinates specialized pattern detectors.
    Single responsibility: fabrication detection coordination.
    """
    
    def __init__(self):
        """Initialize pattern detection components."""
        self._title_detector = TitlePatternDetector()
        self._author_detector = AuthorPatternDetector()
        self._journal_detector = JournalPatternDetector()
        self._doi_detector = DOIPatternDetector()
    
    def check_citation(self, citation: Citation) -> List[str]:
        """Check single citation for fabrication indicators."""
        issues = []
        
        issues.extend(self._title_detector.detect(citation.title))
        issues.extend(self._author_detector.detect(citation.authors))
        issues.extend(self._journal_detector.detect(citation.journal))
        if citation.doi:
            issues.extend(self._doi_detector.detect(citation.doi))
        
        return issues
    
    def check_bibliography(self, citations: List[Citation]) -> Dict:
        """Check entire bibliography for fabrication patterns."""
        total_issues = 0
        citation_issues = {}
        issue_types = {}
        
        for citation in citations:
            issues = self.check_citation(citation)
            if issues:
                citation_issues[citation] = issues
                total_issues += len(issues)
                
                # Count issue types
                for issue in issues:
                    issue_type = issue.split(':')[0]
                    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        return {
            'total_citations': len(citations),
            'citations_with_issues': len(citation_issues),
            'total_issues': total_issues,
            'issue_breakdown': issue_types,
            'citation_issues': citation_issues,
            'fabrication_risk': self._assess_risk(citations, citation_issues)
        }
    
    def _assess_risk(self, citations: List[Citation], issues: Dict) -> str:
        """Assess overall fabrication risk level."""
        if not citations:
            return 'unknown'
        
        issue_rate = len(issues) / len(citations)
        
        if issue_rate >= 0.5:
            return 'critical'
        elif issue_rate >= 0.2:
            return 'high'
        elif issue_rate >= 0.1:
            return 'medium'
        else:
            return 'low'