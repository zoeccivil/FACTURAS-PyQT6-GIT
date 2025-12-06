# Modern GUI - Facturas Pro

## Overview

This implementation provides a modern, clean dashboard UI for the Facturas Pro application, inspired by contemporary SaaS finance applications. The design maintains all existing business logic while providing an enhanced user experience.

## Files Created

### 1. `modern_gui.py`
The main modern dashboard interface with:
- **Dark sidebar** (#1E293B) with navigation menu
- **Company selector** with modern styling
- **KPI cards** displaying financial metrics (Ingresos, Gastos, ITBIS Neto, A Pagar)
- **Modern transactions table** with type badges and filters
- **Month/Year filters** for data visualization
- **Complete controller integration** preserving all existing business logic

### 2. `firebase_config_dialog.py`
Firebase configuration dialog for:
- Setting up Firebase credentials (JSON file)
- Configuring Storage bucket and Project ID
- Testing Firebase connection
- Saving configuration to controller settings

### 3. `migration_dialog.py`
SQLite to Firebase migration dialog with:
- Database file selection
- Migration options (companies, invoices, third parties, attachments)
- Progress tracking with worker thread
- Non-blocking UI during migration

## Key Features

### Visual Design (Clean Finance UI)
- **Sidebar**: Dark slate (#1E293B) with white text and blue active states (#3B82F6)
- **Cards**: White background, subtle borders (#E2E8F0), 12px border radius
- **Typography**: Inter/Segoe UI/Roboto at 10pt base
- **Colors**:
  - Income: Green (#10B981)
  - Expense: Red (#EF4444)
  - Net ITBIS: Blue (#2563EB)
  - Payable: Orange border (#F59E0B)

### Navigation
- **Dashboard** - Main financial summary view
- **Ingresos** - Filter to show only income transactions
- **Gastos** - Filter to show only expense transactions
- **Calc. Impuestos** - Opens tax calculation manager (`_open_tax_calculation_manager`)
- **Reportes** - Opens monthly report window (`_open_report_window`)
- **Configuración** - Opens Firebase configuration dialog

### Herramientas Menu
1. **Configurar Firebase...** - Set up Firebase credentials and settings
2. **Migrar SQLite → Firebase...** - Migrate existing SQLite data to Firebase
3. **Crear backup SQL manual** - Create manual SQL backup (30-day retention)

### Controller Integration

The modern UI integrates seamlessly with the existing controller (`LogicControllerQt` from `logic_qt.py`):

#### Required Methods (from app_gui_qt.py)
- `get_all_companies()` or `get_companies()` → list[dict] with 'id' and 'name'
- `get_dashboard_data(company_id, filter_month, filter_year)` → dict with 'summary' and 'all_transactions'
- `set_active_company(name)` - Called when company selector changes
- `_open_tax_calculation_manager()` - Opens tax calculation window
- `_open_report_window()` - Opens monthly report window

#### Optional Methods
- `open_add_invoice_window()` - Opens new invoice dialog
- `diagnose_row(number=...)` - Diagnostic tool for transactions (double-click)
- `get_sqlite_db_path()` → str - Returns SQLite database path for migration
- `create_sql_backup(retention_days=30)` → str - Creates SQL backup
- `on_firebase_config_updated()` - Callback after Firebase config is saved

### Data Structure

#### Dashboard Data Expected Format
```python
{
    "summary": {
        "total_ingresos": float,
        "total_gastos": float,
        "itbis_ingresos": float,
        "itbis_gastos": float,
        "total_neto": float,
        "itbis_neto": float
    },
    "all_transactions": [
        {
            "id": int,
            "invoice_date": str,  # YYYY-MM-DD
            "invoice_type": str,  # 'emitida' or 'gasto'
            "invoice_number": str,
            "third_party_name": str,
            "itbis": float,
            "exchange_rate": float,
            "total_amount": float,
            "total_amount_rd": float,
            "currency": str
        },
        ...
    ]
}
```

## Usage

### Running with Existing Controller

```python
from modern_gui import ModernMainWindow, STYLESHEET
from logic_qt import LogicControllerQt
from PyQt6.QtWidgets import QApplication
import sys

# Create application
app = QApplication(sys.argv)
app.setStyleSheet(STYLESHEET)

# Create controller
controller = LogicControllerQt('facturas_db.db')

# Create and show modern window
window = ModernMainWindow(controller)
window.show()

sys.exit(app.exec())
```

### Running Demo Mode

```python
from modern_gui import run_demo

# Will attempt to find database or create mock controller
run_demo()
```

### Running from Command Line

```bash
# With offscreen rendering (headless environments)
QT_QPA_PLATFORM=offscreen python3 modern_gui.py

# With display
python3 modern_gui.py
```

## Dependencies

### Required
- **PyQt6** - Core GUI framework
- **Python 3.7+** - Minimum Python version

### Optional
- **qtawesome** - Icon support (gracefully degrades to text-only if not available)

### Installation
```bash
pip install PyQt6 qtawesome
```

## Architecture Decisions

### 1. Preservation of Business Logic
All business logic from `app_gui_qt.py` is preserved. The modern UI acts as a view layer, delegating all data operations to the existing controller.

### 2. Firebase Integration
- Firebase is designed to be the primary data source
- SQLite is retained for daily automatic backups (30-day retention)
- Migration dialog provides one-time data migration from SQLite to Firebase
- Firebase configuration is stored in controller settings

### 3. Icon Handling
Icons use qtawesome with fallback to text-only mode:
```python
try:
    import qtawesome as qta
    icon = qta.icon('fa5s.chart-pie', color='white')
    button.setIcon(icon)
except:
    # Gracefully degrade to text-only
    button.setText("  Dashboard")
```

### 4. Responsive Layout
- Sidebar: Fixed 250px width
- Content area: Expands to fill remaining space
- Table columns: Mix of fixed, content-based, and stretch sizing
- KPI cards: Grid layout with equal distribution

## Testing

The implementation includes comprehensive testing:

```python
# Test imports
from modern_gui import ModernMainWindow, STYLESHEET
from firebase_config_dialog import show_firebase_config_dialog
from migration_dialog import show_migration_dialog

# Test with mock controller
class MockController:
    def get_all_companies(self):
        return [{'id': 1, 'name': 'Test Company'}]
    
    def get_dashboard_data(self, company_id, filter_month=None, filter_year=None):
        return {
            'summary': {...},
            'all_transactions': [...]
        }

app = QApplication([])
app.setStyleSheet(STYLESHEET)
window = ModernMainWindow(MockController())
# Test passes if window creates without error
```

## Future Enhancements

### Potential Additions
1. **Real Firebase Integration**
   - Implement Firebase Admin SDK integration
   - Real-time data synchronization
   - Cloud Storage for attachments

2. **Enhanced KPI Cards**
   - Trend indicators (↑↓)
   - Sparkline charts
   - Comparison with previous period

3. **Advanced Filtering**
   - Date range picker
   - Search functionality
   - Multi-field filters

4. **Dashboard Customization**
   - Drag-and-drop card arrangement
   - User preferences for default view
   - Customizable color themes

## Troubleshooting

### Icons Not Showing
If icons don't appear, ensure qtawesome is installed:
```bash
pip install qtawesome
```

The UI will work without icons (text-only mode).

### Firebase Dialogs Not Opening
Ensure `firebase_config_dialog.py` and `migration_dialog.py` are in the same directory as `modern_gui.py`.

### Controller Method Not Found
If a controller method is missing, the UI will show a warning dialog but continue functioning. Implement the missing method in your controller class.

## License

This implementation follows the same license as the parent FACTURAS-PyQT6-GIT project.

## Credits

- UI Design inspired by Clean Finance UI patterns
- Icons provided by Font Awesome (via qtawesome)
- Built with PyQt6
