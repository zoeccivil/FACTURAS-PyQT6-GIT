import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox

def select_db_file():
    root = tk.Tk()
    root.withdraw()
    db_path = filedialog.askopenfilename(
        title="Seleccionar la base de datos SQLite a limpiar",
        filetypes=[("Bases de datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
    )
    root.destroy()
    return db_path

def clean_invoices(db_path):
    if not db_path:
        print("No se seleccionó ninguna base de datos.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Elimina registros que no sean 'emitida' o 'gasto'
    cur.execute("DELETE FROM invoices WHERE invoice_type NOT IN ('emitida', 'gasto')")

    # 2. Elimina facturas sin número de factura
    cur.execute("DELETE FROM invoices WHERE invoice_number IS NULL OR invoice_number = ''")

    # 3. Si existe la tabla companies, elimina facturas con company_id inexistente
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
        if cur.fetchone():
            cur.execute("DELETE FROM invoices WHERE company_id NOT IN (SELECT id FROM companies)")
    except Exception as e:
        print("No se pudo validar company_id. Detalle:", e)

    # 4. Elimina duplicados por (company_id, invoice_number, rnc)
    cur.execute("""
        DELETE FROM invoices
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM invoices
            GROUP BY company_id, invoice_number, rnc
        )
    """)

    conn.commit()
    conn.close()
    print("Limpieza completada.")
    messagebox.showinfo("Limpieza completada", "La limpieza de la base de datos finalizó correctamente.")

if __name__ == "__main__":
    db_file = select_db_file()
    clean_invoices(db_file)