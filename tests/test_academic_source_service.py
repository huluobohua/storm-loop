"""
Tests for academic source service
"""
import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from storm_loop.models.academic_models import AcademicPaper, Author, SearchResult, SearchQuery
from storm_loop.services.academic_source_service import AcademicSourceService


class TestAcademicSourceService:
    """Test AcademicSourceService functionality"""
    
    @pytest.fixture
    async def service(self):
        """Fixture for AcademicSourceService instance"""
        async with AcademicSourceService() as service:
            yield service
    
    @pytest.fixture
    def mock_openalex_results(self):
        """Mock OpenAlex search results"""
        papers = [
            AcademicPaper(
                id="openalex_1",
                title="OpenAlex Paper 1",
                doi="10.1000/test1",
                citation_count=100,
                publication_year=2023
            ),
            AcademicPaper(
                id="openalex_2", 
                title="OpenAlex Paper 2",
                doi="10.1000/test2",
                citation_count=50,
                publication_year=2022
            )
        ]
        return SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=papers,
            total_count=2,
            source="openalex"
        )
    
    @pytest.fixture
    def mock_crossref_results(self):
        """Mock Crossref search results"""
        papers = [
            AcademicPaper(
                id="crossref_1",
                title="Crossref Paper 1",
                doi="10.1000/test3",
                citation_count=75,
                publication_year=2023
            ),
            AcademicPaper(
                id="crossref_2",
                title="Crossref Paper 2", 
                doi="10.1000/test1",  # Duplicate DOI for deduplication test
                citation_count=100,
                publication_year=2023
            )
        ]
        return SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=papers,
            total_count=2,
            source="crossref"
        )
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization and cleanup"""
        async with AcademicSourceService() as service:
            assert service is not None
            assert service.quality_scorer is not None
            assert service.openalex_client is not None
            assert service.crossref_client is not None
    
    @pytest.mark.asyncio
    async def test_search_papers_openalex_only(self, service, mock_openalex_results):
        """Test searching papers with OpenAlex only"""
        with patch.object(service, '_search_openalex', return_value=mock_openalex_results):
            result = await service.search_papers(
                query="machine learning",
                limit=10,
                sources=['openalex']
            )
            
            assert isinstance(result, SearchResult)
            assert len(result.papers) == 2
            assert result.source == "academic_source_service"
            assert all(paper.quality_score is not None for paper in result.papers)
    
    @pytest.mark.asyncio
    async def test_search_papers_multiple_sources(self, service, mock_openalex_results, mock_crossref_results):
        """Test searching papers across multiple sources"""
        with patch.object(service, '_search_openalex', return_value=mock_openalex_results), \
             patch.object(service, '_search_crossref', return_value=mock_crossref_results):
            
            result = await service.search_papers(
                query="machine learning",
                limit=10,
                sources=['openalex', 'crossref']
            )
            
            assert isinstance(result, SearchResult)
            # Should have 3 unique papers after deduplication (one DOI is duplicate)
            assert len(result.papers) == 3
            assert result.source == "academic_source_service"
    
    @pytest.mark.asyncio
    async def test_deduplication(self, service):
        """Test paper deduplication"""
        papers = [
            AcademicPaper(id="1", title="Paper 1", doi="10.1000/test1"),
            AcademicPaper(id="2", title="Paper 2", doi="10.1000/test2"),
            AcademicPaper(id="3", title="Paper 1", doi="10.1000/test1"),  # Duplicate DOI
            AcademicPaper(id="4", title="Paper 2", doi=None),  # Duplicate title
        ]
        
        deduplicated = service._deduplicate_papers(papers)
        
        # Should have 2 unique papers
        assert len(deduplicated) == 2
        assert deduplicated[0].doi == "10.1000/test1"
        assert deduplicated[1].doi == "10.1000/test2"
    
    @pytest.mark.asyncio
    async def test_quality_scoring(self, service):
        """Test quality scoring of papers"""
        papers = [
            AcademicPaper(
                id="1", 
                title="High Quality Paper",
                citation_count=100,
                publication_year=2023,
                authors=[Author(display_name="Dr. Test")]
            ),
            AcademicPaper(
                id="2",
                title="Low Quality Paper",
                citation_count=1,
                publication_year=1990
            )
        ]
        
        scored_papers = await service._score_papers_quality(papers)
        
        assert len(scored_papers) == 2
        assert all(paper.quality_score is not None for paper in scored_papers)
        # High quality paper should score better
        assert scored_papers[0].quality_score > scored_papers[1].quality_score
    
    @pytest.mark.asyncio 
    async def test_paper_ranking(self, service):
        """Test paper ranking by combined score"""
        papers = [
            AcademicPaper(id="1", title="Old Paper", publication_year=1990, quality_score=0.3),
            AcademicPaper(id="2", title="Recent Paper", publication_year=2023, quality_score=0.8, citation_count=50),
            AcademicPaper(id="3", title="Medium Paper", publication_year=2020, quality_score=0.6)
        ]
        
        ranked = service._rank_papers(papers)
        
        # Recent high-quality paper should be first
        assert ranked[0].id == "2"
        assert ranked[1].id == "3"
        assert ranked[2].id == "1"
    
    @pytest.mark.asyncio
    async def test_get_paper_by_doi(self, service):
        """Test getting paper by DOI"""
        mock_paper = AcademicPaper(
            id="test_paper",
            title="Test Paper",
            doi="10.1000/test"
        )
        
        with patch.object(service.openalex_client, 'get_paper_by_doi', return_value=mock_paper):
            result = await service.get_paper_by_doi("10.1000/test")
            
            assert result is not None
            assert result.doi == "10.1000/test"
            assert result.quality_score is not None
    
    @pytest.mark.asyncio
    async def test_get_paper_by_doi_fallback(self, service):
        """Test DOI lookup with fallback to Crossref"""
        mock_paper = AcademicPaper(
            id="test_paper",
            title="Test Paper", 
            doi="10.1000/test"
        )
        
        # OpenAlex fails, Crossref succeeds
        with patch.object(service.openalex_client, 'get_paper_by_doi', return_value=None), \
             patch.object(service.crossref_client, 'get_paper_by_doi', return_value=mock_paper):
            
            result = await service.get_paper_by_doi("10.1000/test")
            
            assert result is not None
            assert result.doi == "10.1000/test"
    
    @pytest.mark.asyncio
    async def test_validate_doi(self, service):
        """Test DOI validation"""
        with patch.object(service.crossref_client, 'validate_doi', return_value=True):
            result = await service.validate_doi("10.1000/test")
            assert result is True
        
        with patch.object(service.crossref_client, 'validate_doi', return_value=False):
            result = await service.validate_doi("10.1000/invalid")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_search_by_author(self, service, mock_openalex_results):
        """Test searching papers by author"""
        with patch.object(service, 'search_papers', return_value=mock_openalex_results):
            result = await service.search_by_author("John Doe", limit=5)
            
            assert isinstance(result, SearchResult)
            # Should have called search_papers with author query
            service.search_papers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_trending_papers(self, service, mock_openalex_results):
        """Test getting trending papers"""
        with patch.object(service.openalex_client, 'get_trending_papers', return_value=mock_openalex_results):
            result = await service.get_trending_papers(days=7, limit=10)
            
            assert isinstance(result, SearchResult)
            assert len(result.papers) > 0
    
    @pytest.mark.asyncio
    async def test_caching(self, service, mock_openalex_results):
        """Test result caching"""
        with patch.object(service, '_search_openalex', return_value=mock_openalex_results):
            # First call
            result1 = await service.search_papers("test query", limit=5, sources=['openalex'])
            
            # Second call should use cache
            result2 = await service.search_papers("test query", limit=5, sources=['openalex'])
            
            # Should only call API once due to caching
            assert service._search_openalex.call_count == 1
            assert result1.papers == result2.papers
    
    @pytest.mark.asyncio
    async def test_quality_threshold_filtering(self, service, mock_openalex_results):
        """Test filtering by quality threshold"""
        # Mock papers with different quality scores
        papers = [
            AcademicPaper(id="high", title="High Quality", quality_score=0.9),
            AcademicPaper(id="low", title="Low Quality", quality_score=0.3)
        ]
        mock_result = SearchResult(
            query=SearchQuery(query="test", limit=10),
            papers=papers,
            total_count=2,
            source="test"
        )
        
        with patch.object(service, '_search_openalex', return_value=mock_result), \
             patch.object(service, '_score_papers_quality', return_value=papers):
            
            result = await service.search_papers(
                "test",
                quality_threshold=0.5,
                sources=['openalex']
            )
            
            # Should only return high quality paper
            assert len(result.papers) == 1
            assert result.papers[0].id == "high"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling in search"""
        with patch.object(service, '_search_openalex', side_effect=Exception("API Error")):
            result = await service.search_papers("test query", sources=['openalex'])
            
            # Should return empty result on error, not raise exception
            assert isinstance(result, SearchResult)
            assert len(result.papers) == 0
    
    def test_cache_key_generation(self, service):
        """Test cache key generation"""
        key1 = service._get_cache_key("search_papers", query="test", limit=10)
        key2 = service._get_cache_key("search_papers", query="test", limit=10)
        key3 = service._get_cache_key("search_papers", query="different", limit=10)
        
        # Same parameters should generate same key
        assert key1 == key2
        # Different parameters should generate different key
        assert key1 != key3
    
    def test_cache_operations(self, service):
        """Test cache set and get operations"""
        test_data = {"test": "data"}
        cache_key = "test_key"
        
        # Initially should return None
        assert service._get_from_cache(cache_key) is None
        
        # Set cache
        service._set_cache(cache_key, test_data)
        
        # Should now return cached data
        cached = service._get_from_cache(cache_key)
        assert cached == test_data

    @pytest.mark.asyncio
    async def test_fallback_triggered(self, service):
        """Ensure fallback search is used when no academic results."""
        empty = SearchResult(
            query=SearchQuery(query="q", limit=5), papers=[], total_count=0, source="openalex"
        )
        with patch.object(service, "_search_openalex", return_value=empty), \
             patch.object(service, "_search_crossref", return_value=empty), \
             patch.object(service, "fallback_search", return_value=[AcademicPaper(id="p", title="fallback")]) as fb:
            result = await service.search_papers("q", limit=5)
            fb.assert_called_once()
            assert len(result.papers) == 1
            assert result.papers[0].title == "fallback"

    @pytest.mark.asyncio
    async def test_fallback_search(self, service):
        """Test fallback_search converts results to papers."""
        with patch.object(service.perplexity_client, "search", return_value=[{"title": "T", "url": "u", "snippet": "s"}]):
            papers = await service.fallback_search("query", limit=1)
            assert len(papers) == 1
            assert papers[0].title == "T"

    @pytest.mark.asyncio
    async def test_fallback_search_failure(self, service, caplog):
        """fallback_search logs failure and returns empty list."""
        caplog.set_level(logging.WARNING)
        with patch.object(service.perplexity_client, "search", side_effect=Exception("boom")):
            papers = await service.fallback_search("bad", limit=1)
            assert papers == []
            assert any("Perplexity fallback failed" in r.message for r in caplog.records)
