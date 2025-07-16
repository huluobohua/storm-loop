"""
Research memory module for the VERIFY system.

Learns from past research to improve future generation.
This is more valuable than blind iteration.
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from .models import ResearchPattern, VerificationResult

logger = logging.getLogger(__name__)


class ResearchMemory:
    """
    Learn from past research to improve future generation.
    This is more valuable than blind iteration.
    """
    
    def __init__(self, storage_path="research_memory"):
        if isinstance(storage_path, str):
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.patterns: Dict[str, List[ResearchPattern]] = {}
        self.domain_knowledge: Dict[str, Dict] = {}
        self.successful_structures: List[Dict] = []
        
        self._load_memory()

    def store_pattern(self, pattern: ResearchPattern):
        """Store a research pattern. Public interface for tests."""
        domain = pattern.domain
        if domain not in self.patterns:
            self.patterns[domain] = []
        self.patterns[domain].append(pattern)
        self._save_memory()

    def get_patterns(self, domain: str) -> List[ResearchPattern]:
        """Get patterns for a specific domain. Public interface for tests."""
        return self.patterns.get(domain, [])
    
    def get_relevant_context(self, topic: str, domain: str = "general") -> Dict[str, Any]:
        """Get relevant patterns and knowledge for a new research topic."""
        context = {
            "domain_patterns": self.patterns.get(domain, []),
            "successful_structures": self._get_similar_structures(topic),
            "domain_knowledge": self.domain_knowledge.get(domain, {}),
            "common_pitfalls": self._get_common_pitfalls(domain)
        }
        
        # Sort patterns by success metric and recency
        context["domain_patterns"].sort(
            key=lambda p: (p.success_metric, p.usage_count), 
            reverse=True
        )
        
        return context
    
    def learn_from_research(self, 
                          research_text: str, 
                          verification_results: List[VerificationResult],
                          domain: str = "general",
                          user_rating: Optional[float] = None):
        """Learn patterns from completed research."""
        
        # Calculate success metrics
        total_claims = len(verification_results)
        verified_claims = sum(1 for r in verification_results if r.is_supported)
        verification_rate = verified_claims / total_claims if total_claims > 0 else 0
        
        # Extract structural patterns
        structure_pattern = self._extract_structure_pattern(research_text)
        
        # Extract source quality patterns
        source_pattern = self._extract_source_pattern(verification_results)
        
        # Store patterns
        patterns = [
            ResearchPattern(
                pattern_type="structure",
                domain=domain,
                success_metric=user_rating or verification_rate,
                pattern_data=structure_pattern,
                last_used=datetime.now()
            ),
            ResearchPattern(
                pattern_type="source_quality",
                domain=domain,
                success_metric=verification_rate,
                pattern_data=source_pattern,
                last_used=datetime.now()
            )
        ]
        
        # Add to memory
        if domain not in self.patterns:
            self.patterns[domain] = []
        self.patterns[domain].extend(patterns)
        
        # Update domain knowledge
        self._update_domain_knowledge(domain, research_text, verification_results)
        
        # Save to disk
        self._save_memory()
    
    def _extract_structure_pattern(self, research_text: str) -> Dict:
        """Extract structural patterns from successful research."""
        sections = research_text.split('\n\n')
        
        return {
            "section_count": len(sections),
            "avg_section_length": sum(len(s.split()) for s in sections) / len(sections),
            "has_introduction": any("introduction" in s.lower() for s in sections[:3]),
            "has_conclusion": any("conclusion" in s.lower() for s in sections[-3:]),
            "citation_density": len(re.findall(r'\[[^\]]+\]|\([^)]+\)', research_text)) / len(sections)
        }
    
    def _extract_source_pattern(self, verification_results: List[VerificationResult]) -> Dict:
        """Extract patterns about source usage."""
        source_types = {}
        for result in verification_results:
            for source in result.supporting_sources:
                source_type = self._classify_source(source)
                source_types[source_type] = source_types.get(source_type, 0) + 1
        
        return {
            "source_diversity": len(source_types),
            "primary_source_type": max(source_types.items(), key=lambda x: x[1])[0] if source_types else "none",
            "avg_sources_per_claim": sum(len(r.supporting_sources) for r in verification_results) / len(verification_results) if verification_results else 0
        }
    
    def _classify_source(self, source: str) -> str:
        """Classify source type."""
        if "arxiv" in source.lower():
            return "preprint"
        elif "doi.org" in source.lower():
            return "academic"
        elif any(domain in source.lower() for domain in [".edu", "scholar", "pubmed"]):
            return "academic"
        elif any(domain in source.lower() for domain in [".gov", ".org"]):
            return "institutional"
        else:
            return "general"
    
    def _get_similar_structures(self, topic: str) -> List[Dict]:
        """Find similar successful research structures."""
        # In production, use semantic similarity
        # For now, return recent successful structures
        return self.successful_structures[-5:]  # Last 5 successful structures
    
    def _get_common_pitfalls(self, domain: str) -> List[str]:
        """Get common pitfalls for a domain."""
        # Analyze failed patterns
        if domain not in self.patterns:
            return []
            
        failed_patterns = [p for p in self.patterns[domain] if p.success_metric < 0.5]
        
        pitfalls = []
        for pattern in failed_patterns:
            if pattern.pattern_type == "structure" and pattern.pattern_data.get("citation_density", 1) < 0.5:
                pitfalls.append("Low citation density - aim for at least one citation per major claim")
            if pattern.pattern_type == "source_quality" and pattern.pattern_data.get("source_diversity", 1) < 2:
                pitfalls.append("Limited source diversity - include multiple source types")
                
        return pitfalls
    
    def _update_domain_knowledge(self, domain: str, research_text: str, verification_results: List[VerificationResult]):
        """Update domain-specific knowledge."""
        if domain not in self.domain_knowledge:
            self.domain_knowledge[domain] = {
                "common_sources": {},
                "terminology": set(),
                "fact_patterns": []
            }
        
        # Track successful sources
        for result in verification_results:
            if result.is_supported:
                for source in result.supporting_sources:
                    self.domain_knowledge[domain]["common_sources"][source] = \
                        self.domain_knowledge[domain]["common_sources"].get(source, 0) + 1
        
        # Extract domain terminology
        # In production, use NLP for better extraction
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', research_text)
        self.domain_knowledge[domain]["terminology"].update(words)
    
    def _save_memory(self):
        """Save memory to disk."""
        # Ensure directory exists
        if self.storage_path.suffix:  # If it's a file path
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            memory_file = self.storage_path
        else:  # If it's a directory path
            self.storage_path.mkdir(parents=True, exist_ok=True)
            memory_file = self.storage_path / "memory.json"
        
        memory_data = {
            "patterns": {
                domain: [
                    {
                        "pattern_type": p.pattern_type,
                        "success_metric": p.success_metric,
                        "pattern_data": p.pattern_data,
                        "usage_count": p.usage_count,
                        "last_used": p.last_used.isoformat() if p.last_used else None
                    }
                    for p in patterns
                ]
                for domain, patterns in self.patterns.items()
            },
            "domain_knowledge": {
                domain: {
                    **knowledge,
                    "terminology": list(knowledge.get("terminology", set()))
                }
                for domain, knowledge in self.domain_knowledge.items()
            },
            "successful_structures": self.successful_structures
        }
        
        with open(memory_file, "w") as f:
            json.dump(memory_data, f, indent=2)
    
    def _load_memory(self):
        """Load memory from disk."""
        if self.storage_path.suffix:  # If it's a file path
            memory_file = self.storage_path
        else:  # If it's a directory path
            memory_file = self.storage_path / "memory.json"
            
        if not memory_file.exists():
            return
            
        try:
            with open(memory_file, "r") as f:
                memory_data = json.load(f)
                
            # Reconstruct patterns
            for domain, patterns in memory_data.get("patterns", {}).items():
                self.patterns[domain] = [
                    ResearchPattern(
                        pattern_type=p["pattern_type"],
                        domain=domain,
                        success_metric=p["success_metric"],
                        pattern_data=p["pattern_data"],
                        usage_count=p.get("usage_count", 0),
                        last_used=datetime.fromisoformat(p["last_used"]) if p.get("last_used") else None
                    )
                    for p in patterns
                ]
            
            # Load domain knowledge
            self.domain_knowledge = {
                domain: {
                    **knowledge,
                    "terminology": set(knowledge.get("terminology", []))
                }
                for domain, knowledge in memory_data.get("domain_knowledge", {}).items()
            }
            
            self.successful_structures = memory_data.get("successful_structures", [])
            
        except Exception as e:
            logger.error(f"Error loading memory: {e}")