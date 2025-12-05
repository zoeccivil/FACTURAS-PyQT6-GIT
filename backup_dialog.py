"""
Backup Management Dialog
UI for managing SQLite database backups.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from datetime import datetime
from backup_manager import BackupManager


class BackupDialog(QDialog):
    """Dialog for managing database backups"""
    
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.backup_manager = BackupManager(db_path)
        
        self.setWindowTitle("Gestión de Copias de Seguridad")
        self.resize(800, 500)
        self.setModal(True)
        
        self._build_ui()
        self._refresh_backup_list()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title and info
        title = QLabel("Gestión de Copias de Seguridad")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        info = QLabel(
            f"Base de datos: {self.db_path}\n"
            "Las copias se almacenan automáticamente y se eliminan después de 30 días."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Action buttons
        action_group = QGroupBox("Acciones")
        action_layout = QHBoxLayout()
        
        create_btn = QPushButton("Crear Nueva Copia")
        create_btn.clicked.connect(self._create_backup)
        action_layout.addWidget(create_btn)
        
        cleanup_btn = QPushButton("Limpiar Copias Antiguas (>30 días)")
        cleanup_btn.clicked.connect(self._cleanup_old_backups)
        action_layout.addWidget(cleanup_btn)
        
        action_layout.addStretch()
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Backup list table
        list_group = QGroupBox("Copias de Seguridad Disponibles")
        list_layout = QVBoxLayout()
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels([
            "Nombre", "Fecha de Creación", "Tamaño", "Antigüedad (días)"
        ])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        list_layout.addWidget(self.backup_table)
        
        # Table action buttons
        table_btn_layout = QHBoxLayout()
        
        restore_btn = QPushButton("Restaurar Seleccionada")
        restore_btn.clicked.connect(self._restore_backup)
        table_btn_layout.addWidget(restore_btn)
        
        delete_btn = QPushButton("Eliminar Seleccionada")
        delete_btn.clicked.connect(self._delete_backup)
        table_btn_layout.addWidget(delete_btn)
        
        table_btn_layout.addStretch()
        
        refresh_btn = QPushButton("Actualizar Lista")
        refresh_btn.clicked.connect(self._refresh_backup_list)
        table_btn_layout.addWidget(refresh_btn)
        
        list_layout.addLayout(table_btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
    
    def _refresh_backup_list(self):
        """Refresh the list of available backups"""
        self.backup_table.setRowCount(0)
        
        backups = self.backup_manager.list_backups()
        
        for backup in backups:
            row = self.backup_table.rowCount()
            self.backup_table.insertRow(row)
            
            # Filename
            self.backup_table.setItem(row, 0, QTableWidgetItem(backup['filename']))
            
            # Creation date
            date_str = backup['created'].strftime("%Y-%m-%d %H:%M:%S")
            self.backup_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Size
            size_mb = backup['size'] / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{backup['size']:,} bytes"
            self.backup_table.setItem(row, 2, QTableWidgetItem(size_str))
            
            # Age
            self.backup_table.setItem(row, 3, QTableWidgetItem(str(backup['age_days'])))
            
            # Store path in row data
            self.backup_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, backup['path'])
    
    def _create_backup(self):
        """Create a new backup"""
        reply = QMessageBox.question(
            self,
            "Crear Copia de Seguridad",
            "¿Desea crear una nueva copia de seguridad de la base de datos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.backup_manager.create_backup()
            
            if success:
                QMessageBox.information(self, "Éxito", msg)
                self._refresh_backup_list()
            else:
                QMessageBox.warning(self, "Error", msg)
    
    def _cleanup_old_backups(self):
        """Clean up old backups (>30 days)"""
        reply = QMessageBox.question(
            self,
            "Limpiar Copias Antiguas",
            "¿Desea eliminar todas las copias de seguridad con más de 30 días de antigüedad?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted, msg = self.backup_manager.cleanup_old_backups(retention_days=30)
            
            QMessageBox.information(self, "Limpieza Completada", msg)
            self._refresh_backup_list()
    
    def _restore_backup(self):
        """Restore selected backup"""
        selected_rows = self.backup_table.selectedItems()
        
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, seleccione una copia de seguridad para restaurar."
            )
            return
        
        # Get selected backup path
        row = selected_rows[0].row()
        backup_path = self.backup_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        backup_name = self.backup_table.item(row, 0).text()
        
        # Confirm restoration
        reply = QMessageBox.warning(
            self,
            "Confirmar Restauración",
            f"¿Está SEGURO de que desea restaurar esta copia de seguridad?\n\n"
            f"Copia: {backup_name}\n\n"
            "ADVERTENCIA: La base de datos actual será reemplazada.\n"
            "Se creará una copia de seguridad automática antes de restaurar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.backup_manager.restore_backup(backup_path)
            
            if success:
                QMessageBox.information(
                    self,
                    "Restauración Exitosa",
                    f"{msg}\n\n"
                    "IMPORTANTE: Debe reiniciar la aplicación para que los cambios tengan efecto."
                )
                self.accept()  # Close dialog
            else:
                QMessageBox.critical(self, "Error de Restauración", msg)
    
    def _delete_backup(self):
        """Delete selected backup"""
        selected_rows = self.backup_table.selectedItems()
        
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, seleccione una copia de seguridad para eliminar."
            )
            return
        
        # Get selected backup
        row = selected_rows[0].row()
        backup_path = self.backup_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        backup_name = self.backup_table.item(row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar esta copia de seguridad?\n\n"
            f"Copia: {backup_name}\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.backup_manager.delete_backup(backup_path)
            
            if success:
                QMessageBox.information(self, "Éxito", msg)
                self._refresh_backup_list()
            else:
                QMessageBox.warning(self, "Error", msg)
