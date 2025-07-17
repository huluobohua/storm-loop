from typing import Union, Optional, Tuple, List
import re
import dspy

from .callback import BaseCallbackHandler
from .storm_dataclass import StormInformationTable, StormArticle
from ...interface import OutlineGenerationModule
from ...utils import ArticleTextProcessing


class EnhancedWritePageOutline(dspy.Signature):
    """Write a comprehensive, well-structured outline for a Wikipedia-style article.
    
    CRITICAL REQUIREMENTS:
    1. Create a detailed, hierarchical outline with multiple levels of depth
    2. Each main section should have 2-4 relevant subsections
    3. Include specific, informative section titles (avoid generic terms)
    4. Ensure logical flow and comprehensive coverage of the topic
    5. Balance breadth and depth - cover all major aspects while diving deep into important areas
    
    FORMAT:
    - Use "#" for main sections, "##" for subsections, "###" for sub-subsections
    - Section titles should be descriptive and specific
    - Do not include the topic name as a section
    - Aim for 6-10 main sections with appropriate subsections
    """
    
    topic = dspy.InputField(prefix="Topic for the article: ", format=str)
    outline = dspy.OutputField(
        prefix="Generate a comprehensive, well-structured outline:\n", 
        format=str
    )


class EnhancedWritePageOutlineFromConv(dspy.Signature):
    """Enhance and expand an outline based on multi-perspective research conversations.
    
    CRITICAL REQUIREMENTS:
    1. Carefully analyze the conversation to identify key themes, perspectives, and insights
    2. Significantly expand the draft outline with new sections based on discovered information
    3. Reorganize sections for better logical flow and coherence
    4. Add specific subsections that reflect unique insights from the conversations
    5. Ensure the outline captures diverse perspectives and nuanced understanding
    6. Create a structure that tells a compelling, comprehensive story about the topic
    
    ENHANCEMENT GUIDELINES:
    - Identify gaps in the draft outline that conversations have revealed
    - Add new main sections for important aspects discovered in research
    - Break down broad sections into specific, detailed subsections
    - Ensure each perspective from conversations is represented in the structure
    - Prioritize sections based on the depth and quality of available information
    
    FORMAT:
    - Use "#" for main sections, "##" for subsections, "###" for sub-subsections
    - Section titles should be specific and informative
    - Aim for significant expansion (at least 50% more content than draft)
    """
    
    topic = dspy.InputField(prefix="Topic of the article: ", format=str)
    conv = dspy.InputField(prefix="Multi-perspective research conversations:\n", format=str)
    old_outline = dspy.InputField(prefix="Draft outline to enhance:\n", format=str)
    outline = dspy.OutputField(
        prefix="Generate an enhanced, comprehensive outline based on research insights:\n",
        format=str
    )


class OutlineValidator(dspy.Module):
    """Validates and scores outline quality."""
    
    def __init__(self, min_sections=6, min_depth=2):
        super().__init__()
        self.min_sections = min_sections
        self.min_depth = min_depth
        
    def validate_outline(self, outline: str) -> Tuple[bool, List[str], float]:
        """
        Validate outline structure and quality.
        Returns: (is_valid, issues, quality_score)
        """
        issues = []
        lines = [line.strip() for line in outline.split('\n') if line.strip()]
        
        # Check minimum sections
        main_sections = [line for line in lines if line.startswith('# ')]
        if len(main_sections) < self.min_sections:
            issues.append(f"Only {len(main_sections)} main sections (minimum: {self.min_sections})")
            
        # Check depth
        has_subsections = any(line.startswith('## ') for line in lines)
        has_subsubsections = any(line.startswith('### ') for line in lines)
        
        if not has_subsections:
            issues.append("No subsections found - outline lacks depth")
        
        # Check for generic section names
        generic_terms = ['introduction', 'overview', 'conclusion', 'summary', 'background']
        generic_sections = []
        for section in main_sections:
            section_name = section.replace('#', '').strip().lower()
            if any(term in section_name for term in generic_terms):
                generic_sections.append(section_name)
        
        if len(generic_sections) > 2:
            issues.append(f"Too many generic sections: {', '.join(generic_sections)}")
            
        # Check section balance
        section_sizes = []
        current_size = 0
        for line in lines:
            if line.startswith('# '):
                if current_size > 0:
                    section_sizes.append(current_size)
                current_size = 1
            elif line.startswith('##'):
                current_size += 1
        if current_size > 0:
            section_sizes.append(current_size)
            
        if section_sizes:
            avg_size = sum(section_sizes) / len(section_sizes)
            unbalanced = [size for size in section_sizes if size < avg_size * 0.5 or size > avg_size * 2]
            if len(unbalanced) > len(section_sizes) * 0.3:
                issues.append("Sections are unbalanced in size")
                
        # Calculate quality score
        quality_score = 1.0
        quality_score -= 0.1 * len(issues)
        quality_score += 0.1 if has_subsubsections else 0
        quality_score += 0.05 * min(len(main_sections) - self.min_sections, 4)
        quality_score = max(0, min(1, quality_score))
        
        is_valid = len(issues) == 0
        return is_valid, issues, quality_score


