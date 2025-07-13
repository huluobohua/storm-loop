"""
Main PRISMA Assistant orchestrator.

Coordinates all components to provide comprehensive systematic review assistance
while being honest about limitations and focusing on useful automation.
"""

import logging
from typing import Dict, List, Optional, Any
from .models import Paper, SearchStrategy, ExtractionTemplate
from .search import SearchStrategyBuilder
from .screening import ScreeningAssistant
from .extraction import DataExtractionHelper
from .reporting import ZeroDraftGenerator

logger = logging.getLogger(__name__)


class PRISMAAssistant:
    """
    The complete PRISMA assistant that handles the grunt work of systematic reviews.
    Honest about limitations, focused on actually useful automation.
    """
    
    def __init__(self, lm_model=None, retrieval_module=None):
        self.lm_model = lm_model
        self.retrieval_module = retrieval_module
        
        # Initialize components
        self.search_builder = SearchStrategyBuilder()
        self.screening_assistant = ScreeningAssistant()
        self.extraction_helper = DataExtractionHelper()
        self.draft_generator = ZeroDraftGenerator(lm_model)
        
        # Track metrics
        self.time_saved = 0
        self.papers_processed = 0
    
    async def assist_systematic_review(self, 
                                     research_question: str,
                                     papers: Optional[List[Paper]] = None,
                                     generate_draft: bool = False) -> Dict[str, Any]:
        """
        Main entry point for systematic review assistance.
        
        Args:
            research_question: The research question in natural language
            papers: Optional list of papers if already retrieved
            generate_draft: Whether to generate zero draft (default: False)
            
        Returns:
            Dictionary with all assistance outputs and time saved
        """
        logger.info(f"Starting PRISMA assistance for: {research_question}")
        
        # 1. Develop comprehensive search strategy
        logger.info("Building search strategy...")
        search_strategy = self.search_builder.build_search_strategy(research_question)
        self.time_saved += 5  # Hours saved on search development
        
        # 2. Retrieve papers if not provided
        if papers is None and self.retrieval_module:
            logger.info("Retrieving papers...")
            papers = await self._retrieve_papers(search_strategy)
        elif papers is None:
            papers = []  # Empty list for demo
        
        # 3. Screen papers
        logger.info(f"Screening {len(papers)} papers...")
        screening_results = await self.screening_assistant.screen_papers(papers, search_strategy)
        self.papers_processed = len(papers)
        self.time_saved += len(papers) * 0.05  # ~3 minutes per paper for screening
        
        # 4. Create extraction template
        logger.info("Creating extraction template...")
        included_papers = screening_results['definitely_include'] + screening_results['needs_human_review']
        extraction_template = self.extraction_helper.create_extraction_template(
            included_papers, research_question
        )
        self.time_saved += 3  # Hours saved on template creation
        
        # 5. Generate reporting templates
        logger.info("Generating PRISMA reporting templates...")
        prisma_templates = self._generate_prisma_templates(screening_results)
        self.time_saved += 2  # Hours saved on PRISMA setup
        
        # 6. Optionally generate zero draft
        zero_draft = None
        if generate_draft:
            logger.info("Generating zero draft...")
            zero_draft = await self.draft_generator.generate_zero_draft(
                search_strategy, screening_results, extraction_template
            )
            self.time_saved += 5  # Hours saved on initial draft
        
        # Compile results
        results = {
            'search_strategy': search_strategy,
            'screening_results': {
                'definitely_exclude': len(screening_results['definitely_exclude']),
                'definitely_include': len(screening_results['definitely_include']),
                'needs_human_review': len(screening_results['needs_human_review']),
                'exclusion_stats': dict(screening_results['exclusion_stats'])
            },
            'performance_metrics': screening_results.get('performance_metrics', {}),
            'extraction_template': extraction_template,
            'prisma_templates': prisma_templates,
            'zero_draft': zero_draft,
            'metrics': {
                'papers_processed': self.papers_processed,
                'time_saved_hours': self.time_saved,
                'cost_estimate': f"${self.papers_processed * 0.001:.2f}",  # Rough estimate
                'human_tasks': [
                    f"Review {len(screening_results['needs_human_review'])} uncertain papers (<80% confidence)",
                    "Validate auto-screening decisions (spot check)",
                    "Extract data from included studies", 
                    "Assess risk of bias",
                    "Synthesize findings",
                    "Write/revise manuscript"
                ],
                'auto_decision_rate': screening_results.get('performance_metrics', {}).get('auto_decision_rate', 0),
                'confidence_threshold': 0.8
            }
        }
        
        logger.info(f"PRISMA assistance complete. Estimated time saved: {self.time_saved:.1f} hours")
        
        return results
    
    async def _retrieve_papers(self, search_strategy: SearchStrategy) -> List[Paper]:
        """Retrieve papers from databases."""
        # This would interface with actual database APIs
        # For now, return mock data
        return []
    
    def _generate_prisma_templates(self, screening_results: Dict) -> Dict[str, str]:
        """Generate PRISMA checklist and flow diagram templates."""
        
        # PRISMA flow diagram data
        flow_diagram = {
            'identification': {
                'database_records': 'n = [TO BE FILLED]',
                'other_sources': 'n = [TO BE FILLED]'
            },
            'screening': {
                'after_duplicates': f"n = {sum(len(v) for k, v in screening_results.items() if k != 'exclusion_stats')}",
                'excluded': f"n = {len(screening_results['definitely_exclude'])}",
                'reasons': screening_results['exclusion_stats']
            },
            'eligibility': {
                'full_text_assessed': f"n = {len(screening_results['definitely_include']) + len(screening_results['needs_human_review'])}",
                'full_text_excluded': 'n = [TO BE FILLED]',
                'reasons': '[TO BE FILLED]'
            },
            'included': {
                'qualitative_synthesis': 'n = [TO BE FILLED]',
                'quantitative_synthesis': 'n = [TO BE FILLED]'
            }
        }
        
        # PRISMA checklist (partial)
        checklist = """# PRISMA 2020 Checklist

## Title
- [ ] Identify as systematic review ± meta-analysis

## Abstract
- [ ] Structured summary including objectives, methods, results, conclusions

## Introduction
- [x] Rationale (draft provided)
- [x] Objectives with PICO (draft provided)

## Methods
- [x] Protocol and registration info template
- [x] Eligibility criteria specified
- [x] Information sources listed
- [x] Search strategy documented
- [ ] Study selection process (partially automated)
- [x] Data extraction template created
- [ ] Risk of bias method specified
- [ ] Summary measures planned
- [ ] Synthesis methods planned

## Results
- [ ] Study selection with flow diagram
- [ ] Study characteristics table
- [ ] Risk of bias results
- [ ] Individual study results
- [ ] Synthesis results
- [ ] Additional analyses

## Discussion
- [ ] Summary of evidence
- [ ] Limitations discussed
- [ ] Conclusions stated

## Funding
- [ ] Funding sources declared
"""
        
        return {
            'flow_diagram_data': flow_diagram,
            'checklist': checklist
        }