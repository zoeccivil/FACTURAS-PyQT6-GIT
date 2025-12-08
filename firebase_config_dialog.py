"""
Diálogo de Configuración de Firebase para FACOT / Facturas Pro.

Persistencia:
- Usa el setting único "facturas_config" en el controller.
- Dentro de "facturas_config" se guardan:
  - firebase_credentials_path
  - firebase_storage_bucket
  - firebase_project_id

Estilo:
- Alineado con la UI moderna (modern_gui.py):
  - Fondo claro
  - Card central
  - Botón primario oscuro
  - Tipografía limpia
"""

import os
import json

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QGroupBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class FirebaseConfigDialog(QDialog):
    """
    Diálogo para configurar las credenciales de Firebase.

    Permite:
    - Seleccionar archivo JSON de credenciales (service account)
    - Configurar el bucket de Storage
    - Validar credenciales antes de guardar
    """

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Firebase")
        self.setModal(True)
        self.resize(620, 360)

        # Controller para leer/escribir settings
        self.controller = controller

        self._credentials_path: str = ""
        self._storage_bucket: str = ""
        self._project_id: str = ""

        self._init_ui()
        self._apply_styles()
        self._load_existing_config()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        # Layout raíz
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(0)

        # Card central
        container = QFrame()
        container.setObjectName("firebaseCard")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)

        # Header
        header_layout = QVBoxLayout()
        title = QLabel("Configuración de Firebase")
        title.setObjectName("dialogTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Conecta Facturas Pro con tu proyecto de Firebase usando un archivo "
            "de credenciales de cuenta de servicio."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addSpacing(4)
        container_layout.addLayout(header_layout)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        container_layout.addWidget(line)

        # Grupo de credenciales
        cred_group = QGroupBox("Credenciales")
        cred_group.setObjectName("dialogGroupBox")
        cred_layout = QVBoxLayout()
        cred_layout.setContentsMargins(10, 10, 10, 10)
        cred_layout.setSpacing(8)

        cred_label = QLabel("Archivo de credenciales (JSON):")
        cred_layout.addWidget(cred_label)

        cred_row = QHBoxLayout()
        cred_row.setSpacing(8)

        self.cred_edit = QLineEdit()
        self.cred_edit.setPlaceholderText("Selecciona el archivo firebase-credentials.json")
        self.cred_edit.setReadOnly(True)
        cred_row.addWidget(self.cred_edit)

        btn_browse = QPushButton("Seleccionar...")
        btn_browse.setObjectName("secondaryButton")
        btn_browse.clicked.connect(self._browse_credentials)
        cred_row.addWidget(btn_browse)

        cred_layout.addLayout(cred_row)
        cred_group.setLayout(cred_layout)
        container_layout.addWidget(cred_group)

        # Grupo de Storage
        storage_group = QGroupBox("Storage")
        storage_group.setObjectName("dialogGroupBox")
        storage_layout = QVBoxLayout()
        storage_layout.setContentsMargins(10, 10, 10, 10)
        storage_layout.setSpacing(6)

        bucket_label = QLabel("Bucket de Storage:")
        storage_layout.addWidget(bucket_label)

        self.bucket_edit = QLineEdit()
        self.bucket_edit.setPlaceholderText("proyecto-id.firebasestorage.app")
        storage_layout.addWidget(self.bucket_edit)

        bucket_hint = QLabel(
            "Se autocompleta al seleccionar las credenciales. "
            "Formato recomendado: {project_id}.firebasestorage.app"
        )
        bucket_hint.setObjectName("hintLabel")
        bucket_hint.setWordWrap(True)
        storage_layout.addWidget(bucket_hint)

        storage_group.setLayout(storage_layout)
        container_layout.addWidget(storage_group)

        # Espaciador
        container_layout.addStretch()

        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_test = QPushButton("Validar credenciales")
        btn_test.setObjectName("secondaryButton")
        btn_test.clicked.connect(self._test_connection)
        btn_layout.addWidget(btn_test)

        btn_save = QPushButton("Guardar y conectar")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save_and_accept)
        btn_save.setDefault(True)
        btn_layout.addWidget(btn_save)

        container_layout.addLayout(btn_layout)

        root_layout.addWidget(container)

    def _apply_styles(self):
        self.setObjectName("firebaseDialog")
        self.setStyleSheet("""
        QDialog#firebaseDialog {
            background-color: #E5E7EB;
        }
        QFrame#firebaseCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }
        QLabel#dialogTitle {
            color: #0F172A;
        }
        QLabel#dialogSubtitle {
            color: #6B7280;
            font-size: 12px;
        }
        QGroupBox#dialogGroupBox {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            margin-top: 8px;
        }
        QGroupBox#dialogGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px 0 4px;
            color: #1F2933;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }
        QLabel#hintLabel {
            color: #9CA3AF;
            font-size: 11px;
        }
        QLineEdit {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;              /* ← texto oscuro aquí también */
        }
        QLineEdit:focus {
            border-color: #3B82F6;
        }
        QPushButton#primaryButton {
            background-color: #1E293B;
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 500;
            border: none;
        }
        QPushButton#primaryButton:hover {
            background-color: #0F172A;
        }
        QPushButton#secondaryButton {
            background-color: #F9FAFB;
            color: #374151;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #D1D5DB;
            font-weight: 500;
        }
        QPushButton#secondaryButton:hover {
            background-color: #E5E7EB;
        }
        """)
    # ------------------------------------------------------------------ #
    # Configuración / Persistencia
    # ------------------------------------------------------------------ #
    def _load_existing_config(self):
        """Carga la configuración existente desde el setting 'facturas_config'."""
        if self.controller is None:
            return

        try:
            raw = self.controller.get_setting("facturas_config", {})
            # Puede venir como dict o como string JSON; normalizar
            if isinstance(raw, str):
                try:
                    cfg = json.loads(raw)
                except Exception:
                    cfg = {}
            elif isinstance(raw, dict):
                cfg = raw
            else:
                cfg = {}

            cred_path = cfg.get("firebase_credentials_path", "")
            bucket = cfg.get("firebase_storage_bucket", "")
            project_id = cfg.get("firebase_project_id", "")

            if cred_path:
                self.cred_edit.setText(cred_path)
                self._credentials_path = cred_path
            if bucket:
                self.bucket_edit.setText(bucket)
                self._storage_bucket = bucket
            if project_id:
                self._project_id = project_id
        except Exception as e:
            print(f"[FIREBASE] Error cargando configuración existente: {e}")

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #
    def _browse_credentials(self):
        """Abre diálogo para seleccionar archivo de credenciales."""
        start_dir = os.path.expanduser("~")
        if self._credentials_path and os.path.exists(os.path.dirname(self._credentials_path)):
            start_dir = os.path.dirname(self._credentials_path)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar credenciales de Firebase",
            start_dir,
            "Archivos JSON (*.json);;Todos los archivos (*.*)"
        )

        if file_path:
            self.cred_edit.setText(file_path)
            self._credentials_path = file_path

            # Intentar extraer project_id y autocompletar bucket
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cred_data = json.load(f)
                    project_id = cred_data.get('project_id', '')

                    if project_id:
                        self._project_id = project_id
                        suggested_bucket = f"{project_id}.firebasestorage.app"
                        if not self.bucket_edit.text():
                            self.bucket_edit.setText(suggested_bucket)
                            self._storage_bucket = suggested_bucket

                        QMessageBox.information(
                            self,
                            "Credenciales detectadas",
                            f"Proyecto: {project_id}\n"
                            f"Bucket sugerido: {suggested_bucket}"
                        )
            except json.JSONDecodeError:
                QMessageBox.warning(
                    self,
                    "Archivo inválido",
                    "El archivo seleccionado no es un JSON válido."
                )
            except Exception as e:
                print(f"[FIREBASE] Error leyendo credenciales: {e}")

    def _test_connection(self):
        """Valida la estructura del archivo de credenciales (no abre conexión real)."""
        cred_path = self.cred_edit.text().strip()
        bucket = self.bucket_edit.text().strip()

        if not cred_path:
            QMessageBox.warning(self, "Error", "Selecciona un archivo de credenciales.")
            return

        if not os.path.exists(cred_path):
            QMessageBox.warning(self, "Error", "El archivo de credenciales no existe.")
            return

        if not bucket:
            QMessageBox.warning(self, "Error", "Ingresa el nombre del bucket de Storage.")
            return

        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                cred_data = json.load(f)

            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing = [f for f in required_fields if f not in cred_data]

            if missing:
                QMessageBox.warning(
                    self,
                    "Credenciales incompletas",
                    f"El archivo de credenciales no contiene los campos requeridos:\n"
                    f"{', '.join(missing)}\n\n"
                    "Asegúrate de usar un archivo de Service Account válido."
                )
                return

            if cred_data.get('type') != 'service_account':
                QMessageBox.warning(
                    self,
                    "Tipo de credencial inválido",
                    "El archivo debe ser de tipo 'service_account'.\n"
                    "Descarga las credenciales desde Firebase Console > "
                    "Configuración > Service accounts > Generate new private key."
                )
                return

            self._project_id = cred_data.get('project_id', self._project_id)

            QMessageBox.information(
                self,
                "✓ Credenciales válidas",
                f"Las credenciales parecen correctas.\n\n"
                f"Proyecto: {cred_data.get('project_id')}\n"
                f"Email: {cred_data.get('client_email')}"
            )

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "El archivo no es un JSON válido.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al validar credenciales:\n{str(e)}")

    def _save_and_accept(self):
        """Guarda la configuración en 'facturas_config' y cierra el diálogo."""
        cred_path = self.cred_edit.text().strip()
        bucket = self.bucket_edit.text().strip()

        if not cred_path:
            QMessageBox.warning(self, "Error", "Selecciona un archivo de credenciales.")
            return

        if not os.path.exists(cred_path):
            QMessageBox.warning(self, "Error", "El archivo de credenciales no existe.")
            return

        if not bucket:
            QMessageBox.warning(self, "Error", "Ingresa el nombre del bucket de Storage.")
            return

        # Si no teníamos project_id, intentar leerlo ahora
        if not self._project_id:
            try:
                with open(cred_path, 'r', encoding='utf-8') as f:
                    cred_data = json.load(f)
                    self._project_id = cred_data.get('project_id', "")
            except Exception:
                pass

        self._credentials_path = cred_path
        self._storage_bucket = bucket

        # Guardar en setting facturas_config
        if self.controller is not None:
            try:
                raw = self.controller.get_setting("facturas_config", {})
                if isinstance(raw, str):
                    try:
                        cfg = json.loads(raw)
                    except Exception:
                        cfg = {}
                elif isinstance(raw, dict):
                    cfg = raw
                else:
                    cfg = {}

                cfg["firebase_credentials_path"] = cred_path
                cfg["firebase_storage_bucket"] = bucket
                if self._project_id:
                    cfg["firebase_project_id"] = self._project_id

                self.controller.set_setting("facturas_config", cfg)
            except Exception as e:
                print(f"[FIREBASE] Error guardando configuración: {e}")

        QMessageBox.information(
            self,
            "Firebase",
            "Configuración guardada con éxito."
        )
        self.accept()

    # ------------------------------------------------------------------ #
    # Getters
    # ------------------------------------------------------------------ #
    def get_credentials_path(self) -> str:
        return self._credentials_path

    def get_storage_bucket(self) -> str:
        return self._storage_bucket

    def get_project_id(self) -> str:
        return self._project_id


def show_firebase_config_dialog(parent=None, controller=None) -> bool:
    """
    Muestra el diálogo de configuración de Firebase.

    Args:
        parent: Widget padre
        controller: Controller con get_setting / set_setting

    Returns:
        True si el usuario aceptó y guardó la configuración
    """
    dialog = FirebaseConfigDialog(parent, controller=controller)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted