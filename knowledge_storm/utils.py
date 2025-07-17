"""
Utility re-exports for backward compatibility.
This module provides access to utilities that are organized in submodules.
"""

try:
    from .storm_wiki.utils import WebPageHelper, ArticleTextProcessing
except ImportError:
    # If storm_wiki.utils can't be imported, provide stubs
    class WebPageHelper:
        """Stub WebPageHelper class for when storm_wiki.utils is not available"""
        pass
    
    class ArticleTextProcessing:
        """Stub ArticleTextProcessing class for when storm_wiki.utils is not available"""
        pass

# Re-export for backward compatibility
__all__ = ['WebPageHelper', 'ArticleTextProcessing']