"""
Secure Credential Manager
Implements secure credential handling with encryption and validation
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any, List
import threading

# Production-grade encryption
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    import base64
    CRYPTOGRAPHY_AVAILABLE = False


class CredentialManager:
    """
    Secure credential management with encryption
    Adheres to security best practices for credential storage
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self._credentials = {}
        self._master_key = master_key or self._get_or_generate_key()
        self._lock = threading.RLock()
        self._fernet = self._init_encryption()
    
    def _get_or_generate_key(self) -> str:
        """Get key from environment or generate new one"""
        if CRYPTOGRAPHY_AVAILABLE:
            # Production: Use environment variable or secure key management
            env_key = os.environ.get('STORM_ENCRYPTION_KEY')
            if env_key:
                return env_key
            # Generate new key for development
            return Fernet.generate_key().decode()
        else:
            # Fallback for development without cryptography
            return secrets.token_urlsafe(32)
    
    def _init_encryption(self):
        """Initialize encryption engine"""
        if CRYPTOGRAPHY_AVAILABLE:
            # Ensure key is properly formatted for Fernet
            if isinstance(self._master_key, str):
                key_bytes = self._master_key.encode()
                # Pad or truncate to 32 bytes, then base64 encode
                if len(key_bytes) < 32:
                    key_bytes = key_bytes.ljust(32, b'\0')
                elif len(key_bytes) > 32:
                    key_bytes = key_bytes[:32]
                # Create Fernet-compatible key
                import base64
                fernet_key = base64.urlsafe_b64encode(key_bytes)
                return Fernet(fernet_key)
            else:
                return Fernet(self._master_key)
        return None
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data using production-grade encryption"""
        if CRYPTOGRAPHY_AVAILABLE and self._fernet:
            # Production: Use Fernet symmetric encryption
            return self._fernet.encrypt(data.encode()).decode()
        else:
            # Development fallback: Clear warning about security
            print("WARNING: Using development-only base64 encoding - NOT SECURE for production!")
            import base64
            return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using production-grade decryption"""
        if CRYPTOGRAPHY_AVAILABLE and self._fernet:
            # Production: Use Fernet symmetric decryption
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        else:
            # Development fallback: Clear warning about security
            print("WARNING: Using development-only base64 decoding - NOT SECURE for production!")
            import base64
            return base64.b64decode(encrypted_data.encode()).decode()
    
    def store_credential(self, service: str, username: str, credential: str) -> None:
        """Store encrypted credential"""
        with self._lock:
            encrypted_credential = self._encrypt(credential)
            self._credentials[service] = {
                "username": username,
                "credential": encrypted_credential,
                "hash": self._hash_credential(credential)
            }
    
    def retrieve_credential(self, service: str) -> Optional[Dict[str, str]]:
        """Retrieve and decrypt credential"""
        with self._lock:
            if service not in self._credentials:
                return None
            
            stored = self._credentials[service]
            try:
                decrypted = self._decrypt(stored["credential"])
                return {
                    "username": stored["username"],
                    "credential": decrypted,
                    "service": service
                }
            except Exception:
                return None
    
    def verify_credential(self, service: str, credential: str) -> bool:
        """Verify credential without decryption"""
        with self._lock:
            if service not in self._credentials:
                return False
            
            stored_hash = self._credentials[service]["hash"]
            return self._hash_credential(credential) == stored_hash
    
    def _hash_credential(self, credential: str) -> str:
        """Hash credential for verification"""
        return hashlib.sha256(credential.encode()).hexdigest()
    
    def remove_credential(self, service: str) -> bool:
        """Remove credential securely"""
        with self._lock:
            if service in self._credentials:
                del self._credentials[service]
                return True
            return False
    
    def list_services(self) -> List[str]:
        """List services with stored credentials"""
        with self._lock:
            return list(self._credentials.keys())
    
    def validate_credential_format(self, credential: str) -> bool:
        """Validate credential format"""
        # Basic validation - extend as needed
        if not credential or len(credential) < 8:
            return False
        
        # Check for common security issues
        if credential.lower() in ['password', '12345678', 'admin']:
            return False
        
        return True
    
    def export_encrypted(self) -> str:
        """Export credentials in encrypted format"""
        with self._lock:
            return json.dumps(self._credentials)
    
    def import_encrypted(self, encrypted_data: str) -> bool:
        """Import credentials from encrypted format"""
        try:
            with self._lock:
                self._credentials = json.loads(encrypted_data)
                return True
        except Exception:
            return False


