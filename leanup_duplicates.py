import sqlite3
import os

# --- CONFIGURACIÓN ---
# Asegúrate de que este sea el nombre correcto de tu archivo de base de datos.
# Reemplaza 'facturas_bd.db' si tu archivo se llama diferente.
DB_FILE = 'progain_database.db'
# -------------------

def find_and_clean_duplicates(db_path):
    """
    Encuentra y elimina facturas duplicadas de la base de datos,
    conservando siempre el registro más antiguo de cada grupo.
    """
    if not os.path.exists(db_path):
        print(f"Error: No se encontró el archivo de base de datos '{db_path}'.")
        print("Por favor, revisa el nombre del archivo en la variable DB_FILE dentro del script.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Consulta para encontrar todos los grupos de facturas duplicadas
    find_dupes_query = """
        SELECT company_id, rnc, invoice_number, COUNT(*)
        FROM invoices
        GROUP BY company_id, rnc, invoice_number
        HAVING COUNT(*) > 1;
    """
    
    cursor.execute(find_dupes_query)
    duplicate_groups = cursor.fetchall()

    if not duplicate_groups:
        print("¡Buenas noticias! No se encontraron facturas duplicadas en tu base de datos.")
        conn.close()
        return

    print(f"Se encontraron {len(duplicate_groups)} grupos de facturas duplicadas. Procediendo a la limpieza...")
    total_deleted = 0

    # 2. Iterar sobre cada grupo para limpiarlo
    for group in duplicate_groups:
        company_id, rnc, invoice_number, count = group
        print(f"\n--- Limpiando duplicados para RNC: {rnc}, Factura: {invoice_number} ---")
        
        # Obtener los IDs de todas las facturas en este grupo, ordenadas de la más antigua a la más nueva
        get_ids_query = """
            SELECT id FROM invoices
            WHERE company_id = ? AND rnc = ? AND invoice_number = ?
            ORDER BY id ASC;
        """
        cursor.execute(get_ids_query, (company_id, rnc, invoice_number))
        all_ids = [row[0] for row in cursor.fetchall()]

        # El primer ID de la lista es el original, el que conservaremos.
        id_to_keep = all_ids[0]
        ids_to_delete = all_ids[1:]
        
        print(f"  Se conservará el registro con ID: {id_to_keep}")
        print(f"  Se eliminarán los registros duplicados con IDs: {ids_to_delete}")

        # 3. Construir y ejecutar la consulta de eliminación
        if ids_to_delete:
            placeholders = ', '.join('?' for _ in ids_to_delete)
            delete_query = f"DELETE FROM invoices WHERE id IN ({placeholders});"
            
            cursor.execute(delete_query, ids_to_delete)
            total_deleted += len(ids_to_delete)

    # 4. Guardar todos los cambios de forma permanente en la base de datos
    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print("¡Limpieza completada!")
    print(f"Se eliminaron un total de {total_deleted} registros duplicados.")
    print("Tu base de datos ahora está limpia.")
    print("Puedes ejecutar tu programa principal ('main.py') de nuevo.")

if __name__ == '__main__':
    find_and_clean_duplicates(DB_FILE)