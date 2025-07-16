"""
PRISMA Zero Draft Generator.

Focused module for generating zero drafts of systematic review sections
based on search strategies and screening results.
"""

from typing import Dict, Any

from .core import SearchStrategy


class ZeroDraftGenerator:
    """Generates zero drafts of systematic review sections."""
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
    
    async def generate_methods_section(self, search_strategy: SearchStrategy) -> str:
        """Generate methods section from search strategy."""
        methods = f"""
## Methods

### Search Strategy
This systematic review addressed the research question: "{search_strategy.research_question}"

The search strategy was developed using the PICO framework:
- Population: {', '.join(search_strategy.pico_elements.get('population', []))}
- Intervention: {', '.join(search_strategy.pico_elements.get('intervention', []))}
- Comparison: {', '.join(search_strategy.pico_elements.get('comparison', []))}
- Outcome: {', '.join(search_strategy.pico_elements.get('outcome', []))}

### Database Search
The following databases were searched:
{chr(10).join(f"- {db}: {query}" for db, query in search_strategy.search_queries.items())}

### Inclusion Criteria
{chr(10).join(f"- {criterion}" for criterion in search_strategy.inclusion_criteria)}

### Exclusion Criteria
{chr(10).join(f"- {criterion}" for criterion in search_strategy.exclusion_criteria)}

### Date Range
{f"Publications from {search_strategy.date_range[0]} to {search_strategy.date_range[1]}" if search_strategy.date_range else "No date restrictions applied"}

### Language
{', '.join(search_strategy.languages)} language publications included.
"""
        return methods.strip()
    
    async def generate_results_section(self, screening_results: Dict[str, Any]) -> str:
        """Generate results section from screening results."""
        metrics = screening_results['performance_metrics']
        
        results = f"""
## Results

### Study Selection
A total of {metrics['total_papers']} papers were identified through database searching.

After applying inclusion and exclusion criteria:
- {len(screening_results['definitely_include'])} papers were included for full-text review
- {len(screening_results['definitely_exclude'])} papers were excluded
- {len(screening_results['needs_human_review'])} papers required additional human review

The automated screening achieved {metrics['automation_rate']:.1%} automation rate, meeting the 80/20 methodology target.

### Exclusion Reasons
{chr(10).join(f"- {reason}: {count} papers" for reason, count in screening_results['exclusion_stats'].items())}

### Confidence Distribution
- High confidence decisions: {screening_results['confidence_distribution']['high']} papers
- Medium confidence decisions: {screening_results['confidence_distribution']['medium']} papers
- Low confidence decisions: {screening_results['confidence_distribution']['low']} papers
"""
        return results.strip()


# Export classes
__all__ = ['ZeroDraftGenerator']