from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QGroupBox,
    QFrame,
)
from PyQt6.QtCore import Qt


class ThirdPartyReportWindowQt(QDialog):
    """
    Ventana moderna para reporte por Cliente / Proveedor.

    Depende del controller:
      - search_third_parties(query, search_by='name'|'rnc') -> list[{rnc, name}]
      - get_report_by_third_party(company_id, rnc) -> {
            "summary": {
                "total_ingresos": float,
                "total_gastos": float,
            },
            "emitted_invoices": [...],
            "expense_invoices": [...]
        }
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.selected_rnc: str | None = None

        company_name = (
            self.parent.company_selector.currentText()
            if hasattr(self.parent, "company_selector")
            else ""
        )

        self.setWindowTitle(f"Reporte por Cliente / Proveedor - {company_name}")
        self.resize(1000, 650)

        # Habilitar ventana normal/maximizable
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setSizeGripEnabled(True)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        card = QFrame()
        card.setObjectName("thirdPartyReportCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        # Header: título + empresa actual
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        title_box = QVBoxLayout()
        title = QLabel("Reporte por Cliente / Proveedor")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: #0F172A;")
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("font-size: 11px; color: #6B7280;")
        title_box.addWidget(title)
        title_box.addWidget(self.subtitle_label)
        header_row.addLayout(title_box)
        header_row.addStretch()

        card_layout.addLayout(header_row)

        # Línea separadora
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(sep)

        # 1. Buscar Cliente/Proveedor
        search_group = QGroupBox("1. Buscar Cliente o Proveedor")
        search_group.setObjectName("dialogGroupBox")
        search_layout = QHBoxLayout(search_group)
        search_layout.setContentsMargins(10, 8, 10, 8)
        search_layout.setSpacing(8)

        lbl = QLabel("Buscar por Nombre o RNC:")
        lbl.setStyleSheet("color: #4B5563; font-size: 12px;")
        search_layout.addWidget(lbl)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Escribe parte del nombre o RNC...")
        self.search_edit.textChanged.connect(self._on_keyup)
        self.search_edit.returnPressed.connect(self._generate_report)
        search_layout.addWidget(self.search_edit, 1)

        btn_generate = QPushButton("Generar Reporte")
        btn_generate.setObjectName("primaryButton")
        btn_generate.clicked.connect(self._generate_report)
        search_layout.addWidget(btn_generate)

        card_layout.addWidget(search_group)

        # Lista de sugerencias
        self.suggestion_list = QListWidget()
        self.suggestion_list.hide()
        self.suggestion_list.itemClicked.connect(self._on_suggestion_select)
        self.suggestion_list.itemDoubleClicked.connect(
            lambda item: (self._on_suggestion_select(item), self._generate_report())
        )
        card_layout.addWidget(self.suggestion_list)

        # 2. Resumen
        summary_group = QGroupBox("2. Resumen de Transacciones (RD$)")
        summary_group.setObjectName("dialogGroupBox")
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        summary_layout.setSpacing(4)

        self.total_ingresos_lbl = QLabel("Total Ingresado de esta Empresa: RD$ 0.00")
        self.total_ingresos_lbl.setStyleSheet(
            "font-weight: 600; color: #15803D; font-size: 13px;"
        )

        self.total_gastos_lbl = QLabel("Total Gastado en esta Empresa: RD$ 0.00")
        self.total_gastos_lbl.setStyleSheet(
            "font-weight: 600; color: #B91C1C; font-size: 13px;"
        )

        summary_layout.addWidget(self.total_ingresos_lbl)
        summary_layout.addWidget(self.total_gastos_lbl)

        card_layout.addWidget(summary_group)

        # 3. Tablas de facturas
        tables_row = QHBoxLayout()
        tables_row.setSpacing(12)

        # Emitidas
        emitted_group = QGroupBox("3.A Facturas Emitidas (Ingresos)")
        emitted_group.setObjectName("dialogGroupBox")
        emitted_layout = QVBoxLayout(emitted_group)
        emitted_layout.setContentsMargins(10, 8, 10, 8)

        self.emitted_table = QTableWidget(0, 4)
        self.emitted_table.setHorizontalHeaderLabels(
            ["Fecha", "No. Fact.", "ITBIS RD$", "Total RD$"]
        )
        eh = self.emitted_table.horizontalHeader()
        eh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh.setStretchLastSection(True)
        eh.setMinimumSectionSize(70)
        self.emitted_table.verticalHeader().setVisible(False)
        self.emitted_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        emitted_layout.addWidget(self.emitted_table)
        tables_row.addWidget(emitted_group, 1)

        # Gastos
        expenses_group = QGroupBox("3.B Facturas de Gasto")
        expenses_group.setObjectName("dialogGroupBox")
        expenses_layout = QVBoxLayout(expenses_group)
        expenses_layout.setContentsMargins(10, 8, 10, 8)

        self.expenses_table = QTableWidget(0, 4)
        self.expenses_table.setHorizontalHeaderLabels(
            ["Fecha", "No. Fact.", "ITBIS RD$", "Total RD$"]
        )
        eh2 = self.expenses_table.horizontalHeader()
        eh2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh2.setStretchLastSection(True)
        eh2.setMinimumSectionSize(70)
        self.expenses_table.verticalHeader().setVisible(False)
        self.expenses_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        expenses_layout.addWidget(self.expenses_table)
        tables_row.addWidget(expenses_group, 1)

        card_layout.addLayout(tables_row, 1)

        root.addWidget(card)

        # Estilos
        self._apply_styles()
        self._update_subtitle()

    def _apply_styles(self):
        self.setStyleSheet(
            self.styleSheet()
            + """
        QFrame#thirdPartyReportCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
        }
        QGroupBox#dialogGroupBox {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            margin-top: 10px;
        }
        QGroupBox#dialogGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px 0 4px;
            color: #1F2937;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }
        QLineEdit {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;
        }
        QLineEdit:focus {
            border-color: #3B82F6;
        }
        QListWidget {
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            background-color: #FFFFFF;
            color: #111827;              /* <-- texto oscuro */
        }
        QListWidget::item:selected {
            background-color: #E5E7EB;
            color: #111827;
        }
        QTableWidget {
            background-color: #FFFFFF;
            gridline-color: #E5E7EB;
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
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
            border: none;
        }
        QPushButton#primaryButton:hover {
            background-color: #0F172A;
        }
        """
        )
    def _update_subtitle(self):
        company_name = (
            self.parent.company_selector.currentText()
            if hasattr(self.parent, "company_selector")
            else ""
        )
        self.subtitle_label.setText(f"Empresa activa: {company_name}")

    # ------------------------------------------------------------------
    # Búsqueda de terceros
    # ------------------------------------------------------------------
    def _on_keyup(self, text: str):
        query = self.search_edit.text().strip()
        self.selected_rnc = None

        if len(query) < 2:
            self.suggestion_list.hide()
            return

        try:
            search_by = "name" if query[0].isalpha() else "rnc"
            results = (
                self.controller.search_third_parties(query, search_by=search_by)
                or []
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo buscar terceros: {e}"
            )
            results = []

        normalized: list[dict] = []
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
        text = item.text() if hasattr(item, "text") else str(item)
        try:
            rnc, name = text.split(" - ", 1)
        except Exception:
            rnc = text
            name = text
        self.selected_rnc = rnc.strip()
        self.search_edit.setText(name.strip())
        self.suggestion_list.hide()

    # ------------------------------------------------------------------
    # Generar reporte
    # ------------------------------------------------------------------
    def _generate_report(self):
        """
        Genera el reporte para el tercero seleccionado o, si no lo hay,
        intenta resolver la entrada actual de búsqueda.
        """
        query_text = self.search_edit.text().strip()

        if not self.selected_rnc:
            if len(query_text) < 2:
                QMessageBox.warning(
                    self,
                    "Sin Selección",
                    "Por favor, busca y selecciona una empresa de la lista de sugerencias.",
                )
                return

            try:
                search_by = "name" if query_text[0].isalpha() else "rnc"
                raw_results = (
                    self.controller.search_third_parties(
                        query_text, search_by=search_by
                    )
                    or []
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo obtener resultados de búsqueda: {e}",
                )
                return

            results: list[dict] = []
            for r in raw_results:
                try:
                    results.append(dict(r))
                except Exception:
                    results.append(r if isinstance(r, dict) else r)

            if not results:
                QMessageBox.information(
                    self,
                    "Sin Resultados",
                    "No se encontraron empresas con ese criterio.",
                )
                return

            if len(results) == 1:
                self.selected_rnc = results[0].get("rnc")
                self.search_edit.setText(
                    results[0].get("name", self.search_edit.text())
                )
            else:
                lowered = query_text.lower()
                exact = next(
                    (
                        r
                        for r in results
                        if str(r.get("name", "")).lower() == lowered
                        or str(r.get("rnc", "")).lower() == lowered
                    ),
                    None,
                )
                if exact:
                    self.selected_rnc = exact.get("rnc")
                    self.search_edit.setText(exact.get("name", query_text))
                else:
                    self.suggestion_list.clear()
                    for item in results:
                        display = f"{item.get('rnc', '')} - {item.get('name', '')}"
                        self.suggestion_list.addItem(display)
                    self.suggestion_list.show()
                    QMessageBox.warning(
                        self,
                        "Selecciona Empresa",
                        "Se encontraron varias coincidencias. "
                        "Por favor, selecciona la empresa correcta de la lista de sugerencias.",
                    )
                    return

        if not self.selected_rnc:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, busca y selecciona una empresa de la lista de sugerencias.",
            )
            return

        # Empresa activa
        try:
            company_id = (
                self.parent.get_current_company_id()
                if hasattr(self.parent, "get_current_company_id")
                else None
            )
        except Exception:
            company_id = None

        try:
            raw = (
                self.controller.get_report_by_third_party(
                    company_id, self.selected_rnc
                )
                or {}
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo obtener el reporte: {e}"
            )
            return

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

        # Resumen
        self.total_ingresos_lbl.setText(
            f"Total Ingresado de esta Empresa: RD$ {summary.get('total_ingresos', 0.0):,.2f}"
        )
        self.total_gastos_lbl.setText(
            f"Total Gastado en esta Empresa: RD$ {summary.get('total_gastos', 0.0):,.2f}"
        )

        # Limpiar tablas
        self.emitted_table.setRowCount(0)
        self.expenses_table.setRowCount(0)

        # Emitidas
        for inv in emitted:
            row = self.emitted_table.rowCount()
            self.emitted_table.insertRow(row)
            itbis_rd = float(inv.get("itbis", 0.0)) * float(
                inv.get("exchange_rate", 1.0) or 1.0
            )
            total_rd = float(inv.get("total_amount_rd", 0.0))
            self.emitted_table.setItem(
                row, 0, QTableWidgetItem(str(inv.get("invoice_date", "")))
            )
            self.emitted_table.setItem(
                row, 1, QTableWidgetItem(str(inv.get("invoice_number", "")))
            )
            it_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            it_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.emitted_table.setItem(row, 2, it_item)
            tr_item = QTableWidgetItem(f"{total_rd:,.2f}")
            tr_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.emitted_table.setItem(row, 3, tr_item)

        # Gastos
        for inv in expenses:
            row = self.expenses_table.rowCount()
            self.expenses_table.insertRow(row)
            itbis_rd = float(inv.get("itbis", 0.0)) * float(
                inv.get("exchange_rate", 1.0) or 1.0
            )
            total_rd = float(inv.get("total_amount_rd", 0.0))
            self.expenses_table.setItem(
                row, 0, QTableWidgetItem(str(inv.get("invoice_date", "")))
            )
            self.expenses_table.setItem(
                row, 1, QTableWidgetItem(str(inv.get("invoice_number", "")))
            )
            it_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
            it_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.expenses_table.setItem(row, 2, it_item)
            tr_item = QTableWidgetItem(f"{total_rd:,.2f}")
            tr_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.expenses_table.setItem(row, 3, tr_item)