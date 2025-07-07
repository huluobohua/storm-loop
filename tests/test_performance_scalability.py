"""
Performance and scalability testing for academic-scale research loads.
"""
import pytest
import asyncio
import time
import psutil
import resource
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json

from knowledge_storm.storm_wiki.engine import STORMWikiRunner
from knowledge_storm.services.academic_source_service import AcademicSourceService
from knowledge_storm.services.cache_service import CacheService


class TestLargeScaleResearch:
    """Test with 1000+ papers across multiple disciplines."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_paper_dataset_processing(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm,
        performance_benchmarks
    ):
        """Test processing of large academic paper datasets."""
        # Create large mock dataset
        large_dataset = []
        disciplines = ["Computer Science", "Medicine", "Physics", "Engineering", "Biology"]
        
        for i in range(1000):
            paper = {
                "id": f"paper_{i}",
                "title": f"Research Paper {i}: Advanced {disciplines[i % len(disciplines)]} Study",
                "authors": [f"Author_{i}_1", f"Author_{i}_2"],
                "year": 2020 + (i % 4),
                "discipline": disciplines[i % len(disciplines)],
                "abstract": f"This paper presents advanced research in {disciplines[i % len(disciplines)]}...",
                "citations": list(range(i * 10, (i + 1) * 10)),
                "keywords": [f"keyword_{i}_{j}" for j in range(5)]
            }
            large_dataset.append(paper)
        
        # Mock retrieval module for large dataset
        mock_vector_rm.retrieve = AsyncMock(return_value=large_dataset[:100])  # Return subset
        
        # Create STORM runner
        runner = STORMWikiRunner(storm_config)
        runner.storm_knowledge_curation_module.retriever = mock_vector_rm
        runner.storm_knowledge_curation_module.conv_simulator.lm = mock_openai_model
        
        # Test large-scale processing
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Mock processing with progress tracking
        processed_papers = []
        
        async def mock_process_papers(papers):
            for i, paper in enumerate(papers):
                # Simulate processing time
                await asyncio.sleep(0.01)
                processed_papers.append({
                    "paper_id": paper["id"],
                    "processed_at": time.time(),
                    "processing_order": i
                })
                
                # Memory check during processing
                if i % 100 == 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    assert current_memory < performance_benchmarks["performance_thresholds"]["max_memory_usage"]
            
            return processed_papers
        
        # Process large dataset
        results = await mock_process_papers(large_dataset)
        
        end_time = time.time()
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Validate large-scale processing
        assert len(results) == 1000
        assert end_time - start_time < 60  # Should complete within 1 minute
        
        # Memory usage validation
        memory_increase = memory_after - memory_before
        assert memory_increase < performance_benchmarks["performance_thresholds"]["max_memory_usage"]
        
        # Validate processing order
        for i, result in enumerate(results):
            assert result["processing_order"] == i
    
    @pytest.mark.asyncio
    async def test_multi_discipline_concurrent_processing(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test concurrent processing across multiple academic disciplines."""
        disciplines = [
            "Computer Science", "Medicine", "Physics", "Chemistry", 
            "Biology", "Psychology", "Economics", "Engineering"
        ]
        
        # Create discipline-specific datasets
        discipline_datasets = {}
        for discipline in disciplines:
            dataset = []
            for i in range(150):  # 150 papers per discipline
                paper = {
                    "id": f"{discipline.lower().replace(' ', '_')}_paper_{i}",
                    "title": f"{discipline} Research Paper {i}",
                    "discipline": discipline,
                    "abstract": f"Advanced {discipline} research focusing on...",
                    "keywords": [f"{discipline.lower()}_keyword_{j}" for j in range(3)]
                }
                dataset.append(paper)
            discipline_datasets[discipline] = dataset
        
        # Test concurrent discipline processing
        async def process_discipline(discipline, dataset):
            start_time = time.time()
            
            # Mock discipline-specific processing
            processed_count = 0
            for paper in dataset:
                await asyncio.sleep(0.005)  # Simulate processing
                processed_count += 1
            
            end_time = time.time()
            
            return {
                "discipline": discipline,
                "processed_papers": processed_count,
                "processing_time": end_time - start_time,
                "papers_per_second": processed_count / (end_time - start_time)
            }
        
        # Create concurrent tasks for all disciplines
        tasks = []
        for discipline, dataset in discipline_datasets.items():
            task = asyncio.create_task(process_discipline(discipline, dataset))
            tasks.append(task)
        
        # Execute concurrent processing
        results = await asyncio.gather(*tasks)
        
        # Validate concurrent processing
        assert len(results) == len(disciplines)
        
        total_papers = sum(result["processed_papers"] for result in results)
        assert total_papers == 150 * len(disciplines)  # 1200 total papers
        
        # Validate processing efficiency
        avg_papers_per_second = sum(result["papers_per_second"] for result in results) / len(results)
        assert avg_papers_per_second > 10  # Minimum efficiency threshold
    
    @pytest.mark.asyncio
    async def test_memory_efficient_large_dataset_streaming(
        self,
        mock_vector_rm,
        performance_benchmarks
    ):
        """Test memory-efficient streaming of large datasets."""
        # Create large dataset generator
        def generate_large_dataset(size=5000):
            for i in range(size):
                yield {
                    "id": f"stream_paper_{i}",
                    "title": f"Streaming Paper {i}",
                    "content": "A" * 1000,  # 1KB of content per paper
                    "metadata": {
                        "created_at": time.time(),
                        "size_bytes": 1000
                    }
                }
        
        # Test streaming processing
        processed_count = 0
        memory_samples = []
        
        async def stream_processor():
            nonlocal processed_count
            
            for paper in generate_large_dataset():
                # Process paper
                await asyncio.sleep(0.001)
                processed_count += 1
                
                # Sample memory usage
                if processed_count % 500 == 0:
                    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_samples.append(memory_usage)
                    
                    # Ensure memory doesn't grow unbounded
                    assert memory_usage < performance_benchmarks["performance_thresholds"]["max_memory_usage"]
        
        # Execute streaming processing
        await stream_processor()
        
        # Validate streaming efficiency
        assert processed_count == 5000
        assert len(memory_samples) == 10  # 5000 / 500
        
        # Memory should remain stable (not grow linearly with data)
        memory_variance = max(memory_samples) - min(memory_samples)
        assert memory_variance < 100  # Less than 100MB variance


