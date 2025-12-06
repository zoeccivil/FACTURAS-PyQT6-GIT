import os
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

# QSS Stylesheet to replicate "Clean Finance UI" design
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

def try_load_font(font_path: str) -> bool:
    """Attempt to load a font file."""
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        return True
    return False

def apply_app_theme(app: QApplication):
    """Apply the global theme to the app."""
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if os.path.exists(font_dir):
        try_load_font(os.path.join(font_dir, "Inter-Regular.ttf"))
        try_load_font(os.path.join(font_dir, "fa-solid-900.ttf"))

    app.setStyleSheet(STYLESHEET)