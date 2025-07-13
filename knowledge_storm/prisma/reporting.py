"""
Zero draft generator for PRISMA systematic reviews.

Generates structured drafts to overcome blank page syndrome with clear
disclaimers about requiring human expert review.
"""

from datetime import datetime
from typing import Dict, List
from .models import SearchStrategy, Paper, ExtractionTemplate


class ZeroDraftGenerator:
    """
    Generates a 'zero draft' to overcome blank page syndrome.
    Clearly marked as draft requiring human expertise.
    """
    
    def __init__(self, lm_model=None):
        self.lm_model = lm_model
    
    async def generate_zero_draft(self,
                                search_strategy: SearchStrategy,
                                screening_results: Dict[str, List[Paper]],
                                extraction_template: ExtractionTemplate,
                                include_draft: bool = True) -> str:
        """Generate a zero draft with clear disclaimers."""
        
        if not include_draft:
            return self._generate_outline_only(search_strategy, screening_results)
        
        draft = f"""# ZERO DRAFT - SYSTEMATIC REVIEW
## ⚠️ IMPORTANT: This is an AI-generated draft to overcome blank page syndrome
## All claims, numbers, and conclusions MUST be verified by human experts

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status**: DRAFT - NOT FOR SUBMISSION

---

# {search_strategy.research_question}

## Abstract

[DRAFT PLACEHOLDER - TO BE WRITTEN AFTER ANALYSIS]

## 1. Introduction

### 1.1 Background
{self._generate_background(search_strategy)}

### 1.2 Rationale
The need for this systematic review arises from [VERIFY AND EXPAND]:
- Gap in current literature regarding...
- Conflicting evidence about...
- Rapid developments in...

### 1.3 Objectives
This systematic review aims to [REFINE BASED ON FINAL PROTOCOL]:
{self._format_objectives(search_strategy)}

## 2. Methods

### 2.1 Protocol and Registration
[ADD: PROSPERO registration number if applicable]
This review was conducted according to PRISMA guidelines.

### 2.2 Eligibility Criteria
{self._format_criteria(search_strategy)}

### 2.3 Information Sources
Databases searched:
{self._format_databases(search_strategy)}

### 2.4 Search Strategy
Example search (PubMed):
```
{search_strategy.search_queries.get('pubmed', 'SEARCH QUERY TO BE INSERTED')}
```

### 2.5 Study Selection
- {len(screening_results.get('definitely_include', []))} studies identified for inclusion
- {len(screening_results.get('needs_human_review', []))} require human review
- {len(screening_results.get('definitely_exclude', []))} excluded

[INSERT: PRISMA flow diagram]

### 2.6 Data Extraction
Data extraction template includes:
{self._format_extraction_fields(extraction_template)}

### 2.7 Risk of Bias Assessment
[TO BE COMPLETED: Specify tool - Cochrane RoB 2, QUADAS-2, etc.]

### 2.8 Data Synthesis
[TO BE COMPLETED: Specify meta-analysis methods or narrative synthesis approach]

## 3. Results

### 3.1 Study Selection
[TO BE COMPLETED WITH ACTUAL NUMBERS]
- Records identified: [N]
- Duplicates removed: [N]
- Records screened: {len(screening_results.get('definitely_include', [])) + 
                     len(screening_results.get('needs_human_review', [])) + 
                     len(screening_results.get('definitely_exclude', []))}
- Full-text articles assessed: [N]
- Studies included: [N]

### 3.2 Study Characteristics
[INSERT: Summary table of included studies]

### 3.3 Risk of Bias
[INSERT: Risk of bias summary]

### 3.4 Results of Individual Studies
[TO BE COMPLETED: Key findings from each study]

### 3.5 Synthesis of Results
[TO BE COMPLETED: Meta-analysis or narrative synthesis]

## 4. Discussion

### 4.1 Summary of Evidence
[TO BE WRITTEN: Main findings]

### 4.2 Limitations
Study limitations may include:
- [ASSESS: Publication bias]
- [ASSESS: Heterogeneity]
- [ASSESS: Quality of included studies]

### 4.3 Implications
[TO BE WRITTEN: Clinical/research implications]

## 5. Conclusion
[TO BE WRITTEN: Clear conclusions based on evidence]

## References
[TO BE FORMATTED: Include all screened papers]

---

## 📝 HUMAN TASKS CHECKLIST:
- [ ] Verify all numbers and statistics
- [ ] Complete risk of bias assessment
- [ ] Perform data extraction on included studies
- [ ] Conduct meta-analysis if appropriate
- [ ] Write abstract based on final results
- [ ] Review and revise all sections
- [ ] Format references properly
- [ ] Create PRISMA flow diagram
- [ ] Register protocol if not done
- [ ] Check journal requirements

## ⚠️ REMEMBER: This is a starting point only. All content requires expert review.
"""
        
        return draft
    
    def _generate_outline_only(self, search_strategy: SearchStrategy, 
                             screening_results: Dict[str, List[Paper]]) -> str:
        """Generate outline without draft content."""
        return f"""# SYSTEMATIC REVIEW OUTLINE

## Research Question
{search_strategy.research_question}

## Progress Summary
- ✅ Search strategy developed
- ✅ Initial screening complete ({len(screening_results.get('definitely_exclude', []))} excluded)
- ⏳ {len(screening_results.get('needs_human_review', []))} papers need human review
- ⏳ Data extraction pending
- ⏳ Risk of bias assessment pending
- ⏳ Synthesis pending

## Suggested Structure

1. **Introduction** (1-2 pages)
   - Background and rationale
   - Objectives
   
2. **Methods** (3-4 pages)
   - Protocol and registration
   - Eligibility criteria
   - Information sources
   - Search strategy
   - Study selection
   - Data extraction
   - Risk of bias assessment
   - Data synthesis plan
   
3. **Results** (5-8 pages)
   - Study selection (PRISMA diagram)
   - Study characteristics
   - Risk of bias
   - Results of individual studies
   - Synthesis of results
   
4. **Discussion** (3-4 pages)
   - Summary of evidence
   - Limitations
   - Implications for practice
   - Implications for research
   
5. **Conclusion** (1 paragraph)

## Next Steps
1. Complete screening of {len(screening_results.get('needs_human_review', []))} papers
2. Extract data using provided template
3. Assess risk of bias
4. Synthesize findings
5. Write first draft
"""
    
    def _generate_background(self, strategy: SearchStrategy) -> str:
        """Generate background section draft."""
        pico = strategy.pico_elements
        
        background = "[DRAFT - VERIFY ALL CLAIMS]\n\n"
        
        if pico.get('population'):
            background += f"The population of interest includes {', '.join(pico['population'])}. "
        
        if pico.get('intervention'):
            background += f"Recent advances in {', '.join(pico['intervention'])} have shown promise. "
        
        if pico.get('outcome'):
            background += f"Key outcomes of interest include {', '.join(pico['outcome'])}."
        
        return background
    
    def _format_objectives(self, strategy: SearchStrategy) -> str:
        """Format objectives based on PICO."""
        objectives = []
        
        objectives.append(f"Primary: To synthesize evidence on {strategy.research_question}")
        objectives.append("Secondary: To assess the quality of available evidence")
        objectives.append("Secondary: To identify gaps in current research")
        
        return '\n'.join(f"- {obj}" for obj in objectives)
    
    def _format_criteria(self, strategy: SearchStrategy) -> str:
        """Format inclusion/exclusion criteria."""
        criteria = "**Inclusion Criteria:**\n"
        for inc in strategy.inclusion_criteria:
            criteria += f"- {inc}\n"
        
        criteria += "\n**Exclusion Criteria:**\n"
        for exc in strategy.exclusion_criteria:
            criteria += f"- {exc}\n"
        
        return criteria
    
    def _format_databases(self, strategy: SearchStrategy) -> str:
        """Format database list."""
        return '\n'.join(f"- {db.upper()}" for db in strategy.search_queries.keys())
    
    def _format_extraction_fields(self, template: ExtractionTemplate) -> str:
        """Format extraction fields."""
        categories = [
            "**Study Characteristics:**",
            '\n'.join(f"- {char}" for char in template.study_characteristics),
            "\n**Outcome Measures:**",
            '\n'.join(f"- {outcome}" for outcome in template.outcome_measures),
            "\n**Quality Indicators:**",
            '\n'.join(f"- {qual}" for qual in template.quality_indicators)
        ]
        
        return '\n'.join(categories)