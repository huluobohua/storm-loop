"""
Custom exceptions for authentication and authorization
"""


class StormAuthException(Exception):
    """Base exception for authentication system"""
    pass


class AuthenticationError(StormAuthException):
    """General authentication error"""
    pass


class AuthorizationError(StormAuthException):
    """General authorization error"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class InvalidTokenError(AuthenticationError):
    """Invalid JWT token"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username/password"""
    pass


class UserNotFoundError(AuthenticationError):
    """User not found in database"""
    pass


class UserInactiveError(AuthenticationError):
    """User account is inactive"""
    pass


class UserNotVerifiedError(AuthenticationError):
    """User email not verified"""
    pass


class PermissionDeniedError(AuthorizationError):
    """User lacks required permission"""
    pass


class RateLimitExceeded(StormAuthException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 3600):
        super().__init__(message)
        self.retry_after = retry_after


class InvalidApiKeyError(AuthenticationError):
    """Invalid API key"""
    pass


class ApiKeyExpiredError(AuthenticationError):
    """API key has expired"""
    pass


class InstitutionQuotaExceeded(AuthorizationError):
    """Institution quota exceeded"""
    def __init__(self, resource: str, limit: int):
        super().__init__(f"Quota exceeded for {resource}: limit {limit}")
        self.resource = resource
        self.limit = limit


class OAuthError(AuthenticationError):
    """OAuth authentication error"""
    pass


class TwoFactorRequired(AuthenticationError):
    """Two-factor authentication required"""
    pass


class InvalidTwoFactorCode(AuthenticationError):
    """Invalid two-factor authentication code"""
    pass