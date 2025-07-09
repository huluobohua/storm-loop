"""
Database models for authentication and authorization
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()


@dataclass
class User:
    """User model with authentication details"""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = ""
    username: str = ""
    password_hash: str = ""
    full_name: Optional[str] = None
    institution: Optional[str] = None
    institution_id: Optional[uuid.UUID] = None
    role: str = "user"
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # OAuth fields
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    
    # Security fields
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verification_token: Optional[str] = None
    
    @classmethod
    async def get_by_id(cls, user_id: str) -> Optional['User']:
        """Get user by ID from database"""
        # Implement database query
        pass
    
    @classmethod
    async def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email from database"""
        # Implement database query
        pass
    
    @classmethod
    async def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username from database"""
        # Implement database query
        pass
    
    async def save(self) -> None:
        """Save user to database"""
        self.updated_at = datetime.now(timezone.utc)
        # Implement database save
        pass
    
    async def delete(self) -> None:
        """Delete user from database"""
        # Implement database delete
        pass
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if token != self.password_reset_token:
            return False
            
        if datetime.now(timezone.utc) > self.password_reset_expires:
            return False
            
        return True
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "institution": self.institution,
            "institution_id": str(self.institution_id) if self.institution_id else None,
            "role": self.role,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "two_factor_enabled": self.two_factor_enabled,
            "oauth_provider": self.oauth_provider
        }
        
        if include_sensitive:
            data["metadata"] = self.metadata
            
        return data


@dataclass
class Session:
    """User session model"""
    id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def refresh(self, extend_by: timedelta = timedelta(days=7)) -> None:
        """Refresh session expiry"""
        self.last_accessed = datetime.now(timezone.utc)
        self.expires_at = datetime.now(timezone.utc) + extend_by


@dataclass  
class ApiKey:
    """API Key model for programmatic access"""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    key_hash: str = ""
    key_prefix: str = ""  # First 8 chars for identification
    permissions: List[str] = field(default_factory=list)
    rate_limit: int = 1000  # Requests per hour
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    allowed_ips: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def generate_key(cls) -> tuple[str, str]:
        """Generate new API key and its hash"""
        key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key, key_hash
    
    @classmethod
    async def verify_key(cls, key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key data"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        # Implement database lookup by key_hash
        # Return key data if valid and active
        pass
    
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def update_last_used(self) -> None:
        """Update last used timestamp"""
        self.last_used = datetime.now(timezone.utc)
    
    def check_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if not self.allowed_ips:
            return True  # No restrictions
        return ip in self.allowed_ips


@dataclass
class Institution:
    """Institution model for multi-tenancy"""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    domain: str = ""  # Email domain for auto-association
    type: str = "university"  # university, company, research_institute
    country: str = ""
    admin_user_id: Optional[uuid.UUID] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)  # Enabled features
    quota: Dict[str, int] = field(default_factory=dict)  # Usage quotas
    billing_plan: str = "free"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # SSO configuration
    sso_enabled: bool = False
    sso_provider: Optional[str] = None
    sso_config: Dict[str, Any] = field(default_factory=dict)
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    
    def check_domain_match(self, email: str) -> bool:
        """Check if email matches institution domain"""
        if not self.domain:
            return False
        return email.endswith(f"@{self.domain}")
    
    def get_quota_remaining(self, resource: str) -> Optional[int]:
        """Get remaining quota for resource"""
        if resource not in self.quota:
            return None  # Unlimited
        # Implement usage tracking
        return self.quota[resource]


@dataclass
class AuditLog:
    """Audit log for security and compliance"""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    action: str = ""
    resource_type: str = ""
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    async def log(
        cls,
        action: str,
        resource_type: str,
        user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Create audit log entry"""
        log_entry = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        # Save to database
        pass