import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

import firebase_admin
from firebase_admin import credentials, firestore, storage


class InvoiceCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Verificar adjuntos migrados (invoices/1712, 2401)")
        self.root.geometry("700x400")

        self.credentials_path = None
        self.db = None
        self.bucket = None

        self._build_ui()

    def _build_ui(self):
        frm_top = tk.Frame(self.root)
        frm_top.pack(fill=tk.X, padx=10, pady=10)

        # Botón para elegir credenciales
        btn_cred = tk.Button(
            frm_top,
            text="Seleccionar credenciales JSON...",
            command=self._select_credentials,
        )
        btn_cred.grid(row=0, column=0, sticky="w")

        self.lbl_cred = tk.Label(frm_top, text="Sin archivo seleccionado", fg="#2563EB")
        self.lbl_cred.grid(row=0, column=1, sticky="w", padx=8)

        # Entrada para bucket
        tk.Label(frm_top, text="Bucket de Storage:").grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )
        self.entry_bucket = tk.Entry(frm_top, width=50)
        self.entry_bucket.grid(row=1, column=1, sticky="w", pady=(10, 0))
        self.entry_bucket.insert(0, "")  # puedes poner un valor por defecto aquí

        # Botón para ejecutar la verificación
        btn_check = tk.Button(
            frm_top,
            text="Verificar invoices/1712 y 2401",
            command=self._on_check_clicked,
        )
        btn_check.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        # Área de log
        self.txt_output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.txt_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _select_credentials(self):
        path = filedialog.askopenfilename(
            title="Selecciona el archivo JSON de credenciales de Firebase",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        self.credentials_path = path
        self.lbl_cred.config(text=path)

    def _append_log(self, text: str):
        self.txt_output.insert(tk.END, text + "\n")
        self.txt_output.see(tk.END)

    def _init_firebase(self):
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Credenciales no encontradas: {self.credentials_path}"
            )

        bucket_name = self.entry_bucket.get().strip()
        if not bucket_name:
            raise ValueError("Debes indicar el nombre del bucket de Storage.")

        if not firebase_admin._apps:
            with open(self.credentials_path, "r", encoding="utf-8") as f:
                j = json.load(f)
            project_id = j.get("project_id")

            options = {}
            if project_id:
                options["projectId"] = project_id
            if bucket_name:
                options["storageBucket"] = bucket_name

            cred = credentials.Certificate(self.credentials_path)
            firebase_admin.initialize_app(cred, options)

        self.db = firestore.client()
        self.bucket = storage.bucket(bucket_name)

    def _check_invoice(self, invoice_id: str):
        doc_ref = self.db.collection("invoices").document(invoice_id)
        doc = doc_ref.get()

        if not doc.exists:
            self._append_log(f"[X] El documento invoices/{invoice_id} NO existe.")
            self._append_log("-" * 40)
            return

        data = doc.to_dict() or {}
        inv_num = data.get("invoice_number") or data.get("número_de_factura")
        asp = data.get("attachment_storage_path")
        ap = data.get("attachment_path")

        self._append_log(f"=== invoices/{invoice_id} ===")
        self._append_log(f"invoice_number          : {inv_num}")
        self._append_log(f"attachment_path (local) : {ap}")
        self._append_log(f"attachment_storage_path : {asp}")
        self._append_log("-" * 40)

    def _on_check_clicked(self):
        self.txt_output.delete("1.0", tk.END)

        if not self.credentials_path:
            messagebox.showwarning(
                "Falta credenciales",
                "Primero selecciona el archivo JSON de credenciales.",
            )
            return

        try:
            self._init_firebase()
        except Exception as e:
            messagebox.showerror("Error inicializando Firebase", str(e))
            return

        self._append_log("Conexión a Firebase OK.")
        self._append_log("Consultando invoices/1712 y invoices/2401...\n")

        ids_to_check = ["1712", "2401"]
        for doc_id in ids_to_check:
            self._check_invoice(doc_id)


def main():
    root = tk.Tk()
    app = InvoiceCheckerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()