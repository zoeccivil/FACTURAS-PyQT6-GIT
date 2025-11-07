import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext, ttk
import json
import os
import datetime
from tkcalendar import DateEntry
from fpdf import FPDF
import re # <<< AÑADE ESTA LÍNEA
import pandas as pd

# =========================================================================
# Funciones de Lógica de Negocio (Backend)
# (Todo el código de backend permanece sin cambios)
# =========================================================================

def eliminar_factura(nombre_empresa, tipo, no_fact):
    datos_empresa = cargar_datos_empresa(nombre_empresa)
    if tipo == "emitida":
        facturas = datos_empresa.get("facturas_emitidas", [])
        nueva_lista = [f for f in facturas if f.get("no_fact") != no_fact]
        if len(facturas) == len(nueva_lista):
            return False
        datos_empresa["facturas_emitidas"] = nueva_lista
    elif tipo == "gasto":
        facturas = datos_empresa.get("facturas_gastos", [])
        nueva_lista = [f for f in facturas if f.get("no_fact") != no_fact]
        if len(facturas) == len(nueva_lista):
            return False
        datos_empresa["facturas_gastos"] = nueva_lista
    return guardar_datos_empresa(nombre_empresa, datos_empresa)


def modificar_factura(filepath, tipo, no_fact, nueva_data):
    if eliminar_factura(filepath, tipo, no_fact):
        if tipo == "emitida":
            return agregar_factura_emitida(
                filepath,
                nueva_data["fecha"],
                nueva_data["no_fact"],
                nueva_data["tipo_factura"],
                nueva_data["moneda"],
                nueva_data["rnc"],
                nueva_data["empresa"],
                nueva_data["itbis"],
                nueva_data["factura_total"],
                nueva_data["tasa_conversion"],
                nueva_data["monto_convertido_rd"]
            )
        elif tipo == "gasto":
            return agregar_factura_gasto(
                filepath,
                nueva_data["fecha"],
                nueva_data["no_fact"],
                nueva_data["rnc"],
                nueva_data["lugar_compra"],
                nueva_data["moneda"],
                nueva_data["itbis"],
                nueva_data["factura_total"],
                nueva_data["tasa_conversion"],
                nueva_data["monto_convertido_rd"]
            )
    return False

def cargar_datos_empresa(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "available_currencies" not in data:
                    data["available_currencies"] = ["RD$", "USD"]
                if "rnc_directory" not in data:
                    data["rnc_directory"] = {}
                return data
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            messagebox.showerror("Error de lectura", f"Error al leer el archivo '{os.path.basename(filepath)}': {e}")
            return {"facturas_emitidas": [], "facturas_gastos": [], "available_currencies": ["RD$", "USD"], "rnc_directory": {}}
    else:
        return {"facturas_emitidas": [], "facturas_gastos": [], "available_currencies": ["RD$", "USD"], "rnc_directory": {}}

def guardar_datos_empresa(filepath, datos):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error al guardar", f"No se pudieron guardar los datos en '{os.path.basename(filepath)}': {e}")
        return False
    return True

def actualizar_directorio_rnc(nombre_empresa, rnc, nombre_completo_empresa):
    datos_empresa = cargar_datos_empresa(nombre_empresa)
    datos_empresa["rnc_directory"][rnc] = nombre_completo_empresa
    return guardar_datos_empresa(nombre_empresa, datos_empresa)

def add_new_currency_to_file(nombre_empresa, new_currency):
    datos_empresa = cargar_datos_empresa(nombre_empresa)
    if "available_currencies" not in datos_empresa:
        datos_empresa["available_currencies"] = ["RD$", "USD"]
    if new_currency not in datos_empresa["available_currencies"]:
        datos_empresa["available_currencies"].append(new_currency)
        return guardar_datos_empresa(nombre_empresa, datos_empresa)
    return False

def get_available_currencies(nombre_empresa):
    datos_empresa = cargar_datos_empresa(nombre_empresa)
    return datos_empresa.get("available_currencies", ["RD$", "USD"])


def agregar_factura_emitida(filepath, fecha_str, no_fact, tipo_factura, moneda, rnc, empresa_emitida, itbis, factura_total, tasa_conversion, monto_convertido_rd):
    datos_empresa = cargar_datos_empresa(filepath)
    nueva_factura = {
        "fecha": fecha_str,
        "fecha_imputacion": datetime.date.today().strftime('%Y-%m-%d'),
        "no_fact": no_fact,
        "tipo_factura": tipo_factura,
        "moneda": moneda,
        "rnc": rnc,
        "empresa": empresa_emitida,
        "itbis": itbis,
        "factura_total": factura_total,
        "tasa_conversion": tasa_conversion,
        "monto_convertido_rd": monto_convertido_rd
    }
    datos_empresa["facturas_emitidas"].append(nueva_factura)
    if guardar_datos_empresa(filepath, datos_empresa):
        messagebox.showinfo("Éxito", "Factura emitida registrada exitosamente.")
        return True
    return False

def agregar_factura_gasto(filepath, fecha_str, no_fact_gasto, rnc, lugar_compra, moneda, itbis, factura_total, tasa_conversion, monto_convertido_rd):
    datos_empresa = cargar_datos_empresa(filepath)
    nueva_factura = {
        "fecha": fecha_str,
        "fecha_imputacion": datetime.date.today().strftime('%Y-%m-%d'),
        "no_fact": no_fact_gasto,
        "rnc": rnc,
        "lugar_compra": lugar_compra,
        "moneda": moneda,
        "itbis": itbis,
        "factura_total": factura_total,
        "tasa_conversion": tasa_conversion,
        "monto_convertido_rd": monto_convertido_rd
    }
    datos_empresa["facturas_gastos"].append(nueva_factura)
    if guardar_datos_empresa(filepath, datos_empresa):
        messagebox.showinfo("Éxito", "Factura de gasto registrada exitosamente.")
        return True
    return False

def generar_reporte_mensual(filepath, nombre_empresa, mes, anio):
    datos_empresa = cargar_datos_empresa(filepath)
    facturas_emitidas_en_mes, facturas_gastos_en_mes = [], []

    for factura in datos_empresa.get("facturas_emitidas", []):
        try:
            fecha_factura = datetime.datetime.strptime(factura.get("fecha", ""), '%Y-%m-%d')
            if fecha_factura.month == mes and fecha_factura.year == anio:
                facturas_emitidas_en_mes.append(factura)
        except (ValueError, TypeError, KeyError):
            pass

    for factura in datos_empresa.get("facturas_gastos", []):
        try:
            fecha_factura = datetime.datetime.strptime(factura.get("fecha", ""), '%Y-%m-%d')
            if fecha_factura.month == mes and fecha_factura.year == anio:
                facturas_gastos_en_mes.append(factura)
        except (ValueError, TypeError, KeyError):
            pass
            
    # <<< INICIO DE CÁLCULOS CORREGIDOS >>>
    total_itbis_emitidas = sum(float(f.get("itbis", 0.0)) * float(f.get("tasa_conversion", 1.0)) for f in facturas_emitidas_en_mes)
    total_factura_emitidas = sum(float(f.get("monto_convertido_rd", f.get("factura_total", 0.0))) for f in facturas_emitidas_en_mes)
    total_itbis_gastos = sum(float(f.get("itbis", 0.0)) * float(f.get("tasa_conversion", 1.0)) for f in facturas_gastos_en_mes)
    total_factura_gastos = sum(float(f.get("monto_convertido_rd", f.get("factura_total", 0.0))) for f in facturas_gastos_en_mes)
    # <<< FIN DE CÁLCULOS CORREGIDOS >>>

    reporte_str = f"--- Reporte Mensual para '{nombre_empresa}' - Mes: {mes}/{anio} ---\n\n"
    reporte_str += "--- Facturas Emitidas (Ingresos) ---\n"
    if facturas_emitidas_en_mes:
        # <<< INICIO DE FORMATO CORREGIDO (EMITIDAS) >>>
        reporte_str += f"{'Fecha':<12} {'Tipo':<10} {'No. Fact.':<12} {'Empresa':<25} {'RNC':<15} {'Total Orig.':>15} {'Total (RD$)':>15}\n" + "-" * 110 + "\n"
        for f in facturas_emitidas_en_mes:
            monto_orig = f"{float(f.get('factura_total', 0.0)):,.2f} {f.get('moneda', '')}"
            monto_rd = float(f.get('monto_convertido_rd', f.get('factura_total', 0.0)))
            reporte_str += f"{f.get('fecha', ''):<12} {f.get('tipo_factura', '')[0:9]:<10} {f.get('no_fact', ''):<12} {f.get('empresa', '')[0:24]:<25} {f.get('rnc', ''):<15} {monto_orig:>15} {monto_rd:>15,.2f}\n"
        # <<< FIN DE FORMATO CORREGIDO (EMITIDAS) >>>
        reporte_str += "-" * 110 + f"\nTotal ITBIS Emitidas (RD$): {total_itbis_emitidas:,.2f}\nTotal Facturas Emitidas (RD$): {total_factura_emitidas:,.2f}\n"
    else: reporte_str += "No hay facturas emitidas registradas para este mes.\n"
    reporte_str += "\n--- Facturas de Gastos ---\n"
    if facturas_gastos_en_mes:
        # <<< INICIO DE FORMATO CORREGIDO (GASTOS) >>>
        reporte_str += f"{'Fecha':<12} {'No. Fact.':<12} {'RNC':<15} {'Empresa':<28} {'Total Orig.':>15} {'Total (RD$)':>15}\n" + "-" * 110 + "\n"
        for f in facturas_gastos_en_mes:
            monto_orig = f"{float(f.get('factura_total', 0.0)):,.2f} {f.get('moneda', '')}"
            monto_rd = float(f.get('monto_convertido_rd', f.get('factura_total', 0.0)))
            reporte_str += f"{f.get('fecha', ''):<12} {f.get('no_fact', ''):<12} {f.get('rnc', ''):<15} {f.get('lugar_compra', '')[0:27]:<28} {monto_orig:>15} {monto_rd:>15,.2f}\n"
        # <<< FIN DE FORMATO CORREGIDO (GASTOS) >>>
        reporte_str += "-" * 110 + f"\nTotal ITBIS Gastos (RD$): {total_itbis_gastos:,.2f}\nTotal Facturas Gastos (RD$): {total_factura_gastos:,.2f}\n"
    else: reporte_str += "No hay facturas de gastos registradas para este mes.\n"
    reporte_str += f"\n--- Resumen General {mes}/{anio} (en RD$) ---\nITBIS Neto (Emitido - Gasto): {(total_itbis_emitidas - total_itbis_gastos):,.2f}\nTotal Neto (Emitido - Gasto): {(total_factura_emitidas - total_factura_gastos):,.2f}\n" + "-" * 40 + "\n"
    return { "text_report": reporte_str, "data": { "month": mes, "year": anio, "company_name": nombre_empresa, "emitted_invoices": facturas_emitidas_en_mes, "expense_invoices": facturas_gastos_en_mes, "totals": { "total_itbis_emitidas": total_itbis_emitidas, "total_factura_emitidas": total_factura_emitidas, "total_itbis_gastos": total_itbis_gastos, "total_factura_gastos": total_factura_gastos, "itbis_neto": total_itbis_emitidas - total_itbis_gastos, "total_neto": total_factura_emitidas - total_factura_gastos } } }

def generar_reporte_por_imputacion(filepath, nombre_empresa, mes, anio):
    datos_empresa = cargar_datos_empresa(filepath)
    facturas_emitidas_en_mes, facturas_gastos_en_mes = [], []

    for factura in datos_empresa.get("facturas_emitidas", []):
        try:
            fecha_imputacion = factura.get("fecha_imputacion", factura.get("fecha", ""))
            fecha = datetime.datetime.strptime(fecha_imputacion, '%Y-%m-%d')
            if fecha.month == mes and fecha.year == anio:
                facturas_emitidas_en_mes.append(factura)
        except:
            continue

    for factura in datos_empresa.get("facturas_gastos", []):
        try:
            fecha_imputacion = factura.get("fecha_imputacion", factura.get("fecha", ""))
            fecha = datetime.datetime.strptime(fecha_imputacion, '%Y-%m-%d')
            if fecha.month == mes and fecha.year == anio:
                facturas_gastos_en_mes.append(factura)
        except:
            continue

    # <<< INICIO DE CÁLCULOS CORREGIDOS >>>
    total_itbis_emitidas = sum(float(f.get("itbis", 0.0)) * float(f.get("tasa_conversion", 1.0)) for f in facturas_emitidas_en_mes)
    total_factura_emitidas = sum(float(f.get("monto_convertido_rd", f.get("factura_total", 0.0))) for f in facturas_emitidas_en_mes)
    total_itbis_gastos = sum(float(f.get("itbis", 0.0)) * float(f.get("tasa_conversion", 1.0)) for f in facturas_gastos_en_mes)
    total_factura_gastos = sum(float(f.get("monto_convertido_rd", f.get("factura_total", 0.0))) for f in facturas_gastos_en_mes)
    # <<< FIN DE CÁLCULOS CORREGIDOS >>>

    reporte_str = f"--- Reporte por Imputación - {mes}/{anio} ---\n\n--- Facturas Emitidas (Ingresos) ---\n"
    if facturas_emitidas_en_mes:
        # <<< INICIO DE FORMATO CORREGIDO (EMITIDAS) >>>
        reporte_str += f"{'Fecha Imp.':<12} {'Tipo':<10} {'No. Fact.':<12} {'Empresa':<25} {'RNC':<15} {'Total Orig.':>15} {'Total (RD$)':>15}\n" + "-" * 110 + "\n"
        for f in facturas_emitidas_en_mes:
            monto_orig = f"{float(f.get('factura_total', 0.0)):,.2f} {f.get('moneda', '')}"
            monto_rd = float(f.get('monto_convertido_rd', f.get('factura_total', 0.0)))
            reporte_str += f"{f.get('fecha_imputacion', ''):<12} {f.get('tipo_factura', '')[0:9]:<10} {f.get('no_fact', ''):<12} {f.get('empresa', '')[0:24]:<25} {f.get('rnc', ''):<15} {monto_orig:>15} {monto_rd:>15,.2f}\n"
        # <<< FIN DE FORMATO CORREGIDO (EMITIDAS) >>>
        reporte_str += "-" * 110 + f"\nTotal ITBIS Emitidas (RD$): {total_itbis_emitidas:,.2f}\nTotal Facturas Emitidas (RD$): {total_factura_emitidas:,.2f}\n"
    else: reporte_str += "No hay facturas emitidas imputadas este mes.\n"
    reporte_str += "\n--- Facturas de Gastos ---\n"
    if facturas_gastos_en_mes:
        # <<< INICIO DE FORMATO CORREGIDO (GASTOS) >>>
        reporte_str += f"{'Fecha Imp.':<12} {'No. Fact.':<12} {'RNC':<15} {'Empresa':<28} {'Total Orig.':>15} {'Total (RD$)':>15}\n" + "-" * 110 + "\n"
        for f in facturas_gastos_en_mes:
            monto_orig = f"{float(f.get('factura_total', 0.0)):,.2f} {f.get('moneda', '')}"
            monto_rd = float(f.get('monto_convertido_rd', f.get('factura_total', 0.0)))
            reporte_str += f"{f.get('fecha_imputacion', ''):<12} {f.get('no_fact', ''):<12} {f.get('rnc', ''):<15} {f.get('lugar_compra', '')[0:27]:<28} {monto_orig:>15} {monto_rd:>15,.2f}\n"
        # <<< FIN DE FORMATO CORREGIDO (GASTOS) >>>
        reporte_str += "-" * 110 + f"\nTotal ITBIS Gastos (RD$): {total_itbis_gastos:,.2f}\nTotal Facturas Gastos (RD$): {total_factura_gastos:,.2f}\n"
    else: reporte_str += "No hay facturas de gastos imputadas este mes.\n"
    reporte_str += f"\n--- Resumen General {mes}/{anio} (en RD$) ---\nITBIS Neto (Emitido - Gasto): {(total_itbis_emitidas - total_itbis_gastos):,.2f}\nTotal Neto (Emitido - Gasto): {(total_factura_emitidas - total_factura_gastos):,.2f}\n" + "-" * 40 + "\n"
    return { "text_report": reporte_str, "data": { "month": mes, "year": anio, "company_name": nombre_empresa, "emitted_invoices": facturas_emitidas_en_mes, "expense_invoices": facturas_gastos_en_mes, "totals": { "total_itbis_emitidas": total_itbis_emitidas, "total_factura_emitidas": total_factura_emitidas, "total_itbis_gastos": total_itbis_gastos, "total_factura_gastos": total_factura_gastos, "itbis_neto": total_itbis_emitidas - total_itbis_gastos, "total_neto": total_factura_emitidas - total_factura_gastos } } }
# =========================================================================
# Clase de la Aplicación GUI (AppFacturas)
# =========================================================================

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', company_name="", report_title="", report_period=""):
        super().__init__(orientation, unit, format)
        self.company_name = company_name
        self.report_title = report_title
        self.report_period = report_period

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{self.report_title} - {self.company_name}', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Período: {self.report_period}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')


