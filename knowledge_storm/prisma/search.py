"""
Search strategy builder for PRISMA systematic reviews.

Handles building comprehensive search strategies across multiple databases
using PICO methodology and domain-specific optimization.
"""

import re
from typing import Dict, List, Tuple
from .models import SearchStrategy


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
        """Extract PICO elements from research question."""
        # Simplified extraction - in production, use NLP
        pico = {
            'population': [],
            'intervention': [],
            'comparison': [],
            'outcome': []
        }
        
        # Look for key patterns
        if 'patients with' in question.lower():
            population_match = re.search(r'patients with ([^,\.]+)', question, re.I)
            if population_match:
                pico['population'].append(population_match.group(1))
        
        # Extract intervention (AI, ML, etc.)
        ai_terms = ['AI', 'artificial intelligence', 'machine learning', 'deep learning', 
                    'neural network', 'algorithm', 'automated', 'computer-aided']
        for term in ai_terms:
            if term.lower() in question.lower():
                pico['intervention'].append(term)
        
        # Extract outcomes
        outcome_terms = ['diagnosis', 'detection', 'screening', 'prediction', 'prognosis',
                        'treatment', 'outcomes', 'accuracy', 'performance']
        for term in outcome_terms:
            if term.lower() in question.lower():
                pico['outcome'].append(term)
        
        return pico
    
    def _generate_criteria(self, pico: Dict[str, List[str]], 
                          domain: str) -> Tuple[List[str], List[str]]:
        """Generate inclusion and exclusion criteria."""
        inclusion = []
        exclusion = []
        
        # Standard inclusion criteria
        inclusion.append("Peer-reviewed studies")
        inclusion.append("Published in English")
        inclusion.append("Published between 2019-2024")
        
        if pico['population']:
            inclusion.append(f"Studies involving {', '.join(pico['population'])}")
        if pico['intervention']:
            inclusion.append(f"Studies using {', '.join(pico['intervention'])}")
        if pico['outcome']:
            inclusion.append(f"Studies reporting {', '.join(pico['outcome'])}")
        
        # Standard exclusion criteria
        exclusion.append("Conference abstracts without full text")
        exclusion.append("Editorials, opinions, and letters")
        exclusion.append("Studies without primary data")
        exclusion.append("Duplicate publications")
        
        # Domain-specific criteria
        if domain == "medical":
            exclusion.append("Animal studies without human validation")
            exclusion.append("Case reports with n<10")
        elif domain == "cs":
            exclusion.append("Papers without implementation details")
            exclusion.append("Position papers without evaluation")
        
        return inclusion, exclusion
    
    def _build_query(self, pico: Dict[str, List[str]], syntax: Dict[str, str]) -> str:
        """Build database-specific search query."""
        query_parts = []
        
        # Population terms
        if pico['population']:
            pop_terms = [f'"{term}"' for term in pico['population']]
            query_parts.append(f"({syntax['OR'].join(pop_terms)})")
        
        # Intervention terms with synonyms
        if pico['intervention']:
            intervention_groups = []
            for term in pico['intervention']:
                # Add synonyms
                synonyms = self._get_synonyms(term)
                group = syntax['OR'].join([f'"{s}"' for s in synonyms])
                intervention_groups.append(f"({group})")
            query_parts.append(f"({syntax['OR'].join(intervention_groups)})")
        
        # Outcome terms
        if pico['outcome']:
            outcome_terms = [f'"{term}"' for term in pico['outcome']]
            query_parts.append(f"({syntax['OR'].join(outcome_terms)})")
        
        # Combine with AND
        full_query = syntax['AND'].join(query_parts)
        
        # Add filters
        full_query += f"{syntax['AND']}(\"2019\"[Date]:\"2024\"[Date])"
        
        return full_query
    
    def _get_synonyms(self, term: str) -> List[str]:
        """Get synonyms for search terms."""
        synonym_map = {
            'AI': ['AI', 'artificial intelligence'],
            'artificial intelligence': ['AI', 'artificial intelligence'],
            'machine learning': ['machine learning', 'ML', 'deep learning', 'DL'],
            'diagnosis': ['diagnosis', 'diagnostic', 'detection', 'identification'],
            'treatment': ['treatment', 'therapy', 'intervention', 'management']
        }
        
        return synonym_map.get(term.lower(), [term])
    
    def _is_relevant_database(self, db_name: str, domain: str) -> bool:
        """Check if database is relevant for domain."""
        domain_databases = {
            'medical': ['pubmed', 'scopus', 'cochrane', 'embase'],
            'cs': ['ieee', 'acm', 'scopus', 'web_of_science'],
            'general': ['scopus', 'web_of_science']
        }
        
        return db_name in domain_databases.get(domain, domain_databases['general'])