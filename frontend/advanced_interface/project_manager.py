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
from .project_version_manager import ProjectVersionManager


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




class ProjectManager:
    """
    Project management system
    Adheres to Single Responsibility Principle - only manages projects
    """
    
    def __init__(self, user_context: Optional[str] = None, 
                 version_manager: Optional[ProjectVersionManager] = None):
        self._projects = {}
        self._project_users = {}
        self._user_permissions = {}
        self._lock = threading.RLock()
        self._user_context = user_context or "anonymous_user"
        self._version_manager = version_manager or ProjectVersionManager()
    
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
            self._version_manager.create_version(project_id, "Initial version", self._user_context)
        
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
    
    def create_version(self, project_id: str, description: str) -> str:
        """Create project version"""
        return self._version_manager.create_version(project_id, description, self._user_context)
    
    def compare_versions(self, project_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two project versions"""
        return self._version_manager.compare_versions(project_id, version1, version2)
    
    def rollback_to_version(self, project_id: str, version_id: str) -> None:
        """Rollback project to specific version"""
        self._version_manager.rollback_to_version(project_id, version_id)
    
    def get_current_version(self, project_id: str) -> str:
        """Get current version ID"""
        return self._version_manager.get_current_version(project_id)