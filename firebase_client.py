"""
Firebase Client Module
Provides centralized Firebase access for Firestore and Storage operations.
"""

import os
import json
from typing import Optional, Dict, Any
import threading
import firebase_admin
from firebase_admin import credentials, firestore, storage
import config_manager


class FirebaseClient:
    """Singleton client for Firebase operations (thread-safe)"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase client (singleton pattern)"""
        if not self._initialized:
            self.app = None
            self.db = None
            self.bucket = None
            self._initialized = True
    
    def initialize(self, credentials_path: str = None, bucket_name: str = None) -> tuple[bool, str]:
        """
        Initialize Firebase with credentials.
        
        Args:
            credentials_path: Path to service account JSON file
            bucket_name: Firebase Storage bucket name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get config if not provided
            if not credentials_path or not bucket_name:
                config = config_manager.get_firebase_config()
                if not config:
                    return False, "No hay configuración de Firebase. Use 'Configuración Firebase' primero."
                credentials_path = config.get('credentials_path')
                bucket_name = config.get('bucket_name')
            
            if not credentials_path or not os.path.exists(credentials_path):
                return False, f"Archivo de credenciales no encontrado: {credentials_path}"
            
            # Validate credentials file
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
                if cred_data.get('type') != 'service_account':
                    return False, "El archivo debe ser de tipo 'service_account'"
            
            # Initialize Firebase Admin if not already done
            if not self.app:
                cred = credentials.Certificate(credentials_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
            
            # Get Firestore and Storage references
            self.db = firestore.client()
            self.bucket = storage.bucket()
            
            return True, "Firebase inicializado correctamente"
            
        except ValueError as e:
            if "already exists" in str(e):
                # Already initialized, get references
                self.db = firestore.client()
                self.bucket = storage.bucket()
                return True, "Firebase ya estaba inicializado"
            return False, f"Error de inicialización: {e}"
        except Exception as e:
            return False, f"Error al inicializar Firebase: {e}"
    
    def is_available(self) -> bool:
        """Check if Firebase is initialized and available"""
        return self.db is not None
    
    def get_firestore(self):
        """Get Firestore client instance"""
        if not self.is_available():
            success, msg = self.initialize()
            if not success:
                raise RuntimeError(f"Firebase no disponible: {msg}")
        return self.db
    
    def get_storage(self):
        """Get Storage bucket instance"""
        if not self.bucket:
            success, msg = self.initialize()
            if not success:
                raise RuntimeError(f"Firebase Storage no disponible: {msg}")
        return self.bucket
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test Firebase connection by attempting to read from Firestore.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.is_available():
                return False, "Firebase no está inicializado"
            
            # Try to list collections (lightweight operation)
            collections = list(self.db.collections(page_size=1))
            return True, f"Conexión exitosa. Colecciones disponibles: {len(collections)}"
            
        except Exception as e:
            return False, f"Error de conexión: {e}"


# Global instance
_firebase_client = FirebaseClient()


def get_client() -> FirebaseClient:
    """Get the global Firebase client instance"""
    return _firebase_client


def initialize_firebase(credentials_path: str = None, bucket_name: str = None) -> tuple[bool, str]:
    """
    Initialize Firebase with credentials.
    Convenience function that uses the global client.
    """
    return _firebase_client.initialize(credentials_path, bucket_name)


def is_firebase_available() -> bool:
    """Check if Firebase is initialized and available"""
    return _firebase_client.is_available()


def get_firestore():
    """Get Firestore client instance (raises RuntimeError if not available)"""
    return _firebase_client.get_firestore()


def get_storage():
    """Get Storage bucket instance (raises RuntimeError if not available)"""
    return _firebase_client.get_storage()
