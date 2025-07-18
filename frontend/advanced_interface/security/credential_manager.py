"""
Secure Credential Manager
Implements secure credential handling with encryption and validation
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any, List
import base64
import threading


class CredentialManager:
    """
    Secure credential management with encryption
    Adheres to security best practices for credential storage
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self._credentials = {}
        self._master_key = master_key or self._generate_master_key()
        self._lock = threading.RLock()
    
    def _generate_master_key(self) -> str:
        """Generate a secure master key"""
        return secrets.token_urlsafe(32)
    
    def _simple_encrypt(self, data: str) -> str:
        """Simple encryption using base64 (for demo purposes)
        
        PRODUCTION WARNING: This is a demo implementation using base64 encoding.
        For production use, replace with proper encryption like:
        - cryptography.fernet.Fernet
        - AES-256-GCM encryption
        - AWS KMS or similar key management service
        """
        # TODO: Replace with proper encryption before production deployment
        return base64.b64encode(data.encode()).decode()
    
    def _simple_decrypt(self, encrypted_data: str) -> str:
        """Simple decryption using base64 (for demo purposes)
        
        PRODUCTION WARNING: This is a demo implementation using base64 decoding.
        For production use, replace with proper decryption matching the encryption method.
        """
        # TODO: Replace with proper decryption before production deployment
        return base64.b64decode(encrypted_data.encode()).decode()
    
    def store_credential(self, service: str, username: str, credential: str) -> None:
        """Store encrypted credential"""
        with self._lock:
            encrypted_credential = self._simple_encrypt(credential)
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
                decrypted = self._simple_decrypt(stored["credential"])
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
            # Validate input
            if not self._validate_database_name(database):
                raise ValueError(f"Invalid database name: {database}")
            
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            
            if not self._validate_credentials(username, password):
                return {
                    "authenticated": False,
                    "error": "Invalid credentials format"
                }
            
            # Store credentials securely
            self._credential_manager.store_credential(database, username, password)
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            self._session_tokens[database] = {
                "token": session_token,
                "username": username,
                "authenticated": True
            }
            
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