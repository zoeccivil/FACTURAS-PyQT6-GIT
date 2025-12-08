#!/usr/bin/env python3
"""
Script de inspección de backends para FACTURAS-PyQT6-GIT.

Este script permite:
1. Seleccionar un archivo de credenciales Firebase (JSON de service account).
2. Seleccionar un archivo de base de datos SQLite (.db).
3. Mostrar:
   - Las tablas presentes en SQLite y un ejemplo de fila de cada una.
   - Las colecciones presentes en Firestore y un ejemplo de documento de cada una.

Úsalo para entender cómo mapear tablas ↔ colecciones antes de afinar logic_firebase.
"""

import os
import json
import sqlite3
import sys
from typing import List

from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception as e:
    firebase_admin = None
    credentials = None
    firestore = None


def select_file(caption: str, filter_str: str) -> str:
    """Abre un QFileDialog para seleccionar un archivo y devuelve la ruta."""
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        caption,
        "",
        filter_str,
    )
    return file_path or ""


def inspect_sqlite(db_path: str) -> None:
    """Lista tablas e imprime una fila de ejemplo por tabla."""
    if not db_path or not os.path.exists(db_path):
        print(f"[SQLITE] Archivo no encontrado: {db_path}")
        return

    print("\n" + "=" * 60)
    print(f"[SQLITE] Inspeccionando base de datos: {db_path}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Listar tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row["name"] for row in cur.fetchall()]
        if not tables:
            print("[SQLITE] No se encontraron tablas.")
            return

        print(f"[SQLITE] Tablas encontradas ({len(tables)}):")
        for t in tables:
            print(f"  • {t}")

        print("\n[SQLITE] Ejemplo de datos por tabla:")
        for t in tables:
            try:
                cur.execute(f"SELECT * FROM {t} LIMIT 3;")
                rows = cur.fetchall()
                print(f"\n  Tabla: {t}")
                if not rows:
                    print("    (sin filas)")
                    continue
                for r in rows:
                    print("    " + json.dumps(dict(r), ensure_ascii=False))
            except Exception as e:
                print(f"    (error leyendo tabla {t}: {e})")

        conn.close()
    except Exception as e:
        print(f"[SQLITE] Error inspeccionando la base de datos: {e}")


def inspect_firestore(cred_path: str) -> None:
    """Inicializa Firebase y lista colecciones y documentos de ejemplo."""
    if firebase_admin is None or credentials is None or firestore is None:
        print("[FIREBASE] firebase_admin / firestore no está instalado.")
        return

    if not cred_path or not os.path.exists(cred_path):
        print(f"[FIREBASE] Archivo de credenciales no encontrado: {cred_path}")
        return

    print("\n" + "=" * 60)
    print(f"[FIREBASE] Inspeccionando Firestore con credenciales: {cred_path}")
    print("=" * 60)

    # Cargar credenciales
    try:
        with open(cred_path, "r", encoding="utf-8") as f:
            cred_data = json.load(f)
        project_id = cred_data.get("project_id")
    except Exception as e:
        print(f"[FIREBASE] Error leyendo credenciales: {e}")
        return

    if not project_id:
        print("[FIREBASE] El archivo de credenciales no contiene project_id.")
        return

    try:
        cred = credentials.Certificate(cred_path)
        # Para evitar chocar con el app principal, usamos un nombre de app distinto
        app = None
        try:
            app = firebase_admin.get_app("inspect_app")
        except ValueError:
            app = firebase_admin.initialize_app(cred, {"projectId": project_id}, name="inspect_app")

        db = firestore.client(app=app)
        print(f"[FIREBASE] Proyecto: {project_id}")

        # Listar colecciones raíz
        collections = list(db.collections())
        if not collections:
            print("[FIREBASE] No se encontraron colecciones.")
            return

        print(f"[FIREBASE] Colecciones encontradas ({len(collections)}):")
        for c in collections:
            print(f"  • {c.id}")

        print("\n[FIREBASE] Ejemplo de documentos por colección (máx 3 cada una):")
        for c in collections:
            print(f"\n  Colección: {c.id}")
            try:
                docs = list(c.limit(3).stream())
                if not docs:
                    print("    (sin documentos)")
                    continue
                for d in docs:
                    data = d.to_dict() or {}
                    data["_id"] = d.id
                    print("    " + json.dumps(data, ensure_ascii=False))
            except Exception as e:
                print(f"    (error leyendo colección {c.id}: {e})")

    except Exception as e:
        print(f"[FIREBASE] Error inspeccionando Firestore: {e}")


def main():
    app = QApplication(sys.argv)

    # Elegir archivo de credenciales Firebase
    cred_path = select_file(
        "Seleccionar credenciales Firebase (service account JSON)",
        "Archivos JSON (*.json);;Todos los archivos (*.*)",
    )
    if not cred_path:
        QMessageBox.warning(None, "Inspección cancelada", "No se seleccionó archivo de credenciales.")
        return 1

    # Elegir archivo de base de datos SQLite
    db_path = select_file(
        "Seleccionar base de datos SQLite",
        "SQLite Database (*.db *.sqlite *.sqlite3);;Todos los archivos (*.*)",
    )
    if not db_path:
        QMessageBox.warning(None, "Inspección cancelada", "No se seleccionó archivo de base de datos.")
        return 1

    # Ejecutar inspecciones
    inspect_sqlite(db_path)
    inspect_firestore(cred_path)

    QMessageBox.information(
        None,
        "Inspección completada",
        "Se ha impreso en consola la estructura de la base de datos SQLite\n"
        "y las colecciones de Firestore.\n\n"
        "Revisa la terminal para ver los detalles."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())