from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from advanced_retention_window_qt import AdvancedRetentionWindowQt  # Asegúrate de que exista
from datetime import datetime

class TaxCalculationManagementWindowQt(QDialog):
    """
    Ventana para listar/editar/eliminar cálculos de impuestos guardados.
    Usa controller.get_tax_calculations(company_id) y controller.delete_tax_calculation(calc_id).
    Al crear/editar abre AdvancedRetentionWindowQt con calculation_id (None para nuevo).
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.setWindowTitle("Gestión de Cálculos de Impuestos")
        self.resize(700, 450)

        self._build_ui()
        self._load_calculations()

    def _build_ui(self):
        main = QVBoxLayout(self)

        list_frame = QWidget()
        list_layout = QVBoxLayout(list_frame)
        header = QLabel("Cálculos Guardados")
        list_layout.addWidget(header)

        # Table: Name, Creation Date
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nombre del Cálculo", "Fecha de Creación"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        list_layout.addWidget(self.table)

        main.addWidget(list_frame)

        # Buttons
        btn_row = QHBoxLayout()
        btn_new = QPushButton("Nuevo Cálculo")
        btn_new.clicked.connect(self._new)
        btn_edit = QPushButton("Editar Selección")
        btn_edit.clicked.connect(self._edit)
        btn_delete = QPushButton("Eliminar")
        btn_delete.clicked.connect(self._delete)

        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_edit)
        btn_row.addStretch()
        btn_row.addWidget(btn_delete)

        main.addLayout(btn_row)

    def _load_calculations(self):
        # Clear existing rows
        self.table.setRowCount(0)
        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            calculations = self.controller.get_tax_calculations(company_id) or []
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"No se pudieron obtener los cálculos: {e}", Qt.WindowType.Window)
            calculations = []

        # Convertir cada resultado a dict para evitar errores sobre sqlite3.Row (no tienen .get)
        normalized = []
        for c in calculations:
            try:
                # si ya es dict, dict(c) hace copia; si es sqlite3.Row, dict(c) lo convierte correctamente
                normalized.append(dict(c))
            except Exception:
                # fallback: intentar acceder por índice/clave o dejar tal cual
                if isinstance(c, dict):
                    normalized.append(c)
                else:
                    # último recurso: construir dict desde atributos si existen
                    try:
                        normalized.append({k: c[k] for k in c.keys()})
                    except Exception:
                        normalized.append(c)
        calculations = normalized

        # poblar tabla con dicts
        for calc in calculations:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(str(calc.get("name", "")))
            # store id in UserRole for easy retrieval
            name_item.setData(Qt.ItemDataRole.UserRole, calc.get("id"))
            date_str = calc.get("creation_date") or calc.get("created_at") or ""
            date_item = QTableWidgetItem(str(date_str))

            name_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            date_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, date_item)

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

    def _new(self):
        # Open AdvancedRetentionWindowQt in "new" mode
        try:
            dlg = AdvancedRetentionWindowQt(self.parent, self.controller, calculation_id=None)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # reload list after save
                self._load_calculations()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de cálculo: {e}", Qt.WindowType.Window)

    def _edit(self):
        calc_id = self._get_selected_id()
        if not calc_id:
            QMessageBox.warning(self, "Sin selección", "Por favor, selecciona un cálculo para editar.", Qt.WindowType.Window)
            return
        try:
            dlg = AdvancedRetentionWindowQt(self.parent, self.controller, calculation_id=calc_id)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # reload list after edit/save
                self._load_calculations()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de edición: {e}", Qt.WindowType.Window)

    def _delete(self):
        calc_id = self._get_selected_id()
        if not calc_id:
            QMessageBox.warning(self, "Sin selección", "Por favor, selecciona un cálculo para eliminar.", Qt.WindowType.Window)
            return

        resp = QMessageBox.question(self, "Confirmar", "¿Estás seguro de que deseas eliminar este cálculo guardado?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            success, message = self.controller.delete_tax_calculation(calc_id)
            if success:
                QMessageBox.information(self, "Éxito", message, Qt.WindowType.Window)
                self._load_calculations()
            else:
                QMessageBox.critical(self, "Error", message, Qt.WindowType.Window)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el cálculo: {e}", Qt.WindowType.Window)