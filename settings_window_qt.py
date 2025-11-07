from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
import os
from pathlib import Path

class SettingsWindowQt(QDialog):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.setWindowTitle("Configuración")
        self.setModal(True)
        self.resize(600, 320)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ---- Configuración de Base de Datos ----
        db_group = QGroupBox("Ruta de la Base de Datos")
        db_layout = QHBoxLayout(db_group)
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_layout.addWidget(self.db_path_edit)
        self.db_browse_btn = QPushButton("Seleccionar...")
        self.db_browse_btn.clicked.connect(self._choose_db_file)
        db_layout.addWidget(self.db_browse_btn)
        layout.addWidget(db_group)

        # ---- Carpeta Base de Anexos (attachments) ----
        att_group = QGroupBox("Carpeta Base para Anexos (attachments)")
        att_layout = QHBoxLayout(att_group)
        self.att_path_edit = QLineEdit()
        self.att_path_edit.setReadOnly(True)
        att_layout.addWidget(self.att_path_edit)
        self.att_browse_btn = QPushButton("Seleccionar...")
        self.att_browse_btn.clicked.connect(self._choose_attachments_folder)
        att_layout.addWidget(self.att_browse_btn)
        layout.addWidget(att_group)

        # ---- Botones de acción ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancelar)
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.clicked.connect(self._save_settings)
        btn_row.addWidget(self.btn_guardar)
        layout.addLayout(btn_row)

    def _choose_db_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Seleccionar base de datos", "", "Bases de datos (*.db);;Todos los archivos (*)")
        if fname:
            self.db_path_edit.setText(fname)

    def _choose_attachments_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta base para anexos", str(Path.home()))
        if folder:
            self.att_path_edit.setText(folder)

    def _load_settings(self):
        # Lee la ruta desde la configuración (usa tu controlador)
        try:
            db_path = self.controller.get_setting("facturas_config", "")
        except Exception:
            db_path = ""
        self.db_path_edit.setText(db_path or "")

        try:
            att_path = self.controller.get_setting("attachments_root", "")
        except Exception:
            att_path = ""
        self.att_path_edit.setText(att_path or "")

    def _save_settings(self):
        db_path = self.db_path_edit.text().strip()
        att_path = self.att_path_edit.text().strip()

        if not db_path:
            QMessageBox.warning(self, "Campo vacío", "Debes seleccionar una base de datos.")
            return

        # Validar carpeta de anexos: si no existe, preguntar para crear
        if att_path:
            try:
                p = Path(att_path)
                if not p.exists():
                    resp = QMessageBox.question(
                        self,
                        "Crear carpeta",
                        f"La carpeta de anexos seleccionada no existe:\n{att_path}\n\n¿Deseas crearla ahora?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if resp == QMessageBox.StandardButton.Yes:
                        p.mkdir(parents=True, exist_ok=True)
                    else:
                        QMessageBox.warning(self, "Carpeta no creada", "Debes seleccionar o crear una carpeta válida para anexos.")
                        return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo validar/crear la carpeta de anexos:\n{e}")
                return
        else:
            # Si no indicó carpeta de anexos, avisamos que se usará la carpeta local 'attachments' por defecto
            resp = QMessageBox.question(
                self,
                "Carpeta de anexos vacía",
                "No has seleccionado una carpeta para anexos. Se usará la carpeta local './attachments' por defecto.\n¿Deseas continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        # Guardar settings mediante el controller
        try:
            self.controller.set_setting("facturas_config", db_path)
            # Guardamos attachments_root sólo si se indicó (si no, borramos o dejamos vacío)
            if att_path:
                self.controller.set_setting("attachments_root", att_path)
            else:
                # opcional: borrar la key si existe o dejar vacía según tu controller impl
                try:
                    self.controller.set_setting("attachments_root", "")
                except Exception:
                    pass

            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")
            self.accept()
            # Opcional: refrescar la app principal o reiniciar la conexión aquí si lo deseas
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar la configuración:\n{e}")