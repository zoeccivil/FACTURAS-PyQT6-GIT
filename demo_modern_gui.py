#!/usr/bin/env python3
"""
Visual Demo - Modern GUI for Facturas Pro
This script creates a visual demonstration of the modern UI with sample data.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from modern_gui import ModernMainWindow, STYLESHEET


class DemoController:
    """Demo controller with realistic sample data"""
    
    def __init__(self):
        self.db_path = "/tmp/demo.db"
        self.current_company = "Zoec Civil Srl"
    
    def get_all_companies(self):
        """Return sample companies"""
        return [
            {'id': 1, 'name': 'Zoec Civil Srl', 'rnc': '132045678'},
            {'id': 2, 'name': 'Barnhouse Services Srl', 'rnc': '430167890'},
            {'id': 3, 'name': 'Fedasa Srl', 'rnc': '501234567'},
            {'id': 4, 'name': 'Exselicon Srl', 'rnc': '601345678'},
        ]
    
    def get_dashboard_data(self, company_id, filter_month=None, filter_year=None):
        """Return sample dashboard data matching the HTML example"""
        return {
            'summary': {
                'total_ingresos': 1250000.00,
                'itbis_ingresos': 225000.00,
                'total_gastos': 450000.00,
                'itbis_gastos': 81000.00,
                'total_neto': 800000.00,
                'itbis_neto': 144000.00
            },
            'all_transactions': [
                {
                    'id': 1,
                    'invoice_date': '2025-10-14',
                    'invoice_type': 'emitida',
                    'invoice_number': 'E3100000239',
                    'third_party_name': 'Barnhouse Services Srl',
                    'itbis': 12000.00,
                    'exchange_rate': 1.0,
                    'total_amount': 78000.00,
                    'total_amount_rd': 78000.00,
                    'currency': 'RD$'
                },
                {
                    'id': 2,
                    'invoice_date': '2025-10-12',
                    'invoice_type': 'gasto',
                    'invoice_number': 'B0100005512',
                    'third_party_name': 'Ferretería Americana',
                    'itbis': 450.00,
                    'exchange_rate': 1.0,
                    'total_amount': 2950.00,
                    'total_amount_rd': 2950.00,
                    'currency': 'RD$'
                },
                {
                    'id': 3,
                    'invoice_date': '2025-10-10',
                    'invoice_type': 'emitida',
                    'invoice_number': 'E3100000240',
                    'third_party_name': 'Constructora ABC',
                    'itbis': 18000.00,
                    'exchange_rate': 1.0,
                    'total_amount': 118000.00,
                    'total_amount_rd': 118000.00,
                    'currency': 'RD$'
                },
                {
                    'id': 4,
                    'invoice_date': '2025-10-08',
                    'invoice_type': 'gasto',
                    'invoice_number': 'G4567890',
                    'third_party_name': 'Distribuidora XYZ',
                    'itbis': 2700.00,
                    'exchange_rate': 1.0,
                    'total_amount': 17700.00,
                    'total_amount_rd': 17700.00,
                    'currency': 'RD$'
                },
                {
                    'id': 5,
                    'invoice_date': '2025-10-05',
                    'invoice_type': 'emitida',
                    'invoice_number': 'E3100000241',
                    'third_party_name': 'Hotel Paradise',
                    'itbis': 9000.00,
                    'exchange_rate': 1.0,
                    'total_amount': 59000.00,
                    'total_amount_rd': 59000.00,
                    'currency': 'RD$'
                },
                {
                    'id': 6,
                    'invoice_date': '2025-10-03',
                    'invoice_type': 'gasto',
                    'invoice_number': 'G7890123',
                    'third_party_name': 'Oficina Moderna',
                    'itbis': 540.00,
                    'exchange_rate': 1.0,
                    'total_amount': 3540.00,
                    'total_amount_rd': 3540.00,
                    'currency': 'RD$'
                },
                {
                    'id': 7,
                    'invoice_date': '2025-10-01',
                    'invoice_type': 'emitida',
                    'invoice_number': 'E3100000242',
                    'third_party_name': 'Desarrollo Urbano SA',
                    'itbis': 36000.00,
                    'exchange_rate': 1.0,
                    'total_amount': 236000.00,
                    'total_amount_rd': 236000.00,
                    'currency': 'RD$'
                },
            ]
        }
    
    def set_active_company(self, name):
        """Set active company"""
        self.current_company = name
        print(f"[Demo] Active company: {name}")
    
    def get_setting(self, key, default=None):
        """Get setting"""
        settings = {
            'firebase_enabled': 'false',
            'firebase_credentials_path': '',
            'firebase_storage_bucket': '',
            'firebase_project_id': ''
        }
        return settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set setting"""
        print(f"[Demo] Setting {key} = {value}")
    
    def get_sqlite_db_path(self):
        """Get SQLite DB path"""
        return self.db_path
    
    def create_sql_backup(self, retention_days=30):
        """Create SQL backup"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"/tmp/facturas_backup_{timestamp}.sql"
        print(f"[Demo] Creating backup: {backup_path}")
        print(f"[Demo] Retention: {retention_days} days")
        return backup_path
    
    def _open_tax_calculation_manager(self):
        """Placeholder for tax calculation manager"""
        print("[Demo] Opening tax calculation manager...")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Calc. Impuestos",
            "Esta es una demostración del Modern GUI.\n\n"
            "En la aplicación real, este botón abrirá la ventana\n"
            "de gestión de cálculos de impuestos y retenciones."
        )
    
    def _open_report_window(self):
        """Placeholder for reports"""
        print("[Demo] Opening report window...")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Reportes",
            "Esta es una demostración del Modern GUI.\n\n"
            "En la aplicación real, este botón abrirá la ventana\n"
            "de reportes mensuales."
        )
    
    def open_add_invoice_window(self):
        """Placeholder for add invoice"""
        print("[Demo] Opening add invoice window...")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            None,
            "Nueva Factura",
            "Esta es una demostración del Modern GUI.\n\n"
            "En la aplicación real, este botón abrirá el formulario\n"
            "para registrar una nueva factura (ingreso o gasto)."
        )
    
    def diagnose_row(self, number=None):
        """Diagnostic placeholder"""
        print(f"[Demo] Diagnosing invoice: {number}")


def main():
    """Launch demo"""
    print("=" * 70)
    print("FACTURAS PRO - MODERN DASHBOARD DEMO")
    print("=" * 70)
    print("\nThis demo showcases the modern UI with sample data.")
    print("\nFeatures demonstrated:")
    print("  • Clean Finance UI design")
    print("  • Dark sidebar with navigation")
    print("  • KPI cards with financial metrics")
    print("  • Modern transactions table")
    print("  • Month/Year filtering")
    print("  • Transaction type filters (Todos/Ingresos/Gastos)")
    print("  • Company selector")
    print("  • Herramientas menu (Firebase config, Migration, Backup)")
    print("\nNote: This is a visual demonstration. Click buttons to see placeholders.")
    print("=" * 70 + "\n")
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    # Create demo controller and window
    controller = DemoController()
    window = ModernMainWindow(controller)
    
    # Show window
    window.show()
    
    print("Demo window launched!")
    print("Close the window to exit.\n")
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
