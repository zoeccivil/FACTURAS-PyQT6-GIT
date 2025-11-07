# logic.py
import sqlite3
import os
import json
import datetime
from tkinter import simpledialog
# En el archivo: logic.py (al inicio)
from utils import find_dropbox_folder

class LogicControllerQt:
    """
    Maneja toda la lógica de negocio y la interacción con la base de datos.
    """
    def __init__(self, db_path):
        """
        Inicializa el controlador y establece la conexión con la base de datos.
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_db()

    def _connect(self):
        """Establece la conexión a la base de datos SQLite."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print("Conexión a la base de datos establecida exitosamente.")
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos: {e}")
            self.conn = None


# En el archivo: logic.py

# REEMPLAZA ESTE MÉTODO COMPLETO
    def _initialize_db(self):
        """
        Realiza todas las migraciones de esquema necesarias y luego
        crea las tablas si no existen, incluyendo todos los índices.
        """
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()

            # --- MIGRACIONES DE ESQUEMA (se ejecutan si es necesario) ---
            # (El código de migraciones anteriores no cambia)
            cursor.execute("PRAGMA table_info(companies);")
            company_columns = [info['name'] for info in cursor.fetchall()]
            
            if 'rnc' not in company_columns:
                print("Ejecutando migración avanzada para añadir la columna 'rnc'...")
                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute('''CREATE TABLE companies_new (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, rnc TEXT UNIQUE, address TEXT, legacy_filename TEXT, itbis_adelantado REAL DEFAULT 0.0);''')
                cursor.execute('''INSERT INTO companies_new (id, name, legacy_filename, itbis_adelantado) SELECT id, name, legacy_filename, itbis_adelantado FROM companies;''')
                cursor.execute('DROP TABLE companies;')
                cursor.execute('ALTER TABLE companies_new RENAME TO companies;')
                self.conn.commit()
                print("Migración de 'companies' para 'rnc' completada.")
                cursor.execute("PRAGMA table_info(companies);")
                company_columns = [info['name'] for info in cursor.fetchall()]

            if 'address' not in company_columns:
                print("Ejecutando migración: Añadiendo 'address' a la tabla 'companies'...")
                cursor.execute("ALTER TABLE companies ADD COLUMN address TEXT;")
                self.conn.commit()
                print("Migración de 'companies' para 'address' completada.")

            cursor.execute("PRAGMA table_info(invoices);")
            invoice_columns = [info['name'] for info in cursor.fetchall()]
            if 'attachment_path' not in invoice_columns:
                print("Ejecutando migración: Añadiendo 'attachment_path' a 'invoices'...")
                cursor.execute("ALTER TABLE invoices ADD COLUMN attachment_path TEXT;")
                self.conn.commit()
                print("Migración de 'invoices' completada.")

            # --- CREACIÓN DE TABLAS (si no existen) ---
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
                rnc TEXT UNIQUE, address TEXT, legacy_filename TEXT,
                itbis_adelantado REAL DEFAULT 0.0
            );''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL,
                invoice_type TEXT NOT NULL, invoice_date TEXT NOT NULL,
                imputation_date TEXT, invoice_number TEXT NOT NULL,
                invoice_category TEXT, rnc TEXT, third_party_name TEXT,
                currency TEXT, itbis REAL DEFAULT 0.0, total_amount REAL DEFAULT 0.0,
                exchange_rate REAL DEFAULT 1.0, total_amount_rd REAL DEFAULT 0.0,
                attachment_path TEXT,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            );''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS third_parties (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT NOT NULL UNIQUE, name TEXT NOT NULL COLLATE NOCASE);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS currencies (name TEXT PRIMARY KEY);''')
            
            # <<-- NUEVAS TABLAS PARA CÁLCULOS GUARDADOS -->>
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                percent_to_pay REAL DEFAULT 0.0,
                creation_date TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            );''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_calculation_details (
                calculation_id INTEGER NOT NULL,
                invoice_id INTEGER NOT NULL,
                itbis_retention_applied INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (calculation_id, invoice_id),
                FOREIGN KEY (calculation_id) REFERENCES tax_calculations (id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
            );''')
            
            # --- CREACIÓN DE ÍNDICES (si no existen) ---
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_third_parties_name ON third_parties (name);")
            cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_invoice 
            ON invoices (company_id, rnc, invoice_number);
            ''')
            
            # --- DATOS INICIALES ---
            cursor.execute("INSERT OR IGNORE INTO currencies (name) VALUES ('RD$'), ('USD');")
            
            self.conn.commit()
            print("Base de datos inicializada correctamente.")
        except sqlite3.Error as e:
            print(f"Error al inicializar o migrar las tablas: {e}")
            self.conn.rollback()


# <<-- AÑADE ESTOS NUEVOS MÉTODOS AL FINAL DE LA CLASE LogicController -->>

    def save_tax_calculation(self, calc_id, company_id, name, start_date, end_date, percent, details):
        """Guarda o actualiza una configuración de cálculo de impuestos."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            if calc_id: # Actualizar
                cursor.execute("""
                    UPDATE tax_calculations 
                    SET name = ?, start_date = ?, end_date = ?, percent_to_pay = ?
                    WHERE id = ?
                """, (name, start_date, end_date, percent, calc_id))
            else: # Insertar
                creation_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO tax_calculations (company_id, name, start_date, end_date, percent_to_pay, creation_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (company_id, name, start_date, end_date, percent, creation_date))
                calc_id = cursor.lastrowid

            # Borrar detalles viejos e insertar los nuevos
            cursor.execute("DELETE FROM tax_calculation_details WHERE calculation_id = ?", (calc_id,))
            
            details_to_insert = []
            for invoice_id, state in details.items():
                if state['selected']:
                    retention_applied = 1 if state['retention'] else 0
                    details_to_insert.append((calc_id, invoice_id, retention_applied))
            
            cursor.executemany("""
                INSERT INTO tax_calculation_details (calculation_id, invoice_id, itbis_retention_applied)
                VALUES (?, ?, ?)
            """, details_to_insert)
            
            self.conn.commit()
            return True, "Cálculo guardado exitosamente."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error al guardar el cálculo: {e}"

    def get_tax_calculations(self, company_id):
        """Obtiene la lista de cálculos guardados para una empresa."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, creation_date FROM tax_calculations WHERE company_id = ? ORDER BY creation_date DESC", (company_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener cálculos: {e}")
            return []

    def get_tax_calculation_details(self, calculation_id):
        """Obtiene todos los detalles de un cálculo específico."""
        try:
            cursor = self.conn.cursor()
            # Obtener datos maestros del cálculo
            cursor.execute("SELECT * FROM tax_calculations WHERE id = ?", (calculation_id,))
            calc_data = cursor.fetchone()
            if not calc_data: return None

            # Obtener facturas y su estado de retención
            cursor.execute("""
                SELECT invoice_id, itbis_retention_applied 
                FROM tax_calculation_details WHERE calculation_id = ?
            """, (calculation_id,))
            details = cursor.fetchall()
            
            return {"main": dict(calc_data), "details": {row['invoice_id']: bool(row['itbis_retention_applied']) for row in details}}
        except sqlite3.Error as e:
            print(f"Error al obtener detalles del cálculo: {e}")
            return None

    def delete_tax_calculation(self, calculation_id):
        """Elimina un cálculo y todos sus detalles."""
        try:
            cursor = self.conn.cursor()
            # ON DELETE CASCADE se encarga de borrar los detalles automáticamente
            cursor.execute("DELETE FROM tax_calculations WHERE id = ?", (calculation_id,))
            self.conn.commit()
            return True, "Cálculo eliminado exitosamente."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error al eliminar el cálculo: {e}"
        
    def migrate_from_json(self, json_files):
        """
        Lee archivos JSON, inserta los datos de la empresa y sus facturas,
        y puebla el directorio de terceros (third_parties).
        """
        if not self.conn:
            return False, "Sin conexión a la base de datos."

        cursor = self.conn.cursor()
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                filename = os.path.basename(file_path)
                company_name_raw = filename.replace('facturas_', '').replace('.json', '')
                company_name = ' '.join(word.capitalize() for word in company_name_raw.split('_'))

                cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
                company_row = cursor.fetchone()
                
                if company_row is None:
                    print(f"Migrando nueva empresa: {company_name}")
                    # (El código para insertar la empresa y sus facturas no cambia)
                    itbis_adelantado = float(data.get('itbis_adelantado', 0.0))
                    cursor.execute("INSERT INTO companies (name, legacy_filename, itbis_adelantado) VALUES (?, ?, ?)",(company_name, filename, itbis_adelantado))
                    company_id = cursor.lastrowid
                    for factura in data.get("facturas_emitidas", []):
                        cursor.execute(
                            """INSERT INTO invoices (company_id, invoice_type, invoice_date, imputation_date, invoice_number, invoice_category, rnc, third_party_name, currency, itbis, total_amount, exchange_rate, total_amount_rd)
                            VALUES (?, 'emitida', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (company_id, factura.get('fecha'), factura.get('fecha_imputacion'), factura.get('no_fact'), factura.get('tipo_factura'), factura.get('rnc'), factura.get('empresa'), factura.get('moneda'), factura.get('itbis', 0.0), factura.get('factura_total', 0.0), factura.get('tasa_conversion', 1.0), factura.get('monto_convertido_rd', factura.get('factura_total', 0.0)))
                        )
                    for factura in data.get("facturas_gastos", []):
                        cursor.execute(
                            """INSERT INTO invoices (company_id, invoice_type, invoice_date, imputation_date, invoice_number, rnc, third_party_name, currency, itbis, total_amount, exchange_rate, total_amount_rd)
                            VALUES (?, 'gasto', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (company_id, factura.get('fecha'), factura.get('fecha_imputacion'), factura.get('no_fact'), factura.get('rnc'), factura.get('lugar_compra'), factura.get('moneda'), factura.get('itbis', 0.0), factura.get('factura_total', 0.0), factura.get('tasa_conversion', 1.0), factura.get('monto_convertido_rd', factura.get('factura_total', 0.0)))
                        )

                    # --- NUEVA SECCIÓN: Extraer y guardar los terceros ---
                    third_parties_to_add = set()
                    for f in data.get("facturas_emitidas", []):
                        if f.get('rnc') and f.get('empresa'):
                            third_parties_to_add.add((f['rnc'].strip(), f['empresa'].strip()))
                    for f in data.get("facturas_gastos", []):
                        if f.get('rnc') and f.get('lugar_compra'):
                            third_parties_to_add.add((f['rnc'].strip(), f['lugar_compra'].strip()))
                    
                    # Insertar o actualizar cada tercero en la base de datos
                    for rnc, name in third_parties_to_add:
                        self.add_or_update_third_party(rnc, name)
                    # --- FIN DE LA NUEVA SECCIÓN ---

                else:
                    print(f"La empresa {company_name} ya existe. Omitiendo migración para este archivo.")

            except Exception as e:
                self.conn.rollback()
                return False, f"Error migrando el archivo {file_path}: {e}"

        self.conn.commit()
        return True, "Migración completada exitosamente."
# En el archivo: logic.py

    def get_all_companies(self):
        """Recupera todas las empresas (id, name, rnc) de la base de datos."""
        if not self.conn: return []
        try:
            cursor = self.conn.cursor()
            # Añadimos la columna RNC a la consulta
            cursor.execute("SELECT id, name, rnc FROM companies ORDER BY name ASC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener las empresas: {e}")
            return []            


    def get_dashboard_data(self, company_id, filter_month=None, filter_year=None, specific_date=None):
        """
        Obtiene facturas y calcula totales para el dashboard, aplicando filtros opcionales.
        Siempre retorna todas las claves esperadas en cada transacción.
        """
        if not self.conn or company_id is None:
            return None

        def _normalize_transaction_row(row):
            """
            Asegura que cada registro tenga todos los campos requeridos.
            """
            expected_fields = [
                'id', 'invoice_date', 'invoice_type', 'invoice_number', 'third_party_name',
                'itbis', 'exchange_rate', 'total_amount', 'currency', 'total_amount_rd'
            ]
            # Convierte a dict si es necesario
            if not isinstance(row, dict):
                row = dict(row)
            # Completa faltantes
            for key in expected_fields:
                if key not in row or row[key] is None:
                    row[key] = '' if key in ('invoice_date', 'invoice_type', 'invoice_number', 'third_party_name', 'currency') else 0.0
            # exchange_rate nunca debe ser 0
            try:
                if float(row['exchange_rate']) == 0.0:
                    row['exchange_rate'] = 1.0
            except Exception:
                row['exchange_rate'] = 1.0
            return row

        try:
            cursor = self.conn.cursor()
            
            # Construcción de la consulta SQL dinámica
            query = "SELECT * FROM invoices WHERE company_id = ?"
            params = [company_id]
            
            if specific_date:
                # Si se provee una fecha específica, este filtro tiene prioridad
                query += " AND invoice_date = ?"
                params.append(specific_date.strftime('%Y-%m-%d'))
            elif filter_month and filter_year:
                # Filtros de mes y año
                query += " AND strftime('%Y', invoice_date) = ? AND strftime('%m', invoice_date) = ?"
                params.append(str(filter_year))
                params.append(str(filter_month).zfill(2))

            cursor.execute(query, params)
            all_invoices = cursor.fetchall()
            # Normalizar todos los registros
            normalized_invoices = [_normalize_transaction_row(row) for row in all_invoices]

            emitted = [row for row in normalized_invoices if row['invoice_type'] == 'emitida']
            expenses = [row for row in normalized_invoices if row['invoice_type'] == 'gasto']

            total_ingresos = sum(float(f['total_amount_rd']) for f in emitted)
            total_gastos = sum(float(f['total_amount_rd']) for f in expenses)
            itbis_ingresos = sum(float(f['itbis']) * float(f['exchange_rate']) for f in emitted)
            itbis_gastos = sum(float(f['itbis']) * float(f['exchange_rate']) for f in expenses)

            return {
                "all_transactions": sorted(normalized_invoices, key=lambda x: x['invoice_date'], reverse=True),
                "summary": {
                    "total_ingresos": total_ingresos, "total_gastos": total_gastos,
                    "itbis_ingresos": itbis_ingresos, "itbis_gastos": itbis_gastos,
                    "total_neto": total_ingresos - total_gastos,
                    "itbis_neto": itbis_ingresos - itbis_gastos
                }
            }

        except Exception as e:
            print(f"Error al obtener datos del dashboard: {e}")
            return None

    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            print("Conexión a la base de datos cerrada.")


    def get_unique_invoice_years(self, company_id):
        """
        Recupera una lista de años únicos en los que una empresa tiene facturas.
        """
        if not self.conn or company_id is None:
            return []
        
        try:
            cursor = self.conn.cursor()
            # La función strftime('%Y', ...) extrae el año de la fecha.
            # DISTINCT asegura que cada año aparezca solo una vez.
            query = "SELECT DISTINCT strftime('%Y', invoice_date) as year FROM invoices WHERE company_id = ? ORDER BY year DESC"
            cursor.execute(query, (company_id,))
            # Extraemos el valor de la columna 'year' para cada fila y lo convertimos a lista
            years = [row['year'] for row in cursor.fetchall()]
            return years
        except sqlite3.Error as e:
            print(f"Error al obtener años únicos: {e}")
            return []
        

    def get_itbis_adelantado(self, company_id):
        """Obtiene el ITBIS adelantado para una empresa específica."""
        if not self.conn or company_id is None:
            return 0.0
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT itbis_adelantado FROM companies WHERE id = ?", (company_id,))
            result = cursor.fetchone()
            return result['itbis_adelantado'] if result else 0.0
        except sqlite3.Error as e:
            print(f"Error al obtener ITBIS adelantado: {e}")
            return 0.0

    def update_itbis_adelantado(self, company_id, value):
        """Actualiza el ITBIS adelantado para una empresa específica."""
        if not self.conn or company_id is None:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE companies SET itbis_adelantado = ? WHERE id = ?", (value, company_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al actualizar ITBIS adelantado: {e}")
            return False
        

    def add_invoice(self, invoice_data):
        """Añade una nueva factura, con chequeo de duplicados."""
        if not self.conn:
            return False, "Sin conexión a la base de datos."
        
        try:
            # ... (el código para preparar los 'params' no cambia) ...
            cursor = self.conn.cursor()
            imputation_date = datetime.date.today().strftime('%Y-%m-%d')
            invoice_type = invoice_data['invoice_type']
            params = {
                "company_id": invoice_data['company_id'], "invoice_type": invoice_type,
                "invoice_date": invoice_data['invoice_date'], "imputation_date": imputation_date,
                "invoice_number": invoice_data['invoice_number'],
                "invoice_category": invoice_data.get('invoice_category'),
                "rnc": invoice_data['rnc'], "third_party_name": invoice_data['third_party_name'],
                "currency": invoice_data['currency'], "itbis": invoice_data['itbis'],
                "total_amount": invoice_data['total_amount'],
                "exchange_rate": invoice_data['exchange_rate'],
                "total_amount_rd": invoice_data['total_amount_rd'],
                "attachment_path": invoice_data.get('attachment_path')
            }

            cursor.execute(
                """INSERT INTO invoices (company_id, invoice_type, invoice_date, imputation_date, invoice_number, invoice_category, rnc, third_party_name, currency, itbis, total_amount, exchange_rate, total_amount_rd, attachment_path)
                VALUES (:company_id, :invoice_type, :invoice_date, :imputation_date, :invoice_number, :invoice_category, :rnc, :third_party_name, :currency, :itbis, :total_amount, :exchange_rate, :total_amount_rd, :attachment_path)""",
                params
            )
            self.conn.commit()
            self.add_or_update_third_party(invoice_data['rnc'], invoice_data['third_party_name'])
            success_message = "Factura de gasto registrada." if invoice_type == 'gasto' else "Factura emitida registrada."
            return True, success_message

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            # --- LÓGICA MEJORADA ---
            if 'UNIQUE constraint failed' in str(e) and 'idx_unique_invoice' in str(e):
                return False, "Error: Ya existe una factura con el mismo número para este RNC/Cédula."
            return False, f"Error de base de datos: {e}"
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos: {e}"
        
    def get_currencies(self, company_id):
        """
        Devuelve la lista de monedas disponibles desde la base de datos.
        El parámetro company_id se mantiene por compatibilidad pero no se usa actualmente.
        """
        if not self.conn:
            return ["RD$", "USD"] # Fallback por si no hay conexión
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM currencies ORDER BY name")
            return [row['name'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener monedas: {e}")
            return ["RD$", "USD"] # Fallback en caso de error    

    def search_third_parties(self, query, search_by='name'):
        """Busca en el directorio de terceros por nombre o RNC."""
        if not self.conn or len(query) < 2:
            return []
        try:
            cursor = self.conn.cursor()
            column = 'name' if search_by == 'name' else 'rnc'
            
            # Usamos LIKE para buscar coincidencias que empiecen con la consulta
            sql_query = f"SELECT rnc, name FROM third_parties WHERE {column} LIKE ? LIMIT 10"
            cursor.execute(sql_query, (f"{query}%",))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al buscar terceros: {e}")
            return []

    def add_or_update_third_party(self, rnc, name):
        """Añade un nuevo tercero o actualiza el nombre si el RNC ya existe."""
        if not self.conn or not rnc or not name:
            return
        try:
            cursor = self.conn.cursor()
            # 'INSERT ... ON CONFLICT' es una forma eficiente de hacer un "upsert"
            cursor.execute(
                """INSERT INTO third_parties (rnc, name) VALUES (?, ?)
                ON CONFLICT(rnc) DO UPDATE SET name=excluded.name""",
                (rnc.strip(), name.strip())
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al añadir o actualizar tercero: {e}")


    def get_invoice_by_id(self, invoice_id):
        """Recupera todos los datos de una única factura por su ID."""
        if not self.conn or invoice_id is None:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"Error al obtener la factura: {e}")
            return None

    def update_invoice(self, invoice_id, invoice_data):
        """Actualiza una factura existente, con chequeo de duplicados."""
        if not self.conn:
            return False, "Sin conexión a la base de datos."
        
        try:
            # ... (el código para preparar los 'params' no cambia) ...
            cursor = self.conn.cursor()
            params = {
                "invoice_date": invoice_data['invoice_date'], "invoice_number": invoice_data['invoice_number'],
                "invoice_category": invoice_data.get('invoice_category'), "rnc": invoice_data['rnc'],
                "third_party_name": invoice_data['third_party_name'], "currency": invoice_data['currency'],
                "itbis": invoice_data['itbis'], "total_amount": invoice_data['total_amount'],
                "exchange_rate": invoice_data['exchange_rate'], "total_amount_rd": invoice_data['total_amount_rd'],
                "attachment_path": invoice_data.get('attachment_path'), "invoice_id": invoice_id
            }

            cursor.execute(
                """UPDATE invoices SET
                    invoice_date = :invoice_date, invoice_number = :invoice_number,
                    invoice_category = :invoice_category, rnc = :rnc,
                    third_party_name = :third_party_name, currency = :currency,
                    itbis = :itbis, total_amount = :total_amount,
                    exchange_rate = :exchange_rate, total_amount_rd = :total_amount_rd,
                    attachment_path = :attachment_path
                WHERE id = :invoice_id""",
                params
            )
            self.conn.commit()
            self.add_or_update_third_party(invoice_data['rnc'], invoice_data['third_party_name'])
            return True, "Factura actualizada exitosamente."

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            # --- LÓGICA MEJORADA ---
            if 'UNIQUE constraint failed' in str(e) and 'idx_unique_invoice' in str(e):
                 return False, "Error: Ya existe otra factura con ese mismo número para este RNC/Cédula."
            return False, f"Error de base de datos al actualizar: {e}"
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos al actualizar: {e}"
                
    def delete_invoice(self, invoice_id):
        """Elimina una factura de la base de datos por su ID."""
        if not self.conn:
            return False, "Sin conexión a la base de datos."
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            self.conn.commit()
            return True, "Factura eliminada exitosamente."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos al eliminar: {e}"
        

    def get_monthly_report_data(self, company_id, month, year):
        """
        Obtiene los datos de facturas para un mes y año específicos para generar un reporte.
        """
        if not self.conn or company_id is None:
            return None
        
        # Usamos el mismo método de filtrado que ya probamos
        report_data = self.get_dashboard_data(company_id, filter_month=month, filter_year=year)
        
        if not report_data:
            return None

        # Separamos las listas para mayor claridad en el reporte
        emitted_invoices = [dict(row) for row in report_data['all_transactions'] if row['invoice_type'] == 'emitida']
        expense_invoices = [dict(row) for row in report_data['all_transactions'] if row['invoice_type'] == 'gasto']

        return {
            "summary": report_data['summary'],
            "emitted_invoices": emitted_invoices,
            "expense_invoices": expense_invoices
        }
    

    def get_emitted_invoices_for_period(self, company_id, start_date, end_date):
        """Obtiene todas las facturas emitidas para una empresa dentro de un rango de fechas."""
        if not self.conn or not all([company_id, start_date, end_date]):
            return []
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT * FROM invoices 
                WHERE company_id = ? 
                AND invoice_type = 'emitida'
                AND invoice_date BETWEEN ? AND ?
                ORDER BY invoice_date
            """
            cursor.execute(query, (company_id, start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener facturas emitidas por período: {e}")
            return []
        

    def get_setting(self, key, default=None):
        if not os.path.exists("config.json"):
            return default
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            return config.get(key, default)
        except Exception:
            return default

    def set_setting(self, key, value):
        config = {}
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
            except Exception:
                config = {}
        config[key] = value
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

    def get_all_currencies(self):
        """Obtiene todas las monedas de la base de datos."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM currencies ORDER BY name")
            return [row['name'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener monedas: {e}")
            return ["RD$", "USD"]

    def save_currencies(self, currency_list):
        """Borra y guarda la lista completa de monedas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM currencies")
            cursor.executemany("INSERT INTO currencies (name) VALUES (?)", [(c,) for c in currency_list])
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al guardar monedas: {e}")


    def get_report_by_third_party(self, company_id, third_party_rnc):
        """Obtiene todas las facturas y totales para un cliente/proveedor específico."""
        if not all([self.conn, company_id, third_party_rnc]):
            return None

        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM invoices WHERE company_id = ? AND rnc = ? ORDER BY invoice_date DESC"
            cursor.execute(query, (company_id, third_party_rnc))
            all_invoices = [dict(row) for row in cursor.fetchall()]

            emitted = [f for f in all_invoices if f['invoice_type'] == 'emitida']
            expenses = [f for f in all_invoices if f['invoice_type'] == 'gasto']

            total_ingresos = sum(f['total_amount_rd'] for f in emitted)
            total_gastos = sum(f['total_amount_rd'] for f in expenses)

            return {
                "summary": {
                    "total_ingresos": total_ingresos,
                    "total_gastos": total_gastos
                },
                "emitted_invoices": emitted,
                "expense_invoices": expenses
            }
        except sqlite3.Error as e:
            print(f"Error al obtener reporte por tercero: {e}")
            return None



    def reconnect(self):
        """Cierra y reabre la conexión a la base de datos."""
        self.close_connection()
        self._connect()


# En el archivo: logic.py

    def add_company(self, name, rnc):
        """Añade una nueva empresa con su RNC a la base de datos."""
        if not self.conn or not name or not rnc:
            return False, "Nombre y RNC son requeridos."
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO companies (name, rnc) VALUES (?, ?)", (name, rnc))
            self.conn.commit()
            return True, "Empresa añadida exitosamente."
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False, "Ya existe una empresa con ese nombre o RNC."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos: {e}"

# En el archivo: logic.py

    def get_company_details(self, company_id):
        """Recupera todos los detalles de una única empresa por su ID."""
        if not self.conn or not company_id:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"Error al obtener detalles de la empresa: {e}")
            return None

    def update_company(self, company_id, new_name, new_rnc, new_address):
        """Actualiza el nombre, RNC y dirección de una empresa existente."""
        if not all([self.conn, company_id, new_name, new_rnc]):
            return False, "Datos inválidos o sin conexión."
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE companies SET name = ?, rnc = ?, address = ? WHERE id = ?",
                (new_name, new_rnc, new_address, company_id)
            )
            self.conn.commit()
            return True, "Empresa actualizada exitosamente."
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False, "Ya existe otra empresa con ese nuevo nombre o RNC."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos: {e}"

    def delete_company(self, company_id):
        """Elimina una empresa y todas sus facturas asociadas."""
        if not self.conn or not company_id:
            return False, "ID de empresa inválido o sin conexión."
        try:
            cursor = self.conn.cursor()
            # ¡Importante! Eliminar primero las facturas para mantener la integridad
            cursor.execute("DELETE FROM invoices WHERE company_id = ?", (company_id,))
            # Luego, eliminar la empresa
            cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
            self.conn.commit()
            return True, "Empresa y todos sus datos eliminados exitosamente."
        except sqlite3.Error as e:
            self.conn.rollback()
            return False, f"Error de base de datos: {e}"
        

    def ensure_attachment_folder_exists(self, company_name, for_date):
        """
        Asegura que la estructura de carpetas para una empresa y fecha exista.
        Devuelve la ruta completa de la carpeta del mes.
        """
        base_path = self.get_setting('attachment_base_path')
        if not base_path or not os.path.isdir(base_path):
            return None 

        sanitized_company_name = "".join(c for c in company_name if c not in '<>:"/\\|?*')
        year_str = str(for_date.year)
        month_str = f"{for_date.month:02d}"
        
        full_path = os.path.join(base_path, sanitized_company_name, year_str, month_str)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def get_attachment_base_path(self):
        """
        Construye la ruta base completa para los adjuntos combinando
        la ruta de Dropbox detectada y la subcarpeta configurada.
        """
        dropbox_path = find_dropbox_folder()
        subfolder_name = self.get_setting('attachment_subfolder')

        if dropbox_path and subfolder_name:
            return os.path.join(dropbox_path, subfolder_name)
        
        return None


    def get_companies(self):
        """Recupera todas las empresas como lista de dicts."""
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM companies ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener empresas: {e}")
            return []

    def get_all_companies(self):
        """Recupera todas las empresas como lista de dicts."""
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM companies ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener empresas: {e}")
            return []