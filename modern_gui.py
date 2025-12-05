"""
Modern Dashboard GUI for Facturas Pro
Clean, modern SaaS-style dashboard with sidebar navigation and KPI cards.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QFrame, QMessageBox,
    QHeaderView, QMenu
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QAction
import datetime

# Import existing windows
from add_invoice_window_qt import AddInvoiceWindowQt
from add_expense_window_qt import AddExpenseWindowQt
from settings_window_qt import SettingsWindowQt
from advanced_retention_window_qt import AdvancedRetentionWindowQt
from tax_calculation_management_window_qt import TaxCalculationManagementWindowQt
from report_window_qt import ReportWindowQt
from third_party_report_window_qt import ThirdPartyReportWindowQt
from company_management_window_qt import CompanyManagementWindow
from firebase_config_dialog import FirebaseConfigDialog
from migration_dialog import MigrationDialog
from backup_dialog import BackupDialog

# Try to import qtawesome for icons, fallback to text if not available
try:
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False


# Modern stylesheet
STYLESHEET = """
/* Global styles */
QMainWindow {
    background-color: #F8F9FA;
}

/* Sidebar styles */
#sidebar {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}

#sidebar QLabel {
    color: white;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    margin: 2px 8px;
}

#sidebar QPushButton:hover {
    background-color: #334155;
    color: white;
}

#sidebar QPushButton:checked, #sidebar QPushButton#active {
    background-color: #3B82F6;
    color: white;
    font-weight: 500;
}

#sidebar QComboBox {
    background-color: #334155;
    color: white;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

#sidebar QComboBox:hover {
    background-color: #475569;
}

#sidebar QComboBox::drop-down {
    border: none;
}

/* Header styles */
#header {
    background-color: white;
    border-bottom: 1px solid #E5E7EB;
    padding: 16px 32px;
}

#headerTitle {
    font-size: 20px;
    font-weight: bold;
    color: #1E293B;
}

/* KPI Card styles */
.kpi-card {
    background-color: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
}

.kpi-card QLabel#title {
    color: #64748B;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kpi-card QLabel#value {
    color: #1E293B;
    font-size: 24px;
    font-weight: bold;
    margin-top: 8px;
}

.kpi-card QLabel#subtitle {
    color: #94A3B8;
    font-size: 11px;
    margin-top: 4px;
}

/* Primary button */
QPushButton#primary {
    background-color: #1E293B;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#primary:hover {
    background-color: #334155;
}

/* Filter controls */
#filterContainer {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 8px 12px;
}

#filterContainer QLabel {
    color: #64748B;
    font-size: 13px;
    font-weight: 500;
}

/* Table styles */
QTableWidget {
    background-color: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    gridline-color: transparent;
}

QTableWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #1E293B;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Badge styles */
.badge-income {
    background-color: #DCFCE7;
    color: #166534;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
}

