import json
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

# Carpeta y archivo donde guardaremos la ruta al JSON de Firebase
CONFIG_DIR = Path.home() / ".gestion_facturas"
CONFIG_FILE = CONFIG_DIR / "firebase_firebase_settings.json"


def ensure_firebase_config(parent=None) -> dict | None:
    """
    Verifica que exista una configuración de Firebase.
    Si no existe (o está corrupta), abre un diálogo para elegir el JSON
    de credenciales y guarda la configuración.

    Devuelve:
        dict con al menos {"service_account_json": "ruta_absoluta"} o
        None si el usuario cancela o falla algo grave.
    """
    # 1) Si ya existe, intentar leerla
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("service_account_json") and os.path.exists(
                cfg["service_account_json"]
            ):
                return cfg
        except Exception:
            # si está corrupto, seguimos como si no existiera
            pass

    # 2) No hay config válida → pedir JSON
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    QMessageBox.information(
        parent,
        "Configuración de Firebase",
        "No se encontró una configuración válida de Firebase.\n\n"
        "A continuación se te pedirá que selecciones el archivo JSON "
        "de credenciales de servicio de Firebase.",
    )

    json_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Seleccionar archivo JSON de Firebase (service account)",
        "",
        "Archivos JSON (*.json);;Todos los archivos (*.*)",
    )
    if not json_path:
        QMessageBox.warning(
            parent,
            "Configuración",
            "No se seleccionó ningún archivo de configuración de Firebase.\n"
            "La aplicación se cerrará.",
        )
        return None

    json_path = os.path.abspath(json_path)

    cfg = {
        "service_account_json": json_path,
    }

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Configuración",
            f"No se pudo guardar la configuración de Firebase:\n{e}",
        )
        return None

    QMessageBox.information(
        parent,
        "Configuración",
        "Configuración de Firebase creada correctamente.\n"
        "Puedes cambiar este archivo luego en:\n"
        f"{CONFIG_FILE}",
    )

    return cfg