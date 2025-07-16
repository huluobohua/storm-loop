"""
PRISMA Search Strategy Builder.

Focused module for building comprehensive search strategies across databases
for systematic reviews.
"""

import re
from typing import Dict, List, Tuple

from .core import SearchStrategy


class SearchStrategyBuilder:
    """Builds comprehensive search strategies from research questions."""
    
    def __init__(self):
        # Common medical/scientific database syntaxes
        self.database_syntaxes = {
            'pubmed': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'scopus': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' AND NOT ', 'wildcard': '*'},
            'web_of_science': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'cochrane': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'embase': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'ieee': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'},
            'acm': {'AND': ' AND ', 'OR': ' OR ', 'NOT': ' NOT ', 'wildcard': '*'}
        }
        
    def build_search_strategy(self, research_question: str, 
                            domain: str = "medical") -> SearchStrategy:
        """Build comprehensive search strategy from research question."""
        
        # Extract PICO elements (Population, Intervention, Comparison, Outcome)
        pico = self._extract_pico(research_question)
        
        # Generate inclusion/exclusion criteria
        inclusion, exclusion = self._generate_criteria(pico, domain)
        
        # Build database-specific queries
        queries = {}
        for db_name, syntax in self.database_syntaxes.items():
            if self._is_relevant_database(db_name, domain):
                queries[db_name] = self._build_query(pico, syntax)
        
        return SearchStrategy(
            research_question=research_question,
            pico_elements=pico,
            search_queries=queries,
            inclusion_criteria=inclusion,
            exclusion_criteria=exclusion,
            date_range=(2019, 2024)  # Last 5 years by default
        )
    
    def _extract_pico(self, question: str) -> Dict[str, List[str]]:
        """Extract PICO elements from research question using NLP patterns."""
        pico = {'population': [], 'intervention': [], 'comparison': [], 'outcome': []}
        
        # Simple pattern-based extraction (would use NLP in production)
        # Population patterns
        pop_patterns = [
            r'\b(patients?|participants?|subjects?|adults?|children?|elderly)\b',
            r'\b(men|women|males?|females?)\b',
            r'\b(\w+\s+disease|\w+\s+disorder|\w+\s+condition)\b'
        ]
        
        for pattern in pop_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            pico['population'].extend([m.lower() for m in matches if m])
        
        # Intervention patterns
        intervention_patterns = [
            r'\b(treatment|therapy|intervention|medication|drug)\b',
            r'\b(\w+\s+treatment|\w+\s+therapy)\b',
            r'\b(surgery|operation|procedure)\b'
        ]
        
        for pattern in intervention_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            pico['intervention'].extend([m.lower() for m in matches if m])
        
        # Outcome patterns
        outcome_patterns = [
            r'\b(mortality|survival|death|recovery)\b',
            r'\b(improvement|reduction|decrease|increase)\b',
            r'\b(efficacy|effectiveness|safety|adverse effects)\b'
        ]
        
        for pattern in outcome_patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            pico['outcome'].extend([m.lower() for m in matches if m])
        
        # Remove duplicates
        for key in pico:
            pico[key] = list(set(pico[key]))
        
        return pico
    
    def _generate_criteria(self, pico: Dict[str, List[str]], 
                          domain: str) -> Tuple[List[str], List[str]]:
        """Generate inclusion and exclusion criteria from PICO."""
        inclusion = [
            "Published in peer-reviewed journals",
            "Human studies only",
            "English language publications",
            "Original research articles"
        ]
        
        exclusion = [
            "Animal studies",
            "Case reports with <10 patients",
            "Non-English publications",
            "Conference abstracts only",
            "Letters, editorials, commentaries",
            "Duplicate publications"
        ]
        
        # Add domain-specific criteria
        if domain == "medical":
            inclusion.extend([
                "Clinical trials, cohort studies, case-control studies",
                "Studies with clear methodology description"
            ])
            exclusion.extend([
                "In vitro studies only",
                "Studies without human participants"
            ])
        
        return inclusion, exclusion
    
    def _is_relevant_database(self, db_name: str, domain: str) -> bool:
        """Check if database is relevant for the domain."""
        medical_dbs = {'pubmed', 'embase', 'cochrane'}
        tech_dbs = {'ieee', 'acm', 'scopus'}
        general_dbs = {'web_of_science', 'scopus'}
        
        if domain == "medical":
            return db_name in medical_dbs or db_name in general_dbs
        elif domain == "technology":
            return db_name in tech_dbs or db_name in general_dbs
        else:
            return db_name in general_dbs
    
    def _build_query(self, pico: Dict[str, List[str]], 
                    syntax: Dict[str, str]) -> str:
        """Build database-specific query from PICO elements."""
        query_parts = []
        
        # Combine population terms
        if pico['population']:
            pop_query = syntax['OR'].join(f'"{term}"' for term in pico['population'])
            query_parts.append(f"({pop_query})")
        
        # Combine intervention terms
        if pico['intervention']:
            int_query = syntax['OR'].join(f'"{term}"' for term in pico['intervention'])
            query_parts.append(f"({int_query})")
        
        # Combine outcome terms
        if pico['outcome']:
            out_query = syntax['OR'].join(f'"{term}"' for term in pico['outcome'])
            query_parts.append(f"({out_query})")
        
        # Join all parts with AND
        if query_parts:
            return syntax['AND'].join(query_parts)
        else:
            return "systematic review OR meta-analysis"  # Fallback query


# Export classes
__all__ = ['SearchStrategyBuilder']