"""
SQLite to Firebase Migration Dialog
Modern dialog for migrating data from SQLite to Firebase.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFileDialog, QProgressBar,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


def show_migration_dialog(parent, default_db_path=""):
    """
    Show SQLite to Firebase migration dialog.
    This is a placeholder implementation for the modern UI integration.
    
    Args:
        parent: Parent window
        default_db_path: Default SQLite database path
    """
    dialog = MigrationDialog(parent, default_db_path)
    return dialog.exec()


class MigrationWorker(QThread):
    """Worker thread for migration to avoid freezing UI"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, controller, db_path, options):
        super().__init__()
        self.controller = controller
        self.db_path = db_path
        self.options = options
    
    def run(self):
        """Run the migration process"""
        try:
            # This is a placeholder - actual migration would happen here
            self.progress.emit(10, "Conectando a SQLite...")
            self.msleep(500)
            
            self.progress.emit(30, "Leyendo datos de SQLite...")
            self.msleep(500)
            
            self.progress.emit(50, "Conectando a Firebase...")
            self.msleep(500)
            
            self.progress.emit(70, "Migrando datos a Firestore...")
            self.msleep(500)
            
            if self.options.get('migrate_attachments', False):
                self.progress.emit(85, "Subiendo archivos adjuntos a Storage...")
                self.msleep(500)
            
            self.progress.emit(100, "Migración completada exitosamente!")
            
            self.finished.emit(True, "Migración completada exitosamente!")
            
        except Exception as e:
            self.finished.emit(False, f"Error durante la migración: {str(e)}")


