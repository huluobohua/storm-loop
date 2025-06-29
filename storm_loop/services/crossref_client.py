"""
Crossref API client for publication metadata and DOI resolution
"""
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlencode, quote
import logging
from datetime import datetime

from storm_loop.config import get_config
from storm_loop.models.academic_models import (
    AcademicPaper, Author, Journal, SearchQuery, 
    SearchResult, SourceType
)
from storm_loop.utils.logging import storm_logger


class CrossrefClient:
    """
    Async client for Crossref API
    
    Crossref provides DOI registration and metadata services.
    API docs: https://github.com/CrossRef/rest-api-doc
    """
    
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self.config = get_config()
        self.email = email or self.config.openalex_email  # Reuse email config
        self.session = session
        self._own_session = session is None
        
        # Rate limiting - Crossref is more generous than OpenAlex
        self._request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests * 2)
        self._last_request_time = 0
        self._min_request_interval = 0.05  # 50ms between requests
    
    async def __aenter__(self):
        if self._own_session:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with user agent and contact info"""
        headers = {
            "User-Agent": "STORM-Loop/0.1.0 (https://github.com/huluobohua/storm-loop)"
        }
        if self.email:
            headers["User-Agent"] += f"; mailto:{self.email}"
        return headers
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited request to Crossref API"""
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
            
            storm_logger.debug(f"Crossref request: {url} with params: {clean_params}")
            
            try:
                async with self.session.get(url, headers=headers, params=clean_params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    if response.status == 200:
                        data = await response.json()
                        storm_logger.debug(f"Crossref response successful: {len(str(data))} bytes")
                        return data
                    else:
                        error_text = await response.text()
                        storm_logger.error(f"Crossref API error {response.status}: {error_text}")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
            except asyncio.TimeoutError:
                storm_logger.error(f"Crossref request timeout for {url}")
                raise
            except Exception as e:
                storm_logger.error(f"Crossref request failed: {str(e)}")
                raise
    
    def _parse_author(self, author_data: Dict[str, Any]) -> Author:
        """Parse Crossref author data into Author model"""
        return Author(
            display_name=f"{author_data.get('given', '')} {author_data.get('family', '')}".strip(),
            given_name=author_data.get("given"),
            family_name=author_data.get("family"),
            orcid=author_data.get("ORCID"),
            affiliation=author_data.get("affiliation", [{}])[0].get("name") if author_data.get("affiliation") else None
        )
    
    def _parse_journal(self, work_data: Dict[str, Any]) -> Optional[Journal]:
        """Parse Crossref work data into Journal model"""
        container_title = work_data.get("container-title", [])
        if not container_title:
            return None
        
        return Journal(
            name=container_title[0] if container_title else "Unknown",
            issn=work_data.get("ISSN", [None])[0],
            publisher=work_data.get("publisher")
        )
    
    def _determine_source_type(self, work_data: Dict[str, Any]) -> SourceType:
        """Determine source type from Crossref work data"""
        type_mapping = {
            "journal-article": SourceType.JOURNAL_ARTICLE,
            "book-chapter": SourceType.BOOK_CHAPTER,
            "book": SourceType.BOOK,
            "proceedings-article": SourceType.CONFERENCE_PAPER,
            "posted-content": SourceType.PREPRINT,
            "dissertation": SourceType.THESIS,
            "report": SourceType.REPORT,
            "monograph": SourceType.BOOK
        }
        
        crossref_type = work_data.get("type", "").lower()
        return type_mapping.get(crossref_type, SourceType.OTHER)
    
    def _extract_publication_date(self, work_data: Dict[str, Any]) -> tuple[Optional[int], Optional[str]]:
        """Extract publication year and date from Crossref data"""
        # Try different date fields
        date_fields = ["published-print", "published-online", "created", "deposited"]
        
        for field in date_fields:
            if field in work_data:
                date_parts = work_data[field].get("date-parts", [[]])[0]
                if date_parts:
                    year = date_parts[0] if len(date_parts) > 0 else None
                    if len(date_parts) >= 3:
                        month, day = date_parts[1], date_parts[2]
                        date_str = f"{year}-{month:02d}-{day:02d}" if year and month and day else None
                    else:
                        date_str = str(year) if year else None
                    return year, date_str
        
        return None, None
    
    def _parse_work(self, work_data: Dict[str, Any]) -> AcademicPaper:
        """Parse Crossref work data into AcademicPaper model"""
        # Parse authors
        authors = []
        for author_data in work_data.get("author", []):
            authors.append(self._parse_author(author_data))
        
        # Parse journal
        journal = self._parse_journal(work_data)
        
        # Extract dates
        publication_year, publication_date = self._extract_publication_date(work_data)
        
        # Extract title
        title_list = work_data.get("title", [])
        title = title_list[0] if title_list else "Untitled"
        
        # Extract abstract
        abstract_list = work_data.get("abstract")
        abstract = abstract_list if isinstance(abstract_list, str) else None
        
        # Build URLs
        doi = work_data.get("DOI")
        landing_page_url = f"https://doi.org/{doi}" if doi else None
        
        # Extract additional URLs
        external_urls = []
        for link in work_data.get("link", []):
            if link.get("URL"):
                external_urls.append(link["URL"])
        
        return AcademicPaper(
            id=f"crossref:{doi}" if doi else f"crossref:{work_data.get('URL', 'unknown')}",
            doi=doi,
            title=title,
            abstract=abstract,
            publication_year=publication_year,
            publication_date=publication_date,
            authors=authors,
            journal=journal,
            source_type=self._determine_source_type(work_data),
            citation_count=work_data.get("is-referenced-by-count", 0),
            referenced_works_count=work_data.get("references-count", 0),
            landing_page_url=landing_page_url,
            external_urls=external_urls,
            created_date=datetime.now(),
            raw_data=work_data
        )
    
    async def search_papers(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: str = "relevance"
    ) -> SearchResult:
        """
        Search for publications using Crossref API
        
        Args:
            query: Search query string
            limit: Maximum number of results (1-1000)
            offset: Results offset for pagination
            filters: Additional filters (from_pub_date, until_pub_date, etc.)
            sort: Sort order (relevance, score, updated, deposited, etc.)
        
        Returns:
            SearchResult containing papers and metadata
        """
        search_query = SearchQuery(
            query=query,
            limit=min(limit, 1000),
            offset=offset,
            filters=filters or {},
            sort_by=sort
        )
        
        # Build search parameters
        params = {
            "query": query,
            "rows": search_query.limit,
            "offset": search_query.offset,
            "sort": sort
        }
        
        # Add filters
        if filters:
            for key, value in filters.items():
                if key == "publication_year" and isinstance(value, (list, tuple)):
                    if len(value) >= 2:
                        params["from-pub-date"] = f"{value[0]}-01-01"
                        params["until-pub-date"] = f"{value[1]}-12-31"
                elif key == "type":
                    params["filter"] = f"type:{value}"
                elif key == "publisher":
                    params["filter"] = f"publisher-name:{value}"
        
        try:
            start_time = asyncio.get_event_loop().time()
            data = await self._make_request("works", params)
            end_time = asyncio.get_event_loop().time()
            
            # Parse papers
            papers = []
            message = data.get("message", {})
            for work_data in message.get("items", []):
                try:
                    paper = self._parse_work(work_data)
                    papers.append(paper)
                except Exception as e:
                    storm_logger.warning(f"Failed to parse work {work_data.get('DOI', 'unknown')}: {str(e)}")
                    continue
            
            return SearchResult(
                query=search_query,
                papers=papers,
                total_count=message.get("total-results"),
                search_time_ms=(end_time - start_time) * 1000,
                source="crossref"
            )
            
        except Exception as e:
            storm_logger.error(f"Crossref search failed for query '{query}': {str(e)}")
            return SearchResult(
                query=search_query,
                papers=[],
                total_count=0,
                source="crossref"
            )
    
    async def get_paper_by_doi(self, doi: str) -> Optional[AcademicPaper]:
        """
        Get a specific paper by DOI from Crossref
        
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
            data = await self._make_request(f"works/{quote(doi, safe='')}", {})
            work_data = data.get("message", {})
            return self._parse_work(work_data) if work_data else None
        except Exception as e:
            storm_logger.error(f"Failed to get paper by DOI {doi}: {str(e)}")
            return None
    
    async def resolve_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DOI to get basic metadata
        
        Args:
            doi: Digital Object Identifier
        
        Returns:
            Raw metadata dict if found, None otherwise
        """
        try:
            data = await self._make_request(f"works/{quote(doi, safe='')}", {})
            return data.get("message")
        except Exception as e:
            storm_logger.error(f"Failed to resolve DOI {doi}: {str(e)}")
            return None
    
    async def get_publication_metadata(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive publication metadata by DOI
        
        Args:
            doi: Digital Object Identifier
        
        Returns:
            Metadata dictionary if found, None otherwise
        """
        return await self.resolve_doi(doi)
    
    async def search_by_author(self, author_name: str, limit: int = 10) -> SearchResult:
        """Search publications by author name"""
        return await self.search_papers(f'author:"{author_name}"', limit=limit)
    
    async def search_by_title(self, title: str, limit: int = 10) -> SearchResult:
        """Search publications by title"""
        return await self.search_papers(f'title:"{title}"', limit=limit)
    
    async def search_by_publisher(self, publisher: str, limit: int = 10) -> SearchResult:
        """Search publications by publisher"""
        filters = {"publisher": publisher}
        return await self.search_papers("", limit=limit, filters=filters)
    
    async def get_journal_info(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Get journal information by ISSN
        
        Args:
            issn: International Standard Serial Number
        
        Returns:
            Journal metadata if found, None otherwise
        """
        try:
            data = await self._make_request(f"journals/{issn}", {})
            return data.get("message")
        except Exception as e:
            storm_logger.error(f"Failed to get journal info for ISSN {issn}: {str(e)}")
            return None
    
    async def validate_doi(self, doi: str) -> bool:
        """
        Validate if a DOI exists in Crossref
        
        Args:
            doi: Digital Object Identifier to validate
        
        Returns:
            True if DOI exists, False otherwise
        """
        try:
            result = await self.resolve_doi(doi)
            return result is not None
        except Exception:
            return False