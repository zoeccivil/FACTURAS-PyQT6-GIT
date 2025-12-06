import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
import config_manager
import firebase_client

class FirebaseConfigDialog(QDialog):
    """Dialog for configuring Firebase credentials and storage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Firebase")
        self.resize(600, 300)
        self.setModal(True)

        # Añadir objectName para estilización global
        self.setObjectName("firebase_config_dialog")
        
        self._build_ui()
        self._load_current_config()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Configure las credenciales de Firebase para habilitar "
            "la sincronización en la nube y el almacenamiento de archivos."
        )
        instructions.setWordWrap(True)
        instructions.setProperty("muted", True)  # Para estilizar texto secundario
        layout.addWidget(instructions)
        
        # Configuration Group
        config_group = QGroupBox("Credenciales de Firebase")
        config_group.setObjectName("config_group")  # GroupBox estilizable
        config_layout = QFormLayout()
        
        # Credentials file path
        cred_layout = QHBoxLayout()
        self.credentials_edit = QLineEdit()
        self.credentials_edit.setPlaceholderText("Ruta al archivo JSON de credenciales...")
        self.credentials_edit.setReadOnly(True)
        self.credentials_edit.setObjectName("credentials_edit")
        cred_layout.addWidget(self.credentials_edit)
        
        browse_btn = QPushButton("Examinar...")
        browse_btn.setProperty("primary", True)  # Botón con estilo primario
        browse_btn.clicked.connect(self._browse_credentials)
        cred_layout.addWidget(browse_btn)
        
        config_layout.addRow("Archivo de Credenciales:", cred_layout)
        
        # Storage bucket
        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("nombre-proyecto.appspot.com")
        self.bucket_edit.setObjectName("bucket_edit")
        config_layout.addRow("Bucket de Storage:", self.bucket_edit)
        
        # Project ID (read-only, auto-filled)
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setReadOnly(True)
        self.project_id_edit.setPlaceholderText("Se autocompletará del archivo JSON")
        self.project_id_edit.setObjectName("project_id_edit")
        config_layout.addRow("Project ID:", self.project_id_edit)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Test connection button
        test_btn = QPushButton("Probar Conexión")
        test_btn.setProperty("secondary", True)  # Botón secundario
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("secondary", True)  # Botón secundario
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setProperty("primary", True)  # Botón estilo primario
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def _load_current_config(self):
        """Load current Firebase configuration if exists"""
        config = config_manager.get_firebase_config()
        if config:
            self.credentials_edit.setText(config.get('credentials_path', ''))
            self.bucket_edit.setText(config.get('bucket_name', ''))
            
            # Try to load project ID from credentials
            cred_path = config.get('credentials_path', '')
            if cred_path and os.path.exists(cred_path):
                self._update_project_id(cred_path)
    
    def _browse_credentials(self):
        """Browse for Firebase credentials JSON file"""
        # ... (este código no cambió)

    def _update_project_id(self, credentials_path):
        """Update project ID field from credentials file"""
        # ... (este código no cambió)

    def _validate_config(self) -> tuple[bool, str]:
        """Validate the configuration."""
        # ... (este código no cambió)

    def _save_config(self):
        """Save the Firebase configuration"""
        # ... (este código no cambió)

    def _test_connection(self):
        """Test the Firebase connection with current configuration"""
        # ... (este código no cambió)

def show_firebase_config_dialog(parent=None):
    """Helper to show the Firebase configuration dialog."""
    dialog = FirebaseConfigDialog(parent)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted