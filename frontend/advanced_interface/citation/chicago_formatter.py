"""
Chicago Citation Formatter
Concrete implementation of Chicago (Author-Date) citation style
"""

from typing import Dict, Any
from .citation_formatter_interface import CitationFormatterInterface


class ChicagoFormatter(CitationFormatterInterface):
    """
    Chicago citation style formatter (Author-Date system)
    Implements Chicago Manual of Style citation format
    """
    
    def format_citation(self, paper_data: Dict[str, Any]) -> str:
        """
        Format citation in Chicago (Author-Date) style
        
        Args:
            paper_data: Paper information dictionary
            
        Returns:
            Chicago formatted citation string
        """
        self.validate_paper_data(paper_data)
        
        # Extract paper information
        authors = paper_data.get("authors", [])
        title = paper_data.get("title", "")
        journal = paper_data.get("journal", "")
        volume = paper_data.get("volume", "")
        issue = paper_data.get("issue", "")
        year = paper_data.get("year", "")
        pages = paper_data.get("pages", "")
        doi = paper_data.get("doi", "")
        url = paper_data.get("url", "")
        
        # Format authors
        authors_str = self._format_chicago_authors(authors)
        
        # Build citation
        citation_parts = []
        
        # Author(s). Year.
        if authors_str:
            citation_parts.append(f"{authors_str}.")
        if year:
            citation_parts.append(f"{year}.")
        
        # "Title of Article."
        citation_parts.append(f'"{title}."')
        
        # Journal information
        if journal:
            journal_part = f"*{journal}*"
            
            # Add volume and issue
            if volume:
                journal_part += f" {volume}"
                if issue:
                    journal_part += f", no. {issue}"
            
            citation_parts.append(journal_part)
        
        # Pages (with colon)
        if pages:
            citation_parts.append(f": {pages}.")
        elif citation_parts and not citation_parts[-1].endswith('.'):
            citation_parts[-1] += "."
        
        # DOI or URL
        if doi:
            citation_parts.append(f"https://doi.org/{doi}.")
        elif url:
            citation_parts.append(f"{url}.")
        
        return " ".join(citation_parts)
    
    def get_style_name(self) -> str:
        """Get Chicago style name"""
        return "Chicago"
    
    def _format_chicago_authors(self, authors: list) -> str:
        """
        Format authors according to Chicago style
        
        Args:
            authors: List of author names
            
        Returns:
            Chicago formatted authors string
        """
        if not authors:
            return ""
        
        # Chicago specific author formatting
        formatted_authors = []
        
        for i, author in enumerate(authors):
            if i == 0:
                # First author: "Last, First"
                if ' ' in author:
                    parts = author.split()
                    if len(parts) >= 2:
                        last_name = parts[-1]
                        first_names = ' '.join(parts[:-1])
                        formatted_authors.append(f"{last_name}, {first_names}")
                    else:
                        formatted_authors.append(author)
                else:
                    formatted_authors.append(author)
            else:
                # Subsequent authors: "First Last"
                formatted_authors.append(author)
        
        # Join authors according to Chicago rules
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]}, and {formatted_authors[1]}"
        elif len(formatted_authors) <= 10:
            return f"{', '.join(formatted_authors[:-1])}, and {formatted_authors[-1]}"
        else:
            # For more than 10 authors, list first 7 + "et al."
            return f"{', '.join(formatted_authors[:7])}, et al."