"""
Citation formatting package
Provides Strategy pattern implementation for various citation styles
"""

from .citation_formatter_interface import CitationFormatterInterface
from .citation_factory import CitationFactory
from .apa_formatter import ApaFormatter
from .mla_formatter import MlaFormatter
from .chicago_formatter import ChicagoFormatter

__all__ = [
    'CitationFormatterInterface',
    'CitationFactory',
    'ApaFormatter',
    'MlaFormatter',
    'ChicagoFormatter'
]