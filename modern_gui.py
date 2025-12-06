"""
modern_gui.py - Modern Dashboard UI for Facturas Pro
Clean Finance UI inspired design with dark sidebar and modern cards.
Preserves all existing business logic from app_gui_qt.py
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QFrame, QGridLayout,
    QMessageBox, QHeaderView, QApplication, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QAction
import sys

# Try to import qtawesome for icons, fallback gracefully
try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    QTAWESOME_AVAILABLE = False
    print("Warning: qtawesome not available. Icons will be text-only.")

# Modern stylesheet for Clean Finance UI
STYLESHEET = """
/* ============================================
   GLOBAL STYLES
   ============================================ */
QWidget {
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 10pt;
}

QMainWindow {
    background-color: #F8F9FA;
}

/* ============================================
   SIDEBAR STYLES
   ============================================ */
#sidebar {
    background-color: #1E293B;
    border-right: 1px solid #0F172A;
}

#sidebar_header {
    background-color: #1E293B;
    padding: 16px;
}

#logo_box {
    background-color: #3B82F6;
    border-radius: 8px;
    color: white;
    font-weight: bold;
    font-size: 18px;
}

#app_title {
    color: white;
    font-size: 18px;
    font-weight: 600;
}

#company_label {
    color: #94A3B8;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

#company_selector {
    background-color: #0F172A;
    color: white;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    font-weight: 500;
}

#company_selector:hover {
    background-color: #334155;
}

#company_selector::drop-down {
    border: none;
    width: 20px;
}

#company_selector QAbstractItemView {
    background-color: #0F172A;
    color: white;
    selection-background-color: #3B82F6;
    border: 1px solid #334155;
}

/* Navigation buttons */
#nav_button {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
}

#nav_button:hover {
    background-color: #0F172A;
    color: white;
}

#nav_button_active {
    background-color: #3B82F6;
    color: white;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
}

#config_button {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 10px 16px;
    border: none;
    font-size: 13px;
}

#config_button:hover {
    color: white;
}

/* ============================================
   CONTENT AREA STYLES
   ============================================ */
#content_area {
    background-color: #F8F9FA;
}

#header {
    background-color: white;
    border-bottom: 1px solid #E5E7EB;
    min-height: 64px;
    max-height: 64px;
}

#section_title {
    font-size: 20px;
    font-weight: bold;
    color: #1E293B;
}

#btn_new_invoice {
    background-color: #1E293B;
    color: white;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
}

#btn_new_invoice:hover {
    background-color: #0F172A;
}

/* Filter dropdowns */
#filter_combo {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

#filter_combo:hover {
    border-color: #CBD5E1;
}

#filter_combo::drop-down {
    border: none;
    width: 20px;
}

#filter_combo QAbstractItemView {
    background-color: white;
    selection-background-color: #3B82F6;
    selection-color: white;
    border: 1px solid #E5E7EB;
}

/* ============================================
   KPI CARD STYLES
   ============================================ */
.kpi_card {
    background-color: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
}

.kpi_label {
    color: #6B7280;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi_value {
    color: #1E293B;
    font-size: 24px;
    font-weight: bold;
}

.kpi_subtitle {
    color: #9CA3AF;
    font-size: 10px;
}

/* Income card */
#card_income {
    border-left: 4px solid #10B981;
}

/* Expense card */
#card_expense {
    border-left: 4px solid #EF4444;
}

/* Net ITBIS card */
#card_net {
    border-left: 4px solid #3B82F6;
}

/* Payable card */
#card_payable {
    border-left: 4px solid #F59E0B;
}

/* ============================================
   TABLE STYLES
   ============================================ */
#transactions_table {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    gridline-color: #F3F4F6;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
}

#transactions_table::item {
    padding: 12px;
    border: none;
}

#transactions_table::item:selected {
    background-color: #DBEAFE;
}

QHeaderView::section {
    background-color: #F9FAFB;
    color: #6B7280;
    padding: 12px;
    border: none;
    border-bottom: 1px solid #E5E7EB;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

/* Filter buttons above table */
#filter_btn {
    background-color: transparent;
    color: #6B7280;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

#filter_btn:hover {
    background-color: #F3F4F6;
}

