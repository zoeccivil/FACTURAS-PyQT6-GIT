from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QInputDialog, QMessageBox, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import report_generator
from datetime import datetime


class AdvancedRetentionWindowQt(QDialog):
    """
    Ventana PyQt6 para cálculo avanzado de impuestos y retenciones.
    - Permite maximizar/restaurar la ventana.
    - Columnas son interactuables (el usuario puede redimensionarlas) y
      la última columna se estira para llenar el ancho disponible.
    """
    def __init__(self, parent, controller, calculation_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.calculation_id = calculation_id
        self.calculation_name = ""
        self.setWindowTitle("Cálculo de Impuestos y Retenciones")
        self.resize(1100, 700)

        # Habilitar que la ventana tenga botones de minimizar/maximizar y sea redimensionable
        # (QDialog por defecto es redimensionable, pero necesitamos exponer los botones)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setModal(True)
        self.setSizeGripEnabled(True)  # muestra el grip en la esquina para redimensionar

        # Data
        self.all_invoices = []
        self.tree_item_states = {}
        self.debug = False

        # UI state
        self.percent_to_pay_edit = None

        self._build_ui()

        if self.calculation_id:
            self._load_calculation_data()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Top: filters and percent
        top_row = QHBoxLayout()

        # Filter group
        filter_group = QGroupBox("1. Filtrar Facturas de Ingreso")
        filter_layout = QFormLayout()
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addRow(QLabel("Desde:"), self.start_date)
        filter_layout.addRow(QLabel("Hasta:"), self.end_date)
        btn_search = QPushButton("Buscar Facturas")
        btn_search.clicked.connect(self._search_invoices)
        filter_layout.addRow(btn_search)
        filter_group.setLayout(filter_layout)
        top_row.addWidget(filter_group, 1)

        # Percent group
        percent_group = QGroupBox("2. Definir Porcentaje a Pagar")
        percent_layout = QVBoxLayout()
        lbl = QLabel("% sobre Total Factura:")
        percent_layout.addWidget(lbl)
        self.percent_to_pay_edit = QLineEdit("2.0")
        self.percent_to_pay_edit.setMaximumWidth(120)
        self.percent_to_pay_edit.textChanged.connect(self._on_percent_change)
        percent_layout.addWidget(self.percent_to_pay_edit)
        percent_group.setLayout(percent_layout)
        top_row.addWidget(percent_group)

        main.addLayout(top_row)

        # Tree / Table group
        tree_group = QGroupBox("3. Seleccionar Facturas y Aplicar Retenciones")
        tree_layout = QVBoxLayout()

        # Columns:
        cols = [
            "Sel.", "Fecha", "No. Factura", "Empresa",
            "Subtotal", "ITBIS", "Total Factura",
            "Retención ITBIS?", "Valor Retención", "% A Pagar", "Total Impuestos"
        ]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # allow user resizing
        header.setStretchLastSection(True)  # last column fills remaining space
        header.setSectionsMovable(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        # sensible minimums so columns are usable
        header.setMinimumSectionSize(50)
        # Set default column widths (reasonable guesses); user can resize them
        default_widths = [60, 90, 120, 250, 100, 100, 120, 100, 110, 110, 140]
        for i, w in enumerate(default_widths):
            if i < self.table.columnCount():
                self.table.setColumnWidth(i, w)

        # connect click
        self.table.cellClicked.connect(self._on_table_cell_clicked)

        tree_layout.addWidget(self.table)
        tree_group.setLayout(tree_layout)
        main.addWidget(tree_group, 1)

        # Bottom: results and actions
        bottom_layout = QHBoxLayout()

        # Results - dynamic area
        self.results_widget = QGroupBox("4. Resultado Final por Moneda de Origen")
        self.results_layout = QVBoxLayout()
        self.results_widget.setLayout(self.results_layout)
        bottom_layout.addWidget(self.results_widget, 1)

        # Actions
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        btn_save = QPushButton("Guardar Cálculo")
        btn_save.clicked.connect(self._save_calculation)
        btn_export = QPushButton("Generar Reporte PDF")
        btn_export.clicked.connect(self._export_pdf)
        actions_layout.addWidget(btn_save)
        actions_layout.addWidget(btn_export)
        actions_layout.addStretch()
        bottom_layout.addWidget(actions_widget)

        main.addLayout(bottom_layout)

    # -------------------------
    # Load existing calculation
    # -------------------------
    def _load_calculation_data(self):
        try:
            data = self.controller.get_tax_calculation_details(self.calculation_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el cálculo: {e}")
            self.reject()
            return

        if not data:
            QMessageBox.critical(self, "Error", "No se pudo cargar el cálculo.")
            self.reject()
            return

        main = data.get("main", {})
        details = data.get("details", {})

        self.calculation_name = main.get("name", "")
        self.setWindowTitle(f"Editando Cálculo: {self.calculation_name}")

        # set dates and percent
        try:
            sd = main.get("start_date")
            ed = main.get("end_date")
            if sd:
                self.start_date.setDate(QDate.fromString(sd, "yyyy-MM-dd"))
            if ed:
                self.end_date.setDate(QDate.fromString(ed, "yyyy-MM-dd"))
            self.percent_to_pay_edit.setText(str(main.get("percent_to_pay", "2.0")))
        except Exception:
            pass

        # search invoices with preselected details
        self._search_invoices(preselected_details=details)

    # -------------------------
    # Search / populate
    # -------------------------
    def _search_invoices(self, preselected_details=None):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            raw_invoices = self.controller.get_emitted_invoices_for_period(company_id, start, end) or []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener facturas: {e}")
            return

        # Normalizar cada invoice a dict para que invoice.get(...) funcione
        invoices = []
        for inv in raw_invoices:
            try:
                invoices.append(dict(inv))
            except Exception:
                if isinstance(inv, dict):
                    invoices.append(inv)
                else:
                    try:
                        invoices.append({k: inv[k] for k in inv.keys()})
                    except Exception:
                        invoices.append(inv)
        self.all_invoices = invoices

        # limpiar tabla y estados
        self.table.setRowCount(0)
        self.tree_item_states.clear()

        if not self.all_invoices:
            if not preselected_details:
                QMessageBox.information(self, "Sin Datos", "No se encontraron facturas de ingreso en el rango de fechas.")
            return

        # Fill table and initial states
        for inv in self.all_invoices:
            inv_id = int(inv.get("id"))
            # determine selection from preselected_details if any
            is_selected = False
            has_retention = False
            if preselected_details and inv_id in preselected_details:
                detail = preselected_details[inv_id]
                # detail truthy -> retention enabled
                is_selected = True
                has_retention = bool(detail)

            self.tree_item_states[inv_id] = {"selected": is_selected, "retention": has_retention}

            exchange = float(inv.get("exchange_rate", 1.0) or 1.0)
            itbis_rd = float(inv.get("itbis", 0.0)) * exchange
            total_rd = float(inv.get("total_amount_rd") or (float(inv.get("total_amount", 0.0)) * exchange))
            subtotal_rd = total_rd - itbis_rd

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Sel checkbox - use checkstate in item
            sel_item = QTableWidgetItem()
            sel_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            sel_item.setCheckState(Qt.CheckState.Checked if is_selected else Qt.CheckState.Unchecked)
            sel_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, sel_item)

            self.table.setItem(row, 1, QTableWidgetItem(str(inv.get("invoice_date", ""))))
            # invoice number item stores invoice id in UserRole for later ops
            inv_item = QTableWidgetItem(str(inv.get("invoice_number", "")))
            inv_item.setData(Qt.ItemDataRole.UserRole, inv_id)
            self.table.setItem(row, 2, inv_item)

            self.table.setItem(row, 3, QTableWidgetItem(str(inv.get("third_party_name", ""))))

            subtotal_item = QTableWidgetItem(f"{subtotal_rd:,.2f}")
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, subtotal_item)

            itbis_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            itbis_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, itbis_item)

            total_item = QTableWidgetItem(f"{total_rd:,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, total_item)

            # Retention checkbox cell
            ret_item = QTableWidgetItem()
            ret_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            ret_item.setCheckState(Qt.CheckState.Checked if has_retention else Qt.CheckState.Unchecked)
            ret_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, ret_item)

            # Value cells (will be recalculated)
            rv = QTableWidgetItem("0.00")
            rv.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 8, rv)

            mp = QTableWidgetItem("0.00")
            mp.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 9, mp)

            ti = QTableWidgetItem("0.00")
            ti.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 10, ti)

        # After table filled, recalc
        self._recalculate_and_update()

    # -------------------------
    # Interaction handlers
    # -------------------------
    def _on_table_cell_clicked(self, row, column):
        """
        Handle clicks:
         - column 0: toggle selection checkbox
         - column 7: toggle retention checkbox (only if selected)
        """
        try:
            id_item = self.table.item(row, 2)
            if not id_item:
                return
            inv_id = int(id_item.data(Qt.ItemDataRole.UserRole))

            if column == 0:
                cur = self.table.item(row, 0)
                if not cur:
                    return
                new_state = cur.checkState() == Qt.CheckState.Checked
                self.tree_item_states[inv_id]["selected"] = new_state
                if not new_state:
                    self.tree_item_states[inv_id]["retention"] = False
                    retcell = self.table.item(row, 7)
                    if retcell:
                        retcell.setCheckState(Qt.CheckState.Unchecked)

            elif column == 7:
                if not self.tree_item_states.get(inv_id, {}).get("selected"):
                    return
                cur = self.table.item(row, 7)
                if not cur:
                    return
                new_ret = cur.checkState() == Qt.CheckState.Checked
                self.tree_item_states[inv_id]["retention"] = new_ret

            self._recalculate_and_update()
        except Exception as e:
            if self.debug:
                print("_on_table_cell_clicked error:", e)

    def _on_percent_change(self, *_):
        self._recalculate_and_update()

    # -------------------------
    # Recalculate / update UI
    # -------------------------
    def _recalculate_and_update(self):
        currency_totals = {}
        grand_total_rd = 0.0
        currency_symbols = {"USD": "$", "EUR": "€", "RD$": "RD$"}

        try:
            percent = float(self.percent_to_pay_edit.text() or "0") / 100.0
        except Exception:
            percent = 0.0

        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 2)
            if not id_item:
                continue
            inv_id = int(id_item.data(Qt.ItemDataRole.UserRole))
            invoice_data = next((i for i in self.all_invoices if int(i.get("id")) == inv_id), None)
            if not invoice_data:
                continue

            state = self.tree_item_states.get(inv_id, {"selected": False, "retention": False})
            selected = state.get("selected", False)
            retention = state.get("retention", False)

            try:
                itbis_orig = float(invoice_data.get("itbis", 0.0))
                total_orig = float(invoice_data.get("total_amount", 0.0))
                currency = invoice_data.get("currency") or "RD$"
                exchange = float(invoice_data.get("exchange_rate", 1.0) or 1.0)
            except Exception:
                itbis_orig = 0.0
                total_orig = 0.0
                currency = "RD$"
                exchange = 1.0

            valor_retencion_orig = 0.0
            monto_a_pagar_orig = 0.0
            total_impuestos_row_orig = 0.0

            if selected:
                if retention:
                    valor_retencion_orig = itbis_orig * 0.30
                monto_a_pagar_orig = total_orig * percent
                itbis_neto_orig = itbis_orig - valor_retencion_orig
                total_impuestos_row_orig = itbis_neto_orig + monto_a_pagar_orig

                currency_totals.setdefault(currency, 0.0)
                currency_totals[currency] += total_impuestos_row_orig

                grand_total_rd += total_impuestos_row_orig * exchange

            valor_retencion_rd = valor_retencion_orig * exchange
            monto_a_pagar_rd = monto_a_pagar_orig * exchange
            total_impuestos_row_rd = total_impuestos_row_orig * exchange

            try:
                self.table.item(row, 8).setText(f"{valor_retencion_rd:,.2f}")
                self.table.item(row, 9).setText(f"{monto_a_pagar_rd:,.2f}")
                self.table.item(row, 10).setText(f"{total_impuestos_row_rd:,.2f}")
            except Exception:
                pass

        # update results widget (per currency and grand total RD$)
        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if not currency_totals:
            lbl = QLabel("RD$ 0.00")
            lbl.setStyleSheet("font-weight: bold;")
            self.results_layout.addWidget(lbl)
            return

        for currency, total in sorted(currency_totals.items()):
            symbol = currency_symbols.get(currency, currency)
            row = QHBoxLayout()
            label = QLabel(f"Suma Total Impuestos ({currency}):")
            value = QLabel(f"{symbol} {total:,.2f}")
            value.setStyleSheet("font-weight: bold;")
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(value)
            self.results_layout.addWidget(row_widget)

        sep_widget = QWidget()
        sep_layout = QHBoxLayout(sep_widget)
        sep_layout.addStretch()
        self.results_layout.addWidget(sep_widget)

        gt_row = QWidget()
        gt_layout = QHBoxLayout(gt_row)
        gt_label = QLabel("GRAN TOTAL (CONVERTIDO A RD$):")
        gt_value = QLabel(f"RD$ {grand_total_rd:,.2f}")
        gt_value.setStyleSheet("font-weight: bold; color: blue;")
        gt_layout.addWidget(gt_label)
        gt_layout.addStretch()
        gt_layout.addWidget(gt_value)
        self.results_layout.addWidget(gt_row)

    # -------------------------
    # Save calculation
    # -------------------------
    def _save_calculation(self):
        if not any(s.get("selected", False) for s in self.tree_item_states.values()):
            QMessageBox.warning(self, "Nada que guardar", "Debes seleccionar al menos una factura para guardar el cálculo.")
            return

        if not self.calculation_id and not self.calculation_name:
            name, ok = QInputDialog.getText(self, "Nombre del Cálculo", "Introduce un nombre para guardar esta configuración:")
            if not ok or not name:
                return
            self.calculation_name = name

        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            percent_val = float(self.percent_to_pay_edit.text() or "0")
        except Exception:
            percent_val = 0.0

        try:
            success, message = self.controller.save_tax_calculation(
                calc_id=self.calculation_id,
                company_id=company_id,
                name=self.calculation_name,
                start_date=self.start_date.date().toString("yyyy-MM-dd"),
                end_date=self.end_date.date().toString("yyyy-MM-dd"),
                percent=percent_val,
                details=self.tree_item_states
            )
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el cálculo: {e}")

    # -------------------------
    # Export PDF
    # -------------------------
    def _export_pdf(self):
        if not any(s.get("selected", False) for s in self.tree_item_states.values()):
            QMessageBox.warning(self, "Sin Selección", "Debes seleccionar al menos una factura para generar el reporte.")
            return

        # PyQt6: No usar QFileDialog.Options() (ya no existe)
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Reporte de Impuestos", 
            f"Reporte_Impuestos_{datetime.now():%Y%m%d}.pdf", 
            "PDF Files (*.pdf)"
        )
        if not fname:
            return

        selected_invoices_data = []
        currency_totals = {}
        grand_total_rd = 0.0
        try:
            percent = float(self.percent_to_pay_edit.text() or "0") / 100.0
        except Exception:
            percent = 0.0

        for inv_id, state in self.tree_item_states.items():
            if not state.get("selected"):
                continue
            invoice_data = next((i for i in self.all_invoices if int(i.get("id")) == int(inv_id)), None)
            if not invoice_data:
                continue

            itbis_orig = float(invoice_data.get("itbis", 0.0))
            total_orig = float(invoice_data.get("total_amount", 0.0))
            valor_retencion_orig = itbis_orig * 0.30 if state.get("retention") else 0.0
            monto_a_pagar_orig = total_orig * percent
            total_impuestos_row_orig = (itbis_orig - valor_retencion_orig) + monto_a_pagar_orig

            rate = float(invoice_data.get("exchange_rate", 1.0) or 1.0)
            total_rd = total_orig * rate
            total_impuestos_row_rd = total_impuestos_row_orig * rate

            selected_invoices_data.append({
                "fecha": invoice_data.get("invoice_date"),
                "no_fact": invoice_data.get("invoice_number"),
                "empresa": invoice_data.get("third_party_name"),
                "currency": invoice_data.get("currency"),
                "exchange_rate": rate,
                "total_orig": total_orig,
                "total_rd": total_rd,
                "total_imp_orig": total_impuestos_row_orig,
                "total_imp_rd": total_impuestos_row_rd,
            })

            currency_totals.setdefault(invoice_data.get("currency"), 0.0)
            currency_totals[invoice_data.get("currency")] += total_impuestos_row_orig
            grand_total_rd += total_impuestos_row_rd

        summary_data = {
            "percent_to_pay": self.percent_to_pay_edit.text(),
            "currency_totals": currency_totals,
            "grand_total_rd": grand_total_rd
        }

        company_name = ""
        try:
            company_name = self.parent.company_selector.currentText()
        except Exception:
            company_name = ""

        periodo_str = f"Desde {self.start_date.date().toString('yyyy-MM-dd')} hasta {self.end_date.date().toString('yyyy-MM-dd')}"

        try:
            ok, msg = report_generator.generate_advanced_retention_pdf(fname, company_name, periodo_str, summary_data, selected_invoices_data)
            if ok:
                QMessageBox.information(self, "Éxito", msg)
            else:
                QMessageBox.critical(self, "Error", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte: {e}")