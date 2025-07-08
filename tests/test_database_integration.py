"""
Academic database integration tests for OpenAlex, Crossref, and institutional databases.
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime, timedelta

from knowledge_storm.services.crossref_service import CrossrefService
from knowledge_storm.services.academic_source_service import AcademicSourceService
from knowledge_storm.rm import VectorRM


class TestAPIIntegrationTesting:
    """Comprehensive testing of OpenAlex, Crossref, and institutional database connections."""
    
    @pytest.mark.asyncio
    async def test_crossref_api_integration(
        self,
        mock_crossref_service
    ):
        """Test Crossref API integration and response handling."""
        # Mock realistic Crossref responses
        mock_responses = {
            "search_papers": [
                {
                    "DOI": "10.1038/nature12373",
                    "title": ["Machine learning for molecular and materials science"],
                    "author": [
                        {"given": "Keith T.", "family": "Butler"},
                        {"given": "Daniel W.", "family": "Davies"}
                    ],
                    "published-print": {"date-parts": [[2023, 3, 15]]},
                    "container-title": ["Nature"],
                    "volume": "559",
                    "page": "547-555",
                    "abstract": "Machine learning approaches are being used to accelerate...",
                    "reference-count": 45,
                    "is-referenced-by-count": 234
                }
            ],
            "paper_details": {
                "DOI": "10.1038/nature12373",
                "title": ["Machine learning for molecular and materials science"],
                "author": [
                    {"given": "Keith T.", "family": "Butler"},
                    {"given": "Daniel W.", "family": "Davies"}
                ],
                "published-print": {"date-parts": [[2023, 3, 15]]},
                "container-title": ["Nature"],
                "volume": "559",
                "page": "547-555",
                "abstract": "Machine learning approaches are being used to accelerate...",
                "reference": [
                    {
                        "DOI": "10.1021/acs.chemmater.6b00114",
                        "article-title": "Crystal structure prediction"
                    }
                ],
                "citation": [
                    {
                        "DOI": "10.1038/s41524-020-0283-z",
                        "article-title": "Materials discovery with machine learning"
                    }
                ]
            }
        }
        
        # Configure mock service
        mock_crossref_service.search_papers = AsyncMock(return_value=mock_responses["search_papers"])
        mock_crossref_service.get_paper_details = AsyncMock(return_value=mock_responses["paper_details"])
        
        # Test search functionality
        search_query = "machine learning materials science"
        search_results = await mock_crossref_service.search_papers(search_query)
        
        # Validate search results structure
        assert len(search_results) == 1
        paper = search_results[0]
        
        assert "DOI" in paper
        assert "title" in paper
        assert "author" in paper
        assert "published-print" in paper
        assert "container-title" in paper
        
        # Test paper details retrieval
        doi = paper["DOI"]
        paper_details = await mock_crossref_service.get_paper_details(doi)
        
        # Validate detailed paper information
        assert paper_details["DOI"] == doi
        assert "reference" in paper_details
        assert "citation" in paper_details
        assert len(paper_details["reference"]) > 0
        assert len(paper_details["citation"]) > 0
        
        # Test API call tracking
        mock_crossref_service.search_papers.assert_called_once_with(search_query)
        mock_crossref_service.get_paper_details.assert_called_once_with(doi)
    
    @pytest.mark.asyncio
    async def test_openalex_api_integration(
        self,
        mock_academic_source_service
    ):
        """Test OpenAlex API integration and response handling."""
        # Mock OpenAlex API responses
        mock_openalex_response = [
            {
                "id": "https://openalex.org/W2963077736",
                "title": "Attention Is All You Need",
                "display_name": "Attention Is All You Need",
                "authorships": [
                    {
                        "author": {
                            "id": "https://openalex.org/A5023888391",
                            "display_name": "Ashish Vaswani"
                        },
                        "institutions": [
                            {
                                "id": "https://openalex.org/I1281820609",
                                "display_name": "Google"
                            }
                        ]
                    }
                ],
                "publication_date": "2017-06-12",
                "host_venue": {
                    "display_name": "Neural Information Processing Systems",
                    "type": "conference"
                },
                "abstract_inverted_index": {
                    "The": [0, 45],
                    "dominant": [1],
                    "sequence": [2, 23],
                    "transduction": [3],
                    "models": [4, 15],
                    "are": [5, 16]
                },
                "cited_by_count": 15420,
                "concepts": [
                    {
                        "id": "https://openalex.org/C154945302",
                        "display_name": "Artificial intelligence",
                        "score": 0.85
                    },
                    {
                        "id": "https://openalex.org/C41008148",
                        "display_name": "Computer science",
                        "score": 0.75
                    }
                ],
                "referenced_works": [
                    "https://openalex.org/W2963077736",
                    "https://openalex.org/W2148184671"
                ]
            }
        ]
        
        # Configure mock service
        mock_academic_source_service.search_papers = AsyncMock(return_value=mock_openalex_response)
        mock_academic_source_service.get_paper_citations = AsyncMock(return_value={
            "citing_papers": ["https://openalex.org/W123456789"],
            "citation_count": 15420
        })
        
        # Test OpenAlex search
        search_query = "attention mechanism transformer"
        search_results = await mock_academic_source_service.search_papers(search_query)
        
        # Validate OpenAlex response structure
        assert len(search_results) == 1
        paper = search_results[0]
        
        assert "id" in paper
        assert "title" in paper
        assert "authorships" in paper
        assert "publication_date" in paper
        assert "host_venue" in paper
        assert "cited_by_count" in paper
        assert "concepts" in paper
        
        # Test citation analysis
        paper_id = paper["id"]
        citation_data = await mock_academic_source_service.get_paper_citations(paper_id)
        
        assert "citing_papers" in citation_data
        assert "citation_count" in citation_data
        assert citation_data["citation_count"] == 15420
        
        # Validate API calls
        mock_academic_source_service.search_papers.assert_called_once_with(search_query)
        mock_academic_source_service.get_paper_citations.assert_called_once_with(paper_id)
    
    @pytest.mark.asyncio
    async def test_institutional_database_integration(
        self,
        mock_academic_source_service
    ):
        """Test integration with institutional databases (IEEE, ACM, etc.)."""
        # Mock institutional database responses
        institutional_responses = {
            "ieee": [
                {
                    "id": "ieee_8766229",
                    "title": "Deep Learning for Computer Vision: A Brief Review",
                    "authors": ["Li Deng", "Dong Yu"],
                    "publication": "IEEE Signal Processing Magazine",
                    "year": 2019,
                    "volume": "36",
                    "issue": "6",
                    "pages": "85-108",
                    "doi": "10.1109/MSP.2019.2936881",
                    "abstract": "Deep learning has revolutionized computer vision...",
                    "keywords": ["deep learning", "computer vision", "neural networks"],
                    "citation_count": 892
                }
            ],
            "acm": [
                {
                    "id": "acm_3292500.3330701",
                    "title": "Graph Neural Networks: A Review of Methods and Applications",
                    "authors": ["Jie Zhou", "Ganqu Cui", "Shengding Hu"],
                    "publication": "ACM Computing Surveys",
                    "year": 2020,
                    "volume": "53",
                    "issue": "1",
                    "pages": "1-34",
                    "doi": "10.1145/3394486.3403202",
                    "abstract": "Graph neural networks have emerged as a powerful tool...",
                    "keywords": ["graph neural networks", "deep learning", "graph analysis"],
                    "citation_count": 1543
                }
            ]
        }
        
        # Test IEEE database integration
        mock_academic_source_service.search_institutional_db = AsyncMock()
        
        # Configure IEEE search
        mock_academic_source_service.search_institutional_db.side_effect = [
            institutional_responses["ieee"],
            institutional_responses["acm"]
        ]
        
        # Test IEEE search
        ieee_results = await mock_academic_source_service.search_institutional_db(
            "deep learning computer vision", 
            database="ieee"
        )
        
        assert len(ieee_results) == 1
        ieee_paper = ieee_results[0]
        assert ieee_paper["publication"] == "IEEE Signal Processing Magazine"
        assert "10.1109" in ieee_paper["doi"]  # IEEE DOI format
        
        # Test ACM search
        acm_results = await mock_academic_source_service.search_institutional_db(
            "graph neural networks",
            database="acm"
        )
        
        assert len(acm_results) == 1
        acm_paper = acm_results[0]
        assert acm_paper["publication"] == "ACM Computing Surveys"
        assert "10.1145" in acm_paper["doi"]  # ACM DOI format
        
        # Validate database-specific features
        assert ieee_paper["keywords"] == ["deep learning", "computer vision", "neural networks"]
        assert acm_paper["keywords"] == ["graph neural networks", "deep learning", "graph analysis"]


class TestRateLimitingCompliance:
    """Test proper handling of API rate limits during intensive research."""
    
    @pytest.mark.asyncio
    async def test_crossref_rate_limiting(
        self,
        mock_crossref_service
    ):
        """Test Crossref API rate limiting compliance."""
        # Crossref allows 50 requests per second for polite pool
        rate_limit_config = {
            "requests_per_second": 50,
            "burst_allowance": 100,
            "backoff_strategy": "exponential"
        }
        
        # Mock rate limiter
        class CrossrefRateLimiter:
            def __init__(self, rps=50):
                self.rps = rps
                self.last_request_time = 0
                self.request_count = 0
                
            async def acquire_permit(self):
                current_time = asyncio.get_event_loop().time()
                
                # Calculate time since last request
                time_since_last = current_time - self.last_request_time
                
                # If we need to wait, do so
                if time_since_last < (1.0 / self.rps):
                    wait_time = (1.0 / self.rps) - time_since_last
                    await asyncio.sleep(wait_time)
                
                self.last_request_time = asyncio.get_event_loop().time()
                self.request_count += 1
                
                return True
        
        rate_limiter = CrossrefRateLimiter(rate_limit_config["requests_per_second"])
        
        # Mock service with rate limiting
        async def rate_limited_search(query):
            await rate_limiter.acquire_permit()
            
            # Mock response
            return [{
                "DOI": f"10.1000/test{rate_limiter.request_count}",
                "title": [f"Test Paper {rate_limiter.request_count}"],
                "author": [{"given": "Test", "family": "Author"}]
            }]
        
        mock_crossref_service.search_papers = rate_limited_search
        
        # Test intensive requests
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(100):  # 100 requests
            task = asyncio.create_task(
                mock_crossref_service.search_papers(f"query {i}")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Validate rate limiting compliance
        actual_rps = len(results) / total_time
        max_allowed_rps = rate_limit_config["requests_per_second"] * 1.1  # 10% tolerance
        
        assert actual_rps <= max_allowed_rps, f"Rate limit exceeded: {actual_rps} > {max_allowed_rps}"
        assert len(results) == 100, "All requests should complete"
        
        # Minimum time check (should take at least 2 seconds for 100 requests at 50/sec)
        min_expected_time = 100 / rate_limit_config["requests_per_second"]
        assert total_time >= min_expected_time * 0.9, "Requests completed too quickly"
    
    @pytest.mark.asyncio
    async def test_api_error_handling_and_retry(
        self,
        mock_crossref_service,
        mock_academic_source_service
    ):
        """Test API error handling and retry strategies."""
        # Mock different error scenarios
        error_scenarios = [
            {"error_type": "rate_limit", "status_code": 429, "retry_after": 1},
            {"error_type": "server_error", "status_code": 500, "retry": True},
            {"error_type": "network_timeout", "exception": asyncio.TimeoutError()},
            {"error_type": "invalid_response", "status_code": 400, "retry": False}
        ]
        
        for scenario in error_scenarios:
            # Create mock service with error injection
            call_count = 0
            
            async def error_injected_search(query):
                nonlocal call_count
                call_count += 1
                
                if call_count <= 2:  # Fail first 2 attempts
                    if scenario["error_type"] == "rate_limit":
                        raise Exception(f"HTTP {scenario['status_code']}: Rate limit exceeded")
                    elif scenario["error_type"] == "server_error":
                        raise Exception(f"HTTP {scenario['status_code']}: Internal server error")
                    elif scenario["error_type"] == "network_timeout":
                        raise scenario["exception"]
                    elif scenario["error_type"] == "invalid_response":
                        raise Exception(f"HTTP {scenario['status_code']}: Bad request")
                
                # Success on 3rd attempt (if retryable)
                return [{"title": "Success after retry", "doi": "10.1000/success"}]
            
            # Test retry logic
            mock_crossref_service.search_papers = error_injected_search
            
            # Create retry wrapper
            async def search_with_retry(query, max_retries=3):
                for attempt in range(max_retries + 1):
                    try:
                        result = await mock_crossref_service.search_papers(query)
                        return {"success": True, "result": result, "attempts": attempt + 1}
                    
                    except Exception as e:
                        error_message = str(e)
                        
                        # Determine if error is retryable
                        is_retryable = (
                            "rate limit" in error_message.lower() or
                            "500" in error_message or
                            isinstance(e, asyncio.TimeoutError)
                        )
                        
                        if not is_retryable or attempt >= max_retries:
                            return {
                                "success": False, 
                                "error": error_message, 
                                "attempts": attempt + 1
                            }
                        
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                
                return {"success": False, "error": "Max retries exceeded"}
            
            # Test retry behavior
            result = await search_with_retry("test query")
            
            if scenario["error_type"] in ["rate_limit", "server_error", "network_timeout"]:
                # Should succeed after retries
                assert result["success"] is True
                assert result["attempts"] == 3  # Failed twice, succeeded on third
                assert len(result["result"]) == 1
                
            elif scenario["error_type"] == "invalid_response":
                # Should fail immediately (not retryable)
                assert result["success"] is False
                assert result["attempts"] == 1  # No retries for 400 errors
                assert "400" in result["error"]
            
            # Reset call count for next scenario
            call_count = 0


class TestDataQualityValidation:
    """Test handling of incomplete, incorrect, or corrupted academic data."""
    
    @pytest.mark.asyncio
    async def test_incomplete_paper_data_handling(
        self,
        mock_crossref_service
    ):
        """Test handling of papers with missing or incomplete data."""
        # Mock papers with various data quality issues
        incomplete_papers = [
            {
                # Missing title
                "DOI": "10.1000/missing_title",
                "author": [{"given": "John", "family": "Doe"}],
                "published-print": {"date-parts": [[2023, 1, 1]]}
            },
            {
                # Missing authors
                "DOI": "10.1000/missing_authors",
                "title": ["Paper with No Authors"],
                "published-print": {"date-parts": [[2023, 1, 1]]}
            },
            {
                # Missing publication date
                "DOI": "10.1000/missing_date",
                "title": ["Paper with No Date"],
                "author": [{"given": "Jane", "family": "Smith"}]
            },
            {
                # Malformed DOI
                "DOI": "invalid_doi_format",
                "title": ["Paper with Invalid DOI"],
                "author": [{"given": "Bob", "family": "Wilson"}],
                "published-print": {"date-parts": [[2023, 1, 1]]}
            },
            {
                # Empty abstract
                "DOI": "10.1000/empty_abstract",
                "title": ["Paper with Empty Abstract"],
                "author": [{"given": "Alice", "family": "Brown"}],
                "published-print": {"date-parts": [[2023, 1, 1]]},
                "abstract": ""
            }
        ]
        
        mock_crossref_service.search_papers = AsyncMock(return_value=incomplete_papers)
        
        # Create data quality validator
        class DataQualityValidator:
            @staticmethod
            def validate_paper(paper: dict) -> dict:
                """Validate and clean paper data."""
                validation_result = {
                    "is_valid": True,
                    "issues": [],
                    "cleaned_paper": paper.copy()
                }
                
                # Check required fields
                required_fields = ["DOI", "title", "author", "published-print"]
                
                for field in required_fields:
                    if field not in paper or not paper[field]:
                        validation_result["issues"].append(f"Missing {field}")
                        validation_result["is_valid"] = False
                
                # Validate DOI format
                if "DOI" in paper:
                    doi = paper["DOI"]
                    if not doi.startswith("10."):
                        validation_result["issues"].append("Invalid DOI format")
                        validation_result["is_valid"] = False
                
                # Validate title
                if "title" in paper and isinstance(paper["title"], list):
                    if not paper["title"] or not paper["title"][0].strip():
                        validation_result["issues"].append("Empty or invalid title")
                        validation_result["is_valid"] = False
                
                # Validate authors
                if "author" in paper:
                    if not isinstance(paper["author"], list) or len(paper["author"]) == 0:
                        validation_result["issues"].append("No valid authors")
                        validation_result["is_valid"] = False
                
                # Clean and normalize data
                if validation_result["is_valid"]:
                    cleaned = validation_result["cleaned_paper"]
                    
                    # Normalize title
                    if "title" in cleaned and isinstance(cleaned["title"], list):
                        cleaned["title"] = cleaned["title"][0].strip()
                    
                    # Normalize authors
                    if "author" in cleaned:
                        for author in cleaned["author"]:
                            if "given" not in author:
                                author["given"] = ""
                            if "family" not in author:
                                author["family"] = "Unknown"
                    
                    # Add abstract if missing
                    if "abstract" not in cleaned or not cleaned["abstract"]:
                        cleaned["abstract"] = "Abstract not available"
                
                return validation_result
        
        validator = DataQualityValidator()
        
        # Test data quality validation
        search_results = await mock_crossref_service.search_papers("test query")
        
        validation_results = []
        valid_papers = []
        
        for paper in search_results:
            validation = validator.validate_paper(paper)
            validation_results.append(validation)
            
            if validation["is_valid"]:
                valid_papers.append(validation["cleaned_paper"])
        
        # Validate quality checking
        assert len(validation_results) == len(incomplete_papers)
        
        # Count validation issues
        papers_with_issues = sum(1 for v in validation_results if not v["is_valid"])
        papers_without_issues = len(validation_results) - papers_with_issues
        
        # Should detect all problematic papers
        assert papers_with_issues == 4  # 4 out of 5 have issues
        assert papers_without_issues == 1  # Only the last one might be valid after cleaning
        
        # Validate specific issue detection
        issue_types = []
        for validation in validation_results:
            issue_types.extend(validation["issues"])
        
        assert any("Missing title" in issue for issue in issue_types)
        assert any("Missing author" in issue for issue in issue_types)
        assert any("Missing published-print" in issue for issue in issue_types)
        assert any("Invalid DOI format" in issue for issue in issue_types)
    
    @pytest.mark.asyncio
    async def test_corrupted_response_handling(
        self,
        mock_academic_source_service
    ):
        """Test handling of corrupted or malformed API responses."""
        # Mock corrupted responses
        corrupted_responses = [
            # Invalid JSON structure
            '{"incomplete": "json"',
            
            # Missing required fields
            '{"status": "ok", "results": [{"invalid": "paper"}]}',
            
            # Unexpected data types
            '{"results": "should_be_array"}',
            
            # Nested corruption
            '{"results": [{"title": null, "authors": {}}]}',
            
            # Valid structure but corrupted data
            '{"results": [{"id": "test", "title": "\\u0000\\u0001Invalid Unicode"}]}'
        ]
        
        # Test corrupted response handling
        for i, corrupted_response in enumerate(corrupted_responses):
            # Mock corrupted API response
            async def corrupted_api_call(query):
                if i == 0:  # Invalid JSON
                    raise json.JSONDecodeError("Invalid JSON", corrupted_response, 0)
                elif i == 1:  # Missing fields
                    return {"status": "ok", "results": [{"invalid": "paper"}]}
                elif i == 2:  # Wrong data type
                    return {"results": "should_be_array"}
                elif i == 3:  # Nested corruption
                    return {"results": [{"title": None, "authors": {}}]}
                elif i == 4:  # Unicode corruption
                    return {"results": [{"id": "test", "title": "\u0000\u0001Invalid Unicode"}]}
            
            mock_academic_source_service.search_papers = corrupted_api_call
            
            # Create response validator
            async def safe_search_with_validation(query):
                try:
                    raw_result = await mock_academic_source_service.search_papers(query)
                    
                    # Validate response structure
                    if not isinstance(raw_result, dict):
                        return {"error": "Response is not a dictionary", "raw": str(raw_result)}
                    
                    if "results" not in raw_result:
                        return {"error": "Missing 'results' field", "raw": raw_result}
                    
                    if not isinstance(raw_result["results"], list):
                        return {"error": "'results' is not a list", "raw": raw_result}
                    
                    # Validate individual papers
                    validated_papers = []
                    for paper in raw_result["results"]:
                        if not isinstance(paper, dict):
                            continue
                        
                        # Clean corrupted Unicode
                        if "title" in paper and isinstance(paper["title"], str):
                            # Remove control characters
                            paper["title"] = ''.join(char for char in paper["title"] if ord(char) >= 32)
                        
                        # Ensure required fields exist
                        if "id" in paper or "title" in paper:
                            validated_papers.append(paper)
                    
                    return {"success": True, "papers": validated_papers}
                    
                except json.JSONDecodeError as e:
                    return {"error": f"JSON decode error: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error: {str(e)}"}
            
            # Test validation
            result = await safe_search_with_validation("test query")
            
            # Should handle corruption gracefully
            if i == 0:  # JSON error
                assert "error" in result
                assert "JSON decode error" in result["error"]
            elif i in [1, 2, 3]:  # Structure errors
                assert "error" in result
            elif i == 4:  # Unicode corruption
                assert "success" in result
                assert len(result["papers"]) == 1
                # Unicode should be cleaned
                assert "\u0000" not in result["papers"][0]["title"]


class TestSearchStrategyTesting:
    """Test search algorithms against known academic datasets."""
    
    @pytest.mark.asyncio
    async def test_academic_search_algorithm_validation(
        self,
        mock_vector_rm,
        academic_test_data
    ):
        """Test search algorithm effectiveness with academic datasets."""
        # Create test dataset with known relevant papers
        test_dataset = {
            "Machine Learning": [
                {
                    "id": "ml_001",
                    "title": "Deep Learning for Image Recognition",
                    "abstract": "This paper presents a comprehensive study of deep learning techniques for image recognition tasks.",
                    "keywords": ["deep learning", "image recognition", "neural networks", "computer vision"],
                    "relevance_score": 0.95
                },
                {
                    "id": "ml_002", 
                    "title": "Convolutional Neural Networks in Medical Imaging",
                    "abstract": "We explore the application of CNNs in medical image analysis and diagnostic procedures.",
                    "keywords": ["CNN", "medical imaging", "deep learning", "diagnostics"],
                    "relevance_score": 0.88
                },
                {
                    "id": "ml_003",
                    "title": "Transfer Learning in Natural Language Processing",
                    "abstract": "This work investigates transfer learning approaches for NLP tasks and language understanding.",
                    "keywords": ["transfer learning", "NLP", "language models", "BERT"],
                    "relevance_score": 0.72
                }
            ],
            "Climate Science": [
                {
                    "id": "climate_001",
                    "title": "Climate Change Impacts on Arctic Ice",
                    "abstract": "Analysis of long-term trends in Arctic ice coverage and their implications for global climate.",
                    "keywords": ["climate change", "Arctic ice", "global warming", "environmental science"],
                    "relevance_score": 0.93
                },
                {
                    "id": "climate_002",
                    "title": "Carbon Sequestration Technologies",
                    "abstract": "Review of current carbon capture and storage technologies for climate mitigation.",
                    "keywords": ["carbon sequestration", "climate mitigation", "CCS technology"],
                    "relevance_score": 0.89
                }
            ]
        }
        
        # Test search algorithm
        class AcademicSearchAlgorithm:
            def __init__(self, dataset):
                self.dataset = dataset
                
            async def search(self, query: str, discipline: str = None, top_k: int = 10):
                """Search algorithm with keyword matching and semantic similarity."""
                results = []
                query_terms = set(query.lower().split())
                
                # Search in specific discipline or all disciplines
                search_disciplines = [discipline] if discipline else self.dataset.keys()
                
                for disc in search_disciplines:
                    if disc not in self.dataset:
                        continue
                        
                    for paper in self.dataset[disc]:
                        # Calculate similarity score
                        score = self._calculate_similarity(query_terms, paper)
                        
                        if score > 0.1:  # Minimum relevance threshold
                            results.append({
                                **paper,
                                "search_score": score,
                                "discipline": disc
                            })
                
                # Sort by search score and return top_k
                results.sort(key=lambda x: x["search_score"], reverse=True)
                return results[:top_k]
            
            def _calculate_similarity(self, query_terms: set, paper: dict) -> float:
                """Calculate similarity between query and paper."""
                # Combine title, abstract, and keywords for matching
                paper_text = " ".join([
                    paper.get("title", ""),
                    paper.get("abstract", ""),
                    " ".join(paper.get("keywords", []))
                ]).lower()
                
                paper_words = set(paper_text.split())
                
                # Calculate Jaccard similarity
                intersection = len(query_terms.intersection(paper_words))
                union = len(query_terms.union(paper_words))
                
                jaccard_score = intersection / union if union > 0 else 0
                
                # Boost score based on relevance_score
                boosted_score = jaccard_score * paper.get("relevance_score", 1.0)
                
                return boosted_score
        
        search_algorithm = AcademicSearchAlgorithm(test_dataset)
        
        # Test search scenarios
        search_scenarios = [
            {
                "query": "deep learning image recognition",
                "discipline": "Machine Learning",
                "expected_top_result": "ml_001",
                "min_results": 2
            },
            {
                "query": "climate change arctic",
                "discipline": "Climate Science", 
                "expected_top_result": "climate_001",
                "min_results": 1
            },
            {
                "query": "neural networks medical",
                "discipline": None,  # Cross-disciplinary search
                "expected_disciplines": ["Machine Learning"],
                "min_results": 1
            }
        ]
        
        for scenario in search_scenarios:
            results = await search_algorithm.search(
                scenario["query"],
                scenario.get("discipline"),
                top_k=10
            )
            
            # Validate search results
            assert len(results) >= scenario["min_results"], f"Insufficient results for query: {scenario['query']}"
            
            if "expected_top_result" in scenario:
                assert results[0]["id"] == scenario["expected_top_result"], f"Incorrect top result for: {scenario['query']}"
            
            if "expected_disciplines" in scenario:
                result_disciplines = {r["discipline"] for r in results}
                expected_disciplines = set(scenario["expected_disciplines"])
                assert result_disciplines.intersection(expected_disciplines), f"Missing expected disciplines for: {scenario['query']}"
            
            # Validate search score ordering
            search_scores = [r["search_score"] for r in results]
            assert search_scores == sorted(search_scores, reverse=True), "Results not properly ranked by search score"
            
            # Validate relevance threshold
            for result in results:
                assert result["search_score"] > 0.1, "Result below minimum relevance threshold"
    
    @pytest.mark.asyncio
    async def test_citation_network_analysis(
        self,
        mock_crossref_service
    ):
        """Test citation relationship extraction and analysis accuracy."""
        # Mock citation network data
        citation_network = {
            "10.1000/paper_a": {
                "title": "Foundational Machine Learning Concepts",
                "year": 2018,
                "cites": ["10.1000/paper_b", "10.1000/paper_c"],
                "cited_by": ["10.1000/paper_d", "10.1000/paper_e"],
                "citation_count": 245
            },
            "10.1000/paper_b": {
                "title": "Deep Neural Network Architectures", 
                "year": 2017,
                "cites": ["10.1000/paper_c"],
                "cited_by": ["10.1000/paper_a", "10.1000/paper_d"],
                "citation_count": 156
            },
            "10.1000/paper_c": {
                "title": "Statistical Learning Theory",
                "year": 2015,
                "cites": [],
                "cited_by": ["10.1000/paper_a", "10.1000/paper_b", "10.1000/paper_d"],
                "citation_count": 523
            },
            "10.1000/paper_d": {
                "title": "Applications of ML in Healthcare",
                "year": 2020,
                "cites": ["10.1000/paper_a", "10.1000/paper_b", "10.1000/paper_c"],
                "cited_by": ["10.1000/paper_e"],
                "citation_count": 89
            },
            "10.1000/paper_e": {
                "title": "Future Directions in AI Research",
                "year": 2021,
                "cites": ["10.1000/paper_a", "10.1000/paper_d"],
                "cited_by": [],
                "citation_count": 34
            }
        }
        
        # Mock citation network analyzer
        class CitationNetworkAnalyzer:
            def __init__(self, network_data):
                self.network = network_data
            
            async def analyze_citation_patterns(self, paper_doi: str):
                """Analyze citation patterns for a given paper."""
                if paper_doi not in self.network:
                    return {"error": "Paper not found"}
                
                paper = self.network[paper_doi]
                
                analysis = {
                    "paper_doi": paper_doi,
                    "direct_citations": len(paper["cites"]),
                    "direct_citing_papers": len(paper["cited_by"]),
                    "total_citation_count": paper["citation_count"],
                    "citation_analysis": {}
                }
                
                # Analyze citation influence
                analysis["citation_analysis"]["influence_score"] = self._calculate_influence_score(paper_doi)
                analysis["citation_analysis"]["authority_score"] = self._calculate_authority_score(paper_doi)
                analysis["citation_analysis"]["hub_score"] = self._calculate_hub_score(paper_doi)
                
                # Find citation clusters
                analysis["citation_analysis"]["citation_clusters"] = self._find_citation_clusters(paper_doi)
                
                return analysis
            
            def _calculate_influence_score(self, paper_doi: str) -> float:
                """Calculate paper's influence based on citation propagation."""
                paper = self.network[paper_doi]
                
                # Direct citations
                direct_score = len(paper["cited_by"]) * 1.0
                
                # Indirect citations (papers citing papers that cite this one)
                indirect_score = 0
                for citing_paper in paper["cited_by"]:
                    if citing_paper in self.network:
                        indirect_score += len(self.network[citing_paper]["cited_by"]) * 0.5
                
                return direct_score + indirect_score
            
            def _calculate_authority_score(self, paper_doi: str) -> float:
                """Calculate authority score (cited by important papers)."""
                paper = self.network[paper_doi]
                authority_score = 0
                
                for citing_paper in paper["cited_by"]:
                    if citing_paper in self.network:
                        citing_paper_citations = self.network[citing_paper]["citation_count"]
                        authority_score += citing_paper_citations * 0.01  # Normalize
                
                return authority_score
            
            def _calculate_hub_score(self, paper_doi: str) -> float:
                """Calculate hub score (cites important papers)."""
                paper = self.network[paper_doi]
                hub_score = 0
                
                for cited_paper in paper["cites"]:
                    if cited_paper in self.network:
                        cited_paper_citations = self.network[cited_paper]["citation_count"]
                        hub_score += cited_paper_citations * 0.01  # Normalize
                
                return hub_score
            
            def _find_citation_clusters(self, paper_doi: str) -> List[List[str]]:
                """Find citation clusters (groups of papers that cite each other)."""
                paper = self.network[paper_doi]
                
                # Find papers in the citation neighborhood
                neighborhood = set([paper_doi])
                neighborhood.update(paper["cites"])
                neighborhood.update(paper["cited_by"])
                
                # Look for clusters within neighborhood
                clusters = []
                for paper_id in neighborhood:
                    if paper_id not in self.network:
                        continue
                        
                    cluster_papers = [paper_id]
                    neighbor_paper = self.network[paper_id]
                    
                    # Find papers that this paper cites and that cite it back
                    for cited in neighbor_paper["cites"]:
                        if cited in neighborhood and cited in self.network:
                            if paper_id in self.network[cited]["cited_by"]:
                                cluster_papers.append(cited)
                    
                    if len(cluster_papers) > 1:
                        clusters.append(cluster_papers)
                
                return clusters
        
        analyzer = CitationNetworkAnalyzer(citation_network)
        
        # Test citation analysis for each paper
        for paper_doi in citation_network.keys():
            analysis = await analyzer.analyze_citation_patterns(paper_doi)
            
            # Validate analysis structure
            assert "paper_doi" in analysis
            assert "direct_citations" in analysis
            assert "direct_citing_papers" in analysis
            assert "citation_analysis" in analysis
            
            # Validate citation counts
            expected_paper = citation_network[paper_doi]
            assert analysis["direct_citations"] == len(expected_paper["cites"])
            assert analysis["direct_citing_papers"] == len(expected_paper["cited_by"])
            
            # Validate analysis scores
            citation_analysis = analysis["citation_analysis"]
            assert "influence_score" in citation_analysis
            assert "authority_score" in citation_analysis
            assert "hub_score" in citation_analysis
            
            # Scores should be non-negative
            assert citation_analysis["influence_score"] >= 0
            assert citation_analysis["authority_score"] >= 0
            assert citation_analysis["hub_score"] >= 0
        
        # Test specific papers
        
        # Paper C should have high authority (widely cited foundational work)
        paper_c_analysis = await analyzer.analyze_citation_patterns("10.1000/paper_c")
        paper_a_analysis = await analyzer.analyze_citation_patterns("10.1000/paper_a")
        
        # Paper C (2015, foundational) should have higher authority than Paper A
        assert paper_c_analysis["citation_analysis"]["authority_score"] > paper_a_analysis["citation_analysis"]["authority_score"]
        
        # Paper D should have high hub score (cites many important papers)
        paper_d_analysis = await analyzer.analyze_citation_patterns("10.1000/paper_d")
        paper_e_analysis = await analyzer.analyze_citation_patterns("10.1000/paper_e")
        
        # Paper D cites more papers, so should have higher hub score
        assert paper_d_analysis["citation_analysis"]["hub_score"] > paper_e_analysis["citation_analysis"]["hub_score"]