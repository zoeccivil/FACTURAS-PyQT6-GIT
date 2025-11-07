from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt
import typing


class ThirdPartyReportWindowQt(QDialog):
    """
    Ventana PyQt6 para reporte por cliente/proveedor.
    Depende del controller:
      - search_third_parties(query, search_by='name'|'rnc') -> list of {rnc, name}
      - get_report_by_third_party(company_id, rnc) -> dict with summary, emitted_invoices, expense_invoices
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.selected_rnc = None

        self.setWindowTitle("Reporte por Cliente / Proveedor")
        self.resize(900, 600)

        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Search frame
        search_group = QGroupBox("1. Buscar Cliente o Proveedor")
        search_layout = QHBoxLayout()
        lbl = QLabel("Buscar por Nombre o RNC:")
        search_layout.addWidget(lbl)
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._on_keyup)
        # Allow pressing Enter in the search box to try to generate report (convenience)
        self.search_edit.returnPressed.connect(self._generate_report)
        search_layout.addWidget(self.search_edit, 1)
        btn_generate = QPushButton("Generar Reporte")
        btn_generate.clicked.connect(self._generate_report)
        search_layout.addWidget(btn_generate)
        search_group.setLayout(search_layout)
        main.addWidget(search_group)

        # Suggestion list
        self.suggestion_list = QListWidget()
        self.suggestion_list.hide()
        self.suggestion_list.itemClicked.connect(self._on_suggestion_select)
        # Also allow double click to immediately generate
        self.suggestion_list.itemDoubleClicked.connect(lambda item: (self._on_suggestion_select(item), self._generate_report()))
        main.addWidget(self.suggestion_list)

        # Summary
        summary_group = QGroupBox("Resumen de Transacciones")
        summary_layout = QVBoxLayout()
        self.total_ingresos_lbl = QLabel("Total Ingresado de esta Empresa: RD$ 0.00")
        self.total_ingresos_lbl.setStyleSheet("font-weight: bold; color: #006400")
        self.total_gastos_lbl = QLabel("Total Gastado en esta Empresa: RD$ 0.00")
        self.total_gastos_lbl.setStyleSheet("font-weight: bold; color: #C70039")
        summary_layout.addWidget(self.total_ingresos_lbl)
        summary_layout.addWidget(self.total_gastos_lbl)
        summary_group.setLayout(summary_layout)
        main.addWidget(summary_group)

        # Tables
        tables_row = QHBoxLayout()

        self.emitted_table = QTableWidget(0, 4)
        self.emitted_table.setHorizontalHeaderLabels(['Fecha', 'No. Fact.', 'ITBIS RD$', 'Total RD$'])
        eh = self.emitted_table.horizontalHeader()
        eh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh.setStretchLastSection(True)
        tables_row.addWidget(self.emitted_table, 1)

        self.expenses_table = QTableWidget(0, 4)
        self.expenses_table.setHorizontalHeaderLabels(['Fecha', 'No. Fact.', 'ITBIS RD$', 'Total RD$'])
        eh2 = self.expenses_table.horizontalHeader()
        eh2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh2.setStretchLastSection(True)
        tables_row.addWidget(self.expenses_table, 1)

        main.addLayout(tables_row)

    def _on_keyup(self, text: str):
        query = self.search_edit.text().strip()
        self.selected_rnc = None
        # hide suggestion list if short query
        if len(query) < 2:
            self.suggestion_list.hide()
            return
        try:
            # decide search_by
            search_by = 'name' if query[0].isalpha() else 'rnc'
            results = self.controller.search_third_parties(query, search_by=search_by) or []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo buscar terceros: {e}")
            results = []

        # normalize rows to dicts
        normalized = []
        for r in results:
            try:
                normalized.append(dict(r))
            except Exception:
                normalized.append(r if isinstance(r, dict) else r)

        self.suggestion_list.clear()
        if not normalized:
            self.suggestion_list.hide()
            return

        for item in normalized:
            display = f"{item.get('rnc', '')} - {item.get('name', '')}"
            self.suggestion_list.addItem(display)
        self.suggestion_list.show()

    def _on_suggestion_select(self, item):
        # item may be QListWidgetItem
        text = item.text() if hasattr(item, "text") else str(item)
        try:
            rnc, name = text.split(" - ", 1)
        except Exception:
            rnc = text; name = text
        self.selected_rnc = rnc.strip()
        self.search_edit.setText(name.strip())
        self.suggestion_list.hide()

    def _generate_report(self):
        """
        Generate report. If the user didn't explicitly pick a suggestion, try to resolve the
        search entry automatically:
         - if the typed query returns exactly 1 match -> use it
         - if one of the matches has a name equal to the typed query (case-insensitive) -> use it
         - otherwise ask the user to select from the suggestion list
        """
        query_text = self.search_edit.text().strip()

        # If selected_rnc already set (user clicked a suggestion), proceed
        if not self.selected_rnc:
            # minimal validation
            if len(query_text) < 2:
                QMessageBox.warning(self, "Sin Selección", "Por favor, busca y selecciona una empresa de la lista de sugerencias.")
                return

            # try to resolve via search
            try:
                search_by = 'name' if query_text[0].isalpha() else 'rnc'
                raw_results = self.controller.search_third_parties(query_text, search_by=search_by) or []
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo obtener resultados de búsqueda: {e}")
                return

            # normalize
            results = []
            for r in raw_results:
                try:
                    results.append(dict(r))
                except Exception:
                    results.append(r if isinstance(r, dict) else r)

            # if no results -> inform
            if not results:
                QMessageBox.information(self, "Sin Resultados", "No se encontraron empresas con ese criterio.")
                return

            # if exactly one result -> select it automatically
            if len(results) == 1:
                self.selected_rnc = results[0].get('rnc')
                # set search text to the full name for clarity
                self.search_edit.setText(results[0].get('name', self.search_edit.text()))
            else:
                # look for exact name match (case-insensitive)
                lowered = query_text.lower()
                exact = next((r for r in results if str(r.get('name', '')).lower() == lowered or str(r.get('rnc', '')).lower() == lowered), None)
                if exact:
                    self.selected_rnc = exact.get('rnc')
                    self.search_edit.setText(exact.get('name', query_text))
                else:
                    # multiple results and no exact match: show suggestion list and ask user to pick one
                    # populate suggestion list
                    self.suggestion_list.clear()
                    for item in results:
                        display = f"{item.get('rnc', '')} - {item.get('name', '')}"
                        self.suggestion_list.addItem(display)
                    self.suggestion_list.show()
                    QMessageBox.warning(self, "Selecciona Empresa", "Se encontraron varias coincidencias. Por favor, selecciona la empresa correcta de la lista de sugerencias.")
                    return

        # At this point we must have selected_rnc
        if not self.selected_rnc:
            QMessageBox.warning(self, "Sin Selección", "Por favor, busca y selecciona una empresa de la lista de sugerencias.")
            return

        # fetch report
        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            raw = self.controller.get_report_by_third_party(company_id, self.selected_rnc) or {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener el reporte: {e}")
            return

        # normalize lists
        def _normalize_list(lst):
            normalized = []
            for r in lst or []:
                try:
                    normalized.append(dict(r))
                except Exception:
                    normalized.append(r if isinstance(r, dict) else r)
            return normalized

        emitted = _normalize_list(raw.get("emitted_invoices", []))
        expenses = _normalize_list(raw.get("expense_invoices", []))
        summary = raw.get("summary", {})

        # update summary
        self.total_ingresos_lbl.setText(f"Total Ingresado de esta Empresa: RD$ {summary.get('total_ingresos', 0.0):,.2f}")
        self.total_gastos_lbl.setText(f"Total Gastado en esta Empresa: RD$ {summary.get('total_gastos', 0.0):,.2f}")

        # clear tables
        self.emitted_table.setRowCount(0)
        self.expenses_table.setRowCount(0)

        # fill tables
        for inv in emitted:
            row = self.emitted_table.rowCount()
            self.emitted_table.insertRow(row)
            itbis_rd = float(inv.get('itbis', 0.0)) * float(inv.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(inv.get('total_amount_rd', 0.0))
            self.emitted_table.setItem(row, 0, QTableWidgetItem(str(inv.get('invoice_date', ''))))
            self.emitted_table.setItem(row, 1, QTableWidgetItem(str(inv.get('invoice_number', ''))))
            it_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            it_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.emitted_table.setItem(row, 2, it_item)
            tr_item = QTableWidgetItem(f"{total_rd:,.2f}")
            tr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.emitted_table.setItem(row, 3, tr_item)

        for inv in expenses:
            row = self.expenses_table.rowCount()
            self.expenses_table.insertRow(row)
            itbis_rd = float(inv.get('itbis', 0.0)) * float(inv.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(inv.get('total_amount_rd', 0.0))
            self.expenses_table.setItem(row, 0, QTableWidgetItem(str(inv.get('invoice_date', ''))))
            self.expenses_table.setItem(row, 1, QTableWidgetItem(str(inv.get('invoice_number', ''))))
            it_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            it_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 2, it_item)
            tr_item = QTableWidgetItem(f"{total_rd:,.2f}")
            tr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 3, tr_item)