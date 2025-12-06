# 🎨 Modern Dashboard UI - Facturas Pro

A complete modern dashboard interface for the Facturas Pro application, featuring a Clean Finance UI design with dark sidebar, KPI cards, and modern transactions table.

## 📸 Features

### Visual Design
- **Dark Sidebar** (#1E293B) with navigation menu and company selector
- **KPI Cards** displaying financial metrics (Ingresos, Gastos, ITBIS Neto, A Pagar)
- **Modern Table** with transaction badges and filters
- **Month/Year Filters** for data visualization
- **Clean Finance UI** styling matching modern SaaS applications

### Functionality
- ✅ Complete controller integration preserving all business logic
- ✅ Firebase configuration and migration dialogs
- ✅ SQL backup functionality
- ✅ Tax calculation manager integration
- ✅ Monthly reports integration
- ✅ Transaction filtering (Todos, Ingresos, Gastos)
- ✅ Company switching
- ✅ Double-click diagnostics

## 🚀 Quick Start

### Option 1: Demo Mode (No Database Required)
```bash
python3 demo_modern_gui.py
```

### Option 2: With Real Database
```bash
python3 launch_modern_gui.py
```

### Option 3: Programmatic Usage
```python
from modern_gui import ModernMainWindow, STYLESHEET
from logic_qt import LogicControllerQt
from PyQt6.QtWidgets import QApplication

app = QApplication([])
app.setStyleSheet(STYLESHEET)

controller = LogicControllerQt('facturas_db.db')
window = ModernMainWindow(controller)
window.show()

app.exec()
```

## 📦 Installation

### Dependencies
```bash
pip install PyQt6 qtawesome
```

### Files Included
- `modern_gui.py` - Main modern dashboard UI (41KB)
- `firebase_config_dialog.py` - Firebase configuration (9KB)
- `migration_dialog.py` - SQLite to Firebase migration (13KB)
- `demo_modern_gui.py` - Interactive demo with sample data (9KB)
- `launch_modern_gui.py` - Real database launcher (3KB)
- `test_modern_gui.py` - Comprehensive test suite (11KB)
- `MODERN_GUI_README.md` - Detailed documentation (8KB)
- `IMPLEMENTATION_SUMMARY.md` - Implementation details (8KB)

## 🎯 Key Components

### Sidebar Navigation
```
┌─────────────────────────┐
│ [F] Facturas Pro       │
├─────────────────────────┤
│ EMPRESA ACTIVA         │
│ ┌─────────────────────┐│
│ │ Zoec Civil Srl    ▼││
│ └─────────────────────┘│
├─────────────────────────┤
│ ◉ Dashboard            │
│   Ingresos             │
│   Gastos               │
│   Calc. Impuestos      │
│   Reportes             │
├─────────────────────────┤
│ ⚙ Configuración        │
└─────────────────────────┘
```

### KPI Cards
```
┌────────────────┬────────────────┬────────────────┬────────────────┐
│ Total Ingresos │ Total Gastos   │ ITBIS Neto     │ A Pagar        │
│ RD$ 1,250,000  │ RD$ 450,000    │ RD$ 144,000    │ RD$ 144,000    │
│ ITBIS: 225,000 │ ITBIS: 81,000  │ (Diferencia)   │ (Estimado)     │
└────────────────┴────────────────┴────────────────┴────────────────┘
```

### Transactions Table
```
┌─────────────────────────────────────────────────────────────────────┐
│ Transacciones Recientes              [Todos] [Ingresos] [Gastos]   │
├──────────┬─────────┬────────────┬─────────────┬──────────┬─────────┤
│ Fecha    │ Tipo    │ No. Fact.  │ Tercero     │ ITBIS    │ Total   │
├──────────┼─────────┼────────────┼─────────────┼──────────┼─────────┤
│ 2025-10  │ INGRESO │ E31000239  │ Barnhouse...│ 12,000   │ 78,000  │
│ 2025-10  │ GASTO   │ B01000512  │ Ferretería..│ 450      │ 2,950   │
└──────────┴─────────┴────────────┴─────────────┴──────────┴─────────┘
```

## 🔧 Configuration

### Herramientas Menu
1. **Configurar Firebase...** - Set up Firebase credentials and storage
2. **Migrar SQLite → Firebase...** - One-time data migration
3. **Crear backup SQL manual** - Create SQL backup (30-day retention)

### Controller Integration
The modern UI integrates with the existing `LogicControllerQt` controller:

#### Required Methods
- `get_all_companies()` → list[dict]
- `get_dashboard_data(company_id, filter_month, filter_year)` → dict
- `set_active_company(name)`

#### Optional Methods
- `_open_tax_calculation_manager()` - Tax calculations
- `_open_report_window()` - Monthly reports
- `open_add_invoice_window()` - New invoice dialog
- `diagnose_row(number=...)` - Diagnostics
- `get_sqlite_db_path()` → str
- `create_sql_backup(retention_days)` → str
- `get_setting(key, default)` / `set_setting(key, value)`

## 🧪 Testing

Run the comprehensive test suite:
```bash
QT_QPA_PLATFORM=offscreen python3 test_modern_gui.py
```

Expected output:
```
✅ TEST 1: Module Imports - PASSED
✅ TEST 2: Mock Controller Integration - PASSED
✅ TEST 3: UI Component Validation - PASSED
✅ TEST 4: Dialog Validation - PASSED
```

## 📖 Documentation

- **MODERN_GUI_README.md** - Complete usage guide and API reference
- **IMPLEMENTATION_SUMMARY.md** - Implementation details and architecture
- **This README** - Quick start and overview

## 🎨 Design Specifications

### Colors
- Background: `#F8F9FA` (Light gray)
- Sidebar: `#1E293B` (Dark slate)
- Primary: `#3B82F6` (Blue)
- Income: `#10B981` (Green)
- Expense: `#EF4444` (Red)
- Net ITBIS: `#2563EB` (Blue)
- Payable: `#F59E0B` (Orange)

### Typography
- Font: Inter / Segoe UI / Roboto
- Base size: 10pt
- Headers: Bold, 18-20px
- KPI values: Bold, 24px

### Layout
- Sidebar: Fixed 250px width
- Content: Fluid, expandable
- Cards: 12px border radius, subtle shadow
- Table: No vertical gridlines, row hover effect

## 🔮 Future Enhancements

### Firebase Integration
The dialogs are ready for Firebase Admin SDK integration:
- Real-time data synchronization with Firestore
- Cloud Storage for attachments
- Automatic daily SQL backups with 30-day retention

### UI Enhancements
- Trend indicators on KPI cards (↑↓)
- Sparkline charts for historical data
- Drag-and-drop card arrangement
- Dark/light theme toggle
- Advanced date range picker
- Multi-field search and filtering

## 🐛 Troubleshooting

### Icons Not Showing
Install qtawesome:
```bash
pip install qtawesome
```
The UI works without icons (text-only fallback).

### Database Not Found
Ensure `facturas_db.db` exists in the current directory or specify the path:
```python
controller = LogicControllerQt('/path/to/facturas_db.db')
```

### Qt Platform Plugin Error
For headless environments, use:
```bash
QT_QPA_PLATFORM=offscreen python3 your_script.py
```

## 📄 License

This implementation follows the same license as the parent FACTURAS-PyQT6-GIT project.

## 🙏 Acknowledgments

- UI design inspired by Clean Finance UI patterns
- Icons via Font Awesome (qtawesome)
- Built with PyQt6

---

**Ready to use!** Start with `python3 demo_modern_gui.py` to see the modern dashboard in action.
