"""
Targeted fixer module for the VERIFY system.

Fix only what's broken instead of regenerating everything.
This is more efficient and preserves good content.
"""

import re
from typing import List
from .models import VerificationResult


class TargetedFixer:
    """
    Fix only what's broken instead of regenerating everything.
    This is more efficient and preserves good content.
    """
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model

    async def apply_fix(self, original_text: str, verification_result: VerificationResult) -> str:
        """Apply a fix based on verification result. Public interface for tests."""
        if verification_result.suggested_fix:
            # Simple replacement logic for tests
            claim_text = verification_result.claim.text
            suggested_fix = verification_result.suggested_fix
            
            # Try to find and replace the claim with the fix
            if claim_text in original_text:
                return original_text.replace(claim_text, suggested_fix)
            else:
                # If exact match not found, append the fix
                return f"{original_text} {suggested_fix}"
        return original_text
    
    async def fix_issues(self, 
                        research_text: str, 
                        verification_results: List[VerificationResult]) -> str:
        """Fix only the specific issues identified by verification."""
        
        # Group issues by severity
        issues_by_severity = {
            "error": [],
            "warning": [],
            "info": []
        }
        
        for result in verification_results:
            if not result.is_supported:
                issues_by_severity[result.severity].append(result)
        
        # Fix errors first (must fix)
        if issues_by_severity["error"]:
            research_text = await self._fix_errors(research_text, issues_by_severity["error"])
        
        # Fix warnings if they're significant
        if len(issues_by_severity["warning"]) > 3:  # Threshold for fixing warnings
            research_text = await self._fix_warnings(research_text, issues_by_severity["warning"])
        
        # Info items are optional - only fix if requested
        
        return research_text
    
    async def _fix_errors(self, text: str, errors: List[VerificationResult]) -> str:
        """Fix critical errors in the text."""
        # Sort by location to fix in order
        errors.sort(key=lambda e: e.claim.location or (0, 0))
        
        # Split text for targeted fixes
        paragraphs = text.split('\n\n')
        
        for error in errors:
            if error.claim.location:
                p_idx, s_idx = error.claim.location
                
                if p_idx < len(paragraphs):
                    # Fix specific sentence
                    sentences = re.split(r'(?<=[.!?])\s+', paragraphs[p_idx])
                    
                    if s_idx < len(sentences):
                        # Apply targeted fix
                        if error.suggested_fix:
                            if "Add citation" in error.suggested_fix:
                                # Add [citation needed] marker
                                sentences[s_idx] = sentences[s_idx].rstrip('.') + " [citation needed]."
                            elif "cannot be verified" in error.suggested_fix:
                                # Mark as disputed
                                sentences[s_idx] = f"[UNVERIFIED: {sentences[s_idx]}]"
                        
                        # Reconstruct paragraph
                        paragraphs[p_idx] = ' '.join(sentences)
        
        return '\n\n'.join(paragraphs)
    
    async def _fix_warnings(self, text: str, warnings: List[VerificationResult]) -> str:
        """Fix warning-level issues."""
        # For warnings, we might add clarifying language or additional sources
        # This is a simplified implementation
        
        for warning in warnings:
            if "more sources" in warning.suggested_fix:
                # Add a note about limited sourcing
                text = text.replace(
                    warning.claim.text,
                    f"{warning.claim.text} (Note: Limited sources available for this claim)"
                )
        
        return text