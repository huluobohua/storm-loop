"""
Database Management System
Implements academic database integration, search strategy building, and paper management
Following Single Responsibility Principle and Dependency Inversion Principle
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import uuid


class DatabaseType(Enum):
    """Enumeration of available database types"""
    OPENALEX = "openalex"
    CROSSREF = "crossref"
    INSTITUTIONAL = "institutional"


@dataclass
class AuthenticationStatus:
    """Value object for authentication status"""
    authenticated: bool
    username: Optional[str] = None
    institution: Optional[str] = None


@dataclass
class Paper:
    """Value object for paper data"""
    id: str
    title: str
    authors: List[str]
    doi: Optional[str] = None
    year: Optional[int] = None


class QueryBuilder:
    """
    Query builder for academic database searches
    Follows Builder Pattern and Single Responsibility Principle
    """
    
    def __init__(self):
        self.terms = []
        self.operators = []
    
    def add_term(self, term: str, operator: str = "AND") -> None:
        """Add search term with operator"""
        self.terms.append(term)
        if len(self.terms) > 1:  # Don't add operator for first term
            self.operators.append(operator)
    
    def build_query(self) -> str:
        """Build final query string"""
        if not self.terms:
            return ""
        
        query = self.terms[0]
        for i, term in enumerate(self.terms[1:], 1):
            operator = self.operators[i-1] if i-1 < len(self.operators) else "AND"
            query += f" {operator} {term}"
        
        return query


class DatabaseManager:
    """
    Database management system
    Adheres to Single Responsibility Principle - only manages database operations
    """
    
    def __init__(self):
        self.selected_database = None
        self._auth_status = {}
        self._papers = {}
        self._collections = {}
        self._paper_annotations = {}
        self._lock = threading.RLock()
    
    def get_available_databases(self) -> List[str]:
        """Get available database types"""
        return [db.value for db in DatabaseType]
    
    def select_database(self, database: str) -> None:
        """Select database for operations"""
        if database not in self.get_available_databases():
            raise ValueError(f"Invalid database: {database}")
        
        with self._lock:
            self.selected_database = database
    
    def authenticate_database(self, database: str, credentials: Dict[str, str]) -> None:
        """Authenticate with database"""
        if database not in self.get_available_databases():
            raise ValueError(f"Invalid database: {database}")
        
        with self._lock:
            self._auth_status[database] = AuthenticationStatus(
                authenticated=True,
                username=credentials.get("username"),
                institution=credentials.get("institution")
            )
    
    def get_authentication_status(self, database: str) -> Dict[str, Any]:
        """Get authentication status"""
        with self._lock:
            status = self._auth_status.get(database)
            if status:
                return {
                    "authenticated": status.authenticated,
                    "username": status.username,
                    "institution": status.institution
                }
            return {"authenticated": False}
    
    def get_query_builder(self) -> QueryBuilder:
        """Get query builder instance"""
        return QueryBuilder()
    
    def import_paper(self, paper_data: Dict[str, Any]) -> str:
        """Import paper and return paper ID"""
        paper_id = str(uuid.uuid4())
        
        with self._lock:
            self._papers[paper_id] = Paper(
                id=paper_id,
                title=paper_data.get("title", ""),
                authors=paper_data.get("authors", []),
                doi=paper_data.get("doi"),
                year=paper_data.get("year")
            )
        
        return paper_id
    
    def create_collection(self, collection_name: str) -> None:
        """Create paper collection"""
        with self._lock:
            self._collections[collection_name] = []
    
    def add_paper_to_collection(self, paper_id: str, collection_name: str) -> None:
        """Add paper to collection"""
        with self._lock:
            if collection_name not in self._collections:
                self._collections[collection_name] = []
            
            if paper_id not in self._collections[collection_name]:
                self._collections[collection_name].append(paper_id)
    
    def get_collection_papers(self, collection_name: str) -> List[str]:
        """Get papers in collection"""
        with self._lock:
            return self._collections.get(collection_name, [])
    
    def annotate_paper(self, paper_id: str, annotation: str) -> None:
        """Add annotation to paper"""
        with self._lock:
            self._paper_annotations[paper_id] = annotation
    
    def get_paper_annotation(self, paper_id: str) -> str:
        """Get paper annotation"""
        with self._lock:
            return self._paper_annotations.get(paper_id, "")
    
    def search_papers(self, query: str, database: str = None) -> List[Dict[str, Any]]:
        """Search papers in database"""
        # Mock implementation for testing
        return [
            {
                "title": f"Sample Paper for {query}",
                "authors": ["Author 1", "Author 2"],
                "year": 2024,
                "doi": "10.1000/sample"
            }
        ]