import sys
from PyQt6.QtWidgets import QApplication
from app_gui_qt import MainApplicationQt
from modern_gui import ModernMainWindow as ModernDashboard
from logic_qt import LogicControllerQt
from theme import apply_app_theme  # Importamos el tema global

import os
import json

def main():
    # Leer configuración desde config.json si existe
    config = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}
    db_path = config.get("facturas_config") or config.get("database_path", "facturas_db.db")
    
    # Decidir si usar la UI moderna
    use_modern_ui = config.get("use_modern_ui", True)

    # Crear aplicación y aplicar el tema
    app = QApplication(sys.argv)
    apply_app_theme(app)  # Aplica el tema global definido en theme.py

    # Crear controlador de lógica
    logic = LogicControllerQt(db_path)
    
    # Crear ventana principal según configuración
    if use_modern_ui:
        main_win = ModernDashboard(logic)
    else:
        main_win = MainApplicationQt(logic)
    
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()