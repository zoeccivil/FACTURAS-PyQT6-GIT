# theme.py
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont

# Paleta de colores inspirada en Tailwind CSS (Slate & Blue)
COLORS = {
    "slate-900": "#0f172a",
    "slate-800": "#1e293b",
    "slate-700": "#334155",
    "slate-400": "#94a3b8",
    "slate-300": "#cbd5e1",
    "slate-200": "#e2e8f0",
    "gray-50":   "#f8fafc",
    "blue-600":  "#2563eb",
    "blue-500":  "#3b82f6",
    "emerald-500": "#10b981",
    "rose-500":  "#f43f5e",
    "white":     "#ffffff",
    "text-main": "#1e293b"
}

STYLESHEET = f"""
/* --- Global Reset & Base --- */
QWidget {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    color: {COLORS['text-main']};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {COLORS['gray-50']};
}}

/* --- Sidebar (Barra Lateral) --- */
#sidebar {{
    background-color: {COLORS['slate-900']};
    border-right: 1px solid {COLORS['slate-800']};
    min-width: 250px;
    max-width: 250px;
}}

/* Botones del Sidebar */
QPushButton[class="sidebar_btn"] {{
    text-align: left;
    padding: 12px 20px;
    color: {COLORS['slate-400']};
    border: none;
    background-color: transparent;
    font-weight: 500;
    border-radius: 8px;
    margin: 4px 12px;
}}

QPushButton[class="sidebar_btn"]:hover {{
    color: {COLORS['white']};
    background-color: {COLORS['slate-800']};
}}

QPushButton[class="sidebar_btn"]:checked, QPushButton[class="sidebar_btn"][active="true"] {{
    color: {COLORS['white']};
    background-color: {COLORS['blue-600']};
    font-weight: 600;
}}

/* Título de la App en Sidebar */
QLabel#app_logo_text {{
    color: {COLORS['white']};
    font-size: 18px;
    font-weight: 700;
    padding: 20px 0;
}}

/* --- Cards (Tarjetas) --- */
QFrame[class="card"] {{
    background-color: {COLORS['white']};
    border: 1px solid {COLORS['slate-200']};
    border-radius: 12px;
}}

QLabel[class="card_title"] {{
    color: {COLORS['slate-400']};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[class="card_value"] {{
    color: {COLORS['slate-800']};
    font-size: 24px;
    font-weight: 700;
    margin-top: 4px;
}}

/* --- Botones Generales --- */
/* Primario (Negro/Slate Oscuro como en el HTML) */
QPushButton[class="primary"] {{
    background-color: {COLORS['slate-800']};
    color: {COLORS['white']};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    border: none;
}}
QPushButton[class="primary"]:hover {{
    background-color: {COLORS['slate-700']};
}}

/* Acción (Azul) */
QPushButton[class="action"] {{
    background-color: {COLORS['blue-600']};
    color: {COLORS['white']};
    border-radius: 6px;
    padding: 6px 12px;
}}

/* --- Tablas --- */
QTableWidget {{
    background-color: {COLORS['white']};
    border: 1px solid {COLORS['slate-200']};
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: {COLORS['gray-50']};
    selection-color: {COLORS['slate-800']};
}}

QHeaderView::section {{
    background-color: {COLORS['white']};
    color: {COLORS['slate-400']};
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid {COLORS['slate-200']};
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}}

QTableWidget::item {{
    padding: 12px 16px;
    border-bottom: 1px solid {COLORS['gray-50']};
    color: {COLORS['slate-700']};
}}

/* --- Menús y Diálogos --- */
QMenuBar {{
    background-color: {COLORS['white']};
    border-bottom: 1px solid {COLORS['slate-200']};
}}
QMenuBar::item {{
    color: {COLORS['slate-700']};
    padding: 8px 12px;
}}
QMenuBar::item:selected {{
    background-color: {COLORS['gray-50']};
}}
"""

def apply_app_theme(app):
    """Aplica la hoja de estilos global y carga fuentes si existen."""
    app.setStyleSheet(STYLESHEET)
    
    # Intentar cargar fuente Inter desde carpeta local 'fonts'
    fonts_dir = os.path.join(os.getcwd(), "fonts")
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.endswith(".ttf"):
                QFontDatabase.addApplicationFont(os.path.join(fonts_dir, f))
    
    # Configurar fuente por defecto
    font = QFont("Inter")
    if not font.exactMatch():
        font = QFont("Segoe UI") # Fallback Windows
    font.setPointSize(10)
    app.setFont(font)