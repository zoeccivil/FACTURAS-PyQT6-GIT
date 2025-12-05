#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
Run this to diagnose any import issues before running the main application.
"""

import sys

def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ {description}: OK")
        return True
    except Exception as e:
        print(f"✗ {description}: FAILED")
        print(f"  Error: {e}")
        return False

def main():
    print("Testing imports for Facturas Pro...\n")
    
    all_ok = True
    
    # Test core dependencies
    print("Core Dependencies:")
    all_ok &= test_import("PyQt6.QtWidgets", "PyQt6")
    all_ok &= test_import("PyQt6.QtCore", "PyQt6 Core")
    all_ok &= test_import("PyQt6.QtGui", "PyQt6 GUI")
    all_ok &= test_import("pandas", "pandas")
    all_ok &= test_import("openpyxl", "openpyxl")
    
    print("\nOptional Dependencies:")
    test_import("firebase_admin", "Firebase Admin (optional)")
    test_import("qtawesome", "qtawesome (optional - for icons)")
    
    print("\nApplication Modules:")
    all_ok &= test_import("logic_qt", "Logic Controller")
    all_ok &= test_import("config_manager", "Config Manager")
    all_ok &= test_import("app_gui_qt", "Classic GUI")
    all_ok &= test_import("modern_gui", "Modern Dashboard")
    
    print("\nWindow Modules:")
    all_ok &= test_import("add_invoice_window_qt", "Add Invoice Window")
    all_ok &= test_import("add_expense_window_qt", "Add Expense Window")
    all_ok &= test_import("settings_window_qt", "Settings Window")
    all_ok &= test_import("report_window_qt", "Report Window")
    all_ok &= test_import("company_management_window_qt", "Company Management")
    
    print("\nFirebase & Backup Modules:")
    all_ok &= test_import("firebase_client", "Firebase Client")
    all_ok &= test_import("firebase_config_dialog", "Firebase Config Dialog")
    all_ok &= test_import("migration_dialog", "Migration Dialog")
    all_ok &= test_import("backup_manager", "Backup Manager")
    all_ok &= test_import("backup_dialog", "Backup Dialog")
    
    print("\n" + "="*50)
    if all_ok:
        print("✓ All required imports successful!")
        print("\nYou can now run the application with:")
        print("  python main_qt.py")
    else:
        print("✗ Some imports failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
