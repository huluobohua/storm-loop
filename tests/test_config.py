"""
Tests for STORM-Loop configuration management
"""
import pytest
import os
from storm_loop.config import STORMLoopConfig, OperationMode, get_config, update_config


class TestSTORMLoopConfig:
    """Test STORMLoopConfig class"""

    def test_default_config(self):
        """Test default configuration values"""
        config = STORMLoopConfig()
        
        assert config.mode == OperationMode.HYBRID
        assert config.redis_host == "localhost"
        assert config.redis_port == 6379
        assert config.redis_db == 0
        assert config.enable_openalex is True
        assert config.enable_crossref is True
        assert config.max_concurrent_requests == 10
        assert config.request_timeout == 30
        assert config.cache_ttl == 3600
        assert config.min_source_quality_score == 0.7
        assert config.enable_citation_verification is True
        assert config.max_agent_workers == 5
        assert config.database_url == "sqlite:///storm_loop.db"
        assert config.log_level == "INFO"

    def test_operation_modes(self):
        """Test different operation modes"""
        # Academic mode
        config = STORMLoopConfig(mode=OperationMode.ACADEMIC)
        assert config.mode == OperationMode.ACADEMIC
        
        # Wikipedia mode
        config = STORMLoopConfig(mode=OperationMode.WIKIPEDIA)
        assert config.mode == OperationMode.WIKIPEDIA
        
        # Hybrid mode
        config = STORMLoopConfig(mode=OperationMode.HYBRID)
        assert config.mode == OperationMode.HYBRID

    def test_environment_variables(self, monkeypatch):
        """Test configuration from environment variables"""
        # Set environment variables
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        config = STORMLoopConfig()
        
        assert config.redis_host == "redis.example.com"
        assert config.redis_port == 6380
        assert config.log_level == "DEBUG"
        assert config.openai_api_key == "test-key"

    def test_custom_values(self):
        """Test configuration with custom values"""
        config = STORMLoopConfig(
            mode=OperationMode.ACADEMIC,
            redis_host="custom-redis",
            redis_port=6380,
            max_concurrent_requests=20,
            min_source_quality_score=0.8,
            enable_citation_verification=False,
        )
        
        assert config.mode == OperationMode.ACADEMIC
        assert config.redis_host == "custom-redis"
        assert config.redis_port == 6380
        assert config.max_concurrent_requests == 20
        assert config.min_source_quality_score == 0.8
        assert config.enable_citation_verification is False


class TestConfigFunctions:
    """Test configuration utility functions"""

    def test_get_config(self):
        """Test get_config function"""
        config = get_config()
        assert isinstance(config, STORMLoopConfig)

    def test_update_config(self):
        """Test update_config function"""
        original_mode = get_config().mode
        
        # Update configuration
        update_config(mode=OperationMode.ACADEMIC, redis_port=6380)
        
        config = get_config()
        assert config.mode == OperationMode.ACADEMIC
        assert config.redis_port == 6380
        
        # Reset to original
        update_config(mode=original_mode, redis_port=6379)

    def test_update_config_invalid_key(self):
        """Test update_config with invalid key"""
        with pytest.raises(ValueError, match="Unknown configuration key"):
            update_config(invalid_key="value")