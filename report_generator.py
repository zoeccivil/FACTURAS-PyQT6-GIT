import os
import io
import glob
import shutil
import tempfile
import logging
import math
import datetime

import pandas as pd
from fpdf import FPDF
from PIL import Image
from pypdf import PdfWriter, PdfReader

# Logger config
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- DESIGN SYSTEM CONSTANTS (RGB) ---
COLORS = {
    'white': (255, 255, 255),
    'slate_50': (248, 250, 252),   # Backgrounds alternos / Headers tabla
    'slate_100': (241, 245, 249),  # Bordes suaves
    'slate_200': (226, 232, 240),  # Bordes
    'slate_400': (148, 163, 184),  # Texto secundario claro
    'slate_500': (100, 116, 139),  # Texto secundario / Labels
    'slate_600': (71, 85, 105),    # Texto cuerpo
    'slate_700': (51, 65, 85),     # Títulos secundarios
    'slate_800': (30, 41, 59),     # Títulos principales
    'slate_900': (15, 23, 42),     # Negro corporativo / Fondos oscuros
    
    'emerald_50': (236, 253, 245), # Fondo Badge Exito
    'emerald_500': (16, 185, 129), # Acento Exito
    'emerald_600': (5, 150, 105),  # Texto Exito
    
    'red_50': (254, 242, 242),     # Fondo Badge Error/Gasto
    'red_500': (239, 68, 68),      # Acento Error/Gasto
    'red_600': (220, 38, 38),      # Texto Error/Gasto
    
    'blue_50': (239, 246, 255),    # Fondo Badge Info
    'blue_500': (59, 130, 246),    # Acento Info
    'blue_600': (37, 99, 235),     # Texto Info
    'indigo_900': (49, 46, 129),   # Fondo Header Multi-moneda
}

