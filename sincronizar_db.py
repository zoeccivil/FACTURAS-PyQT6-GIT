import sqlite3

# --- CONFIGURACIÓN ---
# Define los nombres de tus archivos
DB_ORIGEN = 'facturas_db.db'
DB_DESTINO = 'facturas_db-2.db' # Esta será la Base de Datos Final actualizada

# Define el nombre de la tabla que quieres sincronizar
NOMBRE_TABLA = 'invoices'
# El nombre de la columna que sirve como identificador único (ID)
COLUMNA_ID = 'id'
# ---------------------

def obtener_ids_existentes(conexion_destino, nombre_tabla, columna_id):
    """Obtiene una lista de todos los IDs presentes en la tabla de destino."""
    print(f"-> Obteniendo IDs existentes en la tabla '{nombre_tabla}' de la DB Destino...")
    cursor = conexion_destino.cursor()
    try:
        cursor.execute(f"SELECT {columna_id} FROM {nombre_tabla}")
        # Retorna un conjunto (set) para una búsqueda de IDs más rápida
        ids_existentes = {fila[0] for fila in cursor.fetchall()}
        print(f"   {len(ids_existentes)} IDs encontrados en la base de datos destino.")
        return ids_existentes
    except sqlite3.OperationalError as e:
        print(f"   [ERROR] No se pudo leer la tabla '{nombre_tabla}' en la DB Destino. Asegúrate de que el nombre de la tabla sea correcto.")
        print(f"   Detalle del error: {e}")
        return set()

def obtener_registros_faltantes(conexion_origen, nombre_tabla, columna_id, ids_existentes):
    """Obtiene los registros del Origen cuyos IDs no están en la lista de IDs existentes."""
    if not ids_existentes:
        # Si no hay IDs en el destino, trae todos los registros del origen
        print(f"-> DB Destino vacía o no se pudieron obtener IDs. Obteniendo todos los registros del Origen...")
        sql_select = f"SELECT * FROM {nombre_tabla}"
    else:
        print(f"-> Filtrando registros en DB Origen para encontrar los faltantes...")
        # Convierte los IDs a una cadena para la cláusula IN/NOT IN
        # Usamos '?' para la lista de IDs para evitar inyección SQL (aunque el ID sea interno)
        # SQLite tiene un límite de 999 para la lista de parámetros,
        # pero para simplicidad usaremos un enfoque que cubre la mayoría de los casos.
        # Si tienes millones de IDs, esto debería manejarse en lotes.
        ids_tuple = tuple(ids_existentes)
        # Crea la parte de la consulta SQL con la condición de los IDs faltantes
        # Usamos una consulta dinámica con PLACEHOLDERS (?)
        placeholders = ','.join('?' for _ in ids_tuple)

        # La consulta selecciona todos los registros del Origen (DB_ORIGEN)
        # cuyo ID *NO* esté en la lista de IDs de la Destino (ids_existentes).
        sql_select = f"SELECT * FROM {nombre_tabla} WHERE {columna_id} NOT IN ({placeholders})"

    cursor_origen = conexion_origen.cursor()
    if ids_existentes:
        cursor_origen.execute(sql_select, ids_tuple)
    else:
        cursor_origen.execute(sql_select)

    registros_faltantes = cursor_origen.fetchall()
    print(f"   {len(registros_faltantes)} registros faltantes identificados.")
    return registros_faltantes, cursor_origen.description

def insertar_registros(conexion_destino, nombre_tabla, registros, esquema_tabla):
    """Inserta los registros faltantes en la tabla de destino."""
    if not registros:
        print("-> No hay registros nuevos para insertar. Sincronización completa.")
        return

    print(f"-> Insertando {len(registros)} registros nuevos en la DB Destino...")

    cursor_destino = conexion_destino.cursor()
    
    # 1. Obtener los nombres de las columnas para construir la sentencia INSERT
    # La descripción contiene tuplas (nombre_columna, tipo,...)
    nombres_columnas = [columna[0] for columna in esquema_tabla]
    columnas_str = ', '.join(nombres_columnas)
    
    # 2. Crear los placeholders para los valores (tantos como columnas)
    placeholders = ', '.join(['?' for _ in nombres_columnas])
    
    sql_insert = f"INSERT INTO {nombre_tabla} ({columnas_str}) VALUES ({placeholders})"

    try:
        # Usamos executemany para insertar todos los registros de manera eficiente
        cursor_destino.executemany(sql_insert, registros)
        conexion_destino.commit()
        print(f"   ¡Inserción exitosa! Se han añadido {len(registros)} nuevos registros.")
    except Exception as e:
        print(f"   [ERROR] Error durante la inserción: {e}")
        conexion_destino.rollback() # Revierte los cambios si hay un error

def sincronizar_bases_de_datos():
    """Función principal que ejecuta el proceso de sincronización."""
    conn_origen = None
    conn_destino = None
    
    try:
        # Conexión a la base de datos Origen (modo solo lectura es más seguro)
        conn_origen = sqlite3.connect(f"file:{DB_ORIGEN}?mode=ro", uri=True)
        # Conexión a la base de datos Destino (modo lectura/escritura)
        conn_destino = sqlite3.connect(DB_DESTINO)

        # 1. Obtener IDs del Destino
        ids_destino = obtener_ids_existentes(conn_destino, NOMBRE_TABLA, COLUMNA_ID)
        
        # 2. Obtener registros faltantes del Origen
        registros_nuevos, esquema = obtener_registros_faltantes(conn_origen, NOMBRE_TABLA, COLUMNA_ID, ids_destino)
        
        # 3. Insertar registros en el Destino
        insertar_registros(conn_destino, NOMBRE_TABLA, registros_nuevos, esquema)
        
        print("\n✨ ¡Proceso de sincronización completado! ✨")
        print(f"La base de datos final es: {DB_DESTINO}")

    except Exception as e:
        print(f"\n[ERROR CRÍTICO] Un error interrumpió la sincronización: {e}")
        
    finally:
        # Asegurarse de cerrar las conexiones
        if conn_origen:
            conn_origen.close()
        if conn_destino:
            conn_destino.close()

if __name__ == "__main__":
    sincronizar_bases_de_datos()