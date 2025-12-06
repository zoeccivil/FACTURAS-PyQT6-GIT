#!/usr/bin/env python3
"""
Test script for modern_gui.py
Validates all components and functionality
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from modern_gui import ModernMainWindow, STYLESHEET, run_demo
        print("✅ modern_gui.py imported successfully")
        print(f"   - STYLESHEET: {len(STYLESHEET)} characters")
        
        from firebase_config_dialog import show_firebase_config_dialog, FirebaseConfigDialog
        print("✅ firebase_config_dialog.py imported successfully")
        
        from migration_dialog import show_migration_dialog, MigrationDialog
        print("✅ migration_dialog.py imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_mock_controller():
    """Test with a mock controller"""
    print("\n" + "=" * 60)
    print("TEST 2: Mock Controller Integration")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from modern_gui import ModernMainWindow, STYLESHEET
        
        # Create mock controller
        class MockController:
            def __init__(self):
                self.db_path = "/tmp/test.db"
            
            def get_all_companies(self):
                return [
                    {'id': 1, 'name': 'Zoec Civil Srl', 'rnc': '123456789'},
                    {'id': 2, 'name': 'Barnhouse Services Srl', 'rnc': '987654321'},
                    {'id': 3, 'name': 'Fedasa Srl', 'rnc': '555666777'}
                ]
            
            def get_dashboard_data(self, company_id, filter_month=None, filter_year=None):
                return {
                    'summary': {
                        'total_ingresos': 1250000.0,
                        'itbis_ingresos': 225000.0,
                        'total_gastos': 450000.0,
                        'itbis_gastos': 81000.0,
                        'total_neto': 800000.0,
                        'itbis_neto': 144000.0
                    },
                    'all_transactions': [
                        {
                            'id': 1,
                            'invoice_date': '2025-10-14',
                            'invoice_type': 'emitida',
                            'invoice_number': 'E3100000239',
                            'third_party_name': 'Barnhouse Services Srl',
                            'itbis': 12000.0,
                            'exchange_rate': 1.0,
                            'total_amount': 78000.0,
                            'total_amount_rd': 78000.0,
                            'currency': 'RD$'
                        },
                        {
                            'id': 2,
                            'invoice_date': '2025-10-12',
                            'invoice_type': 'gasto',
                            'invoice_number': 'B0100005512',
                            'third_party_name': 'Ferretería Americana',
                            'itbis': 450.0,
                            'exchange_rate': 1.0,
                            'total_amount': 2950.0,
                            'total_amount_rd': 2950.0,
                            'currency': 'RD$'
                        },
                        {
                            'id': 3,
                            'invoice_date': '2025-10-10',
                            'invoice_type': 'emitida',
                            'invoice_number': 'E3100000240',
                            'third_party_name': 'Cliente XYZ',
                            'itbis': 5400.0,
                            'exchange_rate': 1.0,
                            'total_amount': 35400.0,
                            'total_amount_rd': 35400.0,
                            'currency': 'RD$'
                        },
                        {
                            'id': 4,
                            'invoice_date': '2025-10-08',
                            'invoice_type': 'gasto',
                            'invoice_number': 'G1234567',
                            'third_party_name': 'Proveedor ABC',
                            'itbis': 900.0,
                            'exchange_rate': 1.0,
                            'total_amount': 5900.0,
                            'total_amount_rd': 5900.0,
                            'currency': 'RD$'
                        }
                    ]
                }
            
            def set_active_company(self, name):
                print(f"   [Controller] Active company set to: {name}")
            
            def get_setting(self, key, default=None):
                settings = {
                    'firebase_enabled': 'false',
                    'firebase_credentials_path': '',
                    'firebase_storage_bucket': '',
                    'firebase_project_id': ''
                }
                return settings.get(key, default)
            
            def set_setting(self, key, value):
                print(f"   [Controller] Setting {key} = {value}")
            
            def get_sqlite_db_path(self):
                return self.db_path
            
            def create_sql_backup(self, retention_days=30):
                import datetime
                backup_path = f"/tmp/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                print(f"   [Controller] Creating backup at {backup_path}")
                return backup_path
        
        # Create app and window
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        app.setStyleSheet(STYLESHEET)
        
        controller = MockController()
        window = ModernMainWindow(controller)
        
        print("✅ ModernMainWindow created successfully")
        print(f"   - Title: {window.windowTitle()}")
        print(f"   - Size: {window.width()}x{window.height()}")
        print(f"   - Companies loaded: {len(window.companies_list)}")
        print(f"   - Transactions loaded: {len(window.all_current_transactions)}")
        
        # Test company selector
        print("\n   Testing company selector...")
        window.company_selector.setCurrentIndex(1)
        print(f"   - Selected company: {window.company_selector.currentText()}")
        
        # Test filter buttons
        print("\n   Testing transaction filters...")
        window._set_transaction_filter("Ingresos")
        print(f"   - Income filter: {window.table.rowCount()} rows")
        
        window._set_transaction_filter("Gastos")
        print(f"   - Expense filter: {window.table.rowCount()} rows")
        
        window._set_transaction_filter("Todos")
        print(f"   - All transactions: {window.table.rowCount()} rows")
        
        print("\n✅ All controller integration tests passed")
        
        return True, window, app
        
    except Exception as e:
        import traceback
        print(f"❌ Controller integration test failed: {e}")
        traceback.print_exc()
        return False, None, None


def test_ui_components(window):
    """Test UI component accessibility"""
    print("\n" + "=" * 60)
    print("TEST 3: UI Component Validation")
    print("=" * 60)
    
    try:
        # Check sidebar components
        assert window.company_selector is not None, "Company selector not found"
        print("✅ Company selector found")
        
        assert window.nav_buttons is not None, "Navigation buttons not found"
        print(f"✅ Navigation buttons found: {len(window.nav_buttons)} items")
        
        # Check content area components
        assert window.section_title is not None, "Section title not found"
        print("✅ Section title found")
        
        assert window.month_combo is not None, "Month combo not found"
        assert window.year_combo is not None, "Year combo not found"
        print("✅ Filter combos found")
        
        # Check KPI cards
        assert window.card_income is not None, "Income card not found"
        assert window.card_expense is not None, "Expense card not found"
        assert window.card_net is not None, "Net ITBIS card not found"
        assert window.card_payable is not None, "Payable card not found"
        print("✅ All KPI cards found")
        
        # Check transactions table
        assert window.table is not None, "Transactions table not found"
        print("✅ Transactions table found")
        
        assert window.filter_buttons is not None, "Filter buttons not found"
        print(f"✅ Filter buttons found: {len(window.filter_buttons)} items")
        
        print("\n✅ All UI components validated successfully")
        return True
        
    except AssertionError as e:
        print(f"❌ UI component validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dialogs(window):
    """Test dialog accessibility (without showing them)"""
    print("\n" + "=" * 60)
    print("TEST 4: Dialog Validation")
    print("=" * 60)
    
    try:
        from firebase_config_dialog import FirebaseConfigDialog
        from migration_dialog import MigrationDialog
        
        # Test Firebase config dialog creation
        firebase_dlg = FirebaseConfigDialog(window)
        print("✅ Firebase config dialog can be created")
        
        # Test migration dialog creation
        migration_dlg = MigrationDialog(window, "/tmp/test.db")
        print("✅ Migration dialog can be created")
        
        print("\n✅ All dialogs validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Dialog validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MODERN GUI COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ FAILED: Import test failed")
        return 1
    
    # Test 2: Mock controller
    success, window, app = test_mock_controller()
    if not success:
        print("\n❌ FAILED: Mock controller test failed")
        return 1
    
    # Test 3: UI components
    if not test_ui_components(window):
        print("\n❌ FAILED: UI component validation failed")
        return 1
    
    # Test 4: Dialogs
    if not test_dialogs(window):
        print("\n❌ FAILED: Dialog validation failed")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ All tests passed successfully!")
    print("\nModern GUI is ready for use.")
    print("\nTo run the GUI:")
    print("  python3 modern_gui.py")
    print("\nOr import and use in your application:")
    print("  from modern_gui import ModernMainWindow")
    print("  window = ModernMainWindow(controller)")
    print("  window.show()")
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
