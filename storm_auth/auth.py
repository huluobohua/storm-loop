"""
JWT Authentication Manager with OAuth support
"""

import os
import time
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import jwt
import bcrypt
from cryptography.fernet import Fernet
import httpx
from cachetools import TTLCache
import logging

from .models import User, Session
from .exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    UserNotFoundError,
    InvalidCredentialsError
)

logger = logging.getLogger(__name__)


class JWTAuthManager:
    """
    Production-grade JWT authentication manager with security best practices
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_ttl: int = 3600,  # 1 hour
        refresh_token_ttl: int = 604800,  # 7 days
        enable_token_rotation: bool = True
    ):
        self.secret_key = secret_key or os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
        self.algorithm = algorithm
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        self.enable_token_rotation = enable_token_rotation
        
        # Token blacklist cache (for logout functionality)
        self.blacklist = TTLCache(maxsize=10000, ttl=refresh_token_ttl)
        
        # Encryption for sensitive data
        self.cipher_suite = Fernet(Fernet.generate_key())
        
    def generate_tokens(self, user: User) -> Tuple[str, str]:
        """Generate access and refresh token pair"""
        now = datetime.now(timezone.utc)
        
        # Access token payload
        access_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "exp": now + timedelta(seconds=self.access_token_ttl),
            "iat": now,
            "type": "access",
            "jti": secrets.token_urlsafe(16)  # JWT ID for blacklisting
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": str(user.id),
            "exp": now + timedelta(seconds=self.refresh_token_ttl),
            "iat": now,
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return access_token, refresh_token
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            # Check if token is blacklisted
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("jti") in self.blacklist:
                raise InvalidTokenError("Token has been revoked")
            
            if payload.get("type") != token_type:
                raise InvalidTokenError(f"Expected {token_type} token")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """Generate new token pair from refresh token"""
        payload = self.verify_token(refresh_token, token_type="refresh")
        
        # Blacklist old refresh token
        self.blacklist[payload["jti"]] = True
        
        # Get user and generate new tokens
        user = User.get_by_id(payload["user_id"])
        if not user:
            raise UserNotFoundError("User not found")
            
        return self.generate_tokens(user)
    
    def revoke_token(self, token: str) -> None:
        """Revoke a token by adding to blacklist"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.blacklist[payload["jti"]] = True
        except jwt.InvalidTokenError:
            pass  # Already invalid
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like API keys"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted.encode()).decode()


class OAuthProvider:
    """
    OAuth 2.0 integration for institutional SSO
    """
    
    SUPPORTED_PROVIDERS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v1/userinfo",
            "scopes": ["openid", "email", "profile"]
        },
        "microsoft": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile", "User.Read"]
        },
        "saml": {
            # SAML configuration for institutional SSO
            "metadata_url": os.environ.get("SAML_METADATA_URL", ""),
            "entity_id": os.environ.get("SAML_ENTITY_ID", "storm-academic")
        }
    }
    
    def __init__(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
            
        self.provider = provider
        self.config = self.SUPPORTED_PROVIDERS[provider]
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.client = httpx.AsyncClient()
        
    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.get("scopes", [])),
            "state": state,
            "access_type": "offline",  # For refresh tokens
            "prompt": "consent"
        }
        
        if self.provider == "google":
            params["include_granted_scopes"] = "true"
            
        from urllib.parse import urlencode
        return f"{self.config['auth_url']}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        response = await self.client.post(self.config["token_url"], data=data)
        response.raise_for_status()
        
        return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = await self.client.get(self.config["userinfo_url"], headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        
        # Normalize user data across providers
        normalized = {
            "id": user_data.get("id") or user_data.get("sub"),
            "email": user_data.get("email") or user_data.get("mail"),
            "name": user_data.get("name") or user_data.get("displayName"),
            "picture": user_data.get("picture") or user_data.get("photo"),
            "provider": self.provider
        }
        
        return normalized
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class SessionManager:
    """
    Secure session management with Redis backend
    """
    
    def __init__(self, redis_client, session_ttl: int = 86400):
        self.redis = redis_client
        self.session_ttl = session_ttl
        
    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> str:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata
        }
        
        await self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session_data)
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
            
        session = json.loads(data)
        
        # Update last accessed time
        session["last_accessed"] = datetime.now(timezone.utc).isoformat()
        await self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session)
        )
        
        return session
    
    async def destroy_session(self, session_id: str) -> None:
        """Destroy session"""
        await self.redis.delete(f"session:{session_id}")
    
    async def destroy_all_user_sessions(self, user_id: str) -> None:
        """Destroy all sessions for a user"""
        # This requires maintaining a user->sessions index
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match="session:*",
                count=100
            )
            
            for key in keys:
                session_data = await self.redis.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session.get("user_id") == user_id:
                        await self.redis.delete(key)
                        
            if cursor == 0:
                break