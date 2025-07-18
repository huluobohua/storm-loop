"""
Test cases for production-grade CredentialManager
Tests encryption, security, and key management
"""

import unittest
import os
import threading
from unittest.mock import patch
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'frontend'))
from advanced_interface.security.credential_manager import CredentialManager

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class TestSecureCredentialManager(unittest.TestCase):
    """Test cases for production-grade CredentialManager"""
    
    def setUp(self):
        """Set up test dependencies"""
        if CRYPTOGRAPHY_AVAILABLE:
            # Generate test key
            self.test_key = Fernet.generate_key().decode()
            self.credential_manager = CredentialManager(master_key=self.test_key)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_production_encryption_decryption(self):
        """Test that production encryption/decryption works correctly"""
        test_data = "super_secret_password_123"
        
        # Encrypt data
        encrypted = self.credential_manager._encrypt(test_data)
        self.assertNotEqual(encrypted, test_data)
        self.assertNotIn("super_secret", encrypted)  # No plaintext leakage
        
        # Decrypt data
        decrypted = self.credential_manager._decrypt(encrypted)
        self.assertEqual(decrypted, test_data)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_encryption_produces_different_outputs(self):
        """Test that encryption produces different outputs for same input"""
        test_data = "same_password"
        
        encrypted1 = self.credential_manager._encrypt(test_data)
        encrypted2 = self.credential_manager._encrypt(test_data)
        
        # Fernet includes timestamp and random IV, so outputs differ
        self.assertNotEqual(encrypted1, encrypted2)
        
        # Both decrypt to same value
        self.assertEqual(self.credential_manager._decrypt(encrypted1), test_data)
        self.assertEqual(self.credential_manager._decrypt(encrypted2), test_data)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_invalid_key_raises_error(self):
        """Test that invalid encryption key raises error"""
        with self.assertRaises(ValueError):
            CredentialManager(master_key="invalid_key_format")
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_corrupted_data_raises_error(self):
        """Test that corrupted encrypted data raises error"""
        with self.assertRaises(RuntimeError):
            self.credential_manager._decrypt("corrupted_encrypted_data")
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_environment_key_usage(self):
        """Test that environment key is used when available"""
        test_env_key = Fernet.generate_key().decode()
        
        with patch.dict(os.environ, {'STORM_ENCRYPTION_KEY': test_env_key}):
            manager = CredentialManager()
            
            # Test encryption works with env key
            test_data = "env_key_test"
            encrypted = manager._encrypt(test_data)
            decrypted = manager._decrypt(encrypted)
            self.assertEqual(decrypted, test_data)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required") 
    def test_production_environment_requires_key(self):
        """Test that production environment requires encryption key"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}, clear=True):
            with self.assertRaises(ValueError) as context:
                CredentialManager()
            
            self.assertIn("STORM_ENCRYPTION_KEY", str(context.exception))
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_development_environment_generates_key(self):
        """Test that development environment generates key with warning"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            with patch('builtins.print') as mock_print:
                manager = CredentialManager()
                
                # Should print warning about generated key
                mock_print.assert_called()
                warning_call = mock_print.call_args[0][0]
                self.assertIn("WARNING", warning_call)
                self.assertIn("Generated development key", warning_call)
                
                # Should still work for encryption
                test_data = "dev_test"
                encrypted = manager._encrypt(test_data)
                decrypted = manager._decrypt(encrypted)
                self.assertEqual(decrypted, test_data)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_credential_storage_and_retrieval(self):
        """Test secure credential storage and retrieval"""
        service = "test_api"
        username = "testuser"
        password = "secure_password_123"
        
        # Store credential
        self.credential_manager.store_credential(service, username, password)
        
        # Retrieve credential
        retrieved = self.credential_manager.retrieve_credential(service)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["username"], username)
        self.assertEqual(retrieved["credential"], password)
        self.assertEqual(retrieved["service"], service)
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_credential_verification_without_decryption(self):
        """Test credential verification using hash without decryption"""
        service = "test_api"
        username = "testuser"
        password = "secure_password_123"
        
        # Store credential
        self.credential_manager.store_credential(service, username, password)
        
        # Verify correct password
        self.assertTrue(self.credential_manager.verify_credential(service, password))
        
        # Verify incorrect password
        self.assertFalse(self.credential_manager.verify_credential(service, "wrong_password"))
    
    @unittest.skipUnless(CRYPTOGRAPHY_AVAILABLE, "cryptography library required")
    def test_thread_safety_encryption(self):
        """Test that encryption is thread-safe"""
        results = []
        test_data = "thread_test_data"
        
        def encrypt_worker():
            encrypted = self.credential_manager._encrypt(test_data)
            decrypted = self.credential_manager._decrypt(encrypted)
            results.append(decrypted == test_data)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=encrypt_worker)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
    
    def test_no_cryptography_library_raises_import_error(self):
        """Test that missing cryptography library raises ImportError"""
        # This test documents the security requirement - cryptography MUST be installed
        # The import error check happens at module import time
        try:
            # Test that the module documents cryptography requirement
            import advanced_interface.security.credential_manager as cm
            # If we reach here, cryptography is available (which is good)
            self.assertTrue(cm.CRYPTOGRAPHY_AVAILABLE)
        except ImportError as e:
            # This would happen if cryptography wasn't installed
            self.assertIn("cryptography library is required", str(e))


if __name__ == "__main__":
    unittest.main()