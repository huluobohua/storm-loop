"""
Base database integration tester interface.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..models import ValidationResult


@dataclass
class DatabaseTestContext:
    """Context for database integration testing."""
    
    database_name: str
    test_type: str  # "connectivity", "search", "retrieval", "performance"
    timeout_seconds: Optional[float] = None
    retry_attempts: Optional[int] = None
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


@dataclass
class DatabaseMetrics:
    """Metrics collected during database testing."""
    
    response_time: float
    success_rate: float
    error_rate: float
    records_found: Optional[int] = None
    records_processed: Optional[int] = None
    api_calls_made: Optional[int] = None
    data_quality_score: Optional[float] = None
    custom_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


class BaseDatabaseIntegrationTester(ABC):
    """
    Base class for all database integration testers.
    
    Provides common functionality for testing academic database integrations.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        database_url: str,
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.database_url = database_url
        self.version = version
        self.config = config or {}
        self._initialized = False
        self._connection = None
    
    async def initialize(self) -> None:
        """Initialize the database integration tester."""
        if not self._initialized:
            await self._initialize_tester()
            self._initialized = True
    
    @abstractmethod
    async def _initialize_tester(self) -> None:
        """Tester-specific initialization logic."""
        pass
    
    @abstractmethod
    async def test_integration(
        self,
        research_output: Any,
        context: Optional[DatabaseTestContext] = None,
        **kwargs: Any
    ) -> Union[ValidationResult, List[ValidationResult]]:
        """
        Test database integration with research output.
        
        Args:
            research_output: The research output to test against
            context: Additional context for testing
            **kwargs: Additional test parameters
            
        Returns:
            ValidationResult or list of ValidationResults
        """
        pass
    
    async def test_connectivity(self) -> ValidationResult:
        """Test basic database connectivity."""
        start_time = time.time()
        
        try:
            await self.initialize()
            connection_successful = await self._test_connection()
            response_time = time.time() - start_time
            
            if connection_successful:
                status = "passed"
                score = 1.0
                details = {"connection_established": True, "response_time": response_time}
            else:
                status = "failed"
                score = 0.0
                details = {"connection_established": False, "response_time": response_time}
            
            metrics = DatabaseMetrics(
                response_time=response_time,
                success_rate=1.0 if connection_successful else 0.0,
                error_rate=0.0 if connection_successful else 1.0,
                api_calls_made=1
            )
            
            return self._create_result(
                test_name="database_connectivity",
                status=status,
                score=score,
                details=details,
                metrics=metrics
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            metrics = DatabaseMetrics(
                response_time=response_time,
                success_rate=0.0,
                error_rate=1.0,
                api_calls_made=1
            )
            
            return self._create_result(
                test_name="database_connectivity",
                status="failed",
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_time": response_time
                },
                metrics=metrics
            )
    
    async def test_search_functionality(
        self, 
        search_terms: List[str],
        expected_min_results: int = 1
    ) -> ValidationResult:
        """Test database search functionality."""
        search_results = []
        total_response_time = 0.0
        successful_searches = 0
        
        for term in search_terms:
            start_time = time.time()
            
            try:
                results = await self._perform_search(term)
                response_time = time.time() - start_time
                total_response_time += response_time
                
                search_results.append({
                    "term": term,
                    "results_count": len(results) if results else 0,
                    "response_time": response_time,
                    "success": True
                })
                
                if results and len(results) >= expected_min_results:
                    successful_searches += 1
                    
            except Exception as e:
                response_time = time.time() - start_time
                total_response_time += response_time
                
                search_results.append({
                    "term": term,
                    "results_count": 0,
                    "response_time": response_time,
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate metrics
        success_rate = successful_searches / len(search_terms) if search_terms else 0.0
        avg_response_time = total_response_time / len(search_terms) if search_terms else 0.0
        total_results = sum(result["results_count"] for result in search_results)
        
        # Determine overall status
        status = "passed" if success_rate >= 0.8 else "failed"
        
        metrics = DatabaseMetrics(
            response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=1.0 - success_rate,
            records_found=total_results,
            api_calls_made=len(search_terms)
        )
        
        return self._create_result(
            test_name="search_functionality",
            status=status,
            score=success_rate,
            details={
                "search_results": search_results,
                "total_searches": len(search_terms),
                "successful_searches": successful_searches,
                "total_results_found": total_results,
                "avg_response_time": avg_response_time,
                "expected_min_results": expected_min_results
            },
            metrics=metrics
        )
    
    async def test_data_quality(
        self, 
        sample_size: int = 10
    ) -> ValidationResult:
        """Test quality of data returned from database."""
        
        try:
            # Get sample data
            sample_data = await self._get_sample_data(sample_size)
            
            if not sample_data:
                return self._create_result(
                    test_name="data_quality",
                    status="failed",
                    score=0.0,
                    details={"error": "No sample data retrieved"}
                )
            
            # Analyze data quality
            quality_metrics = await self._analyze_data_quality(sample_data)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(quality_metrics)
            
            status = "passed" if quality_score >= 0.7 else "failed"
            
            metrics = DatabaseMetrics(
                response_time=quality_metrics.get("analysis_time", 0.0),
                success_rate=1.0,
                error_rate=0.0,
                records_processed=len(sample_data),
                data_quality_score=quality_score,
                custom_metrics=quality_metrics
            )
            
            return self._create_result(
                test_name="data_quality",
                status=status,
                score=quality_score,
                details={
                    "sample_size": len(sample_data),
                    "quality_metrics": quality_metrics,
                    "quality_score": quality_score,
                    "quality_breakdown": self._get_quality_breakdown(quality_metrics)
                },
                metrics=metrics
            )
            
        except Exception as e:
            return self._create_result(
                test_name="data_quality",
                status="failed",
                score=0.0,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def test_performance_under_load(
        self, 
        concurrent_requests: int = 5,
        requests_per_client: int = 10
    ) -> ValidationResult:
        """Test database performance under concurrent load."""
        
        async def client_workload(client_id: int) -> Dict[str, Any]:
            """Simulate workload for a single client."""
            client_results = []
            client_start = time.time()
            
            for request_id in range(requests_per_client):
                request_start = time.time()
                
                try:
                    # Perform a search operation
                    results = await self._perform_search(f"test query {client_id}_{request_id}")
                    request_time = time.time() - request_start
                    
                    client_results.append({
                        "request_id": request_id,
                        "success": True,
                        "response_time": request_time,
                        "results_count": len(results) if results else 0
                    })
                    
                except Exception as e:
                    request_time = time.time() - request_start
                    client_results.append({
                        "request_id": request_id,
                        "success": False,
                        "response_time": request_time,
                        "error": str(e)
                    })
            
            client_total_time = time.time() - client_start
            return {
                "client_id": client_id,
                "results": client_results,
                "total_time": client_total_time
            }
        
        # Run concurrent clients
        start_time = time.time()
        client_tasks = [
            asyncio.create_task(client_workload(i)) 
            for i in range(concurrent_requests)
        ]
        
        client_results = await asyncio.gather(*client_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze performance results
        successful_clients = 0
        total_requests = 0
        successful_requests = 0
        response_times = []
        
        for result in client_results:
            if not isinstance(result, Exception):
                total_requests += len(result["results"])
                client_successful = sum(1 for r in result["results"] if r["success"])
                successful_requests += client_successful
                
                if client_successful >= requests_per_client * 0.8:  # 80% success rate
                    successful_clients += 1
                
                response_times.extend([r["response_time"] for r in result["results"]])
        
        # Calculate metrics
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        client_success_rate = successful_clients / concurrent_requests if concurrent_requests > 0 else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        throughput = total_requests / total_time if total_time > 0 else 0.0
        
        # Determine status
        status = "passed" if success_rate >= 0.8 and client_success_rate >= 0.8 else "failed"
        
        metrics = DatabaseMetrics(
            response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=1.0 - success_rate,
            api_calls_made=total_requests,
            custom_metrics={
                "throughput": throughput,
                "client_success_rate": client_success_rate,
                "concurrent_clients": concurrent_requests
            }
        )
        
        return self._create_result(
            test_name="performance_under_load",
            status=status,
            score=(success_rate + client_success_rate) / 2,
            details={
                "concurrent_requests": concurrent_requests,
                "requests_per_client": requests_per_client,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "successful_clients": successful_clients,
                "success_rate": success_rate,
                "client_success_rate": client_success_rate,
                "avg_response_time": avg_response_time,
                "throughput": throughput,
                "total_test_time": total_time
            },
            metrics=metrics
        )
    
    @abstractmethod
    async def _test_connection(self) -> bool:
        """Test database connection. Return True if successful."""
        pass
    
    @abstractmethod
    async def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a search query and return results."""
        pass
    
    @abstractmethod
    async def _get_sample_data(self, sample_size: int) -> List[Dict[str, Any]]:
        """Get sample data for quality analysis."""
        pass
    
    async def _analyze_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality of sample data."""
        start_time = time.time()
        
        total_records = len(data)
        if total_records == 0:
            return {"analysis_time": time.time() - start_time}
        
        # Common quality checks
        completeness_scores = []
        required_fields = ["title", "authors", "year"]  # Common academic fields
        
        for record in data:
            complete_fields = sum(1 for field in required_fields if field in record and record[field])
            completeness = complete_fields / len(required_fields)
            completeness_scores.append(completeness)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        
        # Check for duplicates
        unique_records = len(set(str(record) for record in data))
        uniqueness_score = unique_records / total_records
        
        # Check data freshness (if year field exists)
        current_year = 2024
        recent_records = sum(
            1 for record in data 
            if "year" in record and isinstance(record["year"], int) and record["year"] >= current_year - 5
        )
        recency_score = recent_records / total_records if total_records > 0 else 0.0
        
        analysis_time = time.time() - start_time
        
        return {
            "completeness_score": avg_completeness,
            "uniqueness_score": uniqueness_score,
            "recency_score": recency_score,
            "total_records_analyzed": total_records,
            "analysis_time": analysis_time,
            "individual_completeness": completeness_scores
        }
    
    def _calculate_quality_score(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score from metrics."""
        weights = {
            "completeness_score": 0.4,
            "uniqueness_score": 0.3,
            "recency_score": 0.3
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in quality_metrics:
                total_score += quality_metrics[metric] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _get_quality_breakdown(self, quality_metrics: Dict[str, Any]) -> Dict[str, str]:
        """Get human-readable quality breakdown."""
        breakdown = {}
        
        completeness = quality_metrics.get("completeness_score", 0.0)
        if completeness >= 0.9:
            breakdown["completeness"] = "Excellent"
        elif completeness >= 0.7:
            breakdown["completeness"] = "Good" 
        elif completeness >= 0.5:
            breakdown["completeness"] = "Fair"
        else:
            breakdown["completeness"] = "Poor"
        
        uniqueness = quality_metrics.get("uniqueness_score", 0.0)
        if uniqueness >= 0.95:
            breakdown["uniqueness"] = "Excellent"
        elif uniqueness >= 0.8:
            breakdown["uniqueness"] = "Good"
        elif uniqueness >= 0.6:
            breakdown["uniqueness"] = "Fair"
        else:
            breakdown["uniqueness"] = "Poor"
        
        recency = quality_metrics.get("recency_score", 0.0)
        if recency >= 0.7:
            breakdown["recency"] = "Excellent"
        elif recency >= 0.5:
            breakdown["recency"] = "Good"
        elif recency >= 0.3:
            breakdown["recency"] = "Fair"
        else:
            breakdown["recency"] = "Poor"
        
        return breakdown
    
    def _create_result(
        self,
        test_name: str,
        status: str,
        score: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metrics: Optional[DatabaseMetrics] = None,
    ) -> ValidationResult:
        """Create a database integration test result."""
        result_metadata = metadata or {}
        result_metadata["database_name"] = self.name
        result_metadata["database_url"] = self.database_url
        
        if metrics:
            result_metadata["database_metrics"] = metrics.__dict__
        
        return ValidationResult(
            validator_name=self.name,
            test_name=test_name,
            status=status,
            score=score,
            details=details or {},
            metadata=result_metadata,
        )
    
    async def cleanup(self) -> None:
        """Cleanup database resources."""
        if self._connection:
            try:
                await self._close_connection()
            except Exception:
                pass  # Ignore cleanup errors
            finally:
                self._connection = None
    
    async def _close_connection(self) -> None:
        """Close database connection (implement in subclasses if needed)."""
        pass
    
    def get_tester_info(self) -> Dict[str, Any]:
        """Get information about this database tester."""
        return {
            "name": self.name,
            "description": self.description,
            "database_url": self.database_url,
            "version": self.version,
            "config": self.config,
            "initialized": self._initialized,
        }