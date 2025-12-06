"""
Firebase Configuration Dialog
Allows users to select Firebase credentials and configure Storage bucket.
"""

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
        layout.addWidget(instructions)
        
        # Configuration Group
        config_group = QGroupBox("Credenciales de Firebase")
        config_layout = QFormLayout()
        
        # Credentials file path
        cred_layout = QHBoxLayout()
        self.credentials_edit = QLineEdit()
        self.credentials_edit.setPlaceholderText("Ruta al archivo JSON de credenciales...")
        self.credentials_edit.setReadOnly(True)
        cred_layout.addWidget(self.credentials_edit)
        
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self._browse_credentials)
        cred_layout.addWidget(browse_btn)
        
        config_layout.addRow("Archivo de Credenciales:", cred_layout)
        
        # Storage bucket
        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("nombre-proyecto.appspot.com")
        config_layout.addRow("Bucket de Storage:", self.bucket_edit)
        
        # Project ID (read-only, auto-filled)
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setReadOnly(True)
        self.project_id_edit.setPlaceholderText("Se autocompletará del archivo JSON")
        config_layout.addRow("Project ID:", self.project_id_edit)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Test connection button
        test_btn = QPushButton("Probar Conexión")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
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
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Credenciales de Firebase",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Validate it's a service account file
            try:
                with open(file_path, 'r') as f:
                    cred_data = json.load(f)
                    
                if cred_data.get('type') != 'service_account':
                    QMessageBox.warning(
                        self,
                        "Archivo Inválido",
                        "El archivo seleccionado no es un archivo de credenciales de "
                        "tipo 'service_account'. Por favor, descargue el archivo correcto "
                        "desde la consola de Firebase."
                    )
                    return
                
                self.credentials_edit.setText(file_path)
                self._update_project_id(file_path)
                
                # Auto-suggest bucket name if empty
                if not self.bucket_edit.text():
                    project_id = cred_data.get('project_id', '')
                    if project_id:
                        self.bucket_edit.setText(f"{project_id}.appspot.com")
                
            except json.JSONDecodeError:
                QMessageBox.warning(
                    self,
                    "Archivo Inválido",
                    "El archivo seleccionado no es un archivo JSON válido."
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error al leer el archivo: {e}"
                )
    
    def _update_project_id(self, credentials_path):
        """Update project ID field from credentials file"""
        try:
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
                project_id = cred_data.get('project_id', '')
                self.project_id_edit.setText(project_id)
        except Exception:
            self.project_id_edit.setText("")
    
    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        credentials_path = self.credentials_edit.text().strip()
        bucket_name = self.bucket_edit.text().strip()
        
        if not credentials_path:
            return False, "Debe seleccionar un archivo de credenciales."
        
        if not os.path.exists(credentials_path):
            return False, "El archivo de credenciales no existe."
        
        if not bucket_name:
            return False, "Debe especificar el nombre del bucket de Storage."
        
        # Validate credentials file
        try:
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
                if cred_data.get('type') != 'service_account':
                    return False, "El archivo debe ser de tipo 'service_account'."
        except Exception as e:
            return False, f"Error al validar credenciales: {e}"
        
        return True, ""
    
    def _save_config(self):
        """Save the Firebase configuration"""
        # Validate
        is_valid, error_msg = self._validate_config()
        if not is_valid:
            QMessageBox.warning(self, "Configuración Inválida", error_msg)
            return
        
        # Save to config
        credentials_path = self.credentials_edit.text().strip()
        bucket_name = self.bucket_edit.text().strip()
        
        try:
            config_manager.set_firebase_config(credentials_path, bucket_name)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "La configuración de Firebase ha sido guardada correctamente.\n\n"
                "Puede usar 'Probar Conexión' para verificar que todo funcione."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar la configuración: {e}"
            )
    
    def _test_connection(self):
        """Test the Firebase connection with current configuration"""
        # Validate first
        is_valid, error_msg = self._validate_config()
        if not is_valid:
            QMessageBox.warning(self, "Configuración Inválida", error_msg)
            return
        
        credentials_path = self.credentials_edit.text().strip()
        bucket_name = self.bucket_edit.text().strip()
        
        try:
            # Try to initialize Firebase with these credentials
            success, msg = firebase_client.initialize_firebase(
                credentials_path,
                bucket_name
            )
            
            if success:
                # Test connection
                client = firebase_client.get_client()
                test_success, test_msg = client.test_connection()
                
                if test_success:
                    QMessageBox.information(
                        self,
                        "Conexión Exitosa",
                        f"✓ Conexión a Firebase exitosa!\n\n{test_msg}\n\n"
                        "La configuración es válida y está lista para usar."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error de Conexión",
                        f"La inicialización fue exitosa pero la conexión falló:\n\n{test_msg}"
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Error de Inicialización",
                    f"No se pudo inicializar Firebase:\n\n{msg}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al probar la conexión:\n\n{e}"
            )


def show_firebase_config_dialog(parent=None):
    """
    Helper function to show the Firebase configuration dialog.
    
    Args:
        parent: Parent widget for the dialog
        
    Returns:
        bool: True if configuration was saved successfully, False otherwise
    """
    dialog = FirebaseConfigDialog(parent)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
