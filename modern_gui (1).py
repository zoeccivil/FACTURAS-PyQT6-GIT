"""Modern dashboard UI for Facturas Pro using PyQt6.
Replaces legacy MainApplicationQt layout with SaaS-style dashboard.
"""
from __future__ import annotations

import datetime
import importlib
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

qtawesome_spec = importlib.util.find_spec("qtawesome")
qtawesome = importlib.import_module("qtawesome") if qtawesome_spec else None

STYLESHEET = """
* { font-family: "Inter", "Segoe UI", "Roboto", sans-serif; }
QMainWindow { background: #F8F9FA; }

/* Sidebar */
#sidebar { background: #1E293B; color: #fff; border: none; }
#sidebar QLabel { color: #E5E7EB; }
#sidebar QPushButton { color: #CBD5E1; text-align: left; padding: 10px 14px; border: none; border-radius: 10px; font-weight: 600; }
#sidebar QPushButton:hover { background: #0F172A; color: #fff; }
#sidebar QPushButton[active="true"] { background: #3B82F6; color: #fff; }
#sidebar QPushButton#configButton { color: #94A3B8; font-weight: 600; }
#sidebar QPushButton#configButton:hover { color: #fff; background: #0F172A; }
#companySelector { background: #0F172A; color: #fff; padding: 6px 8px; border-radius: 8px; border: 1px solid #334155; }
#companySelector::drop-down { width: 20px; border: none; }
#sidebarHeader { font-size: 18px; font-weight: 700; color: #fff; }

/* Header */
#header { background: #fff; border-bottom: 1px solid #E5E7EB; padding: 12px 18px; }
#header QLabel#titleLabel { font-size: 20px; font-weight: 700; color: #0F172A; }
#newInvoiceButton { background: #1E293B; color: #fff; border: none; padding: 10px 14px; border-radius: 10px; font-weight: 600; }
#newInvoiceButton:hover { background: #0F172A; }

/* Cards */
QFrame[class="card"] { background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; }
QFrame[class="card"] QLabel[class="title"] { color: #94A3B8; text-transform: uppercase; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }
QFrame[class="card"] QLabel[class="value"] { color: #0F172A; font-size: 22px; font-weight: 800; }
QFrame[class="card"] QLabel[class="sub"] { color: #94A3B8; font-size: 12px; font-weight: 600; }
#incomeCard QLabel[class="value"] { color: #0F172A; }
#expenseCard QLabel[class="value"] { color: #0F172A; }
#netCard QLabel[class="value"] { color: #2563EB; }
#payableCard { border-left: 4px solid #F59E0B; }

/* Filters */
#filterBar { padding: 12px 0; }
#filterBar QComboBox { background: #fff; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px 12px; min-width: 140px; }

/* Table */
#tableContainer { background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; }
#tableHeader { background: #F8FAFC; border-bottom: 1px solid #E2E8F0; padding: 12px 16px; }
#tableHeader QLabel { font-weight: 700; color: #1F2937; }
#tableFilters QPushButton { border: 1px solid transparent; background: transparent; color: #6B7280; font-weight: 700; padding: 6px 12px; border-radius: 8px; }
#tableFilters QPushButton[active="true"] { background: #E0F2FE; color: #2563EB; border-color: #BFDBFE; }
QTableWidget { border: none; gridline-color: #E5E7EB; background: #fff; }
QHeaderView::section { background: #fff; color: #6B7280; padding: 10px 8px; border: none; border-bottom: 1px solid #E5E7EB; font-weight: 700; }
QTableWidget::item { padding: 8px; }
QTableWidget::item:selected { background: #E0F2FE; color: #0F172A; }
QTableWidget { selection-background-color: #E0F2FE; selection-color: #0F172A; }

/* Generic */
QMessageBox { font-size: 12px; }
"""


