"""
Project Management System
Implements research project creation, collaboration, and version control
Following Single Responsibility Principle and Open/Closed Principle
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import uuid
from datetime import datetime


class UserRole(Enum):
    """Enumeration of user roles"""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass
class Project:
    """Value object for project data"""
    id: str
    name: str
    description: str
    research_type: str
    start_date: str
    end_date: str
    created_at: datetime
    owner: str


@dataclass
class ProjectVersion:
    """Value object for project version"""
    id: str
    project_id: str
    version_number: int
    description: str
    created_at: datetime
    created_by: str


class ProjectManager:
    """
    Project management system
    Adheres to Single Responsibility Principle - only manages projects
    """
    
    def __init__(self, user_context: Optional[str] = None):
        self._projects = {}
        self._project_users = {}
        self._user_permissions = {}
        self._versions = {}
        self._current_versions = {}
        self._lock = threading.RLock()
        self._user_context = user_context or "anonymous_user"
    
    def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create new research project"""
        project_id = str(uuid.uuid4())
        
        with self._lock:
            self._projects[project_id] = Project(
                id=project_id,
                name=project_data.get("name", ""),
                description=project_data.get("description", ""),
                research_type=project_data.get("research_type", ""),
                start_date=project_data.get("start_date", ""),
                end_date=project_data.get("end_date", ""),
                created_at=datetime.now(),
                owner=self._user_context
            )
            
            # Create initial version
            version_id = self._create_version(project_id, "Initial version", self._user_context)
            self._current_versions[project_id] = version_id
        
        return project_id
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project by ID"""
        with self._lock:
            project = self._projects.get(project_id)
            if project:
                return {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "research_type": project.research_type,
                    "start_date": project.start_date,
                    "end_date": project.end_date,
                    "created_at": project.created_at,
                    "owner": project.owner
                }
            return {}
    
    def invite_user(self, project_id: str, user_email: str, role: str) -> None:
        """Invite user to project"""
        if role not in [r.value for r in UserRole]:
            raise ValueError(f"Invalid role: {role}")
        
        with self._lock:
            if project_id not in self._project_users:
                self._project_users[project_id] = []
            
            if user_email not in self._project_users[project_id]:
                self._project_users[project_id].append(user_email)
            
            # Set permissions based on role
            self._user_permissions[f"{project_id}:{user_email}"] = self._get_role_permissions(role)
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for role"""
        if role == UserRole.OWNER.value:
            return ["read", "edit", "delete", "manage_users"]
        elif role == UserRole.EDITOR.value:
            return ["read", "edit"]
        elif role == UserRole.VIEWER.value:
            return ["read"]
        return []
    
    def get_user_permissions(self, project_id: str, user_email: str) -> List[str]:
        """Get user permissions for project"""
        with self._lock:
            return self._user_permissions.get(f"{project_id}:{user_email}", [])
    
    def _create_version(self, project_id: str, description: str, created_by: str) -> str:
        """Create new version"""
        version_id = str(uuid.uuid4())
        
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
        
        return version_id
    
    def create_version(self, project_id: str, description: str) -> str:
        """Create project version"""
        with self._lock:
            return self._create_version(project_id, description, self._user_context)
    
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