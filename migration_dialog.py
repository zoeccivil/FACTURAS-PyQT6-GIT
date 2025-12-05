"""
Migration Dialog - SQLite to Firebase
Modern dialog for migrating data from SQLite to Firebase Firestore.
"""

import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QCheckBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
import firebase_client


class MigrationWorker(QThread):
    """Worker thread for performing migration"""
    
    progress = pyqtSignal(int)  # Progress percentage
    log_message = pyqtSignal(str, str)  # (message, level)
    stats_update = pyqtSignal(dict)  # Migration statistics
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, controller, clean_collections=False):
        super().__init__()
        self.controller = controller
        self.clean_collections = clean_collections
        self.should_cancel = False
        self.stats = {
            'companies': {'total': 0, 'migrated': 0, 'errors': 0},
            'invoices': {'total': 0, 'migrated': 0, 'errors': 0},
            'items': {'total': 0, 'migrated': 0, 'errors': 0}
        }
    
    def cancel(self):
        """Request cancellation of migration"""
        self.should_cancel = True
    
    def run(self):
        """Execute the migration"""
        try:
            self.log_message.emit("Iniciando migración SQLite → Firebase...", "INFO")
            
            # Get Firebase client
            if not firebase_client.is_firebase_available():
                success, msg = firebase_client.initialize_firebase()
                if not success:
                    self.finished.emit(False, f"Error al conectar con Firebase: {msg}")
                    return
            
            db = firebase_client.get_firestore()
            self.log_message.emit("✓ Conectado a Firebase Firestore", "SUCCESS")
            
            # Clean collections if requested
            if self.clean_collections:
                self._clean_collections(db)
            
            # Migrate companies
            if not self.should_cancel:
                self._migrate_companies(db)
            
            # Migrate invoices
            if not self.should_cancel:
                self._migrate_invoices(db)
            
            if self.should_cancel:
                self.log_message.emit("⚠ Migración cancelada por el usuario", "WARNING")
                self.finished.emit(False, "Migración cancelada")
            else:
                self.log_message.emit("✓ Migración completada exitosamente", "SUCCESS")
                self.finished.emit(True, "Migración completada")
                
        except Exception as e:
            self.log_message.emit(f"✗ Error fatal: {e}", "ERROR")
            self.finished.emit(False, str(e))
    
    def _clean_collections(self, db):
        """Clean Firebase collections before migration"""
        self.log_message.emit("Limpiando colecciones existentes...", "INFO")
        
        collections_to_clean = ['companies', 'invoices', 'items']
        for collection_name in collections_to_clean:
            if self.should_cancel:
                return
            
            try:
                # Delete all documents in collection (with pagination for large collections)
                deleted_total = 0
                while True:
                    docs = db.collection(collection_name).limit(500).stream()
                    batch = db.batch()
                    count = 0
                    
                    for doc in docs:
                        batch.delete(doc.reference)
                        count += 1
                    
                    if count == 0:
                        break  # No more documents
                    
                    batch.commit()
                    deleted_total += count
                    
                    # Continue if we hit the limit (might be more)
                    if count < 500:
                        break
                
                if deleted_total > 0:
                    self.log_message.emit(f"  Eliminados {deleted_total} documentos de '{collection_name}'", "INFO")
                    
            except Exception as e:
                self.log_message.emit(f"  Error limpiando '{collection_name}': {e}", "WARNING")
    
    def _migrate_companies(self, db):
        """Migrate companies from SQLite to Firestore"""
        self.log_message.emit("Migrando empresas...", "INFO")
        self.progress.emit(10)
        
        try:
            # Get companies from SQLite
            companies = self.controller.get_all_companies()
            self.stats['companies']['total'] = len(companies)
            
            if not companies:
                self.log_message.emit("  No hay empresas para migrar", "WARNING")
                return
            
            # Migrate each company
            companies_ref = db.collection('companies')
            
            for idx, company in enumerate(companies):
                if self.should_cancel:
                    return
                
                try:
                    # Prepare company data
                    company_data = {
                        'id': company['id'],
                        'name': company['name'],
                        'rnc': company.get('rnc', ''),
                        'address': company.get('address', ''),
                        'itbis_adelantado': float(company.get('itbis_adelantado', 0.0)),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Remove 'id' field before uploading (Firestore uses document ID)
                    doc_id = str(company_data.pop('id'))
                    
                    # Upload to Firestore
                    companies_ref.document(doc_id).set(company_data)
                    
                    self.stats['companies']['migrated'] += 1
                    self.log_message.emit(f"  ✓ Empresa migrada: {company['name']}", "SUCCESS")
                    
                except Exception as e:
                    self.stats['companies']['errors'] += 1
                    self.log_message.emit(f"  ✗ Error migrando empresa {company.get('name', 'N/A')}: {e}", "ERROR")
                
                # Update progress
                progress = 10 + int((idx + 1) / len(companies) * 30)
                self.progress.emit(progress)
                self.stats_update.emit(self.stats.copy())
            
            self.log_message.emit(
                f"Empresas: {self.stats['companies']['migrated']}/{self.stats['companies']['total']} migradas",
                "INFO"
            )
            
        except Exception as e:
            self.log_message.emit(f"Error en migración de empresas: {e}", "ERROR")
    
    def _migrate_invoices(self, db):
        """Migrate invoices from SQLite to Firestore"""
        self.log_message.emit("Migrando facturas...", "INFO")
        self.progress.emit(40)
        
        try:
            # Get all companies to migrate their invoices
            companies = self.controller.get_all_companies()
            
            if not companies:
                return
            
            invoices_ref = db.collection('invoices')
            total_invoices = 0
            
            for comp_idx, company in enumerate(companies):
                if self.should_cancel:
                    return
                
                company_id = company['id']
                
                # Get invoices for this company
                # We need to access SQLite directly for this
                try:
                    cursor = self.controller.conn.cursor()
                    cursor.execute(
                        "SELECT * FROM invoices WHERE company_id = ?",
                        (company_id,)
                    )
                    invoices = cursor.fetchall()
                    
                    for invoice in invoices:
                        if self.should_cancel:
                            return
                        
                        try:
                            total_invoices += 1
                            self.stats['invoices']['total'] = total_invoices
                            
                            # Prepare invoice data
                            invoice_dict = dict(invoice)
                            invoice_data = {
                                'id': invoice_dict['id'],
                                'company_id': invoice_dict['company_id'],
                                'invoice_type': invoice_dict['invoice_type'],
                                'invoice_date': invoice_dict['invoice_date'],
                                'imputation_date': invoice_dict.get('imputation_date', ''),
                                'invoice_number': invoice_dict['invoice_number'],
                                'invoice_category': invoice_dict.get('invoice_category', ''),
                                'rnc': invoice_dict.get('rnc', ''),
                                'third_party_name': invoice_dict.get('third_party_name', ''),
                                'currency': invoice_dict.get('currency', 'RD$'),
                                'itbis': float(invoice_dict.get('itbis', 0.0)),
                                'total_amount': float(invoice_dict.get('total_amount', 0.0)),
                                'exchange_rate': float(invoice_dict.get('exchange_rate', 1.0)),
                                'total_amount_rd': float(invoice_dict.get('total_amount_rd', 0.0)),
                                'attachment_path': invoice_dict.get('attachment_path', ''),
                                'created_at': datetime.now(),
                                'updated_at': datetime.now()
                            }
                            
                            # Remove 'id' field
                            doc_id = str(invoice_data.pop('id'))
                            
                            # Upload to Firestore
                            invoices_ref.document(doc_id).set(invoice_data)
                            
                            # Migrate invoice items (subcollection)
                            self._migrate_invoice_items(db, doc_id, invoice_dict['id'])
                            
                            self.stats['invoices']['migrated'] += 1
                            
                        except Exception as e:
                            self.stats['invoices']['errors'] += 1
                            self.log_message.emit(
                                f"  ✗ Error migrando factura {invoice_dict.get('invoice_number', 'N/A')}: {e}",
                                "ERROR"
                            )
                    
                except Exception as e:
                    self.log_message.emit(f"Error obteniendo facturas de empresa {company_id}: {e}", "ERROR")
                
                # Update progress
                progress = 40 + int((comp_idx + 1) / len(companies) * 50)
                self.progress.emit(progress)
                self.stats_update.emit(self.stats.copy())
            
            self.log_message.emit(
                f"Facturas: {self.stats['invoices']['migrated']}/{self.stats['invoices']['total']} migradas",
                "INFO"
            )
            
        except Exception as e:
            self.log_message.emit(f"Error en migración de facturas: {e}", "ERROR")
    
    def _migrate_invoice_items(self, db, invoice_doc_id, invoice_id):
        """Migrate invoice items as subcollection"""
        try:
            cursor = self.controller.conn.cursor()
            cursor.execute(
                "SELECT * FROM invoice_items WHERE invoice_id = ?",
                (invoice_id,)
            )
            items = cursor.fetchall()
            
            if not items:
                return
            
            items_ref = db.collection('invoices').document(invoice_doc_id).collection('items')
            
            for item in items:
                item_dict = dict(item)
                item_data = {
                    'description': item_dict['description'],
                    'quantity': float(item_dict['quantity']),
                    'unit_price': float(item_dict['unit_price']),
                    'created_at': datetime.now()
                }
                
                items_ref.add(item_data)
                self.stats['items']['migrated'] += 1
            
            self.stats['items']['total'] += len(items)
            
        except Exception as e:
            self.log_message.emit(f"  Error migrando items de factura {invoice_id}: {e}", "WARNING")


class MigrationDialog(QDialog):
    """Dialog for migrating data from SQLite to Firebase"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.worker = None
        
        self.setWindowTitle("Migrador de Datos: SQLite → Firebase")
        self.resize(800, 600)
        self.setModal(True)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Migración de Datos a Firebase")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Este asistente migrará todos los datos de la base de datos SQLite local "
            "a Firebase Firestore. Asegúrese de haber configurado Firebase correctamente "
            "antes de continuar."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Options
        options_group = QGroupBox("Opciones de Migración")
        options_layout = QVBoxLayout()
        
        self.clean_checkbox = QCheckBox("Limpiar colecciones antes de migrar")
        self.clean_checkbox.setToolTip(
            "Si está marcado, eliminará todos los datos existentes en Firebase antes de migrar"
        )
        options_layout.addWidget(self.clean_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Statistics Group
        stats_group = QGroupBox("Estadísticas de Migración")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel("Esperando inicio de migración...")
        self.stats_label.setStyleSheet("font-family: monospace;")
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Log display
        log_group = QGroupBox("Registro de Actividad")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; "
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt;"
        )
        log_layout.addWidget(self.log_display)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_btn = QPushButton("Iniciar Migración")
        self.start_btn.clicked.connect(self._start_migration)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self._cancel_migration)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _log(self, message: str, level: str = "INFO"):
        """Add a message to the log display with color coding"""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Color coding based on level
        fmt = QTextCharFormat()
        if level == "ERROR":
            fmt.setForeground(QColor("#ff6b6b"))
        elif level == "WARNING":
            fmt.setForeground(QColor("#ffd93d"))
        elif level == "SUCCESS":
            fmt.setForeground(QColor("#6bcf7f"))
        else:  # INFO
            fmt.setForeground(QColor("#d4d4d4"))
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] ", fmt)
        cursor.insertText(f"{message}\n", fmt)
        
        self.log_display.setTextCursor(cursor)
        self.log_display.ensureCursorVisible()
    
    def _update_stats(self, stats):
        """Update statistics display"""
        stats_text = (
            f"Empresas: {stats['companies']['migrated']}/{stats['companies']['total']} "
            f"(Errores: {stats['companies']['errors']})\n"
            f"Facturas: {stats['invoices']['migrated']}/{stats['invoices']['total']} "
            f"(Errores: {stats['invoices']['errors']})\n"
            f"Items: {stats['items']['migrated']}/{stats['items']['total']}"
        )
        self.stats_label.setText(stats_text)
    
    def _start_migration(self):
        """Start the migration process"""
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirmar Migración",
            "¿Está seguro de que desea iniciar la migración?\n\n"
            "Este proceso puede tomar varios minutos dependiendo "
            "de la cantidad de datos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Disable controls
        self.start_btn.setEnabled(False)
        self.clean_checkbox.setEnabled(False)
        
        # Create and start worker
        self.worker = MigrationWorker(
            self.controller,
            self.clean_checkbox.isChecked()
        )
        
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self._log)
        self.worker.stats_update.connect(self._update_stats)
        self.worker.finished.connect(self._migration_finished)
        
        self.worker.start()
    
    def _cancel_migration(self):
        """Cancel the ongoing migration"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancelar Migración",
                "¿Está seguro de que desea cancelar la migración?\n\n"
                "Los datos ya migrados permanecerán en Firebase.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self._log("Solicitando cancelación...", "WARNING")
        else:
            self.reject()
    
    def _migration_finished(self, success, message):
        """Handle migration completion"""
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(
                self,
                "Migración Completada",
                "La migración se ha completado exitosamente.\n\n"
                "Todos los datos han sido transferidos a Firebase."
            )
        else:
            QMessageBox.warning(
                self,
                "Migración Incompleta",
                f"La migración no se completó correctamente:\n\n{message}"
            )
        
        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.clean_checkbox.setEnabled(True)
        self.close_btn.setEnabled(True)
        self.cancel_btn.setText("Cerrar")
