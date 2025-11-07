import os
import io
import glob
import shutil
import tempfile
import logging

import pandas as pd
from fpdf import FPDF
from PIL import Image
from pypdf import PdfWriter, PdfReader

# Logger config (the application may already configure logging; this is a sensible default)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class PDF(FPDF):
    """Clase heredada de FPDF para crear encabezados y pies de página personalizados."""
    def __init__(self, orientation='P', unit='mm', format='A4', company_name="", report_title="", report_period=""):
        super().__init__(orientation, unit, format)
        self.company_name = company_name
        self.report_title = report_title
        self.report_period = report_period
        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.set_font('Arial', 'I', 11)
        self.cell(0, 8, f'Empresa: {self.company_name}', 0, 1, 'C')
        self.cell(0, 6, f'Período: {self.report_period}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')


def generate_professional_pdf(report_data, save_path, company_name, month, year, attachment_base_path=None):
    """
    Genera un PDF profesional con el resumen y las tablas del reporte mensual.
    - Ahora soporta anexar archivos referenciados por cada factura (emitidas y gastos).
    - Intenta resolver rutas absolutas, relativas a attachment_base_path, al proyecto y al cwd.
    """
    temp_files = []

    def find_attachment_fullpath(base_path, relative_path, invoice):
        # Primero, acepta rutas ya resueltas proporcionadas por la UI (attachment_resolved)
        try:
            if invoice and invoice.get("attachment_resolved"):
                ar = invoice.get("attachment_resolved")
                if ar and os.path.exists(ar):
                    return ar
        except Exception:
            pass

        # luego, tratar relative_path
        if not relative_path:
            return None
        rel = str(relative_path).strip()
        if not rel:
            return None

        # if absolute path and exists, return it
        if os.path.isabs(rel) and os.path.exists(rel):
            return rel

        candidates = []
        # If base_path provided, try common joins
        if base_path:
            candidates.append(os.path.join(base_path, rel))
            candidates.append(os.path.join(base_path, os.path.basename(rel)))

        # try invoice-level structure: company or id folders
        try:
            comp = invoice.get("company_id") or invoice.get("company")
            if comp and base_path:
                candidates.append(os.path.join(base_path, str(comp), rel))
                candidates.append(os.path.join(base_path, str(comp), os.path.basename(rel)))
        except Exception:
            pass

        # try date-based folders if invoice has date
        try:
            inv_date = invoice.get("invoice_date") or invoice.get("fecha") or ""
            if inv_date:
                ds = str(inv_date)
                if "-" in ds:
                    parts = ds.split("-")
                elif "/" in ds:
                    parts = ds.split("/")
                else:
                    parts = []
                if len(parts) >= 2 and base_path:
                    y, m = parts[0], parts[1]
                    candidates.append(os.path.join(base_path, y, m, rel))
                    candidates.append(os.path.join(base_path, y, m, os.path.basename(rel)))
        except Exception:
            pass

        # try invoice number/id folders
        try:
            invnum = invoice.get("invoice_number") or invoice.get("no") or ""
            inv_id = invoice.get("id")
            if base_path:
                if invnum:
                    candidates.append(os.path.join(base_path, str(invnum), rel))
                    candidates.append(os.path.join(base_path, str(invnum), os.path.basename(rel)))
                if inv_id:
                    candidates.append(os.path.join(base_path, str(inv_id), rel))
                    candidates.append(os.path.join(base_path, str(inv_id), os.path.basename(rel)))
        except Exception:
            pass

        # Project relative and cwd
        try:
            proj_candidate = os.path.join(os.path.dirname(__file__), rel)
            candidates.append(proj_candidate)
            proj_candidate2 = os.path.join(os.getcwd(), rel)
            candidates.append(proj_candidate2)
            candidates.append(os.path.join(os.getcwd(), os.path.basename(rel)))
        except Exception:
            pass

        # Check candidates
        for c in candidates:
            try:
                if c and os.path.exists(c):
                    return c
            except Exception:
                continue

        # glob search under base_path for basename
        try:
            if base_path:
                pattern = os.path.join(base_path, "**", os.path.basename(rel))
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    return matches[0]
        except Exception:
            pass

        return None

    try:
        # Temp file for main report
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_report:
            temp_report_path = temp_report.name
            temp_files.append(temp_report_path)

        pdf_report = PDF(orientation='L', company_name=company_name,
                         report_title="Reporte Mensual de Facturación",
                         report_period=f"{month}/{year}")
        pdf_report.add_page()

        # -------------------------
        # Nuevo bloque: Resumen (no desborda)
        # -------------------------
        HEADER_BG_COLOR = (220, 220, 220)
        ROW_BG_COLOR_ALT = (245, 245, 245)

        pdf_report.set_font('Arial', 'B', 12)
        pdf_report.cell(0, 10, 'Resumen General del Mes (en RD$)', 0, 1, 'L')
        pdf_report.ln(2)

        # valores defensivos
        summary = report_data.get('summary', {}) if report_data else {}

        # calcular anchos en la página (respetando margenes)
        page_width = pdf_report.w - 2 * pdf_report.l_margin
        label_col = page_width * 0.60
        value_col = page_width - label_col  # 40%

        # usar fuente un poco más pequeña para el bloque de resumen
        pdf_report.set_font('Arial', '', 9)
        # lista de pares a mostrar (etiqueta, key en summary)
        pairs = [
            ("Total Ingresos:", "total_ingresos"),
            ("Total Gastos:", "total_gastos"),
            ("Total Neto:", "total_neto"),
            ("ITBIS Ingresos:", "itbis_ingresos"),
            ("ITBIS Gastos:", "itbis_gastos"),
            ("ITBIS Neto:", "itbis_neto"),
        ]

        for label, key in pairs:
            val = summary.get(key, 0.0)
            # etiqueta
            pdf_report.cell(label_col, 6, label, border=0, ln=0)
            # valor alineado a la derecha dentro del value_col
            pdf_report.cell(value_col, 6, f"RD$ {val:,.2f}", border=0, ln=1, align='R')

        # separador
        pdf_report.ln(3)
        pdf_report.set_draw_color(0, 0, 0)
        pdf_report.set_line_width(0.3)
        pdf_report.line(pdf_report.l_margin, pdf_report.get_y(), pdf_report.w - pdf_report.r_margin, pdf_report.get_y())
        pdf_report.ln(6)

        # -------------------------
        # Dibujar tablas (igual que antes)
        # -------------------------
        def draw_table(title, headers, data, column_widths_percent):
            pdf_report.set_font('Arial', 'B', 12)
            pdf_report.cell(0, 10, title, 0, 1, 'L')
            pdf_report.set_font('Arial', 'B', 9)
            pdf_report.set_fill_color(*HEADER_BG_COLOR)
            page_width_inner = pdf_report.w - 2 * pdf_report.l_margin
            column_widths = [(w / 100.0) * page_width_inner for w in column_widths_percent]
            for i, header in enumerate(headers):
                pdf_report.cell(column_widths[i], 8, header, 1, 0, 'C', 1)
            pdf_report.ln()
            pdf_report.set_font('Arial', '', 8)
            fill = False
            for row in data:
                try:
                    pdf_report.set_fill_color(*ROW_BG_COLOR_ALT) if fill else pdf_report.set_fill_color(255, 255, 255)
                    for i, datum in enumerate(row):
                        pdf_report.cell(column_widths[i], 6, str(datum), 1, 0, 'L' if i < 3 else 'R', 1)
                    pdf_report.ln()
                    fill = not fill
                except Exception:
                    continue

        # Normalize helpers (como antes)
        def _safe_list_of_dicts(lst):
            normalized = []
            for r in lst or []:
                try:
                    normalized.append(dict(r))
                except Exception:
                    if isinstance(r, dict):
                        normalized.append(r)
                    else:
                        try:
                            normalized.append({k: r[k] for k in r.keys()})
                        except Exception:
                            normalized.append(r)
            return normalized

        emitted_invoices = _safe_list_of_dicts(report_data.get('emitted_invoices', []))
        expense_invoices = _safe_list_of_dicts(report_data.get('expense_invoices', []))

        headers_emitted = ['Fecha', 'No. Fact.', 'Empresa', 'ITBIS (RD$)', 'Total (RD$)']
        data_emitted = []
        for f in emitted_invoices:
            itbis = float(f.get('itbis', 0.0))
            rate = float(f.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(f.get('total_amount_rd') or (float(f.get('total_amount', 0.0)) * rate))
            data_emitted.append([f.get('invoice_date', ''), f.get('invoice_number', ''), f.get('third_party_name', ''), f"{itbis * rate:,.2f}", f"{total_rd:,.2f}"])
        draw_table('Facturas Emitidas (Ingresos)', headers_emitted, data_emitted, [15, 15, 45, 12.5, 12.5])
        pdf_report.ln(6)

        headers_expenses = ['Fecha', 'No. Fact.', 'Empresa', 'ITBIS (RD$)', 'Total (RD$)']
        data_expenses = []
        for f in expense_invoices:
            itbis = float(f.get('itbis', 0.0))
            rate = float(f.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(f.get('total_amount_rd') or (float(f.get('total_amount', 0.0)) * rate))
            data_expenses.append([f.get('invoice_date', ''), f.get('invoice_number', ''), f.get('third_party_name', ''), f"{itbis * rate:,.2f}", f"{total_rd:,.2f}"])
        draw_table('Facturas de Gastos', headers_expenses, data_expenses, [15, 15, 45, 12.5, 12.5])

        # write primary report to temp path
        pdf_report.output(temp_report_path)

        # Merge with attachments (mantén tu lógica actual de búsqueda/append)
        merger = PdfWriter()
        try:
            merger.append(temp_report_path)
        except Exception:
            logger.warning("No se pudo anexar el PDF principal al writer. Continuando con fallback.")
            pass

        # Build attachments list from both emitted and expense invoices, unless an explicit ordered list is provided
        attachments_candidates = []
        if report_data and report_data.get('ordered_attachments') is not None:
            attachments_candidates = report_data.get('ordered_attachments')
        else:
            # include attachments from both lists
            for f in emitted_invoices + expense_invoices:
                ap = f.get('attachment_resolved') or f.get('attachment_path') or f.get('attachment') or f.get('anexo')
                if ap:
                    # keep original invoice dict along with path for processing
                    new_inv = dict(f)
                    new_inv['attachment_path'] = ap
                    attachments_candidates.append(new_inv)

        # Process attachments; if attachment_base_path is None, find_attachment_fullpath will still try several locations
        if attachments_candidates:
            for invoice in attachments_candidates:
                try:
                    rel = invoice.get('attachment_path') or ''
                    full_path = find_attachment_fullpath(attachment_base_path, rel, invoice)
                    if not full_path:
                        logger.warning("Anexo no encontrado para factura %s -> '%s'", invoice.get('invoice_number'), rel)
                        continue

# PDF attachments: append directly
                    if full_path.lower().endswith('.pdf'):
                        try:
                            # [FIX] Usar PdfReader con strict=False para manejar PDFs problemáticos
                            reader = PdfReader(full_path, strict=False)
                            merger.append(reader)
                        except Exception as e:
                            logger.warning("No se pudo anexar PDF %s: %s", full_path, e)
                            continue

                    # Image attachments: convert to PDF and append
                    elif full_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_img:
                            temp_img_path = temp_img.name
                            temp_files.append(temp_img_path)
                        try:
                            pdf_img = PDF(orientation='P', company_name=company_name,
                                          report_title="Anexo de Comprobante",
                                          report_period=f"Factura: {invoice.get('invoice_number', '')}")
                            pdf_img.add_page()
                            y_position = pdf_img.get_y()
                            with Image.open(full_path) as img:
                                img_w, img_h = img.size
                                aspect_ratio = img_w / img_h if img_h != 0 else 1.0
                                printable_width = pdf_img.w - 2 * pdf_img.l_margin
                                display_w = printable_width
                                display_h = display_w / aspect_ratio
                                available_height = pdf_img.h - y_position - pdf_img.b_margin
                                if display_h > available_height:
                                    display_h = available_height
                                    display_w = display_h * aspect_ratio
                                # Use try/except because FPDF may fail with some image modes
                                try:
                                    pdf_img.image(full_path, x=pdf_img.l_margin, y=y_position, w=display_w, h=display_h)
                                except Exception:
                                    # fallback: convert image to RGB and save a temp PNG then embed
                                    tmp_img_path = None
                                    try:
                                        with Image.open(full_path) as imconv:
                                            rgb = imconv.convert('RGB')
                                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as t2:
                                                tmp_img_path = t2.name
                                                rgb.save(tmp_img_path, format="PNG")
                                        pdf_img.image(tmp_img_path, x=pdf_img.l_margin, y=y_position, w=display_w, h=display_h)
                                    finally:
                                        if tmp_img_path and os.path.exists(tmp_img_path):
                                            try:
                                                os.remove(tmp_img_path)
                                            except Exception:
                                                pass
                                pdf_img.output(temp_img_path)
                                try:
                                    # [FIX] Usar PdfReader con strict=False aquí también
                                    reader = PdfReader(temp_img_path, strict=False)
                                    merger.append(reader)
                                except Exception as e:
                                    logger.warning("No se pudo anexar PDF generado desde imagen %s: %s", temp_img_path, e)
                                    continue
                        except Exception as e:
                            logger.warning("Error al convertir imagen a PDF para %s: %s", full_path, e)
                            continue
                    else:
                        logger.warning("Tipo de archivo no soportado para anexo: %s", full_path)
                        continue
                except Exception as e:
                    logger.warning("Error procesando anexo para factura %s: %s", invoice.get('invoice_number'), e)
                    continue

        # write merged file
        try:
            with open(save_path, "wb") as f_out:
                merger.write(f_out)
        except Exception as e:
            try:
                shutil.copyfile(temp_report_path, save_path)
                logger.warning("Se uso fallback y se copió el reporte principal sin anexos: %s", e)
            except Exception as e2:
                return False, f"No se pudo escribir el PDF final: {e2}"

        return True, "Reporte PDF con anexos generado exitosamente."

    except Exception as e:
        logger.exception("Error generando professional PDF")
        return False, f"No se pudo generar el PDF: {e}"
    finally:
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass


def generate_excel_report(report_data, save_path):
    """Genera un reporte mensual en formato Excel."""
    try:
        summary_totals = report_data["summary"]
        resumen_data = {
            "Descripción": ["Total Ingresos (RD$)", "Total ITBIS Ingresos (RD$)", "Total Gastos (RD$)", "Total ITBIS Gastos (RD$)", "ITBIS Neto (RD$)", "Total Neto (RD$)"],
            "Monto": [summary_totals.get("total_ingresos", 0.0), summary_totals.get("itbis_ingresos", 0.0), summary_totals.get("total_gastos", 0.0), summary_totals.get("itbis_gastos", 0.0), summary_totals.get("itbis_neto", 0.0), summary_totals.get("total_neto", 0.0)]
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_ingresos = pd.DataFrame(report_data["emitted_invoices"])
        df_gastos = pd.DataFrame(report_data["expense_invoices"])

        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            df_ingresos.to_excel(writer, sheet_name='Ingresos', index=False)
            df_gastos.to_excel(writer, sheet_name='Gastos', index=False)

        return True, "Reporte Excel generado exitosamente."
    except Exception as e:
        return False, f"No se pudo generar el Excel: {e}"


def generate_retention_pdf(save_path, company_name, period_str, results_data, selected_invoices):
    """Genera un PDF profesional para el cálculo de retenciones."""
    try:
        pdf = PDF(orientation='P', company_name=company_name, report_title="Cálculo de Retenciones", report_period=period_str)
        pdf.add_page()

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Base del Cálculo ({results_data['num_invoices']} facturas seleccionadas)", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f"Total General Seleccionado: RD$ {results_data['total_general_rd']:,.2f}", 0, 1, 'L')
        pdf.cell(0, 7, f"Total ITBIS Seleccionado: RD$ {results_data['total_itbis_rd']:,.2f}", 0, 1, 'L')
        pdf.cell(0, 7, f"Total Subtotal Seleccionado: RD$ {results_data['total_subtotal_rd']:,.2f}", 0, 1, 'L')
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Resultados de Retenciones", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f"Retención del {results_data['p_itb']:.2f}% del ITBIS: RD$ {results_data['ret_itbis']:,.2f}", 0, 1, 'L')
        pdf.cell(0, 7, f"Retención del {results_data['p_tot']:.2f}% del Total: RD$ {results_data['ret_total']:,.2f}", 0, 1, 'L')
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 13)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(0, 10, f"TOTAL A RETENER: RD$ {results_data['total_a_retener']:,.2f}", border=1, ln=1, align='C', fill=True)
        pdf.ln(10)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Facturas Incluidas en el Cálculo", 0, 1, 'L')

        pdf.set_font('Arial', 'B', 9)
        pdf.cell(25, 7, "Fecha", 1, 0, 'C'); pdf.cell(40, 7, "No. Factura", 1, 0, 'C'); pdf.cell(85, 7, "Empresa", 1, 0, 'C'); pdf.cell(30, 7, "Total (RD$)", 1, 1, 'C')

        pdf.set_font('Arial', '', 8)
        for inv in selected_invoices:
            pdf.cell(25, 6, inv['invoice_date'], 1, 0, 'L')
            pdf.cell(40, 6, inv['invoice_number'], 1, 0, 'L')
            pdf.cell(85, 6, inv['third_party_name'][:50], 1, 0, 'L')
            pdf.cell(30, 6, f"{inv['total_amount_rd']:,.2f}", 1, 1, 'R')

        pdf.output(save_path)
        return True, "Reporte de retenciones generado exitosamente."
    except Exception as e:
        logger.exception("Error generando PDF de retenciones")
        return False, f"No se pudo generar el PDF de retenciones: {e}"


def generate_advanced_retention_pdf(save_path, company_name, period_str, summary_data, selected_invoices):
    """Genera un PDF para el cálculo avanzado de impuestos, mostrando valores originales y convertidos."""
    try:
        pdf = PDF(orientation='L', company_name=company_name, report_title="Reporte de Cálculo de Impuestos", report_period=period_str)
        pdf.add_page()

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Facturas Incluidas en el Cálculo", 0, 1, 'L')

        # <<-- CAMBIO: Nuevas columnas y anchos para la tabla detallada -->>
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(220, 220, 220)

        # Anchos de columna optimizados para A4 horizontal
        col_widths = [20, 30, 70, 12, 15, 25, 25, 25, 25]
        headers = ['Fecha', 'No. Factura', 'Empresa', 'Mon.', 'Tasa', 'Total (Orig)', 'Total (RD$)', 'Impuestos (Orig)', 'Impuestos (RD$)']

        for i, header in enumerate(headers):
            ln = 1 if i == len(headers) - 1 else 0
            pdf.cell(col_widths[i], 7, header, 1, ln, 'C', 1)

        pdf.set_font('Arial', '', 7)
        currency_symbols = {'USD': '$', 'EUR': '€', 'RD$': 'RD$'}
        fill = False

        # <<-- CAMBIO: Llenar la tabla con los nuevos datos -->>
        for inv in selected_invoices:
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)

            symbol = currency_symbols.get(inv['currency'], inv['currency'])

            # Formatear valores
            total_orig_str = f"{symbol} {inv['total_orig']:,.2f}"
            total_rd_str = f"RD$ {inv['total_rd']:,.2f}"
            imp_orig_str = f"{symbol} {inv['total_imp_orig']:,.2f}"
            imp_rd_str = f"RD$ {inv['total_imp_rd']:,.2f}"

            pdf.cell(col_widths[0], 6, inv['fecha'], 1, 0, 'L', 1)
            pdf.cell(col_widths[1], 6, inv['no_fact'], 1, 0, 'L', 1)
            pdf.cell(col_widths[2], 6, inv['empresa'][:45], 1, 0, 'L', 1)  # Acortar nombre de empresa si es largo
            pdf.cell(col_widths[3], 6, inv['currency'], 1, 0, 'C', 1)
            pdf.cell(col_widths[4], 6, f"{inv['exchange_rate']:.2f}", 1, 0, 'R', 1)
            pdf.cell(col_widths[5], 6, total_orig_str, 1, 0, 'R', 1)
            pdf.cell(col_widths[6], 6, total_rd_str, 1, 0, 'R', 1)
            pdf.cell(col_widths[7], 6, imp_orig_str, 1, 0, 'R', 1)
            pdf.cell(col_widths[8], 6, imp_rd_str, 1, 1, 'R', 1)
            fill = not fill

        # --- El Resumen Final no cambia y ya es compatible con la nueva lógica ---
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Resumen del Cálculo", 0, 1, 'L')

        pdf.set_font('Arial', '', 11)
        pdf.cell(90, 8, f"Cálculo basado en {len(selected_invoices)} facturas seleccionadas.", 0, 1)
        pdf.cell(90, 8, f"Porcentaje aplicado sobre el total: {summary_data.get('percent_to_pay', '0')}%", 0, 1)

        pdf.set_font('Arial', 'B', 11)
        pdf.cell(90, 8, "Totales por Moneda de Origen:", 0, 1)
        pdf.set_font('Arial', '', 11)

        currency_totals = summary_data.get('currency_totals', {})
        for currency, total in sorted(currency_totals.items()):
            symbol = currency_symbols.get(currency, currency)
            pdf.cell(90, 8, f"   - Suma Total Impuestos ({currency}): {symbol} {total:,.2f}", 0, 1)

        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(220, 220, 220)
        grand_total = summary_data.get('grand_total_rd', 0.0)
        pdf.cell(0, 12, f"GRAN TOTAL (CONVERTIDO A RD$): RD$ {grand_total:,.2f}", 1, 1, 'C', 1)

        pdf.output(save_path)
        return True, "Reporte de impuestos y retenciones generado exitosamente."
    except Exception as e:
        logger.exception("Error generando advanced retention PDF")
        return False, f"No se pudo generar el PDF: {e}"