class EnhancedOutlineRefinement(dspy.Signature):
    """Refine an outline to address specific quality issues.
    
    Your task is to improve the outline by:
    1. Addressing each of the identified issues
    2. Maintaining all valuable content while improving structure
    3. Ensuring logical flow and comprehensive coverage
    4. Adding depth where needed without being redundant
    
    IMPORTANT: Output ONLY the refined outline with proper # formatting. Do not include the issues or any other text.
    """
    
    topic = dspy.InputField(prefix="Topic: ", format=str)
    outline = dspy.InputField(prefix="Current outline:\n", format=str)
    issues = dspy.InputField(prefix="Issues to address:\n", format=str)
    refined_outline = dspy.OutputField(
        prefix="Generate refined outline addressing all issues (output ONLY the outline):\n",
        format=str
    )


class EnhancedWriteOutline(dspy.Module):
    """Enhanced outline generation with validation and iterative refinement."""
    
    def __init__(self, engine: Union[dspy.LM, dspy.HFModel], max_refinements: int = 2):
        super().__init__()
        self.draft_page_outline = dspy.Predict(EnhancedWritePageOutline)
        self.write_page_outline = dspy.Predict(EnhancedWritePageOutlineFromConv)
        self.refine_outline = dspy.Predict(EnhancedOutlineRefinement)
        self.validator = OutlineValidator()
        self.engine = engine
        self.max_refinements = max_refinements
        
    def forward(
        self,
        topic: str,
        dlg_history,
        old_outline: Optional[str] = None,
        callback_handler: BaseCallbackHandler = None,
    ):
        # Process dialogue history
        trimmed_dlg_history = []
        for turn in dlg_history:
            if (
                "topic you" in turn.agent_utterance.lower()
                or "topic you" in turn.user_utterance.lower()
            ):
                continue
            trimmed_dlg_history.append(turn)
            
        conv = "\n".join(
            [
                f"Wikipedia Writer: {turn.user_utterance}\nExpert: {turn.agent_utterance}"
                for turn in trimmed_dlg_history
            ]
        )
        conv = ArticleTextProcessing.remove_citations(conv)
        conv = ArticleTextProcessing.limit_word_count_preserve_newline(conv, 5000)
        
        with dspy.settings.context(lm=self.engine):
            # Generate initial draft if needed
            if old_outline is None:
                old_outline = ArticleTextProcessing.clean_up_outline(
                    self.draft_page_outline(topic=topic).outline
                )
                if callback_handler:
                    callback_handler.on_direct_outline_generation_end(
                        outline=old_outline
                    )
                    
            # Generate enhanced outline from conversations
            outline = ArticleTextProcessing.clean_up_outline(
                self.write_page_outline(
                    topic=topic, old_outline=old_outline, conv=conv
                ).outline
            )
            
            # Validate and refine iteratively
            for i in range(self.max_refinements):
                is_valid, issues, quality_score = self.validator.validate_outline(outline)
                
                if is_valid or quality_score > 0.8:
                    break
                    
                # Refine outline to address issues
                issues_text = "\n".join(f"- {issue}" for issue in issues)
                refined_result = self.refine_outline(
                    topic=topic,
                    outline=outline,
                    issues=issues_text
                ).refined_outline
                
                # Clean up the refined outline to ensure it only contains outline content
                refined_lines = []
                for line in refined_result.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('#') or (refined_lines and not line.startswith('#'))):
                        # Keep lines that start with # or are continuation of previous content
                        # But skip lines that look like issue descriptions
                        if not any(keyword in line.lower() for keyword in ['minimum:', 'lacks depth', 'only', 'issues']):
                            refined_lines.append(line)
                
                outline = '\n'.join(refined_lines)
                outline = ArticleTextProcessing.clean_up_outline(outline)
                
            if callback_handler:
                callback_handler.on_outline_refinement_end(outline=outline)
                
        return dspy.Prediction(outline=outline, old_outline=old_outline)


class EnhancedStormOutlineGenerationModule(OutlineGenerationModule):
    """
    Enhanced outline generation module with better prompting, validation, and refinement.
    """
    
    def __init__(self, outline_gen_lm: Union[dspy.LM, dspy.HFModel]):
        super().__init__()
        self.outline_gen_lm = outline_gen_lm
        self.write_outline = EnhancedWriteOutline(engine=self.outline_gen_lm)
        
    def generate_outline(
        self,
        topic: str,
        information_table: StormInformationTable,
        old_outline: Optional[StormArticle] = None,
        callback_handler: BaseCallbackHandler = None,
        return_draft_outline=False,
    ) -> Union[StormArticle, Tuple[StormArticle, StormArticle]]:
        """
        Generates an enhanced outline with validation and refinement.
        """
        if callback_handler is not None:
            callback_handler.on_information_organization_start()
            
        concatenated_dialogue_turns = sum(
            [conv for (_, conv) in information_table.conversations], []
        )
        result = self.write_outline(
            topic=topic,
            dlg_history=concatenated_dialogue_turns,
            callback_handler=callback_handler,
        )
        article_with_outline_only = StormArticle.from_outline_str(
            topic=topic, outline_str=result.outline
        )
        article_with_draft_outline_only = StormArticle.from_outline_str(
            topic=topic, outline_str=result.old_outline
        )
        if not return_draft_outline:
            return article_with_outline_only
        return article_with_outline_only, article_with_draft_outline_only