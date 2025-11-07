import sys
from PyQt6.QtWidgets import QApplication
from app_gui_qt import MainApplicationQt

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
    db_path = config.get("facturas_config", "database.db")

    app = QApplication(sys.argv)
    logic = LogicControllerQt(db_path)
    main_win = MainApplicationQt(logic)
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()