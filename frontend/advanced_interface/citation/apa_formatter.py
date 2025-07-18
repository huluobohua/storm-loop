"""
APA Citation Formatter
Concrete implementation of APA (American Psychological Association) citation style
"""

from typing import Dict, Any
from .citation_formatter_interface import CitationFormatterInterface


class ApaFormatter(CitationFormatterInterface):
    """
    APA citation style formatter
    Implements American Psychological Association citation format
    """
    
    def format_citation(self, paper_data: Dict[str, Any]) -> str:
        """
        Format citation in APA style
        
        Args:
            paper_data: Paper information dictionary
            
        Returns:
            APA formatted citation string
        """
        self.validate_paper_data(paper_data)
        
        # Extract paper information
        authors = paper_data.get("authors", [])
        title = paper_data.get("title", "")
        year = paper_data.get("year", "n.d.")
        journal = paper_data.get("journal", "")
        doi = paper_data.get("doi", "")
        url = paper_data.get("url", "")
        
        # Format authors
        authors_str = self._format_apa_authors(authors)
        
        # Build citation
        citation_parts = []
        
        # Authors (Year).
        citation_parts.append(f"{authors_str} ({year}).")
        
        # Title.
        citation_parts.append(f"{title}.")
        
        # Journal information
        if journal:
            journal_part = f"*{journal}*"
            
            # Add volume and issue if available
            volume = paper_data.get("volume")
            issue = paper_data.get("issue")
            if volume:
                journal_part += f", {volume}"
                if issue:
                    journal_part += f"({issue})"
            
            # Add page numbers if available
            pages = paper_data.get("pages")
            if pages:
                journal_part += f", {pages}"
            
            citation_parts.append(f"{journal_part}.")
        
        # DOI or URL
        if doi:
            citation_parts.append(f"https://doi.org/{doi}")
        elif url:
            citation_parts.append(url)
        
        return " ".join(citation_parts)
    
    def get_style_name(self) -> str:
        """Get APA style name"""
        return "APA"
    
    def _format_apa_authors(self, authors: list) -> str:
        """
        Format authors according to APA style
        
        Args:
            authors: List of author names
            
        Returns:
            APA formatted authors string
        """
        if not authors:
            return "Unknown Author"
        
        # APA specific author formatting
        formatted_authors = []
        
        for author in authors:
            # Handle "First Last" format - convert to "Last, F."
            if ' ' in author:
                parts = author.split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    first_names = ' '.join(parts[:-1])
                    # Take first initial of each first name
                    initials = ''.join([name[0] + '.' for name in first_names.split() if name])
                    formatted_authors.append(f"{last_name}, {initials}")
                else:
                    formatted_authors.append(author)
            else:
                formatted_authors.append(author)
        
        # Join authors according to APA rules
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]}, & {formatted_authors[1]}"
        elif len(formatted_authors) <= 20:
            return f"{', '.join(formatted_authors[:-1])}, & {formatted_authors[-1]}"
        else:
            # For more than 20 authors, list first 19, then "..." then last author
            return f"{', '.join(formatted_authors[:19])}, ... {formatted_authors[-1]}"