class ModernMainWindow(QMainWindow):
    """Modern dashboard window preserving controller logic."""

    def __init__(self, controller: Any | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Facturas Pro - Dashboard")
        self.resize(1400, 900)
        self.setStyleSheet(STYLESHEET)

        self.months_map = {
            "Enero": "01",
            "Febrero": "02",
            "Marzo": "03",
            "Abril": "04",
            "Mayo": "05",
            "Junio": "06",
            "Julio": "07",
            "Agosto": "08",
            "Septiembre": "09",
            "Octubre": "10",
            "Noviembre": "11",
            "Diciembre": "12",
        }
        self.current_filter = "all"
        self.companies: List[str] = []

        self._build_ui()
        self._populate_companies()
        self._init_period_selectors()
        self.refresh_all()

    # ------------------- UI CREATION -------------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_sidebar(main_layout)
        self._build_content_area(main_layout)
        self._build_menubar()
        self._initialize_filter_from_controller()

    def _build_sidebar(self, parent_layout: QHBoxLayout) -> None:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)

        # Header
        header_container = QHBoxLayout()
        logo = QLabel("F")
        logo.setFixedSize(32, 32)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background:#3B82F6;color:white;border-radius:8px;font-weight:800;font-size:16px;")
        title = QLabel("Facturas Pro")
        title.setObjectName("sidebarHeader")
        header_container.addWidget(logo)
        header_container.addWidget(title)
        header_container.addStretch()
        sidebar_layout.addLayout(header_container)

        # Company selector
        company_label = QLabel("EMPRESA ACTIVA")
        company_label.setStyleSheet("font-size:10px;font-weight:800;color:#94A3B8;letter-spacing:1px;")
        sidebar_layout.addWidget(company_label)
        self.company_selector = QComboBox()
        self.company_selector.setObjectName("companySelector")
        self.company_selector.currentIndexChanged.connect(self._on_company_changed)
        sidebar_layout.addWidget(self.company_selector)

        sidebar_layout.addSpacing(6)

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "fa5s.chart-pie", lambda: self._set_filter("all")),
            ("Ingresos", "fa5s.file-invoice-dollar", lambda: self._set_filter("income")),
            ("Gastos", "fa5s.shopping-cart", lambda: self._set_filter("expense")),
            ("Calc. Impuestos", "fa5s.calculator", self._trigger_tax_manager),
            ("Resumen ITBIS", "fa5s.percent", self._open_itbis_summary),
            ("Reportes", "fa5s.chart-line", self._open_reports),
        ]
        for text, icon_name, callback in nav_items:
            btn = self._create_nav_button(text, icon_name, callback)
            self.nav_buttons[text] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch(1)

        config_btn = self._create_nav_button("Configuración", "fa5s.cog", self._open_firebase_config)
        config_btn.setObjectName("configButton")
        sidebar_layout.addWidget(config_btn)

        parent_layout.addWidget(sidebar)

    def _build_content_area(self, parent_layout: QHBoxLayout) -> None:
        container = QWidget()
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        self._build_header(content_layout)
        self._build_filters(content_layout)
        self._build_kpis(content_layout)
        self._build_table(content_layout)

        parent_layout.addWidget(container, 1)

    def _build_header(self, parent: QVBoxLayout) -> None:
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)

        self.title_label = QLabel("Resumen Financiero")
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        new_invoice_btn = QPushButton("+ Nueva Factura")
        new_invoice_btn.setObjectName("newInvoiceButton")
        new_invoice_btn.clicked.connect(self._open_add_invoice)
        header_layout.addWidget(new_invoice_btn)
        self.new_invoice_btn = new_invoice_btn

        parent.addWidget(header)

    def _build_filters(self, parent: QVBoxLayout) -> None:
        filter_bar = QFrame()
        filter_bar.setObjectName("filterBar")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        self.month_combo = QComboBox()
        self.year_combo = QComboBox()
        self.month_combo.currentIndexChanged.connect(self.refresh_all)
        self.year_combo.currentIndexChanged.connect(self.refresh_all)

        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(self.year_combo)
        filter_layout.addStretch()

        parent.addWidget(filter_bar)

    def _build_kpis(self, parent: QVBoxLayout) -> None:
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_income = self._create_kpi_card("Total Ingresos", "incomeCard")
        self.card_expense = self._create_kpi_card("Total Gastos", "expenseCard")
        self.card_net = self._create_kpi_card("ITBIS Neto", "netCard")
        self.card_payable = self._create_kpi_card("A Pagar (Estimado)", "payableCard")

        grid.addWidget(self.card_income, 0, 0)
        grid.addWidget(self.card_expense, 0, 1)
        grid.addWidget(self.card_net, 0, 2)
        grid.addWidget(self.card_payable, 0, 3)

        parent.addLayout(grid)

    def _build_table(self, parent: QVBoxLayout) -> None:
        container = QFrame()
        container.setObjectName("tableContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setObjectName("tableHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)

        title = QLabel("Transacciones Recientes")
        header_layout.addWidget(title)
        header_layout.addStretch()

        filters = QFrame()
        filters.setObjectName("tableFilters")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_buttons = {}
        for key, text in [("all", "Todos"), ("income", "Ingresos"), ("expense", "Gastos")]:
            btn = QPushButton(text)
            btn.setProperty("active", "true" if key == "all" else "false")
            btn.clicked.connect(lambda checked=False, k=key: self._set_filter(k))
            self.filter_buttons[key] = btn
            filters_layout.addWidget(btn)
        header_layout.addWidget(filters)

        layout.addWidget(header)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels([
            "Fecha",
            "Tipo",
            "No. Factura",
            "Empresa / Tercero",
            "ITBIS",
            "Monto Total",
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setHighlightSections(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.cellDoubleClicked.connect(self._handle_row_double_click)
        self.table = table
        layout.addWidget(table)

        parent.addWidget(container)

    def _build_menubar(self) -> None:
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        tools_menu = menubar.addMenu("Herramientas")
        migrate_action = QAction("Migrar SQLite → Firebase...", self)
        migrate_action.triggered.connect(self._open_migration_dialog)
        tools_menu.addAction(migrate_action)

        config_action = QAction("Configurar Firebase...", self)
        config_action.triggered.connect(self._open_firebase_config)
        tools_menu.addAction(config_action)

        backup_action = QAction("Crear backup SQL manual", self)
        backup_action.triggered.connect(self._create_backup)
        tools_menu.addAction(backup_action)

    # ------------------- HELPERS -------------------
    def _create_nav_button(self, text: str, icon_name: str, callback) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if qtawesome:
            try:
                icon = qtawesome.icon(icon_name)
                btn.setIcon(icon)
                btn.setIconSize(QSize(16, 16))
            except Exception:
                pass
        btn.clicked.connect(callback)
        return btn

    def _create_kpi_card(self, title: str, obj_name: str) -> QWidget:
        card = QFrame()
        card.setObjectName(obj_name)
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setProperty("class", "title")
        value_label = QLabel("RD$ 0.00")
        value_label.setObjectName("value")
        value_label.setProperty("class", "value")
        sub_label = QLabel("")
        sub_label.setObjectName("sub")
        sub_label.setProperty("class", "sub")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(sub_label)
        layout.addStretch()
        card.value_label = value_label  # type: ignore[attr-defined]
        card.sub_label = sub_label  # type: ignore[attr-defined]
        return card

    def _init_period_selectors(self) -> None:
        current = datetime.date.today()
        months = list(self.months_map.keys())
        self.month_combo.addItems(months)
        current_month_name = months[current.month - 1]
        self.month_combo.setCurrentText(current_month_name)

        years = [str(y) for y in range(current.year - 3, current.year + 3)]
        for y in years:
            self.year_combo.addItem(y)
        self.year_combo.setCurrentText(str(current.year))

    def _initialize_filter_from_controller(self) -> None:
        if self.controller and hasattr(self.controller, "current_tx_filter"):
            try:
                initial_filter = getattr(self.controller, "current_tx_filter", None) or "all"
                if initial_filter in {"all", "income", "expense"}:
                    self.current_filter = initial_filter
            except Exception:
                self.current_filter = "all"
        self._mark_filter_buttons(self.current_filter)
        self._mark_active_nav_from_filter(self.current_filter)

    def _populate_companies(self) -> None:
        self.company_selector.clear()
        companies: List[str] = []
        if self.controller and hasattr(self.controller, "list_companies"):
            try:
                companies = self.controller.list_companies()
            except Exception:
                companies = []
        self.companies = companies
        if companies:
            self.company_selector.addItems(companies)
        else:
            self.company_selector.addItem("Sin empresas")

    # ------------------- ACTIONS -------------------
    def _on_company_changed(self, index: int) -> None:
        if not self.controller or not self.companies:
            return
        try:
            company = self.company_selector.currentText()
            if hasattr(self.controller, "set_active_company"):
                self.controller.set_active_company(company)
        except Exception as exc:
            QMessageBox.warning(self, "Empresa", f"No se pudo cambiar la empresa: {exc}")
        self.refresh_all()

    def _open_add_invoice(self) -> None:
        if self.controller and hasattr(self.controller, "open_add_invoice_window"):
            try:
                self.controller.open_add_invoice_window()
                return
            except Exception as exc:
                QMessageBox.warning(self, "Facturación", f"No se pudo abrir la ventana de factura: {exc}")
        QMessageBox.information(self, "Facturación", "El controlador no tiene implementado open_add_invoice_window().")

    def _trigger_tax_manager(self) -> None:
        if self.controller and hasattr(self.controller, "_open_tax_calculation_manager"):
            try:
                self.controller._open_tax_calculation_manager()
                self._mark_active_nav("Calc. Impuestos")
                return
            except Exception as exc:
                QMessageBox.warning(self, "Impuestos", f"No se pudo abrir el gestor de impuestos: {exc}")
        QMessageBox.information(self, "Impuestos", "No hay gestor de impuestos disponible en el controlador.")

    def _open_reports(self) -> None:
        if self.controller and hasattr(self.controller, "_open_report_window"):
            try:
                self.controller._open_report_window()
                self._mark_active_nav("Reportes")
                return
            except Exception as exc:
                QMessageBox.warning(self, "Reportes", f"No se pudo abrir el módulo de reportes: {exc}")
        QMessageBox.information(self, "Reportes", "El controlador no tiene implementado _open_report_window().")

    def _open_itbis_summary(self) -> None:
        if self.controller and hasattr(self.controller, "_open_itbis_summary"):
            try:
                self.controller._open_itbis_summary()
                self._mark_active_nav("Resumen ITBIS")
                return
            except Exception as exc:
                QMessageBox.warning(self, "ITBIS", f"No se pudo abrir el resumen: {exc}")
        QMessageBox.information(self, "ITBIS", "No hay resumen ITBIS disponible en el controlador.")

    def _open_migration_dialog(self) -> None:
        dialog_module = None
        spec = importlib.util.find_spec("migration_dialog")
        if spec:
            dialog_module = importlib.import_module("migration_dialog")
        if dialog_module and hasattr(dialog_module, "show_migration_dialog"):
            try:
                default_path = ""
                if self.controller and hasattr(self.controller, "get_sqlite_db_path"):
                    default_path = self.controller.get_sqlite_db_path() or ""
                dialog_module.show_migration_dialog(self, default_db_path=default_path)
                return
            except Exception as exc:
                QMessageBox.warning(self, "Migración", f"No se pudo abrir el diálogo de migración: {exc}")
        else:
            QMessageBox.information(self, "Migración", "El módulo migration_dialog no está disponible.")

    def _open_firebase_config(self) -> None:
        dialog_module = None
        spec = importlib.util.find_spec("firebase_config_dialog")
        if spec:
            dialog_module = importlib.import_module("firebase_config_dialog")
        if dialog_module and hasattr(dialog_module, "show_firebase_config_dialog"):
            try:
                dialog_module.show_firebase_config_dialog(self)
                if self.controller and hasattr(self.controller, "on_firebase_config_updated"):
                    try:
                        self.controller.on_firebase_config_updated()
                    except Exception:
                        pass
                return
            except Exception as exc:
                QMessageBox.warning(self, "Firebase", f"No se pudo abrir la configuración: {exc}")
        else:
            QMessageBox.information(self, "Firebase", "El módulo firebase_config_dialog no está disponible.")

    def _create_backup(self) -> None:
        if self.controller and hasattr(self.controller, "create_sql_backup"):
            try:
                path = self.controller.create_sql_backup(retention_days=30)
                QMessageBox.information(
                    self,
                    "Backup SQL",
                    f"Copia creada en:\n{path}\nSe eliminará automáticamente en 30 días.",
                )
                return
            except Exception as exc:
                QMessageBox.warning(self, "Backup", f"No se pudo crear la copia de seguridad: {exc}")
        else:
            QMessageBox.information(self, "Backup", "El controlador no implementa create_sql_backup().")

    def _set_filter(self, tx_filter: str) -> None:
        self.current_filter = tx_filter
        if self.controller and hasattr(self.controller, "set_transaction_filter"):
            try:
                self.controller.set_transaction_filter(tx_filter)
            except Exception:
                pass
        self._mark_active_nav_from_filter(tx_filter)
        self._mark_filter_buttons(tx_filter)
        self.refresh_all()

    def _mark_filter_buttons(self, tx_filter: str) -> None:
        for key, btn in self.filter_buttons.items():
            btn.setProperty("active", "true" if key == tx_filter else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _mark_active_nav_from_filter(self, tx_filter: str) -> None:
        mapping = {
            "all": "Dashboard",
            "income": "Ingresos",
            "expense": "Gastos",
        }
        self._mark_active_nav(mapping.get(tx_filter, "Dashboard"))

    def _mark_active_nav(self, active_text: str) -> None:
        for text, btn in self.nav_buttons.items():
            btn.setProperty("active", "true" if text == active_text else "false")
            btn.setChecked(text == active_text)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh_all(self) -> None:
        self._update_dashboard()
        self._load_transactions()

    def _update_dashboard(self) -> None:
        data = {
            "income": 0,
            "income_itbis": 0,
            "expense": 0,
            "expense_itbis": 0,
            "net_itbis": 0,
            "payable": 0,
        }
        if self.controller and hasattr(self.controller, "_refresh_dashboard"):
            try:
                month, year = self._selected_period()
                refreshed = self.controller._refresh_dashboard(month, year)
                if isinstance(refreshed, dict):
                    data.update(refreshed)
            except Exception:
                pass

        self._set_card_values(self.card_income, data.get("income", 0), data.get("income_itbis", 0))
        self._set_card_values(self.card_expense, data.get("expense", 0), data.get("expense_itbis", 0))
        self._set_card_values(self.card_net, data.get("net_itbis", 0), None)
        self._set_card_values(self.card_payable, data.get("payable", 0), None)

    def _set_card_values(self, card: QFrame, value: float, sub_value: float | None) -> None:
        value_label: QLabel = getattr(card, "value_label")
        sub_label: QLabel = getattr(card, "sub_label")
        value_label.setText(self._format_currency(value))
        if sub_value is None:
            sub_label.setText("")
        else:
            sub_label.setText(f"ITBIS: {self._format_currency(sub_value)}")

    def _load_transactions(self) -> None:
        self.table.setRowCount(0)
        tx_list: List[Dict[str, Any]] = []
        if self.controller and hasattr(self.controller, "_populate_transactions_table"):
            try:
                month, year = self._selected_period()
                tx_list = self.controller._populate_transactions_table(month, year, self.current_filter)
            except Exception:
                tx_list = []
        for tx in tx_list:
            self._add_transaction_row(tx)

    def _add_transaction_row(self, tx: Dict[str, Any]) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            str(tx.get("date", "")),
            str(tx.get("type", "")),
            str(tx.get("number", "")),
            str(tx.get("party", "")),
            self._format_currency(tx.get("itbis", 0)),
            self._format_currency(tx.get("total", 0)),
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col >= 4:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)

    def _handle_row_double_click(self, row: int, column: int) -> None:  # noqa: ARG002
        if not self.controller:
            return
        number_item = self.table.item(row, 2)
        number_value = number_item.text() if number_item else None
        if number_value and hasattr(self.controller, "diagnose_row"):
            try:
                self.controller.diagnose_row(number=number_value)
            except Exception:
                pass

    # ------------------- UTILITIES -------------------
    def _selected_period(self) -> tuple[str, str]:
        month_name = self.month_combo.currentText() or ""
        year = self.year_combo.currentText() or ""
        month = self.months_map.get(month_name, "")
        return month, year

    @staticmethod
    def _format_currency(value: float) -> str:
        try:
            return f"RD$ {float(value):,.2f}"
        except Exception:
            return str(value)


def run_demo(controller: Optional[Any] = None) -> None:
    import sys

    app = QApplication(sys.argv)
    window = ModernMainWindow(controller)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_demo()
