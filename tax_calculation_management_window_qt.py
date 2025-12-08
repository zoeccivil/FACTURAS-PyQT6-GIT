from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QWidget,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from datetime import datetime

try:
    from advanced_retention_window_qt import AdvancedRetentionWindowQt
except Exception:
    AdvancedRetentionWindowQt = None  # placeholder si aún no está migrada


class TaxCalculationManagementWindowQt(QDialog):
    """
    Ventana moderna para gestionar cálculos de impuestos guardados.

    Espera que el controller implemente (en modo real o placeholder):
      - get_tax_calculations(company_id) -> lista de dicts
      - delete_tax_calculation(calc_id) -> (bool, mensaje)

    Para crear/editar usa AdvancedRetentionWindowQt si está disponible.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller

        self.setWindowTitle("Gestión de Cálculos de Impuestos")
        self.resize(780, 480)
        self.setModal(True)

        self._build_ui()
        self._load_calculations()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # Layout raíz
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        # Card principal para alinearse con estilo moderno
        card = QFrame()
        card.setObjectName("taxCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        # Título y subtítulo
        header = QHBoxLayout()
        title = QLabel("Cálculos de Impuestos Guardados")
        title.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #0F172A;"
        )
        subtitle = QLabel(
            "Administra los escenarios de cálculo de impuestos retenidos y adelantados "
            "que has guardado previamente."
        )
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        subtitle.setWordWrap(True)

        header.addWidget(title)
        header.addStretch()
        card_layout.addLayout(header)
        card_layout.addWidget(subtitle)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(line)

        # Tabla dentro de un contenedor
        list_frame = QWidget()
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)

        table_label = QLabel("Cálculos Guardados")
        table_label.setStyleSheet(
            "font-weight: 600; color: #4B5563; font-size: 13px;"
        )
        list_layout.addWidget(table_label)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(
            ["Nombre del Cálculo", "Fecha de Creación"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        list_layout.addWidget(self.table)

        card_layout.addWidget(list_frame)

        # Fila de botones
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 8, 0, 0)
        btn_row.setSpacing(8)

        btn_new = QPushButton("Nuevo Cálculo")
        btn_new.setObjectName("primaryButton")
        btn_new.clicked.connect(self._new)

        btn_edit = QPushButton("Editar Selección")
        btn_edit.setObjectName("secondaryButton")
        btn_edit.clicked.connect(self._edit)

        btn_delete = QPushButton("Eliminar")
        btn_delete.setObjectName("dangerButton")
        btn_delete.clicked.connect(self._delete)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("secondaryButton")
        btn_close.clicked.connect(self.reject)

        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_edit)
        btn_row.addStretch()
        btn_row.addWidget(btn_delete)
        btn_row.addWidget(btn_close)

        card_layout.addLayout(btn_row)

        # Añadir card al layout raíz
        root.addWidget(card)

        # Estilos mínimos para botones, puedes integrarlos en tu STYLESHEET global
        self.setStyleSheet(
            self.styleSheet()
            + """
        QFrame#taxCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
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
        QPushButton#dangerButton {
            background-color: #FEF2F2;
            color: #B91C1C;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #FECACA;
            font-weight: 500;
        }
        QPushButton#dangerButton:hover {
            background-color: #FEE2E2;
        }
        """
        )

    # ------------------------------------------------------------------ #
    # Carga de datos
    # ------------------------------------------------------------------ #
    def _load_calculations(self):
        """Carga los cálculos guardados para la empresa actual."""
        self.table.setRowCount(0)

        company_id = None
        try:
            if self.parent and hasattr(self.parent, "get_current_company_id"):
                company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            if hasattr(self.controller, "get_tax_calculations"):
                calculations = self.controller.get_tax_calculations(company_id) or []
            else:
                calculations = []
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudieron obtener los cálculos: {e}",
            )
            calculations = []

        # Normalizar a dicts
        normalized = []
        for c in calculations:
            try:
                normalized.append(dict(c))
            except Exception:
                if isinstance(c, dict):
                    normalized.append(c)
                else:
                    try:
                        normalized.append({k: c[k] for k in c.keys()})
                    except Exception:
                        normalized.append(c)
        calculations = normalized

        # Poblar tabla
        for calc in calculations:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name = str(calc.get("name") or calc.get("title") or "")
            name_item = QTableWidgetItem(name)
            name_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            name_item.setData(Qt.ItemDataRole.UserRole, calc.get("id"))

            date_raw = calc.get("creation_date") or calc.get("created_at") or ""
            date_str = self._format_date(date_raw)
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, date_item)

    def _format_date(self, value) -> str:
        if not value:
            return ""
        # Si ya es datetime
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        # Timestamp Firestore / string ISO
        try:
            s = str(value)
            # Intentar YYYY-MM-DD primero
            if len(s) >= 10:
                return s[:16]  # YYYY-MM-DD HH:MM aproximado
            return s
        except Exception:
            return str(value)

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        try:
            return int(val)
        except Exception:
            return val

    # ------------------------------------------------------------------ #
    # Acciones
    # ------------------------------------------------------------------ #
    def _new(self):
        """Crear un nuevo cálculo (abre AdvancedRetentionWindowQt si está disponible)."""
        if AdvancedRetentionWindowQt is None:
            QMessageBox.information(
                self,
                "No disponible",
                "La ventana avanzada de cálculo de retenciones aún no está disponible.",
            )
            return
        try:
            dlg = AdvancedRetentionWindowQt(
                self.parent, self.controller, calculation_id=None
            )
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._load_calculations()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la ventana de cálculo: {e}",
            )

    def _edit(self):
        """Editar cálculo seleccionado."""
        calc_id = self._get_selected_id()
        if not calc_id:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Por favor, selecciona un cálculo para editar.",
            )
            return

        if AdvancedRetentionWindowQt is None:
            QMessageBox.information(
                self,
                "No disponible",
                "La ventana avanzada de cálculo de retenciones aún no está disponible.",
            )
            return

        try:
            dlg = AdvancedRetentionWindowQt(
                self.parent, self.controller, calculation_id=calc_id
            )
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._load_calculations()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la ventana de edición: {e}",
            )

    def _delete(self):
        """Eliminar cálculo seleccionado."""
        calc_id = self._get_selected_id()
        if not calc_id:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Por favor, selecciona un cálculo para eliminar.",
            )
            return

        resp = QMessageBox.question(
            self,
            "Confirmar",
            "¿Estás seguro de que deseas eliminar este cálculo guardado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            if hasattr(self.controller, "delete_tax_calculation"):
                success, message = self.controller.delete_tax_calculation(calc_id)
            else:
                success, message = False, "El controlador no implementa delete_tax_calculation."

            if success:
                QMessageBox.information(self, "Éxito", message)
                self._load_calculations()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo eliminar el cálculo: {e}",
            )