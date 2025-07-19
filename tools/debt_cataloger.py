#!/usr/bin/env python3
"""
Automated Technical Debt Cataloging System
Part of Project Phoenix - Technical Debt Reduction Strategy

Scans codebase for technical debt markers (TODO, FIXME, HACK) and generates
comprehensive reports with severity classification and actionable insights.
"""

import os
import re
import ast
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import argparse
import sys

# Optional dependencies for enhanced functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


@dataclass
class DebtItem:
    """Represents a single technical debt item"""
    file_path: str
    line_number: int
    debt_type: str  # TODO, FIXME, HACK
    content: str
    priority: str  # critical, high, medium, low
    category: str  # security, architecture, performance, quality
    context_lines: List[str]
    estimated_effort: str  # hours estimate
    risk_level: str  # blocking, high, medium, low
    debt_id: str  # unique identifier


class DebtPatternAnalyzer:
    """Analyzes debt patterns and classifies severity"""
    
    # Security-related patterns (Critical priority)
    SECURITY_PATTERNS = [
        r'(password|secret|key|token|auth|encrypt|decrypt|credential)',
        r'(sql.*injection|xss|csrf|vulnerability)',
        r'(unsafe|insecure|security.*issue)',
        r'(permission|authorization|authentication)',
    ]
    
    # Architecture-related patterns (High priority)
    ARCHITECTURE_PATTERNS = [
        r'(circular.*dependency|god.*object|singleton|anti.*pattern)',
        r'(tight.*coupling|solid.*violation|architecture)',
        r'(refactor|redesign|restructure)',
        r'(package.*structure|module.*organization)',
    ]
    
    # Performance-related patterns (High/Medium priority)
    PERFORMANCE_PATTERNS = [
        r'(performance|slow|optimize|bottleneck)',
        r'(memory.*leak|cache|n\+1|efficiency)',
        r'(database.*query|index|pagination)',
        r'(async|concurrent|parallel)',
    ]
    
    # Quality-related patterns (Medium priority)
    QUALITY_PATTERNS = [
        r'(test|spec|coverage|validation)',
        r'(documentation|comment|doc)',
        r'(type.*hint|typing|annotation)',
        r'(cleanup|polish|improve)',
    ]
    
    # Critical blocking patterns
    BLOCKING_PATTERNS = [
        r'(production|deploy|release|critical)',
        r'(break|broken|fail|error)',
        r'(block|prevent|stop)',
        r'(urgent|asap|immediate)',
    ]

    def analyze_debt_item(self, content: str, context: List[str]) -> Tuple[str, str, str, str]:
        """
        Analyze debt item and return (priority, category, effort, risk_level)
        """
        content_lower = content.lower()
        context_text = ' '.join(context).lower()
        full_text = f"{content_lower} {context_text}"
        
        # Determine category
        category = self._classify_category(full_text)
        
        # Determine priority based on category and patterns
        priority = self._classify_priority(full_text, category)
        
        # Estimate effort
        effort = self._estimate_effort(full_text)
        
        # Assess risk level
        risk_level = self._assess_risk(full_text, priority)
        
        return priority, category, effort, risk_level
    
    def _classify_category(self, text: str) -> str:
        """Classify debt into categories"""
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.SECURITY_PATTERNS):
            return "security"
        elif any(re.search(pattern, text, re.IGNORECASE) for pattern in self.ARCHITECTURE_PATTERNS):
            return "architecture"
        elif any(re.search(pattern, text, re.IGNORECASE) for pattern in self.PERFORMANCE_PATTERNS):
            return "performance"
        else:
            return "quality"
    
    def _classify_priority(self, text: str, category: str) -> str:
        """Classify priority level"""
        if category == "security" or any(re.search(pattern, text, re.IGNORECASE) for pattern in self.BLOCKING_PATTERNS):
            return "critical"
        elif category in ["architecture", "performance"]:
            return "high"
        else:
            return "medium"
    
    def _estimate_effort(self, text: str) -> str:
        """Estimate effort required"""
        # Simple heuristic based on keywords
        if any(keyword in text for keyword in ["refactor", "redesign", "rewrite", "restructure"]):
            return "8-16 hours"
        elif any(keyword in text for keyword in ["implement", "add", "create", "build"]):
            return "4-8 hours"
        elif any(keyword in text for keyword in ["fix", "update", "improve", "optimize"]):
            return "2-4 hours"
        else:
            return "1-2 hours"
    
    def _assess_risk(self, text: str, priority: str) -> str:
        """Assess risk level"""
        if priority == "critical":
            return "blocking"
        elif any(re.search(pattern, text, re.IGNORECASE) for pattern in self.BLOCKING_PATTERNS):
            return "high"
        elif priority == "high":
            return "medium"
        else:
            return "low"