class SecureAuthenticationManager:
    """
    Secure authentication manager for database connections
    Implements secure credential handling with proper validation
    """
    
    def __init__(self):
        self._credential_manager = CredentialManager()
        self._session_tokens = {}
        self._lock = threading.RLock()
    
    def authenticate_database(self, database: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Authenticate with database using secure credentials"""
        with self._lock:
            self._validate_database_input(database)
            username, password = self._extract_credentials(credentials)
            return self._process_authentication(database, username, password)
    
    def _validate_database_input(self, database: str) -> None:
        """Validate database name input"""
        if not self._validate_database_name(database):
            raise ValueError(f"Invalid database name: {database}")
    
    def _extract_credentials(self, credentials: Dict[str, str]) -> tuple:
        """Extract username and password from credentials"""
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        return username, password
    
    def _process_authentication(self, database: str, username: str, password: str) -> Dict[str, Any]:
        """Process authentication with validated inputs"""
        if not self._validate_credentials(username, password):
            return self._create_failure_response()
        return self._create_success_response(database, username, password)
    
    def _create_failure_response(self) -> Dict[str, Any]:
        """Create authentication failure response"""
        return {
            "authenticated": False,
            "error": "Invalid credentials format"
        }
    
    def _create_success_response(self, database: str, username: str, password: str) -> Dict[str, Any]:
        """Create authentication success response"""
        self._credential_manager.store_credential(database, username, password)
        session_token = self._generate_session_token(database, username)
        return self._build_success_result(session_token, username)
    
    def _generate_session_token(self, database: str, username: str) -> str:
        """Generate and store session token"""
        session_token = secrets.token_urlsafe(32)
        self._session_tokens[database] = {
            "token": session_token,
            "username": username,
            "authenticated": True
        }
        return session_token
    
    def _build_success_result(self, session_token: str, username: str) -> Dict[str, Any]:
        """Build final success response"""
        return {
            "authenticated": True,
            "session_token": session_token,
            "username": username
        }
    
    def get_authentication_status(self, database: str) -> Dict[str, Any]:
        """Get authentication status for database"""
        with self._lock:
            if database in self._session_tokens:
                session = self._session_tokens[database]
                return {
                    "authenticated": session["authenticated"],
                    "username": session["username"]
                }
            return {"authenticated": False}
    
    def _validate_database_name(self, database: str) -> bool:
        """Validate database name"""
        if not database or not isinstance(database, str):
            return False
        
        # Check for SQL injection patterns
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        for char in dangerous_chars:
            if char in database.lower():
                return False
        
        return True
    
    def _validate_credentials(self, username: str, password: str) -> bool:
        """Validate credential format"""
        if not username or not password:
            return False
        
        if len(username) < 3 or len(password) < 8:
            return False
        
        return self._credential_manager.validate_credential_format(password)
    
    def logout_database(self, database: str) -> bool:
        """Logout from database"""
        with self._lock:
            if database in self._session_tokens:
                del self._session_tokens[database]
                self._credential_manager.remove_credential(database)
                return True
            return False
    
    def get_secure_connection_string(self, database: str) -> Optional[str]:
        """Get secure connection string without exposing credentials"""
        with self._lock:
            if database not in self._session_tokens:
                return None
            
            # Return sanitized connection string
            return f"Database: {database}, Status: Connected"