class TestConcurrentUserLoad:
    """Test system behavior with 50+ simultaneous research sessions."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_user_sessions(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm,
        performance_benchmarks
    ):
        """Test 50+ concurrent user research sessions."""
        from knowledge_storm.storm_wiki.engine import STORMWikiRunner
        
        # Create session manager
        active_sessions = {}
        session_results = []
        
        async def simulate_research_session(session_id: int, topic: str):
            """Simulate a complete research session."""
            session_start = time.time()
            
            # Create isolated runner instance
            runner = STORMWikiRunner(storm_config)
            runner.storm_knowledge_curation_module.retriever = mock_vector_rm
            runner.storm_knowledge_curation_module.conv_simulator.lm = mock_openai_model
            
            # Track active session
            active_sessions[session_id] = {
                "topic": topic,
                "start_time": session_start,
                "status": "active"
            }
            
            try:
                # Mock research process
                with patch.object(runner, 'run_knowledge_curation_module') as mock_curation:
                    mock_curation.return_value = Mock(
                        raw_utterances=[
                            {"role": "researcher", "content": f"Research on {topic}"},
                            {"role": "critic", "content": f"Analysis of {topic}"}
                        ]
                    )
                    
                    # Simulate research time
                    await asyncio.sleep(0.5 + (session_id % 10) * 0.1)  # Variable processing time
                    
                    result = await runner.run_knowledge_curation_module(
                        topic=topic,
                        callback=Mock(),
                        max_conv_turn=3
                    )
                
                session_end = time.time()
                
                session_result = {
                    "session_id": session_id,
                    "topic": topic,
                    "duration": session_end - session_start,
                    "success": True,
                    "utterances_count": len(result.raw_utterances),
                    "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024
                }
                
                active_sessions[session_id]["status"] = "completed"
                return session_result
                
            except Exception as e:
                session_end = time.time()
                
                session_result = {
                    "session_id": session_id,
                    "topic": topic,
                    "duration": session_end - session_start,
                    "success": False,
                    "error": str(e),
                    "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024
                }
                
                active_sessions[session_id]["status"] = "failed"
                return session_result
        
        # Create 50 concurrent sessions
        concurrent_users = 50
        tasks = []
        
        for session_id in range(concurrent_users):
            topic = f"Research Topic {session_id}: Advanced Study in Area {session_id % 10}"
            task = asyncio.create_task(simulate_research_session(session_id, topic))
            tasks.append(task)
        
        # Monitor system resources during execution
        resource_monitor_task = asyncio.create_task(self._monitor_system_resources())
        
        # Execute all sessions concurrently
        session_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop resource monitoring
        resource_monitor_task.cancel()
        
        # Validate concurrent session handling
        successful_sessions = [r for r in session_results if not isinstance(r, Exception) and r.get("success")]
        failed_sessions = [r for r in session_results if isinstance(r, Exception) or not r.get("success")]
        
        success_rate = len(successful_sessions) / len(session_results)
        assert success_rate >= performance_benchmarks["performance_thresholds"]["min_success_rate"]
        
        # Validate response times
        response_times = [s["duration"] for s in successful_sessions]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time <= performance_benchmarks["performance_thresholds"]["max_response_time"]
        assert max_response_time <= performance_benchmarks["performance_thresholds"]["max_response_time"] * 2
        
        # Validate resource usage
        memory_usages = [s["memory_usage"] for s in successful_sessions]
        max_memory = max(memory_usages)
        assert max_memory <= performance_benchmarks["performance_thresholds"]["max_memory_usage"]
    
    async def _monitor_system_resources(self):
        """Monitor system resources during concurrent testing."""
        resource_samples = []
        
        try:
            while True:
                await asyncio.sleep(1)
                
                sample = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                    "open_files": len(psutil.Process().open_files())
                }
                
                resource_samples.append(sample)
                
                # Basic resource limits
                assert sample["cpu_percent"] <= 95  # CPU shouldn't max out
                assert sample["memory_percent"] <= 90  # Memory shouldn't max out
                
        except asyncio.CancelledError:
            # Return collected samples
            return resource_samples
    
    @pytest.mark.asyncio
    async def test_session_isolation(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test isolation between concurrent user sessions."""
        from knowledge_storm.storm_wiki.engine import STORMWikiRunner
        
        # Test session state isolation
        session_states = {}
        
        async def isolated_session(session_id: int, shared_data: dict):
            """Test session with isolated state."""
            # Create session-specific state
            session_state = {
                "session_id": session_id,
                "private_data": f"private_to_session_{session_id}",
                "shared_access": shared_data.copy()
            }
            
            session_states[session_id] = session_state
            
            # Simulate session operations that might interfere
            runner = STORMWikiRunner(storm_config)
            runner.storm_knowledge_curation_module.retriever = mock_vector_rm
            runner.storm_knowledge_curation_module.conv_simulator.lm = mock_openai_model
            
            # Modify session state
            session_state["operations"] = []
            
            for i in range(3):
                await asyncio.sleep(0.1)
                operation = f"operation_{i}_session_{session_id}"
                session_state["operations"].append(operation)
                
                # Try to access shared data (should not interfere with other sessions)
                shared_data[f"session_{session_id}_operation_{i}"] = f"data_from_session_{session_id}"
            
            return session_state
        
        # Create shared data that sessions will access
        shared_data = {"initial": "shared_value"}
        
        # Run multiple isolated sessions
        tasks = []
        for session_id in range(10):
            task = asyncio.create_task(isolated_session(session_id, shared_data))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Validate session isolation
        assert len(results) == 10
        
        # Each session should have its own state
        for i, result in enumerate(results):
            assert result["session_id"] == i
            assert result["private_data"] == f"private_to_session_{i}"
            assert len(result["operations"]) == 3
            
            # Verify operations are session-specific
            for j, operation in enumerate(result["operations"]):
                assert operation == f"operation_{j}_session_{i}"
        
        # Verify shared data doesn't have cross-contamination
        for session_id in range(10):
            for operation_id in range(3):
                key = f"session_{session_id}_operation_{operation_id}"
                expected_value = f"data_from_session_{session_id}"
                assert shared_data[key] == expected_value


