# --- LIBRERÍAS DE PYQT6 ---
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QMenu,
    QSplitter, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QSizePolicy, QMessageBox, QFileDialog, QGroupBox, QLineEdit, QDateEdit,
    QApplication, QHeaderView, QDialog
)
# QAction se importa de QtGui, que es el lugar correcto.
from PyQt6.QtGui import QAction, QFont, QColor
from PyQt6.QtCore import Qt, QDate

# --- LIBRERÍAS ESTÁNDAR Y DE TERCEROS ---
import pandas as pd
import datetime
from pathlib import Path

# --- IMPORTS DE TUS PROPIOS MÓDULOS DE LA APLICACIÓN ---
from add_invoice_window_qt import AddInvoiceWindowQt
from add_expense_window_qt import AddExpenseWindowQt
from settings_window_qt import SettingsWindowQt
from advanced_retention_window_qt import AdvancedRetentionWindowQt
from tax_calculation_management_window_qt import TaxCalculationManagementWindowQt
from report_window_qt import ReportWindowQt
from third_party_report_window_qt import ThirdPartyReportWindowQt
from attachment_editor_window_qt import AttachmentEditorWindowQt
from company_management_window_qt import CompanyManagementWindow # Asegúrate que la clase se llame así en el archivo


class MainApplicationQt(QMainWindow):
    def __init__(self, controller, layout="default"):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Asistente de Gestión de Facturas (PyQt6)")
        self.resize(1400, 800)
        self.months_map = {
            'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
            'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
            'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
        }
        # Lista maestra que SIEMPRE contiene TODAS las transacciones del filtro actual
        self.all_current_transactions = []
        self.companies_list = []
        self.current_itbis_neto = 0.0

        # build UI (these methods must be implemented in your class)
        # they are preserved from your original codebase
        self._create_menubar()
        self._create_main_layout(layout)

        # populate selectors and table behavior
        self._populate_company_selector()

        # integrate company management action AFTER UI and controller exist
        try:
            self.integrate_company_management()
        except Exception:
            # Defensive: if integration fails, don't break the app
            pass

        # remaining UI wiring from your snippet
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Conexión del botón de cálculo
        self.btn_calcular.clicked.connect(self._recalculate_itbis_restante)

    # ------------------------
    # Company management integration
    # ------------------------
    def open_company_management(self):
        """
        Open the CompanyManagementWindow as a modal dialog.
        Uses self.controller and updates UI after dialog closes.
        """
        try:
            if not hasattr(self, "controller") or self.controller is None:
                QMessageBox.warning(self, "Controlador", "No hay controlador disponible para gestionar empresas.")
                return
            dlg = CompanyManagementWindow(self, controller=self.controller)
            # modal exec so the user finishes management before returning
            dlg.exec()
            # After closing, refresh company selector in case of changes
            try:
                if hasattr(self, "_populate_company_selector"):
                    self._populate_company_selector()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la gestión de empresas:\n{e}")

    def integrate_company_management(self):
        """
        Create the 'Gestionar Empresas' action and add it to the menu and toolbar (if present).
        Call this after the UI and self.controller are initialized.
        """
        try:
            # avoid adding twice
            if getattr(self, "company_mgmt_action", None):
                return

            action = QAction("Gestionar Empresas", self)
            action.setStatusTip("Abrir el módulo de gestión de empresas")
            action.triggered.connect(self.open_company_management)
            self.company_mgmt_action = action

            # Add to menubar: try to attach to an 'Empresas' menu, otherwise create
            try:
                menubar = self.menuBar() if hasattr(self, "menuBar") and callable(getattr(self, "menuBar")) else None
                if menubar:
                    # create or reuse a menu named 'Empresas'
                    # Note: QMenuBar.addMenu returns a QMenu, which we can add actions to
                    empresas_menu = None
                    # Try to find existing menu "Empresas"
                    for act in menubar.actions():
                        if act.text().lower() == "empresas":
                            empresas_menu = act.menu()
                            break
                    if not empresas_menu:
                        empresas_menu = menubar.addMenu("Empresas")
                    empresas_menu.addAction(action)
            except Exception:
                # not critical if menu integration fails
                pass

            # Add to toolbar if one exists (try common attribute names)
            try:
                toolbar = getattr(self, "toolBar", None) or getattr(self, "toolbar", None) or getattr(self, "main_toolbar", None)
                if toolbar and hasattr(toolbar, "addAction"):
                    toolbar.addAction(action)
                else:
                    # If this is a QMainWindow and addToolBar exists, add a small toolbar
                    if hasattr(self, "addToolBar") and callable(getattr(self, "addToolBar")):
                        tb = self.addToolBar("Empresas")
                        tb.addAction(action)
            except Exception:
                # not critical
                pass

        except Exception as e:
            QMessageBox.warning(self, "Integración", f"No se pudo integrar el menú de empresas: {e}")

    def _create_menubar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # --- Menú Archivo
        file_menu = menubar.addMenu("Archivo")
        file_menu.addAction("Cambiar Base de Datos...", self._change_database)
        file_menu.addAction("Crear Copia de Seguridad...", self._backup_database)
        file_menu.addAction("Restaurar Copia de Seguridad...", self._restore_database)
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close)

        # --- Menú Reportes
        report_menu = menubar.addMenu("Reportes")
        report_menu.addAction("Reporte Mensual...", self._open_report_window)
        report_menu.addAction("Reporte por Cliente/Proveedor...", self._open_third_party_report_window)

        # --- Menú Opciones
        options_menu = menubar.addMenu("Opciones")
        options_menu.addAction("Configuración...", self._open_settings_window)
        options_menu.addSeparator()
        theme_menu = options_menu.addMenu("Cambiar Tema")
        for theme in ["Fusion", "Windows", "WindowsVista"]:
            theme_menu.addAction(theme, lambda checked=False, t=theme: self._change_theme(t))

    def _create_main_layout(self, layout):
        if layout == "default":
            central = QWidget(self)
            self.setCentralWidget(central)
            main_layout = QHBoxLayout(central)
            splitter = QSplitter(Qt.Orientation.Horizontal)

            # -------- Panel Izquierdo (Opciones y Filtros)
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            empresa_layout = QHBoxLayout()
            label_empresa = QLabel("Empresa Activa:")
            label_empresa.setStyleSheet("font-weight: bold; font-size: 16px;")
            empresa_layout.addWidget(label_empresa)
            self.company_selector = QComboBox()
            self.company_selector.setMinimumWidth(350)
            self.company_selector.setStyleSheet("font-size: 15px;")
            self.company_selector.currentIndexChanged.connect(self._on_company_select)
            empresa_layout.addWidget(self.company_selector, 1)
            self.btn_migrar = QPushButton("Migrar Datos (JSON)")
            self.btn_migrar.clicked.connect(self._migrate_json)
            empresa_layout.addWidget(self.btn_migrar)
            left_layout.addLayout(empresa_layout)
            left_layout.addSpacing(10)

            fact_group = QGroupBox("Opciones de Facturación")
            fact_layout = QVBoxLayout()
            self.btn_add_emitida = QPushButton("Registrar Factura Emitida (Ingreso)")
            self.btn_add_emitida.clicked.connect(self._open_add_emitted_window)
            fact_layout.addWidget(self.btn_add_emitida)
            self.btn_add_gasto = QPushButton("Registrar Factura de Gasto")
            self.btn_add_gasto.clicked.connect(self._open_add_expense_window)
            fact_layout.addWidget(self.btn_add_gasto)
            self.btn_generar_reporte = QPushButton("Ver Reporte Mensual (Ventana)")
            self.btn_generar_reporte.clicked.connect(self._open_report_window)
            fact_layout.addWidget(self.btn_generar_reporte)
            self.btn_calculadora_retenciones = QPushButton("Cálculo Impuestos y Retenciones")
            # Abrimos primero el gestor de cálculos (lista); desde allí el usuario crea/edita y se abre AdvancedRetentionWindowQt
            self.btn_calculadora_retenciones.clicked.connect(self._open_tax_calculation_manager)
            fact_layout.addWidget(self.btn_calculadora_retenciones)
            self.btn_mini_calc = QPushButton("Mini Calculadora")
            self.btn_mini_calc.clicked.connect(self._open_mini_calculator)
            fact_layout.addWidget(self.btn_mini_calc)
            self.btn_salir = QPushButton("Salir")
            self.btn_salir.clicked.connect(self.close)
            fact_layout.addWidget(self.btn_salir)
            fact_group.setLayout(fact_layout)
            left_layout.addWidget(fact_group)

