"""
Base report generator interface.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import ValidationSession


class BaseReportGenerator(ABC):
    """
    Base class for all report generators.
    
    Provides common functionality for generating validation reports.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        output_dir: str = "validation_reports",
        formats: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.output_dir = Path(output_dir)
        self.formats = formats or ["json", "html"]
        self.config = config or {}
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def generate_report(
        self,
        session: ValidationSession,
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        Generate report for validation session.
        
        Args:
            session: The validation session to report on
            **kwargs: Additional report parameters
            
        Returns:
            Dictionary mapping format to file path
        """
        pass
    
    def _generate_filename(
        self, 
        session: ValidationSession, 
        format_type: str,
        suffix: str = ""
    ) -> str:
        """Generate filename for report."""
        timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
        base_name = f"{self.name}_{session.session_id}_{timestamp}"
        if suffix:
            base_name += f"_{suffix}"
        return f"{base_name}.{format_type}"
    
    def _save_json_report(
        self, 
        session: ValidationSession, 
        report_data: Dict[str, Any],
        suffix: str = ""
    ) -> str:
        """Save report as JSON file."""
        filename = self._generate_filename(session, "json", suffix)
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(filepath)
    
    def _save_html_report(
        self, 
        session: ValidationSession, 
        html_content: str,
        suffix: str = ""
    ) -> str:
        """Save report as HTML file."""
        filename = self._generate_filename(session, "html", suffix)
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _generate_html_template(
        self, 
        session: ValidationSession, 
        content_sections: List[Dict[str, str]]
    ) -> str:
        """Generate HTML report using a basic template."""
        
        # Basic HTML template
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name} Report - {session.session_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header {{
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .summary {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .metric {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin: 5px;
        }}
        .status-passed {{
            background: #28a745;
        }}
        .status-failed {{
            background: #dc3545;
        }}
        .status-warning {{
            background: #ffc107;
            color: #212529;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.name} Report</h1>
            <p><strong>Session:</strong> {session.session_id}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">Total Tests: {session.total_count}</div>
            <div class="metric status-passed">Passed: {session.passed_count}</div>
            <div class="metric status-failed">Failed: {session.failed_count}</div>
            <div class="metric">Success Rate: {session.success_rate:.1%}</div>
            {f'<div class="metric">Duration: {session.duration:.2f}s</div>' if session.duration else ''}
        </div>
        
        {"".join(f'<div class="section">{section["content"]}</div>' for section in content_sections)}
        
        <div class="section">
            <h2>Report Generation Info</h2>
            <p><strong>Generated by:</strong> {self.name}</p>
            <p><strong>Framework Version:</strong> Academic Validation Framework v1.0.0</p>
            <p><strong>Report Time:</strong> {datetime.now().isoformat()}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _create_results_table(self, results: List[Any]) -> str:
        """Create HTML table for validation results."""
        if not results:
            return "<p>No results to display.</p>"
        
        table_html = """
        <table>
            <thead>
                <tr>
                    <th>Validator</th>
                    <th>Test</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Execution Time</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for result in results:
            status_class = f"status-{result.status}"
            score_display = f"{result.score:.2f}" if result.score is not None else "N/A"
            time_display = f"{result.execution_time:.3f}s" if result.execution_time else "N/A"
            
            table_html += f"""
                <tr>
                    <td>{result.validator_name}</td>
                    <td>{result.test_name}</td>
                    <td><span class="{status_class}">{result.status}</span></td>
                    <td>{score_display}</td>
                    <td>{time_display}</td>
                </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        
        return table_html
    
    async def cleanup(self) -> None:
        """Cleanup report generator resources."""
        pass