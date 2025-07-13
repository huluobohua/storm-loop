"""
Fact verification module for the VERIFY system.

Verifies claims against actual sources instead of checking formatting.
This is what actually matters for research quality.
"""

import re
import hashlib
from typing import Dict, List, Optional
from .models import Claim, VerificationResult


class FactChecker:
    """
    Verify claims against actual sources instead of checking formatting.
    This is what actually matters for research quality.
    """
    
    def __init__(self, retrieval_module=None):
        self.retrieval_module = retrieval_module
        self.verified_claims_cache = {}
        self._cache = {}  # For backwards compatibility with tests
        
    async def verify_research(self, research_text: str, sources: List[Dict]) -> List[VerificationResult]:
        """Verify all claims in research text against provided sources."""
        # Extract claims
        claims = self._extract_claims(research_text)
        
        # Verify each claim
        results = []
        for claim in claims:
            # Check cache first
            claim_hash = self._hash_claim(claim)
            if claim_hash in self.verified_claims_cache:
                results.append(self.verified_claims_cache[claim_hash])
                continue
                
            # Verify against sources
            result = await self._verify_single_claim(claim, sources)
            
            # Cache result
            self.verified_claims_cache[claim_hash] = result
            results.append(result)
            
        return results
    
    def extract_claims(self, text: str) -> List[Claim]:
        """Extract factual claims from research text. Public interface."""
        return self._extract_claims(text)
    
    def _extract_claims(self, text: str) -> List[Claim]:
        """Extract factual claims from research text."""
        claims = []
        
        # Split into paragraphs and sentences
        paragraphs = text.split('\n\n')
        
        for p_idx, paragraph in enumerate(paragraphs):
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            
            for s_idx, sentence in enumerate(sentences):
                # Look for factual claim patterns
                if self._is_factual_claim(sentence):
                    # Extract any cited source
                    source_match = re.search(r'\[([^\]]+)\]|\(([^)]+)\)', sentence)
                    source_cited = source_match.group(1) if source_match else None
                    
                    claims.append(Claim(
                        text=sentence,
                        context=paragraph,
                        source_cited=source_cited,
                        location=(p_idx, s_idx)
                    ))
        
        return claims
    
    def _is_factual_claim(self, sentence: str) -> bool:
        """Determine if a sentence contains a factual claim."""
        # Indicators of factual claims
        factual_patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+',  # Dollar amounts
            r'\b\d{4}\b',  # Years
            r'\b(study|research|report|survey|analysis)\b',
            r'\b(found|showed|revealed|demonstrated|indicated)\b',
            r'\b(increased|decreased|reduced|improved)\b',
            r'\b(according to|based on|as reported)\b',
        ]
        
        # Check if sentence contains factual indicators
        for pattern in factual_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                return True
                
        return False
    
    async def _verify_single_claim(self, claim: Claim, sources: List[Dict]) -> VerificationResult:
        """Verify a single claim against sources."""
        supporting_sources = []
        
        # Check against provided sources
        for source in sources:
            if self._claim_supported_by_source(claim, source):
                supporting_sources.append(source.get('url', source.get('title', 'Unknown source')))
        
        # If no supporting sources found and we have retrieval capability
        if not supporting_sources and self.retrieval_module:
            # Try to find supporting evidence
            search_results = await self._search_for_evidence(claim)
            supporting_sources.extend(search_results)
        
        # Determine verification status
        is_supported = len(supporting_sources) > 0
        confidence = min(1.0, len(supporting_sources) * 0.3)  # More sources = higher confidence
        
        # Generate fix if needed
        suggested_fix = None
        severity = "info"
        
        if not is_supported:
            severity = "error"
            if claim.source_cited:
                suggested_fix = f"Claim cites '{claim.source_cited}' but cannot be verified. Please check source or revise claim."
            else:
                suggested_fix = f"Add citation for claim: '{claim.text[:50]}...'"
        elif confidence < 0.5:
            severity = "warning"
            suggested_fix = f"Consider adding more sources to support: '{claim.text[:50]}...'"
        
        return VerificationResult(
            claim=claim,
            is_supported=is_supported,
            confidence=confidence,
            supporting_sources=supporting_sources,
            suggested_fix=suggested_fix,
            severity=severity
        )
    
    def _claim_supported_by_source(self, claim: Claim, source: Dict) -> bool:
        """Check if a claim is supported by a specific source."""
        source_text = source.get('content', '') + source.get('snippet', '')
        
        # Simple keyword matching - in production, use semantic similarity
        claim_keywords = set(word.lower() for word in claim.text.split() 
                           if len(word) > 3 and word.isalnum())
        source_keywords = set(word.lower() for word in source_text.split() 
                            if len(word) > 3 and word.isalnum())
        
        # Check overlap
        overlap = len(claim_keywords & source_keywords)
        overlap_ratio = overlap / len(claim_keywords) if claim_keywords else 0
        
        return overlap_ratio > 0.3  # 30% keyword overlap threshold
    
    async def _search_for_evidence(self, claim: Claim) -> List[str]:
        """Search for evidence to support a claim."""
        # This would use the retrieval module to search for supporting evidence
        # For now, return empty list
        return []
    
    def _hash_claim(self, claim: Claim) -> str:
        """Generate hash for claim caching."""
        return hashlib.md5(claim.text.encode()).hexdigest()

    async def verify_claim(self, claim: Claim) -> VerificationResult:
        """Verify a single claim. Public interface for tests."""
        return await self._verify_single_claim(claim, [])

    def _get_cache_key(self, claim: Claim) -> str:
        """Get cache key for a claim."""
        return self._hash_claim(claim)

    def _get_cached_result(self, claim: Claim) -> Optional[VerificationResult]:
        """Get cached verification result for a claim."""
        cache_key = self._get_cache_key(claim)
        return self._cache.get(cache_key)

    async def _verify_against_sources(self, claim: Claim) -> VerificationResult:
        """Verify claim against sources. For test mocking."""
        return await self._verify_single_claim(claim, [])