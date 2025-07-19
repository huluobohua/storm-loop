"""
Pattern Detection Components

Specialized pattern detectors for fabrication indicators.
Each detector focuses on one type of suspicious pattern.
"""

import re
from typing import List, Set
from .models import Citation


class TitlePatternDetector:
    """Detects suspicious patterns in citation titles."""
    
    def __init__(self):
        """Initialize suspicious title patterns."""
        self._patterns = [
            r'fake|fabricated|imaginary|fictional',
            r'made.*up|invented|created',
            r'test.*paper|sample.*article',
            r'placeholder|dummy|mock'
        ]
    
    def detect(self, title: str) -> List[str]:
        """Check title for suspicious patterns."""
        issues = []
        title_lower = title.lower()
        
        for pattern in self._patterns:
            if re.search(pattern, title_lower):
                issues.append(f'suspicious_title_pattern: {pattern}')
        
        return issues


class AuthorPatternDetector:
    """Detects suspicious patterns in author names."""
    
    def detect(self, authors: List[str]) -> List[str]:
        """Check authors for fabrication indicators."""
        issues = []
        
        for author in authors:
            author_lower = author.lower()
            
            # Check for obviously fake author names
            if any(fake in author_lower for fake in ['fake', 'fictional', 'made', 'test']):
                issues.append(f'suspicious_author: {author}')
            
            # Check for placeholder patterns
            if re.search(r'author.*\d+|name.*\d+', author_lower):
                issues.append(f'placeholder_author: {author}')
        
        return issues


class JournalPatternDetector:
    """Detects suspicious journal names and known fake publications."""
    
    def __init__(self):
        """Initialize known fake journal names."""
        self._fake_journals = {
            'journal of imaginary science',
            'fake research quarterly',
            'fictional studies review',
            'made up journal',
            'test publication'
        }
    
    def detect(self, journal: str) -> List[str]:
        """Check journal for known fake publications."""
        issues = []
        journal_lower = journal.lower()
        
        if journal_lower in self._fake_journals:
            issues.append(f'known_fake_journal: {journal}')
        
        # Check for suspicious journal patterns
        if any(pattern in journal_lower for pattern in ['fake', 'imaginary', 'test']):
            issues.append(f'suspicious_journal_name: {journal}')
        
        return issues


class DOIPatternDetector:
    """Detects suspicious DOI patterns and format violations."""
    
    def detect(self, doi: str) -> List[str]:
        """Check DOI for fabrication indicators."""
        if not doi:
            return []
        
        issues = []
        doi_lower = doi.lower()
        
        # Check for obviously fake DOI patterns
        if any(fake in doi_lower for fake in ['fake', 'test', 'dummy']):
            issues.append(f'suspicious_doi: {doi}')
        
        # Check for invalid DOI format
        if not re.match(r'10\.\d{4,}/.*', doi):
            issues.append(f'invalid_doi_format: {doi}')
        
        return issues