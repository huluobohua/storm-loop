"""
Role-Based Access Control (RBAC) System
"""

from enum import Enum
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
import fnmatch
import logging

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""
    # Research permissions
    RESEARCH_CREATE = "research:create"
    RESEARCH_READ = "research:read"
    RESEARCH_UPDATE = "research:update"
    RESEARCH_DELETE = "research:delete"
    RESEARCH_PUBLISH = "research:publish"
    RESEARCH_SHARE = "research:share"
    
    # Article permissions
    ARTICLE_CREATE = "article:create"
    ARTICLE_READ = "article:read"
    ARTICLE_UPDATE = "article:update"
    ARTICLE_DELETE = "article:delete"
    ARTICLE_EXPORT = "article:export"
    
    # API permissions
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # User management
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"
    
    # Institution management
    INSTITUTION_READ = "institution:read"
    INSTITUTION_UPDATE = "institution:update"
    INSTITUTION_ADMIN = "institution:admin"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_CONFIG = "system:config"


@dataclass
class Role:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional[List[str]] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions


class RoleManager:
    """Manage roles and permissions"""
    
    # Default system roles
    DEFAULT_ROLES = {
        "guest": Role(
            name="guest",
            description="Unauthenticated user with minimal read access",
            permissions={
                Permission.RESEARCH_READ,
                Permission.ARTICLE_READ,
                Permission.API_READ
            }
        ),
        "user": Role(
            name="user",
            description="Regular authenticated user",
            permissions={
                Permission.RESEARCH_CREATE,
                Permission.RESEARCH_READ,
                Permission.RESEARCH_UPDATE,
                Permission.RESEARCH_DELETE,
                Permission.ARTICLE_CREATE,
                Permission.ARTICLE_READ,
                Permission.ARTICLE_UPDATE,
                Permission.ARTICLE_DELETE,
                Permission.ARTICLE_EXPORT,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.USER_READ,
                Permission.USER_UPDATE
            },
            inherits_from=["guest"]
        ),
        "researcher": Role(
            name="researcher",
            description="Academic researcher with advanced features",
            permissions={
                Permission.RESEARCH_PUBLISH,
                Permission.RESEARCH_SHARE,
                Permission.INSTITUTION_READ
            },
            inherits_from=["user"]
        ),
        "institution_admin": Role(
            name="institution_admin",
            description="Institution administrator",
            permissions={
                Permission.USER_ADMIN,
                Permission.INSTITUTION_UPDATE,
                Permission.INSTITUTION_ADMIN,
                Permission.SYSTEM_MONITOR
            },
            inherits_from=["researcher"]
        ),
        "system_admin": Role(
            name="system_admin",
            description="System administrator with full access",
            permissions={
                Permission.SYSTEM_ADMIN,
                Permission.SYSTEM_CONFIG,
                Permission.API_ADMIN
            },
            inherits_from=["institution_admin"]
        )
    }
    
    def __init__(self):
        self.roles = self.DEFAULT_ROLES.copy()
        self._resolve_inheritance()
        
    def _resolve_inheritance(self):
        """Resolve permission inheritance between roles"""
        for role_name, role in self.roles.items():
            if role.inherits_from:
                inherited_permissions = set()
                for parent_role_name in role.inherits_from:
                    if parent_role_name in self.roles:
                        parent_role = self.roles[parent_role_name]
                        inherited_permissions.update(parent_role.permissions)
                role.permissions.update(inherited_permissions)
    
    def add_role(self, role: Role):
        """Add custom role"""
        self.roles[role.name] = role
        self._resolve_inheritance()
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name"""
        return self.roles.get(name)
    
    def check_permission(
        self,
        role_name: str,
        permission: Permission,
        resource_context: Optional[Dict] = None
    ) -> bool:
        """Check if role has permission, optionally with resource context"""
        role = self.get_role(role_name)
        if not role:
            return False
            
        # Basic permission check
        if not role.has_permission(permission):
            return False
            
        # Resource-based access control (if context provided)
        if resource_context:
            return self._check_resource_access(role_name, permission, resource_context)
            
        return True
    
    def _check_resource_access(
        self,
        role_name: str,
        permission: Permission,
        context: Dict
    ) -> bool:
        """
        Check resource-based access control
        Example: User can only edit their own resources
        """
        # Owner check
        if context.get("owner_id") and context.get("user_id"):
            if context["owner_id"] != context["user_id"]:
                # Check if user has admin permission
                admin_permission = Permission(permission.value.split(":")[0] + ":admin")
                role = self.get_role(role_name)
                if not role or not role.has_permission(admin_permission):
                    return False
                    
        # Institution check
        if context.get("institution_id") and context.get("user_institution_id"):
            if context["institution_id"] != context["user_institution_id"]:
                # Check if user has cross-institution permission
                if role_name not in ["system_admin"]:
                    return False
                    
        return True
    
    def get_role_permissions(self, role_name: str) -> Set[str]:
        """Get all permissions for a role as strings"""
        role = self.get_role(role_name)
        if not role:
            return set()
        return {p.value for p in role.permissions}


class PermissionChecker:
    """
    Utility class for permission checking with caching
    """
    
    def __init__(self, role_manager: RoleManager):
        self.role_manager = role_manager
        self._cache = {}
        
    def has_permission(
        self,
        user_role: str,
        permission: str,
        resource_context: Optional[Dict] = None
    ) -> bool:
        """Check if user has permission (with caching)"""
        cache_key = f"{user_role}:{permission}:{hash(frozenset(resource_context.items())) if resource_context else 'no-context'}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            perm_enum = Permission(permission)
            result = self.role_manager.check_permission(user_role, perm_enum, resource_context)
            self._cache[cache_key] = result
            return result
        except ValueError:
            logger.warning(f"Invalid permission requested: {permission}")
            return False
    
    def has_any_permission(
        self,
        user_role: str,
        permissions: List[str],
        resource_context: Optional[Dict] = None
    ) -> bool:
        """Check if user has any of the given permissions"""
        return any(
            self.has_permission(user_role, perm, resource_context)
            for perm in permissions
        )
    
    def has_all_permissions(
        self,
        user_role: str,
        permissions: List[str],
        resource_context: Optional[Dict] = None
    ) -> bool:
        """Check if user has all of the given permissions"""
        return all(
            self.has_permission(user_role, perm, resource_context)
            for perm in permissions
        )
    
    def clear_cache(self):
        """Clear permission cache"""
        self._cache.clear()


class ResourceAccessPolicy:
    """
    Define access policies for resources
    """
    
    def __init__(self):
        self.policies = {}
        
    def add_policy(self, resource_type: str, policy_name: str, policy_func):
        """Add access policy for resource type"""
        if resource_type not in self.policies:
            self.policies[resource_type] = {}
        self.policies[resource_type][policy_name] = policy_func
        
    def check_access(
        self,
        resource_type: str,
        policy_name: str,
        context: Dict
    ) -> bool:
        """Check if access is allowed by policy"""
        if resource_type not in self.policies:
            return True  # No policy means allow
            
        if policy_name not in self.policies[resource_type]:
            return True
            
        policy_func = self.policies[resource_type][policy_name]
        return policy_func(context)


# Example policies
def owner_only_policy(context: Dict) -> bool:
    """Only resource owner can access"""
    return context.get("user_id") == context.get("resource_owner_id")


def institution_members_policy(context: Dict) -> bool:
    """Only institution members can access"""
    return context.get("user_institution_id") == context.get("resource_institution_id")


def public_read_policy(context: Dict) -> bool:
    """Anyone can read, only owner can write"""
    if context.get("action") == "read":
        return True
    return owner_only_policy(context)