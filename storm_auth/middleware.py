"""
Security middleware for authentication, rate limiting, and request validation
"""

import time
import json
import hashlib
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_429_TOO_MANY_REQUESTS
)

from .auth import JWTAuthManager
from .rbac import PermissionChecker
from .models import User, ApiKey
from .exceptions import AuthenticationError, RateLimitExceeded

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication middleware with multiple auth methods support
    """
    
    def __init__(
        self,
        app,
        jwt_manager: JWTAuthManager,
        permission_checker: PermissionChecker,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.jwt_manager = jwt_manager
        self.permission_checker = permission_checker
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/oauth",
            "/_stcore"  # Streamlit paths
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Try to authenticate request
        auth_result = await self._authenticate_request(request)
        
        if not auth_result:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Attach auth info to request
        request.state.user = auth_result["user"]
        request.state.auth_method = auth_result["method"]
        request.state.permissions = auth_result["permissions"]
        
        # Log authentication
        logger.info(
            f"Authenticated request: user={auth_result['user'].id}, "
            f"method={auth_result['method']}, path={request.url.path}"
        )
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    async def _authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Try multiple authentication methods"""
        
        # 1. JWT Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = self.jwt_manager.verify_token(token)
                user = await User.get_by_id(payload["user_id"])
                if user:
                    return {
                        "user": user,
                        "method": "jwt",
                        "permissions": set(payload.get("permissions", []))
                    }
            except Exception as e:
                logger.warning(f"JWT authentication failed: {e}")
        
        # 2. API Key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_data = await ApiKey.verify_key(api_key)
            if key_data:
                user = await User.get_by_id(key_data["user_id"])
                if user:
                    return {
                        "user": user,
                        "method": "api_key",
                        "permissions": set(key_data.get("permissions", []))
                    }
        
        # 3. Session cookie (for web UI)
        session_id = request.cookies.get("storm_session")
        if session_id:
            # Implement session validation
            pass
        
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with multiple strategies
    """
    
    def __init__(
        self,
        app,
        redis_client=None,
        default_limit: int = 100,
        window_seconds: int = 3600,
        burst_limit: int = 10,
        burst_window: int = 60
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        
        # In-memory fallback if Redis not available
        self.local_counters = defaultdict(list)
        
        # Different limits for different endpoints
        self.endpoint_limits = {
            "/api/v1/research/generate": 10,  # 10 per hour
            "/api/v1/auth/login": 5,  # 5 per hour
            "/api/v1/auth/register": 3,  # 3 per hour
            "/api/v1/export": 20,  # 20 per hour
        }
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self._get_client_id(request)
        endpoint = request.url.path
        
        # Check rate limit
        is_allowed = await self._check_rate_limit(client_id, endpoint)
        
        if not is_allowed:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.window_seconds
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self._get_limit_for_endpoint(endpoint)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds)
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_id, endpoint)
        response.headers["X-RateLimit-Limit"] = str(self._get_limit_for_endpoint(endpoint))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Prefer authenticated user ID
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
    
    def _get_limit_for_endpoint(self, endpoint: str) -> int:
        """Get rate limit for specific endpoint"""
        for path, limit in self.endpoint_limits.items():
            if endpoint.startswith(path):
                return limit
        return self.default_limit
    
    async def _check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check if request is within rate limit"""
        if self.redis:
            return await self._check_redis_rate_limit(client_id, endpoint)
        else:
            return self._check_local_rate_limit(client_id, endpoint)
    
    async def _check_redis_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check rate limit using Redis"""
        key = f"rate_limit:{client_id}:{endpoint}"
        burst_key = f"burst:{client_id}:{endpoint}"
        
        # Check burst limit
        burst_count = await self.redis.incr(burst_key)
        if burst_count == 1:
            await self.redis.expire(burst_key, self.burst_window)
        
        if burst_count > self.burst_limit:
            return False
        
        # Check regular limit
        current_count = await self.redis.incr(key)
        if current_count == 1:
            await self.redis.expire(key, self.window_seconds)
        
        limit = self._get_limit_for_endpoint(endpoint)
        return current_count <= limit
    
    def _check_local_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check rate limit using local memory"""
        now = time.time()
        key = f"{client_id}:{endpoint}"
        
        # Clean old entries
        self.local_counters[key] = [
            timestamp for timestamp in self.local_counters[key]
            if now - timestamp < self.window_seconds
        ]
        
        # Check limit
        limit = self._get_limit_for_endpoint(endpoint)
        if len(self.local_counters[key]) >= limit:
            return False
        
        # Add current request
        self.local_counters[key].append(now)
        return True
    
    async def _get_remaining_requests(self, client_id: str, endpoint: str) -> int:
        """Get remaining requests for client"""
        if self.redis:
            key = f"rate_limit:{client_id}:{endpoint}"
            current = await self.redis.get(key)
            current_count = int(current) if current else 0
            limit = self._get_limit_for_endpoint(endpoint)
            return max(0, limit - current_count)
        else:
            key = f"{client_id}:{endpoint}"
            current_count = len(self.local_counters.get(key, []))
            limit = self._get_limit_for_endpoint(endpoint)
            return max(0, limit - current_count)


class CORSMiddleware(BaseHTTPMiddleware):
    """
    CORS middleware with security considerations
    """
    
    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = True,
        max_age: int = 86400
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["https://storm.yourdomain.com"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID"
        ]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._preflight_response(request)
        
        response = await call_next(request)
        
        # Add CORS headers
        origin = request.headers.get("Origin")
        if origin and self._is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
            response.headers["Vary"] = "Origin"
        
        return response
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins
    
    def _preflight_response(self, request: Request) -> Response:
        """Handle preflight OPTIONS request"""
        headers = {
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Max-Age": str(self.max_age)
        }
        
        origin = request.headers.get("Origin")
        if origin and self._is_allowed_origin(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
        
        return Response(status_code=200, headers=headers)


def require_permission(permission: str):
    """Decorator to require specific permission for endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "user") or not request.state.user:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"error": "Authentication required"}
                )
            
            # Check permission
            user = request.state.user
            has_perm = permission in request.state.permissions
            
            if not has_perm:
                logger.warning(
                    f"Permission denied: user={user.id}, "
                    f"required={permission}, path={request.url.path}"
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": f"Permission '{permission}' required"}
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator