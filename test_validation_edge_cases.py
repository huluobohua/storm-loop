"""Test edge cases for the perfected warm_cache validation."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from knowledge_storm.services.academic_source_service import AcademicSourceService


@pytest.mark.asyncio
async def test_edge_case_validations():
    """Test edge cases for input validation."""
    
    with patch.multiple(
        'knowledge_storm.services.academic_source_service',
        CacheService=Mock(),
        CircuitBreaker=Mock(),
        CacheKeyBuilder=Mock()
    ):
        service = AcademicSourceService()
        service.search_combined = AsyncMock(return_value=[])
        
        # Test parallel=0 (should fail)
        with pytest.raises(ValueError, match="parallel parameter must be a positive integer"):
            await service.warm_cache(['test'], parallel=0)
        
        # Test parallel=-1 (should fail)
        with pytest.raises(ValueError, match="parallel parameter must be a positive integer"):
            await service.warm_cache(['test'], parallel=-1)
        
        # Test parallel="invalid" (should fail)
        with pytest.raises(ValueError, match="parallel parameter must be a positive integer"):
            await service.warm_cache(['test'], parallel="invalid")  # type: ignore
        
        # Test parallel=None (should use default)
        await service.warm_cache(['test1', 'test2'], parallel=None)
        
        # Test parallel=1 (minimum valid)
        await service.warm_cache(['test'], parallel=1)
        
        # Test parallel=100 (maximum without warning)
        await service.warm_cache(['test'], parallel=100)
        
        print("✅ All edge case validations passed!")


if __name__ == "__main__":
    asyncio.run(test_edge_case_validations())