class AppFacturas:
    def __init__(self, master):
        self.master = master
        master.title("Asistente de Gestión de Facturas")
        master.geometry("1200x700")
        master.resizable(True, True)

        self.nombre_empresa_actual = ""
        self.current_filepath = ""
        self.last_report_data = None

        top_frame = tk.Frame(master, bd=2, relief="groove", padx=10, pady=5)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)

        self.label_empresa_display = tk.Label(top_frame, text="Empresa Actual: Ninguna seleccionada (Archivo: N/A)", font=("Arial", 12, "bold"))
        self.label_empresa_display.pack(side=tk.LEFT, padx=10)

        self.btn_crear_empresa = tk.Button(top_frame, text="Crear Nueva Empresa", command=self.crear_nueva_empresa)
        self.btn_crear_empresa.pack(side=tk.RIGHT, padx=5)

        self.btn_seleccionar_empresa = tk.Button(top_frame, text="Seleccionar Archivo Existente", command=self.seleccionar_archivo_empresa)
        self.btn_seleccionar_empresa.pack(side=tk.RIGHT, padx=5)
        
        self.paned_window = tk.PanedWindow(master, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.left_pane = tk.Frame(self.paned_window, bd=2, relief="sunken")
        self.paned_window.add(self.left_pane, width=350)

        # --- Frame de Menú ---
        self.frame_menu = tk.LabelFrame(self.left_pane, text="Opciones de Facturación", bd=2, relief="groove", padx=10, pady=10, font=("Arial", 11, "bold"))
        self.frame_menu.pack(pady=10, padx=5, fill=tk.X)

        self.btn_add_emitida = tk.Button(self.frame_menu, text="Registrar Factura Emitida (Ingreso)", command=self.open_add_emitida_window, width=35, height=2, font=("Arial", 10))
        self.btn_add_emitida.pack(pady=5, fill=tk.X)
        self.btn_add_gasto = tk.Button(self.frame_menu, text="Registrar Factura de Gasto", command=self.open_add_gasto_window, width=35, height=2, font=("Arial", 10))
        self.btn_add_gasto.pack(pady=5, fill=tk.X)
        self.btn_generar_reporte = tk.Button(self.frame_menu, text="Ver Reporte Mensual (Ventana)", command=self.open_reporte_window, width=35, height=2, font=("Arial", 10))
        self.btn_generar_reporte.pack(pady=5, fill=tk.X)
        self.btn_gestionar_transacciones = tk.Button(self.frame_menu, text="Modificar / Eliminar Transacciones", command=self.open_manage_transactions_window, width=35, height=2, font=("Arial", 10))
        self.btn_gestionar_transacciones.pack(pady=5, fill=tk.X)
        self.btn_calculadora_retenciones = tk.Button(self.frame_menu, text="Calculadora de Retenciones", command=self.open_retention_calculator_window, width=35, height=2, font=("Arial", 10), bg="lightblue")
        self.btn_calculadora_retenciones.pack(pady=5, fill=tk.X)
        self.btn_salir = tk.Button(self.frame_menu, text="Salir", command=master.quit, width=35, height=2, bg="lightcoral", font=("Arial", 10, "bold"))
        self.btn_salir.pack(pady=15, fill=tk.X)
        self.set_menu_state("disabled")

        # --- Frame de Filtros ---
        self.filter_frame = tk.LabelFrame(self.left_pane, text="Filtros del Dashboard", bd=2, relief="groove", padx=10, pady=10, font=("Arial", 11, "bold"))
        self.filter_frame.pack(pady=10, padx=5, fill=tk.BOTH, expand=True)

        tk.Label(self.filter_frame, text="Por Mes y Año:", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        tk.Label(self.filter_frame, text="Mes:").grid(row=1, column=0, sticky="w")
        self.dashboard_mes_cb = ttk.Combobox(self.filter_frame, width=10, values=[str(i) for i in range(1, 13)])
        self.dashboard_mes_cb.grid(row=1, column=1, padx=5, sticky="w")
        
        tk.Label(self.filter_frame, text="Año:").grid(row=2, column=0, sticky="w")
        self.dashboard_anio_entry = tk.Entry(self.filter_frame, width=12)
        self.dashboard_anio_entry.grid(row=2, column=1, padx=5, sticky="w")

        tk.Label(self.filter_frame, text="Por Fecha Específica:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 5))
        self.date_filter_entry = DateEntry(self.filter_frame, width=12, date_pattern='yyyy-mm-dd', state="readonly")
        self.date_filter_entry.grid(row=4, column=0, columnspan=2, sticky="w")
        self.date_filter_entry.set_date(None)
        self.date_filter_entry.bind("<<DateEntrySelected>>", self._on_date_select)

        tk.Button(self.filter_frame, text="Aplicar Filtro Mes/Año", command=self._apply_month_year_filter).grid(row=5, column=0, columnspan=3, pady=5, sticky="ew")
        tk.Button(self.filter_frame, text="Ver Todo / Limpiar Filtros", command=self._clear_all_filters).grid(row=6, column=0, columnspan=3, pady=5, sticky="ew")

        tk.Label(self.filter_frame, text="Por No. Factura (Ingresos):", font=("Arial", 10, "bold")).grid(row=7, column=0, columnspan=3, sticky="w", pady=(10, 5))
        invoice_list_frame = tk.Frame(self.filter_frame)
        invoice_list_frame.grid(row=8, column=0, columnspan=3, sticky="nsew")
        self.filter_frame.grid_rowconfigure(8, weight=1)
        
        invoice_scrollbar = tk.Scrollbar(invoice_list_frame, orient=tk.VERTICAL)
        # ### CAMBIO 1: Habilitar selección múltiple con selectmode="extended" ###
        self.invoice_filter_listbox = tk.Listbox(
            invoice_list_frame, 
            yscrollcommand=invoice_scrollbar.set, 
            exportselection=False,
            selectmode="extended" # <-- ESTA LÍNEA ES LA CLAVE
        )
        invoice_scrollbar.config(command=self.invoice_filter_listbox.yview)
        
        invoice_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.invoice_filter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.invoice_filter_listbox.bind("<<ListboxSelect>>", self._on_invoice_select)
        
        # --- Panel Derecho ---
        self.right_pane = tk.Frame(self.paned_window, bd=2, relief="sunken")
        self.paned_window.add(self.right_pane, width=850)

        self.summary_frame = tk.LabelFrame(self.right_pane, text="Resumen Financiero Actual", bd=2, relief="groove", padx=20, pady=15, font=("Arial", 12, "bold"))
        self.summary_frame.pack(fill=tk.X, pady=10, padx=10)
        
# gestion_facturas.py

# gestion_facturas.py
        


        self.itbis_adelantado_var = tk.StringVar(value="0.0")
        self.summary_value_widgets = {}
        # Diccionario actualizado para el layout con botón
        summary_info = {
            "Total Ingresos": {"row": 0, "col": 0}, "ITBIS Ingresos": {"row": 0, "col": 2},
            "Total Gastos": {"row": 1, "col": 0}, "ITBIS Gastos": {"row": 1, "col": 2},
        }

        # --- Creación de widgets del resumen ---
        for text, props in summary_info.items():
            tk.Label(self.summary_frame, text=f"{text}:", font=("Arial", 11)).grid(row=props["row"], column=props["col"], padx=5, pady=2, sticky="w")
            value_label = tk.Label(self.summary_frame, text="RD$0.00", font=props.get("font", ("Arial", 11)), fg=props.get("fg", "black"))
            value_label.grid(row=props["row"], column=props["col"] + 1, padx=5, pady=2, sticky="e")
            self.summary_value_widgets[text] = value_label

        # --- Fila de ITBIS Adelantado (Input) ---
        tk.Label(self.summary_frame, text="ITBIS Adelantado (Mes Ant.):", font=("Arial", 11)).grid(row=2, column=0, padx=5, pady=4, sticky="w")
        entry_widget = tk.Entry(self.summary_frame, textvariable=self.itbis_adelantado_var, font=("Arial", 11, "bold"), width=15, justify='right')
        entry_widget.grid(row=2, column=1, padx=5, pady=4, sticky="e")

        # --- Fila de ITBIS a Pagar (Resultado y Botón) ---
        tk.Label(self.summary_frame, text="ITBIS a Pagar (Restante):", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=5, pady=4, sticky="w")
        itbis_pagar_label = tk.Label(self.summary_frame, text="RD$0.00", font=("Arial", 12, "bold"), fg="black")
        itbis_pagar_label.grid(row=3, column=1, padx=5, pady=4, sticky="e")
        self.summary_value_widgets["ITBIS a Pagar (Restante)"] = itbis_pagar_label
        
        # <<< AQUÍ AÑADIMOS EL BOTÓN "CALCULAR" >>>
        btn_calcular = tk.Button(self.summary_frame, text="Calcular", font=("Arial", 9, "bold"), command=self._recalculate_itbis_restante, bg="lightblue")
        btn_calcular.grid(row=3, column=2, padx=(10, 5), pady=4, sticky="w")

        # --- Separador y Totales Finales ---
        tk.Frame(self.summary_frame, height=2, bg="gray").grid(row=4, column=0, columnspan=4, sticky="ew", pady=8)
        tk.Label(self.summary_frame, text="ITBIS Neto:", font=("Arial", 12, "bold", "underline")).grid(row=5, column=0, padx=5, pady=2, sticky="w")
        neto_label = tk.Label(self.summary_frame, text="RD$0.00", font=("Arial", 12, "bold", "underline"), fg="blue")
        neto_label.grid(row=5, column=1, padx=5, pady=2, sticky="e")
        self.summary_value_widgets["ITBIS Neto"] = neto_label

        tk.Label(self.summary_frame, text="Total Neto:", font=("Arial", 12, "bold", "underline")).grid(row=5, column=2, padx=5, pady=2, sticky="w")
        total_neto_label = tk.Label(self.summary_frame, text="RD$0.00", font=("Arial", 12, "bold", "underline"), fg="blue")
        total_neto_label.grid(row=5, column=3, padx=5, pady=2, sticky="e")
        self.summary_value_widgets["Total Neto"] = total_neto_label
        self.transactions_display_frame = tk.LabelFrame(self.right_pane, text="Transacciones Filtradas", bd=2, relief="groove", padx=10, pady=10, font=("Arial", 12, "bold"))
        self.transactions_display_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        header_font = ("Consolas", 9, "bold")
        header_text = f"{'Fecha':<12} {'Tipo':<8} {'No. Fact.':<15} {'RNC':<15} {'Empresa':<25} {'Monto Original':<20} {'Total (RD$)':>15}"
        self.header_label = tk.Label(self.transactions_display_frame, text=header_text, font=header_font, anchor="w")
        self.header_label.pack(fill=tk.X)

        tk.Frame(self.transactions_display_frame, height=1, bg="gray").pack(fill=tk.X, pady=1)

        self.transactions_text_area = scrolledtext.ScrolledText(self.transactions_display_frame, wrap=tk.WORD, font=("Consolas", 9), height=15)
        self.transactions_text_area.pack(fill=tk.BOTH, expand=True)
        self.transactions_text_area.config(state=tk.DISABLED)


    # <<< NUEVO MÉTODO >>>
    def _update_dashboard_on_change(self, *args):
        """Llama a la actualización del dashboard cuando hay un cambio en un campo monitoreado."""
        self._update_main_dashboard()

    def _recalculate_itbis_restante(self):
        """
        Calcula el ITBIS restante basándose en el ITBIS NETO y guarda el valor 
        del ITBIS adelantado en el archivo JSON de la empresa.
        """
        try:
            # --- INICIO DE LA CORRECCIÓN ---
            # 1. Obtenemos el valor del ITBIS NETO directamente del Label
            neto_text = self.summary_value_widgets["ITBIS Neto"].cget("text")
            # Limpiamos el texto para obtener solo el número (manejando negativos)
            cleaned_neto = re.sub(r'[^\d.-]', '', neto_text)
            itbis_neto = float(cleaned_neto if cleaned_neto else 0)
            # --- FIN DE LA CORRECCIÓN ---

            # 2. Obtenemos el valor del ITBIS adelantado (esto no cambia)
            adelantado_text = self.itbis_adelantado_var.get()
            itbis_adelantado = float(adelantado_text if adelantado_text else 0)
            
            # 3. Guardamos el valor del ITBIS adelantado (esto no cambia)
            if self.current_filepath:
                datos_empresa = cargar_datos_empresa(self.current_filepath)
                datos_empresa['itbis_adelantado'] = adelantado_text
                guardar_datos_empresa(self.current_filepath, datos_empresa)
                
            # --- LÍNEA DE CÁLCULO CORREGIDA ---
            itbis_a_pagar = itbis_neto - itbis_adelantado
            
            # 4. Actualizamos el Label de resultado (esto no cambia)
            self.summary_value_widgets["ITBIS a Pagar (Restante)"].config(
                text=f"RD${itbis_a_pagar:,.2f}",
                fg="darkred" if itbis_a_pagar >= 0 else "darkgreen"
            )

        except (ValueError, TypeError, KeyError):
            self.summary_value_widgets["ITBIS a Pagar (Restante)"].config(
                text="RD$0.00",
                fg="black"
            )




    def _clear_all_filters(self):
        self.dashboard_mes_cb.set('')
        self.dashboard_anio_entry.delete(0, tk.END)
        self.date_filter_entry.set_date(None)
        if self.invoice_filter_listbox.curselection():
            self.invoice_filter_listbox.selection_clear(0, tk.END)
        self._update_main_dashboard()
        
    def _populate_invoice_filter_list(self):
        self.invoice_filter_listbox.unbind("<<ListboxSelect>>")
        
        current_selection_indices = self.invoice_filter_listbox.curselection()
        
        self.invoice_filter_listbox.delete(0, tk.END)
        if not self.current_filepath: 
            self.invoice_filter_listbox.bind("<<ListboxSelect>>", self._on_invoice_select)
            return
        
        datos = cargar_datos_empresa(self.current_filepath)
        invoice_numbers = sorted(list(set([f.get("no_fact", "N/A") for f in datos.get("facturas_emitidas", [])])))
        
        for num in invoice_numbers:
            self.invoice_filter_listbox.insert(tk.END, num)
            
        if current_selection_indices:
            try:
                for idx in current_selection_indices:
                    self.invoice_filter_listbox.selection_set(idx)
            except:
                pass
                
        self.invoice_filter_listbox.bind("<<ListboxSelect>>", self._on_invoice_select)

    def _on_date_select(self, event):
        self.dashboard_mes_cb.set('')
        self.dashboard_anio_entry.delete(0, tk.END)
        if self.invoice_filter_listbox.curselection():
            self.invoice_filter_listbox.selection_clear(0, tk.END)
        selected_date = self.date_filter_entry.get_date()
        self._update_main_dashboard(specific_date=selected_date)

    # ### CAMBIO 2: Modificar el manejador para obtener una lista de facturas ###
    def _on_invoice_select(self, event):
        selection_indices = self.invoice_filter_listbox.curselection()
        if not selection_indices: return

        # Limpiar los otros filtros
        self.dashboard_mes_cb.set('')
        self.dashboard_anio_entry.delete(0, tk.END)
        self.date_filter_entry.set_date(None)
        
        # Crear una lista con todos los números de factura seleccionados
        selected_invoice_nos = [self.invoice_filter_listbox.get(i) for i in selection_indices]
        
        # Llamar a la función de actualización con la lista de facturas
        self._update_main_dashboard(invoice_nos=selected_invoice_nos)

    def seleccionar_archivo_empresa(self, event=None):
        filepath = filedialog.askopenfilename(
            parent=self.master,
            title="Seleccionar Archivo de Empresa",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            # <<< INICIO DEL CÓDIGO A AÑADIR >>>
            # Carga los datos para leer el valor guardado
            datos = cargar_datos_empresa(filepath)
            itbis_guardado = datos.get('itbis_adelantado', '0.0') # Obtiene el valor o usa '0.0' si no existe
            self.itbis_adelantado_var.set(itbis_guardado) # Actualiza el campo de texto
            # <<< FIN DEL CÓDIGO A AÑADIR >>>

            self.current_filepath = filepath
            filename = os.path.basename(filepath)            
            company_name_raw = os.path.splitext(filename)[0]
            company_name_display = ' '.join(word.capitalize() for word in company_name_raw.split('_'))
            self.nombre_empresa_actual = company_name_display
            self.label_empresa_display.config(text=f"Empresa Actual: {self.nombre_empresa_actual.upper()} (Archivo: {filename})")
            messagebox.showinfo("Empresa Seleccionada", f"Ahora estás trabajando con la empresa: {self.nombre_empresa_actual.upper()}")
            self.set_menu_state("normal")
            self._clear_all_filters()
        else:
            if not self.nombre_empresa_actual:
                self.set_menu_state("disabled")
                
    def crear_nueva_empresa(self):
        company_name_input = simpledialog.askstring("Crear Nueva Empresa", "Introduce el nombre para la nueva empresa:", parent=self.master)
        if company_name_input:
            company_name_input = company_name_input.strip()
            if not company_name_input:
                messagebox.showwarning("Advertencia", "El nombre de la empresa no puede estar vacío.", parent=self.master)
                return

            suggested_filename_base = company_name_input.replace(' ', '_').lower()
            filepath = filedialog.asksaveasfilename(
                parent=self.master,
                title="Guardar Nueva Empresa Como",
                initialfile=f"{suggested_filename_base}.json",
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            if filepath:
                self.current_filepath = filepath
                actual_filename = os.path.basename(filepath)
                actual_company_name_raw = os.path.splitext(actual_filename)[0]
                actual_company_name_display = ' '.join(word.capitalize() for word in actual_company_name_raw.split('_'))
                initial_data = {"facturas_emitidas": [], "facturas_gastos": [], "available_currencies": ["RD$", "USD"], "rnc_directory": {}, "itbis_adelantado": "0.0"}
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(initial_data, f, indent=2, ensure_ascii=False)
                    self.itbis_adelantado_var.set("0.0") # Reinicia el campo a cero
                    self.nombre_empresa_actual = actual_company_name_display
                    self.label_empresa_display.config(text=f"Empresa Actual: {self.nombre_empresa_actual.upper()} (Archivo: {actual_filename})")
                    messagebox.showinfo("Creación Exitosa", f"Nueva empresa '{self.nombre_empresa_actual.upper()}' creada y seleccionada. Archivo guardado en: {filepath}")                    
                    self.set_menu_state("normal")
                    self._clear_all_filters()
                except Exception as e:
                    messagebox.showerror("Error al Crear Archivo", f"No se pudo crear el archivo para la nueva empresa: {e}", parent=self.master)
                    self.set_menu_state("disabled")

    def set_menu_state(self, state):
        self.btn_add_emitida.config(state=state)
        self.btn_add_gasto.config(state=state)
        self.btn_generar_reporte.config(state=state)
        self.btn_gestionar_transacciones.config(state=state)
        self.btn_calculadora_retenciones.config(state=state)

    def _apply_month_year_filter(self):
        if not self.nombre_empresa_actual:
            messagebox.showwarning("Advertencia", "Por favor, selecciona o crea una empresa primero.")
            return

        mes_str = self.dashboard_mes_cb.get()
        anio_str = self.dashboard_anio_entry.get()
        try:
            filter_mes = int(mes_str) if mes_str else None
            filter_anio = int(anio_str) if anio_str else None
            if not filter_mes or not filter_anio:
                 raise ValueError("Mes y año son requeridos para este filtro.")
            if not (1 <= filter_mes <= 12 and 1900 < filter_anio <= datetime.datetime.now().year + 5):
                raise ValueError("Mes o año inválidos.")
        except ValueError as e:
            messagebox.showerror("Error de Filtro", f"Error: {e}")
            return
        
        self.date_filter_entry.set_date(None)
        if self.invoice_filter_listbox.curselection():
            self.invoice_filter_listbox.selection_clear(0, tk.END)
        self._update_main_dashboard(filter_month=filter_mes, filter_year=filter_anio)
    
    # ### CAMBIO 3: Actualizar la función para que acepte una lista de facturas ###
    def _update_main_dashboard(self, filter_month=None, filter_year=None, specific_date=None, invoice_nos=None):
        if not self.current_filepath:
            for key in self.summary_value_widgets: self.summary_value_widgets[key].config(text="RD$0.00")
            self.transactions_text_area.config(state=tk.NORMAL)
            self.transactions_text_area.delete(1.0, tk.END)
            self.transactions_text_area.insert(tk.END, "Selecciona o crea una empresa para ver el dashboard.")
            self.transactions_text_area.config(state=tk.DISABLED)
            return
        
        self._populate_invoice_filter_list()

        datos_empresa = cargar_datos_empresa(self.current_filepath)
        filtered_emitted, filtered_gastos = [], []
        
        all_invoices = datos_empresa.get("facturas_emitidas", []) + datos_empresa.get("facturas_gastos", [])

        temp_filtered = []
        for f in all_invoices:
            try:
                fecha_dt = datetime.datetime.strptime(f["fecha"], '%Y-%m-%d')
                
                # Lógica de filtrado actualizada
                if specific_date and fecha_dt.date() != specific_date: continue
                # Si se provee una lista de facturas, chequear si la factura actual está en esa lista
                if invoice_nos and f.get("no_fact") not in invoice_nos: continue
                if filter_month and fecha_dt.month != filter_month: continue
                if filter_year and fecha_dt.year != filter_year: continue
                
                temp_filtered.append(f)
            except:
                pass
        
        for f in temp_filtered:
            if "empresa" in f:
                filtered_emitted.append(f)
            else:
                filtered_gastos.append(f)
        
        total_ingresos = sum(float(f.get('monto_convertido_rd', f.get('factura_total', 0.0))) for f in filtered_emitted)
        total_gastos = sum(float(f.get('monto_convertido_rd', f.get('factura_total', 0.0))) for f in filtered_gastos)
        itbis_ingresos = sum(float(f.get('itbis', 0.0)) * float(f.get('tasa_conversion', 1.0)) for f in filtered_emitted)
        itbis_gastos = sum(float(f.get('itbis', 0.0)) * float(f.get('tasa_conversion', 1.0)) for f in filtered_gastos)


        itbis_neto = itbis_ingresos - itbis_gastos
        total_neto = total_ingresos - total_gastos

        # <<< INICIO DE NUEVA LÓGICA DE CÁLCULO >>>
        try:
            # Obtenemos el valor del ITBIS adelantado desde el campo de entrada
            itbis_adelantado = float(self.itbis_adelantado_var.get())
        except (ValueError, TypeError):
            itbis_adelantado = 0.0

        # Calculamos el ITBIS restante
        itbis_a_pagar = itbis_ingresos - itbis_adelantado
        # <<< FIN DE NUEVA LÓGICA DE CÁLCULO >>>

        self.summary_value_widgets["Total Ingresos"].config(text=f"RD${total_ingresos:,.2f}", fg="darkgreen")
        self.summary_value_widgets["ITBIS Ingresos"].config(text=f"RD${itbis_ingresos:,.2f}", fg="darkgreen")
        self.summary_value_widgets["Total Gastos"].config(text=f"RD${total_gastos:,.2f}", fg="darkred")
        self.summary_value_widgets["ITBIS Gastos"].config(text=f"RD${itbis_gastos:,.2f}", fg="darkred")
        
        # <<< ACTUALIZACIÓN DE WIDGETS CON NUEVOS VALORES >>>
        # Actualizamos la nueva etiqueta con el color condicional
        self.summary_value_widgets["ITBIS a Pagar (Restante)"].config(
            text=f"RD${itbis_a_pagar:,.2f}",
            fg="darkgreen" if itbis_a_pagar >= 0 else "darkred" # Verde si es >= 0, Rojo si es negativo
        )
        
        self.summary_value_widgets["ITBIS Neto"].config(text=f"RD${itbis_neto:,.2f}", fg="blue" if itbis_neto >= 0 else "purple")
        self.summary_value_widgets["Total Neto"].config(text=f"RD${total_neto:,.2f}", fg="blue" if total_neto >= 0 else "purple")
        self._recalculate_itbis_restante() # <<< AÑADE ESTA LLAMADA AQUÍ
        all_to_display = []
        for f in filtered_emitted:
            f_copy = f.copy(); f_copy['tipo'] = 'INGRESO'; all_to_display.append(f_copy)
        for f in filtered_gastos:
            f_copy = f.copy(); f_copy['tipo'] = 'GASTO'; all_to_display.append(f_copy)
        
        all_to_display.sort(key=lambda x: x.get('fecha', ''), reverse=True)

        display_text = ""
        for trans in all_to_display:
            monto_original = float(trans.get('factura_total', 0.0))
            moneda_original = trans.get('moneda', 'RD$')
            monto_convertido = float(trans.get('monto_convertido_rd', monto_original))
            monto_original_str = f"{monto_original:,.2f} {moneda_original}"
            empresa_o_lugar = trans.get('empresa', '') or trans.get('lugar_compra', '')
            
            display_text += (
                f"{trans.get('fecha', ''):<12} "
                f"{trans.get('tipo', ''):<8} "
                f"{trans.get('no_fact', 'N/A')[0:14]:<15} "
                f"{trans.get('rnc', 'N/A')[0:14]:<15} "
                f"{empresa_o_lugar[0:24]:<25} "
                f"{monto_original_str:<20} "
                f"{monto_convertido:>15,.2f}\n"
            )

        self.transactions_text_area.config(state=tk.NORMAL)
        self.transactions_text_area.delete(1.0, tk.END)
        self.transactions_text_area.insert(tk.END, display_text)
        self.transactions_text_area.config(state=tk.DISABLED)

    def open_retention_calculator_window(self):
        if not self.current_filepath:
            messagebox.showwarning("Advertencia", "Por favor, selecciona o crea una empresa primero.")
            return

        try:
            mes_str = self.dashboard_mes_cb.get()
            anio_str = self.dashboard_anio_entry.get()
            filter_month = int(mes_str) if mes_str else None
            filter_year = int(anio_str) if anio_str else None
        except (ValueError, TypeError):
            filter_month, filter_year = None, None

        datos_empresa = cargar_datos_empresa(self.current_filepath)
        filtered_incomes = []
        for f in datos_empresa.get("facturas_emitidas", []):
            try:
                fecha = datetime.datetime.strptime(f["fecha"], '%Y-%m-%d')
                if (filter_month is None or fecha.month == filter_month) and \
                   (filter_year is None or fecha.year == filter_year):
                    filtered_incomes.append(f)
            except: continue
            
        if not filtered_incomes:
            messagebox.showinfo("Sin Datos", "No hay ingresos en el filtro actual para calcular.")
            return

        calc_win = tk.Toplevel(self.master)
        calc_win.title("Calculadora de Retenciones sobre Ingresos")
        calc_win.geometry("500x450")
        calc_win.grab_set()

        porc_subtotal_var = tk.StringVar(value="4.0")
        porc_total_var = tk.StringVar(value="4.0")
        porc_itbis_var = tk.StringVar(value="100.0")
        
        calculation_results = {}

        config_frame = ttk.LabelFrame(calc_win, text="Porcentajes de Retención (Editables)", padding=10)
        config_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(config_frame, text="Retención sobre Subtotal (%):").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=porc_subtotal_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(config_frame, text="Retención sobre Total (%):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=porc_total_var).grid(row=1, column=1, sticky="ew")
        ttk.Label(config_frame, text="Retención sobre ITBIS (%):").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=porc_itbis_var).grid(row=2, column=1, sticky="ew")
        config_frame.columnconfigure(1, weight=1)

        results_frame = ttk.LabelFrame(calc_win, text="Resultados del Cálculo", padding=10)
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        results_text = scrolledtext.ScrolledText(results_frame, height=10, font=("Consolas", 10))
        results_text.pack(fill="both", expand=True)
        results_text.config(state=tk.DISABLED)

        def do_calculation():
            nonlocal calculation_results
            try:
                p_sub = float(porc_subtotal_var.get())
                p_tot = float(porc_total_var.get())
                p_itb = float(porc_itbis_var.get())
                
                total_general_rd = sum(float(f.get('monto_convertido_rd', f.get('factura_total', 0.0))) for f in filtered_incomes)
                total_itbis_rd = sum(float(f.get('itbis', 0.0)) * float(f.get('tasa_conversion', 1.0)) for f in filtered_incomes)
                total_subtotal_rd = total_general_rd - total_itbis_rd

                ret_subtotal = total_subtotal_rd * (p_sub / 100)
                ret_total = total_general_rd * (p_tot / 100)
                ret_itbis = total_itbis_rd * (p_itb / 100)
                
                # ### CAMBIO 3: NUEVO CÁLCULO DEL TOTAL A RETENER ###
                total_a_retener = ret_total + ret_itbis
                
                calculation_results = {
                    "num_invoices": len(filtered_incomes),
                    "total_subtotal_rd": total_subtotal_rd, "total_itbis_rd": total_itbis_rd, "total_general_rd": total_general_rd,
                    "p_sub": p_sub, "p_tot": p_tot, "p_itb": p_itb,
                    "ret_subtotal": ret_subtotal, "ret_total": ret_total, "ret_itbis": ret_itbis,
                    "total_a_retener": total_a_retener
                }

                texto_resultado = (
                    f"Cálculo sobre {len(filtered_incomes)} facturas de ingreso:\n"
                    f"{'-'*45}\n"
                    f"{'Total Subtotal:':<25} RD${total_subtotal_rd:,.2f}\n"
                    f"{'Total ITBIS:':<25} RD${total_itbis_rd:,.2f}\n"
                    f"{'Total General:':<25} RD${total_general_rd:,.2f}\n"
                    f"{'-'*45}\n\n"
                    f"CÁLCULOS DE RETENCIÓN DETALLADOS:\n"
                    f"Retención del {p_sub:.2f}% del Subtotal: RD${ret_subtotal:,.2f}\n"
                    f"Retención del {p_tot:.2f}% del Total:    RD${ret_total:,.2f}\n"
                    f"Retención del {p_itb:.2f}% del ITBIS:  RD${ret_itbis:,.2f}\n\n"
                    f"---------------------------------------------\n"
                    f"{'TOTAL A RETENER:':<25} RD${total_a_retener:,.2f}\n"
                    f"---------------------------------------------"
                )
                
                results_text.config(state=tk.NORMAL)
                results_text.delete('1.0', tk.END)
                results_text.insert(tk.END, texto_resultado)
                results_text.config(state=tk.DISABLED)

            except ValueError:
                messagebox.showerror("Error de Valor", "Asegúrate de que los porcentajes sean números válidos.", parent=calc_win)
                calculation_results = {}
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}", parent=calc_win)
                calculation_results = {}
        
        def export_to_pdf():
            if not calculation_results:
                messagebox.showwarning("Sin datos", "Primero debes realizar un cálculo exitoso.", parent=calc_win)
                return
            
            periodo_str = f"{filter_month}/{filter_year}" if filter_month and filter_year else "Todos los Períodos"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
                title="Guardar Reporte de Retenciones",
                initialfile=f"Reporte_Retenciones_{self.nombre_empresa_actual.replace(' ', '_')}_{periodo_str.replace('/', '-')}.pdf"
            )

            if not file_path: return

            try:
                pdf = PDF(company_name=self.nombre_empresa_actual,
                          report_title="Reporte de Cálculo de Retenciones",
                          report_period=periodo_str)
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f"Base del Cálculo ({calculation_results['num_invoices']} facturas de ingreso)", 0, 1, 'L')
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 7, f"Total Subtotal: RD${calculation_results['total_subtotal_rd']:,.2f}", 0, 1, 'L')
                pdf.cell(0, 7, f"Total ITBIS: RD${calculation_results['total_itbis_rd']:,.2f}", 0, 1, 'L')
                pdf.cell(0, 7, f"Total General: RD${calculation_results['total_general_rd']:,.2f}", 0, 1, 'L')
                pdf.ln(5)

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Resultados de Retenciones", 0, 1, 'L')
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 7, f"Retencion del {calculation_results['p_sub']:.2f}% del Subtotal: RD${calculation_results['ret_subtotal']:,.2f}", 0, 1, 'L')
                pdf.cell(0, 7, f"Retencion del {calculation_results['p_tot']:.2f}% del Total: RD${calculation_results['ret_total']:,.2f}", 0, 1, 'L')
                pdf.cell(0, 7, f"Retencion del {calculation_results['p_itb']:.2f}% del ITBIS: RD${calculation_results['ret_itbis']:,.2f}", 0, 1, 'L')
                pdf.ln(5)
                
                # Total a Retener en el PDF
                pdf.set_font('Arial', 'B', 13)
                pdf.cell(0, 8, f"TOTAL A RETENER: RD${calculation_results['total_a_retener']:,.2f}", border=1, ln=1, align='C')

                pdf.output(file_path)
                messagebox.showinfo("Éxito", f"Reporte PDF guardado exitosamente en:\n{file_path}", parent=calc_win)

            except Exception as e:
                messagebox.showerror("Error al Exportar", f"No se pudo generar el PDF: {e}", parent=calc_win)

        button_frame = ttk.Frame(calc_win)
        button_frame.pack(pady=10, fill='x', padx=10)

        ttk.Button(button_frame, text="Calcular", command=do_calculation).pack(side='left', expand=True, padx=5)
        ttk.Button(button_frame, text="Exportar a PDF", command=export_to_pdf).pack(side='left', expand=True, padx=5)

        do_calculation()
    
    # --- El resto de los métodos de la clase no necesitan cambios ---
    def _save_invoice_data(self, parent_window, invoice_type):
        try:
            tasa_conversion = 1.0
            monto_convertido_rd = 0.0

            if invoice_type == "emitida":
                moneda = self.moneda_emitida_cb.get()
                factura_total_str = self.factura_total_emitida_entry.get()
                
                if moneda != "RD$":
                    tasa_str = simpledialog.askstring("Tasa de Cambio", f"Introduce la tasa de cambio para {moneda} a RD$:", parent=parent_window)
                    if not tasa_str: return
                    tasa_conversion = float(tasa_str)

                factura_total = float(factura_total_str)
                monto_convertido_rd = factura_total * tasa_conversion
                
                success = agregar_factura_emitida(
                    self.current_filepath, self.fecha_emitida_cal.get_date().strftime('%Y-%m-%d'),
                    self.no_fact_entry.get(), self.tipo_factura_cb.get(), moneda,
                    self.rnc_entry.get(), self.empresa_emitida_entry.get(),
                    float(self.itbis_emitida_entry.get()), factura_total,
                    tasa_conversion, monto_convertido_rd
                )

            elif invoice_type == "gasto":
                moneda = self.moneda_gasto_cb.get()
                factura_total_str = self.factura_total_gasto_entry.get()

                if moneda != "RD$":
                    tasa_str = simpledialog.askstring("Tasa de Cambio", f"Introduce la tasa de cambio para {moneda} a RD$:", parent=parent_window)
                    if not tasa_str: return
                    tasa_conversion = float(tasa_str)
                
                factura_total = float(factura_total_str)
                monto_convertido_rd = factura_total * tasa_conversion
                
                success = agregar_factura_gasto(
                    self.current_filepath, self.fecha_gasto_cal.get_date().strftime('%Y-%m-%d'),
                    self.no_fact_gasto_entry.get(), self.rnc_gasto_entry.get(),
                    self.lugar_compra_entry.get(), moneda,
                    float(self.itbis_gasto_entry.get()), factura_total,
                    tasa_conversion, monto_convertido_rd
                )
            else:
                return

            if success:
                parent_window.destroy()
                self._update_main_dashboard()
                self._populate_invoice_filter_list()

        except (ValueError, TypeError):
            messagebox.showerror("Error de Datos", "ITBIS, Factura Total y Tasa deben ser números válidos.", parent=parent_window)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}", parent=parent_window)    
   
    def _add_new_currency_dialog(self, combobox_widget):
        new_currency = simpledialog.askstring("Añadir Nueva Moneda", "Introduce la nueva moneda (ej. 'EUR'):", parent=self.master)
        if new_currency and new_currency.strip().upper():
            if add_new_currency_to_file(self.current_filepath, new_currency.strip().upper()):
                combobox_widget['values'] = get_available_currencies(self.current_filepath)
                combobox_widget.set(new_currency.strip().upper())
            else: messagebox.showinfo("Información", f"La moneda '{new_currency}' ya existe o no se pudo añadir.")
    
    def _lookup_rnc_emitida(self):
        rnc = self.rnc_entry.get().strip()
        if not rnc:
            messagebox.showwarning("Advertencia", "Por favor, introduce un RNC para buscar.")
            return

        datos_empresa = cargar_datos_empresa(self.nombre_empresa_actual)
        empresa_asociada = datos_empresa["rnc_directory"].get(rnc)

        self.empresa_emitida_entry.delete(0, tk.END)
        if empresa_asociada:
            self.empresa_emitida_entry.insert(0, empresa_asociada)
            messagebox.showinfo("RNC Encontrado", f"RNC '{rnc}' asociado a: {empresa_asociada}")
            self.btn_asociar_rnc.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("RNC No Encontrado", f"RNC '{rnc}' no encontrado en el directorio. Por favor, ingresa el nombre de la empresa y asócialo.")
            self.btn_asociar_rnc.config(state=tk.NORMAL)

    def _associate_rnc_company_emitida(self):
        rnc = self.rnc_entry.get().strip()
        empresa_nombre = self.empresa_emitida_entry.get().strip()

        if not rnc or not empresa_nombre:
            messagebox.showwarning("Campos Vacíos", "Por favor, introduce tanto el RNC como el nombre de la empresa para asociar.")
            return
        
        if actualizar_directorio_rnc(self.nombre_empresa_actual, rnc, empresa_nombre):
            messagebox.showinfo("Asociación Exitosa", f"RNC '{rnc}' asociado a '{empresa_nombre}' exitosamente.")
            self.btn_asociar_rnc.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Error de Asociación", "No se pudo asociar el RNC con la empresa.")


    def open_add_emitida_window(self):
        if not self.nombre_empresa_actual:
            messagebox.showwarning("Advertencia", "Por favor, selecciona o crea una empresa primero.")
            return

        add_emitida_window = tk.Toplevel(self.master)
        add_emitida_window.title(f"Registrar Factura Emitida para {self.nombre_empresa_actual.upper()}")
        add_emitida_window.geometry("550x450")
        add_emitida_window.grab_set()

        form_frame = tk.LabelFrame(add_emitida_window, text="Datos de Factura Emitida", padx=10, pady=10)
        form_frame.pack(padx=15, pady=15, fill="both", expand=True)

        row_idx = 0

        tk.Label(form_frame, text="Fecha:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.fecha_emitida_cal = DateEntry(form_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2, year=datetime.date.today().year,
                                           month=datetime.date.today().month, day=datetime.date.today().day,
                                           date_pattern='yyyy-mm-dd')
        self.fecha_emitida_cal.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="Tipo de Factura:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.tipo_factura_cb = ttk.Combobox(form_frame, width=32,
                                            values=["Factura Privada", "Factura Gubernamental", "Factura Excenta", "Factura de Consumo"])
        self.tipo_factura_cb.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        self.tipo_factura_cb.set("Factura Privada")
        row_idx += 1

        tk.Label(form_frame, text="Número de Factura:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.no_fact_entry = tk.Entry(form_frame, width=35)
        self.no_fact_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        tk.Label(form_frame, text="Moneda:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.moneda_emitida_cb = ttk.Combobox(form_frame, width=25,
                                               values=get_available_currencies(self.nombre_empresa_actual))
        self.moneda_emitida_cb.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        if "RD$" in get_available_currencies(self.nombre_empresa_actual):
             self.moneda_emitida_cb.set("RD$")
        else:
             self.moneda_emitida_cb.set(get_available_currencies(self.nombre_empresa_actual)[0] if get_available_currencies(self.nombre_empresa_actual) else "")

        tk.Button(form_frame, text="+", width=3, command=lambda: self._add_new_currency_dialog(self.moneda_emitida_cb)).grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="RNC:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.rnc_entry = tk.Entry(form_frame, width=25)
        self.rnc_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        
        self.btn_buscar_rnc = tk.Button(form_frame, text="Buscar", width=6, command=self._lookup_rnc_emitida)
        self.btn_buscar_rnc.grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="Empresa a la que se emitió:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.empresa_emitida_entry = tk.Entry(form_frame, width=35)
        self.empresa_emitida_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        
        self.btn_asociar_rnc = tk.Button(form_frame, text="Asociar RNC", width=12, command=self._associate_rnc_company_emitida)
        self.btn_asociar_rnc.grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        self.btn_asociar_rnc.config(state=tk.DISABLED)
        row_idx += 1

        tk.Label(form_frame, text="ITBIS:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.itbis_emitida_entry = tk.Entry(form_frame, width=35)
        self.itbis_emitida_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        tk.Label(form_frame, text="Factura Total:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.factura_total_emitida_entry = tk.Entry(form_frame, width=35)
        self.factura_total_emitida_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        tk.Button(form_frame, text="Guardar Factura Emitida",
                command=lambda: self._save_invoice_data(add_emitida_window, "emitida")
                ).grid(row=row_idx, column=0, columnspan=3, pady=15)
        
    def _lookup_rnc_gasto(self):
        rnc = self.rnc_gasto_entry.get().strip()
        if not rnc:
            messagebox.showwarning("Advertencia", "Por favor, introduce un RNC para buscar.")
            return

        datos_empresa = cargar_datos_empresa(self.nombre_empresa_actual)
        empresa_asociada = datos_empresa["rnc_directory"].get(rnc)

        self.lugar_compra_entry.delete(0, tk.END)
        if empresa_asociada:
            self.lugar_compra_entry.insert(0, empresa_asociada)
            messagebox.showinfo("RNC Encontrado", f"RNC '{rnc}' asociado a: {empresa_asociada}")
            self.btn_asociar_rnc_gasto.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("RNC No Encontrado", f"RNC '{rnc}' no encontrado en el directorio. Por favor, ingresa el nombre de la empresa y asócialo.")
            self.btn_asociar_rnc_gasto.config(state=tk.NORMAL)

    def _associate_rnc_company_gasto(self):
        rnc = self.rnc_gasto_entry.get().strip()
        empresa_nombre = self.lugar_compra_entry.get().strip()

        if not rnc or not empresa_nombre:
            messagebox.showwarning("Campos Vacíos", "Por favor, introduce tanto el RNC como el nombre de la empresa para asociar.")
            return
        
        if actualizar_directorio_rnc(self.nombre_empresa_actual, rnc, empresa_nombre):
            messagebox.showinfo("Asociación Exitosa", f"RNC '{rnc}' asociado a '{empresa_nombre}' exitosamente.")
            self.btn_asociar_rnc_gasto.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Error de Asociación", "No se pudo asociar el RNC con la empresa.")


    def open_add_gasto_window(self):
        if not self.nombre_empresa_actual:
            messagebox.showwarning("Advertencia", "Por favor, selecciona o crea una empresa primero.")
            return

        add_gasto_window = tk.Toplevel(self.master)
        add_gasto_window.title(f"Registrar Factura de Gasto para {self.nombre_empresa_actual.upper()}")
        add_gasto_window.geometry("550x450")
        add_gasto_window.grab_set()

        form_frame = tk.LabelFrame(add_gasto_window, text="Datos de Factura de Gasto", padx=10, pady=10)
        form_frame.pack(padx=15, pady=15, fill="both", expand=True)

        row_idx = 0

        tk.Label(form_frame, text="Fecha:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.fecha_gasto_cal = DateEntry(form_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2, year=datetime.date.today().year,
                                           month=datetime.date.today().month, day=datetime.date.today().day,
                                           date_pattern='yyyy-mm-dd')
        self.fecha_gasto_cal.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="Número de Factura:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.no_fact_gasto_entry = tk.Entry(form_frame, width=35)
        self.no_fact_gasto_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1
        
        tk.Label(form_frame, text="RNC:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.rnc_gasto_entry = tk.Entry(form_frame, width=25)
        self.rnc_gasto_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        
        self.btn_buscar_rnc_gasto = tk.Button(form_frame, text="Buscar", width=6, command=self._lookup_rnc_gasto)
        self.btn_buscar_rnc_gasto.grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="Lugar de Compra/Empresa:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.lugar_compra_entry = tk.Entry(form_frame, width=35)
        self.lugar_compra_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        
        self.btn_asociar_rnc_gasto = tk.Button(form_frame, text="Asociar RNC", width=12, command=self._associate_rnc_company_gasto)
        self.btn_asociar_rnc_gasto.config(state=tk.DISABLED)
        self.btn_asociar_rnc_gasto.grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="Moneda:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.moneda_gasto_cb = ttk.Combobox(form_frame, width=25,
                                               values=get_available_currencies(self.nombre_empresa_actual))
        self.moneda_gasto_cb.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        if "RD$" in get_available_currencies(self.nombre_empresa_actual):
             self.moneda_gasto_cb.set("RD$")
        else:
             self.moneda_gasto_cb.set(get_available_currencies(self.nombre_empresa_actual)[0] if get_available_currencies(self.nombre_empresa_actual) else "")

        tk.Button(form_frame, text="+", width=3, command=lambda: self._add_new_currency_dialog(self.moneda_gasto_cb)).grid(row=row_idx, column=2, padx=2, pady=5, sticky="w")
        row_idx += 1

        tk.Label(form_frame, text="ITBIS:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.itbis_gasto_entry = tk.Entry(form_frame, width=35)
        self.itbis_gasto_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        tk.Label(form_frame, text="Factura Total:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        self.factura_total_gasto_entry = tk.Entry(form_frame, width=35)
        self.factura_total_gasto_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        tk.Button(form_frame, text="Guardar Factura de Gasto",
                command=lambda: self._save_invoice_data(add_gasto_window, "gasto")
                ).grid(row=row_idx, column=0, columnspan=3, pady=15)    
    def open_reporte_window(self):
        if not self.nombre_empresa_actual:
            messagebox.showwarning("Advertencia", "Por favor, selecciona o crea una empresa primero.")
            return

        reporte_window = tk.Toplevel(self.master)
        reporte_window.title(f"Reporte Mensual para {self.nombre_empresa_actual.upper()}")
        reporte_window.geometry("850x600")
        reporte_window.grab_set()

        input_frame = tk.LabelFrame(reporte_window, text="Seleccionar Mes y Año", padx=10, pady=10)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Mes (1-12):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.mes_reporte_entry = tk.Entry(input_frame, width=10)
        self.mes_reporte_entry.grid(row=0, column=1, padx=5, pady=5)
        self.mes_reporte_entry.insert(0, str(datetime.date.today().month))

        tk.Label(input_frame, text="Año (YYYY):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.anio_reporte_entry = tk.Entry(input_frame, width=10)
        self.anio_reporte_entry.grid(row=0, column=3, padx=5, pady=5)
        self.anio_reporte_entry.insert(0, str(datetime.date.today().year))

# Reemplaza los botones en input_frame con esto para un mejor orden
        tk.Button(input_frame, text="Generar Reporte", command=lambda: self._generate_and_display_report_window(reporte_window)).grid(row=0, column=4, padx=10, pady=5)
        tk.Button(input_frame, text="Exportar a PDF", command=self._export_report_to_pdf).grid(row=1, column=4, padx=10, pady=5, sticky="ew")
        tk.Button(input_frame, text="Exportar a Excel", command=self._export_report_to_excel, bg="lightgreen").grid(row=1, column=5, padx=10, pady=5, sticky="ew")
        tk.Button(input_frame, text="Reporte por Imputación", command=lambda: self._generate_imputacion_report_window(reporte_window)).grid(row=0, column=5, padx=10, pady=5)

        self.report_text_area = scrolledtext.ScrolledText(reporte_window, wrap=tk.WORD, width=100, height=25, font=("Consolas", 10))
        self.report_text_area.pack(padx=10, pady=10, fill="both", expand=True)
        self.report_text_area.config(state=tk.DISABLED)

        self._generate_and_display_report_window(reporte_window)

    def _generate_and_display_report_window(self, parent_window):
        mes_str = self.mes_reporte_entry.get()
        anio_str = self.anio_reporte_entry.get()

        try:
            mes = int(mes_str)
            anio = int(anio_str)
            if not (1 <= mes <= 12 and 1900 < anio <= datetime.datetime.now().year + 5):
                raise ValueError("Mes o año inválidos.")
        except ValueError:
            messagebox.showerror("Error de Entrada", "Por favor, introduce un mes (1-12) y un año (YYYY) válidos.", parent=parent_window)
            return

        report_output = generar_reporte_mensual(self.current_filepath, self.nombre_empresa_actual, mes, anio)
        self.current_report_content_text = report_output["text_report"]
        self.last_report_data = report_output["data"]

        self.report_text_area.config(state=tk.NORMAL)
        self.report_text_area.delete(1.0, tk.END)
        self.report_text_area.insert(tk.END, self.current_report_content_text)
        self.report_text_area.config(state=tk.DISABLED)

    def _generate_imputacion_report_window(self, parent_window):
        mes_str = self.mes_reporte_entry.get()
        anio_str = self.anio_reporte_entry.get()

        try:
            mes = int(mes_str)
            anio = int(anio_str)
            if not (1 <= mes <= 12 and 1900 < anio <= datetime.datetime.now().year + 5):
                raise ValueError("Mes o año inválidos.")
        except ValueError:
            messagebox.showerror("Error de Entrada", "Por favor, introduce un mes (1-12) y un año (YYYY) válidos.", parent=parent_window)
            return

        report_output = generar_reporte_por_imputacion(self.current_filepath, self.nombre_empresa_actual, mes, anio)
        self.current_report_content_text = report_output["text_report"]
        self.last_report_data = report_output["data"]

        self.report_text_area.config(state=tk.NORMAL)
        self.report_text_area.delete(1.0, tk.END)
        self.report_text_area.insert(tk.END, self.current_report_content_text)
        self.report_text_area.config(state=tk.DISABLED)


    def _export_report_to_pdf(self):
        if not self.last_report_data:
            messagebox.showwarning("Advertencia", "Primero genera un reporte para poder exportar a PDF.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            title="Guardar Reporte como PDF",
            initialfile=f"Reporte_{self.nombre_empresa_actual.replace(' ', '_')}_{self.last_report_data['month']}_{self.last_report_data['year']}.pdf"
        )

        if file_path:
            try:
                pdf = PDF(company_name=self.last_report_data['company_name'],
                        report_title="Reporte Mensual",
                        report_period=f"{self.last_report_data['month']}/{self.last_report_data['year']}")
                pdf.alias_nb_pages()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                # --- Resumen General (esto ya estaba correcto) ---
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Resumen General del Reporte (en RD$)', 0, 1, 'C')
                pdf.ln(5)

                pdf.set_font('Arial', '', 11)
                pdf.cell(95, 8, f'Total Ingresos: ${self.last_report_data["totals"]["total_factura_emitidas"]:,.2f}', 0, 0, 'L')
                pdf.cell(95, 8, f'ITBIS Ingresos: ${self.last_report_data["totals"]["total_itbis_emitidas"]:,.2f}', 0, 1, 'L')

                pdf.cell(95, 8, f'Total Gastos: ${self.last_report_data["totals"]["total_factura_gastos"]:,.2f}', 0, 0, 'L')
                pdf.cell(95, 8, f'ITBIS Gastos: ${self.last_report_data["totals"]["total_itbis_gastos"]:,.2f}', 0, 1, 'L')
                pdf.ln(2)

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(95, 8, f'ITBIS Neto: ${self.last_report_data["totals"]["itbis_neto"]:,.2f}', 0, 0, 'L')
                pdf.cell(95, 8, f'Total Neto: ${self.last_report_data["totals"]["total_neto"]:,.2f}', 0, 1, 'L')
                pdf.ln(10)
                
                # <<< INICIO DE CAMBIOS EN TABLA DE FACTURAS EMITIDAS >>>
                col_widths_emitidas = [20, 15, 25, 55, 25, 25, 25]
                col_headers_emitidas = ["Fecha", "Tipo", "No. Fact.", "Empresa", "RNC", "Total Orig.", "Total (RD$)"]
                
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Facturas Emitidas (Ingresos)', 0, 1, 'L')
                pdf.set_font('Arial', 'B', 9)
                for i, header in enumerate(col_headers_emitidas):
                    pdf.cell(col_widths_emitidas[i], 7, header, 1, 0, 'C')
                pdf.ln()

                pdf.set_font('Arial', '', 8)
                for invoice in self.last_report_data["emitted_invoices"]:
                    monto_orig_str = f"{float(invoice.get('factura_total', 0.0)):,.2f} {invoice.get('moneda', '')}"
                    monto_rd = float(invoice.get('monto_convertido_rd', invoice.get('factura_total', 0.0)))
                    
                    pdf.cell(col_widths_emitidas[0], 6, invoice.get('fecha', ''), 1, 0, 'L')
                    pdf.cell(col_widths_emitidas[1], 6, invoice.get('tipo_factura', '')[0:9], 1, 0, 'L')
                    pdf.cell(col_widths_emitidas[2], 6, invoice.get('no_fact', ''), 1, 0, 'L')
                    pdf.cell(col_widths_emitidas[3], 6, invoice.get('empresa', '')[0:39], 1, 0, 'L')
                    pdf.cell(col_widths_emitidas[4], 6, invoice.get('rnc', ''), 1, 0, 'L')
                    pdf.cell(col_widths_emitidas[5], 6, monto_orig_str, 1, 0, 'R')
                    pdf.cell(col_widths_emitidas[6], 6, f"{monto_rd:,.2f}", 1, 1, 'R')
                pdf.ln(10)
                # <<< FIN DE CAMBIOS EN TABLA DE FACTURAS EMITIDAS >>>

                # <<< INICIO DE CAMBIOS EN TABLA DE FACTURAS DE GASTOS >>>
                col_widths_gastos = [20, 25, 25, 60, 25, 25]
                col_headers_gastos = ["Fecha", "No. Fact.", "RNC", "Empresa", "Total Orig.", "Total (RD$)"]

                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Facturas de Gastos', 0, 1, 'L')
                pdf.set_font('Arial', 'B', 9)
                for i, header in enumerate(col_headers_gastos):
                    pdf.cell(col_widths_gastos[i], 7, header, 1, 0, 'C')
                pdf.ln()

                pdf.set_font('Arial', '', 8)
                for invoice in self.last_report_data["expense_invoices"]:
                    monto_orig_str = f"{float(invoice.get('factura_total', 0.0)):,.2f} {invoice.get('moneda', '')}"
                    monto_rd = float(invoice.get('monto_convertido_rd', invoice.get('factura_total', 0.0)))

                    pdf.cell(col_widths_gastos[0], 6, invoice.get('fecha', ''), 1, 0, 'L')
                    pdf.cell(col_widths_gastos[1], 6, invoice.get('no_fact', ''), 1, 0, 'L')
                    pdf.cell(col_widths_gastos[2], 6, invoice.get('rnc', ''), 1, 0, 'L')
                    pdf.cell(col_widths_gastos[3], 6, invoice.get('lugar_compra', '')[0:39], 1, 0, 'L')
                    pdf.cell(col_widths_gastos[4], 6, monto_orig_str, 1, 0, 'R')
                    pdf.cell(col_widths_gastos[5], 6, f"{monto_rd:,.2f}", 1, 1, 'R')
                pdf.ln(10)
                # <<< FIN DE CAMBIOS EN TABLA DE FACTURAS DE GASTOS >>>

                pdf.output(file_path)
                messagebox.showinfo("Éxito", f"Reporte exportado a PDF exitosamente en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error de Exportación", f"No se pudo exportar el reporte a PDF: {e}")


    def _export_report_to_excel(self):
        """
        Exporta los datos del último reporte generado a un archivo Excel (.xlsx)
        con tres hojas: Resumen, Ingresos y Gastos.
        """
        if not self.last_report_data:
            messagebox.showwarning("Advertencia", "Primero debes generar un reporte para poder exportar a Excel.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            title="Guardar Reporte como Excel",
            initialfile=f"Reporte_{self.nombre_empresa_actual.replace(' ', '_')}_{self.last_report_data['month']}_{self.last_report_data['year']}.xlsx"
        )

        if not file_path:
            return

        try:
            # Preparamos los datos del resumen
            summary_totals = self.last_report_data["totals"]
            resumen_data = {
                "Descripción": [
                    "Total Ingresos (RD$)", "Total ITBIS Ingresos (RD$)",
                    "Total Gastos (RD$)", "Total ITBIS Gastos (RD$)",
                    "ITBIS Neto (RD$)", "Total Neto (RD$)"
                ],
                "Monto": [
                    summary_totals["total_factura_emitidas"], summary_totals["total_itbis_emitidas"],
                    summary_totals["total_factura_gastos"], summary_totals["total_itbis_gastos"],
                    summary_totals["itbis_neto"], summary_totals["total_neto"]
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)

            # Preparamos los datos de Ingresos
            df_ingresos = pd.DataFrame(self.last_report_data["emitted_invoices"])
            # Seleccionamos y renombramos las columnas para un reporte limpio
            df_ingresos_report = df_ingresos[[
                "fecha", "tipo_factura", "no_fact", "empresa", "rnc", 
                "moneda", "factura_total", "monto_convertido_rd"
            ]].rename(columns={
                "fecha": "Fecha", "tipo_factura": "Tipo Factura", "no_fact": "No. Factura",
                "empresa": "Empresa", "rnc": "RNC", "moneda": "Moneda",
                "factura_total": "Total Original", "monto_convertido_rd": "Total (RD$)"
            })
            
            # Preparamos los datos de Gastos
            df_gastos = pd.DataFrame(self.last_report_data["expense_invoices"])
            # Seleccionamos y renombramos las columnas
            df_gastos_report = df_gastos[[
                "fecha", "no_fact", "lugar_compra", "rnc", "moneda", 
                "factura_total", "monto_convertido_rd"
            ]].rename(columns={
                "fecha": "Fecha", "no_fact": "No. Factura", "lugar_compra": "Empresa",
                "rnc": "RNC", "moneda": "Moneda", "factura_total": "Total Original",
                "monto_convertido_rd": "Total (RD$)"
            })

            # Escribimos los datos en un archivo Excel con múltiples hojas
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                df_ingresos_report.to_excel(writer, sheet_name='Ingresos', index=False)
                df_gastos_report.to_excel(writer, sheet_name='Gastos', index=False)

            messagebox.showinfo("Éxito", f"Reporte de Excel guardado exitosamente en:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo exportar el reporte a Excel: {e}")

    def open_manage_transactions_window(self):
        if not self.current_filepath:
            messagebox.showwarning("Advertencia", "Selecciona una empresa primero.")
            return

        datos = cargar_datos_empresa(self.current_filepath)
        
        todas = [("emitida", f) for f in datos.get("facturas_emitidas", [])] + \
                [("gasto", f) for f in datos.get("facturas_gastos", [])]
        
        todas.sort(key=lambda x: x[1].get('fecha', ''), reverse=True)

        win = tk.Toplevel(self.master)
        win.title("Modificar / Eliminar Transacciones")
        win.geometry("950x500")
        win.grab_set()

        lista = tk.Listbox(win, width=130, height=20, font=("Consolas", 9))
        lista.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        header = f"{'Fecha':<12} {'Tipo':<8} {'No. Fact.':<15} {'Empresa':<30} {'Moneda':<8} {'Monto Original':>15} {'Total (RD$)':>15}"
        lista.insert(tk.END, header)
        lista.insert(tk.END, "-" * 130)

        for idx, (tipo, f) in enumerate(todas):
            monto_original = float(f.get('factura_total', 0.0))
            monto_convertido = float(f.get('monto_convertido_rd', monto_original))
            
            texto = f"{f.get('fecha', ''):<12} {tipo.upper():<8} {f.get('no_fact', ''):<15} " \
                    f"{f.get('empresa', f.get('lugar_compra', ''))[0:29]:<30} " \
                    f"{f.get('moneda', 'RD$'):<8} {monto_original:>15,.2f} {monto_convertido:>15,.2f}"
            lista.insert(tk.END, texto)

        def eliminar_sel():
            seleccion = lista.curselection()
            if not seleccion or seleccion[0] < 2:
                messagebox.showwarning("Selecciona una transacción", "Debes seleccionar una transacción válida para eliminar.")
                return
            
            idx = seleccion[0] - 2
            tipo, trans = todas[idx]
            
            if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que deseas eliminar la transacción '{trans.get('no_fact')}'?"):
                if eliminar_factura(self.current_filepath, tipo, trans.get("no_fact")):
                    messagebox.showinfo("Eliminado", "Transacción eliminada correctamente.")
                    win.destroy()
                    self._update_main_dashboard()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar.")

        def modificar_sel():
            seleccion = lista.curselection()
            if not seleccion or seleccion[0] < 2:
                messagebox.showwarning("Selecciona una transacción", "Debes seleccionar una transacción válida para modificar.")
                return
            
            idx = seleccion[0] - 2
            tipo, trans_original = todas[idx]

            form_win = tk.Toplevel(win)
            form_win.title("Modificar Transacción")
            form_win.geometry("500x600")
            form_win.grab_set()

            entries = {}
            campos = [("fecha", "Fecha"), ("no_fact", "No. Factura")]
            if tipo == "emitida":
                campos.extend([("tipo_factura", "Tipo de Factura"), ("empresa", "Empresa Emitida")])
            else:
                campos.extend([("lugar_compra", "Empresa")])
                
            campos.extend([("rnc", "RNC"), ("moneda", "Moneda"), ("itbis", "ITBIS"), ("factura_total", "Total Original")])
            
            for idx_f, (clave, texto) in enumerate(campos):
                tk.Label(form_win, text=texto + ":").grid(row=idx_f, column=0, sticky="w", padx=10, pady=5)
                entry = tk.Entry(form_win, width=40)
                entry.grid(row=idx_f, column=1, padx=10, pady=5)
                entry.insert(0, str(trans_original.get(clave, "")))
                entries[clave] = entry

            def guardar_modificacion():
                nueva_data = {clave: entry.get().strip() for clave, entry in entries.items()}
                
                moneda = nueva_data.get("moneda", "RD$")
                total_original = float(nueva_data.get("factura_total", 0.0))
                
                if moneda != "RD$":
                    tasa_str = simpledialog.askstring("Tasa de Cambio", f"Introduce la nueva tasa de cambio para {moneda} a RD$:", parent=form_win)
                    tasa = float(tasa_str) if tasa_str else 1.0
                else:
                    tasa = 1.0

                nueva_data["tasa_conversion"] = tasa
                nueva_data["monto_convertido_rd"] = total_original * tasa
                nueva_data["itbis"] = float(nueva_data.get("itbis", 0.0))
                nueva_data["factura_total"] = total_original

                if modificar_factura(self.current_filepath, tipo, trans_original["no_fact"], nueva_data):
                    messagebox.showinfo("Éxito", "Transacción modificada correctamente.")
                    form_win.destroy()
                    win.destroy()
                    self._update_main_dashboard()
                else:
                    messagebox.showerror("Error", "No se pudo modificar la transacción.")

            tk.Button(form_win, text="Guardar Cambios", command=guardar_modificacion, bg="lightgreen").grid(
                row=len(campos), column=0, columnspan=2, pady=20)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Eliminar Seleccionada", bg="tomato", command=eliminar_sel).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Modificar Seleccionada", bg="lightblue", command=modificar_sel).pack(side=tk.LEFT, padx=10)

# =========================================================================
# Bloque principal para ejecutar la aplicación
# =========================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = AppFacturas(root)
    app._update_main_dashboard()
    root.mainloop()