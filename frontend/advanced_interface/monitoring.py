"""
Monitoring Module Entry Point
Provides backward compatibility with the refactored monitoring system
"""

from .monitoring.research_monitor import ResearchMonitor

# Export the main class for backward compatibility
__all__ = ['ResearchMonitor']