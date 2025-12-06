#!/usr/bin/env python3
"""
Example launcher for the modern GUI with real controller.
This shows how to integrate modern_gui.py with the existing application.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from modern_gui import ModernMainWindow, STYLESHEET


def find_database():
    """Find the database file in common locations"""
    possible_paths = [
        'facturas_db.db',
        './facturas_db.db',
        os.path.join(os.path.dirname(__file__), 'facturas_db.db'),
        '/home/runner/work/FACTURAS-PyQT6-GIT/FACTURAS-PyQT6-GIT/facturas_db.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def main():
    """Main entry point for the modern GUI application"""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Apply modern stylesheet
    app.setStyleSheet(STYLESHEET)
    
    # Find database
    db_path = find_database()
    
    if not db_path:
        QMessageBox.warning(
            None,
            "Database Not Found",
            "No se encontró la base de datos facturas_db.db\n\n"
            "Por favor, asegúrate de que el archivo existe en el directorio actual."
        )
        return 1
    
    try:
        # Import and create controller
        from logic_qt import LogicControllerQt
        
        print(f"Loading database: {db_path}")
        controller = LogicControllerQt(db_path)
        
        # Create and show modern window
        window = ModernMainWindow(controller)
        window.show()
        
        print("Modern GUI launched successfully!")
        print("=" * 60)
        print("FACTURAS PRO - MODERN DASHBOARD")
        print("=" * 60)
        print(f"Database: {db_path}")
        print(f"Window Size: {window.width()}x{window.height()}")
        print("\nFeatures:")
        print("  • Dark sidebar with navigation")
        print("  • Real-time KPI cards")
        print("  • Modern transactions table")
        print("  • Firebase integration ready")
        print("  • Month/Year filtering")
        print("\nMenu Herramientas:")
        print("  • Configurar Firebase...")
        print("  • Migrar SQLite → Firebase...")
        print("  • Crear backup SQL manual")
        print("=" * 60)
        
        # Run the application
        return app.exec()
        
    except ImportError as e:
        QMessageBox.critical(
            None,
            "Import Error",
            f"No se pudo importar el controlador:\n{e}\n\n"
            "Asegúrate de que logic_qt.py existe."
        )
        return 1
    except Exception as e:
        import traceback
        QMessageBox.critical(
            None,
            "Error",
            f"Error al iniciar la aplicación:\n{e}\n\n{traceback.format_exc()}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
