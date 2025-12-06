"""
Firebase Configuration Dialog
Modern dialog for configuring Firebase settings.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QMessageBox, QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt


def show_firebase_config_dialog(parent):
    """
    Show Firebase configuration dialog.
    This is a placeholder implementation for the modern UI integration.
    """
    dialog = FirebaseConfigDialog(parent)
    result = dialog.exec()
    
    # If configuration was saved and parent has callback, call it
    if result == QDialog.DialogCode.Accepted:
        if hasattr(parent, 'controller') and hasattr(parent.controller, 'on_firebase_config_updated'):
            try:
                parent.controller.on_firebase_config_updated()
            except Exception as e:
                print(f"Error calling on_firebase_config_updated: {e}")
    
    return result


class FirebaseConfigDialog(QDialog):
    """Modern Firebase Configuration Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Configurar Firebase")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._build_ui()
        self._load_config()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Configuración de Firebase")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Configura las credenciales de Firebase para habilitar la sincronización en la nube.\n"
            "Puedes obtener las credenciales desde la consola de Firebase."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(instructions)
        
        # Credentials group
        creds_group = QGroupBox("Credenciales de Firebase")
        creds_layout = QVBoxLayout()
        
        # JSON credentials file
        json_layout = QHBoxLayout()
        json_layout.addWidget(QLabel("Archivo de credenciales JSON:"))
        self.json_path_edit = QLineEdit()
        self.json_path_edit.setPlaceholderText("Selecciona el archivo de credenciales...")
        json_layout.addWidget(self.json_path_edit, 1)
        
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self._browse_credentials)
        json_layout.addWidget(browse_btn)
        creds_layout.addLayout(json_layout)
        
        # Storage bucket
        bucket_layout = QHBoxLayout()
        bucket_layout.addWidget(QLabel("Storage Bucket:"))
        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("your-project.appspot.com")
        bucket_layout.addWidget(self.bucket_edit, 1)
        creds_layout.addLayout(bucket_layout)
        
        # Project ID
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project ID:"))
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("your-project-id")
        project_layout.addWidget(self.project_edit, 1)
        creds_layout.addLayout(project_layout)
        
        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)
        
        # Test connection group
        test_group = QGroupBox("Probar Conexión")
        test_layout = QVBoxLayout()
        
        test_btn = QPushButton("Probar Conexión a Firebase")
        test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(test_btn)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Estado de la conexión aparecerá aquí...")
        test_layout.addWidget(self.status_text)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Guardar Configuración")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_credentials(self):
        """Browse for credentials JSON file"""
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de credenciales",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if fname:
            self.json_path_edit.setText(fname)
    
    def _load_config(self):
        """Load existing configuration if available"""
        if not hasattr(self.parent, 'controller'):
            return
        
        try:
            controller = self.parent.controller
            if hasattr(controller, 'get_setting'):
                json_path = controller.get_setting('firebase_credentials_path', '')
                bucket = controller.get_setting('firebase_storage_bucket', '')
                project = controller.get_setting('firebase_project_id', '')
                
                if json_path:
                    self.json_path_edit.setText(json_path)
                if bucket:
                    self.bucket_edit.setText(bucket)
                if project:
                    self.project_edit.setText(project)
        except Exception as e:
            print(f"Error loading Firebase config: {e}")
    
    def _save_config(self):
        """Save Firebase configuration"""
        json_path = self.json_path_edit.text().strip()
        bucket = self.bucket_edit.text().strip()
        project = self.project_edit.text().strip()
        
        if not json_path:
            QMessageBox.warning(self, "Configuración incompleta", 
                              "Por favor selecciona el archivo de credenciales JSON.")
            return
        
        # Save to controller settings
        if hasattr(self.parent, 'controller'):
            try:
                controller = self.parent.controller
                if hasattr(controller, 'set_setting'):
                    controller.set_setting('firebase_credentials_path', json_path)
                    controller.set_setting('firebase_storage_bucket', bucket)
                    controller.set_setting('firebase_project_id', project)
                    controller.set_setting('firebase_enabled', 'true')
                    
                    QMessageBox.information(
                        self,
                        "Configuración guardada",
                        "La configuración de Firebase se ha guardado correctamente.\n\n"
                        "Nota: Firebase será utilizado como fuente principal de datos.\n"
                        "Los backups SQL se realizarán automáticamente cada día."
                    )
                    self.accept()
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{e}")
                return
        
        QMessageBox.warning(self, "Error", "No se pudo acceder al controlador para guardar la configuración.")
    
    def _test_connection(self):
        """Test Firebase connection"""
        self.status_text.clear()
        self.status_text.append("Probando conexión a Firebase...\n")
        
        json_path = self.json_path_edit.text().strip()
        
        if not json_path:
            self.status_text.append("❌ Error: No se ha seleccionado archivo de credenciales.")
            return
        
        # Check if file exists
        import os
        if not os.path.exists(json_path):
            self.status_text.append(f"❌ Error: El archivo no existe: {json_path}")
            return
        
        # This is a placeholder - actual Firebase connection would happen here
        self.status_text.append(f"📄 Archivo de credenciales: {json_path}\n")
        self.status_text.append("⚠️  Nota: Esta es una implementación de prueba.\n")
        self.status_text.append("La conexión real a Firebase requiere la instalación del SDK de Firebase:\n")
        self.status_text.append("  pip install firebase-admin\n")
        self.status_text.append("\nPara una integración completa, el controlador debe implementar\n")
        self.status_text.append("los métodos de Firebase (Firestore y Storage).")
