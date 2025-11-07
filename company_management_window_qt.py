# PyQt6 migration of the old tkinter company management window.
# Provides:
#  - CompanyDialog: modal dialog to add / edit a single company (name, rnc, address)
#  - CompanyManagementWindow: modal dialog to list / add / edit / delete companies
#
# The dialog talks to a "controller" object. It tries to be flexible and accept several
# controller method names/signatures used across different versions:
#   - get_all_companies() or get_companies() -> list[dict]
#   - get_company_details(id) or get_company(id) -> dict
#   - add_company(name, rnc) OR add_company(data:dict) -> (ok, msg_or_id)
#   - update_company(id, name, rnc, address) OR update_company(id, data:dict) -> (ok,msg)
#   - delete_company(id) -> (ok,msg)
#
# The returned tuples are interpreted permissively: if add_company returns (True, id) we treat it as success.
# If the controller is missing methods the UI will show warnings instead of crashing.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialogButtonBox, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from typing import Optional
from pathlib import Path


class CompanyDialog(QDialog):
    """
    Modal dialog to add / edit a company.
    - existing_data: optional dict with keys 'name','rnc','address'
    On accept, self.result will contain the dict with those keys.
    """
    def __init__(self, parent: Optional[QWidget] = None, title: str = "Empresa", existing_data: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result = None
        self._build_ui()
        if existing_data:
            self._load_existing(existing_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_le = QLineEdit()
        self.rnc_le = QLineEdit()
        self.address_le = QLineEdit()
        form.addRow(QLabel("Nombre de la Empresa:"), self.name_le)
        form.addRow(QLabel("RNC / Identificación:"), self.rnc_le)
        form.addRow(QLabel("Dirección:"), self.address_le)
        layout.addLayout(form)

        bb = QDialogButtonBox()
        btn_ok = QPushButton("Guardar")
        btn_cancel = QPushButton("Cancelar")
        bb.addButton(btn_ok, QDialogButtonBox.ButtonRole.AcceptRole)
        bb.addButton(btn_cancel, QDialogButtonBox.ButtonRole.RejectRole)
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(bb)

    def _load_existing(self, d: dict):
        self.name_le.setText(str(d.get("name", "") or ""))
        self.rnc_le.setText(str(d.get("rnc", "") or ""))
        self.address_le.setText(str(d.get("address", "") or ""))

    def _on_ok(self):
        name = self.name_le.text().strip()
        rnc = self.rnc_le.text().strip()
        address = self.address_le.text().strip()
        if not name or not rnc:
            QMessageBox.warning(self, "Campos requeridos", "El nombre y el RNC son obligatorios.", parent=self)
            return
        self.result = {"name": name, "rnc": rnc, "address": address}
        self.accept()


class CompanyManagementWindow(QDialog):
    """
    Window to manage companies (list, add, edit, delete).
    Constructor: CompanyManagementWindow(parent, controller)
    """
    def __init__(self, parent: Optional[QWidget] = None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        self.setWindowTitle("Gestionar Empresas")
        self.resize(760, 420)
        self._build_ui()
        self._load_companies()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "RNC"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(lambda _: self._on_edit())
        main.addWidget(self.table)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Añadir Nueva")
        self.btn_edit = QPushButton("Editar Seleccionada")
        self.btn_delete = QPushButton("Eliminar Seleccionada")
        self.btn_refresh = QPushButton("Refrescar")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_refresh)
        main.addLayout(btn_row)

        # Close button at bottom
        bottom_row = QHBoxLayout()
        bottom_row.addItem(QSpacerItem(20, 12, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.clicked.connect(self.close)
        bottom_row.addWidget(self.btn_close)
        main.addLayout(bottom_row)

        # Connect actions
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_refresh.clicked.connect(self._load_companies)

    # -------------------------
    # Data loading / helpers
    # -------------------------
    def _load_companies(self):
        """Load companies from controller into table."""
        self.table.setRowCount(0)
        companies = []
        try:
            if self.controller:
                if hasattr(self.controller, "get_all_companies"):
                    companies = self.controller.get_all_companies() or []
                elif hasattr(self.controller, "get_companies"):
                    companies = self.controller.get_companies() or []
                else:
                    QMessageBox.warning(self, "Controlador No Disponible", "El controlador no implementa get_companies/get_all_companies.")
                    return
            else:
                QMessageBox.warning(self, "Controlador", "No se proporcionó controlador.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista de empresas:\n{e}")
            return

        for comp in companies:
            row = self.table.rowCount()
            self.table.insertRow(row)
            id_item = QTableWidgetItem(str(comp.get("id", "")))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(comp.get("name", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(comp.get("rnc", ""))))

        # If parent exposes a method to repopulate selectors (like original), call it
        try:
            if self.parent and hasattr(self.parent, "_populate_company_selector"):
                self.parent._populate_company_selector()
        except Exception:
            pass

    def _get_selected_company_id(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Sin selección", "Por favor, selecciona una empresa de la lista.", parent=self)
            return None
        try:
            # first column holds id
            row = sel[0].row()
            item = self.table.item(row, 0)
            return int(item.text())
        except Exception:
            QMessageBox.warning(self, "ID inválido", "No se pudo determinar el ID de la empresa seleccionada.", parent=self)
            return None

    # -------------------------
    # Actions: Add / Edit / Delete
    # -------------------------
    def _on_add(self):
        dlg = CompanyDialog(self, "Nueva Empresa")
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result:
            return
        data = dlg.result  # dict with name,rnc,address

        # Try flexible add_company signatures
        try:
            if hasattr(self.controller, "add_company"):
                # try (data dict) first
                try:
                    res = self.controller.add_company(data)
                except TypeError:
                    # older signature add_company(name, rnc)
                    res = self.controller.add_company(data["name"], data["rnc"])
                # interpret response
                if isinstance(res, tuple):
                    ok, msg = res[0], (res[1] if len(res) > 1 else "")
                elif isinstance(res, bool):
                    ok, msg = res, ""
                else:
                    # maybe returned inserted id
                    ok, msg = True, str(res)
                if ok:
                    # If initial add_company didn't store address, try update_company to set it
                    # (some controllers had two-step flow)
                    try:
                        if hasattr(self.controller, "get_all_companies"):
                            # find the inserted record by name+rnc (best-effort)
                            companies = self.controller.get_all_companies() or []
                        elif hasattr(self.controller, "get_companies"):
                            companies = self.controller.get_companies() or []
                        else:
                            companies = []
                        inserted = next((c for c in companies if c.get("name") == data["name"] and c.get("rnc") == data["rnc"]), None)
                        if inserted and hasattr(self.controller, "update_company"):
                            try:
                                # try update_company(id, data) signature
                                self.controller.update_company(inserted.get("id"), data)
                            except TypeError:
                                # fallback to older signature update_company(id, name, rnc, address)
                                try:
                                    self.controller.update_company(inserted.get("id"), data["name"], data["rnc"], data.get("address", ""))
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    QMessageBox.information(self, "Éxito", "Empresa creada correctamente.", parent=self)
                    self._load_companies()
                else:
                    QMessageBox.warning(self, "Error", msg or "No se pudo crear la empresa.", parent=self)
            else:
                QMessageBox.warning(self, "Advertencia", "El controlador no implementa add_company.", parent=self)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la empresa:\n{e}", parent=self)

    def _on_edit(self):
        cid = self._get_selected_company_id()
        if not cid:
            return
        # fetch existing data from controller (try multiple names)
        try:
            company = {}
            if hasattr(self.controller, "get_company_details"):
                company = self.controller.get_company_details(cid) or {}
            elif hasattr(self.controller, "get_company"):
                company = self.controller.get_company(cid) or {}
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"No se pudo obtener datos de la empresa: {e}")
            company = {}

        dlg = CompanyDialog(self, "Editar Empresa", existing_data=company)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result:
            return
        data = dlg.result
        try:
            if hasattr(self.controller, "update_company"):
                try:
                    res = self.controller.update_company(cid, data)
                except TypeError:
                    # fallback older signature
                    res = self.controller.update_company(cid, data["name"], data["rnc"], data.get("address", ""))
                if isinstance(res, tuple):
                    ok, msg = res[0], (res[1] if len(res) > 1 else "")
                elif isinstance(res, bool):
                    ok, msg = res, ""
                else:
                    ok, msg = True, str(res)
                if ok:
                    QMessageBox.information(self, "Éxito", "Empresa actualizada correctamente.")
                    self._load_companies()
                else:
                    QMessageBox.warning(self, "Error", msg or "No se pudo actualizar la empresa.")
            else:
                QMessageBox.warning(self, "Advertencia", "El controlador no implementa update_company.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la empresa:\n{e}")
            
    def _on_delete(self):
        cid = self._get_selected_company_id()
        if not cid:
            return
        # get details for confirmation
        try:
            company = {}
            if hasattr(self.controller, "get_company_details"):
                company = self.controller.get_company_details(cid) or {}
            elif hasattr(self.controller, "get_company"):
                company = self.controller.get_company(cid) or {}
        except Exception:
            company = {}
        name = company.get("name", "N/A")
        rnc = company.get("rnc", "N/A")
        text = (f"¿Estás seguro de que quieres eliminar la empresa '{name}' (RNC: {rnc})?\n\n"
                "¡ATENCIÓN! Se borrarán TODAS las facturas asociadas.")
        resp = QMessageBox.question(self, "Confirmar Eliminación", text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, parent=self)
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            if hasattr(self.controller, "delete_company"):
                res = self.controller.delete_company(cid)
                if isinstance(res, tuple):
                    ok, msg = res[0], (res[1] if len(res) > 1 else "")
                elif isinstance(res, bool):
                    ok, msg = res, ""
                else:
                    ok, msg = True, str(res)
                if ok:
                    QMessageBox.information(self, "Éxito", "Empresa eliminada correctamente.", parent=self)
                    self._load_companies()
                else:
                    QMessageBox.warning(self, "Error", msg or "No se pudo eliminar la empresa.", parent=self)
            else:
                QMessageBox.warning(self, "Advertencia", "El controlador no implementa delete_company.", parent=self)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la empresa:\n{e}", parent=self)