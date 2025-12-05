# Crea este nuevo archivo: config_manager.py

import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    """Carga la configuración desde config.json."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Archivo corrupto o vacío
    return {}

def save_config(data):
    """Guarda un diccionario de datos en config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_db_path():
    """Obtiene la ruta de la BD desde el config, o devuelve None."""
    config = load_config()
    path = config.get("database_path")
    # Verificamos que la ruta guardada todavía exista
    if path and os.path.exists(path):
        return path
    return None

def set_db_path(path):
    """Guarda la nueva ruta de la BD en el config."""
    config = load_config()
    config["database_path"] = path
    save_config(config)


def get_firebase_config():
    """Obtiene la configuración de Firebase desde el config, o devuelve None."""
    config = load_config()
    return config.get("firebase_config")


def set_firebase_config(credentials_path, bucket_name):
    """Guarda la configuración de Firebase en el config."""
    config = load_config()
    config["firebase_config"] = {
        "credentials_path": credentials_path,
        "bucket_name": bucket_name
    }
    save_config(config)