class ModernPDF(FPDF):
    """
    Clase extendida de FPDF con capacidades gráficas modernas:
    - Colores HEX/RGB centralizados
    - Rectángulos redondeados
    - Badges
    - Tipografía estándar limpia (Arial como proxy de Inter)
    """
    def __init__(self, orientation='P', unit='mm', format='A4', company_name="", report_title="", report_period=""):
        super().__init__(orientation, unit, format)
        self.company_name = company_name
        self.report_title = report_title
        self.report_period = report_period
        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()
        self.set_margins(15, 15, 15) # Márgenes más generosos

    def set_color_rgb(self, rgb_tuple):
        self.set_draw_color(*rgb_tuple)
        self.set_fill_color(*rgb_tuple)
        self.set_text_color(*rgb_tuple)

    def set_text_color_rgb(self, rgb_tuple):
        self.set_text_color(*rgb_tuple)
        
    def set_fill_color_rgb(self, rgb_tuple):
        self.set_fill_color(*rgb_tuple)
        
    def set_draw_color_rgb(self, rgb_tuple):
        self.set_draw_color(*rgb_tuple)

    def rounded_rect(self, x, y, w, h, r, style='D', corners='1234'):
        """Dibuja un rectángulo con esquinas redondeadas."""
        k = 0.26878  # Kappa para curvas de Bezier aproximando círculo
        # Corrección fpdf 1.7
        # x, y son coordenadas esquina superior izquierda
        
        if style == 'F':
            op = 'f'
        elif style == 'FD' or style == 'DF':
            op = 'B'
        else:
            op = 'S'
            
        hp = self.h
        self._out('%.2f %.2f m' % ((x + r) * self.k, (hp - y) * self.k))

        # Esquina 2 (Arriba Derecha)
        if '2' in corners:
            xc = x + w - r
            yc = y + r
            self._out('%.2f %.2f l' % (xc * self.k, (hp - y) * self.k))
            self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % 
                ((xc + r * k) * self.k, (hp - y) * self.k,
                 (x + w) * self.k, (hp - (yc - r * k)) * self.k,
                 (x + w) * self.k, (hp - yc) * self.k))
        else:
            self._out('%.2f %.2f l' % ((x + w) * self.k, (hp - y) * self.k))

        # Esquina 3 (Abajo Derecha)
        if '3' in corners:
            xc = x + w - r
            yc = y + h - r
            self._out('%.2f %.2f l' % ((x + w) * self.k, (hp - yc) * self.k))
            self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % 
                ((x + w) * self.k, (hp - (yc + r * k)) * self.k,
                 (xc + r * k) * self.k, (hp - (y + h)) * self.k,
                 xc * self.k, (hp - (y + h)) * self.k))
        else:
            self._out('%.2f %.2f l' % ((x + w) * self.k, (hp - (y + h)) * self.k))

        # Esquina 4 (Abajo Izquierda)
        if '4' in corners:
            xc = x + r
            yc = y + h - r
            self._out('%.2f %.2f l' % (xc * self.k, (hp - (y + h)) * self.k))
            self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % 
                ((xc - r * k) * self.k, (hp - (y + h)) * self.k,
                 x * self.k, (hp - (yc + r * k)) * self.k,
                 x * self.k, (hp - yc) * self.k))
        else:
            self._out('%.2f %.2f l' % (x * self.k, (hp - (y + h)) * self.k))

        # Esquina 1 (Arriba Izquierda)
        if '1' in corners:
            xc = x + r
            yc = y + r
            self._out('%.2f %.2f l' % (x * self.k, (hp - yc) * self.k))
            self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % 
                (x * self.k, (hp - (yc - r * k)) * self.k,
                 (xc - r * k) * self.k, (hp - y) * self.k,
                 xc * self.k, (hp - y) * self.k))
        else:
            self._out('%.2f %.2f l' % (x * self.k, (hp - y) * self.k))

        self._out(op)

    def draw_badge(self, text, x, y, bg_color, text_color):
        """Dibuja una píldora (badge) pequeña."""
        self.set_font('Arial', 'B', 7)
        w = self.get_string_width(text) + 6
        h = 5
        
        self.set_fill_color_rgb(bg_color)
        self.set_text_color_rgb(text_color)
        self.set_draw_color_rgb(bg_color) # Borde del mismo color que fondo
        
        self.rounded_rect(x, y, w, h, 2, 'DF')
        
        self.set_xy(x, y)
        self.cell(w, h, text, 0, 0, 'C')
        
    def header(self):
        # Header Moderno Limpio
        if self.page_no() == 1:
            # Logo placeholder (cuadrado oscuro)
            self.set_fill_color_rgb(COLORS['slate_900'])
            self.rounded_rect(15, 12, 10, 10, 2, 'F')
            
            # Título App
            self.set_xy(28, 12)
            self.set_font('Arial', 'B', 14)
            self.set_text_color_rgb(COLORS['slate_900'])
            self.cell(0, 6, "Gestión Facturas PRO", 0, 1, 'L')
            
            # Subtítulo Reporte
            self.set_xy(28, 18)
            self.set_font('Arial', '', 10)
            self.set_text_color_rgb(COLORS['slate_500'])
            self.cell(0, 5, self.report_title, 0, 1, 'L')
            
            # Bloque Derecho (Periodo/Empresa)
            self.set_y(12)
            self.set_font('Arial', 'B', 8)
            self.set_text_color_rgb(COLORS['slate_400'])
            self.cell(0, 4, "EMPRESA / PERIODO", 0, 1, 'R')
            
            self.set_font('Arial', 'B', 10)
            self.set_text_color_rgb(COLORS['slate_800'])
            self.cell(0, 5, self.company_name[:40], 0, 1, 'R')
            
            self.set_font('Arial', '', 9)
            self.set_text_color_rgb(COLORS['slate_500'])
            self.cell(0, 5, self.report_period, 0, 1, 'R')
            
            # Línea separadora
            self.ln(5)
            self.set_draw_color_rgb(COLORS['slate_200'])
            self.line(15, self.get_y(), self.w - 15, self.get_y())
            self.ln(8)
        else:
            # Header simplificado páginas siguientes
            self.set_font('Arial', 'I', 8)
            self.set_text_color_rgb(COLORS['slate_400'])
            self.cell(0, 10, f"{self.report_title} - {self.report_period}", 0, 0, 'R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.set_text_color_rgb(COLORS['slate_400'])
        self.set_draw_color_rgb(COLORS['slate_100'])
        self.line(15, self.get_y() - 2, self.w - 15, self.get_y() - 2)
        self.cell(0, 10, f'Confidencial - Página {self.page_no()}/{{nb}}', 0, 0, 'C')


def generate_professional_pdf(report_data, save_path, company_name, month, year, attachment_base_path=None):
    """
    Genera el Reporte Mensual estilo Dashboard moderno.
    """
    temp_files = []

    # (Lógica original de búsqueda de adjuntos se mantiene intacta)
    def find_attachment_fullpath(base_path, relative_path, invoice):
        # ... (código existente de resolución de rutas se mantiene igual) ...
        # (Para brevedad, asumo que esta función auxiliar existe tal cual 
        #  estaba en el archivo original. La insertaré completa en el archivo final)
        try:
            if invoice and invoice.get("attachment_resolved"):
                ar = invoice.get("attachment_resolved")
                if ar and os.path.exists(ar): return ar
        except: pass
        if not relative_path: return None
        rel = str(relative_path).strip()
        if not rel: return None
        if os.path.isabs(rel) and os.path.exists(rel): return rel
        candidates = []
        if base_path:
            candidates.append(os.path.join(base_path, rel))
            candidates.append(os.path.join(base_path, os.path.basename(rel)))
        try:
            comp = invoice.get("company_id") or invoice.get("company")
            if comp and base_path: candidates.append(os.path.join(base_path, str(comp), rel))
        except: pass
        try:
            if base_path:
                pattern = os.path.join(base_path, "**", os.path.basename(rel))
                matches = glob.glob(pattern, recursive=True)
                if matches: return matches[0]
        except: pass
        return None

    try:
        # Temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_report:
            temp_report_path = temp_report.name
            temp_files.append(temp_report_path)

        # Usar orientación Vertical (P) para mejor layout tipo A4 documento, 
        # o Horizontal (L) si se prefiere dashboard. El mockup parecía Vertical.
        pdf = ModernPDF(
            orientation='P',
            company_name=company_name,
            report_title="Reporte Mensual de Facturación",
            report_period=f"{month}/{year}",
        )
        pdf.add_page()

        summary = report_data.get('summary', {}) if report_data else {}
        
        # -----------------------------------------------------------------
        # KPI CARDS (Grid de 3)
        # -----------------------------------------------------------------
        # Margen izquierdo ya es 15
        full_width = pdf.w - 30
        card_gap = 5
        card_w = (full_width - (card_gap * 2)) / 3
        card_h = 25
        
        y_start = pdf.get_y()
        
        # Datos para cards
        kpis = [
            {
                "label": "TOTAL INGRESOS", 
                "value": summary.get('total_ingresos', 0.0), 
                "color_accent": COLORS['emerald_500'],
                "icon": "+" 
            },
            {
                "label": "TOTAL GASTOS", 
                "value": summary.get('total_gastos', 0.0), 
                "color_accent": COLORS['red_500'],
                "icon": "-"
            },
            {
                "label": "BALANCE NETO", 
                "value": summary.get('total_neto', 0.0), 
                "color_accent": COLORS['slate_800'],
                "icon": "="
            }
        ]
        
        for i, kpi in enumerate(kpis):
            x = 15 + (card_w + card_gap) * i
            
            # Fondo Card
            pdf.set_fill_color_rgb(COLORS['white'])
            pdf.set_draw_color_rgb(COLORS['slate_200'])
            pdf.rounded_rect(x, y_start, card_w, card_h, 2, 'DF')
            
            # Borde lateral izquierdo grueso
            pdf.set_fill_color_rgb(kpi['color_accent'])
            pdf.rect(x, y_start, 1.5, card_h, 'F')
            
            # Label
            pdf.set_xy(x + 4, y_start + 4)
            pdf.set_font('Arial', 'B', 7)
            pdf.set_text_color_rgb(COLORS['slate_500'])
            pdf.cell(card_w - 5, 4, kpi['label'], 0, 1, 'L')
            
            # Value
            pdf.set_xy(x + 4, y_start + 12)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color_rgb(COLORS['slate_800'])
            val_str = f"RD$ {kpi['value']:,.2f}"
            pdf.cell(card_w - 5, 6, val_str, 0, 1, 'L')

        pdf.set_y(y_start + card_h + 8)

        # -----------------------------------------------------------------
        # ITBIS MINI CARDS (Grid 3 abajo)
        # -----------------------------------------------------------------
        mini_card_h = 12
        itbis_data = [
            ("ITBIS Ventas", summary.get('itbis_ingresos', 0.0), COLORS['slate_50']),
            ("ITBIS Compras", summary.get('itbis_gastos', 0.0), COLORS['slate_50']),
            ("ITBIS Neto", summary.get('itbis_neto', 0.0), COLORS['blue_50'])
        ]
        
        y_mini = pdf.get_y()
        for i, (label, val, bg) in enumerate(itbis_data):
            x = 15 + (card_w + card_gap) * i
            
            pdf.set_fill_color_rgb(bg)
            pdf.set_draw_color_rgb(COLORS['slate_100'])
            pdf.rounded_rect(x, y_mini, card_w, mini_card_h, 2, 'DF')
            
            pdf.set_xy(x + 3, y_mini + 3)
            pdf.set_font('Arial', '', 7)
            pdf.set_text_color_rgb(COLORS['slate_500'])
            pdf.cell(card_w/2, 6, label, 0, 0, 'L')
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color_rgb(COLORS['slate_700'])
            pdf.cell((card_w/2)-6, 6, f"{val:,.2f}", 0, 0, 'R')
            
        pdf.set_y(y_mini + mini_card_h + 10)

        # -----------------------------------------------------------------
        # TABLAS
        # -----------------------------------------------------------------
        def draw_modern_table(title, headers, data, col_widths_pct, accent_color):
            # Título Sección
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color_rgb(COLORS['slate_800'])
            
            # Pequeña barra decorativa
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.set_fill_color_rgb(accent_color)
            pdf.rounded_rect(x, y+1, 1, 4, 0.5, 'F')
            
            pdf.set_x(x + 3)
            pdf.cell(0, 6, title.upper(), 0, 1, 'L')
            pdf.ln(2)
            
            # Header Tabla
            full_w = pdf.w - 30
            col_widths = [(pct/100)*full_w for pct in col_widths_pct]
            
            pdf.set_font('Arial', 'B', 7)
            pdf.set_text_color_rgb(COLORS['slate_500'])
            pdf.set_fill_color_rgb(COLORS['slate_50'])
            pdf.set_draw_color_rgb(COLORS['slate_200'])
            
            # Fondo Header redondeado top
            # pdf.rounded_rect(15, pdf.get_y(), full_w, 8, 2, 'F', corners='12') 
            # Simple rect por compatibilidad
            pdf.rect(15, pdf.get_y(), full_w, 8, 'F')
            
            start_x = 15
            for i, h_text in enumerate(headers):
                align = 'R' if i >= 3 else 'L' # Ultimas columnas numéricas
                pdf.set_xy(start_x, pdf.get_y())
                pdf.cell(col_widths[i], 8, h_text, 0, 0, align)
                start_x += col_widths[i]
            pdf.ln(8)
            
            # Filas
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color_rgb(COLORS['slate_600'])
            
            for row_idx, row in enumerate(data):
                pdf.set_draw_color_rgb(COLORS['slate_50']) # Línea muy sutil
                h_row = 8
                
                # Check page break
                if pdf.get_y() > 270:
                    pdf.add_page()
                    # Re-imprimir header si corta
                    pdf.set_font('Arial', 'B', 7)
                    pdf.set_text_color_rgb(COLORS['slate_500'])
                    pdf.set_fill_color_rgb(COLORS['slate_50'])
                    pdf.rect(15, pdf.get_y(), full_w, 8, 'F')
                    start_x = 15
                    for i, h_text in enumerate(headers):
                        align = 'R' if i >= 3 else 'L'
                        pdf.set_xy(start_x, pdf.get_y())
                        pdf.cell(col_widths[i], 8, h_text, 0, 0, align)
                        start_x += col_widths[i]
                    pdf.ln(8)
                    pdf.set_font('Arial', '', 8)
                    pdf.set_text_color_rgb(COLORS['slate_600'])

                start_x = 15
                for i, cell_val in enumerate(row):
                    align = 'R' if i >= 3 else 'L'
                    
                    # Highlight Total column
                    if i == 4: 
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_text_color_rgb(COLORS['slate_800'])
                    else:
                        pdf.set_font('Arial', '', 8)
                        pdf.set_text_color_rgb(COLORS['slate_600'])
                        
                    # Badge logic para estado (si existiera columna estado, aqui simulado)
                    # if i == 3: ...
                    
                    pdf.set_xy(start_x, pdf.get_y())
                    pdf.cell(col_widths[i], h_row, str(cell_val), 'B', 0, align)
                    start_x += col_widths[i]
                pdf.ln(h_row)

        def _safe_list(lst):
            n = []
            for x in lst or []:
                if isinstance(x, dict): n.append(x)
                else: 
                    try: n.append(dict(x)) 
                    except: pass
            return n

        # Datos Facturas Emitidas
        inv_emitted = _safe_list(report_data.get('emitted_invoices', []))
        data_em = []
        for f in inv_emitted:
            rate = float(f.get('exchange_rate', 1.0) or 1.0)
            itbis = float(f.get('itbis', 0.0)) * rate
            total = float(f.get('total_amount_rd') or (float(f.get('total_amount', 0.0)) * rate))
            data_em.append([
                f.get('invoice_date', ''),
                f.get('invoice_number', ''),
                f.get('third_party_name', '')[:30], # Truncar nombre largo
                f"{itbis:,.2f}",
                f"{total:,.2f}"
            ])
            
        draw_modern_table(
            "Últimas Facturas Emitidas",
            ['Fecha', 'NCF', 'Cliente', 'ITBIS', 'Total (RD$)'],
            data_em,
            [15, 20, 35, 15, 15],
            COLORS['emerald_500']
        )
        
        pdf.ln(8)
        
        # Datos Gastos
        inv_expenses = _safe_list(report_data.get('expense_invoices', []))
        data_ex = []
        for f in inv_expenses:
            rate = float(f.get('exchange_rate', 1.0) or 1.0)
            itbis = float(f.get('itbis', 0.0)) * rate
            total = float(f.get('total_amount_rd') or (float(f.get('total_amount', 0.0)) * rate))
            data_ex.append([
                f.get('invoice_date', ''),
                f.get('invoice_number', ''),
                f.get('third_party_name', '')[:30],
                f"{itbis:,.2f}",
                f"{total:,.2f}"
            ])
            
        draw_modern_table(
            "Gastos Registrados",
            ['Fecha', 'NCF', 'Proveedor', 'ITBIS', 'Total (RD$)'],
            data_ex,
            [15, 20, 35, 15, 15],
            COLORS['red_500']
        )

        pdf.output(temp_report_path)

        # ---------------------------------------------------------
        # FASE 2: UNIÓN DE ANEXOS (Lógica preservada del original)
        # ---------------------------------------------------------
        merger = PdfWriter()
        try:
            merger.append(temp_report_path)
        except: pass
        
        attachments_candidates = []
        if report_data and report_data.get('ordered_attachments') is not None:
             attachments_candidates = report_data.get('ordered_attachments')
        else:
             for f in inv_emitted + inv_expenses:
                 res = f.get('attachment_resolved')
                 orig = f.get('attachment_path') or f.get('attachment')
                 if res or orig:
                     nf = dict(f)
                     nf['attachment_resolved'] = res
                     nf['attachment_original'] = orig
                     attachments_candidates.append(nf)
                     
        for invoice in attachments_candidates:
            try:
                rel = invoice.get('attachment_original') or ''
                full_path = find_attachment_fullpath(attachment_base_path, rel, invoice)
                if not full_path: continue
                
                if full_path.lower().endswith('.pdf'):
                    try:
                        merger.append(PdfReader(full_path, strict=False))
                    except: pass
                elif full_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Convert image to PDF page
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as timg:
                        timg_p = timg.name
                        temp_files.append(timg_p)
                    
                    pdf_img = ModernPDF(orientation='P', report_title="Anexo", report_period=invoice.get('invoice_number', ''))
                    pdf_img.add_page()
                    # Fit image logic
                    try:
                        with Image.open(full_path) as im:
                            w, h = im.size
                            aspect = w / h
                            avail_w = pdf_img.w - 30
                            avail_h = pdf_img.h - 40
                            disp_w = avail_w
                            disp_h = disp_w / aspect
                            if disp_h > avail_h:
                                disp_h = avail_h
                                disp_w = disp_h * aspect
                            pdf_img.image(full_path, x=15, y=30, w=disp_w, h=disp_h)
                        pdf_img.output(timg_p)
                        merger.append(PdfReader(timg_p, strict=False))
                    except: pass
            except: pass

        with open(save_path, "wb") as f_out:
            merger.write(f_out)
            
        return True, "Reporte generado con éxito."

    except Exception as e:
        logger.exception("Error generando PDF mensual")
        return False, str(e)
    finally:
        for tf in temp_files:
            try: os.remove(tf)
            except: pass

def generate_retention_pdf(save_path, company_name, period_str, results_data, selected_invoices):
    """
    Genera el 'Estado de Retención' estilo extracto bancario.
    """
    try:
        pdf = ModernPDF(orientation='P', company_name=company_name, report_title="Estado de Retención", report_period=period_str)
        pdf.add_page()

        # --- HEADER "CLASSIC BANK" ---
        pdf.set_y(15)
        # Left
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color_rgb(COLORS['slate_900'])
        pdf.cell(0, 8, "Estado de Retención", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color_rgb(COLORS['slate_500'])
        pdf.cell(0, 6, "Cálculo de impuestos retenidos a terceros", 0, 1, 'L')
        
        # Right box (Ref)
        ref_code = results_data.get("ref_code", f"RET-{period_str.replace(' ','-')}")
        pdf.set_xy(pdf.w - 70, 15)
        pdf.set_fill_color_rgb(COLORS['slate_50'])
        pdf.rounded_rect(pdf.w - 70, 15, 55, 14, 2, 'F')
        
        pdf.set_xy(pdf.w - 68, 17)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color_rgb(COLORS['slate_600'])
        pdf.cell(50, 4, f"Ref: {ref_code}", 0, 1, 'R')
        pdf.set_x(pdf.w - 68)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color_rgb(COLORS['slate_400'])
        pdf.cell(50, 4, f"Corte: {datetime.date.today()}", 0, 1, 'R')
        
        pdf.ln(15)
        
        # --- STATEMENT CARD (DARK) ---
        card_h = 45
        card_w = pdf.w - 30
        x = 15
        y = pdf.get_y()
        
        # Fondo oscuro
        pdf.set_fill_color_rgb(COLORS['slate_900'])
        pdf.rounded_rect(x, y, card_w, card_h, 4, 'F')
        
        # Círculo decorativo (simulado con rect)
        # No soportado easy, omitir o usar imagen overlay. Omitimos por limpieza.
        
        # Data
        base = float(results_data.get("total_general_rd", 0.0) or 0.0)
        total_ret = float(results_data.get("total_a_retener", 0.0) or 0.0)
        count = int(results_data.get("num_invoices", len(selected_invoices)))
        norma = results_data.get("norm_label", "Norma 02-05")
        
        # Columna Izq (Base)
        pdf.set_xy(x+10, y+8)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color_rgb(COLORS['slate_400'])
        pdf.cell(80, 5, "MONTO BASE CALCULADO", 0, 1, 'L')
        
        pdf.set_x(x+10)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color_rgb(COLORS['white'])
        pdf.cell(80, 8, f"RD$ {base:,.2f}", 0, 1, 'L')
        
        # Badges dentro de la card oscura
        bx = x+10
        by = y+25
        pdf.draw_badge(f"{count} Facturas", bx, by, COLORS['slate_700'], COLORS['slate_100'])
        pdf.draw_badge(norma, bx+30, by, COLORS['slate_700'], COLORS['slate_100'])
        
        # Columna Der (Total a Pagar) - Separador vertical
        pdf.set_draw_color_rgb(COLORS['slate_700'])
        pdf.line(x + (card_w/2), y+5, x + (card_w/2), y+card_h-5)
        
        pdf.set_xy(x + (card_w/2) + 10, y+8)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color_rgb(COLORS['emerald_500'])
        pdf.cell(80, 5, "TOTAL A RETENER (PAGAR)", 0, 1, 'L')
        
        pdf.set_xy(x + (card_w/2) + 10, y+14)
        pdf.set_font('Arial', 'B', 24)
        pdf.set_text_color_rgb(COLORS['white'])
        pdf.cell(80, 12, f"RD$ {total_ret:,.2f}", 0, 1, 'L')
        
        pdf.set_xy(x + (card_w/2) + 10, y+28)
        pdf.set_font('Arial', '', 7)
        pdf.set_text_color_rgb(COLORS['slate_400'])
        pdf.cell(80, 4, "Remitir a DGII antes del día 17.", 0, 1, 'L')
        
        pdf.set_y(y + card_h + 10)
        
        # --- DESGLOSE ---
        pdf.set_fill_color_rgb(COLORS['white'])
        pdf.set_draw_color_rgb(COLORS['slate_200'])
        pdf.rounded_rect(x, pdf.get_y(), card_w, 35, 2, 'S') # Borde simple
        
        y_d = pdf.get_y() + 4
        pdf.set_xy(x+5, y_d)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color_rgb(COLORS['slate_800'])
        pdf.cell(0, 5, "Desglose del Cálculo", 0, 1, 'L')
        pdf.set_draw_color_rgb(COLORS['slate_100'])
        pdf.line(x+5, pdf.get_y()+1, x+card_w-5, pdf.get_y()+1)
        
        # Filas desglose
        itbis_tot = float(results_data.get("total_itbis_rd", 0.0) or 0.0)
        ret_itbis = float(results_data.get("ret_itbis", 0.0) or 0.0)
        
        lines = [
            ("ITBIS Total Facturado", f"RD$ {itbis_tot:,.2f}", COLORS['slate_600']),
            ("Retención ITBIS (100% Norma)", f"- RD$ {ret_itbis:,.2f}", COLORS['red_600']),
        ]
        
        y_line = pdf.get_y() + 4
        for label, val, color in lines:
            pdf.set_xy(x+5, y_line)
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color_rgb(COLORS['slate_500'])
            pdf.cell(100, 5, label, 0, 0, 'L')
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color_rgb(color)
            pdf.cell(card_w - 110, 5, val, 0, 0, 'R')
            y_line += 6
            
        # Total Final línea
        pdf.line(x+5, y_line+1, x+card_w-5, y_line+1)
        pdf.set_xy(x+5, y_line+3)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color_rgb(COLORS['slate_900'])
        pdf.cell(100, 5, "Total Retenido", 0, 0, 'L')
        pdf.cell(card_w - 110, 5, f"RD$ {total_ret:,.2f}", 0, 0, 'R')
        
        pdf.set_y(y_d + 35 + 8)
        
        # --- TABLA DOCUMENTOS ---
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color_rgb(COLORS['slate_500'])
        pdf.cell(0, 6, "DOCUMENTOS INCLUIDOS", 0, 1, 'L')
        
        # Header Tabla
        headers = ["Fecha", "Proveedor", "NCF", "Base Imp.", "ITBIS", "Retención"]
        widths = [20, 60, 30, 25, 20, 25]
        
        pdf.set_fill_color_rgb(COLORS['slate_50'])
        pdf.set_text_color_rgb(COLORS['slate_500'])
        pdf.set_font('Arial', 'B', 7)
        pdf.rect(15, pdf.get_y(), card_w, 8, 'F')
        
        start_x = 15
        for i, h in enumerate(headers):
            align = 'R' if i >= 3 else 'L'
            pdf.set_xy(start_x, pdf.get_y())
            pdf.cell(widths[i], 8, h, 0, 0, align)
            start_x += widths[i]
        pdf.ln(8)
        
        # Rows
        pdf.set_font('Arial', '', 7)
        pdf.set_text_color_rgb(COLORS['slate_600'])
        
        for inv in selected_invoices:
            # Cálculos de fila
            base_rd = float(inv.get("total_amount_rd", 0.0) or 0.0)
            rate = float(inv.get("exchange_rate", 1.0) or 1.0)
            itbis_rd = float(inv.get("itbis", 0.0) or 0.0) * rate
            # Retención proporcional simple para display
            ret_row = 0.0
            if itbis_tot > 0:
                ret_row = (itbis_rd / itbis_tot) * total_ret
            
            vals = [
                str(inv.get("invoice_date", "")),
                str(inv.get("third_party_name", ""))[:35],
                str(inv.get("invoice_number", "")),
                f"{base_rd:,.2f}",
                f"{itbis_rd:,.2f}",
                f"{ret_row:,.2f}"
            ]
            
            start_x = 15
            bg_ret = False
            for i, v in enumerate(vals):
                align = 'R' if i >= 3 else 'L'
                pdf.set_xy(start_x, pdf.get_y())
                
                # Columna retención con fondo sutil
                if i == 5:
                    pdf.set_fill_color_rgb(COLORS['slate_50'])
                    pdf.cell(widths[i], 6, v, 0, 0, align, fill=True)
                    pdf.set_font('Arial', 'B', 7) # Negrita
                else:
                    pdf.cell(widths[i], 6, v, 0, 0, align)
                    pdf.set_font('Arial', '', 7)
                
                start_x += widths[i]
            pdf.ln(6)
            
        pdf.output(save_path)
        return True, "PDF generado."

    except Exception as e:
        logger.exception("Error Retencion PDF")
        return False, str(e)

def generate_advanced_retention_pdf(save_path, company_name, period_str, summary_data, selected_invoices):
    """
    Genera el reporte multi-moneda / impuestos avanzados.
    """
    try:
        # Orientación Horizontal para muchas columnas
        pdf = ModernPDF(orientation='L', company_name=company_name, report_title="Reporte Impuestos Multi-Moneda", report_period=period_str)
        pdf.add_page()
        
        full_w = pdf.w - 30
        
        # --- GLOBAL SUMMARY BAR (Indigo) ---
        pdf.set_fill_color_rgb(COLORS['indigo_900'])
        pdf.rounded_rect(15, pdf.get_y(), full_w, 20, 3, 'F')
        
        grand_total = summary_data.get('grand_total_rd', 0.0)
        
        # Label
        pdf.set_xy(20, 20)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color_rgb(COLORS['blue_50']) # Indigo muy claro
        pdf.cell(100, 4, "IMPUESTO TOTAL ESTIMADO (GLOBAL)", 0, 1, 'L')
        
        # Value
        pdf.set_xy(20, 25)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color_rgb(COLORS['white'])
        pdf.cell(100, 8, f"RD$ {grand_total:,.2f}", 0, 1, 'L')
        
        # Tasas info (simuladas o reales si vinieran en summary_data)
        pdf.set_xy(full_w - 60, 20)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color_rgb(COLORS['blue_50'])
        pdf.cell(60, 4, f"Tasa USD Ref: 58.50", 0, 1, 'R') # Placeholder si no hay dato real
        
        pdf.set_y(45)
        
        # --- GROUP BY CURRENCY ---
        # Agrupar facturas por moneda
        grouped = {}
        for inv in selected_invoices:
            curr = inv.get('currency', 'RD$')
            if curr not in grouped: grouped[curr] = []
            grouped[curr].append(inv)
            
        currency_map = {
            'USD': {'name': 'Dólar Estadounidense', 'badge': COLORS['emerald_50']},
            'EUR': {'name': 'Euro', 'badge': COLORS['blue_50']},
            'RD$': {'name': 'Peso Dominicano', 'badge': COLORS['slate_50']}
        }
        
        for curr, invoices in grouped.items():
            # Header Sección Moneda
            meta = currency_map.get(curr, {'name': curr, 'badge': COLORS['slate_50']})
            
            # Badge Moneda
            pdf.draw_badge(f"{curr} - {meta['name']}", 15, pdf.get_y(), meta['badge'], COLORS['slate_700'])
            
            # Subtotal Impuestos de esta moneda
            sub_imp = sum(x.get('total_imp_orig', 0) for x in invoices)
            pdf.set_xy(70, pdf.get_y())
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color_rgb(COLORS['slate_600'])
            pdf.cell(100, 5, f"Impuestos: {sub_imp:,.2f} {curr}", 0, 1, 'L')
            
            pdf.ln(2)
            
            # Tabla
            headers = ["Fecha", "Factura / Empresa", "Tasa", f"Total ({curr})", f"Imp. ({curr})", "Imp. (RD$)"]
            # Anchos adaptados a Landscape
            widths = [25, 100, 25, 35, 35, 40]
            
            # Table Head
            pdf.set_fill_color_rgb(COLORS['slate_50'])
            pdf.set_text_color_rgb(COLORS['slate_500'])
            pdf.set_font('Arial', '', 8)
            pdf.rect(15, pdf.get_y(), full_w, 8, 'F')
            
            start_x = 15
            for i, h in enumerate(headers):
                align = 'R' if i >= 2 else 'L'
                pdf.set_xy(start_x, pdf.get_y())
                pdf.cell(widths[i], 8, h, 0, 0, align)
                start_x += widths[i]
            pdf.ln(8)
            
            # Table Body
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color_rgb(COLORS['slate_600'])
            
            sub_imp_rd = 0.0
            
            for inv in invoices:
                # Check page break
                if pdf.get_y() > 180: pdf.add_page()
                
                imp_rd = inv.get('total_imp_rd', 0.0)
                sub_imp_rd += imp_rd
                
                vals = [
                    inv.get('fecha', ''),
                    f"{inv.get('no_fact','')} - {inv.get('empresa','')[:30]}",
                    f"{inv.get('exchange_rate',1):.2f}",
                    f"{inv.get('total_orig',0):,.2f}",
                    f"{inv.get('total_imp_orig',0):,.2f}",
                    f"{imp_rd:,.2f}"
                ]
                
                start_x = 15
                for i, v in enumerate(vals):
                    align = 'R' if i >= 2 else 'L'
                    pdf.set_xy(start_x, pdf.get_y())
                    
                    # Highlight last col
                    if i == 5:
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_fill_color_rgb(COLORS['slate_50'])
                        pdf.cell(widths[i], 6, v, 0, 0, align, fill=True)
                        pdf.set_font('Arial', '', 8)
                    elif i == 4:
                        pdf.set_text_color_rgb(COLORS['red_600']) # Impuesto orig en rojo
                        pdf.cell(widths[i], 6, v, 0, 0, align)
                        pdf.set_text_color_rgb(COLORS['slate_600'])
                    else:
                        pdf.cell(widths[i], 6, v, 0, 0, align)
                        
                    start_x += widths[i]
                pdf.ln(6)
            
            # Subtotal Footer
            pdf.ln(2)
            pdf.set_x(full_w - 80)
            pdf.set_fill_color_rgb(COLORS['emerald_50'])
            pdf.set_text_color_rgb(COLORS['emerald_600'])
            pdf.set_font('Arial', 'B', 8)
            pdf.rounded_rect(pdf.get_x(), pdf.get_y(), 95, 8, 2, 'F')
            pdf.cell(95, 8, f"Subtotal Convertido: RD$ {sub_imp_rd:,.2f}", 0, 1, 'C')
            
            pdf.ln(10)

        # Final Card (Bottom Right)
        if pdf.get_y() > 150: pdf.add_page()
        
        pdf.set_x(full_w/2)
        pdf.set_fill_color_rgb(COLORS['slate_900'])
        pdf.rounded_rect(pdf.w/2 + 15, pdf.get_y(), (full_w/2), 30, 3, 'F')
        
        y_f = pdf.get_y()
        pdf.set_xy(pdf.w/2 + 25, y_f + 5)
        pdf.set_text_color_rgb(COLORS['slate_400'])
        pdf.cell(50, 5, "TOTAL A PAGAR (RD$)", 0, 1, 'L')
        
        pdf.set_xy(pdf.w/2 + 25, y_f + 12)
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color_rgb(COLORS['white'])
        pdf.cell(50, 10, f"{grand_total:,.2f}", 0, 1, 'L')

        pdf.output(save_path)
        return True, "Reporte Multi-moneda Generado."

    except Exception as e:
        logger.exception("Error Adv PDF")
        return False, str(e)

def generate_excel_report(report_data, save_path):
    """Genera reporte Excel (sin cambios de diseño visual, solo datos)."""
    try:
        summary_totals = report_data["summary"]
        resumen_data = {
            "Descripción": ["Total Ingresos (RD$)", "Total ITBIS Ingresos (RD$)", "Total Gastos (RD$)", "Total ITBIS Gastos (RD$)", "ITBIS Neto (RD$)", "Total Neto (RD$)"],
            "Monto": [summary_totals.get("total_ingresos", 0.0), summary_totals.get("itbis_ingresos", 0.0), summary_totals.get("total_gastos", 0.0), summary_totals.get("itbis_gastos", 0.0), summary_totals.get("itbis_neto", 0.0), summary_totals.get("total_neto", 0.0)]
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_ingresos = pd.DataFrame(report_data.get("emitted_invoices", []))
        df_gastos = pd.DataFrame(report_data.get("expense_invoices", []))

        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            df_ingresos.to_excel(writer, sheet_name='Ingresos', index=False)
            df_gastos.to_excel(writer, sheet_name='Gastos', index=False)

        return True, "Excel generado exitosamente."
    except Exception as e:
        return False, f"Error generando Excel: {e}"

def generate_tax_calculation_pdf(report_data, output_path):
    """
    Wrapper para reporte avanzado usando la estructura de datos de Tax Calculation.
    Transforma los datos y llama a generate_advanced_retention_pdf.
    """
    try:
        calc = report_data.get("calculation", {}) or {}
        invoices = report_data.get("invoices", []) or []
        company_name = str(calc.get("company_id", ""))
        period_str = f"{calc.get('start_date', '')} al {calc.get('end_date', '')}"
        percent_to_pay = float(calc.get("percent_to_pay", 0.0) or 0.0)

        currency_totals = {}
        grand_total_rd = 0.0
        selected_invoices_data = []

        for inv in invoices:
            if not inv.get("selected_for_calc", False): continue

            currency = inv.get("currency") or "RD$"
            rate = float(inv.get("exchange_rate", 1.0) or 1.0)
            total_orig = float(inv.get("total_amount", 0.0) or 0.0)
            itbis_orig = float(inv.get("itbis", 0.0) or 0.0)
            
            # Lógica de cálculo (simplificada para display)
            valor_retencion_orig = itbis_orig * 0.30 if inv.get("has_retention") else 0.0
            monto_a_pagar_orig = total_orig * (percent_to_pay / 100.0)
            itbis_neto_orig = itbis_orig - valor_retencion_orig
            # Total impuestos = ITBIS neto + % sobre total
            total_impuestos_row_orig = itbis_neto_orig + monto_a_pagar_orig

            total_rd = float(inv.get("total_amount_rd", 0.0) or (total_orig * rate))
            total_imp_rd = total_impuestos_row_orig * rate

            currency_totals.setdefault(currency, 0.0)
            currency_totals[currency] += total_impuestos_row_orig
            grand_total_rd += total_imp_rd

            selected_invoices_data.append({
                "fecha": str(inv.get("invoice_date", "")),
                "no_fact": str(inv.get("invoice_number", "")),
                "empresa": str(inv.get("third_party_name", "")),
                "currency": currency,
                "exchange_rate": rate,
                "total_orig": total_orig,
                "total_rd": total_rd,
                "total_imp_orig": total_impuestos_row_orig,
                "total_imp_rd": total_imp_rd,
            })

        summary_data = {
            "percent_to_pay": percent_to_pay,
            "currency_totals": currency_totals,
            "grand_total_rd": grand_total_rd,
        }

        return generate_advanced_retention_pdf(output_path, company_name, period_str, summary_data, selected_invoices_data)
        
    except Exception as e:
        logger.exception("Error wrapper tax pdf")
        return False, str(e)