"""
Test-Driven Development: TokenTrackingLM Base Class Tests
RED Phase: These tests MUST fail initially and specify exact requirements
"""

import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor


class TestTokenTrackingLMTDD:
    """
    TDD-style tests for TokenTrackingLM base class
    These tests define the exact behavior expected from the abstraction
    """

    def test_token_tracking_initialization(self):
        """Test that TokenTrackingLM initializes with correct defaults"""
        from knowledge_storm.lm import TokenTrackingLM
        
        # This should fail initially - TokenTrackingLM is abstract
        with pytest.raises(TypeError):
            TokenTrackingLM(model="test-model")
    
    def test_token_tracking_concrete_implementation(self):
        """Test that concrete implementations can be created"""
        from knowledge_storm.lm import TokenTrackingLM
        
        class ConcreteTokenTracker(TokenTrackingLM):
            def basic_request(self, prompt, **kwargs):
                return {"choices": [{"text": "test"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            
            def __call__(self, prompt, **kwargs):
                return ["test response"]
        
        tracker = ConcreteTokenTracker(model="test-model")
        assert tracker.kwargs.get("model") == "test-model"
        assert tracker.prompt_tokens == 0
        assert tracker.completion_tokens == 0
        assert hasattr(tracker, '_token_usage_lock')
    
    def test_log_usage_tracks_tokens_correctly(self):
        """Test that log_usage correctly increments token counts"""
        from knowledge_storm.lm import TokenTrackingLM
        
        class ConcreteTokenTracker(TokenTrackingLM):
            def basic_request(self, prompt, **kwargs):
                return {"choices": [{"text": "test"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            
            def __call__(self, prompt, **kwargs):
                return ["test response"]
        
        tracker = ConcreteTokenTracker(model="test-model")
        
        # Test normal usage data
        response = {
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 8
            }
        }
        
        tracker.log_usage(response)
        assert tracker.prompt_tokens == 15
        assert tracker.completion_tokens == 8
        
        # Test cumulative usage
        tracker.log_usage(response)
        assert tracker.prompt_tokens == 30
        assert tracker.completion_tokens == 16
    
    def test_log_usage_handles_missing_usage_data(self):
        """Test that log_usage handles responses without usage data"""
        from knowledge_storm.lm import TokenTrackingLM
        
        class ConcreteTokenTracker(TokenTrackingLM):
            def basic_request(self, prompt, **kwargs):
                return {"choices": [{"text": "test"}]}
            
            def __call__(self, prompt, **kwargs):
                return ["test response"]
        
        tracker = ConcreteTokenTracker(model="test-model")
        
        # Test missing usage key
        response = {"choices": [{"text": "test"}]}
        tracker.log_usage(response)
        assert tracker.prompt_tokens == 0
        assert tracker.completion_tokens == 0
        
        # Test empty usage
        response = {"usage": {}}
        tracker.log_usage(response)
        assert tracker.prompt_tokens == 0
        assert tracker.completion_tokens == 0
    
    def test_get_usage_and_reset_thread_safety(self):
        """Test that get_usage_and_reset is thread-safe"""
        from knowledge_storm.lm import TokenTrackingLM
        
        class ConcreteTokenTracker(TokenTrackingLM):
            def basic_request(self, prompt, **kwargs):
                return {"choices": [{"text": "test"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            
            def __call__(self, prompt, **kwargs):
                return ["test response"]
        
        tracker = ConcreteTokenTracker(model="test-model")
        
        # Set initial token counts
        tracker.prompt_tokens = 100
        tracker.completion_tokens = 50
        
        # Test concurrent access
        results = []
        
        def concurrent_reset():
            result = tracker.get_usage_and_reset()
            results.append(result)
        
        def concurrent_log():
            tracker.log_usage({"usage": {"prompt_tokens": 10, "completion_tokens": 5}})
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            # Submit multiple reset operations
            for _ in range(5):
                futures.append(executor.submit(concurrent_reset))
            
            # Submit multiple log operations
            for _ in range(5):
                futures.append(executor.submit(concurrent_log))
            
            # Wait for all operations to complete
            for future in futures:
                future.result()
        
        # Only one reset should have gotten the original values
        original_values_found = False
        for result in results:
            if result["test-model"]["prompt_tokens"] == 100:
                assert not original_values_found, "Multiple resets got original values - race condition!"
                original_values_found = True
        
        assert original_values_found, "No reset got original values - something went wrong"
        
        # Final state should be consistent
        assert tracker.prompt_tokens >= 0
        assert tracker.completion_tokens >= 0
    
    def test_get_usage_and_reset_returns_correct_format(self):
        """Test that get_usage_and_reset returns the correct format"""
        from knowledge_storm.lm import TokenTrackingLM
        
        class ConcreteTokenTracker(TokenTrackingLM):
            def basic_request(self, prompt, **kwargs):
                return {"choices": [{"text": "test"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
            
            def __call__(self, prompt, **kwargs):
                return ["test response"]
        
        tracker = ConcreteTokenTracker(model="test-model")
        tracker.prompt_tokens = 25
        tracker.completion_tokens = 15
        
        usage = tracker.get_usage_and_reset()
        
        # Check format
        assert isinstance(usage, dict)
        assert "test-model" in usage
        assert "prompt_tokens" in usage["test-model"]
        assert "completion_tokens" in usage["test-model"]
        assert usage["test-model"]["prompt_tokens"] == 25
        assert usage["test-model"]["completion_tokens"] == 15
        
        # Check reset
        assert tracker.prompt_tokens == 0
        assert tracker.completion_tokens == 0
    
    def test_token_tracking_inheritance_works(self):
        """Test that classes inheriting from TokenTrackingLM work correctly"""
        from knowledge_storm.lm import OpenAIModel, DeepSeekModel
        
        # Test OpenAIModel still has token tracking
        with patch('dspy.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.basic_request.return_value = {
                "choices": [{"text": "test"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}
            }
            mock_openai.return_value = mock_client
            
            openai_model = OpenAIModel(model="gpt-3.5-turbo")
            assert hasattr(openai_model, 'log_usage')
            assert hasattr(openai_model, 'get_usage_and_reset')
            assert hasattr(openai_model, '_token_usage_lock')
        
        # Test DeepSeekModel still has token tracking
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}
            }
            mock_post.return_value = mock_response
            
            deepseek_model = DeepSeekModel(model="deepseek-chat", api_key="test")
            assert hasattr(deepseek_model, 'log_usage')
            assert hasattr(deepseek_model, 'get_usage_and_reset')
            assert hasattr(deepseek_model, '_token_usage_lock')


class TestDeepSeekModelInheritanceChanges:
    """Test that DeepSeekModel inheritance changes work correctly"""
    
    def test_deepseek_model_token_tracking_after_inheritance(self):
        """Test that DeepSeekModel token tracking works after inheriting from TokenTrackingLM"""
        from knowledge_storm.lm import DeepSeekModel
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 15}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            model = DeepSeekModel(model="deepseek-chat", api_key="test_key")
            
            # Test that token tracking works
            result = model.basic_request("test prompt")
            
            assert model.prompt_tokens == 20
            assert model.completion_tokens == 15
            
            # Test usage reporting
            usage = model.get_usage_and_reset()
            assert usage["deepseek-chat"]["prompt_tokens"] == 20
            assert usage["deepseek-chat"]["completion_tokens"] == 15
            
            # Test reset
            assert model.prompt_tokens == 0
            assert model.completion_tokens == 0
    
    def test_deepseek_model_api_key_validation_still_works(self):
        """Test that API key validation still works after inheritance changes"""
        from knowledge_storm.lm import DeepSeekModel
        
        # Test missing API key
        with pytest.raises(ValueError, match="DeepSeek API key must be provided"):
            DeepSeekModel(model="deepseek-chat", api_key=None)
        
        # Test valid API key
        model = DeepSeekModel(model="deepseek-chat", api_key="valid_key")
        assert model.api_key == "valid_key"
    
    def test_deepseek_model_thread_safety(self):
        """Test that DeepSeekModel token tracking is thread-safe"""
        from knowledge_storm.lm import DeepSeekModel
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            model = DeepSeekModel(model="deepseek-chat", api_key="test_key")
            
            # Test concurrent operations
            def make_request():
                model.basic_request("test prompt")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                for future in futures:
                    future.result()
            
            # Should have accumulated tokens from all requests
            assert model.prompt_tokens == 50  # 10 requests * 5 tokens each
            assert model.completion_tokens == 30  # 10 requests * 3 tokens each


if __name__ == "__main__":
    pytest.main([__file__, "-v"])