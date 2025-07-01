"""
Main academic source service that orchestrates multiple APIs and quality scoring
"""
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
import hashlib
import json
from uuid import uuid4

from storm_loop.config import get_config
from storm_loop.models.academic_models import (
    AcademicPaper, SearchQuery, SearchResult, QualityMetrics
)
from storm_loop.services.openalex_client import OpenAlexClient
from storm_loop.services.crossref_client import CrossrefClient
from storm_loop.services.source_quality_scorer import SourceQualityScorer
from storm_loop.services.perplexity_client import PerplexityClient
from storm_loop.utils.cache_decorators import (
    cache_academic_search, cache_paper_details, cache_doi_resolution,
    cache_quality_score, cache_author_search, cache_trending_papers
)
from storm_loop.utils.logging import storm_logger


class AcademicSourceService:
    """
    Unified service for academic source retrieval and quality assessment
    
    Orchestrates multiple academic APIs (OpenAlex, Crossref) with intelligent
    result merging, deduplication, and quality scoring.
    """
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.config = get_config()
        self.session = session
        self._own_session = session is None
        
        # Initialize clients
        self.openalex_client = None
        self.crossref_client = None
        self.perplexity_client = None
        self.quality_scorer = SourceQualityScorer()

        # simple local cache for tests
        self._cache: Dict[str, Any] = {}
        
    
    async def __aenter__(self):
        if self._own_session:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Initialize API clients
        self.openalex_client = OpenAlexClient(session=self.session)
        self.crossref_client = CrossrefClient(session=self.session)
        self.perplexity_client = PerplexityClient(session=self.session)

        await self.openalex_client.__aenter__()
        await self.crossref_client.__aenter__()
        await self.perplexity_client.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.openalex_client:
            await self.openalex_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.crossref_client:
            await self.crossref_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.perplexity_client:
            await self.perplexity_client.__aexit__(exc_type, exc_val, exc_tb)
        if self._own_session and self.session:
            await self.session.close()

    # --- simple cache helpers used in tests ---
    def _get_cache_key(self, prefix: str, **params: Any) -> str:
        params_str = json.dumps(params, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.md5(params_str.encode()).hexdigest()}"

    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def _get_from_cache(self, key: str) -> Any:
        return self._cache.get(key)
    
    
    @cache_academic_search(ttl=3600)
    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        sources: Optional[List[str]] = None,
        quality_threshold: float = 0.0,
        deduplicate: bool = True,
        **search_kwargs
    ) -> SearchResult:
        """
        Search for academic papers across multiple sources with quality scoring
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            sources: List of sources to search ('openalex', 'crossref', 'all')
            quality_threshold: Minimum quality score filter (0.0-1.0)
            deduplicate: Whether to remove duplicate papers
            **search_kwargs: Additional search parameters (filters, sort, etc.)
        
        Returns:
            SearchResult with ranked, quality-scored papers
        """
        
        # Determine which sources to use
        if sources is None:
            sources = ['openalex', 'crossref'] if self.config.enable_openalex and self.config.enable_crossref else ['openalex']
        elif 'all' in sources:
            sources = ['openalex', 'crossref']
        
        storm_logger.info(f"Searching papers: query='{query}', sources={sources}, limit={limit}")
        
        # Execute searches in parallel
        search_tasks = []
        if 'openalex' in sources and self.config.enable_openalex:
            search_tasks.append(self._search_openalex(query, limit, **search_kwargs))
        if 'crossref' in sources and self.config.enable_crossref:
            search_tasks.append(self._search_crossref(query, limit, **search_kwargs))
        
        try:
            start_time = asyncio.get_event_loop().time()
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            end_time = asyncio.get_event_loop().time()
            
            # Combine results
            all_papers = []
            total_count = 0
            
            for result in search_results:
                if isinstance(result, SearchResult):
                    all_papers.extend(result.papers)
                    total_count += result.total_count or 0
                elif isinstance(result, Exception):
                    storm_logger.warning(f"Search task failed: {str(result)}")
            
            # Deduplicate papers
            if deduplicate:
                all_papers = self._deduplicate_papers(all_papers)
            
            # Score papers for quality
            all_papers = await self._score_papers_quality(all_papers)
            
            # Filter by quality threshold
            if quality_threshold > 0.0:
                all_papers = [p for p in all_papers if (p.quality_score or 0.0) >= quality_threshold]
            
            # Sort by combined relevance and quality score
            all_papers = self._rank_papers(all_papers)

            # Use Perplexity fallback if no papers found
            if not all_papers:
                fallback = await self.fallback_search(query, limit=limit)
                all_papers.extend(fallback)

            # Limit results
            all_papers = all_papers[:limit]
            
            # Create final result
            result = SearchResult(
                query=SearchQuery(query=query, limit=limit, **search_kwargs),
                papers=all_papers,
                total_count=len(all_papers),
                search_time_ms=(end_time - start_time) * 1000,
                source="academic_source_service"
            )
            
            
            storm_logger.info(f"Search completed: {len(all_papers)} papers returned")
            return result
            
        except Exception as e:
            storm_logger.error(f"Academic search failed: {str(e)}")
            return SearchResult(
                query=SearchQuery(query=query, limit=limit),
                papers=[],
                total_count=0,
                source="academic_source_service"
            )
    
    async def _search_openalex(self, query: str, limit: int, **kwargs) -> SearchResult:
        """Search OpenAlex with error handling"""
        try:
            return await self.openalex_client.search_papers(query, limit=limit, **kwargs)
        except Exception as e:
            storm_logger.warning(f"OpenAlex search failed: {str(e)}")
            return SearchResult(
                query=SearchQuery(query=query, limit=limit),
                papers=[],
                total_count=0,
                source="openalex"
            )
    
    async def _search_crossref(self, query: str, limit: int, **kwargs) -> SearchResult:
        """Search Crossref with error handling"""
        try:
            return await self.crossref_client.search_papers(query, limit=limit, **kwargs)
        except Exception as e:
            storm_logger.warning(f"Crossref search failed: {str(e)}")
            return SearchResult(
                query=SearchQuery(query=query, limit=limit),
                papers=[],
                total_count=0,
                source="crossref"
            )

    async def fallback_search(self, query: str, limit: int = 5) -> List[AcademicPaper]:
        """Fallback search using Perplexity when academic sources fail."""
        try:
            results = await self.perplexity_client.search(query, limit=limit)
            return self._convert_perplexity_to_papers(results)
        except Exception as e:
            storm_logger.warning(f"Perplexity fallback failed for '{query}': {e}")
            return []

    def _convert_perplexity_to_papers(self, results: List[Dict[str, Any]]) -> List[AcademicPaper]:
        """Convert Perplexity search results into AcademicPaper models."""
        papers: List[AcademicPaper] = []
        for item in results:
            papers.append(
                AcademicPaper(
                    id=f"perplexity:{uuid4().hex}",
                    title=item.get("title", "Unknown"),
                    abstract=item.get("snippet"),
                    landing_page_url=item.get("url"),
                    created_date=datetime.now(),
                    raw_data=item,
                )
            )
        return papers

    
    def _deduplicate_papers(self, papers: List[AcademicPaper]) -> List[AcademicPaper]:
        """
        Remove duplicate papers based on DOI, title similarity, and other factors
        """
        if not papers:
            return papers
        
        unique_papers = []
        seen_dois = set()
        seen_titles = set()
        
        for paper in papers:
            is_duplicate = False
            
            # Check DOI duplicates
            if paper.doi and paper.doi in seen_dois:
                is_duplicate = True
            elif paper.doi:
                seen_dois.add(paper.doi)
            
            # Check title similarity (simple exact match for now)
            if not is_duplicate and paper.title:
                title_normalized = paper.title.lower().strip()
                if title_normalized in seen_titles:
                    is_duplicate = True
                else:
                    seen_titles.add(title_normalized)
            
            if not is_duplicate:
                unique_papers.append(paper)
        
        storm_logger.debug(f"Deduplication: {len(papers)} -> {len(unique_papers)} papers")
        return unique_papers
    
    async def _score_papers_quality(self, papers: List[AcademicPaper]) -> List[AcademicPaper]:
        """Score papers for quality and add quality_score field"""
        if not papers:
            return papers
        
        try:
            # Score papers in batches to avoid blocking
            batch_size = 50
            for i in range(0, len(papers), batch_size):
                batch = papers[i:i + batch_size]
                for paper in batch:
                    metrics = self.quality_scorer.score_paper(paper)
                    paper.quality_score = metrics.overall_score
                
                # Yield control occasionally
                if i % batch_size == 0:
                    await asyncio.sleep(0)  # Allow other tasks to run
            
            storm_logger.debug(f"Quality scoring completed for {len(papers)} papers")
            
        except Exception as e:
            storm_logger.warning(f"Quality scoring failed: {str(e)}")
            # Set default scores on error
            for paper in papers:
                paper.quality_score = 0.5
        
        return papers
    
    def _rank_papers(self, papers: List[AcademicPaper]) -> List[AcademicPaper]:
        """
        Rank papers by combined relevance and quality score
        """
        def paper_score(paper: AcademicPaper) -> float:
            quality = paper.quality_score or 0.5
            
            # Boost recent papers slightly
            recency_boost = 0.0
            if paper.publication_year:
                age = datetime.now().year - paper.publication_year
                if age <= 3:
                    recency_boost = 0.1 * (3 - age) / 3
            
            # Boost papers with citations
            citation_boost = 0.0
            if paper.citation_count and paper.citation_count > 0:
                citation_boost = min(0.2, paper.citation_count / 100)
            
            return quality + recency_boost + citation_boost
        
        papers.sort(key=paper_score, reverse=True)
        return papers
    
    @cache_doi_resolution(ttl=604800)
    async def get_paper_by_doi(self, doi: str) -> Optional[AcademicPaper]:
        """
        Get a paper by DOI, trying multiple sources
        """
        
        storm_logger.debug(f"Looking up paper by DOI: {doi}")
        
        # Try OpenAlex first (usually more complete metadata)
        if self.config.enable_openalex:
            try:
                paper = await self.openalex_client.get_paper_by_doi(doi)
                if paper:
                    metrics = self.quality_scorer.score_paper(paper)
                    paper.quality_score = metrics.overall_score
                    return paper
            except Exception as e:
                storm_logger.warning(f"OpenAlex DOI lookup failed: {str(e)}")
        
        # Fallback to Crossref
        if self.config.enable_crossref:
            try:
                paper = await self.crossref_client.get_paper_by_doi(doi)
                if paper:
                    metrics = self.quality_scorer.score_paper(paper)
                    paper.quality_score = metrics.overall_score
                    return paper
            except Exception as e:
                storm_logger.warning(f"Crossref DOI lookup failed: {str(e)}")
        
        storm_logger.warning(f"Could not find paper with DOI: {doi}")
        return None
    
    async def validate_doi(self, doi: str) -> bool:
        """Validate if a DOI exists"""
        if self.config.enable_crossref:
            return await self.crossref_client.validate_doi(doi)
        elif self.config.enable_openalex:
            paper = await self.openalex_client.get_paper_by_doi(doi)
            return paper is not None
        return False
    
    @cache_author_search(ttl=43200)
    async def search_by_author(self, author_name: str, limit: int = 10) -> SearchResult:
        """Search papers by author across sources"""
        return await self.search_papers(
            query=f'author:"{author_name}"',
            limit=limit,
            sources=['openalex', 'crossref']
        )
    
    @cache_trending_papers(ttl=1800)
    async def get_trending_papers(self, days: int = 7, limit: int = 10) -> SearchResult:
        """Get trending/recent high-quality papers"""
        # Use OpenAlex for trending as it has better recency data
        if self.config.enable_openalex:
            try:
                result = await self.openalex_client.get_trending_papers(days=days, limit=limit)
                result.papers = await self._score_papers_quality(result.papers)
                result.papers = self._rank_papers(result.papers)
                return result
            except Exception as e:
                storm_logger.warning(f"Trending papers search failed: {str(e)}")
        
        # Fallback to regular search with recent filter
        current_year = datetime.now().year
        return await self.search_papers(
            query="",
            limit=limit,
            filters={"publication_year": [current_year - 1, current_year]},
            sources=['openalex']
        )
    
    def get_quality_threshold(self) -> float:
        """Get configured minimum quality threshold"""
        return self.config.min_source_quality_score
    
    async def batch_quality_score(self, papers: List[AcademicPaper]) -> Dict[str, QualityMetrics]:
        """Score multiple papers and return detailed metrics"""
        return self.quality_scorer.score_multiple_papers(papers)