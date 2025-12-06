# -*- coding: utf-8 -*-
"""
Modern Dashboard GUI for FACTURAS-PyQT6-GIT

- Refactors legacy MainApplicationQt (from app_gui_qt.py) into a modern SaaS-style dashboard.
- Preserves existing business logic and controller connections.
- Adds Tools menu with:
  - Firebase Config dialog (firebase_config_dialog.py)
  - SQLite → Firebase Migration dialog (migration_dialog.py)
- Does NOT replace SQL usage in-app logic; Firebase will be used as the main data source,
  and SQL is only touched for daily backups that auto-expire in 30 days (handled by controller/services).
"""

from typing import Optional, Callable, Any
import os

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction, QIcon
from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QSpacerItem, QSizePolicy, QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenuBar, QMenu, QApplication, QMessageBox
)

# Icons: try to use qtawesome, fallback to plain text
try:
    import qtawesome as qta
    HAS_QTAWESOME = True
except Exception:
    HAS_QTAWESOME = False

# Import dialogs
try:
    from firebase_config_dialog import show_firebase_config_dialog
except Exception:
    show_firebase_config_dialog = None

try:
    from migration_dialog import show_migration_dialog
except Exception:
    show_migration_dialog = None


STYLESHEET = """
/* Global */
QMainWindow {
    background: #F8F9FA;
}
* {
    font-family: "Inter", "Segoe UI", "Roboto", sans-serif;
    font-size: 10pt;
}

/* Sidebar */
#Sidebar {
    background: #1E293B;
    color: #FFFFFF;
    border: none;
}
#Sidebar QLabel {
    color: #E5E7EB;
}
#Sidebar QPushButton {
    color: #CBD5E1;
    background: transparent;
    border: none;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
}
#Sidebar QPushButton:hover {
    background: #0F172A;
    color: #FFFFFF;
}
#Sidebar QPushButton[active="true"] {
    background: #3B82F6;
    color: #FFFFFF;
}
#Sidebar QComboBox {
    background: #0F172A;
    color: #FFFFFF;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 8px;
}
#Sidebar QComboBox::drop-down {
    border: none;
}

/* Header */
#Header {
    background: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
}
#Header QLabel#Title {
    color: #0F172A;
    font-weight: 700;
    font-size: 14pt;
}
#Header QPushButton#PrimaryAction {
    background: #0F172A;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
}
#Header QPushButton#PrimaryAction:hover {
    background: #1F2937;
}

/* Cards */
.Card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px;
}
.Card QLabel.Title {
    color: #6B7280;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 9pt;
}
.Card QLabel.Value {
    color: #0F172A;
    font-weight: 700;
    font-size: 16pt;
}
.Card QLabel.SubText {
    color: #9CA3AF;
    font-size: 9pt;
}
.Card[data="income"] QLabel.Value {
    color: #10B981;
}
.Card[data="expense"] QLabel.Value {
    color: #EF4444;
}
.Card[data="net"] QLabel.Value {
    color: #2563EB;
}
.Card[data="payable"] {
    border-left: 4px solid #F59E0B;
}

/* Filters */
#Filters {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 8px 12px;
}

/* Table */
#TransactionsGroup {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
}
#TransactionsHeader {
    background: #F9FAFB;
    border-bottom: 1px solid #E5E7EB;
}
QTableWidget {
    background: #FFFFFF;
    gridline-color: #F1F5F9;
    selection-background-color: #DBEAFE; /* blue-100 */
    selection-color: #1E293B;
    outline: 0;
}
QHeaderView::section {
    background: #FFFFFF;
    color: #6B7280;
    border: none;
    border-bottom: 1px solid #F1F5F9;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item {
    padding: 8px;
}

/* Buttons */
QPushButton.Primary {
    background: #3B82F6;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton.Primary:hover {
    background: #2563EB;
}
QPushButton.Secondary {
    background: #E5E7EB;
    color: #111827;
    border: none;
    border-radius: 8px;
    padding: 6px 10px;
}
QPushButton.Secondary:hover {
    background: #D1D5DB;
}

/* Menu bar */
QMenuBar {
    background: #FFFFFF;
}
QMenuBar::item:selected {
    background: #E5E7EB;
    border-radius: 6px;
}
QMenu {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
}
QMenu::item:selected {
    background: #E5E7EB;
}
"""


def _icon(name: str, default_text: str = "") -> Optional[QIcon]:
    """
    Returns a QIcon using qtawesome if available.
    name examples: 'fa5s.chart-pie', 'fa5s.file-invoice-dollar'
    """
    if HAS_QTAWESOME:
        try:
            return qta.icon(name)
        except Exception:
            pass
    # Fallback: return None, caller can set text-only buttons
    return None