# In MainApplicationQt (_create_main_layout)

            # ... (after your existing buttons)

            # --- ADD THIS BLOCK ---
            diag_group = QGroupBox("Herramienta de Diagnóstico")
            diag_layout = QVBoxLayout(diag_group)
            
            self.btn_diagnosticar = QPushButton("Diagnosticar Fila Seleccionada (en Terminal)")
            self.btn_diagnosticar.setStyleSheet("background-color: #f39c12; color: white;") # Eye-catching style
            self.btn_diagnosticar.clicked.connect(self._diagnose_row_to_terminal)
            diag_layout.addWidget(self.btn_diagnosticar)
            
            fact_layout.addWidget(diag_group)
            # --- END OF BLOCK ---

            self.btn_salir = QPushButton("Salir")
            # ...
            # ...

            fact_group.setLayout(fact_layout)
            left_layout.addWidget(fact_group)

            # Bloque modificado: Filtros del Dashboard (reemplaza el bloque original en _create_main_layout)
            filtro_group = QGroupBox("Filtros del Dashboard")
            filtro_layout = QVBoxLayout()
            filtro_layout.addWidget(QLabel("<b>Por Mes y Año:</b>"))

            # --- Mes ---
            mes_layout = QHBoxLayout()
            mes_layout.addWidget(QLabel("Mes:"))
            self.dashboard_mes_cb = QComboBox()
            meses_lista = list(self.months_map.keys())
            self.dashboard_mes_cb.addItems(meses_lista)
            # Seleccionar el mes actual por defecto
            current_month_index = QDate.currentDate().month() - 1
            if 0 <= current_month_index < len(meses_lista):
                self.dashboard_mes_cb.setCurrentIndex(current_month_index)
            else:
                self.dashboard_mes_cb.setCurrentIndex(0)
            # No editable y conectar a handler por si se desea reaccionar al cambio
            self.dashboard_mes_cb.setEditable(False)
            self.dashboard_mes_cb.currentIndexChanged.connect(self._on_month_changed)
            mes_layout.addWidget(self.dashboard_mes_cb)
            filtro_layout.addLayout(mes_layout)

            # --- Año ---
            anio_layout = QHBoxLayout()
            anio_layout.addWidget(QLabel("Año:"))
            # Año NO editable; se llenará con los años disponibles para la empresa seleccionada
            self.dashboard_anio_entry = QComboBox()
            self.dashboard_anio_entry.setEditable(False)
            self.dashboard_anio_entry.setToolTip("Selecciona el año desde las transacciones disponibles")
            # Si no se han cargado años aún, mostrar el año actual como valor provisional
            self.dashboard_anio_entry.addItem(str(QDate.currentDate().year()))
            self.dashboard_anio_entry.setCurrentIndex(0)
            anio_layout.addWidget(self.dashboard_anio_entry)
            filtro_layout.addLayout(anio_layout)

            filtro_layout.addSpacing(8)
            filtro_layout.addWidget(QLabel("<b>Por Fecha Específica:</b>"))
            self.date_filter_entry = QDateEdit(calendarPopup=True)
            self.date_filter_entry.setDate(QDate.currentDate())
            self.date_filter_entry.setDisplayFormat("yyyy-MM-dd")
            filtro_layout.addWidget(self.date_filter_entry)

            self.btn_aplicar_filtro = QPushButton("Aplicar Filtro Mes/Año")
            self.btn_aplicar_filtro.clicked.connect(self._apply_month_year_filter)
            filtro_layout.addWidget(self.btn_aplicar_filtro)

            self.btn_limpiar_filtro = QPushButton("Ver Todo / Limpiar Filtros")
            self.btn_limpiar_filtro.clicked.connect(self._clear_all_filters)
            filtro_layout.addWidget(self.btn_limpiar_filtro)

            filtro_group.setLayout(filtro_layout)
            left_layout.addWidget(filtro_group)
            left_layout.addStretch()
            left_panel.setLayout(left_layout)
            splitter.addWidget(left_panel)
            # -------- Panel Derecho (Resumen y Tabla)
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            resumen_group = QGroupBox("Resumen Financiero Actual")
            resumen_layout = QVBoxLayout()
            tot_layout = QHBoxLayout()
            self.label_total_ingresos = QLabel("RD$ 0.00")
            self.label_total_ingresos.setStyleSheet("color: #006400; font-weight: bold; font-size: 16px;")
            tot_layout.addWidget(QLabel("Total Ingresos:"))
            tot_layout.addWidget(self.label_total_ingresos)
            self.label_total_gastos = QLabel("RD$ 0.00")
            self.label_total_gastos.setStyleSheet("color: #C70039; font-weight: bold; font-size: 16px;")
            tot_layout.addSpacing(20)
            tot_layout.addWidget(QLabel("Total Gastos:"))
            tot_layout.addWidget(self.label_total_gastos)
            resumen_layout.addLayout(tot_layout)
            itbis_layout = QHBoxLayout()
            self.label_itbis_ingresos = QLabel("RD$ 0.00")
            self.label_itbis_ingresos.setStyleSheet("color: #006400; font-weight: bold; font-size: 14px;")
            itbis_layout.addWidget(QLabel("ITBIS Ingresos:"))
            itbis_layout.addWidget(self.label_itbis_ingresos)
            self.label_itbis_gastos = QLabel("RD$ 0.00")
            self.label_itbis_gastos.setStyleSheet("color: #C70039; font-weight: bold; font-size: 14px;")
            itbis_layout.addSpacing(20)
            itbis_layout.addWidget(QLabel("ITBIS Gastos:"))
            itbis_layout.addWidget(self.label_itbis_gastos)
            resumen_layout.addLayout(itbis_layout)
            adel_layout = QHBoxLayout()
            adel_layout.addWidget(QLabel("ITBIS Adelantado (Mes Ant.):"))
            self.edit_itbis_adelantado = QLineEdit("0.00")
            self.edit_itbis_adelantado.setMaximumWidth(100)
            adel_layout.addWidget(self.edit_itbis_adelantado)
            adel_layout.addSpacing(30)
            self.btn_calcular = QPushButton("Calcular")
            adel_layout.addWidget(self.btn_calcular)
            resumen_layout.addLayout(adel_layout)
            pagar_layout = QHBoxLayout()
            self.label_itbis_a_pagar = QLabel("RD$ 0.00")
            self.label_itbis_a_pagar.setStyleSheet("color: #C70039; font-weight: bold; font-size: 16px;")
            pagar_layout.addWidget(QLabel("ITBIS a Pagar (Restante):"))
            pagar_layout.addWidget(self.label_itbis_a_pagar)
            resumen_layout.addLayout(pagar_layout)
            neto_layout = QHBoxLayout()
            self.label_itbis_neto = QLabel("RD$ 0.00")
            self.label_itbis_neto.setStyleSheet("color: blue; font-size: 16px; font-weight: bold; text-decoration: underline;")
            neto_layout.addWidget(QLabel("ITBIS Neto:"))
            neto_layout.addWidget(self.label_itbis_neto)
            self.label_total_neto = QLabel("RD$ 0.00")
            self.label_total_neto.setStyleSheet("color: blue; font-size: 16px; font-weight: bold; text-decoration: underline;")
            neto_layout.addSpacing(20)
            neto_layout.addWidget(QLabel("Total Neto:"))
            neto_layout.addWidget(self.label_total_neto)
            resumen_layout.addLayout(neto_layout)
            resumen_group.setLayout(resumen_layout)
            right_layout.addWidget(resumen_group)

            tabla_filtro_layout = QHBoxLayout()
            tabla_filtro_layout.addWidget(QLabel("Mostrar:"))
            self.transaction_filter = QComboBox()
            self.transaction_filter.addItems(["Todos", "Ingresos", "Gastos"])
            self.transaction_filter.currentIndexChanged.connect(self._apply_transaction_filter)
            tabla_filtro_layout.addWidget(self.transaction_filter)
            tabla_filtro_layout.addStretch()
            right_layout.addLayout(tabla_filtro_layout)

            self.table = QTableWidget(0, 7)
            self.table.setHorizontalHeaderLabels([
                "Fecha", "Tipo", "No. Fact.", "Empresa", "ITBIS (RD$)", "Monto Original", "Total (RD$)"
            ])
            self.table.setAlternatingRowColors(True)
            self.table.setSortingEnabled(True)
            self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
            # --------- Cambios para columnas expansibles ---------
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionsMovable(True)
            self.table.horizontalHeader().setStretchLastSection(True)
            # -----------------------------------------------------
            right_layout.addWidget(self.table)
            right_panel.setLayout(right_layout)
            splitter.addWidget(right_panel)
            splitter.setStretchFactor(1, 3)
            splitter.setSizes([200, 1200])  # Panel izquierdo inicia con 260px, derecho el resto
            main_layout.addWidget(splitter)

    # ---------------------------------------------------
    # Métodos de integración lógica y UI
    # ---------------------------------------------------
    def _populate_company_selector(self):
        companies = self.controller.get_all_companies()
        self.companies_list = companies
        self.company_selector.clear()
        for company in companies:
            self.company_selector.addItem(company['name'])

    def _on_company_select(self, index):
        """
        Cuando cambie la empresa activa:
        - actualiza el dashboard
        - actualiza el combo de años con los años disponibles para la empresa
        """
        # refrescar datos del dashboard (usa los filtros ya seleccionados o por defecto)
        self._refresh_dashboard()
        # actualizar lista de años disponibles para la empresa seleccionada
        company_id = self.get_current_company_id()
        if company_id:
            self._update_year_selector(company_id)


    def _update_year_selector(self, company_id):
        """
        Pide a controller.get_unique_invoice_years(company_id) la lista de años disponibles
        y la carga en self.dashboard_anio_entry (QComboBox no editable).
        Selecciona por defecto el año más reciente si existe.
        """
        try:
            years = []
            if hasattr(self.controller, "get_unique_invoice_years"):
                years = self.controller.get_unique_invoice_years(company_id) or []
            # asegurar strings y orden descendente (más reciente primero)
            years = sorted({int(y) for y in years if y not in (None, '')}, reverse=True) if years else []
            years_str = [str(y) for y in years]

            self.dashboard_anio_entry.clear()
            if years_str:
                self.dashboard_anio_entry.addItems(years_str)
                # seleccionar el año más reciente por defecto (primer elemento)
                self.dashboard_anio_entry.setCurrentIndex(0)
            else:
                # si no hay años disponibles, poner el año actual como única opción
                current_year = QDate.currentDate().year()
                self.dashboard_anio_entry.addItem(str(current_year))
                self.dashboard_anio_entry.setCurrentIndex(0)
        except Exception as e:
            # No queremos romper la UI por un fallo en controlador; logueamos y ponemos año actual
            print(f"[WARN] _update_year_selector: {e}")
            current_year = QDate.currentDate().year()
            self.dashboard_anio_entry.clear()
            self.dashboard_anio_entry.addItem(str(current_year))
            self.dashboard_anio_entry.setCurrentIndex(0)


    def _refresh_dashboard(self, filter_month=None, filter_year=None, specific_date=None):
        """
        Función ÚNICA y CENTRALIZADA para obtener datos y refrescar TODA la UI.
        """
        company_id = self.get_current_company_id()
        if not company_id:
            self._clear_ui()
            return

        # 1. Obtener los datos del controlador
        dashboard_data = self.controller.get_dashboard_data(
            company_id, filter_month=filter_month, filter_year=filter_year, specific_date=specific_date
        )

        if dashboard_data and dashboard_data['summary']:
            summary = dashboard_data['summary']
            
            # 2. Actualizar el panel de resumen (CORREGIDO)
            self.label_total_ingresos.setText(f"RD$ {summary.get('total_ingresos', 0.0):,.2f}")
            self.label_total_gastos.setText(f"RD$ {summary.get('total_gastos', 0.0):,.2f}")
            self.label_itbis_ingresos.setText(f"RD$ {summary.get('itbis_ingresos', 0.0):,.2f}")
            self.label_itbis_gastos.setText(f"RD$ {summary.get('itbis_gastos', 0.0):,.2f}")
            self.label_total_neto.setText(f"RD$ {summary.get('total_neto', 0.0):,.2f}")
            self.label_itbis_neto.setText(f"RD$ {summary.get('itbis_neto', 0.0):,.2f}")
            
            # Guardamos el ITBIS neto y recalculamos
            self.current_itbis_neto = summary.get('itbis_neto', 0.0)
            self._recalculate_itbis_restante()
            
            # 3. Guardar la lista COMPLETA de transacciones
            self.all_current_transactions = dashboard_data['all_transactions']
            
            # 4. Poblar la tabla usando el filtro de tipo (Ingreso/Gasto/Todos)
            self._apply_transaction_filter()

        else:
            self._clear_ui()

