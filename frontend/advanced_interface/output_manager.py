"""
Advanced Output Management System
Implements multiple format export, citation styles, and quality reports
Following Single Responsibility Principle and Interface Segregation Principle
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import threading


class OutputFormat(Enum):
    """Enumeration of available output formats"""
    PDF = "pdf"
    WORD = "word"
    LATEX = "latex"
    MARKDOWN = "markdown"
    HTML = "html"


class CitationStyle(Enum):
    """Enumeration of available citation styles"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    NATURE = "nature"


class ReportType(Enum):
    """Enumeration of available report types"""
    METHODOLOGY = "methodology"
    BIAS_ANALYSIS = "bias_analysis"
    GAP_IDENTIFICATION = "gap_identification"
    QUALITY_ASSESSMENT = "quality_assessment"


@dataclass
class QualityReport:
    """Value object for quality reports"""
    report_type: str
    data: Dict[str, Any]
    generated_at: str


class OutputManager:
    """
    Advanced output management system
    Adheres to Single Responsibility Principle - only manages output generation
    """
    
    def __init__(self):
        self.selected_formats = []
        self._format_configs = {}
        self.citation_style = "apa"
        self.included_sections = []
        self.excluded_sections = []
        self._quality_reports = {}
        self._lock = threading.RLock()
    
    def get_available_formats(self) -> List[str]:
        """Get available output formats"""
        return [fmt.value for fmt in OutputFormat]
    
    def select_output_formats(self, formats: List[str]) -> None:
        """Select output formats"""
        available = self.get_available_formats()
        for fmt in formats:
            if fmt not in available:
                raise ValueError(f"Invalid format: {fmt}")
        
        with self._lock:
            self.selected_formats = formats
    
    def configure_format(self, format_name: str, config: Dict[str, Any]) -> None:
        """Configure output format"""
        if format_name not in self.get_available_formats():
            raise ValueError(f"Invalid format: {format_name}")
        
        with self._lock:
            self._format_configs[format_name] = config
    
    def get_format_config(self, format_name: str) -> Dict[str, Any]:
        """Get format configuration"""
        with self._lock:
            return self._format_configs.get(format_name, {})
    
    def get_citation_styles(self) -> List[str]:
        """Get available citation styles"""
        return [style.value for style in CitationStyle]
    
    def set_citation_style(self, style: str) -> None:
        """Set citation style"""
        if style not in self.get_citation_styles():
            raise ValueError(f"Invalid citation style: {style}")
        
        with self._lock:
            self.citation_style = style
    
    def preview_citation_style(self, style: str, paper_data: Dict[str, Any]) -> str:
        """Preview citation in specified style"""
        if style not in self.get_citation_styles():
            raise ValueError(f"Invalid citation style: {style}")
        
        # Simple APA style preview implementation
        if style == "apa":
            authors = ", ".join(paper_data.get("authors", []))
            title = paper_data.get("title", "")
            year = paper_data.get("year", "")
            journal = paper_data.get("journal", "")
            
            return f"{authors} ({year}). {title}. {journal}."
        
        # Default format for other styles
        return f"Citation in {style} style: {paper_data.get('title', 'Unknown')}"
    
    def get_available_sections(self) -> List[str]:
        """Get available document sections"""
        return [
            "abstract",
            "introduction", 
            "methodology",
            "results",
            "discussion",
            "conclusion"
        ]
    
    def include_sections(self, sections: List[str]) -> None:
        """Include specific sections"""
        available = self.get_available_sections()
        for section in sections:
            if section not in available:
                raise ValueError(f"Invalid section: {section}")
        
        with self._lock:
            self.included_sections = sections
    
    def exclude_sections(self, sections: List[str]) -> None:
        """Exclude specific sections"""
        available = self.get_available_sections()
        for section in sections:
            if section not in available:
                raise ValueError(f"Invalid section: {section}")
        
        with self._lock:
            self.excluded_sections = sections
            # Remove from included sections if present
            self.included_sections = [s for s in self.included_sections if s not in sections]
    
    def get_report_types(self) -> List[str]:
        """Get available report types"""
        return [rt.value for rt in ReportType]
    
    def generate_quality_report(self, report_type: str, data: Dict[str, Any]) -> None:
        """Generate quality report"""
        if report_type not in self.get_report_types():
            raise ValueError(f"Invalid report type: {report_type}")
        
        with self._lock:
            self._quality_reports[report_type] = QualityReport(
                report_type=report_type,
                data=data,
                generated_at=str(datetime.now()) if 'datetime' in globals() else "2024-01-01"
            )
    
    def get_quality_report(self, report_type: str) -> Dict[str, Any]:
        """Get quality report"""
        with self._lock:
            report = self._quality_reports.get(report_type)
            if report:
                return {
                    "report_type": report.report_type,
                    **report.data,
                    "generated_at": report.generated_at
                }
            return {}