.badge-expense {
    background-color: #FEE2E2;
    color: #991B1B;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
}
"""


class ModernDashboard(QMainWindow):
    """Modern dashboard UI for Facturas Pro"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Facturas Pro - Dashboard Moderno")
        self.resize(1400, 900)
        
        # Set modern stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Data structures
        self.companies_list = []
        self.all_current_transactions = []
        self.current_itbis_neto = 0.0
        self.months_map = {
            'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
            'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
            'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
        }
        
        # Build UI
        self._create_ui()
        self._populate_company_selector()
        
        # Set current month/year
        now = datetime.datetime.now()
        month_name = list(self.months_map.keys())[now.month - 1]
        self.filter_month.setCurrentText(month_name)
        self.filter_year.setCurrentText(str(now.year))
    
    def _create_ui(self):
        """Create the modern dashboard UI"""
        # Main container
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Create content area
        content = self._create_content_area()
        main_layout.addWidget(content, 1)
    
    def _create_sidebar(self):
        """Create the sidebar with navigation"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Title
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        logo_label = QLabel("F")
        logo_label.setStyleSheet(
            "background-color: #3B82F6; color: white; font-weight: bold; "
            "font-size: 20px; border-radius: 8px; padding: 8px 12px;"
        )
        title_layout.addWidget(logo_label)
        
        app_name = QLabel("Facturas Pro")
        app_name.setStyleSheet("color: white; font-weight: 600; font-size: 18px;")
        title_layout.addWidget(app_name)
        title_layout.addStretch()
        
        layout.addWidget(title_container)
        
        # Company selector
        selector_container = QWidget()
        selector_layout = QVBoxLayout(selector_container)
        selector_layout.setContentsMargins(16, 0, 16, 20)
        
        selector_label = QLabel("EMPRESA ACTIVA")
        selector_label.setStyleSheet(
            "color: #64748B; font-size: 10px; font-weight: bold; "
            "letter-spacing: 1px;"
        )
        selector_layout.addWidget(selector_label)
        
        self.company_selector = QComboBox()
        self.company_selector.setObjectName("companySelector")
        self.company_selector.currentIndexChanged.connect(self._on_company_select)
        selector_layout.addWidget(self.company_selector)
        
        layout.addWidget(selector_container)
        
        # Navigation menu
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 0, 8, 0)
        nav_layout.setSpacing(4)
        
        # Dashboard button (active by default)
        self.btn_dashboard = self._create_nav_button("Dashboard", "fa5s.chart-pie")
        self.btn_dashboard.setObjectName("active")
        self.btn_dashboard.clicked.connect(lambda: self._filter_transactions("Todos"))
        nav_layout.addWidget(self.btn_dashboard)
        
        # Ingresos button
        self.btn_ingresos = self._create_nav_button("Ingresos", "fa5s.file-invoice-dollar")
        self.btn_ingresos.clicked.connect(lambda: self._filter_transactions("Ingresos"))
        nav_layout.addWidget(self.btn_ingresos)
        
        # Gastos button
        self.btn_gastos = self._create_nav_button("Gastos", "fa5s.shopping-cart")
        self.btn_gastos.clicked.connect(lambda: self._filter_transactions("Gastos"))
        nav_layout.addWidget(self.btn_gastos)
        
        # Calc. Impuestos button
        self.btn_calc_impuestos = self._create_nav_button("Calc. Impuestos", "fa5s.percent")
        self.btn_calc_impuestos.clicked.connect(self._open_tax_calculation_manager)
        nav_layout.addWidget(self.btn_calc_impuestos)
        
        # Reportes button
        self.btn_reportes = self._create_nav_button("Reportes", "fa5s.chart-line")
        self.btn_reportes.clicked.connect(self._open_report_window)
        nav_layout.addWidget(self.btn_reportes)
        
        nav_layout.addStretch()
        layout.addWidget(nav_container, 1)
        
        # Settings button at bottom
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(8, 0, 8, 16)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #334155;")
        settings_layout.addWidget(separator)
        
        settings_btn = self._create_nav_button("Configuración", "fa5s.cog")
        settings_btn.clicked.connect(self._open_settings_window)
        settings_layout.addWidget(settings_btn)
        
        layout.addWidget(settings_container)
        
        return sidebar
    
    def _create_nav_button(self, text, icon_name=None):
        """Create a navigation button with optional icon"""
        btn = QPushButton()
        
        if HAS_QTAWESOME and icon_name:
            try:
                icon = qta.icon(icon_name, color='#94A3B8')
                btn.setIcon(icon)
                btn.setText(f"  {text}")
            except:
                btn.setText(text)
        else:
            # Fallback to emoji/text icons
            icon_map = {
                "fa5s.chart-pie": "📊",
                "fa5s.file-invoice-dollar": "💰",
                "fa5s.shopping-cart": "🛒",
                "fa5s.percent": "💹",
                "fa5s.chart-line": "📈",
                "fa5s.cog": "⚙️"
            }
            emoji = icon_map.get(icon_name, "•")
            btn.setText(f"{emoji}  {text}")
        
        return btn
    
    def _create_content_area(self):
        """Create the main content area"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Scrollable content
        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.setContentsMargins(32, 24, 32, 24)
        scroll_layout.setSpacing(24)
        
        # Filters
        filters = self._create_filters()
        scroll_layout.addWidget(filters)
        
        # KPI Cards
        kpi_cards = self._create_kpi_cards()
        scroll_layout.addLayout(kpi_cards)
        
        # Transactions table
        table = self._create_transactions_table()
        scroll_layout.addWidget(table, 1)
        
        layout.addWidget(scroll_area, 1)
        
        # Create menubar
        self._create_menubar()
        
        return content
    
    def _create_header(self):
        """Create the header with title and action button"""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        
        title = QLabel("Resumen Financiero")
        title.setObjectName("headerTitle")
        layout.addWidget(title)
        
        layout.addStretch()
        
        new_invoice_btn = QPushButton("+ Nueva Factura")
        new_invoice_btn.setObjectName("primary")
        new_invoice_btn.clicked.connect(self._open_add_emitted_window)
        layout.addWidget(new_invoice_btn)
        
        return header
    
    def _create_filters(self):
        """Create filter controls"""
        container = QFrame()
        container.setObjectName("filterContainer")
        container.setMaximumHeight(60)
        
        layout = QHBoxLayout(container)
        
        # Month filter
        month_label = QLabel("Mes:")
        layout.addWidget(month_label)
        
        self.filter_month = QComboBox()
        self.filter_month.addItems(list(self.months_map.keys()))
        self.filter_month.setMinimumWidth(120)
        layout.addWidget(self.filter_month)
        
        # Year filter
        year_label = QLabel("Año:")
        layout.addWidget(year_label)
        
        self.filter_year = QComboBox()
        current_year = datetime.datetime.now().year
        for year in range(current_year - 5, current_year + 2):
            self.filter_year.addItem(str(year))
        self.filter_year.setCurrentText(str(current_year))
        self.filter_year.setMinimumWidth(100)
        layout.addWidget(self.filter_year)
        
        # Apply button
        apply_btn = QPushButton("Aplicar Filtro")
        apply_btn.clicked.connect(self._apply_month_year_filter)
        layout.addWidget(apply_btn)
        
        # Clear button
        clear_btn = QPushButton("Ver Todo")
        clear_btn.clicked.connect(self._clear_all_filters)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        return container
    
    def _create_kpi_cards(self):
        """Create KPI metric cards"""
        layout = QHBoxLayout()
        layout.setSpacing(16)
        
        # Total Ingresos card
        self.card_ingresos = self._create_kpi_card(
            "Total Ingresos",
            "RD$ 0.00",
            "ITBIS: RD$ 0.00",
            "#10B981"
        )
        layout.addWidget(self.card_ingresos)
        
        # Total Gastos card
        self.card_gastos = self._create_kpi_card(
            "Total Gastos",
            "RD$ 0.00",
            "ITBIS: RD$ 0.00",
            "#EF4444"
        )
        layout.addWidget(self.card_gastos)
        
        # ITBIS Neto card
        self.card_itbis_neto = self._create_kpi_card(
            "ITBIS Neto",
            "RD$ 0.00",
            "Diferencia (Ingreso - Gasto)",
            "#3B82F6"
        )
        layout.addWidget(self.card_itbis_neto)
        
        # A Pagar card (with input)
        self.card_a_pagar = self._create_kpi_card(
            "A Pagar (Estimado)",
            "RD$ 0.00",
            "Después de adelantos",
            "#F59E0B"
        )
        layout.addWidget(self.card_a_pagar)
        
        return layout
    
    def _create_kpi_card(self, title, value, subtitle, color="#3B82F6"):
        """Create a single KPI card"""
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setProperty("class", "kpi-card")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # Store labels for updating
        card.value_label = value_label
        card.subtitle_label = subtitle_label
        
        return card
    
    def _create_transactions_table(self):
        """Create the transactions table"""
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-bottom: none; padding: 12px 16px;")
        header_layout = QHBoxLayout(header_frame)
        
        table_title = QLabel("Transacciones Recientes")
        table_title.setStyleSheet("font-weight: 600; color: #475569; font-size: 14px;")
        header_layout.addWidget(table_title)
        
        header_layout.addStretch()
        
        # Transaction type filters
        filter_all = QPushButton("Todos")
        filter_all.setStyleSheet("padding: 6px 12px; font-size: 12px; font-weight: 600; color: #3B82F6; border: 1px solid #3B82F6; border-radius: 4px; background: white;")
        filter_all.clicked.connect(lambda: self._filter_transactions("Todos"))
        header_layout.addWidget(filter_all)
        
        filter_income = QPushButton("Ingresos")
        filter_income.setStyleSheet("padding: 6px 12px; font-size: 12px; color: #64748B; border: 1px solid transparent; border-radius: 4px;")
        filter_income.clicked.connect(lambda: self._filter_transactions("Ingresos"))
        header_layout.addWidget(filter_income)
        
        filter_expense = QPushButton("Gastos")
        filter_expense.setStyleSheet("padding: 6px 12px; font-size: 12px; color: #64748B; border: 1px solid transparent; border-radius: 4px;")
        filter_expense.clicked.connect(lambda: self._filter_transactions("Gastos"))
        header_layout.addWidget(filter_expense)
        
        container_layout.addWidget(header_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "No. Factura", "Empresa / Tercero", 
            "ITBIS", "Monto Total", "Acciones"
        ])
        
        # Configure table
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        container_layout.addWidget(self.table)
        
        return container
    
    def _create_menubar(self):
        """Create the application menubar"""
        menubar = self.menuBar()
        
        # Archivo menu
        file_menu = menubar.addMenu("Archivo")
        file_menu.addAction("Nueva Factura Emitida", self._open_add_emitted_window)
        file_menu.addAction("Nueva Factura de Gasto", self._open_add_expense_window)
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close)
        
        # Reportes menu
        report_menu = menubar.addMenu("Reportes")
        report_menu.addAction("Reporte Mensual...", self._open_report_window)
        report_menu.addAction("Reporte por Tercero...", self._open_third_party_report_window)
        
        # Herramientas menu
        tools_menu = menubar.addMenu("Herramientas")
        tools_menu.addAction("Migrador de Datos (SQLite → Firebase)", self._open_migration_dialog)
        tools_menu.addAction("Configuración Firebase", self._open_firebase_config)
        tools_menu.addSeparator()
        tools_menu.addAction("Gestionar Copias de Seguridad...", self._open_backup_manager)
        tools_menu.addSeparator()
        tools_menu.addAction("Gestionar Empresas...", self._open_company_management)
        
        # Opciones menu
        options_menu = menubar.addMenu("Opciones")
        options_menu.addAction("Configuración...", self._open_settings_window)
    
    # ========== Data Methods ==========
    
    def _populate_company_selector(self):
        """Populate the company selector"""
        self.company_selector.clear()
        self.companies_list = self.controller.get_all_companies()
        
        for company in self.companies_list:
            self.company_selector.addItem(company['name'], company['id'])
        
        if self.companies_list:
            self._refresh_dashboard()
    
    def _on_company_select(self, index):
        """Handle company selection change"""
        if index >= 0:
            self._refresh_dashboard()
    
    def _refresh_dashboard(self):
        """Refresh all dashboard data"""
        company_id = self._get_current_company_id()
        if not company_id:
            return
        
        # Get data with current filters
        filter_month = self.months_map.get(self.filter_month.currentText())
        filter_year = int(self.filter_year.currentText()) if self.filter_year.currentText() else None
        
        data = self.controller.get_dashboard_data(
            company_id,
            filter_month=filter_month,
            filter_year=filter_year
        )
        
        if not data:
            return
        
        # Update KPI cards
        summary = data['summary']
        
        self.card_ingresos.value_label.setText(f"RD$ {summary['total_ingresos']:,.2f}")
        self.card_ingresos.subtitle_label.setText(f"ITBIS: RD$ {summary['itbis_ingresos']:,.2f}")
        
        self.card_gastos.value_label.setText(f"RD$ {summary['total_gastos']:,.2f}")
        self.card_gastos.subtitle_label.setText(f"ITBIS: RD$ {summary['itbis_gastos']:,.2f}")
        
        self.card_itbis_neto.value_label.setText(f"RD$ {summary['itbis_neto']:,.2f}")
        
        self.card_a_pagar.value_label.setText(f"RD$ {summary['itbis_neto']:,.2f}")
        
        # Store and display transactions
        self.all_current_transactions = data['all_transactions']
        self._populate_transactions_table(self.all_current_transactions)
    
    def _populate_transactions_table(self, transactions):
        """Populate the transactions table"""
        self.table.setRowCount(0)
        
        for trans in transactions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Date
            self.table.setItem(row, 0, QTableWidgetItem(trans['invoice_date']))
            
            # Type (badge)
            type_widget = QLabel()
            if trans['invoice_type'] == 'emitida':
                type_widget.setText("INGRESO")
                type_widget.setProperty("class", "badge-income")
            else:
                type_widget.setText("GASTO")
                type_widget.setProperty("class", "badge-expense")
            type_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 1, type_widget)
            
            # Invoice number
            self.table.setItem(row, 2, QTableWidgetItem(trans['invoice_number']))
            
            # Third party
            self.table.setItem(row, 3, QTableWidgetItem(trans.get('third_party_name', '')))
            
            # ITBIS
            itbis_rd = trans['itbis'] * trans['exchange_rate']
            self.table.setItem(row, 4, QTableWidgetItem(f"RD$ {itbis_rd:,.2f}"))
            
            # Total
            self.table.setItem(row, 5, QTableWidgetItem(f"RD$ {trans['total_amount_rd']:,.2f}"))
            
            # Actions (placeholder)
            actions = QLabel("⋮")
            actions.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions.setStyleSheet("color: #94A3B8; font-size: 18px;")
            self.table.setCellWidget(row, 6, actions)
            
            # Store transaction ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, trans['id'])
    
    def _filter_transactions(self, filter_type):
        """Filter transactions by type"""
        if filter_type == "Todos":
            filtered = self.all_current_transactions
        elif filter_type == "Ingresos":
            filtered = [t for t in self.all_current_transactions if t['invoice_type'] == 'emitida']
        else:  # Gastos
            filtered = [t for t in self.all_current_transactions if t['invoice_type'] == 'gasto']
        
        self._populate_transactions_table(filtered)
    
    def _apply_month_year_filter(self):
        """Apply month/year filter"""
        self._refresh_dashboard()
    
    def _clear_all_filters(self):
        """Clear all filters and show all data"""
        company_id = self._get_current_company_id()
        if not company_id:
            return
        
        data = self.controller.get_dashboard_data(company_id)
        if data:
            self.all_current_transactions = data['all_transactions']
            self._populate_transactions_table(self.all_current_transactions)
    
    def _get_current_company_id(self):
        """Get the currently selected company ID"""
        if self.company_selector.currentIndex() >= 0:
            return self.company_selector.currentData()
        return None
    
    def _show_context_menu(self, position):
        """Show context menu for table row"""
        menu = QMenu(self)
        menu.addAction("Ver Detalles", self._view_transaction_details)
        menu.addAction("Editar", self._edit_transaction)
        menu.addSeparator()
        menu.addAction("Eliminar", self._delete_transaction)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    # ========== Window Methods ==========
    
    def _open_add_emitted_window(self):
        """Open add invoice window"""
        company_id = self._get_current_company_id()
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Seleccione una empresa primero.")
            return
        
        win = AddInvoiceWindowQt(self, self.controller, company_id)
        if win.exec():
            self._refresh_dashboard()
    
    def _open_add_expense_window(self):
        """Open add expense window"""
        company_id = self._get_current_company_id()
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Seleccione una empresa primero.")
            return
        
        win = AddExpenseWindowQt(self, self.controller, company_id)
        if win.exec():
            self._refresh_dashboard()
    
    def _open_report_window(self):
        """Open report window"""
        company_id = self._get_current_company_id()
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Seleccione una empresa primero.")
            return
        
        win = ReportWindowQt(self, self.controller, company_id)
        win.exec()
    
    def _open_third_party_report_window(self):
        """Open third party report window"""
        company_id = self._get_current_company_id()
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Seleccione una empresa primero.")
            return
        
        win = ThirdPartyReportWindowQt(self, self.controller)
        win.exec()
    
    def _open_tax_calculation_manager(self):
        """Open tax calculation manager"""
        company_id = self._get_current_company_id()
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Seleccione una empresa primero.")
            return
        
        win = TaxCalculationManagementWindowQt(self, self.controller, company_id)
        win.exec()
        self._refresh_dashboard()
    
    def _open_settings_window(self):
        """Open settings window"""
        win = SettingsWindowQt(self, self.controller)
        win.exec()
    
    def _open_firebase_config(self):
        """Open Firebase configuration dialog"""
        dialog = FirebaseConfigDialog(self)
        dialog.exec()
    
    def _open_migration_dialog(self):
        """Open migration dialog"""
        dialog = MigrationDialog(self, self.controller)
        dialog.exec()
    
    def _open_backup_manager(self):
        """Open backup manager"""
        dialog = BackupDialog(self, self.controller.db_path)
        dialog.exec()
    
    def _open_company_management(self):
        """Open company management"""
        win = CompanyManagementWindow(self, self.controller)
        win.exec()
        self._populate_company_selector()
    
    def _view_transaction_details(self):
        """View transaction details"""
        # Placeholder for future implementation
        QMessageBox.information(self, "Detalles", "Funcionalidad en desarrollo")
    
    def _edit_transaction(self):
        """Edit selected transaction"""
        # Placeholder for future implementation
        QMessageBox.information(self, "Editar", "Funcionalidad en desarrollo")
    
    def _delete_transaction(self):
        """Delete selected transaction"""
        # Placeholder for future implementation
        QMessageBox.information(self, "Eliminar", "Funcionalidad en desarrollo")