# -------------------------------------------------------------------
# Método modificado/robusto: poblar la tabla de transacciones
# (Reemplaza la versión existente por esta)
# -------------------------------------------------------------------
    def _populate_transactions_table(self, transactions):
        """
        Pobla la QTableWidget con la lista de transacciones.
        - Monto Original: muestra el valor en la moneda original (ej. "118.00 USD" o "RD$ 1,234.56")
        - ITBIS (RD$): itbis * exchange_rate
        - Total (RD$): usa total_amount_rd si existe y >0, si no total_amount * exchange_rate
        - Guarda el ID de la factura en la columna "No. Fact." usando ItemDataRole.UserRole
        - Debug prints controlables por self.debug_transactions (False por defecto)
        """
        from PyQt6.QtWidgets import QTableWidgetItem
        from PyQt6.QtGui import QColor

        debug = getattr(self, "debug_transactions", False)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.current_transactions = transactions or []
        self.table.setRowCount(len(self.current_transactions))

        for row_index, trans in enumerate(self.current_transactions):
            try:
                if debug:
                    print(f"[DBG] row {row_index} id={trans.get('id')} currency={trans.get('currency')} exchange_rate={trans.get('exchange_rate')} total_amount_rd={trans.get('total_amount_rd')}")

                invoice_date = str(trans.get('invoice_date') or '')
                invoice_type = str(trans.get('invoice_type') or '')
                invoice_number = str(trans.get('invoice_number') or '')
                third_party_name = str(trans.get('third_party_name') or '')

                # Normalizar moneda
                currency = trans.get('currency') or trans.get('moneda') or 'RD$'
                if isinstance(currency, str):
                    currency = currency.strip()
                if currency.upper() in ("RDS", "RDS$", "RD", "DOP"):
                    currency = "RD$"

                # Lectura segura numérica con fallbacks
                def _safe_float(keys, default=0.0):
                    for k in keys:
                        v = trans.get(k)
                        if v in (None, ''):
                            continue
                        try:
                            return float(v)
                        except Exception:
                            continue
                    return float(default)

                itbis = _safe_float(['itbis', 'itb', 'tax'], 0.0)
                exchange_rate = _safe_float(['exchange_rate', 'tasa_cambio', 'rate'], 1.0)
                total_amount = _safe_float(['total_amount', 'amount', 'monto'], 0.0)

                # total_amount_rd preferido si está y > 0, si no calcularlo
                total_amount_rd_val = trans.get('total_amount_rd')
                total_amount_rd = None
                try:
                    if total_amount_rd_val not in (None, '', 0):
                        total_amount_rd = float(total_amount_rd_val)
                except Exception:
                    total_amount_rd = None
                if not total_amount_rd:
                    total_amount_rd = total_amount * exchange_rate

                # Tipo y color
                if invoice_type == 'emitida':
                    tipo_texto = "↑ INGRESO"
                    color = QColor("#35ff95")
                elif invoice_type == 'gasto':
                    tipo_texto = "↓ GASTO"
                    color = QColor("#ff5370")
                else:
                    tipo_texto = "N/A"
                    color = QColor("gray")

                # Construir items no-editables (solo seleccionables)
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

                # Fecha
                date_item = QTableWidgetItem(invoice_date)
                date_item.setFlags(flags)
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, 0, date_item)

                # Tipo
                tipo_item = QTableWidgetItem(tipo_texto)
                tipo_item.setFlags(flags)
                tipo_item.setForeground(color)
                tipo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, 1, tipo_item)

                # No. Fact. (guardar ID en UserRole)
                invoice_number_item = QTableWidgetItem(invoice_number)
                invoice_number_item.setFlags(flags)
                fact_id = trans.get('id') or ''
                invoice_number_item.setData(Qt.ItemDataRole.UserRole, fact_id)
                invoice_number_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, 2, invoice_number_item)

                # Empresa / tercero
                third_item = QTableWidgetItem(third_party_name)
                third_item.setFlags(flags)
                third_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, 3, third_item)

                # ITBIS en RD$ (numérico, alineado a la derecha)
                itbis_rd = itbis * exchange_rate
                itbis_item = QTableWidgetItem(f"{itbis_rd:,.2f}")
                itbis_item.setFlags(flags)
                itbis_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, 4, itbis_item)

                # Monto Original: mostrar con prefijo "RD$ " si es RD$, o sufijo con la abreviatura si no
                if currency == "RD$":
                    monto_original_str = f"RD$ {total_amount:,.2f}"
                else:
                    monto_original_str = f"{total_amount:,.2f} {currency}"
                monto_item = QTableWidgetItem(monto_original_str)
                monto_item.setFlags(flags)
                monto_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                monto_item.setToolTip(f"Tasa: {exchange_rate} → Total RD$: {total_amount_rd:,.2f}")
                self.table.setItem(row_index, 5, monto_item)

                # Total en RD$ (numérico)
                total_rd_item = QTableWidgetItem(f"{total_amount_rd:,.2f}")
                total_rd_item.setFlags(flags)
                total_rd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, 6, total_rd_item)

            except Exception as e:
                # No detener el poblado; log para depuración
                print(f"[ERROR] Al poblar la fila {row_index}: {e}")
                print(f"[ERROR] Datos de la transacción: {trans}")

        self.table.setSortingEnabled(True)
        # (Opcional) Si agregaste la columna de ID, puedes ocultarla así:
        # self.table.setColumnHidden(7, True)
    def get_current_company_id(self):
        idx = self.company_selector.currentIndex()
        if idx < 0 or not hasattr(self, "companies_list"):
            return None
        return self.companies_list[idx]['id']

    def _apply_transaction_filter(self):
        """
        Filtra la lista maestra de transacciones (sin volver a la DB)
        y llama a la función que puebla la tabla.
        """
        filter_value = self.transaction_filter.currentText()
        
        if filter_value == "Ingresos":
            filtered = [t for t in self.all_current_transactions if t['invoice_type'] == 'emitida']
        elif filter_value == "Gastos":
            filtered = [t for t in self.all_current_transactions if t['invoice_type'] == 'gasto']
        else: # "Todos"
            filtered = self.all_current_transactions
            
        self._populate_transactions_table(filtered)

    def _apply_month_year_filter(self):
        """Aplica el filtro por mes y año llamando a la función central."""
        mes_nombre = self.dashboard_mes_cb.currentText()
        anio_str = self.dashboard_anio_entry.currentText()
        try:
            if not mes_nombre or not anio_str:
                raise ValueError("El mes y el año son requeridos.")
            mes_numero = self.months_map[mes_nombre]
            anio = int(anio_str)
            self._refresh_dashboard(filter_month=mes_numero, filter_year=anio)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entrada", str(e))


    def _on_month_changed(self, index):
        """
        Handler por si quieres reaccionar inmediatamente al cambio de mes.
        Actualmente no aplica el filtro automáticamente para evitar cambios indeseados,
        pero puedes descomentar la llamada a _apply_month_year_filter si deseas aplicar
        en cuanto el usuario cambie mes/año.
        """
        # Por ahora no aplicamos automáticamente; el usuario debe presionar "Aplicar Filtro Mes/Año"
        # Si quieres aplicar automáticamente, descomenta la línea siguiente:
        # self._apply_month_year_filter()
        pass


    def _refresh_dashboard_filtered(self, filter_month, filter_year):
        company_id = self.get_current_company_id()
        if not company_id:
            return
        dashboard_data = self.controller.get_dashboard_data(
            company_id, filter_month=filter_month, filter_year=filter_year
        )
        if dashboard_data:
            summary = dashboard_data['summary']
            self.label_total_ingresos.setText(f"RD$ {summary.get('total_ingresos', 0.0):,.2f}")
            self.label_total_gastos.setText(f"RD$ {summary.get('total_gastos', 0.0):,.2f}")
            self.label_itbis_ingresos.setText(f"RD$ {summary.get('itbis_ingresos', 0.0):,.2f}")
            self.label_itbis_gastos.setText(f"RD$ {summary.get('itbis_gastos', 0.0):,.2f}")
            self.label_total_neto.setText(f"RD$ {summary.get('total_neto', 0.0):,.2f}")
            self.label_itbis_neto.setText(f"RD$ {summary.get('itbis_neto', 0.0):,.2f}")
            self._populate_transactions_table(dashboard_data['all_transactions'])


    def _clear_ui(self):
        """Limpia todos los paneles de datos."""
        self.label_total_ingresos.setText("RD$ 0.00")
        self.label_total_gastos.setText("RD$ 0.00")
        self.label_itbis_ingresos.setText("RD$ 0.00")
        self.label_itbis_gastos.setText("RD$ 0.00")
        self.label_total_neto.setText("RD$ 0.00")
        self.label_itbis_neto.setText("RD$ 0.00")
        self.label_itbis_a_pagar.setText("RD$ 0.00")
        self.table.setRowCount(0)
        self.all_current_transactions = []
        
    def _recalculate_itbis_restante(self):
        """Calcula y muestra el ITBIS a pagar."""
        try:
            adelantado_str = self.edit_itbis_adelantado.text().replace(",", "")
            itbis_adelantado = float(adelantado_str or 0.0)
            
            itbis_neto = getattr(self, 'current_itbis_neto', 0.0)
            itbis_a_pagar = itbis_neto - itbis_adelantado
            
            color = "#C70039" if itbis_a_pagar >= 0 else "#006400"
            self.label_itbis_a_pagar.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")
            self.label_itbis_a_pagar.setText(f"RD$ {itbis_a_pagar:,.2f}")
            
        except (ValueError, TypeError):
            self.label_itbis_a_pagar.setStyleSheet("color: red;")
            self.label_itbis_a_pagar.setText("Error de formato")

    def _clear_all_filters(self):
        """Limpia los filtros y refresca el dashboard para mostrar todos los datos."""
        # Mes al mes actual
        meses_lista = list(self.months_map.keys())
        current_month_index = QDate.currentDate().month() - 1
        if 0 <= current_month_index < len(meses_lista):
            self.dashboard_mes_cb.setCurrentIndex(current_month_index)
        else:
            self.dashboard_mes_cb.setCurrentIndex(0)

        # Año: seleccionar el primer (más reciente) si hay elementos, si no añadir año actual
        if self.dashboard_anio_entry.count() > 0:
            self.dashboard_anio_entry.setCurrentIndex(0)
        else:
            self.dashboard_anio_entry.addItem(str(QDate.currentDate().year()))
            self.dashboard_anio_entry.setCurrentIndex(0)

        # Fecha específica -> dejar en hoy
        self.date_filter_entry.setDate(QDate.currentDate())

        # Refrescar sin filtros (muestra todo)
        self._refresh_dashboard()



    def _open_add_emitted_window(self):
        win = AddInvoiceWindowQt(self, self.controller, tipo_factura="emitida", on_save=self._save_invoice_callback)
        win.exec()

    def _open_report_window(self):
        """Abre el reporte mensual (modal)."""
        try:
            dlg = ReportWindowQt(self, self.controller)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de Reportes:\n{e}")

    def _open_third_party_report_window(self):
        """Abre el reporte por tercero (modal)."""
        try:
            dlg = ThirdPartyReportWindowQt(self, self.controller)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el reporte por tercero:\n{e}")

    def _open_company_management_window(self):
        QMessageBox.information(self, "Info", "Función aún no implementada (Gestión de Empresas)")

    def _open_settings_window(self):
        win = SettingsWindowQt(self, self.controller)
        if win.exec() == QDialog.DialogCode.Accepted:
            # Opcional: recargar la base de datos/configuración aquí si lo deseas
            db_path = self.controller.get_setting("facturas_config", "")
            if db_path and db_path != self.controller.db_path:
                self.controller.db_path = db_path
                self.controller.reconnect()
                self._populate_company_selector()
                self._refresh_dashboard()

    def _open_retention_calculator(self):
        """
        Abre la ventana de Cálculo de Impuestos y Retenciones (AdvancedRetentionWindowQt)
        como diálogo modal. Si el diálogo guardó cambios, se refresca el dashboard.
        """
        try:
            win = AdvancedRetentionWindowQt(self, self.controller, calculation_id=None)
            # Ejecutar modalmente. Si devuelve Accepted (se guardó), refrescar.
            res = win.exec()
            from PyQt6.QtWidgets import QDialog
            if res == QDialog.DialogCode.Accepted:
                # Refrescar los datos para recoger posibles cambios
                self._refresh_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de Retenciones:\n{e}")

    def _open_mini_calculator(self):
        QMessageBox.information(self, "Info", "Función aún no implementada (Mini Calculadora)")

    def _change_database(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Abrir Base de Datos", "", "Base de Datos SQLite (*.db);;Todos los archivos (*)")
        if fname:
            self.controller.db_path = fname
            self.controller.reconnect()
            self._populate_company_selector()
            self._refresh_dashboard()
            QMessageBox.information(self, "Base de Datos", "Base de datos cambiada correctamente.")

    def _migrate_json(self):
        QMessageBox.information(self, "Info", "Función aún no implementada (Migrar JSON)")

    def _backup_database(self):
        QMessageBox.information(self, "Info", "Función aún no implementada (Backup BD)")

    def _restore_database(self):
        QMessageBox.information(self, "Info", "Función aún no implementada (Restaurar BD)")

    def _change_theme(self, theme_name):
        QApplication.instance().setStyle(theme_name)

    def _save_invoice_callback(self, parent_window, form_data, invoice_type, invoice_id=None):
        """
        Callback para guardar/actualizar facturas (PyQt6).
        Asegura que si la moneda != 'RD$' haya una exchange_rate y que se calcule total_amount_rd.
        """
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        import traceback

        try:
            # Validaciones mínimas (ITBIS NO es obligatorio, puede ser 0)
            required_fields = {
                "número_de_factura": "Número de Factura",
                "rnc_cédula": "RNC/Cédula",
                # "itbis": "ITBIS",  # <-- REMOVIDO: ITBIS puede ser 0
                "factura_total": "Factura Total"
            }
            third_party_key = 'lugar_de_compra_empresa' if invoice_type == 'gasto' else 'empresa_a_la_que_se_emitió'
            required_fields[third_party_key] = "Empresa/Lugar"

            for key, name in required_fields.items():
                v = form_data.get(key) or ""
                if not str(v).strip():
                    QMessageBox.critical(parent_window, "Campo Vacío", f"El campo '{name}' no puede estar vacío.")
                    return

            num_factura = str(form_data['número_de_factura']).strip()
            if not num_factura:
                QMessageBox.critical(parent_window, "Campo Inválido", "Número de factura vacío.")
                return
            # ejemplo de validación de formato (opcional)
            if not num_factura[0].isalpha():
                QMessageBox.critical(parent_window, "Formato Inválido", "El 'Número de Factura' debe comenzar con una letra.")
                return

            # Construir invoice_data con claves en inglés (controller)
            invoice_data = {
                'invoice_type': invoice_type,
                'invoice_date': form_data['fecha'].strftime('%Y-%m-%d') if hasattr(form_data['fecha'], 'strftime') else form_data.get('fecha'),
                'invoice_number': num_factura,
                'currency': form_data.get('moneda') or form_data.get('currency') or "RD$",
                'rnc': form_data.get('rnc_cédula') or form_data.get('rnc'),
                'third_party_name': form_data.get(third_party_key),
                'itbis': float(form_data.get('itbis') or 0.0),  # Puede ser 0
                'total_amount': float(form_data.get('factura_total') or 0.0),
                'attachment_path': form_data.get('attachment_path')
            }
            if invoice_type == 'emitida':
                invoice_data['invoice_category'] = form_data.get('tipo_de_factura') or form_data.get('invoice_category')

            # --- Exchange rate logic ---
            currency = invoice_data.get('currency', 'RD$')
            # check if the form already provided a rate (campo legacy or nuevo)
            candidate_rate = form_data.get('tasa_cambio') or form_data.get('exchange_rate') or None
            exchange_rate = None
            if candidate_rate not in (None, '', 0):
                try:
                    exchange_rate = float(candidate_rate)
                except Exception:
                    exchange_rate = None

            if currency != "RD$":
                # si no tenemos rate razonable preguntamos al usuario
                if not exchange_rate or exchange_rate == 1.0:
                    # proponemos un valor por defecto (1.0) o intentamos tomar de current_transactions primer elemento
                    default_rate = "1.0"
                    # si hay transacciones previas intentamos usar su exchange_rate como sugerencia
                    try:
                        if self.current_transactions and len(self.current_transactions) > 0:
                            default_rate = str(self.current_transactions[0].get('exchange_rate', default_rate) or default_rate)
                    except Exception:
                        pass

                    rate_str, ok = QInputDialog.getText(parent_window, "Tasa de Cambio",
                                                    f"Tasa para {currency} a RD$:",
                                                    text=str(default_rate))
                    if not ok:
                        # el usuario canceló; abortamos la operación de guardado
                        return
                    try:
                        exchange_rate = float(rate_str)
                    except Exception:
                        QMessageBox.critical(parent_window, "Tasa inválida", "La tasa de cambio ingresada no es válida.")
                        return
            else:
                exchange_rate = 1.0

            invoice_data['exchange_rate'] = float(exchange_rate or 1.0)
            invoice_data['total_amount_rd'] = float(invoice_data['total_amount']) * float(invoice_data['exchange_rate'])

            # Añadir company_id en creación
            if not invoice_id:
                selected_name = self.company_selector.currentText() if hasattr(self, "company_selector") else (self.company_selector_var.get() if hasattr(self, "company_selector_var") else None)
                company_id = None
                if selected_name and hasattr(self, "companies_list"):
                    company_id = next((c['id'] for c in self.companies_list if c['name'] == selected_name), None)
                invoice_data['company_id'] = company_id

            # Debug: imprime lo que vamos a enviar al controlador (temporal, quitar en producción)
            print("[DBG] Saving invoice ->", invoice_data)

            # Llamada al controlador (update o add)
            if invoice_id:
                success, message = self.controller.update_invoice(invoice_id, invoice_data)
            else:
                success, message = self.controller.add_invoice(invoice_data)

            if success:
                QMessageBox.information(parent_window, "Éxito", message)
                # cerrar la ventana y refrescar dashboard
                try:
                    parent_window.accept() if hasattr(parent_window, "accept") else parent_window.destroy()
                except Exception:
                    pass
                self._refresh_dashboard()
            else:
                QMessageBox.critical(parent_window, "Error al Guardar", message)

        except Exception as e:
            tb = traceback.format_exc()
            print("Traceback _save_invoice_callback:\n", tb)
            QMessageBox.critical(parent_window, "Error Inesperado", f"Ocurrió un error: {e}")

    def _edit_selected_invoice(self, row, column):
        # Obtén el ID de la factura desde la fila seleccionada
        if not self.current_transactions or row >= len(self.current_transactions):
            return
        invoice_data = self.current_transactions[row]
        from add_invoice_window_qt import AddInvoiceWindowQt
        win = AddInvoiceWindowQt(self, self.controller, tipo_factura=invoice_data['invoice_type'],
                                on_save=self._save_invoice_callback, existing_data=invoice_data)
        win.exec()


# En la clase MainApplicationQt (app_gui_qt.py)
# Puedes añadir este método al final de la clase, antes de las funciones de menú

    def _diagnose_selected_row(self):
        """
        Obtiene los datos crudos de la fila seleccionada y los muestra en una ventana.
        """
        import json # Importamos json para un formato legible

        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona una fila en la tabla para diagnosticar.")
            return

        # Verificamos que el índice de la fila sea válido para la lista de datos
        if current_row >= len(self.current_transactions):
            QMessageBox.critical(self, "Error de Sincronización", 
                                 f"El índice de la fila ({current_row}) está fuera del rango de los datos actuales ({len(self.current_transactions)} registros).\n"
                                 "Intenta refrescar los datos.")
            return

        # Obtenemos el diccionario de datos exacto para esa fila
        transaction_data = self.current_transactions[current_row]
        
        # Formateamos los datos para que sean fáciles de leer
        if transaction_data:
            # json.dumps es excelente para "imprimir bonito" un diccionario
            pretty_data = json.dumps(transaction_data, indent=4, ensure_ascii=False, default=str)
        else:
            pretty_data = "El dato para esta fila es None o está vacío."

        info_message = f"Datos crudos para la fila {current_row}:\n\n{pretty_data}"
        
        QMessageBox.information(self, "Diagnóstico de Fila", info_message)

# En la clase MainApplicationQt (app_gui_qt.py), pégalos al final de la clase

    def _select_row_for_comparison(self, row_type):
        """Guarda los datos de la fila seleccionada para la comparación."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona una fila en la tabla.")
            return

        if current_row >= len(self.current_transactions):
            QMessageBox.critical(self, "Error", "El índice de la fila está fuera de rango.")
            return

        transaction_data = self.current_transactions[current_row]

        if row_type == 'full':
            self.full_row_data = transaction_data
            QMessageBox.information(self, "Paso 1 Completado", "Fila LLENA seleccionada.\nAhora, selecciona una fila vacía y presiona el botón 2.")
        elif row_type == 'empty':
            self.empty_row_data = transaction_data
            QMessageBox.information(self, "Paso 2 Completado", "Fila VACÍA seleccionada.\nAhora, presiona el botón 3 para generar el reporte.")

    def _generate_comparison_report(self):
        """Genera un archivo Excel comparando los datos de la fila llena y la vacía."""
        if not hasattr(self, 'full_row_data') or not self.full_row_data:
            QMessageBox.warning(self, "Falta Información", "Primero debes seleccionar una fila LLENA con el botón 1.")
            return
        
        if not hasattr(self, 'empty_row_data'):
            QMessageBox.warning(self, "Falta Información", "Primero debes seleccionar una fila VACÍA con el botón 2.")
            return
        
        df_full = pd.DataFrame([self.full_row_data])
        df_empty = pd.DataFrame([self.empty_row_data])

        try:
            # --- SOLUCIÓN DEFINITIVA ---
            # Itera a través de ambos DataFrames para eliminar la información de zona horaria.
            # Esta versión es más robusta y convierte cualquier columna de fecha/hora.
            for df in [df_full, df_empty]:
                # Busca todas las columnas que son de tipo fecha/hora (con o sin zona horaria)
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        # Forzamos la columna a no tener zona horaria (timezone-naive)
                        df[col] = df[col].dt.tz_localize(None)
            # --- FIN DE LA SOLUCIÓN ---

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Diagnostico_Fila_Llena_vs_Vacia_{timestamp}.xlsx"
            
            save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo de Diagnóstico", filename, "Archivos de Excel (*.xlsx)")

            if save_path:
                with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                    df_full.to_excel(writer, sheet_name='Fila_Llena_Datos', index=False)
                    df_empty.to_excel(writer, sheet_name='Fila_Vacia_Datos', index=False)
                
                QMessageBox.information(self, "Éxito", f"Archivo de diagnóstico guardado en:\n{save_path}")
                self.full_row_data = None
                self.empty_row_data = None

        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo generar el archivo Excel:\n{e}")

# In MainApplicationQt (app_gui_qt.py)

    def _diagnose_row_to_terminal(self):
        """
        Gets the raw data for the selected row and prints it to the terminal.
        """
        import json # Used for pretty-printing the dictionary

        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona una fila en la tabla para diagnosticar.")
            return

        if current_row >= len(self.current_transactions):
            QMessageBox.critical(self, "Error de Sincronización", "El índice de la fila está fuera de rango. Intenta refrescar los datos.")
            return

        # Get the exact data dictionary for that row
        transaction_data = self.current_transactions[current_row]
        
        # Format the data for easy reading
        pretty_data = json.dumps(transaction_data, indent=4, ensure_ascii=False, default=str)

        # Print to the terminal
        print("\n" + "="*50)
        print(f"  DIAGNÓSTICO DE DATOS CRUDOS PARA LA FILA: {current_row}")
        print("="*50)
        print(pretty_data)
        print("="*50 + "\n")

        QMessageBox.information(self, "Diagnóstico Completo", "Los datos crudos de la fila seleccionada se han impreso en la terminal.")

    def _open_add_expense_window(self):
        """
        Abre la ventana específica para registrar una factura de gasto.
        Si la ventana retorna Accepted, refresca el dashboard.
        """
        win = AddExpenseWindowQt(parent=self, controller=self.controller, on_save=self._save_invoice_callback)
        # Ejecuta como modal
        res = win.exec()
        # Si la ventana cerró con Accepted, refrescamos la vista
        from PyQt6.QtWidgets import QDialog
        if res == QDialog.DialogCode.Accepted:
            self._refresh_dashboard()
    def _edit_selected_invoice(self, row, column):
        # Obtén el índice/ID de la factura desde la fila seleccionada
        if not self.current_transactions or row < 0 or row >= len(self.current_transactions):
            return
        invoice_data = self.current_transactions[row]
        invoice_type = invoice_data.get('invoice_type', '')

        if invoice_type == 'gasto':
            # Abrir ventana de gasto
            win = AddExpenseWindowQt(self, self.controller, on_save=self._save_invoice_callback, existing_data=invoice_data, invoice_id=invoice_data.get('id'))
            win.exec()
        else:
            # Abrir ventana de emitida (la tuya existente)
            from add_invoice_window_qt import AddInvoiceWindowQt
            win = AddInvoiceWindowQt(self, self.controller, tipo_factura=invoice_data.get('invoice_type', 'emitida'), on_save=self._save_invoice_callback, existing_data=invoice_data, invoice_id=invoice_data.get('id'))
            win.exec()

        # Después de la edición, refrescamos para releer datos
        self._refresh_dashboard()



# -------------------------------------------------------------------
# Método nuevo: crear la zona de filtro + botones + tabla de transacciones
# Reemplaza en _create_main_layout la sección que crea tabla_filtro_layout
# y self.table por una llamada a: self._create_transactions_panel(right_layout)
# -------------------------------------------------------------------
    def _create_transactions_panel(self, right_layout):
        """
        Crea y añade al right_layout:
        - la barra de filtro (Mostrar: Todos/Ingresos/Gastos) junto a los botones Editar/Eliminar
        - la QTableWidget (self.table) con configuración adecuada
        """
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget
        # Contenedor para la barra de filtro y botones
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        lbl = QLabel("Mostrar:")
        filter_layout.addWidget(lbl)

        # Combo filtro
        self.transaction_filter = QComboBox()
        self.transaction_filter.addItems(["Todos", "Ingresos", "Gastos"])
        self.transaction_filter.setCurrentText("Todos")
        self.transaction_filter.currentIndexChanged.connect(self._apply_transaction_filter)
        filter_layout.addWidget(self.transaction_filter)

        # Botones Editar / Eliminar al lado del filtro
        self.edit_tx_btn = QPushButton("Editar")
        self.edit_tx_btn.setToolTip("Editar la transacción seleccionada")
        self.edit_tx_btn.clicked.connect(self._edit_selected_transaction)
        filter_layout.addWidget(self.edit_tx_btn)

        self.delete_tx_btn = QPushButton("Eliminar")
        self.delete_tx_btn.setToolTip("Eliminar la transacción seleccionada")
        self.delete_tx_btn.clicked.connect(self._delete_selected_transaction)
        filter_layout.addWidget(self.delete_tx_btn)

        filter_layout.addStretch()
        # Añadir la barra al layout provisto
        right_layout.addWidget(filter_widget)

        # Crear la tabla y guardarla en self.table (si ya existe, la sobreescribimos)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "No. Fact.", "Empresa", "ITBIS (RD$)", "Monto Original", "Total (RD$)"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Conexiones de interacción
        # Doble-clic abre editor
        self.table.cellDoubleClicked.connect(lambda r, c: self._edit_selected_transaction(r))
        # Clic derecho -> menú (ya conectado en __init__, pero aseguramos política)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Finalmente agregamos la tabla al layout
        right_layout.addWidget(self.table)

        # Nota: si en tu _create_main_layout antes habías creado la tabla,
        # reemplaza esa sección por: self._create_transactions_panel(right_layout)

# -------------------------------------------------------------------
# Métodos de interacción: menú contextual, obtener id, editar y eliminar
# (Pégalos dentro de la clase MainApplicationQt)
# -------------------------------------------------------------------
    def _show_context_menu(self, pos):
        """
        Muestra el menú contextual con Editar / Eliminar en la fila clickeada.
        pos es QPoint relativo al viewport de la tabla.
        """
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        # seleccionar la fila visualmente
        self.table.selectRow(row)

        menu = QMenu(self)
        menu.addAction("Editar", lambda: self._edit_selected_transaction(row))
        menu.addAction("Eliminar", lambda: self._delete_selected_transaction(row))
        menu.exec(self.table.viewport().mapToGlobal(pos))


    def _get_invoice_id_from_row(self, row):
        """
        Devuelve el invoice id almacenado en UserRole del item No. Fact. (columna 2).
        """
        try:
            item = self.table.item(row, 2)
            if not item:
                return None
            val = item.data(Qt.ItemDataRole.UserRole)
            if val is None or val == "":
                return None
            try:
                return int(val)
            except Exception:
                return val
        except Exception:
            return None


    def _edit_selected_transaction(self, row=None):
        """
        Abre la ventana de edición para la transacción seleccionada.
        Si row es None, usa la fila actualmente seleccionada.
        """
        from PyQt6.QtWidgets import QMessageBox
        if row is None:
            row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecciona primero una transacción en la tabla.")
            return

        invoice_id = self._get_invoice_id_from_row(row)
        if not invoice_id:
            QMessageBox.warning(self, "Editar", "No se pudo determinar el ID de la factura seleccionada.")
            return

        # Obtener datos completos desde el controlador
        try:
            existing_data = self.controller.get_invoice_by_id(int(invoice_id))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la factura: {e}")
            return

        if not existing_data:
            QMessageBox.warning(self, "Editar", "No se encontró la factura en la base de datos.")
            return

        # Abrir la ventana apropiada según el tipo
        try:
            if existing_data.get('invoice_type') == 'emitida':
                dlg = AddInvoiceWindowQt(self, self.controller, tipo_factura='emitida', on_save=self._save_invoice_callback, existing_data=existing_data, invoice_id=invoice_id)
            else:
                dlg = AddExpenseWindowQt(self, self.controller, on_save=self._save_invoice_callback, existing_data=existing_data, invoice_id=invoice_id)

            # Modal: si devuelve Accepted refrescar
            if hasattr(dlg, 'exec') and dlg.exec() == QDialog.DialogCode.Accepted:
                self._refresh_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana de edición: {e}")


    def _delete_selected_transaction(self, row=None):
        """
        Borra la transacción seleccionada tras confirmación y refresca la tabla.
        """
        from PyQt6.QtWidgets import QMessageBox
        if row is None:
            row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Eliminar", "Selecciona primero una transacción en la tabla.")
            return

        invoice_id = self._get_invoice_id_from_row(row)
        if not invoice_id:
            QMessageBox.warning(self, "Eliminar", "No se pudo determinar el ID de la factura seleccionada.")
            return

        resp = QMessageBox.question(self, "Confirmar Eliminación", "¿Deseas eliminar esta factura de forma permanente?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            success, message = self.controller.delete_invoice(int(invoice_id))
            if success:
                QMessageBox.information(self, "Eliminado", message)
                self._refresh_dashboard()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la factura: {e}")

    def _open_tax_calculation_manager(self):
        """
        Abre la ventana de gestión de cálculos guardados (lista).
        Esta ventana abre AdvancedRetentionWindowQt para Nuevo / Editar.
        Al volver, refresca el dashboard por si hubo cambios.
        """
        try:
            dlg = TaxCalculationManagementWindowQt(self, self.controller)
            dlg.exec()
            # Refrescar el dashboard al cerrar el gestor (por si se guardaron cambios)
            self._refresh_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la gestión de cálculos:\n{e}")

    def _open_attachment_editor(self, relative_or_absolute_path):
        """
        Abre el editor de anexos. Si se pasa ruta relativa, la intenta resolver usando
        controller.get_setting('attachment_base_path').
        """
        import os
        path = relative_or_absolute_path or ""
        if not os.path.isabs(path):
            try:
                base = self.controller.get_setting("attachment_base_path")
            except Exception:
                base = None
            if base:
                candidate = os.path.join(base, path)
                if os.path.exists(candidate):
                    path = candidate
        if not os.path.exists(path):
            QMessageBox.warning(self, "Archivo no encontrado", f"No se encontró el anexo: {path}")
            return
        dlg = AttachmentEditorWindowQt(self, path)
        dlg.exec()


