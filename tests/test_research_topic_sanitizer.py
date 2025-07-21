"""
Test suite for ResearchTopicSanitizer following TDD principles.
"""
import pytest
from research.topic_sanitizer import ResearchTopicSanitizer


class TestResearchTopicSanitizer:
    """Test ResearchTopicSanitizer following Sandi Metz rules"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sanitizer = ResearchTopicSanitizer()
    
    def test_sanitize_basic_topic(self):
        """Should convert basic topic to safe directory name"""
        result = self.sanitizer.sanitize("AI in Healthcare")
        assert result == "ai_in_healthcare"
    
    def test_sanitize_removes_special_characters(self):
        """Should remove special characters"""
        result = self.sanitizer.sanitize("AI & ML: The Future!")
        assert result == "ai_ml_the_future"
    
    def test_sanitize_limits_length(self):
        """Should limit output to 100 characters"""
        long_topic = "A" * 150
        result = self.sanitizer.sanitize(long_topic)
        assert len(result) <= 100
    
    def test_sanitize_handles_empty_string(self):
        """Should handle empty string input"""
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            self.sanitizer.sanitize("")
    
    def test_sanitize_preserves_alphanumeric(self):
        """Should preserve alphanumeric characters"""
        result = self.sanitizer.sanitize("AI2023 Healthcare")
        assert "ai2023" in result
        assert "healthcare" in result