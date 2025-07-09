"""
Storm Authentication and Security Module

Production-grade authentication system with JWT tokens, OAuth integration,
and role-based access control (RBAC) for academic research platform.
"""

from .auth import JWTAuthManager, OAuthProvider
from .rbac import RoleManager, Permission
from .middleware import AuthMiddleware, RateLimitMiddleware
from .models import User, Session, ApiKey

__all__ = [
    "JWTAuthManager",
    "OAuthProvider", 
    "RoleManager",
    "Permission",
    "AuthMiddleware",
    "RateLimitMiddleware",
    "User",
    "Session",
    "ApiKey"
]

__version__ = "1.0.0"