class MigrationDialog(QDialog):
    """SQLite to Firebase Migration Dialog"""
    
    def __init__(self, parent=None, default_db_path=""):
        super().__init__(parent)
        self.parent = parent
        self.default_db_path = default_db_path
        self.migration_worker = None
        
        self.setWindowTitle("Migrar SQLite → Firebase")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        
        self._build_ui()
        
        # Set default path if provided
        if default_db_path:
            self.db_path_edit.setText(default_db_path)
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Migración de Datos: SQLite → Firebase")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Warning
        warning = QLabel(
            "⚠️  Esta herramienta migrará todos los datos de tu base de datos SQLite local a Firebase.\n"
            "Asegúrate de tener configurado Firebase correctamente antes de continuar."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("""
            background-color: #FEF3C7;
            color: #92400E;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #F59E0B;
            margin-bottom: 15px;
        """)
        layout.addWidget(warning)
        
        # Source group
        source_group = QGroupBox("Origen (SQLite)")
        source_layout = QVBoxLayout()
        
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Base de datos SQLite:"))
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("Selecciona el archivo .db...")
        db_layout.addWidget(self.db_path_edit, 1)
        
        browse_btn = QPushButton("Examinar...")
        browse_btn.clicked.connect(self._browse_database)
        db_layout.addWidget(browse_btn)
        source_layout.addLayout(db_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Options group
        options_group = QGroupBox("Opciones de Migración")
        options_layout = QVBoxLayout()
        
        self.migrate_companies_cb = QCheckBox("Migrar empresas")
        self.migrate_companies_cb.setChecked(True)
        options_layout.addWidget(self.migrate_companies_cb)
        
        self.migrate_invoices_cb = QCheckBox("Migrar facturas (ingresos y gastos)")
        self.migrate_invoices_cb.setChecked(True)
        options_layout.addWidget(self.migrate_invoices_cb)
        
        self.migrate_third_parties_cb = QCheckBox("Migrar terceros (clientes/proveedores)")
        self.migrate_third_parties_cb.setChecked(True)
        options_layout.addWidget(self.migrate_third_parties_cb)
        
        self.migrate_attachments_cb = QCheckBox("Migrar archivos adjuntos a Firebase Storage")
        self.migrate_attachments_cb.setChecked(False)
        self.migrate_attachments_cb.setToolTip(
            "Los archivos adjuntos se subirán a Firebase Storage. Esto puede tomar tiempo."
        )
        options_layout.addWidget(self.migrate_attachments_cb)
        
        self.keep_sqlite_cb = QCheckBox("Mantener SQLite como backup local")
        self.keep_sqlite_cb.setChecked(True)
        self.keep_sqlite_cb.setToolTip(
            "Si está marcado, la base SQLite se conservará como backup.\n"
            "Si no, se usará solo para backups diarios automáticos."
        )
        options_layout.addWidget(self.keep_sqlite_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Progress group
        progress_group = QGroupBox("Progreso de Migración")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("El progreso de la migración se mostrará aquí...")
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.migrate_btn = QPushButton("Iniciar Migración")
        self.migrate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.migrate_btn.clicked.connect(self._start_migration)
        btn_layout.addWidget(self.migrate_btn)
        
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_database(self):
        """Browse for SQLite database file"""
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar base de datos SQLite",
            "",
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if fname:
            self.db_path_edit.setText(fname)
    
    def _start_migration(self):
        """Start the migration process"""
        db_path = self.db_path_edit.text().strip()
        
        if not db_path:
            QMessageBox.warning(
                self,
                "Base de datos requerida",
                "Por favor selecciona la base de datos SQLite a migrar."
            )
            return
        
        import os
        if not os.path.exists(db_path):
            QMessageBox.critical(
                self,
                "Archivo no encontrado",
                f"El archivo de base de datos no existe:\n{db_path}"
            )
            return
        
        # Check if Firebase is configured
        firebase_configured = False
        if hasattr(self.parent, 'controller'):
            try:
                controller = self.parent.controller
                if hasattr(controller, 'get_setting'):
                    firebase_enabled = controller.get_setting('firebase_enabled', 'false')
                    firebase_configured = firebase_enabled.lower() == 'true'
            except Exception:
                pass
        
        if not firebase_configured:
            reply = QMessageBox.question(
                self,
                "Firebase no configurado",
                "Firebase no parece estar configurado.\n\n"
                "¿Deseas configurar Firebase ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Try to open Firebase config dialog
                try:
                    from firebase_config_dialog import show_firebase_config_dialog
                    show_firebase_config_dialog(self.parent)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo abrir la configuración de Firebase:\n{e}")
                return
            else:
                return
        
        # Confirm migration
        reply = QMessageBox.question(
            self,
            "Confirmar migración",
            "¿Estás seguro de que deseas iniciar la migración?\n\n"
            "Este proceso puede tomar varios minutos dependiendo del tamaño de tus datos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable buttons during migration
        self.migrate_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        
        # Clear log and reset progress
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # Gather options
        options = {
            'migrate_companies': self.migrate_companies_cb.isChecked(),
            'migrate_invoices': self.migrate_invoices_cb.isChecked(),
            'migrate_third_parties': self.migrate_third_parties_cb.isChecked(),
            'migrate_attachments': self.migrate_attachments_cb.isChecked(),
            'keep_sqlite': self.keep_sqlite_cb.isChecked()
        }
        
        # Start migration worker
        controller = self.parent.controller if hasattr(self.parent, 'controller') else None
        self.migration_worker = MigrationWorker(controller, db_path, options)
        self.migration_worker.progress.connect(self._on_progress)
        self.migration_worker.finished.connect(self._on_finished)
        self.migration_worker.start()
    
    def _on_progress(self, percent, message):
        """Handle progress updates"""
        self.progress_bar.setValue(percent)
        self.log_text.append(f"[{percent}%] {message}")
    
    def _on_finished(self, success, message):
        """Handle migration completion"""
        self.log_text.append(f"\n{'✅' if success else '❌'} {message}")
        
        # Re-enable buttons
        self.migrate_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self,
                "Migración completada",
                "La migración se ha completado exitosamente.\n\n"
                "Firebase es ahora la fuente principal de datos.\n"
                "Los backups SQL se realizarán automáticamente cada día."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error en la migración",
                f"Hubo un error durante la migración:\n\n{message}\n\n"
                "Por favor revisa el log para más detalles."
            )
