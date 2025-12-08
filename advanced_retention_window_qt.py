from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QWidget,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime


class AdvancedRetentionWindowQt(QDialog):
    """
    Ventana moderna para cálculo avanzado de impuestos y retenciones.

    - Filtros por rango de fechas.
    - Definición de % a pagar sobre el total de factura.
    - Selección de facturas y retenciones.
    - Resumen por moneda y total convertido a RD$.
    - Guardar escenario y exportar PDF (usando controller/report_generator).
    """

    def __init__(self, parent, controller, calculation_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.calculation_id = calculation_id
        self.calculation_name = ""

        self.setWindowTitle("Cálculo de Impuestos y Retenciones")
        self.resize(1100, 700)

        # Habilitar botones de minimizar / maximizar
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        # Data
        self.all_invoices = []
        self.tree_item_states = {}
        self.debug = False

        # UI state
        self.percent_to_pay_edit: QLineEdit | None = None
        self.start_date: QDateEdit | None = None
        self.end_date: QDateEdit | None = None
        self.table: QTableWidget | None = None
        self.results_widget: QGroupBox | None = None
        self.results_layout: QVBoxLayout | None = None

        self._build_ui()

        if self.calculation_id:
            self._load_calculation_data()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        # Card principal
        card = QFrame()
        card.setObjectName("advancedTaxCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(16)

        # Header
        header_layout = QVBoxLayout()
        title = QLabel("Cálculo de Impuestos y Retenciones")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #0F172A;"
        )
        subtitle = QLabel(
            "Selecciona facturas emitidas, define un porcentaje a pagar y aplica "
            "retenciones para obtener el total de impuestos por moneda y en RD$."
        )
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        subtitle.setWordWrap(True)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        card_layout.addLayout(header_layout)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(line)

        # ------------------------------------------------------------------
        # Sección superior: Filtros + Porcentaje
        # ------------------------------------------------------------------
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Grupo filtros
        filter_group = QGroupBox("1. Filtrar Facturas de Ingreso")
        filter_group.setObjectName("dialogGroupBox")
        fg_layout = QVBoxLayout()
        fg_layout.setContentsMargins(10, 10, 10, 10)
        fg_layout.setSpacing(6)

        dates_row = QHBoxLayout()
        dates_row.setSpacing(8)

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("font-size: 12px; color: #374151;")
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("font-size: 12px; color: #374151;")
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())

        dates_row.addWidget(lbl_desde)
        dates_row.addWidget(self.start_date)
        dates_row.addSpacing(12)
        dates_row.addWidget(lbl_hasta)
        dates_row.addWidget(self.end_date)
        dates_row.addStretch()

        fg_layout.addLayout(dates_row)

        btn_search = QPushButton("Buscar Facturas")
        btn_search.setObjectName("primaryButton")
        btn_search.setMinimumHeight(32)
        btn_search.clicked.connect(self._search_invoices)
        fg_layout.addWidget(btn_search)

        filter_group.setLayout(fg_layout)
        top_row.addWidget(filter_group, 2)

        # Grupo porcentaje
        percent_group = QGroupBox("2. Definir Porcentaje a Pagar")
        percent_group.setObjectName("dialogGroupBox")
        pg_layout = QVBoxLayout()
        pg_layout.setContentsMargins(10, 10, 10, 10)
        pg_layout.setSpacing(8)

        lbl_pct = QLabel("% sobre Total Factura:")
        lbl_pct.setStyleSheet("font-size: 12px; color: #374151;")
        pg_layout.addWidget(lbl_pct)

        pct_row = QHBoxLayout()
        pct_row.setSpacing(6)
        self.percent_to_pay_edit = QLineEdit("2.0")
        self.percent_to_pay_edit.setMaximumWidth(80)
        self.percent_to_pay_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.percent_to_pay_edit.textChanged.connect(self._on_percent_change)
        pct_row.addWidget(self.percent_to_pay_edit)
        pct_row.addWidget(QLabel("%"))
        pct_row.addStretch()

        pg_layout.addLayout(pct_row)
        pg_layout.addStretch()

        percent_group.setLayout(pg_layout)
        top_row.addWidget(percent_group, 1)

        card_layout.addLayout(top_row)

        # ------------------------------------------------------------------
        # Tabla de facturas
        # ------------------------------------------------------------------
        tree_group = QGroupBox("3. Seleccionar Facturas y Aplicar Retenciones")
        tree_group.setObjectName("dialogGroupBox")
        tree_layout = QVBoxLayout()
        tree_layout.setContentsMargins(10, 10, 10, 10)
        tree_layout.setSpacing(6)

        cols = [
            "Sel.",
            "Fecha",
            "No. Factura",
            "Empresa",
            "Subtotal",
            "ITBIS",
            "Total Factura",
            "Retención ITBIS?",
            "Valor Retención",
            "% A Pagar",
            "Total Impuestos",
        ]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setMinimumSectionSize(60)

        default_widths = [55, 90, 120, 230, 100, 90, 110, 110, 110, 110, 130]
        for i, w in enumerate(default_widths):
            if i < self.table.columnCount():
                self.table.setColumnWidth(i, w)

        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_table_cell_clicked)

        tree_layout.addWidget(self.table)
        tree_group.setLayout(tree_layout)
        card_layout.addWidget(tree_group, 1)

        # ------------------------------------------------------------------
        # Parte inferior: resultados + acciones
        # ------------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)

        self.results_widget = QGroupBox("4. Resultado Final por Moneda de Origen")
        self.results_widget.setObjectName("dialogGroupBox")
        self.results_layout = QVBoxLayout()
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(4)
        self.results_widget.setLayout(self.results_layout)
        bottom_layout.addWidget(self.results_widget, 2)

        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        btn_save = QPushButton("Guardar Cálculo")
        btn_save.setObjectName("primaryButton")
        btn_save.setMinimumHeight(32)
        btn_save.clicked.connect(self._save_calculation)

        btn_export = QPushButton("Generar Reporte PDF")
        btn_export.setObjectName("secondaryButton")
        btn_export.setMinimumHeight(32)
        btn_export.clicked.connect(self._export_pdf)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("secondaryButton")
        btn_close.setMinimumHeight(28)
        btn_close.clicked.connect(self.reject)

        actions_layout.addWidget(btn_save)
        actions_layout.addWidget(btn_export)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_close)

        bottom_layout.addWidget(actions_widget, 1)

        card_layout.addLayout(bottom_layout)
        root.addWidget(card)

        self.setStyleSheet(
            self.styleSheet()
            + """
        QFrame#advancedTaxCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }
        QGroupBox#dialogGroupBox {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            margin-top: 12px;
            background-color: #F9FAFB;
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
        QDateEdit, QLineEdit {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 18px;
        }
        QDateEdit:focus, QLineEdit:focus {
            border-color: #3B82F6;
        }
        QTableWidget {
            background-color: #FFFFFF;
            gridline-color: #E5E7EB;
            selection-background-color: #DBEAFE;
            selection-color: #111827;
        }
        QHeaderView::section {
            background-color: #F9FAFB;
            padding: 4px;
            border: 1px solid #E5E7EB;
            font-weight: 500;
            color: #4B5563;
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
        """
        )

    # ------------------------------------------------------------------ #
    # Cargar cálculo existente
    # ------------------------------------------------------------------ #
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

        try:
            sd = main.get("start_date")
            ed = main.get("end_date")
            if sd:
                self.start_date.setDate(QDate.fromString(str(sd)[:10], "yyyy-MM-dd"))
            if ed:
                self.end_date.setDate(QDate.fromString(str(ed)[:10], "yyyy-MM-dd"))
            self.percent_to_pay_edit.setText(str(main.get("percent_to_pay", "2.0")))
        except Exception:
            pass

        self._search_invoices(preselected_details=details)

    # ------------------------------------------------------------------ #
    # Búsqueda y poblar tabla
    # ------------------------------------------------------------------ #
    def _search_invoices(self, preselected_details=None):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None

        try:
            raw_invoices = (
                self.controller.get_emitted_invoices_for_period(
                    company_id, start, end
                )
                or []
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener facturas: {e}")
            return

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

        self.table.setRowCount(0)
        self.tree_item_states.clear()

        if not self.all_invoices:
            if not preselected_details:
                QMessageBox.information(
                    self,
                    "Sin Datos",
                    "No se encontraron facturas de ingreso en el rango de fechas.",
                )
            return

        for inv in self.all_invoices:
            inv_id = int(inv.get("id"))

            is_selected = False
            has_retention = False
            if preselected_details and inv_id in preselected_details:
                detail = preselected_details[inv_id]
                is_selected = bool(detail.get("selected", True))
                has_retention = bool(detail.get("retention", False))

            self.tree_item_states[inv_id] = {
                "selected": is_selected,
                "retention": has_retention,
            }

            exchange = float(inv.get("exchange_rate", 1.0) or 1.0)
            itbis_rd = float(inv.get("itbis", 0.0)) * exchange
            total_rd = float(
                inv.get("total_amount_rd")
                or (float(inv.get("total_amount", 0.0)) * exchange)
            )
            subtotal_rd = total_rd - itbis_rd

            row = self.table.rowCount()
            self.table.insertRow(row)

            sel_item = QTableWidgetItem()
            sel_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            sel_item.setCheckState(
                Qt.CheckState.Checked if is_selected else Qt.CheckState.Unchecked
            )
            sel_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, sel_item)

            self.table.setItem(
                row, 1, QTableWidgetItem(str(inv.get("invoice_date", "")))
            )

            inv_item = QTableWidgetItem(str(inv.get("invoice_number", "")))
            inv_item.setData(Qt.ItemDataRole.UserRole, inv_id)
            self.table.setItem(row, 2, inv_item)

            self.table.setItem(
                row, 3, QTableWidgetItem(str(inv.get("third_party_name", "")))
            )

            subtotal_item = QTableWidgetItem(f"{subtotal_rd:,.2f}")
            subtotal_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 4, subtotal_item)

            itbis_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            itbis_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 5, itbis_item)

            total_item = QTableWidgetItem(f"{total_rd:,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 6, total_item)

            ret_item = QTableWidgetItem()
            ret_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            ret_item.setCheckState(
                Qt.CheckState.Checked if has_retention else Qt.CheckState.Unchecked
            )
            ret_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, ret_item)

            rv = QTableWidgetItem("0.00")
            rv.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 8, rv)

            mp = QTableWidgetItem("0.00")
            mp.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 9, mp)

            ti = QTableWidgetItem("0.00")
            ti.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 10, ti)

        self._recalculate_and_update()

    # ------------------------------------------------------------------ #
    # Interacción
    # ------------------------------------------------------------------ #
    def _on_table_cell_clicked(self, row, column):
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

    # ------------------------------------------------------------------ #
    # Recalcular y actualizar resultados
    # ------------------------------------------------------------------ #
    def _recalculate_and_update(self):
        currency_totals: dict[str, float] = {}
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
            invoice_data = next(
                (i for i in self.all_invoices if int(i.get("id")) == inv_id), None
            )
            if not invoice_data:
                continue

            state = self.tree_item_states.get(
                inv_id, {"selected": False, "retention": False}
            )
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

        # Limpiar resultados previos
        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if not currency_totals:
            lbl = QLabel("RD$ 0.00")
            lbl.setStyleSheet(
                "font-weight: 600; font-size: 13px; color: #111827;"
            )
            self.results_layout.addWidget(lbl)
            return

        for currency, total in sorted(currency_totals.items()):
            symbol = currency_symbols.get(currency, currency)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(6)

            badge = QLabel(currency)
            badge.setStyleSheet(
                """
                QLabel {
                    background-color: #EEF2FF;
                    color: #4F46E5;
                    border-radius: 10px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                """
            )

            label = QLabel("Suma Total Impuestos:")
            label.setStyleSheet("font-size: 12px; color: #4B5563;")

            value = QLabel(f"{symbol} {total:,.2f}")
            value.setStyleSheet(
                "font-weight: 600; font-size: 13px; color: #111827;"
            )

            row_layout.addWidget(badge)
            row_layout.addSpacing(4)
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(value)

            self.results_layout.addWidget(row_widget)

        sep_widget = QWidget()
        sep_layout = QHBoxLayout(sep_widget)
        sep_layout.setContentsMargins(0, 4, 0, 4)
        sep_layout.addStretch()
        self.results_layout.addWidget(sep_widget)

        gt_row = QWidget()
        gt_layout = QHBoxLayout(gt_row)
        gt_layout.setContentsMargins(4, 0, 4, 0)
        gt_layout.setSpacing(4)

        gt_label = QLabel("GRAN TOTAL (CONVERTIDO A RD$):")
        gt_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #111827;"
        )
        gt_value = QLabel(f"RD$ {grand_total_rd:,.2f}")
        gt_value.setStyleSheet(
            "font-weight: 700; font-size: 14px; color: #1D4ED8;"
        )

        gt_layout.addWidget(gt_label)
        gt_layout.addStretch()
        gt_layout.addWidget(gt_value)

        self.results_layout.addWidget(gt_row)

    # ------------------------------------------------------------------ #
    # Guardar cálculo
    # ------------------------------------------------------------------ #
    def _save_calculation(self):
        if not any(s.get("selected", False) for s in self.tree_item_states.values()):
            QMessageBox.warning(
                self,
                "Nada que guardar",
                "Debes seleccionar al menos una factura para guardar el cálculo.",
            )
            return

        if not self.calculation_id and not self.calculation_name:
            name, ok = QInputDialog.getText(
                self,
                "Nombre del Cálculo",
                "Introduce un nombre para guardar esta configuración:",
            )
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
                details=self.tree_item_states,
            )
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el cálculo: {e}",
            )

    # ------------------------------------------------------------------ #
    # Exportar PDF (integrado con LogicControllerFirebase / report_generator)
    # ------------------------------------------------------------------ #
    def _export_pdf(self):
        if not any(s.get("selected", False) for s in self.tree_item_states.values()):
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Debes seleccionar al menos una factura para generar el reporte.",
            )
            return

        # Si el cálculo aún no existe, forzamos un guardado rápido
        if not self.calculation_id:
            if not self.calculation_name:
                name, ok = QInputDialog.getText(
                    self,
                    "Nombre del Cálculo",
                    "Antes de exportar, introduce un nombre para guardar este cálculo:",
                )
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
                    details=self.tree_item_states,
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo guardar el cálculo antes de exportar: {e}",
                )
                return

            if not success:
                QMessageBox.critical(
                    self,
                    "Error",
                    message or "No se pudo guardar el cálculo antes de exportar.",
                )
                return

            # Nota: para tener un ID concreto tras guardar, puedes extender
            # save_tax_calculation para que devuelva también calc_id.
            # Aquí asumimos que si calculation_id era None, el usuario volverá
            # a abrir desde la ventana de gestión para un PDF “persistente”.
            if not self.calculation_id:
                QMessageBox.information(
                    self,
                    "Cálculo guardado",
                    "El cálculo se guardó correctamente. "
                    "Para generar un PDF asociado a un ID fijo en Firebase, "
                    "abre este cálculo desde la ventana de gestión y exporta de nuevo.",
                )
                return

        # Si el controller tiene helper dedicado, lo usamos
        if hasattr(self.controller, "open_tax_calculation_pdf"):
            try:
                self.controller.open_tax_calculation_pdf(
                    self.calculation_id,
                    parent=self,
                )
                return
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo generar el PDF: {e}",
                )
                return

        # Fallback si el controller no implementa el helper
        QMessageBox.warning(
            self,
            "Exportar PDF",
            "El controlador actual no implementa 'open_tax_calculation_pdf'.",
        )