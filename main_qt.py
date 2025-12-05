import sys
from PyQt6.QtWidgets import QApplication
from app_gui_qt import MainApplicationQt
from modern_gui import ModernDashboard

from logic_qt import LogicControllerQt
import os
import json

def main():
    # Lee facturas_config desde config.json si existe
    config = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    db_path = config.get("facturas_config") or config.get("database_path", "facturas_db.db")
    
    # Check if modern UI should be used (default: True)
    use_modern_ui = config.get("use_modern_ui", True)

    app = QApplication(sys.argv)
    logic = LogicControllerQt(db_path)
    
    # Create main window based on preference
    if use_modern_ui:
        main_win = ModernDashboard(logic)
    else:
        main_win = MainApplicationQt(logic)
    
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()