#filter_btn_active {
    background-color: white;
    color: #3B82F6;
    border: 1px solid #BFDBFE;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* ============================================
   BADGE STYLES (for transaction type)
   ============================================ */
QLabel[class="badge_income"] {
    background-color: #D1FAE5;
    color: #065F46;
    border-radius: 12px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: bold;
}

QLabel[class="badge_expense"] {
    background-color: #FEE2E2;
    color: #991B1B;
    border-radius: 12px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: bold;
}

/* ============================================
   SCROLLBAR STYLES
   ============================================ */
QScrollBar:vertical {
    background: #F3F4F6;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar:horizontal {
    background: #F3F4F6;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}
"""


class ModernMainWindow(QMainWindow):
    """
    Modern Dashboard Main Window for Facturas Pro.
    Integrates with existing controller from app_gui_qt.py
    """
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Facturas Pro - Dashboard Moderno")
        self.resize(1400, 900)
        
        # Data attributes
        self.companies_list = []
        self.all_current_transactions = []
        self.current_tx_filter = "Todos"
        self.months_map = {
            'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
            'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
            'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
        }
        
        # Build UI
        self._create_menubar()
        self._create_main_ui()
        
        # Load initial data
        self._populate_company_selector()
        self._refresh_dashboard()
    
    def _create_menubar(self):
        """Create menu bar with Herramientas menu"""
        menubar = self.menuBar()
        
        # Herramientas menu
        tools_menu = menubar.addMenu("Herramientas")
        
        # Firebase configuration
        config_action = QAction("Configurar Firebase...", self)
        config_action.triggered.connect(self._open_firebase_config)
        tools_menu.addAction(config_action)
        
        # SQLite to Firebase migration
        migrate_action = QAction("Migrar SQLite → Firebase...", self)
        migrate_action.triggered.connect(self._open_migration_dialog)
        tools_menu.addAction(migrate_action)
        
        tools_menu.addSeparator()
        
        # Manual SQL backup
        backup_action = QAction("Crear backup SQL manual", self)
        backup_action.triggered.connect(self._create_manual_backup)
        tools_menu.addAction(backup_action)
        
        # Archivo menu
        file_menu = menubar.addMenu("Archivo")
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _create_main_ui(self):
        """Create the main UI layout"""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main horizontal layout: Sidebar | Content
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar and content area
        sidebar = self._create_sidebar()
        content = self._create_content_area()
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)  # Content takes remaining space
    
    def _create_sidebar(self):
        """Create the dark sidebar with navigation"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with logo
        header = QWidget()
        header.setObjectName("sidebar_header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        # Logo box
        logo = QLabel("F")
        logo.setObjectName("logo_box")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo)
        
        # App title
        title = QLabel("Facturas Pro")
        title.setObjectName("app_title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Company selector section
        company_widget = QWidget()
        company_layout = QVBoxLayout(company_widget)
        company_layout.setContentsMargins(16, 16, 16, 16)
        company_layout.setSpacing(8)
        
        company_label = QLabel("EMPRESA ACTIVA")
        company_label.setObjectName("company_label")
        company_layout.addWidget(company_label)
        
        self.company_selector = QComboBox()
        self.company_selector.setObjectName("company_selector")
        self.company_selector.currentIndexChanged.connect(self._on_company_changed)
        company_layout.addWidget(self.company_selector)
        
        layout.addWidget(company_widget)
        
        # Navigation menu
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 0, 12, 0)
        nav_layout.setSpacing(4)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "Dashboard", "fa5s.chart-pie", self._show_dashboard),
            ("income", "Ingresos", "fa5s.file-invoice-dollar", self._filter_income),
            ("expense", "Gastos", "fa5s.shopping-cart", self._filter_expense),
            ("tax", "Calc. Impuestos", "fa5s.calculator", self._open_tax_calculation_manager),
            ("reports", "Reportes", "fa5s.chart-line", self._open_report_window),
        ]
        
        for key, text, icon_name, callback in nav_items:
            btn = self._create_nav_button(text, icon_name, callback, active=(key == "dashboard"))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)
        
        layout.addWidget(nav_widget)
        layout.addStretch()
        
        # Config button at bottom
        config_widget = QWidget()
        config_widget.setStyleSheet("border-top: 1px solid #334155;")
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(12, 12, 12, 12)
        
        config_btn = self._create_nav_button("Configuración", "fa5s.cog", self._open_firebase_config, is_config=True)
        config_layout.addWidget(config_btn)
        
        layout.addWidget(config_widget)
        
        return sidebar
    
    def _create_nav_button(self, text, icon_name, callback, active=False, is_config=False):
        """Create a navigation button with optional icon"""
        btn = QPushButton()
        
        if is_config:
            btn.setObjectName("config_button")
        elif active:
            btn.setObjectName("nav_button_active")
        else:
            btn.setObjectName("nav_button")
        
        # Try to add icon
        if QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon(icon_name, color='white' if active else '#94A3B8')
                btn.setIcon(icon)
                btn.setText(f"  {text}")
            except Exception:
                btn.setText(f"  {text}")
        else:
            btn.setText(f"  {text}")
        
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        
        return btn
    
    def _create_content_area(self):
        """Create the main content area"""
        content = QWidget()
        content.setObjectName("content_area")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Scrollable content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(24, 24, 24, 24)
        scroll_layout.setSpacing(20)
        
        # Filters
        filters = self._create_filters()
        scroll_layout.addWidget(filters)
        
        # KPI Cards
        kpi_grid = self._create_kpi_cards()
        scroll_layout.addLayout(kpi_grid)
        
        # Transactions table
        table_widget = self._create_transactions_table()
        scroll_layout.addWidget(table_widget, 1)
        
        layout.addWidget(scroll_content, 1)
        
        return content
    
    def _create_header(self):
        """Create the header bar"""
        header = QWidget()
        header.setObjectName("header")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        # Section title
        self.section_title = QLabel("Resumen Financiero")
        self.section_title.setObjectName("section_title")
        header_layout.addWidget(self.section_title)
        
        header_layout.addStretch()
        
        # New invoice button
        btn_new = QPushButton("Nueva Factura")
        btn_new.setObjectName("btn_new_invoice")
        if QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon('fa5s.plus', color='white')
                btn_new.setIcon(icon)
                btn_new.setText("  Nueva Factura")
            except Exception:
                pass
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._open_add_invoice_window)
        header_layout.addWidget(btn_new)
        
        return header
    
    def _create_filters(self):
        """Create month/year filter dropdowns"""
        filters = QWidget()
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        
        # Month selector
        self.month_combo = QComboBox()
        self.month_combo.setObjectName("filter_combo")
        self.month_combo.addItems(list(self.months_map.keys()))
        # Set current month
        current_month = QDate.currentDate().month() - 1
        if 0 <= current_month < 12:
            self.month_combo.setCurrentIndex(current_month)
        self.month_combo.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.month_combo)
        
        # Year selector
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("filter_combo")
        current_year = QDate.currentDate().year()
        for year in range(current_year - 5, current_year + 2):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.year_combo)
        
        filters_layout.addStretch()
        
        return filters
    
    def _create_kpi_cards(self):
        """Create the KPI cards grid"""
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Create cards
        self.card_income = self._create_kpi_card("Total Ingresos", "RD$ 0.00", "ITBIS: RD$ 0.00", "card_income")
        self.card_expense = self._create_kpi_card("Total Gastos", "RD$ 0.00", "ITBIS: RD$ 0.00", "card_expense")
        self.card_net = self._create_kpi_card("ITBIS Neto", "RD$ 0.00", "Diferencia (Ingreso - Gasto)", "card_net")
        self.card_payable = self._create_kpi_card("A Pagar (Estimado)", "RD$ 0.00", "", "card_payable")
        
        # Add to grid
        grid.addWidget(self.card_income, 0, 0)
        grid.addWidget(self.card_expense, 0, 1)
        grid.addWidget(self.card_net, 0, 2)
        grid.addWidget(self.card_payable, 0, 3)
        
        return grid
    
    def _create_kpi_card(self, label_text, value_text, subtitle_text, card_id):
        """Create a single KPI card"""
        card = QFrame()
        card.setObjectName(card_id)
        card.setProperty("class", "kpi_card")
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Label
        label = QLabel(label_text)
        label.setProperty("class", "kpi_label")
        layout.addWidget(label)
        
        # Value
        value = QLabel(value_text)
        value.setProperty("class", "kpi_value")
        value.setObjectName(f"{card_id}_value")
        layout.addWidget(value)
        
        # Subtitle
        if subtitle_text:
            subtitle = QLabel(subtitle_text)
            subtitle.setProperty("class", "kpi_subtitle")
            subtitle.setObjectName(f"{card_id}_subtitle")
            layout.addWidget(subtitle)
        
        layout.addStretch()
        
        return card
    
    def _create_transactions_table(self):
        """Create the transactions table with filter buttons"""
        container = QFrame()
        container.setObjectName("transactions_table")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Table header with filter buttons
        table_header = QWidget()
        table_header.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        header_layout = QHBoxLayout(table_header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        header_title = QLabel("Transacciones Recientes")
        header_title.setStyleSheet("font-weight: 600; color: #374151; font-size: 14px;")
        header_layout.addWidget(header_title)
        
        header_layout.addStretch()
        
        # Filter buttons
        self.filter_buttons = {}
        for filter_name in ["Todos", "Ingresos", "Gastos"]:
            btn = QPushButton(filter_name)
            if filter_name == "Todos":
                btn.setObjectName("filter_btn_active")
            else:
                btn.setObjectName("filter_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, f=filter_name: self._set_transaction_filter(f))
            self.filter_buttons[filter_name] = btn
            header_layout.addWidget(btn)
        
        layout.addWidget(table_header)
        
        # Table
        self.table = QTableWidget()
        self.table.setObjectName("transactions_table")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "No. Factura", "Empresa / Tercero", "ITBIS", "Monto Total", "Acciones"
        ])
        
        # Table settings
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Tipo
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # No. Factura
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Tercero
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # ITBIS
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Total
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Acciones
        self.table.setColumnWidth(6, 80)
        
        # Double-click for diagnose
        self.table.doubleClicked.connect(self._on_table_double_click)
        
        layout.addWidget(self.table)
        
        return container
    
    # ============================================
    # DATA INTEGRATION METHODS
    # ============================================
    
    def _populate_company_selector(self):
        """Load companies into selector (from controller)"""
        try:
            if hasattr(self.controller, 'get_all_companies'):
                companies = self.controller.get_all_companies()
            elif hasattr(self.controller, 'get_companies'):
                companies = self.controller.get_companies()
            else:
                companies = []
            
            self.companies_list = companies
            self.company_selector.clear()
            
            for company in companies:
                self.company_selector.addItem(company.get('name', 'Unknown'))
        except Exception as e:
            print(f"Error loading companies: {e}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las empresas:\n{e}")
    
    def _get_current_company_id(self):
        """Get the currently selected company ID"""
        idx = self.company_selector.currentIndex()
        if idx < 0 or not self.companies_list:
            return None
        return self.companies_list[idx].get('id')
    
    def _refresh_dashboard(self, filter_month=None, filter_year=None):
        """Refresh dashboard data (KPIs and transactions)"""
        company_id = self._get_current_company_id()
        if not company_id:
            self._clear_dashboard()
            return
        
        try:
            # Use current filter values if not specified
            if filter_month is None:
                month_name = self.month_combo.currentText()
                filter_month = self.months_map.get(month_name, '01')
            
            if filter_year is None:
                filter_year = int(self.year_combo.currentText())
            
            # Call controller method
            if hasattr(self.controller, 'get_dashboard_data'):
                dashboard_data = self.controller.get_dashboard_data(
                    company_id,
                    filter_month=filter_month,
                    filter_year=filter_year
                )
            else:
                print("Warning: Controller doesn't have get_dashboard_data method")
                dashboard_data = None
            
            if dashboard_data and dashboard_data.get('summary'):
                summary = dashboard_data['summary']
                
                # Update KPI cards
                self._update_kpi_card('card_income', 
                                     summary.get('total_ingresos', 0.0),
                                     summary.get('itbis_ingresos', 0.0))
                
                self._update_kpi_card('card_expense',
                                     summary.get('total_gastos', 0.0),
                                     summary.get('itbis_gastos', 0.0))
                
                net_itbis = summary.get('itbis_neto', 0.0)
                self._update_kpi_simple('card_net', net_itbis)
                
                # A Pagar is same as net ITBIS for now
                self._update_kpi_simple('card_payable', net_itbis)
                
                # Store transactions and populate table
                self.all_current_transactions = dashboard_data.get('all_transactions', [])
                self._apply_transaction_filter()
            else:
                self._clear_dashboard()
                
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            QMessageBox.warning(self, "Error", f"Error al actualizar el dashboard:\n{e}")
            self._clear_dashboard()
    
    def _update_kpi_card(self, card_id, total_value, itbis_value):
        """Update a KPI card with total and ITBIS values"""
        # Find value label
        value_label = self.findChild(QLabel, f"{card_id}_value")
        subtitle_label = self.findChild(QLabel, f"{card_id}_subtitle")
        
        if value_label:
            value_label.setText(f"RD$ {total_value:,.2f}")
        
        if subtitle_label:
            subtitle_label.setText(f"ITBIS: RD$ {itbis_value:,.2f}")
    
    def _update_kpi_simple(self, card_id, value):
        """Update a simple KPI card with just a value"""
        value_label = self.findChild(QLabel, f"{card_id}_value")
        if value_label:
            value_label.setText(f"RD$ {value:,.2f}")
    
    def _clear_dashboard(self):
        """Clear all dashboard data"""
        self._update_kpi_card('card_income', 0.0, 0.0)
        self._update_kpi_card('card_expense', 0.0, 0.0)
        self._update_kpi_simple('card_net', 0.0)
        self._update_kpi_simple('card_payable', 0.0)
        self.all_current_transactions = []
        self.table.setRowCount(0)
    
    def _populate_transactions_table(self, transactions):
        """Populate the table with transaction data"""
        self.table.setRowCount(0)
        self.table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            try:
                # Date
                date_item = QTableWidgetItem(str(trans.get('invoice_date', '')))
                date_item.setForeground(QColor("#6B7280"))
                self.table.setItem(row, 0, date_item)
                
                # Type (with badge styling)
                invoice_type = trans.get('invoice_type', '')
                if invoice_type == 'emitida':
                    type_text = "INGRESO"
                    type_color = QColor("#065F46")
                    type_bg = QColor("#D1FAE5")
                elif invoice_type == 'gasto':
                    type_text = "GASTO"
                    type_color = QColor("#991B1B")
                    type_bg = QColor("#FEE2E2")
                else:
                    type_text = "N/A"
                    type_color = QColor("#6B7280")
                    type_bg = QColor("#F3F4F6")
                
                type_item = QTableWidgetItem(type_text)
                type_item.setForeground(type_color)
                type_item.setBackground(type_bg)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, type_item)
                
                # Invoice number
                number_item = QTableWidgetItem(str(trans.get('invoice_number', '')))
                number_item.setForeground(QColor("#1E293B"))
                number_item.setData(Qt.ItemDataRole.UserRole, trans.get('id'))  # Store ID for diagnose
                self.table.setItem(row, 2, number_item)
                
                # Third party
                party_item = QTableWidgetItem(str(trans.get('third_party_name', '')))
                party_item.setForeground(QColor("#6B7280"))
                self.table.setItem(row, 3, party_item)
                
                # ITBIS (converted to RD$)
                itbis = float(trans.get('itbis', 0.0))
                exchange_rate = float(trans.get('exchange_rate', 1.0))
                itbis_rd = itbis * exchange_rate
                itbis_item = QTableWidgetItem(f"RD$ {itbis_rd:,.2f}")
                itbis_item.setForeground(QColor("#6B7280"))
                itbis_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, itbis_item)
                
                # Total (in RD$)
                total_rd = float(trans.get('total_amount_rd', 0.0))
                if not total_rd:
                    total_amount = float(trans.get('total_amount', 0.0))
                    total_rd = total_amount * exchange_rate
                
                total_item = QTableWidgetItem(f"RD$ {total_rd:,.2f}")
                total_item.setForeground(QColor("#1E293B"))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                font = total_item.font()
                font.setBold(True)
                total_item.setFont(font)
                self.table.setItem(row, 5, total_item)
                
                # Actions (placeholder)
                actions_item = QTableWidgetItem("⋮")
                actions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                actions_item.setForeground(QColor("#D1D5DB"))
                self.table.setItem(row, 6, actions_item)
                
            except Exception as e:
                print(f"Error populating row {row}: {e}")
    
    def _apply_transaction_filter(self):
        """Apply the current transaction filter (Todos/Ingresos/Gastos)"""
        if self.current_tx_filter == "Ingresos":
            filtered = [t for t in self.all_current_transactions if t.get('invoice_type') == 'emitida']
        elif self.current_tx_filter == "Gastos":
            filtered = [t for t in self.all_current_transactions if t.get('invoice_type') == 'gasto']
        else:
            filtered = self.all_current_transactions
        
        self._populate_transactions_table(filtered)
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    def _on_company_changed(self, index):
        """Handle company selector change"""
        try:
            company_id = self._get_current_company_id()
            if company_id and hasattr(self.controller, 'set_active_company'):
                company_name = self.companies_list[index].get('name', '')
                self.controller.set_active_company(company_name)
        except Exception as e:
            print(f"Error changing company: {e}")
        
        self._refresh_dashboard()
    
    def _on_filter_changed(self, index):
        """Handle month/year filter change"""
        self._refresh_dashboard()
    
    def _set_transaction_filter(self, filter_name):
        """Set transaction type filter and update table"""
        self.current_tx_filter = filter_name
        
        # Update button styles
        for name, btn in self.filter_buttons.items():
            if name == filter_name:
                btn.setObjectName("filter_btn_active")
            else:
                btn.setObjectName("filter_btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Apply filter
        self._apply_transaction_filter()
    
    def _on_table_double_click(self, index):
        """Handle double-click on table row for diagnosis"""
        if not index.isValid():
            return
        
        row = index.row()
        number_item = self.table.item(row, 2)
        if number_item:
            invoice_number = number_item.text()
            try:
                if hasattr(self.controller, 'diagnose_row'):
                    self.controller.diagnose_row(number=invoice_number)
                else:
                    print(f"Diagnose row: {invoice_number}")
            except Exception as e:
                print(f"Error diagnosing row: {e}")
    
    # ============================================
    # NAVIGATION ACTIONS
    # ============================================
    
    def _show_dashboard(self):
        """Show dashboard view (default)"""
        self.section_title.setText("Resumen Financiero")
        self.current_tx_filter = "Todos"
        self._set_nav_active("dashboard")
        self._refresh_dashboard()
    
    def _filter_income(self):
        """Filter to show only income"""
        self.section_title.setText("Ingresos")
        self._set_nav_active("income")
        self._set_transaction_filter("Ingresos")
    
    def _filter_expense(self):
        """Filter to show only expenses"""
        self.section_title.setText("Gastos")
        self._set_nav_active("expense")
        self._set_transaction_filter("Gastos")
    
    def _set_nav_active(self, active_key):
        """Set the active navigation button"""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.setObjectName("nav_button_active")
            else:
                btn.setObjectName("nav_button")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _open_add_invoice_window(self):
        """Open add invoice window"""
        try:
            if hasattr(self.controller, 'open_add_invoice_window'):
                self.controller.open_add_invoice_window()
            else:
                # Try importing and opening directly
                from add_invoice_window_qt import AddInvoiceWindowQt
                
                def save_callback(parent, form_data, invoice_type, invoice_id=None):
                    # This would normally save via controller
                    print(f"Save invoice: {form_data}")
                    self._refresh_dashboard()
                
                dlg = AddInvoiceWindowQt(
                    parent=self,
                    controller=self.controller,
                    tipo_factura="emitida",
                    on_save=save_callback
                )
                dlg.exec()
                self._refresh_dashboard()
        except Exception as e:
            print(f"Error opening add invoice window: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo abrir la ventana de nueva factura:\n{e}")
    
    def _open_tax_calculation_manager(self):
        """Open tax calculation manager window"""
        try:
            if hasattr(self.controller, '_open_tax_calculation_manager'):
                self.controller._open_tax_calculation_manager()
            else:
                # Try importing directly
                from tax_calculation_management_window_qt import TaxCalculationManagementWindowQt
                dlg = TaxCalculationManagementWindowQt(self, self.controller)
                dlg.exec()
                self._refresh_dashboard()
        except Exception as e:
            print(f"Error opening tax calculation manager: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo abrir el gestor de cálculos:\n{e}")
    
    def _open_report_window(self):
        """Open monthly report window"""
        try:
            if hasattr(self.controller, '_open_report_window'):
                self.controller._open_report_window()
            else:
                # Try importing directly
                from report_window_qt import ReportWindowQt
                dlg = ReportWindowQt(self, self.controller)
                dlg.exec()
        except Exception as e:
            print(f"Error opening report window: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo abrir la ventana de reportes:\n{e}")
    
    # ============================================
    # HERRAMIENTAS MENU ACTIONS
    # ============================================
    
    def _open_firebase_config(self):
        """Open Firebase configuration dialog"""
        try:
            from firebase_config_dialog import show_firebase_config_dialog
            show_firebase_config_dialog(self)
        except Exception as e:
            print(f"Error opening Firebase config: {e}")
            QMessageBox.warning(
                self,
                "Firebase Config",
                f"No se pudo abrir la configuración de Firebase:\n{e}\n\n"
                "Asegúrate de que firebase_config_dialog.py existe."
            )
    
    def _open_migration_dialog(self):
        """Open SQLite to Firebase migration dialog"""
        try:
            from migration_dialog import show_migration_dialog
            
            # Get default DB path from controller
            default_path = ""
            if hasattr(self.controller, 'get_sqlite_db_path'):
                default_path = self.controller.get_sqlite_db_path() or ""
            elif hasattr(self.controller, 'db_path'):
                default_path = self.controller.db_path or ""
            
            show_migration_dialog(self, default_path)
        except Exception as e:
            print(f"Error opening migration dialog: {e}")
            QMessageBox.warning(
                self,
                "Migration Dialog",
                f"No se pudo abrir el diálogo de migración:\n{e}\n\n"
                "Asegúrate de que migration_dialog.py existe."
            )
    
    def _create_manual_backup(self):
        """Create manual SQL backup"""
        try:
            if hasattr(self.controller, 'create_sql_backup'):
                backup_path = self.controller.create_sql_backup(retention_days=30)
                QMessageBox.information(
                    self,
                    "Backup Creado",
                    f"Backup SQL creado exitosamente:\n\n{backup_path}\n\n"
                    "Este backup se eliminará automáticamente en 30 días."
                )
            else:
                QMessageBox.information(
                    self,
                    "Backup Manual",
                    "Función de backup manual aún no implementada en el controlador.\n\n"
                    "El controlador debe implementar el método:\n"
                    "create_sql_backup(retention_days=30) -> str"
                )
        except Exception as e:
            print(f"Error creating backup: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear el backup:\n{e}"
            )


def run_demo(controller=None):
    """
    Helper function to run the modern GUI for testing.
    
    Args:
        controller: Optional controller instance. If None, creates a mock controller.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Apply stylesheet
    app.setStyleSheet(STYLESHEET)
    
    # Create controller if not provided
    if controller is None:
        # Try to import and create real controller
        try:
            from logic_qt import LogicControllerQt
            import os
            
            # Look for database
            possible_paths = [
                'facturas_db.db',
                '/home/runner/work/FACTURAS-PyQT6-GIT/FACTURAS-PyQT6-GIT/facturas_db.db'
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if db_path:
                controller = LogicControllerQt(db_path)
            else:
                print("Warning: No database found, using mock controller")
                controller = None
        except Exception as e:
            print(f"Warning: Could not create controller: {e}")
            controller = None
    
    # Create and show window
    window = ModernMainWindow(controller)
    window.show()
    
    if app:
        sys.exit(app.exec())


if __name__ == "__main__":
    run_demo()
