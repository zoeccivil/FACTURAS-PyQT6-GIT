import sys
import os
from typing import Optional

from PyQt6.QtWidgets import QApplication, QFileDialog

import firebase_admin
from firebase_admin import credentials, firestore


def select_credentials_file() -> Optional[str]:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Selecciona el archivo de credenciales de Firebase (service account JSON)",
        "",
        "JSON files (*.json);;Todos los archivos (*.*)",
    )
    if not file_path:
        print("No se seleccionaron credenciales.")
        return None
    return file_path


def init_firestore(creds_path: str):
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credenciales no encontradas: {creds_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        print(f"[DEBUG] Firebase inicializado con: {creds_path}")
    else:
        print("[DEBUG] Firebase ya estaba inicializado.")
    return firestore.client()


def get_last_invoices(db, collection_name: str = "invoices", limit: int = 5):
    """
    Obtiene las últimas 'limit' facturas guardadas en la colección 'invoices'.

    Intenta ordenar por:
      1) created_at (si existe)
      2) created (si existe)
      3) _created_at (si existe)
      4) invoice_date (string) descendente como fallback
    """
    col_ref = db.collection(collection_name)

    # Intentar distintos campos de fecha de creación, en orden de preferencia
    possible_order_fields = ["created_at", "created", "_created_at", "invoice_date"]

    for field in possible_order_fields:
        try:
            print(f"[DEBUG] Probando orden por campo '{field}'...")
            query = col_ref.order_by(field, direction=firestore.Query.DESCENDING).limit(limit)
            docs = list(query.stream())
            if docs:
                print(f"[DEBUG] Usando campo de orden '{field}', docs encontrados: {len(docs)}")
                return docs, field
        except Exception as e:
            # Puede fallar si el campo no existe en todos los docs, probamos el siguiente
            print(f"[DEBUG] No se pudo ordenar por '{field}': {e}")
            continue

    # Si todo falla, devolvemos los primeros 'limit' sin orden explícito
    print("[DEBUG] No se pudo ordenar por ningún campo conocido, devolviendo documentos sin orden.")
    docs = list(col_ref.limit(limit).stream())
    return docs, None


def main():
    creds_path = select_credentials_file()
    if not creds_path:
        return

    db = init_firestore(creds_path)

    docs, order_field = get_last_invoices(db, collection_name="invoices", limit=5)

    print("\n=== ÚLTIMAS FACTURAS ENCONTRADAS ===")
    print(f"(Ordenadas por: {order_field if order_field else 'sin orden explícito'})\n")

    for doc in docs:
        data = doc.to_dict() or {}

        company_id = data.get("company_id")
        inv_num = data.get("invoice_number") or data.get("número_de_factura")
        invoice_date = data.get("invoice_date") or data.get("fecha")
        invoice_type = data.get("invoice_type") or data.get("tipo_de_factura")
        third_party = data.get("third_party_name") or data.get("empresa_a_la_que_se_emitió")

        attachment_path = data.get("attachment_path")
        storage_path = data.get("attachment_storage_path") or data.get("storage_path")

        created_at = (
            data.get("created_at")
            or data.get("created")
            or data.get("_created_at")
        )

        print(
            f"- doc_id                = {doc.id}\n"
            f"  company_id           = {company_id}\n"
            f"  invoice_number       = {inv_num}\n"
            f"  invoice_date         = {invoice_date}\n"
            f"  invoice_type         = {invoice_type}\n"
            f"  third_party_name     = {third_party}\n"
            f"  created_at_like      = {created_at}\n"
            f"  attachment_path      = {attachment_path}\n"
            f"  attachment_storage_path = {storage_path}\n"
        )

    print("=== FIN LISTADO ===")


if __name__ == "__main__":
    main()