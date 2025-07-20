"""
Validation Strategy

Core verification logic extracted for single responsibility.
Handles external API interactions and error management.
"""

import asyncio
from typing import Dict, Any
from .models import Citation, VerificationResult


class ValidationStrategy:
    """
    Handles core verification logic against external APIs.
    
    Single responsibility: API verification coordination.
    Keeps CitationValidator under 100 lines per Sandi Metz rules.
    """
    
    def __init__(self, openalex_client, crossref_client):
        """Initialize with database clients."""
        self._openalex = openalex_client
        self._crossref = crossref_client
    
    async def verify_with_openalex(self, citation: Citation) -> VerificationResult:
        """Verify citation against OpenAlex database."""
        try:
            result = await self._openalex.verify_paper({
                'title': citation.title,
                'authors': citation.authors,
                'journal': citation.journal,
                'year': citation.year
            })
            
            return self._process_openalex_result(result, citation)
            
        except asyncio.TimeoutError:
            return VerificationResult(
                is_verified=False,
                confidence_score=0.0,
                verification_source='error',
                issues=['api_timeout'],
                error_type='timeout'
            )
        except ConnectionError:
            return VerificationResult(
                is_verified=False,
                confidence_score=0.0,
                verification_source='error',
                issues=['connection_failed'],
                error_type='network_error'
            )
        except Exception as e:
            return VerificationResult(
                is_verified=False,
                confidence_score=0.0,
                verification_source='error',
                issues=[str(e)],
                error_type='unknown_error'
            )
    
    def _process_openalex_result(self, result: Dict[str, Any], citation: Citation) -> VerificationResult:
        """Process OpenAlex API response into verification result."""
        if not result.get('exists', False):
            return VerificationResult(
                is_verified=False,
                confidence_score=0.0,
                verification_source='openalex',
                issues=['fabricated']
            )
        
        confidence = self._calculate_confidence(result)
        issues = self._extract_issues(result)
        
        return VerificationResult(
            is_verified=confidence >= 0.7,
            confidence_score=confidence,
            verification_source='openalex',
            issues=issues
        )
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score from API result."""
        score = 0.0
        
        if result.get('exists', False):
            score += 0.4
        
        if result.get('metadata_matches', False):
            score += 0.4
        else:
            # Partial credit for similarity
            similarity = result.get('title_similarity', 0.0)
            score += similarity * 0.3
        
        if result.get('authors_match', False):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_issues(self, result: Dict[str, Any]) -> list:
        """Extract issues from API result."""
        issues = []
        
        if not result.get('metadata_matches', True):
            if result.get('title_similarity', 1.0) < 1.0:
                issues.append('partial_match')
        
        return issues