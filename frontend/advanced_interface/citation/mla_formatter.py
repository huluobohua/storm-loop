"""
MLA Citation Formatter
Concrete implementation of MLA (Modern Language Association) citation style
"""

from typing import Dict, Any
from .citation_formatter_interface import CitationFormatterInterface


class MlaFormatter(CitationFormatterInterface):
    """
    MLA citation style formatter
    Implements Modern Language Association citation format
    """
    
    def format_citation(self, paper_data: Dict[str, Any]) -> str:
        """
        Format citation in MLA style
        
        Args:
            paper_data: Paper information dictionary
            
        Returns:
            MLA formatted citation string
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
        authors_str = self._format_mla_authors(authors)
        
        # Build citation
        citation_parts = []
        
        # Author(s).
        if authors_str:
            citation_parts.append(f"{authors_str}.")
        
        # "Title of Article."
        citation_parts.append(f'"{title}."')
        
        # Journal information
        if journal:
            journal_part = f"*{journal}*"
            
            # Add volume and issue
            if volume:
                journal_part += f", vol. {volume}"
                if issue:
                    journal_part += f", no. {issue}"
            
            citation_parts.append(journal_part + ",")
        
        # Year
        if year:
            citation_parts.append(f"{year},")
        
        # Pages
        if pages:
            # MLA uses "pp." for multiple pages, "p." for single page
            if '-' in str(pages) or ',' in str(pages):
                citation_parts.append(f"pp. {pages}.")
            else:
                citation_parts.append(f"p. {pages}.")
        
        # DOI or URL
        if doi:
            citation_parts.append(f"doi:{doi}.")
        elif url:
            citation_parts.append(f"{url}.")
        
        return " ".join(citation_parts)
    
    def get_style_name(self) -> str:
        """Get MLA style name"""
        return "MLA"
    
    def _format_mla_authors(self, authors: list) -> str:
        """
        Format authors according to MLA style
        
        Args:
            authors: List of author names
            
        Returns:
            MLA formatted authors string
        """
        if not authors:
            return ""
        
        # MLA specific author formatting
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
        
        # Join authors according to MLA rules
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]}, and {formatted_authors[1]}"
        elif len(formatted_authors) <= 3:
            return f"{', '.join(formatted_authors[:-1])}, and {formatted_authors[-1]}"
        else:
            # For more than 3 authors, use first author + "et al."
            return f"{formatted_authors[0]}, et al."