class ModernMainWindow(QMainWindow):
    """
    Modern dashboard that wraps legacy MainApplicationQt controller and logic.
    - Keeps references to controller and preserves existing methods if present:
      _refresh_dashboard, _populate_transactions_table, save_callback,
      _open_tax_calculation_manager, _open_report_window, diagnose_row, etc.
    """

    def __init__(self, controller: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller

        # Window setup
        self.setWindowTitle("Facturas Pro - Dashboard")
        self.setMinimumSize(1100, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        self.sidebar.setObjectName("Sidebar")

        # Content area
        self.content = self._build_content_area()

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content, 1)

        # Menu bar
        self._build_menu_bar()

        # Apply stylesheet
        self.setStyleSheet(STYLESHEET)

        # Initial populate
        self._safe_refresh_dashboard()
        self._safe_populate_transactions_table()

    # ===== Menus =====
    def _build_menu_bar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        tools_menu = QMenu("Herramientas", self)
        menubar.addMenu(tools_menu)

        # Firebase Config
        act_config = QAction("Configurar Firebase…", self)
        act_config.triggered.connect(self._open_firebase_config_dialog)
        tools_menu.addAction(act_config)

        # SQLite → Firebase Migration
        act_migrate = QAction("Migrar SQLite → Firebase…", self)
        act_migrate.triggered.connect(self._open_migration_dialog)
        tools_menu.addAction(act_migrate)

        # Backup manual (optional hook to controller)
        act_backup = QAction("Crear backup SQL manual", self)
        act_backup.triggered.connect(self._trigger_manual_backup)
        tools_menu.addAction(act_backup)

    def _open_firebase_config_dialog(self):
        if not show_firebase_config_dialog:
            QMessageBox.warning(self, "No disponible", "El diálogo de configuración de Firebase no está disponible.")
            return
        ok = show_firebase_config_dialog(self)
        if ok:
            QMessageBox.information(self, "Firebase", "Configuración guardada correctamente.")
            # Optional: notify controller to reconnect
            if hasattr(self.controller, "on_firebase_config_updated"):
                try:
                    self.controller.on_firebase_config_updated()
                except Exception:
                    pass

    def _open_migration_dialog(self):
        if not show_migration_dialog:
            QMessageBox.warning(self, "No disponible", "El diálogo de migración no está disponible.")
            return
        # Optional: default db path from controller
        default_db_path = ""
        if hasattr(self.controller, "get_sqlite_db_path"):
            try:
                default_db_path = self.controller.get_sqlite_db_path() or ""
            except Exception:
                default_db_path = ""
        show_migration_dialog(self, default_db_path=default_db_path)

    def _trigger_manual_backup(self):
        # Manual backup trigger; actual implementation in controller
        if hasattr(self.controller, "create_sql_backup"):
            try:
                path = self.controller.create_sql_backup(retention_days=30)
                QMessageBox.information(self, "Backup creado", f"Backup SQL creado:\n{path}\n(Se eliminará automáticamente en 30 días)")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el backup SQL:\n{e}")
        else:
            QMessageBox.information(self, "No disponible", "La función de backup no está disponible en el controlador.")

    def _open_tax_calculation_manager(self):
        """
        Opens the tax calculation management window.
        This window allows users to create and manage tax calculations.
        """
        try:
            from tax_calculation_management_window_qt import TaxCalculationManagementWindowQt
            dlg = TaxCalculationManagementWindowQt(self, self.controller)
            dlg.exec()
            # Refresh dashboard after closing (in case changes were made)
            self._safe_refresh_dashboard()
        except ImportError as e:
            QMessageBox.warning(
                self, 
                "Módulo no disponible", 
                f"El módulo de cálculo de impuestos no está disponible:\n{e}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"No se pudo abrir el gestor de cálculo de impuestos:\n{e}"
            )

    # ===== Sidebar =====
    def _build_sidebar(self) -> QWidget:
        sb = QFrame()
        sb.setFixedWidth(250)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Header/logo
        header = QHBoxLayout()
        logo = QLabel("F")
        logo.setFixedSize(32, 32)
        logo.setStyleSheet("background:#3B82F6;color:#FFFFFF;border-radius:6px;font-weight:bold;"
                           "font-size:16pt; text-align:center;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Facturas Pro")
        f = QFont()
        f.setBold(True)
        f.setPointSize(12)
        title.setFont(f)

        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        lay.addLayout(header)

        # Company selector
        lbl_company = QLabel("EMPRESA ACTIVA")
        lbl_company.setStyleSheet("color:#94A3B8; font-size:8pt; font-weight:bold; letter-spacing:1px;")
        lay.addWidget(lbl_company)

        self.company_combo = QComboBox()
        self.company_combo.addItem("Zoec Civil Srl")
        # Hook to controller for companies
        if hasattr(self.controller, "list_companies"):
            try:
                self.company_combo.clear()
                for c in self.controller.list_companies() or []:
                    self.company_combo.addItem(str(c))
            except Exception:
                pass
        self.company_combo.currentIndexChanged.connect(self._on_company_changed)
        lay.addWidget(self.company_combo)

        # Navigation
        def add_nav(text: str, icon_name: Optional[str], slot: Callable, active=False) -> QPushButton:
            btn = QPushButton(text)
            btn.setProperty("active", "true" if active else "false")
            ic = _icon(icon_name) if icon_name else None
            if ic:
                btn.setIcon(ic)
                btn.setIconSize(QSize(16, 16))
            btn.clicked.connect(slot)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn

        self.btn_dashboard = add_nav("Dashboard", "fa5s.chart-pie", self._nav_dashboard, active=True)
        self.btn_ingresos = add_nav("Ingresos", "fa5s.file-invoice-dollar", self._nav_ingresos, active=False)
        self.btn_gastos = add_nav("Gastos", "fa5s.shopping-cart", self._nav_gastos, active=False)
        self.btn_tax = add_nav("Calc. Impuestos", "fa5s.percent", self._nav_tax, active=False)  # CRITICAL: calls _open_tax_calculation_manager
        self.btn_itbis = add_nav("Resumen ITBIS", "fa5s.coins", self._nav_itbis, active=False)
        self.btn_reportes = add_nav("Reportes", "fa5s.chart-line", self._nav_reportes, active=False)

        for b in [self.btn_dashboard, self.btn_ingresos, self.btn_gastos, self.btn_tax, self.btn_itbis, self.btn_reportes]:
            lay.addWidget(b)

        lay.addStretch()

        # Settings at bottom
        self.btn_settings = add_nav("Configuración", "fa5s.cog", self._nav_settings, active=False)
        lay.addWidget(self.btn_settings)

        return sb

    # ===== Content Area =====
    def _build_content_area(self) -> QWidget:
        content = QFrame()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(64)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        self.lbl_title = QLabel("Resumen Financiero")
        self.lbl_title.setObjectName("Title")
        hl.addWidget(self.lbl_title)

        hl.addStretch()

        self.btn_new_invoice = QPushButton("+ Nueva Factura")
        self.btn_new_invoice.setObjectName("PrimaryAction")
        self.btn_new_invoice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_invoice.clicked.connect(self._new_invoice)
        # icon
        ic = _icon("fa5s.plus")
        if ic:
            self.btn_new_invoice.setIcon(ic)
        hl.addWidget(self.btn_new_invoice)

        outer.addWidget(header)

        # Scrollable area replacement: just vertical stack
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 16, 16, 16)
        inner.setSpacing(12)

        # Filters
        filters = QFrame()
        filters.setObjectName("Filters")
        fl = QHBoxLayout(filters)
        fl.setContentsMargins(10, 6, 10, 6)
        fl.setSpacing(8)

        self.cmb_month = QComboBox()
        self.cmb_year = QComboBox()
        self.cmb_month.addItems(["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.cmb_year.addItems([str(y) for y in range(2022, 2031)])
        self.cmb_month.currentIndexChanged.connect(self._on_filters_changed)
        self.cmb_year.currentIndexChanged.connect(self._on_filters_changed)
        fl.addWidget(QLabel("Mes:"))
        fl.addWidget(self.cmb_month)
        fl.addWidget(QLabel("Año:"))
        fl.addWidget(self.cmb_year)
        fl.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        inner.addWidget(filters)

        # KPI Cards grid
        kpis_group = QGroupBox()
        kpis_layout = QGridLayout(kpis_group)
        kpis_layout.setContentsMargins(0, 0, 0, 0)
        kpis_layout.setHorizontalSpacing(12)
        kpis_layout.setVerticalSpacing(12)

        self.card_income = self._build_card("Total Ingresos", "RD$ 0.00", "ITBIS: RD$ 0.00", data_role="income")
        self.card_expense = self._build_card("Total Gastos", "RD$ 0.00", "ITBIS: RD$ 0.00", data_role="expense")
        self.card_net = self._build_card("ITBIS Neto", "RD$ 0.00", "Diferencia (Ingreso - Gasto)", data_role="net")
        self.card_payable = self._build_card("A Pagar (Estimado)", "RD$ 0.00", "", data_role="payable")

        kpis_layout.addWidget(self.card_income, 0, 0)
        kpis_layout.addWidget(self.card_expense, 0, 1)
        kpis_layout.addWidget(self.card_net, 0, 2)
        kpis_layout.addWidget(self.card_payable, 0, 3)

        inner.addWidget(kpis_group)

        # Transactions table section
        trans_group = QFrame()
        trans_group.setObjectName("TransactionsGroup")
        tg = QVBoxLayout(trans_group)
        tg.setContentsMargins(0, 0, 0, 0)
        tg.setSpacing(0)

        trans_header = QFrame()
        trans_header.setObjectName("TransactionsHeader")
        thl = QHBoxLayout(trans_header)
        thl.setContentsMargins(12, 8, 12, 8)
        thl.setSpacing(8)

        thl.addWidget(QLabel("Transacciones Recientes"))
        thl.addStretch()

        self.btn_filter_all = QPushButton("Todos")
        self.btn_filter_all.setProperty("class", "Secondary")
        self.btn_filter_all.clicked.connect(lambda: self._apply_type_filter(None))
        self.btn_filter_inc = QPushButton("Ingresos")
        self.btn_filter_inc.setProperty("class", "Secondary")
        self.btn_filter_inc.clicked.connect(lambda: self._apply_type_filter("INGRESO"))
        self.btn_filter_exp = QPushButton("Gastos")
        self.btn_filter_exp.setProperty("class", "Secondary")
        self.btn_filter_exp.clicked.connect(lambda: self._apply_type_filter("GASTO"))

        for b in [self.btn_filter_all, self.btn_filter_inc, self.btn_filter_exp]:
            thl.addWidget(b)

        tg.addWidget(trans_header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Fecha", "Tipo", "No. Factura", "Empresa / Tercero", "ITBIS", "Monto Total", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        tg.addWidget(self.table)

        inner.addWidget(trans_group)

        # pack inner
        content_l = QVBoxLayout()
        content_l.setContentsMargins(0, 0, 0, 0)
        content_l.setSpacing(0)
        content_l.addLayout(inner)
        content.setLayout(content_l)
        return content

    def _build_card(self, title: str, value: str, subtext: str, data_role: str) -> QWidget:
        card = QFrame()
        card.setProperty("class", "Card")
        card.setProperty("data", data_role)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "Title")
        lbl_value = QLabel(value)
        lbl_value.setProperty("class", "Value")
        lbl_sub = QLabel(subtext)
        lbl_sub.setProperty("class", "SubText")

        # store refs to update later
        card.lbl_value = lbl_value
        card.lbl_sub = lbl_sub

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        if subtext:
            layout.addWidget(lbl_sub)
        return card

    # ===== Navigation slots =====
    def _nav_dashboard(self):
        self.lbl_title.setText("Resumen Financiero")
        self._set_active(self.btn_dashboard)

    def _nav_ingresos(self):
        self.lbl_title.setText("Ingresos")
        self._set_active(self.btn_ingresos)
        self._apply_type_filter("INGRESO")

    def _nav_gastos(self):
        self.lbl_title.setText("Gastos")
        self._set_active(self.btn_gastos)
        self._apply_type_filter("GASTO")

    def _nav_tax(self):
        # Call the tax calculation manager
        self._open_tax_calculation_manager()
        self._set_active(self.btn_tax)

    def _nav_itbis(self):
        self.lbl_title.setText("Resumen ITBIS")
        self._set_active(self.btn_itbis)
        # Optional: could open a dedicated window if controller provides it
        if hasattr(self.controller, "_open_itbis_summary"):
            try:
                self.controller._open_itbis_summary()
            except Exception:
                pass

    def _nav_reportes(self):
        self.lbl_title.setText("Reportes")
        self._set_active(self.btn_reportes)
        if hasattr(self.controller, "_open_report_window"):
            try:
                self.controller._open_report_window()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir reportes:\n{e}")

    def _nav_settings(self):
        # For now, reuse Firebase dialog as "configuración"
        self._open_firebase_config_dialog()

    def _set_active(self, active_btn: QPushButton):
        for b in [self.btn_dashboard, self.btn_ingresos, self.btn_gastos, self.btn_tax, self.btn_itbis, self.btn_reportes, self.btn_settings]:
            b.setProperty("active", "true" if b is active_btn else "false")
            b.style().unpolish(b)
            b.style().polish(b)

    # ===== Actions =====
    def _new_invoice(self):
        # Preserve logic via controller
        if hasattr(self.controller, "open_add_invoice_window"):
            try:
                self.controller.open_add_invoice_window()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir 'Nueva Factura':\n{e}")
        else:
            QMessageBox.information(self, "No disponible", "La acción 'Nueva Factura' no está disponible.")

    def _on_company_changed(self, idx: int):
        # Inform controller of company change, then refresh
        if hasattr(self.controller, "set_active_company"):
            try:
                self.controller.set_active_company(self.company_combo.currentText())
            except Exception:
                pass
        self._safe_refresh_dashboard()
        self._safe_populate_transactions_table()

    def _on_filters_changed(self):
        self._safe_refresh_dashboard()
        self._safe_populate_transactions_table()

    def _apply_type_filter(self, tx_type: Optional[str]):
        # Hook into controller filtering logic if present, else client-side
        if hasattr(self.controller, "set_transaction_filter"):
            try:
                self.controller.set_transaction_filter(tx_type)
            except Exception:
                pass
        self._safe_populate_transactions_table()

    # ===== Legacy-preserving wrappers =====
    def _safe_refresh_dashboard(self):
        # Call legacy method if exists, then update cards
        totals = {"income": 0.0, "income_itbis": 0.0, "expense": 0.0, "expense_itbis": 0.0, "net_itbis": 0.0, "payable": 0.0}
        if hasattr(self.controller, "_refresh_dashboard"):
            try:
                data = self.controller._refresh_dashboard(
                    month=self.cmb_month.currentText(),
                    year=self.cmb_year.currentText()
                )
                if isinstance(data, dict):
                    totals.update(data)
            except Exception:
                pass
        # Update cards
        self._set_money(self.card_income, totals["income"], sub_hint="ITBIS: RD$ {:.2f}".format(totals["income_itbis"]))
        self._set_money(self.card_expense, totals["expense"], sub_hint="ITBIS: RD$ {:.2f}".format(totals["expense_itbis"]))
        self._set_money(self.card_net, totals["net_itbis"])
        self._set_money(self.card_payable, totals["payable"])

    def _safe_populate_transactions_table(self):
        # Let legacy method fill, or do a minimal fallback
        if hasattr(self.controller, "_populate_transactions_table"):
            try:
                rows = self.controller._populate_transactions_table(
                    month=self.cmb_month.currentText(),
                    year=self.cmb_year.currentText(),
                    tx_type=getattr(self.controller, "current_tx_filter", None)
                )
                # Expected rows format: list of dicts with keys: date, type, number, party, itbis, total
                if isinstance(rows, list):
                    self._fill_table(rows)
                    return
            except Exception:
                pass
        # Fallback empty
        self._fill_table([])

    def _fill_table(self, rows: list):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            def _txt(k, default=""):
                v = row.get(k, default)
                return "" if v is None else str(v)

            items = [
                QTableWidgetItem(_txt("date")),
                QTableWidgetItem(_txt("type")),
                QTableWidgetItem(_txt("number")),
                QTableWidgetItem(_txt("party")),
                QTableWidgetItem(_txt("itbis")),
                QTableWidgetItem(_txt("total")),
                QTableWidgetItem("⋯"),
            ]
            # Align numeric
            items[4].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items[5].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items[6].setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            for c, it in enumerate(items):
                self.table.setItem(r, c, it)

        # Optional context action for diagnose row
        if hasattr(self.controller, "diagnose_row"):
            self.table.cellDoubleClicked.connect(self._diagnose_selected_row)

    def _diagnose_selected_row(self, row: int, col: int):
        if hasattr(self.controller, "diagnose_row"):
            try:
                number_item = self.table.item(row, 2)
                number = number_item.text() if number_item else ""
                self.controller.diagnose_row(number=number)
            except Exception:
                pass

    @staticmethod
    def _set_money(card: QWidget, amount: float, sub_hint: Optional[str] = None):
        try:
            card.lbl_value.setText("RD$ {:,.2f}".format(amount))
            if sub_hint is not None and hasattr(card, "lbl_sub"):
                card.lbl_sub.setText(sub_hint)
        except Exception:
            pass


# Helper to run standalone for testing
def run_demo(controller=None):
    app = QApplication([])
    win = ModernMainWindow(controller=controller or object())
    win.show()
    return app.exec()


if __name__ == "__main__":
    run_demo()
