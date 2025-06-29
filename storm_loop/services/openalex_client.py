"""
OpenAlex API client for academic paper retrieval
"""
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlencode, quote
import logging
from datetime import datetime

from storm_loop.config import get_config
from storm_loop.models.academic_models import (
    AcademicPaper, Author, Journal, Concept, SearchQuery, 
    SearchResult, SourceType, QualityMetrics
)
from storm_loop.utils.logging import storm_logger


class OpenAlexClient:
    """
    Async client for OpenAlex API
    
    OpenAlex is a fully open catalog of scholarly papers, authors, 
    institutions, and more. API docs: https://docs.openalex.org/
    """
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self, email: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self.config = get_config()
        self.email = email or self.config.openalex_email
        self.session = session
        self._own_session = session is None
        
        # Rate limiting
        self._request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests for politeness
        
    async def __aenter__(self):
        if self._own_session:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with user agent and email if available"""
        headers = {
            "User-Agent": "STORM-Loop/0.1.0 (https://github.com/huluobohua/storm-loop)"
        }
        if self.email:
            headers["User-Agent"] += f" mailto:{self.email}"
        return headers
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited request to OpenAlex API"""
        async with self._request_semaphore:
            # Rate limiting
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - time_since_last)
            
            url = f"{self.BASE_URL}/{endpoint}"
            headers = self._get_headers()
            
            # Clean up None values from params
            clean_params = {k: v for k, v in params.items() if v is not None}
            
            storm_logger.debug(f"OpenAlex request: {url} with params: {clean_params}")
            
            try:
                async with self.session.get(url, headers=headers, params=clean_params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    if response.status == 200:
                        data = await response.json()
                        storm_logger.debug(f"OpenAlex response successful: {len(str(data))} bytes")
                        return data
                    else:
                        error_text = await response.text()
                        storm_logger.error(f"OpenAlex API error {response.status}: {error_text}")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
            except asyncio.TimeoutError:
                storm_logger.error(f"OpenAlex request timeout for {url}")
                raise
            except Exception as e:
                storm_logger.error(f"OpenAlex request failed: {str(e)}")
                raise
    
    def _parse_author(self, author_data: Dict[str, Any]) -> Author:
        """Parse OpenAlex author data into Author model"""
        return Author(
            display_name=author_data.get("display_name", "Unknown"),
            given_name=author_data.get("given_name"),
            family_name=author_data.get("family_name"),
            orcid=author_data.get("orcid"),
            affiliation=author_data.get("affiliation", {}).get("display_name") if author_data.get("affiliation") else None,
            author_position=author_data.get("author_position")
        )
    
    def _parse_journal(self, venue_data: Dict[str, Any]) -> Optional[Journal]:
        """Parse OpenAlex venue data into Journal model"""
        if not venue_data:
            return None
        
        return Journal(
            name=venue_data.get("display_name", "Unknown"),
            issn=venue_data.get("issn_l"),
            publisher=venue_data.get("publisher"),
            impact_factor=venue_data.get("impact_factor"),
            h_index=venue_data.get("h_index")
        )
    
    def _parse_concept(self, concept_data: Dict[str, Any]) -> Concept:
        """Parse OpenAlex concept data into Concept model"""
        return Concept(
            id=concept_data.get("id", ""),
            display_name=concept_data.get("display_name", "Unknown"),
            score=concept_data.get("score"),
            level=concept_data.get("level")
        )
    
    def _determine_source_type(self, work_data: Dict[str, Any]) -> SourceType:
        """Determine source type from OpenAlex work data"""
        type_mapping = {
            "journal-article": SourceType.JOURNAL_ARTICLE,
            "book-chapter": SourceType.BOOK_CHAPTER,
            "book": SourceType.BOOK,
            "proceedings-article": SourceType.CONFERENCE_PAPER,
            "preprint": SourceType.PREPRINT,
            "dissertation": SourceType.THESIS,
            "report": SourceType.REPORT
        }
        
        openalex_type = work_data.get("type", "").lower()
        return type_mapping.get(openalex_type, SourceType.OTHER)
    
    def _parse_work(self, work_data: Dict[str, Any]) -> AcademicPaper:
        """Parse OpenAlex work data into AcademicPaper model"""
        # Parse authors
        authors = []
        for author_data in work_data.get("authorships", []):
            if author_data.get("author"):
                authors.append(self._parse_author(author_data["author"]))
        
        # Parse venue/journal
        journal = self._parse_journal(work_data.get("host_venue"))
        
        # Parse concepts
        concepts = []
        for concept_data in work_data.get("concepts", []):
            concepts.append(self._parse_concept(concept_data))
        
        # Extract URLs
        pdf_url = None
        landing_page_url = None
        external_urls = []
        
        for location in work_data.get("open_access", {}).get("oa_locations", []):
            if location.get("host_type") == "repository" and location.get("url"):
                if location.get("url").endswith(".pdf"):
                    pdf_url = location["url"]
                else:
                    external_urls.append(location["url"])
        
        if work_data.get("doi"):
            landing_page_url = f"https://doi.org/{work_data['doi']}"
        
        return AcademicPaper(
            id=work_data.get("id", ""),
            doi=work_data.get("doi"),
            openalex_id=work_data.get("id"),
            title=work_data.get("title", "Untitled"),
            abstract=work_data.get("abstract"),
            publication_year=work_data.get("publication_year"),
            publication_date=work_data.get("publication_date"),
            authors=authors,
            journal=journal,
            source_type=self._determine_source_type(work_data),
            concepts=concepts,
            citation_count=work_data.get("cited_by_count", 0),
            referenced_works_count=work_data.get("referenced_works_count", 0),
            is_open_access=work_data.get("open_access", {}).get("is_oa", False),
            pdf_url=pdf_url,
            landing_page_url=landing_page_url,
            external_urls=external_urls,
            indexed_date=datetime.fromisoformat(work_data["updated_date"].replace("Z", "+00:00")) if work_data.get("updated_date") else None,
            created_date=datetime.now(),
            raw_data=work_data
        )
    
    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: str = "relevance_score:desc"
    ) -> SearchResult:
        """
        Search for academic papers using OpenAlex API
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-200)
            offset: Results offset for pagination
            filters: Additional filters (publication_year, etc.)
            sort: Sort order (relevance_score:desc, cited_by_count:desc, etc.)
        
        Returns:
            SearchResult containing papers and metadata
        """
        search_query = SearchQuery(
            query=query,
            limit=min(limit, 200),
            offset=offset,
            filters=filters or {},
            sort_by=sort
        )
        
        # Build search parameters
        params = {
            "search": query,
            "per-page": search_query.limit,
            "page": (search_query.offset // search_query.limit) + 1,
            "sort": sort
        }
        
        # Add filters
        filter_parts = []
        if filters:
            for key, value in filters.items():
                if key == "publication_year" and isinstance(value, (list, tuple)):
                    filter_parts.append(f"publication_year:{value[0]}-{value[1]}")
                elif key == "open_access" and value:
                    filter_parts.append("is_oa:true")
                elif key == "type":
                    filter_parts.append(f"type:{value}")
        
        if filter_parts:
            params["filter"] = ",".join(filter_parts)
        
        try:
            start_time = asyncio.get_event_loop().time()
            data = await self._make_request("works", params)
            end_time = asyncio.get_event_loop().time()
            
            # Parse papers
            papers = []
            for work_data in data.get("results", []):
                try:
                    paper = self._parse_work(work_data)
                    papers.append(paper)
                except Exception as e:
                    storm_logger.warning(f"Failed to parse work {work_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return SearchResult(
                query=search_query,
                papers=papers,
                total_count=data.get("count"),
                search_time_ms=(end_time - start_time) * 1000,
                source="openalex"
            )
            
        except Exception as e:
            storm_logger.error(f"OpenAlex search failed for query '{query}': {str(e)}")
            return SearchResult(
                query=search_query,
                papers=[],
                total_count=0,
                source="openalex"
            )
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[AcademicPaper]:
        """
        Get a specific paper by OpenAlex ID
        
        Args:
            paper_id: OpenAlex work ID (with or without prefix)
        
        Returns:
            AcademicPaper if found, None otherwise
        """
        # Ensure proper ID format
        if not paper_id.startswith("https://openalex.org/"):
            if paper_id.startswith("W"):
                paper_id = f"https://openalex.org/{paper_id}"
            else:
                paper_id = f"https://openalex.org/W{paper_id}"
        
        try:
            # Extract just the ID part for the API call
            clean_id = paper_id.split("/")[-1]
            data = await self._make_request(f"works/{clean_id}", {})
            return self._parse_work(data)
        except Exception as e:
            storm_logger.error(f"Failed to get paper {paper_id}: {str(e)}")
            return None
    
    async def get_paper_by_doi(self, doi: str) -> Optional[AcademicPaper]:
        """
        Get a specific paper by DOI
        
        Args:
            doi: Digital Object Identifier
        
        Returns:
            AcademicPaper if found, None otherwise
        """
        # Clean DOI format
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        elif doi.startswith("doi:"):
            doi = doi.replace("doi:", "")
        
        try:
            results = await self.search_papers(f'doi:"{doi}"', limit=1)
            return results.papers[0] if results.papers else None
        except Exception as e:
            storm_logger.error(f"Failed to get paper by DOI {doi}: {str(e)}")
            return None
    
    async def search_by_author(self, author_name: str, limit: int = 10) -> SearchResult:
        """Search papers by author name"""
        return await self.search_papers(f'author.display_name:"{author_name}"', limit=limit)
    
    async def search_by_institution(self, institution_name: str, limit: int = 10) -> SearchResult:
        """Search papers by institution"""
        return await self.search_papers(f'institutions.display_name:"{institution_name}"', limit=limit)
    
    async def get_trending_papers(self, days: int = 7, limit: int = 10) -> SearchResult:
        """Get trending papers based on recent citation activity"""
        # OpenAlex doesn't have a direct trending endpoint, so we'll approximate
        # by getting recent papers with high citation counts
        current_year = datetime.now().year
        filters = {
            "publication_year": [current_year - 1, current_year]
        }
        return await self.search_papers(
            query="",  # Empty query to get all
            limit=limit,
            filters=filters,
            sort="cited_by_count:desc"
        )