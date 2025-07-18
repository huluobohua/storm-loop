"""
Project Version Management System
Implements version control for research projects
Following Single Responsibility Principle
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading
import uuid
from datetime import datetime


@dataclass
class ProjectVersion:
    """Value object for project version"""
    id: str
    project_id: str
    version_number: int
    description: str
    created_at: datetime
    created_by: str


class ProjectVersionManager:
    """
    Project version management system
    Adheres to Single Responsibility Principle - only manages versions
    """
    
    def __init__(self):
        self._versions = {}
        self._current_versions = {}
        self._lock = threading.RLock()
    
    def create_version(self, project_id: str, description: str, created_by: str) -> str:
        """Create new version"""
        version_id = str(uuid.uuid4())
        
        with self._lock:
            # Get next version number
            project_versions = [v for v in self._versions.values() if v.project_id == project_id]
            version_number = len(project_versions) + 1
            
            self._versions[version_id] = ProjectVersion(
                id=version_id,
                project_id=project_id,
                version_number=version_number,
                description=description,
                created_at=datetime.now(),
                created_by=created_by
            )
            
            # Set as current version
            self._current_versions[project_id] = version_id
        
        return version_id
    
    def get_version(self, version_id: str) -> Optional[ProjectVersion]:
        """Get version by ID"""
        with self._lock:
            return self._versions.get(version_id)
    
    def get_project_versions(self, project_id: str) -> List[ProjectVersion]:
        """Get all versions for a project"""
        with self._lock:
            return [v for v in self._versions.values() if v.project_id == project_id]
    
    def compare_versions(self, project_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two project versions"""
        with self._lock:
            v1 = self._versions.get(version1)
            v2 = self._versions.get(version2)
            
            if v1 and v2:
                return {
                    "version1": {
                        "id": v1.id,
                        "description": v1.description,
                        "created_at": v1.created_at
                    },
                    "version2": {
                        "id": v2.id,
                        "description": v2.description,
                        "created_at": v2.created_at
                    },
                    "differences": ["Content differences would be shown here"]
                }
            return {}
    
    def rollback_to_version(self, project_id: str, version_id: str) -> None:
        """Rollback project to specific version"""
        with self._lock:
            if version_id in self._versions:
                self._current_versions[project_id] = version_id
    
    def get_current_version(self, project_id: str) -> str:
        """Get current version ID"""
        with self._lock:
            return self._current_versions.get(project_id, "")
    
    def set_current_version(self, project_id: str, version_id: str) -> None:
        """Set current version ID"""
        with self._lock:
            if version_id in self._versions:
                self._current_versions[project_id] = version_id