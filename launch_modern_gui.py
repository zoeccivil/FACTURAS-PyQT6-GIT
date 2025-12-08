#!/usr/bin/env python3
"""
Launcher for the modern GUI using the Firebase logic controller.

Esta versión usa LogicControllerFirebase como backend principal.
Si Firestore no puede inicializarse, intenta guiar al usuario para
configurar el JSON de Firebase en primer arranque (y no romper).
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox

from modern_gui import ModernMainWindow, STYLESHEET
from firebase_config_bootstrap import ensure_firebase_config


def main():
    """Main entry point for the modern GUI application (Firebase backend)."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # 1) Intentar importar LogicControllerFirebase
    try:
        from logic_firebase import LogicControllerFirebase
    except ImportError as e:
        QMessageBox.critical(
            None,
            "Error de importación",
            f"No se pudo importar logic_firebase:\n{e}\n\n"
            "Asegúrate de que logic_firebase.py existe y no tiene errores de sintaxis."
        )
        return 1

    controller = None

    # 2) Primer intento: inicializar sin config explícita (como antes)
    try:
        controller = LogicControllerFirebase()
    except Exception:
        controller = None

    # 3) Si no hay _db, entonces pedimos JSON al usuario y reintentamos
    if controller is None or getattr(controller, "_db", None) is None:
        cfg = ensure_firebase_config(parent=None)
        if cfg is None:
            # Usuario canceló o no se pudo guardar config
            return 1

        service_json = cfg.get("service_account_json")

        try:
            # Reintentar con la ruta al JSON (ajusta el nombre del parámetro
            # según tu implementación de LogicControllerFirebase)
            controller = LogicControllerFirebase(service_account_json_path=service_json)
        except TypeError:
            # Si tu __init__ usa otro nombre o detecta el JSON vía settings,
            # simplemente reintenta sin parámetros, sabiendo que la ruta
            # ya quedó guardada en un archivo global que logic_firebase leerá.
            try:
                controller = LogicControllerFirebase()
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "Firebase no configurado",
                    f"No se pudo inicializar la conexión con Firebase "
                    f"usando el JSON seleccionado:\n{e}",
                )
                return 1
        except Exception as e:
            QMessageBox.critical(
                None,
                "Firebase no configurado",
                f"No se pudo inicializar la conexión con Firebase "
                f"usando el JSON seleccionado:\n{e}",
            )
            return 1

    # 4) Verificación mínima: Firestore inicializado
    if getattr(controller, "_db", None) is None:
        QMessageBox.critical(
            None,
            "Firebase no configurado",
            "No se pudo inicializar la conexión con Firebase.\n\n"
            "Verifica la configuración en:\n"
            "  • Herramientas → Configurar Firebase...\n\n"
            "Asegúrate de que:\n"
            "  • El archivo de credenciales existe.\n"
            "  • El project_id es correcto.\n"
        )
        return 1

    # 5) Lanzar ventana principal
    window = ModernMainWindow(controller)
    window.show()

    return app.exec()


if __name__ == "__main__":
    print("Modern GUI launched (Firebase backend).")
    sys.exit(main())