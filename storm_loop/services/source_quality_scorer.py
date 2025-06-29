"""
Source quality scoring system for academic papers
"""
import math
import re
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from storm_loop.models.academic_models import AcademicPaper, QualityMetrics, Journal
from storm_loop.utils.logging import storm_logger


class SourceQualityScorer:
    """
    Comprehensive quality scoring system for academic papers
    
    Evaluates papers based on multiple factors:
    - Citation metrics and impact
    - Venue/journal quality and reputation
    - Recency and relevance
    - Author reputation indicators
    - Content quality signals
    - Open access and accessibility
    """
    
    # Known predatory publishers/journals (simplified list)
    PREDATORY_INDICATORS = {
        "publishers": {
            "hindawi", "mdpi", "frontiers", "scientific research",
            "omics", "waset", "science domain", "longdom"
        },
        "domains": {
            "scirp.org", "omicsonline.org", "waset.org",
            "sciepub.com", "ijser.org"
        },
        "title_patterns": [
            r"international.*journal.*research",
            r"global.*journal.*science",
            r"world.*journal.*research"
        ]
    }
    
    # High-quality venue indicators
    HIGH_QUALITY_VENUES = {
        "nature", "science", "cell", "lancet", "nejm", "plos one",
        "proceedings of the national academy", "ieee", "acm",
        "springer", "elsevier", "oxford", "cambridge"
    }
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def score_paper(self, paper: AcademicPaper) -> QualityMetrics:
        """
        Calculate comprehensive quality score for a paper
        
        Args:
            paper: AcademicPaper to evaluate
        
        Returns:
            QualityMetrics with detailed scoring breakdown
        """
        metrics = QualityMetrics()
        
        try:
            # Calculate individual metric scores
            metrics.citation_score = self._calculate_citation_score(paper)
            metrics.recency_score = self._calculate_recency_score(paper)
            metrics.venue_score = self._calculate_venue_score(paper)
            metrics.author_score = self._calculate_author_score(paper)
            metrics.content_score = self._calculate_content_score(paper)
            
            # Check for quality flags
            metrics.is_predatory = self._is_predatory_publication(paper)
            metrics.is_retracted = self._is_retracted(paper)
            metrics.has_peer_review = self._has_peer_review(paper)
            
            # Calculate open access bonus
            metrics.open_access_bonus = 0.1 if paper.is_open_access else 0.0
            
            # Calculate overall score
            metrics.calculate_overall_score()
            
            storm_logger.debug(f"Quality score calculated for paper {paper.id}: {metrics.overall_score:.3f}")
            
        except Exception as e:
            storm_logger.warning(f"Error calculating quality score for paper {paper.id}: {str(e)}")
            metrics.overall_score = 0.5  # Default neutral score on error
        
        return metrics
    
    def _calculate_citation_score(self, paper: AcademicPaper) -> float:
        """
        Calculate citation-based quality score
        
        Uses log-normalized citation count with age weighting
        """
        if not paper.citation_count or paper.citation_count <= 0:
            return 0.0
        
        # Age adjustment factor
        age_years = max(1, self.current_year - (paper.publication_year or self.current_year))
        age_factor = math.log(age_years + 1) / math.log(10)  # Logarithmic age adjustment
        
        # Normalize citation count per year
        citations_per_year = paper.citation_count / age_years
        
        # Log-normalize to handle wide citation ranges
        # Using log10(x + 1) to handle 0 citations gracefully
        normalized_citations = math.log10(citations_per_year + 1) / math.log10(1000 + 1)  # Max ~1000 cites/year
        
        # Apply age factor (more recent papers get slight boost)
        score = normalized_citations * (1.0 + 0.1 / age_factor)
        
        return min(1.0, max(0.0, score))
    
    def _calculate_recency_score(self, paper: AcademicPaper) -> float:
        """
        Calculate recency score based on publication date
        
        More recent papers get higher scores, with exponential decay
        """
        if not paper.publication_year:
            return 0.5  # Neutral score for unknown date
        
        age_years = self.current_year - paper.publication_year
        
        if age_years < 0:
            return 0.2  # Future dates are suspicious
        
        # Exponential decay with half-life of ~5 years
        decay_factor = math.exp(-age_years * 0.139)  # ln(2)/5 ≈ 0.139
        
        # Boost very recent papers (last 2 years)
        if age_years <= 2:
            decay_factor *= 1.2
        
        return min(1.0, max(0.0, decay_factor))
    
    def _calculate_venue_score(self, paper: AcademicPaper) -> float:
        """
        Calculate venue quality score based on journal reputation
        """
        if not paper.journal:
            return 0.3  # Lower score for unknown venue
        
        journal = paper.journal
        journal_name = journal.name.lower() if journal.name else ""
        publisher = journal.publisher.lower() if journal.publisher else ""
        
        # Check for high-quality venues
        quality_score = 0.5  # Default score
        
        for venue in self.HIGH_QUALITY_VENUES:
            if venue in journal_name or venue in publisher:
                quality_score = 0.8
                break
        
        # Impact factor bonus (if available)
        if journal.impact_factor:
            # Normalize impact factor (typical range 0-10, exceptional up to 50+)
            if_normalized = min(1.0, journal.impact_factor / 10.0)
            quality_score = max(quality_score, 0.5 + 0.4 * if_normalized)
        
        # H-index bonus (if available)
        if journal.h_index:
            # Normalize h-index (typical range 0-200+)
            h_normalized = min(1.0, journal.h_index / 200.0)
            quality_score = max(quality_score, 0.4 + 0.5 * h_normalized)
        
        # Check for predatory indicators
        if self._is_predatory_venue(journal_name, publisher):
            quality_score *= 0.1  # Heavy penalty
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_author_score(self, paper: AcademicPaper) -> float:
        """
        Calculate author reputation score
        
        Based on author count, affiliations, and ORCID presence
        """
        if not paper.authors:
            return 0.2  # Low score for no authors
        
        author_count = len(paper.authors)
        
        # Base score from author count (optimal 3-8 authors)
        if author_count == 1:
            base_score = 0.6  # Single author can be high quality
        elif 2 <= author_count <= 8:
            base_score = 0.7 + 0.1 * min(3, author_count - 2) / 3  # Peak at 3-5 authors
        elif 9 <= author_count <= 15:
            base_score = 0.6  # Many authors, decent
        else:
            base_score = 0.4  # Too many authors might indicate lesser contribution
        
        # ORCID bonus (indicates established researchers)
        orcid_count = sum(1 for author in paper.authors if author.orcid)
        orcid_ratio = orcid_count / author_count if author_count > 0 else 0
        orcid_bonus = orcid_ratio * 0.2
        
        # Affiliation bonus (indicates institutional backing)
        affiliation_count = sum(1 for author in paper.authors if author.affiliation)
        affiliation_ratio = affiliation_count / author_count if author_count > 0 else 0
        affiliation_bonus = affiliation_ratio * 0.1
        
        total_score = base_score + orcid_bonus + affiliation_bonus
        return min(1.0, max(0.0, total_score))
    
    def _calculate_content_score(self, paper: AcademicPaper) -> float:
        """
        Calculate content quality score based on available metadata
        """
        score = 0.5  # Base score
        
        # Title quality indicators
        if paper.title:
            title = paper.title.lower()
            # Longer titles often indicate more specific research
            title_length_score = min(0.1, len(title.split()) / 100)
            score += title_length_score
            
            # Check for question marks (often good research papers)
            if '?' in title:
                score += 0.05
        
        # Abstract quality
        if paper.abstract:
            abstract_length = len(paper.abstract)
            # Good abstracts are typically 150-300 words
            if 500 <= abstract_length <= 2000:  # Character count
                score += 0.15
            elif abstract_length > 100:
                score += 0.1
        
        # Keywords/concepts availability
        if paper.concepts and len(paper.concepts) > 0:
            concept_score = min(0.1, len(paper.concepts) / 10)
            score += concept_score
        
        # Reference count (indicates scholarship)
        if paper.referenced_works_count:
            if 10 <= paper.referenced_works_count <= 100:
                ref_score = min(0.1, paper.referenced_works_count / 100)
                score += ref_score
            elif paper.referenced_works_count > 5:
                score += 0.05
        
        # DOI presence (indicates formal publication)
        if paper.doi:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _is_predatory_publication(self, paper: AcademicPaper) -> bool:
        """Check if paper appears to be from a predatory publisher"""
        if not paper.journal:
            return False
        
        journal_name = paper.journal.name.lower() if paper.journal.name else ""
        publisher = paper.journal.publisher.lower() if paper.journal.publisher else ""
        
        return self._is_predatory_venue(journal_name, publisher)
    
    def _is_predatory_venue(self, journal_name: str, publisher: str) -> bool:
        """Check if venue shows predatory indicators"""
        # Check publisher blacklist
        for pred_pub in self.PREDATORY_INDICATORS["publishers"]:
            if pred_pub in publisher:
                return True
        
        # Check domain patterns in journal name
        for domain in self.PREDATORY_INDICATORS["domains"]:
            if domain in journal_name:
                return True
        
        # Check title patterns
        for pattern in self.PREDATORY_INDICATORS["title_patterns"]:
            if re.search(pattern, journal_name, re.IGNORECASE):
                return True
        
        return False
    
    def _is_retracted(self, paper: AcademicPaper) -> bool:
        """Check if paper has been retracted"""
        if not paper.title:
            return False
        
        retraction_indicators = [
            "retracted", "retraction", "withdrawn", "correction"
        ]
        
        title_lower = paper.title.lower()
        return any(indicator in title_lower for indicator in retraction_indicators)
    
    def _has_peer_review(self, paper: AcademicPaper) -> Optional[bool]:
        """Determine if paper underwent peer review"""
        if not paper.journal or not paper.journal.name:
            return None
        
        # Preprints typically don't have peer review
        if paper.source_type and "preprint" in str(paper.source_type).lower():
            return False
        
        # Journal articles typically have peer review
        if paper.source_type and "journal" in str(paper.source_type).lower():
            return True
        
        # Check venue name for indicators
        journal_name = paper.journal.name.lower()
        
        # Preprint servers
        preprint_servers = ["arxiv", "biorxiv", "medrxiv", "preprints.org"]
        if any(server in journal_name for server in preprint_servers):
            return False
        
        # Peer-reviewed venues
        peer_reviewed_indicators = ["journal", "proceedings", "conference"]
        if any(indicator in journal_name for indicator in peer_reviewed_indicators):
            return True
        
        return None  # Unknown
    
    def score_multiple_papers(self, papers: List[AcademicPaper]) -> Dict[str, QualityMetrics]:
        """
        Score multiple papers and return results dictionary
        
        Args:
            papers: List of AcademicPaper objects to score
        
        Returns:
            Dictionary mapping paper IDs to QualityMetrics
        """
        results = {}
        
        for paper in papers:
            try:
                metrics = self.score_paper(paper)
                results[paper.id] = metrics
            except Exception as e:
                storm_logger.error(f"Failed to score paper {paper.id}: {str(e)}")
                # Add default metrics on error
                results[paper.id] = QualityMetrics(overall_score=0.5)
        
        return results
    
    def rank_papers_by_quality(self, papers: List[AcademicPaper]) -> List[tuple[AcademicPaper, QualityMetrics]]:
        """
        Rank papers by quality score in descending order
        
        Args:
            papers: List of papers to rank
        
        Returns:
            List of (paper, metrics) tuples sorted by quality score
        """
        paper_scores = []
        
        for paper in papers:
            metrics = self.score_paper(paper)
            paper_scores.append((paper, metrics))
        
        # Sort by overall score (descending)
        paper_scores.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return paper_scores
    
    def filter_by_quality_threshold(
        self, 
        papers: List[AcademicPaper], 
        threshold: float = 0.7
    ) -> List[AcademicPaper]:
        """
        Filter papers by minimum quality threshold
        
        Args:
            papers: Papers to filter
            threshold: Minimum quality score (0.0-1.0)
        
        Returns:
            List of papers meeting quality threshold
        """
        filtered_papers = []
        
        for paper in papers:
            metrics = self.score_paper(paper)
            if metrics.overall_score >= threshold and not metrics.is_predatory:
                paper.quality_score = metrics.overall_score
                filtered_papers.append(paper)
        
        return filtered_papers