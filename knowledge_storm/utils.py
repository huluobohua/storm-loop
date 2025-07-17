"""
Utility re-exports for backward compatibility.
This module provides access to utilities that are organized in submodules.
"""

try:
    from .storm_wiki.utils import WebPageHelper, ArticleTextProcessing, FileIOHelper, makeStringRed, truncate_filename
except ImportError:
    # If storm_wiki.utils can't be imported, provide stubs
    class WebPageHelper:
        """Stub WebPageHelper class for when storm_wiki.utils is not available"""
        pass
    
    class ArticleTextProcessing:
        """Stub ArticleTextProcessing class for when storm_wiki.utils is not available"""
        pass
    
    class FileIOHelper:
        """Stub FileIOHelper class for when storm_wiki.utils is not available"""
        pass
    
    def makeStringRed(message):
        """Stub makeStringRed function for when storm_wiki.utils is not available"""
        return message
    
    def truncate_filename(filename, max_length=125):
        """Stub truncate_filename function for when storm_wiki.utils is not available"""
        return filename

# Re-export for backward compatibility
__all__ = ['WebPageHelper', 'ArticleTextProcessing', 'FileIOHelper', 'makeStringRed', 'truncate_filename']