class DebtCatalogingEngine:
    """Main engine for cataloging technical debt"""
    
    def __init__(self, root_path: str, output_dir: str = "debt_analysis"):
        self.root_path = Path(root_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.analyzer = DebtPatternAnalyzer()
        self.debt_items: List[DebtItem] = []
        
        # Debt marker patterns
        self.debt_patterns = {
            'TODO': re.compile(r'#\s*TODO:?\s*(.+)', re.IGNORECASE),
            'FIXME': re.compile(r'#\s*FIXME:?\s*(.+)', re.IGNORECASE),
            'HACK': re.compile(r'#\s*HACK:?\s*(.+)', re.IGNORECASE),
            'BUG': re.compile(r'#\s*BUG:?\s*(.+)', re.IGNORECASE),
            'XXX': re.compile(r'#\s*XXX:?\s*(.+)', re.IGNORECASE),
        }
        
        # Files to ignore
        self.ignore_patterns = {
            '*.pyc', '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', '.pytest_cache', '.coverage', '*.egg-info',
            '.taskmaster', '.cursor', '.roo', '.trae', '.windsurf',
            'storm/storm/lib/', 'storm/storm/bin/', 'storm/storm/include/',
            'site-packages/', 'lib/python', 'bin/python', 'include/python'
        }
    
    def scan_codebase(self) -> List[DebtItem]:
        """Scan entire codebase for debt markers"""
        print(f"🔍 Scanning codebase at {self.root_path}")
        
        python_files = self._find_python_files()
        print(f"📁 Found {len(python_files)} Python files to scan")
        
        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                print(f"⚠️  Error scanning {file_path}: {e}")
        
        print(f"📊 Found {len(self.debt_items)} debt items")
        return self.debt_items
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the codebase"""
        python_files = []
        
        for file_path in self.root_path.rglob("*.py"):
            # Skip ignored directories
            if any(ignore in str(file_path) for ignore in self.ignore_patterns):
                continue
            python_files.append(file_path)
        
        return python_files
    
    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for debt markers"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            return
        
        for line_num, line in enumerate(lines, 1):
            for debt_type, pattern in self.debt_patterns.items():
                match = pattern.search(line)
                if match:
                    debt_item = self._create_debt_item(
                        file_path, line_num, debt_type, match.group(1), lines
                    )
                    self.debt_items.append(debt_item)
    
    def _create_debt_item(self, file_path: Path, line_num: int, debt_type: str, 
                         content: str, all_lines: List[str]) -> DebtItem:
        """Create a DebtItem with analysis"""
        # Get context lines (3 before, 3 after)
        start_idx = max(0, line_num - 4)
        end_idx = min(len(all_lines), line_num + 3)
        context_lines = [line.strip() for line in all_lines[start_idx:end_idx]]
        
        # Analyze the debt item
        priority, category, effort, risk_level = self.analyzer.analyze_debt_item(
            content, context_lines
        )
        
        # Generate unique ID
        debt_id = self._generate_debt_id(file_path, line_num, content)
        
        return DebtItem(
            file_path=str(file_path.relative_to(self.root_path)),
            line_number=line_num,
            debt_type=debt_type,
            content=content.strip(),
            priority=priority,
            category=category,
            context_lines=context_lines,
            estimated_effort=effort,
            risk_level=risk_level,
            debt_id=debt_id
        )
    
    def _generate_debt_id(self, file_path: Path, line_num: int, content: str) -> str:
        """Generate unique ID for debt item"""
        unique_string = f"{file_path}:{line_num}:{content}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def generate_reports(self) -> None:
        """Generate comprehensive debt reports"""
        print("📈 Generating debt analysis reports...")
        
        # Generate JSON export
        self._export_json()
        
        # Generate summary report
        self._generate_summary_report()
        
        # Generate detailed reports by category
        self._generate_category_reports()
        
        # Generate heat map data
        self._generate_heat_map_data()
        
        # Generate priority action items
        self._generate_action_items()
        
        if PLOTLY_AVAILABLE:
            self._generate_visualizations()
        
        print(f"✅ Reports generated in {self.output_dir}")
    
    def _export_json(self) -> None:
        """Export debt items to JSON"""
        debt_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_debt_items": len(self.debt_items),
            "debt_items": [asdict(item) for item in self.debt_items]
        }
        
        with open(self.output_dir / "debt_inventory.json", 'w') as f:
            json.dump(debt_data, f, indent=2)
    
    def _generate_summary_report(self) -> None:
        """Generate executive summary report"""
        stats = self._calculate_statistics()
        
        report = f"""# Technical Debt Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

**Total Debt Items**: {stats['total_items']}
**Critical Items**: {stats['critical_count']} ({stats['critical_percent']:.1f}%)
**High Priority Items**: {stats['high_count']} ({stats['high_percent']:.1f}%)

### Debt Distribution by Type
{self._format_distribution(stats['by_type'])}

### Debt Distribution by Category
{self._format_distribution(stats['by_category'])}

### Priority Distribution
{self._format_distribution(stats['by_priority'])}

### Risk Level Distribution
{self._format_distribution(stats['by_risk'])}

## Critical Action Items (Top 10)
{self._format_critical_items()}

## Files with Highest Debt Concentration
{self._format_debt_hotspots()}

## Estimated Total Effort
- Critical items: {stats['critical_effort']}
- High priority: {stats['high_effort']}
- All items: {stats['total_effort']}
"""
        
        with open(self.output_dir / "debt_summary.md", 'w') as f:
            f.write(report)
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        total_items = len(self.debt_items)
        
        # Count by priority
        by_priority = Counter(item.priority for item in self.debt_items)
        critical_count = by_priority.get('critical', 0)
        high_count = by_priority.get('high', 0)
        
        # Percentages
        critical_percent = (critical_count / total_items * 100) if total_items > 0 else 0
        high_percent = (high_count / total_items * 100) if total_items > 0 else 0
        
        return {
            'total_items': total_items,
            'critical_count': critical_count,
            'high_count': high_count,
            'critical_percent': critical_percent,
            'high_percent': high_percent,
            'by_type': Counter(item.debt_type for item in self.debt_items),
            'by_category': Counter(item.category for item in self.debt_items),
            'by_priority': by_priority,
            'by_risk': Counter(item.risk_level for item in self.debt_items),
            'critical_effort': self._estimate_total_effort('critical'),
            'high_effort': self._estimate_total_effort('high'),
            'total_effort': self._estimate_total_effort('all')
        }
    
    def _format_distribution(self, counter: Counter) -> str:
        """Format counter as a readable distribution"""
        lines = []
        for item, count in counter.most_common():
            lines.append(f"- {item}: {count}")
        return '\n'.join(lines)
    
    def _format_critical_items(self) -> str:
        """Format critical debt items"""
        critical_items = [item for item in self.debt_items if item.priority == 'critical'][:10]
        
        if not critical_items:
            return "No critical debt items found."
        
        lines = []
        for i, item in enumerate(critical_items, 1):
            lines.append(f"{i}. **{item.file_path}:{item.line_number}** - {item.content}")
        
        return '\n'.join(lines)
    
    def _format_debt_hotspots(self) -> str:
        """Format files with highest debt concentration"""
        file_debt_count = Counter(item.file_path for item in self.debt_items)
        
        lines = []
        for file_path, count in file_debt_count.most_common(10):
            lines.append(f"- {file_path}: {count} items")
        
        return '\n'.join(lines)
    
    def _estimate_total_effort(self, priority_filter: str) -> str:
        """Estimate total effort for given priority"""
        if priority_filter == 'all':
            items = self.debt_items
        else:
            items = [item for item in self.debt_items if item.priority == priority_filter]
        
        effort_mapping = {
            "1-2 hours": 1.5,
            "2-4 hours": 3,
            "4-8 hours": 6,
            "8-16 hours": 12
        }
        
        total_hours = sum(effort_mapping.get(item.estimated_effort, 2) for item in items)
        
        if total_hours < 8:
            return f"{total_hours:.1f} hours"
        elif total_hours < 40:
            return f"{total_hours / 8:.1f} days"
        else:
            return f"{total_hours / 40:.1f} weeks"
    
    def _generate_category_reports(self) -> None:
        """Generate detailed reports by category"""
        categories = set(item.category for item in self.debt_items)
        
        for category in categories:
            category_items = [item for item in self.debt_items if item.category == category]
            
            report = f"""# {category.title()} Debt Report

**Total Items**: {len(category_items)}

## Items by Priority
"""
            
            for priority in ['critical', 'high', 'medium', 'low']:
                priority_items = [item for item in category_items if item.priority == priority]
                if priority_items:
                    report += f"\n### {priority.title()} Priority ({len(priority_items)} items)\n\n"
                    for item in priority_items[:20]:  # Limit to top 20
                        report += f"- **{item.file_path}:{item.line_number}** - {item.content}\n"
            
            with open(self.output_dir / f"debt_{category}.md", 'w') as f:
                f.write(report)
    
    def _generate_heat_map_data(self) -> None:
        """Generate heat map data for visualization"""
        heat_map_data = []
        
        # Group by file and calculate debt density
        file_debt = defaultdict(list)
        for item in self.debt_items:
            file_debt[item.file_path].append(item)
        
        for file_path, items in file_debt.items():
            # Calculate weighted score based on priority
            priority_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
            weighted_score = sum(priority_weights.get(item.priority, 1) for item in items)
            
            heat_map_data.append({
                'file_path': file_path,
                'debt_count': len(items),
                'weighted_score': weighted_score,
                'directory': str(Path(file_path).parent),
                'file_name': Path(file_path).name
            })
        
        # Sort by weighted score
        heat_map_data.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        with open(self.output_dir / "debt_heat_map.json", 'w') as f:
            json.dump(heat_map_data, f, indent=2)
    
    def _generate_action_items(self) -> None:
        """Generate prioritized action items for immediate work"""
        # Critical items that block production
        blocking_items = [item for item in self.debt_items if item.risk_level == 'blocking']
        
        # High priority security items
        security_items = [item for item in self.debt_items 
                         if item.category == 'security' and item.priority in ['critical', 'high']]
        
        # Architecture violations
        arch_items = [item for item in self.debt_items 
                     if item.category == 'architecture' and item.priority == 'high']
        
        action_report = f"""# Immediate Action Items - Technical Debt

## 🚨 BLOCKING ITEMS - FIX IMMEDIATELY ({len(blocking_items)} items)
"""
        
        for item in blocking_items[:10]:
            action_report += f"""
### {item.file_path}:{item.line_number}
- **Type**: {item.debt_type}
- **Issue**: {item.content}
- **Effort**: {item.estimated_effort}
- **ID**: {item.debt_id}
"""
        
        action_report += f"""

## 🔒 SECURITY DEBT - HIGH PRIORITY ({len(security_items)} items)
"""
        
        for item in security_items[:10]:
            action_report += f"""
### {item.file_path}:{item.line_number}
- **Type**: {item.debt_type}
- **Issue**: {item.content}
- **Effort**: {item.estimated_effort}
- **ID**: {item.debt_id}
"""
        
        action_report += f"""

## 🏗️ ARCHITECTURE DEBT - HIGH PRIORITY ({len(arch_items)} items)
"""
        
        for item in arch_items[:10]:
            action_report += f"""
### {item.file_path}:{item.line_number}
- **Type**: {item.debt_type}
- **Issue**: {item.content}
- **Effort**: {item.estimated_effort}
- **ID**: {item.debt_id}
"""
        
        with open(self.output_dir / "action_items.md", 'w') as f:
            f.write(action_report)
    
    def _generate_visualizations(self) -> None:
        """Generate interactive visualizations using Plotly"""
        try:
            # Debt distribution charts
            self._create_distribution_charts()
            
            # Debt timeline (if we had commit data)
            # self._create_timeline_chart()
            
            # File heat map
            self._create_file_heat_map()
            
        except Exception as e:
            print(f"⚠️  Error generating visualizations: {e}")
    
    def _create_distribution_charts(self) -> None:
        """Create distribution charts"""
        if not PANDAS_AVAILABLE or not PLOTLY_AVAILABLE:
            return
        
        # Create DataFrame
        df = pd.DataFrame([asdict(item) for item in self.debt_items])
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Debt by Type', 'Debt by Category', 'Debt by Priority', 'Debt by Risk Level'),
            specs=[[{"type": "pie"}, {"type": "pie"}],
                   [{"type": "pie"}, {"type": "pie"}]]
        )
        
        # Debt by type
        type_counts = df['debt_type'].value_counts()
        fig.add_trace(go.Pie(labels=type_counts.index, values=type_counts.values, name="Type"),
                      row=1, col=1)
        
        # Debt by category
        category_counts = df['category'].value_counts()
        fig.add_trace(go.Pie(labels=category_counts.index, values=category_counts.values, name="Category"),
                      row=1, col=2)
        
        # Debt by priority
        priority_counts = df['priority'].value_counts()
        fig.add_trace(go.Pie(labels=priority_counts.index, values=priority_counts.values, name="Priority"),
                      row=2, col=1)
        
        # Debt by risk level
        risk_counts = df['risk_level'].value_counts()
        fig.add_trace(go.Pie(labels=risk_counts.index, values=risk_counts.values, name="Risk"),
                      row=2, col=2)
        
        fig.update_layout(title_text="Technical Debt Distribution Analysis")
        fig.write_html(str(self.output_dir / "debt_distribution.html"))
    
    def _create_file_heat_map(self) -> None:
        """Create file-level debt heat map"""
        if not PANDAS_AVAILABLE or not PLOTLY_AVAILABLE:
            return
        
        # Load heat map data
        with open(self.output_dir / "debt_heat_map.json", 'r') as f:
            heat_data = json.load(f)
        
        df = pd.DataFrame(heat_data)
        
        # Create treemap
        fig = px.treemap(
            df.head(50),  # Top 50 files
            path=['directory', 'file_name'],
            values='weighted_score',
            color='debt_count',
            color_continuous_scale='Reds',
            title='Technical Debt Heat Map - File Level'
        )
        
        fig.write_html(str(self.output_dir / "debt_heat_map.html"))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Technical Debt Cataloging System")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parser.add_argument("--output", default="debt_analysis", help="Output directory")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both",
                       help="Output format")
    
    args = parser.parse_args()
    
    print("🚀 Starting Technical Debt Analysis...")
    print(f"📂 Scanning: {os.path.abspath(args.root)}")
    print(f"📁 Output: {os.path.abspath(args.output)}")
    
    # Initialize cataloging engine
    engine = DebtCatalogingEngine(args.root, args.output)
    
    # Scan codebase
    debt_items = engine.scan_codebase()
    
    if not debt_items:
        print("✅ No technical debt found!")
        return
    
    # Generate reports
    engine.generate_reports()
    
    # Print summary
    stats = engine._calculate_statistics()
    print(f"""
📊 DEBT ANALYSIS COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Total Items: {stats['total_items']}
🚨 Critical: {stats['critical_count']} ({stats['critical_percent']:.1f}%)
⚠️  High Priority: {stats['high_count']} ({stats['high_percent']:.1f}%)

📁 Reports generated in: {args.output}/
   • debt_summary.md - Executive summary
   • debt_inventory.json - Complete debt inventory
   • action_items.md - Immediate action items
   • debt_heat_map.json - Heat map data
   • debt_*.md - Category-specific reports

🎯 Next Steps:
   1. Review action_items.md for immediate fixes
   2. Address critical security debt first
   3. Integrate with CI/CD pipeline
   4. Set up regular debt monitoring
""")


if __name__ == "__main__":
    main()