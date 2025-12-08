import sys
import sqlite3
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QInputDialog,
)

import firebase_admin
from firebase_admin import credentials, firestore


def choose_file(parent, caption: str, filter_str: str) -> Optional[str]:
    path, _ = QFileDialog.getOpenFileName(parent, caption, "", filter_str)
    return path or None


def ask_table_name(parent, title: str, prompt: str, choices: list[str]) -> Optional[str]:
    """
    Muestra un diálogo simple para elegir o escribir el nombre de una tabla.
    """
    if not choices:
        # No hay sugerencias, pedir texto libre
        text, ok = QInputDialog.getText(parent, title, prompt)
        return text if ok and text.strip() else None

    text, ok = QInputDialog.getItem(
        parent,
        title,
        prompt,
        choices,
        editable=True,
    )
    if not ok or not text.strip():
        return None
    return text.strip()


def load_tables(sqlite_path: str) -> list[str]:
    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def migrate(
    parent,
    sqlite_path: str,
    cred_path: str,
    calc_table: str,
    details_table: str,
) -> None:
    # ------------------------------------------------------------------ #
    # Inicializar Firebase Admin
    # ------------------------------------------------------------------ #
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Error Firebase",
            f"No se pudo inicializar Firebase Admin:\n{e}",
        )
        return

    # ------------------------------------------------------------------ #
    # Abrir SQLite
    # ------------------------------------------------------------------ #
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Error SQLite",
            f"No se pudo abrir la base de datos SQLite:\n{e}",
        )
        return

    migrated = 0
    failed = 0

    try:
        cur = conn.cursor()

        # Leer todos los cálculos
        try:
            cur.execute(f"SELECT * FROM {calc_table}")
            calc_rows = cur.fetchall()
        except Exception as e:
            QMessageBox.critical(
                parent,
                "Error leyendo cálculos",
                f"No se pudo leer la tabla '{calc_table}':\n{e}",
            )
            return

        if not calc_rows:
            QMessageBox.information(
                parent,
                "Sin datos",
                f"La tabla '{calc_table}' no tiene registros para migrar.",
            )
            return

        # Intentar adivinar campos comunes
        def row_to_calc_dict(r: sqlite3.Row) -> Dict[str, Any]:
            d = dict(r)
            # Normalización de nombres típicos
            out: Dict[str, Any] = {}
            out["id"] = d.get("id") or d.get("calc_id") or d.get("calculation_id")

            out["company_id"] = d.get("company_id")
            out["name"] = d.get("name") or d.get("calc_name") or d.get("title")
            out["start_date"] = d.get("start_date")
            out["end_date"] = d.get("end_date")
            out["percent_to_pay"] = (
                d.get("percent_to_pay")
                or d.get("percent")
                or d.get("porcentaje_a_pagar")
            )
            out["created_at"] = d.get("creation_date") or d.get("created_at")
            out["updated_at"] = d.get("updated_at") or d.get("modified_at")
            return out

        def details_for_calc(calc_id) -> list[Dict[str, Any]]:
            """
            Devuelve lista de dicts con {invoice_id, selected, retention}
            para un cálculo dado.
            """
            cur2 = conn.cursor()
            try:
                cur2.execute(
                    f"SELECT * FROM {details_table} WHERE calculation_id = ?",
                    (calc_id,),
                )
                rows = cur2.fetchall()
            except Exception:
                # Intentar otros nombres comunes
                try:
                    cur2.execute(
                        f"SELECT * FROM {details_table} WHERE calc_id = ?",
                        (calc_id,),
                    )
                    rows = cur2.fetchall()
                except Exception:
                    rows = []

            results: list[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                inv_id = (
                    d.get("invoice_id")
                    or d.get("factura_id")
                    or d.get("invoice")
                )
                selected = d.get("selected")
                retention = (
                    d.get("retention")
                    or d.get("has_retention")
                    or d.get("retencion_itbis")
                )
                # Normalizar booleans (0/1, '0'/'1', etc.)
                def to_bool(v):
                    if v is None:
                        return False
                    if isinstance(v, bool):
                        return v
                    try:
                        return bool(int(v))
                    except Exception:
                        return str(v).lower() in ("true", "t", "yes", "y", "si")

                results.append(
                    {
                        "invoice_id": inv_id,
                        "selected": to_bool(selected),
                        "retention": to_bool(retention),
                    }
                )
            return results

        # ------------------------------------------------------------------ #
        # Migrar cada cálculo
        # ------------------------------------------------------------------ #
        for r in calc_rows:
            try:
                calc = row_to_calc_dict(r)
                calc_id = calc.get("id")
                if calc_id is None:
                    failed += 1
                    continue

                # Documento principal en tax_calculations
                doc_ref = db.collection("tax_calculations").document(str(calc_id))

                main_payload: Dict[str, Any] = {
                    "company_id": calc.get("company_id"),
                    "name": calc.get("name"),
                    "start_date": calc.get("start_date"),
                    "end_date": calc.get("end_date"),
                    "percent_to_pay": float(calc.get("percent_to_pay") or 0.0),
                    "created_at": calc.get("created_at"),
                    "updated_at": calc.get("updated_at") or calc.get("created_at"),
                }

                # Limpiar None vacíos que no quieras:
                main_payload = {
                    k: v for k, v in main_payload.items() if v is not None
                }

                doc_ref.set(main_payload)

                # Subcolección details
                dets = details_for_calc(calc_id)
                for det in dets:
                    inv_id = det.get("invoice_id")
                    if inv_id is None:
                        continue
                    det_ref = doc_ref.collection("details").document(str(inv_id))
                    det_ref.set(
                        {
                            "invoice_id": inv_id,
                            "selected": bool(det.get("selected", False)),
                            "retention": bool(det.get("retention", False)),
                        }
                    )

                migrated += 1
            except Exception as e:
                print(f"[MIGRATE] Error migrando cálculo {r}: {e}")
                failed += 1

    finally:
        conn.close()

    QMessageBox.information(
        parent,
        "Migración finalizada",
        f"Cálculos migrados correctamente: {migrated}\n"
        f"Cálculos con error: {failed}",
    )


def main():
    app = QApplication(sys.argv)

    # 1) Seleccionar base de datos SQLite
    sqlite_path = choose_file(
        None,
        "Seleccionar base de datos SQLite antigua",
        "SQLite DB (*.db *.sqlite *.sqlite3);;Todos los archivos (*.*)",
    )
    if not sqlite_path:
        return

    # 2) Seleccionar credenciales Firebase (service account JSON)
    cred_path = choose_file(
        None,
        "Seleccionar credenciales de Firebase (Service Account JSON)",
        "JSON Files (*.json);;Todos los archivos (*.*)",
    )
    if not cred_path:
        return

    # 3) Leer tablas disponibles
    try:
        tables = load_tables(sqlite_path)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error",
            f"No se pudieron listar las tablas de SQLite:\n{e}",
        )
        return

    if not tables:
        QMessageBox.critical(
            None,
            "Sin tablas",
            "La base de datos SQLite no contiene tablas.",
        )
        return

    # 4) Elegir tabla de cálculos
    calc_table = ask_table_name(
        None,
        "Tabla de Cálculos",
        "Selecciona (o escribe) el nombre de la tabla de CÁLCULOS de impuestos:",
        tables,
    )
    if not calc_table:
        return

    # 5) Elegir tabla de detalles
    details_table = ask_table_name(
        None,
        "Tabla de Detalles",
        "Selecciona (o escribe) el nombre de la tabla de DETALLES de cálculos:",
        tables,
    )
    if not details_table:
        return

    # Confirmación
    reply = QMessageBox.question(
        None,
        "Confirmar migración",
        f"Base SQLite:\n  {sqlite_path}\n\n"
        f"Tabla de cálculos: {calc_table}\n"
        f"Tabla de detalles: {details_table}\n\n"
        f"¿Deseas iniciar la migración a Firestore (colección 'tax_calculations')?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    # 6) Ejecutar migración
    migrate(None, sqlite_path, cred_path, calc_table, details_table)


if __name__ == "__main__":
    main()