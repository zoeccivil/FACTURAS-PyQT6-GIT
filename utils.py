# Archivo nuevo: utils.py

import os
import json

def find_dropbox_folder():
    """
    Encuentra la ruta de la carpeta de Dropbox personal en Windows.
    Busca en las ubicaciones estándar del archivo de configuración de Dropbox.
    Devuelve la ruta como un string o None si no se encuentra.
    """
    info_path_options = [
        os.path.join(os.getenv('APPDATA'), 'Dropbox', 'info.json'),
        os.path.join(os.getenv('LOCALAPPDATA'), 'Dropbox', 'info.json')
    ]

    for info_path in info_path_options:
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r') as f:
                    data = json.load(f)
                    # La ruta está anidada dentro de la clave 'personal'
                    path = data.get('personal', {}).get('path')
                    if path and os.path.isdir(path):
                        return path
            except (json.JSONDecodeError, KeyError):
                # El archivo podría estar corrupto o tener un formato inesperado
                continue
    return None