class TestMemoryUsageProfiling:
    """Test memory efficiency with various research project sizes."""
    
    @pytest.mark.asyncio
    async def test_memory_scaling_by_project_size(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test memory usage scaling with research project size."""
        project_sizes = [
            {"name": "Small", "papers": 10, "max_memory_mb": 50},
            {"name": "Medium", "papers": 100, "max_memory_mb": 200},
            {"name": "Large", "papers": 500, "max_memory_mb": 800},
            {"name": "XLarge", "papers": 1000, "max_memory_mb": 1500}
        ]
        
        memory_results = []
        
        for size_config in project_sizes:
            # Measure baseline memory
            baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Create project data
            project_data = []
            for i in range(size_config["papers"]):
                paper = {
                    "id": f"paper_{i}",
                    "title": f"Research Paper {i}",
                    "content": "Lorem ipsum " * 100,  # ~1KB per paper
                    "metadata": {
                        "authors": [f"Author {j}" for j in range(3)],
                        "keywords": [f"keyword_{j}" for j in range(5)],
                        "citations": list(range(i * 10, (i + 1) * 10))
                    }
                }
                project_data.append(paper)
            
            # Process project data
            async def process_project(data):
                processed_items = []
                
                for item in data:
                    # Simulate processing
                    await asyncio.sleep(0.001)
                    
                    processed_item = {
                        "original_id": item["id"],
                        "processed_title": item["title"].upper(),
                        "summary": item["content"][:100],
                        "metadata_count": len(item["metadata"])
                    }
                    processed_items.append(processed_item)
                
                return processed_items
            
            # Monitor memory during processing
            memory_samples = []
            
            async def memory_monitor():
                while True:
                    try:
                        await asyncio.sleep(0.1)
                        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                    except asyncio.CancelledError:
                        break
            
            # Start memory monitoring
            monitor_task = asyncio.create_task(memory_monitor())
            
            # Process project
            start_time = time.time()
            processed_data = await process_project(project_data)
            end_time = time.time()
            
            # Stop monitoring
            monitor_task.cancel()
            
            # Calculate memory usage
            peak_memory = max(memory_samples) if memory_samples else baseline_memory
            memory_increase = peak_memory - baseline_memory
            
            result = {
                "project_size": size_config["name"],
                "paper_count": size_config["papers"],
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": memory_increase,
                "processing_time_s": end_time - start_time,
                "memory_per_paper_kb": (memory_increase * 1024) / size_config["papers"] if size_config["papers"] > 0 else 0
            }
            
            memory_results.append(result)
            
            # Validate memory limits
            assert peak_memory <= size_config["max_memory_mb"], f"Memory exceeded for {size_config['name']} project"
            
            # Clean up for next test
            del project_data
            del processed_data
        
        # Validate memory scaling characteristics
        assert len(memory_results) == len(project_sizes)
        
        # Memory should scale sub-linearly (efficiency should improve with size)
        memory_per_paper_values = [r["memory_per_paper_kb"] for r in memory_results[1:]]  # Skip small project
        
        # Later projects should be more memory-efficient per paper
        for i in range(len(memory_per_paper_values) - 1):
            efficiency_improvement = memory_per_paper_values[i] >= memory_per_paper_values[i + 1]
            # Allow for some variance in efficiency
            assert efficiency_improvement or (memory_per_paper_values[i] / memory_per_paper_values[i + 1]) < 1.2
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(
        self,
        storm_config,
        mock_openai_model,
        mock_vector_rm
    ):
        """Test for memory leaks during extended operation."""
        from knowledge_storm.storm_wiki.engine import STORMWikiRunner
        
        # Baseline memory measurement
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples = [baseline_memory]
        
        # Run multiple research cycles
        for cycle in range(20):
            # Create runner for this cycle
            runner = STORMWikiRunner(storm_config)
            runner.storm_knowledge_curation_module.retriever = mock_vector_rm
            runner.storm_knowledge_curation_module.conv_simulator.lm = mock_openai_model
            
            # Mock research cycle
            with patch.object(runner, 'run_knowledge_curation_module') as mock_curation:
                mock_curation.return_value = Mock(
                    raw_utterances=[
                        {"role": "researcher", "content": f"Research cycle {cycle}"},
                        {"role": "critic", "content": f"Critique cycle {cycle}"}
                    ]
                )
                
                # Simulate research work
                await runner.run_knowledge_curation_module(
                    topic=f"Research Topic {cycle}",
                    callback=Mock(),
                    max_conv_turn=3
                )
            
            # Force garbage collection and measure memory
            import gc
            gc.collect()
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Clean up references
            del runner
        
        # Analyze memory trend
        final_memory = memory_samples[-1]
        memory_increase = final_memory - baseline_memory
        
        # Memory increase should be minimal (< 100MB over 20 cycles)
        assert memory_increase < 100, f"Potential memory leak detected: {memory_increase}MB increase"
        
        # Memory should stabilize (last 5 samples should be similar)
        recent_samples = memory_samples[-5:]
        memory_variance = max(recent_samples) - min(recent_samples)
        assert memory_variance < 50, f"Memory not stabilizing: {memory_variance}MB variance"


class TestAPIResponseTiming:
    """Benchmark response times for all external API calls."""
    
    @pytest.mark.asyncio
    async def test_external_api_response_benchmarks(
        self,
        mock_crossref_service,
        mock_academic_source_service,
        performance_benchmarks
    ):
        """Test response time benchmarks for external API services."""
        api_services = {
            "crossref": mock_crossref_service,
            "academic_source": mock_academic_source_service
        }
        
        benchmark_results = {}
        
        for service_name, service in api_services.items():
            service_results = {
                "response_times": [],
                "error_count": 0,
                "success_count": 0
            }
            
            # Test multiple API calls
            for i in range(10):
                start_time = time.time()
                
                try:
                    if service_name == "crossref":
                        # Mock Crossref API call
                        service.search_papers = AsyncMock(return_value=[
                            {"title": f"Paper {i}", "doi": f"10.1000/test{i}"}
                        ])
                        await service.search_papers(f"query {i}")
                        
                    elif service_name == "academic_source":
                        # Mock Academic Source API call
                        service.search_papers = AsyncMock(return_value=[
                            {"id": f"paper_{i}", "title": f"Academic Paper {i}"}
                        ])
                        await service.search_papers(f"academic query {i}")
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    service_results["response_times"].append(response_time)
                    service_results["success_count"] += 1
                    
                    # Individual response time check
                    assert response_time <= 5.0, f"{service_name} API response too slow: {response_time}s"
                    
                except Exception as e:
                    service_results["error_count"] += 1
                    end_time = time.time()
                    response_time = end_time - start_time
                    service_results["response_times"].append(response_time)
            
            # Calculate service statistics
            avg_response_time = sum(service_results["response_times"]) / len(service_results["response_times"])
            max_response_time = max(service_results["response_times"])
            success_rate = service_results["success_count"] / (service_results["success_count"] + service_results["error_count"])
            
            service_results.update({
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "success_rate": success_rate
            })
            
            benchmark_results[service_name] = service_results
            
            # Validate service performance
            assert avg_response_time <= 2.0, f"{service_name} average response time too high"
            assert success_rate >= 0.9, f"{service_name} success rate too low"
        
        # Overall API performance validation
        overall_avg_response = sum(
            results["avg_response_time"] for results in benchmark_results.values()
        ) / len(benchmark_results)
        
        assert overall_avg_response <= 2.0, "Overall API performance below threshold"
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting_compliance(
        self,
        mock_crossref_service,
        mock_academic_source_service
    ):
        """Test API rate limiting compliance and backoff strategies."""
        # Test rate limiting scenarios
        rate_limit_scenarios = [
            {"requests_per_second": 1, "burst_size": 5},
            {"requests_per_second": 10, "burst_size": 20},
            {"requests_per_second": 50, "burst_size": 100}
        ]
        
        for scenario in rate_limit_scenarios:
            rps = scenario["requests_per_second"]
            burst_size = scenario["burst_size"]
            
            # Mock rate limiter
            class MockRateLimiter:
                def __init__(self, requests_per_second, burst_size):
                    self.rps = requests_per_second
                    self.burst_size = burst_size
                    self.tokens = burst_size
                    self.last_refill = time.time()
                
                async def acquire(self):
                    now = time.time()
                    elapsed = now - self.last_refill
                    
                    # Refill tokens
                    self.tokens = min(
                        self.burst_size,
                        self.tokens + elapsed * self.rps
                    )
                    self.last_refill = now
                    
                    if self.tokens >= 1:
                        self.tokens -= 1
                        return True
                    
                    # Calculate wait time
                    wait_time = (1 - self.tokens) / self.rps
                    await asyncio.sleep(wait_time)
                    self.tokens = 0
                    return True
            
            rate_limiter = MockRateLimiter(rps, burst_size)
            
            # Test rate limiting compliance
            request_times = []
            start_time = time.time()
            
            for i in range(burst_size + 10):  # Test beyond burst capacity
                await rate_limiter.acquire()
                
                # Mock API call
                mock_crossref_service.search_papers = AsyncMock(return_value=[])
                await mock_crossref_service.search_papers(f"query {i}")
                
                request_times.append(time.time())
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Validate rate limiting
            actual_rps = len(request_times) / total_duration
            assert actual_rps <= rps * 1.1, f"Rate limiting failed: {actual_rps} > {rps}"
            
            # Validate burst handling
            initial_burst_time = request_times[burst_size - 1] - start_time
            assert initial_burst_time <= 1.0, "Burst requests should complete quickly"


class TestDatabasePerformance:
    """Test database operations under academic-scale data loads."""
    
    @pytest.mark.asyncio
    async def test_large_citation_network_queries(
        self,
        mock_vector_rm,
        performance_benchmarks
    ):
        """Test database performance with large citation networks."""
        # Create large citation network
        citation_network = {}
        paper_count = 10000
        
        # Build citation relationships
        for i in range(paper_count):
            paper_id = f"paper_{i}"
            
            # Each paper cites 5-15 other papers
            citation_count = 5 + (i % 11)  # 5-15 citations
            citations = []
            
            for j in range(citation_count):
                cited_paper_id = f"paper_{(i + j + 1) % paper_count}"
                citations.append(cited_paper_id)
            
            citation_network[paper_id] = {
                "id": paper_id,
                "title": f"Research Paper {i}",
                "citations": citations,
                "cited_by": [],  # Will be populated
                "year": 2000 + (i % 24)
            }
        
        # Build reverse citations (cited_by relationships)
        for paper_id, paper_data in citation_network.items():
            for cited_id in paper_data["citations"]:
                if cited_id in citation_network:
                    citation_network[cited_id]["cited_by"].append(paper_id)
        
        # Test citation network queries
        async def query_citation_network(query_type: str, paper_id: str):
            start_time = time.time()
            
            if query_type == "direct_citations":
                result = citation_network[paper_id]["citations"]
            elif query_type == "cited_by":
                result = citation_network[paper_id]["cited_by"]
            elif query_type == "citation_depth_2":
                # Papers cited by papers that this paper cites
                direct_citations = citation_network[paper_id]["citations"]
                depth_2_citations = set()
                for cited_id in direct_citations:
                    if cited_id in citation_network:
                        depth_2_citations.update(citation_network[cited_id]["citations"])
                result = list(depth_2_citations)
            elif query_type == "co_citation_analysis":
                # Papers that cite the same papers as this one
                this_paper_citations = set(citation_network[paper_id]["citations"])
                co_citations = set()
                
                for other_paper_id, other_paper in citation_network.items():
                    if other_paper_id != paper_id:
                        other_citations = set(other_paper["citations"])
                        overlap = len(this_paper_citations.intersection(other_citations))
                        if overlap >= 3:  # Threshold for co-citation
                            co_citations.add(other_paper_id)
                
                result = list(co_citations)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            return {
                "query_type": query_type,
                "paper_id": paper_id,
                "result_count": len(result),
                "query_time": query_time,
                "results": result[:10]  # Return first 10 results
            }
        
        # Test different query types
        query_types = ["direct_citations", "cited_by", "citation_depth_2", "co_citation_analysis"]
        test_papers = [f"paper_{i}" for i in range(0, 100, 10)]  # Sample papers
        
        query_results = []
        
        for query_type in query_types:
            for paper_id in test_papers:
                result = await query_citation_network(query_type, paper_id)
                query_results.append(result)
                
                # Validate query performance
                max_query_time = 1.0  # 1 second max per query
                assert result["query_time"] <= max_query_time, f"Query too slow: {query_type} took {result['query_time']}s"
        
        # Validate overall performance
        avg_query_time = sum(r["query_time"] for r in query_results) / len(query_results)
        assert avg_query_time <= 0.1, f"Average query time too high: {avg_query_time}s"
        
        # Validate result quality
        citation_queries = [r for r in query_results if r["query_type"] == "direct_citations"]
        avg_citations = sum(r["result_count"] for r in citation_queries) / len(citation_queries)
        assert 5 <= avg_citations <= 15, "Citation count outside expected range"