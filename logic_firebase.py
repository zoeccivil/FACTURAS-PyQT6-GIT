import os
import json
import datetime
from typing import Optional, List, Dict, Any

# Intentamos usar firebase_admin (ya lo utilizas en migration_dialog indirectamente)
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    from google.cloud.firestore_v1 import FieldFilter
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None
    storage = None
    FieldFilter = None


class LogicControllerFirebase:
    """
    Controlador que replica la interfaz del LogicControllerQt, pero usando
    Firebase Firestore como backend de datos.

    Se apoya en el archivo config.json, clave "facturas_config", que contiene:
      - firebase_credentials_path
      - firebase_project_id
      - firebase_storage_bucket
    """

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path

        # Estado de Firebase
        self._firebase_app = None
        self._db = None          # Firestore client
        self._bucket = None      # Firebase Storage bucket

        # Estado de la app
        self.active_company_id: Optional[int] = None
        self.active_company_name: Optional[str] = None
        self.tx_filter: Optional[str] = None  # 'emitida' | 'gasto' | None

        # Inicializar Firebase
        self._init_firebase_from_settings()

    # ------------------------------------------------------------------ #
    # Inicialización Firebase (Firestore + Storage)
    # ------------------------------------------------------------------ #
    def _init_firebase_from_settings(self):
        """Inicializa Firestore y Storage usando la configuración de 'facturas_config'."""
        if firebase_admin is None or credentials is None or firestore is None:
            print("[FIREBASE] firebase_admin no está disponible. Instala firebase-admin.")
            return

        raw = self.get_setting("facturas_config", {})
        if isinstance(raw, str):
            try:
                cfg = json.loads(raw)
            except Exception:
                cfg = {}
        elif isinstance(raw, dict):
            cfg = raw
        else:
            cfg = {}

        cred_path = cfg.get("firebase_credentials_path")
        project_id = cfg.get("firebase_project_id")
        storage_bucket = cfg.get("firebase_storage_bucket")  # puede ser None

        if not cred_path or not os.path.exists(cred_path):
            print("[FIREBASE] credenciales no configuradas o archivo no existe.")
            return

        if not project_id:
            # Intentar leer project_id desde el JSON de credenciales
            try:
                with open(cred_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    project_id = data.get("project_id")
            except Exception:
                project_id = None

        if not project_id:
            print("[FIREBASE] project_id no definido; no se puede inicializar Firebase.")
            return

        try:
            if not self._firebase_app:
                cred = credentials.Certificate(cred_path)
                options = {
                    "projectId": project_id,
                }
                if storage_bucket:
                    options["storageBucket"] = storage_bucket
                self._firebase_app = firebase_admin.initialize_app(cred, options)

            # Firestore
            self._db = firestore.client()

            # Storage
            if storage is not None:
                try:
                    if storage_bucket:
                        self._bucket = storage.bucket(storage_bucket)
                    else:
                        self._bucket = storage.bucket()
                except Exception:
                    self._bucket = None
            else:
                self._bucket = None

        except Exception:
            self._db = None
            self._bucket = None

    # ------------------------------------------------------------------ #
    # Settings (compatibles con LogicControllerQt)
    # ------------------------------------------------------------------ #
    def get_setting(self, key: str, default=None):
        """Lee una clave del config.json. Se usa especialmente 'facturas_config'."""
        if not os.path.exists(self.config_path):
            return default
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get(key, default)
        except Exception:
            return default

    def set_setting(self, key: str, value):
        """Escribe una clave en config.json. Si ya existe el archivo, se mergea."""
        data: Dict[str, Any] = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[key] = value
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def on_firebase_config_updated(self):
        """Llamado desde la UI moderna después de cambiar la configuración."""
        self._firebase_app = None
        self._db = None
        self._bucket = None
        self._init_firebase_from_settings()

    # ------------------------------------------------------------------ #
    # API esperada por ModernMainWindow
    # ------------------------------------------------------------------ #
    # Empresas
    # ------------------------------------------------------------------ #
    def list_companies(self) -> List[str]:
        """Devuelve solo los nombres de empresas, para poblar el combo del sidebar."""
        companies = self.get_companies()
        return [c.get("name", "") for c in companies]

    def get_companies(self) -> List[Dict[str, Any]]:
        """
        Recupera todas las empresas como lista de dicts desde la colección
        'companies' de Firestore.
        """
        if self._db is None:
            print("[FIREBASE] Firestore no está inicializado.")
            return []

        results: List[Dict[str, Any]] = []
        try:
            docs = self._db.collection("companies").order_by("name").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                try:
                    data["id"] = int(doc.id)
                except Exception:
                    data["id"] = doc.id
                results.append(data)
        except Exception:
            pass
        return results

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Alias para compatibilidad."""
        return self.get_companies()

    def set_active_company(self, name: str) -> None:
        """
        Establece la empresa activa dado su nombre (viene del combo).
        """
        self.active_company_name = name or None
        self.active_company_id = None

        if not name or self._db is None:
            return

        try:
            if FieldFilter is None:
                # fallback a where clásico si no está disponible
                q = self._db.collection("companies").where("name", "==", name).limit(1)
            else:
                q = (
                    self._db.collection("companies")
                    .where(filter=FieldFilter("name", "==", name))
                    .limit(1)
                )
            docs = list(q.stream())
            if docs:
                try:
                    self.active_company_id = int(docs[0].id)
                except Exception:
                    self.active_company_id = docs[0].id
        except Exception as e:
            print(f"[FIREBASE] Error estableciendo empresa activa: {e}")

    # ------------------------------------------------------------------ #
    # Filtros / años disponibles
    # ------------------------------------------------------------------ #
    def set_transaction_filter(self, tx_type: Optional[str]) -> None:
        """Guarda el filtro actual de transacciones ('emitida'|'gasto'|None)."""
        self.tx_filter = tx_type

    def get_unique_invoice_years(self, company_id=None) -> List[int]:
        """
        Devuelve los años distintos en los que hay facturas para la empresa activa.
        Lee siempre invoice_date (string o timestamp).
        """
        if self._db is None:
            return []

        company = company_id or self.active_company_id
        if not company:
            return []

        years = set()
        try:
            if FieldFilter is None:
                q = self._db.collection("invoices").where("company_id", "==", company)
            else:
                q = self._db.collection("invoices").where(
                    filter=FieldFilter("company_id", "==", company)
                )
            docs = list(q.stream())

            try:
                from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
            except Exception:
                DatetimeWithNanoseconds = type("DTWN", (), {})

            def _norm_date(v) -> Optional[datetime.date]:
                if v is None:
                    return None
                if isinstance(v, DatetimeWithNanoseconds):
                    return v.date()
                if isinstance(v, datetime.datetime):
                    return v.date()
                if isinstance(v, datetime.date):
                    return v
                try:
                    s = str(v)
                    return datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
                except Exception:
                    return None

            for doc in docs:
                data = doc.to_dict() or {}
                d = _norm_date(data.get("invoice_date"))
                if d is not None:
                    years.add(d.year)

        except Exception:
            return []

        return sorted(years, reverse=True)

    # ------------------------------------------------------------------ #
    # Dashboard: resumen y tabla
    # ------------------------------------------------------------------ #
    def _refresh_dashboard(self, month: Optional[str], year: Optional[int]) -> Dict[str, float]:
        """
        Calcula los KPIs del dashboard para la empresa activa usando Firestore.

        month: código de mes "01".."12" o None
        year: año como entero o None
        """
        if self._db is None or not self.active_company_id:
            return {
                "income": 0.0,
                "income_itbis": 0.0,
                "expense": 0.0,
                "expense_itbis": 0.0,
                "net_itbis": 0.0,
                "payable": 0.0,
                "itbis_adelantado": 0.0,
                "payable_estimated": 0.0,
            }

        invoices = self._query_invoices(
            self.active_company_id,
            month,
            year,
            tx_type=self.tx_filter,
        )

        emitted = [inv for inv in invoices if inv.get("invoice_type") == "emitida"]
        expenses = [inv for inv in invoices if inv.get("invoice_type") == "gasto"]

        total_ingresos = sum(float(inv.get("total_amount_rd", 0.0)) for inv in emitted)
        total_gastos = sum(float(inv.get("total_amount_rd", 0.0)) for inv in expenses)

        def _fx(inv: Dict[str, Any]) -> float:
            try:
                rate = float(inv.get("exchange_rate", 1.0) or 1.0)
                return rate if rate != 0 else 1.0
            except Exception:
                return 1.0

        itbis_ingresos = sum(float(inv.get("itbis", 0.0)) * _fx(inv) for inv in emitted)
        itbis_gastos = sum(float(inv.get("itbis", 0.0)) * _fx(inv) for inv in expenses)

        net_itbis = itbis_ingresos - itbis_gastos

        # ITBIS adelantado del mes/año actual (para esta empresa)
        itbis_adelantado = 0.0
        try:
            if hasattr(self, "get_itbis_adelantado_period") and month and year:
                itbis_adelantado = float(
                    self.get_itbis_adelantado_period(
                        self.active_company_id, month, year
                    )
                    or 0.0
                )
        except Exception:
            itbis_adelantado = 0.0

        # A pagar estimado = neto - adelantado
        payable_estimated = net_itbis - itbis_adelantado

        # Para compatibilidad, 'payable' sigue siendo el neto
        payable = net_itbis

        return {
            "income": total_ingresos,
            "income_itbis": itbis_ingresos,
            "expense": total_gastos,
            "expense_itbis": itbis_gastos,
            "net_itbis": net_itbis,
            "payable": payable,
            "itbis_adelantado": itbis_adelantado,
            "payable_estimated": payable_estimated,
        }
    

    def _populate_transactions_table(
        self,
        month: Optional[str],
        year: Optional[int],
        tx_type: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Devuelve la lista de transacciones normalizadas para poblar la tabla.
        """
        if self._db is None or not self.active_company_id:
            return []

        invoices = self._query_invoices(
            self.active_company_id,
            month,
            year,
            tx_type=tx_type,
        )

        def _key(inv: Dict[str, Any]):
            return inv.get("invoice_date") or ""

        invoices_sorted = sorted(invoices, key=_key, reverse=True)

        try:
            from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
        except Exception:
            DatetimeWithNanoseconds = type("DTWN", (), {})  # dummy

        def _format_date_for_display(v) -> str:
            if v is None:
                return ""
            if isinstance(v, DatetimeWithNanoseconds):
                return v.date().strftime("%Y-%m-%d")
            if isinstance(v, datetime.datetime):
                return v.date().strftime("%Y-%m-%d")
            if isinstance(v, datetime.date):
                return v.strftime("%Y-%m-%d")
            s = str(v)
            return s[:10]

        rows: List[Dict[str, Any]] = []
        for inv in invoices_sorted:
            rows.append(
                {
                    "date": _format_date_for_display(inv.get("invoice_date")),
                    "type": inv.get("invoice_type", ""),
                    "number": inv.get("invoice_number", ""),
                    "party": inv.get("third_party_name", ""),
                    "itbis": float(inv.get("itbis", 0.0)),
                    "total": float(
                        inv.get("total_amount_rd", inv.get("total_amount", 0.0))
                    ),
                }
            )
        return rows

    def _query_invoices(
        self,
        company_id: int,
        month_str: Optional[str],
        year_int: Optional[int],
        tx_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Devuelve lista de facturas para una empresa.

        Filtra por company_id (y opcionalmente invoice_type) en Firestore.
        El filtro por mes/año se hace en Python usando invoice_date.
        """
        if self._db is None:
            return []

        try:
            col = self._db.collection("invoices")

            if FieldFilter is None:
                q = col.where("company_id", "==", int(company_id))
                if tx_type:
                    q = q.where("invoice_type", "==", tx_type)
            else:
                q = col.where(
                    filter=FieldFilter("company_id", "==", int(company_id))
                )
                if tx_type:
                    q = q.where(
                        filter=FieldFilter("invoice_type", "==", tx_type)
                    )

            docs = list(q.stream())

            invoices: List[dict] = []
            for doc in docs:
                data = doc.to_dict() or {}
                data["id"] = doc.id
                invoices.append(data)

            try:
                from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
            except Exception:
                DatetimeWithNanoseconds = type("DTWN", (), {})  # dummy

            def _norm_date(v) -> datetime.date:
                if v is None:
                    return datetime.date(1970, 1, 1)
                if isinstance(v, DatetimeWithNanoseconds):
                    return v.date()
                if isinstance(v, datetime.datetime):
                    return v.date()
                if isinstance(v, datetime.date):
                    return v
                try:
                    s = str(v)
                    return datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
                except Exception:
                    return datetime.date(1970, 1, 1)

            filtered: List[dict] = []
            for inv in invoices:
                d_raw = inv.get("invoice_date")
                d = _norm_date(d_raw)
                if year_int is not None and d.year != year_int:
                    continue
                if month_str is not None:
                    try:
                        m_int = int(month_str)
                    except Exception:
                        m_int = None
                    if m_int is not None and d.month != m_int:
                        continue
                filtered.append(inv)

            filtered.sort(
                key=lambda inv: _norm_date(inv.get("invoice_date")),
                reverse=True,
            )

            return filtered

        except Exception as e:
            print(f"[FIREBASE-DASH] Error en _query_invoices: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Diagnóstico / helpers
    # ------------------------------------------------------------------ #
    def diagnose_row(self, number: str):
        """Diagnóstico básico de una factura a partir de su invoice_number."""
        if self._db is None or not self.active_company_id or not number:
            print(
                f"[FIREBASE] diagnose_row: sin datos suficientes "
                f"(company={self.active_company_id}, number={number})"
            )
            return

        try:
            if FieldFilter is None:
                q = (
                    self._db.collection("invoices")
                    .where("company_id", "==", self.active_company_id)
                    .where("invoice_number", "==", number)
                    .limit(1)
                )
            else:
                q = (
                    self._db.collection("invoices")
                    .where(
                        filter=FieldFilter("company_id", "==", self.active_company_id)
                    )
                    .where(filter=FieldFilter("invoice_number", "==", number))
                    .limit(1)
                )
            docs = list(q.stream())
            if not docs:
                return
            inv = docs[0].to_dict() or {}
            print(
                f"[FIREBASE] Diagnóstico factura {number}: "
                f"{json.dumps(inv, indent=2, ensure_ascii=False)}"
            )
        except Exception as e:
            print(f"[FIREBASE] Error en diagnose_row: {e}")
    # ------------------------------------------------------------------ #
    # Alta de facturas en Firebase
    # ------------------------------------------------------------------ #
    def add_invoice(self, invoice_data: dict) -> tuple[bool, str]:
        """
        Crea una factura en la colección 'invoices'.
        Normaliza:
          - company_id
          - total_amount_rd
          - fechas (invoice_date / imputation_date / due_date)
          - invoice_year / invoice_month
        Y asegura el registro del tercero en 'third_parties'.
        """
        if self._db is None:
            return False, "Firestore no está inicializado."

        if not self.active_company_id and not invoice_data.get("company_id"):
            return False, "No hay empresa activa seleccionada."

        company_id = invoice_data.get("company_id") or self.active_company_id
        try:
            invoice_data["company_id"] = int(company_id)
        except Exception:
            invoice_data["company_id"] = company_id

        try:
            if "total_amount_rd" not in invoice_data:
                try:
                    rate = float(invoice_data.get("exchange_rate", 1.0) or 1.0)
                except Exception:
                    rate = 1.0
                try:
                    total = float(invoice_data.get("total_amount", 0.0))
                except Exception:
                    total = 0.0
                invoice_data["total_amount_rd"] = total * (rate or 1.0)

            def _normalize_date_field(key: str):
                val = invoice_data.get(key)
                if isinstance(val, datetime.date) and not isinstance(
                    val, datetime.datetime
                ):
                    invoice_data[key] = datetime.datetime(val.year, val.month, val.day)

            _normalize_date_field("invoice_date")
            _normalize_date_field("imputation_date")
            _normalize_date_field("due_date")

            inv_date = invoice_data.get("invoice_date")
            year_field = invoice_data.get("invoice_year")
            month_field = invoice_data.get("invoice_month")

            if inv_date and (year_field is None or month_field in (None, "")):
                y = None
                m = None
                if isinstance(inv_date, datetime.datetime):
                    y = inv_date.year
                    m = inv_date.month
                elif isinstance(inv_date, datetime.date):
                    y = inv_date.year
                    m = inv_date.month
                else:
                    try:
                        s = str(inv_date)
                        y, m, _ = map(int, s[:10].split("-"))
                    except Exception:
                        y = None
                        m = None

                if y is not None and m is not None:
                    invoice_data["invoice_year"] = int(y)
                    invoice_data["invoice_month"] = f"{int(m):02d}"

            rnc = str(invoice_data.get("rnc") or "")
            name = str(
                invoice_data.get("third_party_name")
                or invoice_data.get("client_name")
                or ""
            )
            self._ensure_third_party(rnc, name)

            doc_ref = self._db.collection("invoices").document()
            doc_ref.set(invoice_data)
            return True, "Factura registrada correctamente."
        except Exception as e:
            return False, f"Error al añadir factura en Firebase: {e}"

    # ------------------------------------------------------------------ #
    # Firebase Storage: manejo de anexos
    # ------------------------------------------------------------------ #
    def upload_attachment_to_storage(
        self,
        local_path: str,
        company_id: Optional[int],
        invoice_number: str,
        invoice_date: Optional[datetime.date],
        rnc: Optional[str] = None,
    ) -> Optional[str]:
        """
        Sube un archivo local a Firebase Storage y devuelve la ruta lógica
        del objeto en el bucket (object_name), p.ej.:

            Adjuntos/CARVAJAL_DIAZ_SRL/2025/12/B010000584_132125177.jpg
        """
        if not self._bucket:
            return None

        if not local_path or not os.path.exists(local_path):
            return None

        try:
            # Nombre de empresa seguro
            try:
                company_name = getattr(self, "active_company_name", None)
            except Exception:
                company_name = None

            if not company_name:
                company_name = str(company_id or "company")

            safe_company = (
                "".join(
                    c for c in company_name
                    if c.isalnum() or c in (" ", "-", "_")
                )
                .strip()
                .replace(" ", "_")
            ) or "company"

            # Año y mes para carpetas
            if isinstance(invoice_date, datetime.date):
                year = invoice_date.strftime("%Y")
                month = invoice_date.strftime("%m")
            else:
                today = datetime.date.today()
                year = today.strftime("%Y")
                month = today.strftime("%m")

            # RNC / código
            rnc_val = (rnc or "").strip() or "noRNC"
            safe_rnc = (
                "".join(
                    c for c in rnc_val
                    if c.isalnum() or c in ("-", "_")
                )
                or "noRNC"
            )

            # Nombre de archivo final: NUM_FACTURA_RNC.ext
            filename = os.path.basename(local_path)
            ext = os.path.splitext(filename)[1].lower()

            invoice_part = (
                "".join(
                    c for c in (invoice_number or "")
                    if (c.isalnum() or c in ("-", "_"))
                )
                or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            file_name = f"{invoice_part}_{safe_rnc}{ext}"

            # Ruta lógica en Storage (INCLUYENDO MES)
            object_name = f"Adjuntos/{safe_company}/{year}/{month}/{file_name}"
            object_name = object_name.replace("\\", "/")

            blob = self._bucket.blob(object_name)
            blob.upload_from_filename(local_path)

            # Este valor es el que se debe guardar en la factura como attachment_storage_path
            return object_name

        except Exception as e:
            print(f"[FIREBASE-STORAGE] Error subiendo adjunto: {e}")
            return None
    
    def get_attachment_download_url(self, storage_path: str) -> Optional[str]:
        """
        Devuelve una URL de descarga para un objeto en Storage.
        Por ahora, intentamos usar blob.public_url (si el blob es público).
        """
        if not self._bucket or not storage_path:
            return None
        try:
            blob = self._bucket.blob(storage_path)
            return blob.public_url
        except Exception:
            return None

    def _ensure_third_party(self, rnc: str, name: str) -> None:
        """
        Crea un registro en 'third_parties' si no existe ya uno con el mismo RNC
        para la empresa activa. Es idempotente.
        """
        if self._db is None or FieldFilter is None:
            return
        rnc = (rnc or "").strip()
        name = (name or "").strip()
        if not rnc and not name:
            return

        try:
            col = self._db.collection("third_parties")
            if self.active_company_id is not None:
                q = (
                    col.where(
                        filter=FieldFilter("company_id", "==", self.active_company_id)
                    )
                    .where(filter=FieldFilter("rnc", "==", rnc))
                    .limit(1)
                )
            else:
                q = col.where(filter=FieldFilter("rnc", "==", rnc)).limit(1)

            docs = list(q.stream())
            if docs:
                return  # ya existe

            payload = {
                "rnc": rnc,
                "name": name,
                "name_normalized": name.lower(),
                "company_id": self.active_company_id,
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
            col.add(payload)
        except Exception as e:
            print(f"[FIREBASE] Error creando third_party: {e}")

    # ------------------------------------------------------------------ #
    # Integración con ventanas clásicas de facturas
    # ------------------------------------------------------------------ #
    def open_add_income_invoice_window(self, parent=None):
        from PyQt6.QtWidgets import QApplication
        from add_invoice_window_qt import AddInvoiceWindowQt

        app = QApplication.instance()
        if app is None:
            print(
                "[FIREBASE] open_add_income_invoice_window: no hay QApplication activa."
            )
            return
        if parent is None:
            parent = app.activeWindow()

        def on_save(dialog, form_data, invoice_type, invoice_id=None):
            fecha = form_data.get("invoice_date") or form_data.get("fecha")
            invoice_num = (
                form_data.get("invoice_number")
                or form_data.get("número_de_factura")
            )
            currency = form_data.get("currency") or form_data.get("moneda")
            rnc = form_data.get("rnc") or form_data.get("rnc_cédula")
            tercero = (
                form_data.get("third_party_name")
                or form_data.get("empresa_a_la_que_se_emitió")
                or form_data.get("empresa")
            )
            itbis = form_data.get("itbis") or 0.0
            total = (
                form_data.get("total_amount")
                or form_data.get("factura_total")
                or 0.0
            )
            exchange = (
                form_data.get("exchange_rate")
                or form_data.get("tasa_cambio")
                or 1.0
            )

            try:
                itbis = float(itbis)
            except Exception:
                itbis = 0.0
            try:
                total = float(total)
            except Exception:
                total = 0.0
            try:
                exchange = float(exchange)
            except Exception:
                exchange = 1.0

            invoice_data = {
                "company_id": self.active_company_id,
                "invoice_type": "emitida",
                "invoice_date": fecha,
                "imputation_date": fecha,
                "invoice_number": invoice_num,
                "invoice_category": None,
                "rnc": rnc,
                "third_party_name": tercero,
                "currency": currency,
                "itbis": itbis,
                "total_amount": total,
                "exchange_rate": exchange,
                "attachment_path": None,
                "client_name": tercero,
                "client_rnc": rnc,
                "excel_path": None,
                "pdf_path": None,
                "due_date": None,
            }

            ok, msg = self.add_invoice(invoice_data)
            return ok, msg

        dlg = AddInvoiceWindowQt(
            parent=parent,
            controller=self,
            tipo_factura="emitida",
            on_save=on_save,
        )
        if dlg.exec() and parent is not None and hasattr(parent, "refresh_dashboard"):
            parent.refresh_dashboard()

    def open_add_expense_invoice_window(self, parent=None):
        """
        Abre AddExpenseWindowQt para facturas de gasto,
        pero guardando el resultado en Firestore.
        """
        from PyQt6.QtWidgets import QApplication
        from add_expense_window_qt import AddExpenseWindowQt

        app = QApplication.instance()
        if app is None:
            print(
                "[FIREBASE] open_add_expense_invoice_window: no hay QApplication activa."
            )
            return
        if parent is None:
            parent = app.activeWindow()

        def on_save(dialog, form_data, invoice_type, invoice_id=None):
            # Extraemos valores normalizados desde form_data
            fecha = form_data.get("invoice_date") or form_data.get("fecha")
            invoice_num = (
                form_data.get("invoice_number")
                or form_data.get("número_de_factura")
            )
            currency = form_data.get("currency") or form_data.get("moneda")
            rnc = form_data.get("rnc") or form_data.get("rnc_cédula")
            tercero = (
                form_data.get("third_party_name")
                or form_data.get("empresa_a_la_que_se_emitió")
                or form_data.get("lugar_de_compra_empresa")
            )
            itbis = form_data.get("itbis") or 0.0
            total = (
                form_data.get("total_amount")
                or form_data.get("factura_total")
                or 0.0
            )
            exchange = (
                form_data.get("exchange_rate")
                or form_data.get("tasa_cambio")
                or 1.0
            )
            attach = form_data.get("attachment_path")
            attach_storage = form_data.get("attachment_storage_path")  # <- NUEVO

            try:
                itbis = float(itbis)
            except Exception:
                itbis = 0.0
            try:
                total = float(total)
            except Exception:
                total = 0.0
            try:
                exchange = float(exchange)
            except Exception:
                exchange = 1.0

            invoice_data = {
                "company_id": self.active_company_id,
                "invoice_type": "gasto",
                "invoice_date": fecha,
                "imputation_date": fecha,
                "invoice_number": invoice_num,
                "invoice_category": None,
                "rnc": rnc,
                "third_party_name": tercero,
                "currency": currency,
                "itbis": itbis,
                "total_amount": total,
                "exchange_rate": exchange,
                "attachment_path": attach,
                "attachment_storage_path": attach_storage,  # <- NUEVO
                "client_name": None,
                "client_rnc": None,
                "excel_path": None,
                "pdf_path": None,
                "due_date": None,
            }

            ok, msg = self.add_invoice(invoice_data)
            return ok, msg

        dlg = AddExpenseWindowQt(parent=parent, controller=self, on_save=on_save)
        if dlg.exec() and parent is not None and hasattr(parent, "refresh_dashboard"):
            parent.refresh_dashboard()

        def on_save(dialog, form_data, invoice_type, invoice_id=None):
            fecha = form_data.get("invoice_date") or form_data.get("fecha")
            invoice_num = (
                form_data.get("invoice_number")
                or form_data.get("número_de_factura")
            )
            currency = form_data.get("currency") or form_data.get("moneda")
            rnc = form_data.get("rnc") or form_data.get("rnc_cédula")
            tercero = (
                form_data.get("third_party_name")
                or form_data.get("empresa_a_la_que_se_emitió")
                or form_data.get("lugar_de_compra_empresa")
            )
            itbis = form_data.get("itbis") or 0.0
            total = (
                form_data.get("total_amount")
                or form_data.get("factura_total")
                or 0.0
            )
            exchange = (
                form_data.get("exchange_rate")
                or form_data.get("tasa_cambio")
                or 1.0
            )
            attach = form_data.get("attachment_path")

            try:
                itbis = float(itbis)
            except Exception:
                itbis = 0.0
            try:
                total = float(total)
            except Exception:
                total = 0.0
            try:
                exchange = float(exchange)
            except Exception:
                exchange = 1.0

            invoice_data = {
                "company_id": self.active_company_id,
                "invoice_type": "gasto",
                "invoice_date": fecha,
                "imputation_date": fecha,
                "invoice_number": invoice_num,
                "invoice_category": None,
                "rnc": rnc,
                "third_party_name": tercero,
                "currency": currency,
                "itbis": itbis,
                "total_amount": total,
                "exchange_rate": exchange,
                "attachment_path": attach,
                "client_name": None,
                "client_rnc": None,
                "excel_path": None,
                "pdf_path": None,
                "due_date": None,
            }

            ok, msg = self.add_invoice(invoice_data)
            return ok, msg

        dlg = AddExpenseWindowQt(parent=parent, controller=self, on_save=on_save)
        if dlg.exec() and parent is not None and hasattr(parent, "refresh_dashboard"):
            parent.refresh_dashboard()

    # ------------------------------------------------------------------ #
    # Reportes / Cálculo impuestos (stubs por ahora)
    # ------------------------------------------------------------------ #
    def _open_tax_calculation_manager(self):
        print("[FIREBASE] _open_tax_calculation_manager: no implementado aún.")

    def _open_report_window(self):
        print("[FIREBASE] _open_report_window: no implementado aún.")

    def create_sql_backup(self, retention_days: int = 30) -> str:
        """
        Mantener firma para el menú 'Crear backup SQL manual'.
        En Firebase no aplica, devolvemos un placeholder.
        """
        path = f"backup_firestore_placeholder_{datetime.date.today().isoformat()}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("Backup simbólico: Firestore no usa SQLite.\n")
        return os.path.abspath(path)

    # ------------------------------------------------------------------ #
    # Terceros (third_parties): búsqueda por RNC / nombre
    # ------------------------------------------------------------------ #
    def search_third_parties(self, query: str, search_by: str = "rnc") -> List[Dict[str, Any]]:
        """
        Busca terceros en:
          1) La colección 'third_parties'
          2) Si no hay suficientes resultados, completa con terceros derivados
             de las facturas de la colección 'invoices'.
        """
        if self._db is None:
            return []

        raw_query = query
        query = (query or "").strip()
        if len(query) < 2:
            return []

        results: List[Dict[str, Any]] = []

        # 1) third_parties
        try:
            if FieldFilter is None:
                raise RuntimeError("FieldFilter no disponible")

            col = self._db.collection("third_parties")

            if self.active_company_id is not None:
                col = col.where(
                    filter=FieldFilter("company_id", "==", self.active_company_id)
                )

            if search_by == "rnc":
                start = query
                end = query + "\uf8ff"
                q = (
                    col.where(filter=FieldFilter("rnc", ">=", start))
                    .where(filter=FieldFilter("rnc", "<=", end))
                    .limit(15)
                )
            else:
                start = query.lower()
                end = start + "\uf8ff"
                q = (
                    col.where(filter=FieldFilter("name_normalized", ">=", start))
                    .where(filter=FieldFilter("name_normalized", "<=", end))
                    .limit(15)
                )

            docs = list(q.stream())
            for doc in docs:
                data = doc.to_dict() or {}
                rnc_val = str(data.get("rnc") or "")
                name_val = str(data.get("name") or "")
                if not rnc_val and not name_val:
                    continue
                results.append({"rnc": rnc_val, "name": name_val})

        except Exception as e:
            print(f"[FIREBASE] Error en search_third_parties (third_parties): {e}")

        if len(results) >= 5:
            return results

        # 2) invoices
        try:
            col_inv = self._db.collection("invoices")

            if self.active_company_id is not None:
                if FieldFilter is None:
                    col_inv = col_inv.where("company_id", "==", int(self.active_company_id))
                else:
                    col_inv = col_inv.where(
                        filter=FieldFilter("company_id", "==", int(self.active_company_id))
                    )

            inv_docs = list(col_inv.limit(1000).stream())

            existing_keys = {(r["rnc"], r["name"]) for r in results}
            extra: List[Dict[str, Any]] = []

            q_lower = query.lower()

            for doc in inv_docs:
                data = doc.to_dict() or {}
                rnc_val = str(data.get("rnc") or data.get("client_rnc") or "").strip()
                name_val = str(
                    data.get("third_party_name")
                    or data.get("client_name")
                    or ""
                ).strip()
                if not (rnc_val or name_val):
                    continue

                match = False
                if search_by == "rnc":
                    match = rnc_val.startswith(query)
                else:
                    match = name_val.lower().startswith(q_lower)

                if not match:
                    continue

                key = (rnc_val, name_val)
                if key in existing_keys:
                    continue

                extra.append({"rnc": rnc_val, "name": name_val})
                existing_keys.add(key)

                if len(results) + len(extra) >= 15:
                    break

            if extra:
                results.extend(extra)

        except Exception as e:
            print(f"[FIREBASE] Error en search_third_parties (invoices): {e}")

        return results
    # ==================================================================
    #  Cálculos de impuestos / retenciones (tax_calculations)
    # ==================================================================

    def get_emitted_invoices_for_period(
        self,
        company_id: int | None,
        start_date: str,
        end_date: str,
    ):
        """
        Devuelve facturas EMITIDAS (ingresos) para una empresa en un rango de fechas.

        - company_id: id de la empresa (int o str) o None para no filtrar.
        - start_date / end_date: strings 'YYYY-MM-DD'.
        """
        print(
            f"[DEBUG-TAX] get_emitted_invoices_for_period("
            f"company_id={company_id!r}, start_date={start_date!r}, end_date={end_date!r})"
        )

        if not self._db:
            print("[DEBUG-TAX] _db es None; devolviendo lista vacía.")
            return []

        col = self._db.collection("invoices")

        # 1) Filtro base por tipo e empresa
        try:
            if FieldFilter is not None:
                query = col.where(
                    filter=FieldFilter("invoice_type", "==", "emitida")
                )
                if company_id is not None:
                    query = query.where(
                        filter=FieldFilter("company_id", "==", int(company_id))
                    )
            else:
                # Fallback positional (puede dar warning pero mantiene compatibilidad)
                query = col.where("invoice_type", "==", "emitida")
                if company_id is not None:
                    query = query.where("company_id", "==", int(company_id))
        except Exception as e:
            print(f"[FIREBASE-TAX] Error construyendo query de facturas: {e}")
            return []

        # 2) Intentar filtrar por rango de fechas en Firestore solo si invoice_date es string
        use_python_date_filter = False
        try:
            if FieldFilter is not None:
                query = query.where(
                    filter=FieldFilter("invoice_date", ">=", start_date)
                ).where(
                    filter=FieldFilter("invoice_date", "<=", end_date)
                )
            else:
                query = query.where("invoice_date", ">=", start_date).where(
                    "invoice_date", "<=", end_date
                )
        except Exception as e:
            # Por ejemplo, si invoice_date es timestamp -> Firestore no acepta comparar con str
            print(
                "[DEBUG-TAX] No se pudo aplicar filtro de fechas en Firestore, "
                f"usaremos filtro en Python. Detalle: {e}"
            )
            use_python_date_filter = True

        try:
            docs = list(query.stream())
            print(f"[DEBUG-TAX] facturas obtenidas de Firestore (sin filtrar en Python): {len(docs)}")
        except Exception as e:
            print(f"[FIREBASE-TAX] Error ejecutando query de facturas: {e}")
            return []

        results: list[dict] = []

        # Helper para normalizar fecha si tenemos que filtrar en Python
        try:
            from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
        except Exception:
            DatetimeWithNanoseconds = type("DTWN", (), {})

        def _norm_date(value) -> datetime.date | None:
            if value is None:
                return None
            if isinstance(value, DatetimeWithNanoseconds):
                return value.date()
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, datetime.date):
                return value
            try:
                s = str(value)[:10]
                return datetime.datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None

        start_d = None
        end_d = None
        if use_python_date_filter:
            try:
                start_d = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_d = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                print(f"[DEBUG-TAX] Filtro de fechas en Python: {start_d} .. {end_d}")
            except Exception as e:
                print(f"[DEBUG-TAX] No se pudieron parsear las fechas para filtro Python: {e}")
                start_d = end_d = None

        for d in docs:
            data = d.to_dict() or {}
            data["id"] = int(d.id) if str(d.id).isdigit() else d.id

            if use_python_date_filter and start_d and end_d:
                inv_date = _norm_date(data.get("invoice_date"))
                if not inv_date:
                    continue
                if inv_date < start_d or inv_date > end_d:
                    continue

            # Asegurar campos clave para ventanas de cálculo / retenciones
            if "total_amount_rd" not in data:
                try:
                    rate = float(data.get("exchange_rate", 1.0) or 1.0)
                except Exception:
                    rate = 1.0
                try:
                    total = float(data.get("total_amount", 0.0) or 0.0)
                except Exception:
                    total = 0.0
                data["total_amount_rd"] = total * (rate or 1.0)

            data.setdefault("itbis", 0.0)
            data.setdefault("exchange_rate", 1.0)
            data.setdefault("invoice_number", "")
            data.setdefault("invoice_date", "")
            data.setdefault("third_party_name", "")

            results.append(data)

        print(f"[DEBUG-TAX] facturas devueltas tras normalizar/filtrar: {len(results)}")
        return results

    def get_tax_calculations(self, company_id: int | None):
        print(f"[DEBUG-TAX] get_tax_calculations(company_id={company_id!r})")

        if not self._db:
            print("[DEBUG-TAX] _db es None; devolviendo lista vacía.")
            return []

        col = self._db.collection("tax_calculations")

        try:
            if company_id is not None:
                if FieldFilter is not None:
                    query = col.where(
                        filter=FieldFilter("company_id", "==", int(company_id))
                    )
                else:
                    query = col.where("company_id", "==", int(company_id))
            else:
                query = col
            query = query.order_by("created_at")
        except Exception as e:
            print(f"[FIREBASE-TAX] Error construyendo query tax_calculations: {e}")
            return []

        try:
            docs = list(query.stream())
            print(f"[DEBUG-TAX] cálculos leídos de Firestore: {len(docs)}")
        except Exception as e:
            print(f"[FIREBASE-TAX] Error leyendo tax_calculations: {e}")
            return []

        results: list[dict] = []
        for d in docs:
            data = d.to_dict() or {}
            data["id"] = int(d.id) if str(d.id).isdigit() else d.id
            if "created_at" not in data and "creation_date" in data:
                data["created_at"] = data["creation_date"]
            results.append(data)

        print(f"[DEBUG-TAX] cálculos devueltos tras normalizar: {len(results)}")
        return results
    def save_tax_calculation(
        self,
        calc_id,
        company_id,
        name: str,
        start_date: str,
        end_date: str,
        percent: float,
        details: dict,
    ):
        """
        Crea o actualiza un cálculo en:
          - tax_calculations
          - tax_calculation_details

        NOTA: company_id se guarda siempre como entero (si es posible) para
        ser compatible con los filtros de get_tax_calculations.
        """
        if not self._db:
            return False, "Firestore no está inicializado."

        from firebase_admin import firestore as fb_fs

        doc_id = str(calc_id) if calc_id is not None else None

        try:
            col = self._db.collection("tax_calculations")
            if doc_id:
                doc_ref = col.document(doc_id)
            else:
                doc_ref = col.document()

            try:
                company_id_normalized = int(company_id) if company_id is not None else None
            except Exception:
                company_id_normalized = company_id

            payload = {
                "company_id": company_id_normalized,
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "percent_to_pay": float(percent or 0.0),
                "updated_at": fb_fs.SERVER_TIMESTAMP,
            }
            if not calc_id:
                payload["created_at"] = fb_fs.SERVER_TIMESTAMP

            payload = {k: v for k, v in payload.items() if v is not None}
            doc_ref.set(payload, merge=True)

            final_calc_id = int(doc_ref.id) if str(doc_ref.id).isdigit() else doc_ref.id

            details_col = self._db.collection("tax_calculation_details")
            existing = list(
                details_col.where("calculation_id", "==", final_calc_id).stream()
            )
            if existing:
                batch_del = self._db.batch()
                for d in existing:
                    batch_del.delete(d.reference)
                batch_del.commit()

            batch = self._db.batch()
            count = 0
            for inv_id, state in (details or {}).items():
                selected = bool(state.get("selected"))
                retention = bool(state.get("retention"))
                if not selected:
                    continue

                try:
                    inv_key = int(inv_id)
                except Exception:
                    inv_key = inv_id

                det_payload = {
                    "calculation_id": final_calc_id,
                    "invoice_id": inv_key,
                    "selected": selected,
                    "retention": retention,
                    "updated_at": fb_fs.SERVER_TIMESTAMP,
                }
                det_ref = details_col.document()
                batch.set(det_ref, det_payload)
                count += 1

                if count % 400 == 0:
                    batch.commit()
                    batch = self._db.batch()

            if count % 400 != 0:
                batch.commit()

            msg = (
                "Cálculo creado correctamente."
                if not calc_id
                else "Cálculo actualizado correctamente."
            )
            return True, msg

        except Exception as e:
            print(f"[FIREBASE-TAX] Error guardando cálculo: {e}")
            return False, f"Error guardando cálculo: {e}"

    def delete_tax_calculation(self, calc_id):
        """
        Elimina un cálculo y sus detalles asociados.
        """
        if not self._db:
            return False, "Firestore no está inicializado."

        if calc_id is None:
            return False, "ID de cálculo inválido."

        doc_id = str(calc_id)
        try:
            calc_ref = self._db.collection("tax_calculations").document(doc_id)
            calc_doc = calc_ref.get()
            if not calc_doc.exists:
                return False, "El cálculo no existe en Firebase."

            try:
                final_calc_id = int(doc_id)
            except Exception:
                final_calc_id = doc_id

            details_col = self._db.collection("tax_calculation_details")
            detail_docs = list(
                details_col.where("calculation_id", "==", final_calc_id).stream()
            )
            if detail_docs:
                batch = self._db.batch()
                for d in detail_docs:
                    batch.delete(d.reference)
                batch.commit()

            calc_ref.delete()

            return True, "Cálculo y sus detalles han sido eliminados."

        except Exception as e:
            print(f"[FIREBASE-TAX] Error eliminando cálculo: {e}")
            return False, f"No se pudo eliminar el cálculo: {e}"
        

    def get_tax_calculation_details(self, calc_id):
        """
        Devuelve un cálculo y sus detalles en el formato esperado por AdvancedRetentionWindowQt.
        """
        if not self._db or calc_id is None:
            return None

        doc_id = str(calc_id)

        try:
            doc = self._db.collection("tax_calculations").document(doc_id).get()
        except Exception:
            return None

        if not doc.exists:
            return None

        main = doc.to_dict() or {}
        main["id"] = int(doc.id) if str(doc.id).isdigit() else doc.id

        try:
            detail_query = (
                self._db.collection("tax_calculation_details")
                .where("calculation_id", "==", main["id"])
            )
            detail_docs = list(detail_query.stream())
        except Exception:
            detail_docs = []

        details: dict[int, dict] = {}
        for d in detail_docs:
            data = d.to_dict() or {}
            inv_id = data.get("invoice_id")
            if inv_id is None:
                continue
            try:
                key = int(inv_id)
            except Exception:
                key = inv_id
            details[key] = {
                "selected": bool(data.get("selected", False)),
                "retention": bool(data.get("retention", False)),
            }

        return {"main": main, "details": details}

    def save_tax_calculation(
        self,
        calc_id,
        company_id,
        name: str,
        start_date: str,
        end_date: str,
        percent: float,
        details: dict,
    ):
        """
        Crea o actualiza un cálculo en:
          - tax_calculations
          - tax_calculation_details
        """
        if not self._db:
            return False, "Firestore no está inicializado."

        from firebase_admin import firestore as fb_fs

        doc_id = str(calc_id) if calc_id is not None else None

        try:
            col = self._db.collection("tax_calculations")
            if doc_id:
                doc_ref = col.document(doc_id)
            else:
                doc_ref = col.document()

            payload = {
                "company_id": int(company_id) if company_id is not None else None,
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "percent_to_pay": float(percent or 0.0),
                "updated_at": fb_fs.SERVER_TIMESTAMP,
            }
            if not calc_id:
                payload["created_at"] = fb_fs.SERVER_TIMESTAMP

            payload = {k: v for k, v in payload.items() if v is not None}
            doc_ref.set(payload, merge=True)

            final_calc_id = int(doc_ref.id) if str(doc_ref.id).isdigit() else doc_ref.id

            details_col = self._db.collection("tax_calculation_details")
            existing = list(
                details_col.where("calculation_id", "==", final_calc_id).stream()
            )
            if existing:
                batch_del = self._db.batch()
                for d in existing:
                    batch_del.delete(d.reference)
                batch_del.commit()

            batch = self._db.batch()
            count = 0
            for inv_id, state in (details or {}).items():
                selected = bool(state.get("selected"))
                retention = bool(state.get("retention"))
                if not selected:
                    continue

                try:
                    inv_key = int(inv_id)
                except Exception:
                    inv_key = inv_id

                det_payload = {
                    "calculation_id": final_calc_id,
                    "invoice_id": inv_key,
                    "selected": selected,
                    "retention": retention,
                    "updated_at": fb_fs.SERVER_TIMESTAMP,
                }
                det_ref = details_col.document()
                batch.set(det_ref, det_payload)
                count += 1

                if count % 400 == 0:
                    batch.commit()
                    batch = self._db.batch()

            if count % 400 != 0:
                batch.commit()

            msg = (
                "Cálculo creado correctamente."
                if not calc_id
                else "Cálculo actualizado correctamente."
            )
            return True, msg

        except Exception as e:
            print(f"[FIREBASE-TAX] Error guardando cálculo: {e}")
            return False, f"Error guardando cálculo: {e}"

    def delete_tax_calculation(self, calc_id):
        """
        Elimina un cálculo y sus detalles asociados.
        """
        if not self._db:
            return False, "Firestore no está inicializado."

        if calc_id is None:
            return False, "ID de cálculo inválido."

        doc_id = str(calc_id)
        try:
            calc_ref = self._db.collection("tax_calculations").document(doc_id)
            calc_doc = calc_ref.get()
            if not calc_doc.exists:
                return False, "El cálculo no existe en Firebase."

            try:
                final_calc_id = int(doc_id)
            except Exception:
                final_calc_id = doc_id

            details_col = self._db.collection("tax_calculation_details")
            detail_docs = list(
                details_col.where("calculation_id", "==", final_calc_id).stream()
            )
            if detail_docs:
                batch = self._db.batch()
                for d in detail_docs:
                    batch.delete(d.reference)
                batch.commit()

            calc_ref.delete()

            return True, "Cálculo y sus detalles han sido eliminados."

        except Exception as e:
            print(f"[FIREBASE-TAX] Error eliminando cálculo: {e}")
            return False, f"No se pudo eliminar el cálculo: {e}"
        
    def get_itbis_month_summary(
        self,
        company_id: int | None,
        month_str: str | None,
        year_int: int | None,
    ) -> dict:
        """
        Resume para una empresa y mes/año:
          - total_income, total_expense
          - itbis_income, itbis_expense
          - itbis_neto, total_neto

        Reutiliza _query_invoices para respetar toda la lógica de fechas.
        """
        if not self._db or not company_id:
            return {
                "total_income": 0.0,
                "total_expense": 0.0,
                "itbis_income": 0.0,
                "itbis_expense": 0.0,
                "itbis_neto": 0.0,
                "total_neto": 0.0,
            }

        invoices = self._query_invoices(
            company_id=company_id,
            month_str=month_str,
            year_int=year_int,
            tx_type=None,
        )

        def _fx(inv: dict) -> float:
            try:
                rate = float(inv.get("exchange_rate", 1.0) or 1.0)
                return rate if rate != 0 else 1.0
            except Exception:
                return 1.0

        total_income = 0.0
        total_expense = 0.0
        itbis_income = 0.0
        itbis_expense = 0.0

        for inv in invoices:
            tipo = inv.get("invoice_type")
            total_rd = float(inv.get("total_amount_rd", inv.get("total_amount", 0.0)))
            itbis_orig = float(inv.get("itbis", 0.0))
            itbis_rd = itbis_orig * _fx(inv)

            if tipo == "emitida":
                total_income += total_rd
                itbis_income += itbis_rd
            elif tipo == "gasto":
                total_expense += total_rd
                itbis_expense += itbis_rd

        itbis_neto = itbis_income - itbis_expense
        total_neto = total_income - total_expense

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "itbis_income": itbis_income,
            "itbis_expense": itbis_expense,
            "itbis_neto": itbis_neto,
            "total_neto": total_neto,
        }
    
    def get_itbis_adelantado(self, company_id) -> float:
        """Obtiene el ITBIS adelantado para una empresa específica (desde companies.itbis_adelantado)."""
        if not self._db or company_id is None:
            return 0.0
        try:
            doc = self._db.collection("companies").document(str(company_id)).get()
            if not doc.exists:
                return 0.0
            data = doc.to_dict() or {}
            return float(data.get("itbis_adelantado", 0.0) or 0.0)
        except Exception:
            return 0.0

    def update_itbis_adelantado(self, company_id, value: float) -> bool:
        """Actualiza el ITBIS adelantado para una empresa específica (companies.itbis_adelantado)."""
        if not self._db or company_id is None:
            return False
        try:
            self._db.collection("companies").document(str(company_id)).set(
                {"itbis_adelantado": float(value or 0.0)}, merge=True
            )
            return True
        except Exception as e:
            print(f"[FIREBASE] Error al actualizar ITBIS adelantado: {e}")
            return False
        
    # ------------------------------------------------------------------
    # ITBIS adelantado por periodo (empresa + mes + año)
    # ------------------------------------------------------------------
    def get_itbis_adelantado_period(
        self,
        company_id: int | None,
        month_str: str | None,
        year_int: int | None,
    ) -> float:
        """
        Devuelve el ITBIS adelantado para company_id en un mes/año específico.
        Usa la colección 'itbis_adelantado_period'.
        """
        if not self._db or company_id is None or not month_str or year_int is None:
            return 0.0
        try:
            doc_id = f"{company_id}_{year_int}_{month_str}"
            doc = self._db.collection("itbis_adelantado_period").document(doc_id).get()
            if not doc.exists:
                return 0.0
            data = doc.to_dict() or {}
            return float(data.get("amount", 0.0) or 0.0)
        except Exception:
            return 0.0

    def update_itbis_adelantado_period(
        self,
        company_id: int | None,
        month_str: str | None,
        year_int: int | None,
        value: float,
    ) -> bool:
        """
        Actualiza/crea el ITBIS adelantado para company_id, mes y año en
        la colección 'itbis_adelantado_period'.
        """
        if not self._db or company_id is None or not month_str or year_int is None:
            return False
        try:
            from firebase_admin import firestore as fb_fs
        except Exception:
            fb_fs = None

        try:
            doc_id = f"{company_id}_{year_int}_{month_str}"
            payload = {
                "company_id": int(company_id),
                "year": int(year_int),
                "month": str(month_str),
                "amount": float(value or 0.0),
            }
            if fb_fs is not None:
                payload["updated_at"] = fb_fs.SERVER_TIMESTAMP
            self._db.collection("itbis_adelantado_period").document(doc_id).set(
                payload, merge=True
            )
            return True
        except Exception as e:
            print(f"[FIREBASE] Error al actualizar ITBIS adelantado periodo: {e}")
            return False
        
    def get_monthly_report_data(
        self,
        company_id: int,
        month: int,
        year: int,
    ) -> dict:
        """
        Devuelve los datos para el reporte mensual en el mismo formato que
        usaba la versión SQLite:

        {
          "summary": {
              "total_ingresos": float,
              "total_gastos": float,
              "total_neto": float,
              "itbis_ingresos": float,
              "itbis_gastos": float,
              "itbis_neto": float,
          },
          "emitted_invoices": [ ... ],
          "expense_invoices": [ ... ],
        }

        - Usa _query_invoices para obtener las facturas de ese mes/año.
        - Calcula montos en RD$ respetando exchange_rate y total_amount_rd.
        """
        if not self._db or not company_id:
            return {
                "summary": {
                    "total_ingresos": 0.0,
                    "total_gastos": 0.0,
                    "total_neto": 0.0,
                    "itbis_ingresos": 0.0,
                    "itbis_gastos": 0.0,
                    "itbis_neto": 0.0,
                },
                "emitted_invoices": [],
                "expense_invoices": [],
            }

        # mes como string "01".."12" para _query_invoices
        month_str = f"{int(month):02d}"
        year_int = int(year)

        # Traer TODAS las facturas del mes (emitidas + gastos)
        invoices = self._query_invoices(
            company_id=company_id,
            month_str=month_str,
            year_int=year_int,
            tx_type=None,
        )

        emitted = [inv for inv in invoices if inv.get("invoice_type") == "emitida"]
        expenses = [inv for inv in invoices if inv.get("invoice_type") == "gasto"]

        def _fx(inv: dict) -> float:
            try:
                rate = float(inv.get("exchange_rate", 1.0) or 1.0)
                return rate if rate != 0 else 1.0
            except Exception:
                return 1.0

        # Totales por grupo
        total_ingresos = 0.0
        total_gastos = 0.0
        itbis_ingresos = 0.0
        itbis_gastos = 0.0

        for inv in emitted:
            rate = _fx(inv)
            total_rd = float(inv.get("total_amount_rd", 0.0) or 0.0)
            if not total_rd:
                total_rd = float(inv.get("total_amount", 0.0) or 0.0) * rate
            itbis_orig = float(inv.get("itbis", 0.0) or 0.0)
            total_ingresos += total_rd
            itbis_ingresos += itbis_orig * rate

        for inv in expenses:
            rate = _fx(inv)
            total_rd = float(inv.get("total_amount_rd", 0.0) or 0.0)
            if not total_rd:
                total_rd = float(inv.get("total_amount", 0.0) or 0.0) * rate
            itbis_orig = float(inv.get("itbis", 0.0) or 0.0)
            total_gastos += total_rd
            itbis_gastos += itbis_orig * rate

        itbis_neto = itbis_ingresos - itbis_gastos
        total_neto = total_ingresos - total_gastos

        summary = {
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "total_neto": total_neto,
            "itbis_ingresos": itbis_ingresos,
            "itbis_gastos": itbis_gastos,
            "itbis_neto": itbis_neto,
        }

        # El reporte espera listas "emitted_invoices" y "expense_invoices"
        # con los campos que ya se usan en ReportWindowQt y report_generator.
        return {
            "summary": summary,
            "emitted_invoices": emitted,
            "expense_invoices": expenses,
        }
    
    def get_report_by_third_party(
        self,
        company_id: int | None,
        rnc: str,
    ) -> dict:
        """
        Devuelve un reporte resumido por tercero (cliente/proveedor) para la empresa dada.

        Formato:
        {
          "summary": {
            "total_ingresos": float,
            "total_gastos": float,
          },
          "emitted_invoices": [ ... ],   # facturas 'emitida' para ese RNC
          "expense_invoices": [ ... ],   # facturas 'gasto'   para ese RNC
        }

        - Filtra por company_id (si se pasa) y por rnc en la colección 'invoices'.
        - No limita por mes/año; es histórico completo para ese tercero y empresa.
        """
        if not self._db or not rnc:
            return {
                "summary": {
                    "total_ingresos": 0.0,
                    "total_gastos": 0.0,
                },
                "emitted_invoices": [],
                "expense_invoices": [],
            }

        rnc = str(rnc).strip()
        if not rnc:
            return {
                "summary": {
                    "total_ingresos": 0.0,
                    "total_gastos": 0.0,
                },
                "emitted_invoices": [],
                "expense_invoices": [],
            }

        try:
            col = self._db.collection("invoices")

            # Filtro por empresa si se proporciona
            if company_id is not None:
                col = col.where("company_id", "==", int(company_id))

            # Filtro por RNC (campo 'rnc' o 'client_rnc' como fallback)
            # No podemos hacer OR en Firestore, así que primero probamos rnc,
            # y si no hay suficientes resultados, intentamos client_rnc.
            emitted: list[dict] = []
            expenses: list[dict] = []

            # Helper para sumar totales
            def _fx(inv: dict) -> float:
                try:
                    rate = float(inv.get("exchange_rate", 1.0) or 1.0)
                    return rate if rate != 0 else 1.0
                except Exception:
                    return 1.0

            # 1) Buscar por campo 'rnc'
            q_base = col.where("rnc", "==", rnc)
            docs = list(q_base.stream())

            # 2) Si no hay nada y el RNC está grabado como client_rnc, intentamos ese campo
            if not docs:
                q_base = col.where("client_rnc", "==", rnc)
                docs = list(q_base.stream())

            invoices: list[dict] = []
            for d in docs:
                data = d.to_dict() or {}
                data["id"] = d.id
                invoices.append(data)

            # Separar por tipo
            for inv in invoices:
                tipo = inv.get("invoice_type")
                if tipo == "emitida":
                    emitted.append(inv)
                elif tipo == "gasto":
                    expenses.append(inv)

            # Calcular totales (en RD$)
            total_ingresos = 0.0
            total_gastos = 0.0

            for inv in emitted:
                rate = _fx(inv)
                total_rd = float(inv.get("total_amount_rd", 0.0) or 0.0)
                if not total_rd:
                    total_rd = float(inv.get("total_amount", 0.0) or 0.0) * rate
                total_ingresos += total_rd

            for inv in expenses:
                rate = _fx(inv)
                total_rd = float(inv.get("total_amount_rd", 0.0) or 0.0)
                if not total_rd:
                    total_rd = float(inv.get("total_amount", 0.0) or 0.0) * rate
                total_gastos += total_rd

            summary = {
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
            }

            return {
                "summary": summary,
                "emitted_invoices": emitted,
                "expense_invoices": expenses,
            }

        except Exception as e:
            print(f"[FIREBASE-REPORT] Error en get_report_by_third_party: {e}")
            return {
                "summary": {
                    "total_ingresos": 0.0,
                    "total_gastos": 0.0,
                },
                "emitted_invoices": [],
                "expense_invoices": [],
            }
        
    def download_invoice_attachments_for_report(
        self,
        invoices: list[dict],
    ) -> dict[str, str]:
        """
        Descarga anexos de facturas desde Firebase Storage a una carpeta temporal
        para usarlos en los reportes.

        Usa SOLO rutas de Storage:
            - attachment_storage_path
            - storage_path
        """
        import tempfile
        import os

        result: dict[str, str] = {}

        if not self._bucket or not invoices:
            return result

        try:
            temp_dir = tempfile.mkdtemp(prefix="facturas_report_")
        except Exception:
            return result

        for inv in invoices:
            try:
                inv_id = str(inv.get("id") or inv.get("invoice_number") or "")
                if not inv_id:
                    continue

                storage_path = (
                    inv.get("attachment_storage_path")
                    or inv.get("storage_path")
                    or None
                )
                if not storage_path:
                    continue

                sp = str(storage_path).strip().replace("\\", "/")
                if not sp:
                    continue

                blob = self._bucket.blob(sp)

                base_name = os.path.basename(sp) or f"{inv_id}.bin"
                local_path = os.path.join(temp_dir, base_name)

                blob.download_to_filename(local_path)
                result[inv_id] = local_path

            except Exception as e:
                print(f"[FIREBASE-STORAGE] Error descargando adjunto para reporte: {e}")
                continue

        return result
    
    def migrate_invoice_attachment_from_local(
        self,
        invoice: dict,
        local_full_path: str,
    ) -> bool:
        """
        Dado un invoice (dict) y una ruta local ABSOLUTA a su anexo,
        sube el archivo a Firebase Storage y actualiza el documento
        de 'invoices' con attachment_storage_path.

        No sobreescribe si el invoice ya tiene attachment_storage_path.
        Devuelve True si migró y actualizó, False si no hizo nada.
        """
        # Validaciones básicas
        if not self._db or not self._bucket:
            return False
        if not local_full_path or not os.path.exists(local_full_path):
            return False

        # Si ya tiene ruta en Storage, no migramos
        if invoice.get("attachment_storage_path") or invoice.get("storage_path"):
            return False

        doc_id = invoice.get("id")
        if not doc_id:
            return False

        company_id = invoice.get("company_id")
        invoice_number = invoice.get("invoice_number") or invoice.get("número_de_factura")
        invoice_date = invoice.get("invoice_date") or invoice.get("fecha")
        rnc = invoice.get("rnc") or invoice.get("client_rnc") or invoice.get("rnc_cédula")

        # Normalizar invoice_date a datetime.date
        inv_date_py = None
        try:
            if isinstance(invoice_date, datetime.date):
                inv_date_py = invoice_date
            elif isinstance(invoice_date, datetime.datetime):
                inv_date_py = invoice_date.date()
            elif invoice_date:
                s = str(invoice_date)
                inv_date_py = datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
        except Exception:
            inv_date_py = None

        try:
            # Subir al Storage usando la lógica ya existente
            sp = self.upload_attachment_to_storage(
                local_path=str(local_full_path),
                company_id=company_id,
                invoice_number=str(invoice_number or doc_id),
                invoice_date=inv_date_py,
                rnc=str(rnc or ""),
            )
            if not sp:
                return False

            # Actualizar documento en Firestore
            col = self._db.collection("invoices")
            col.document(str(doc_id)).update({"attachment_storage_path": sp})

            print(
                f"[MIGRA-ON-REPORT] doc_id={doc_id}, fact={invoice_number}: "
                f"attachment_storage_path='{sp}'"
            )
            return True

        except Exception as e:
            print(f"[MIGRA-ON-REPORT] Error migrando anexo para doc_id={doc_id}: {e}")
            return False
        
    # —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # Métodos para editar / eliminar / ver adjuntos desde la GUI moderna
    # —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

    def _find_invoice_doc_by_number(self, invoice_number: str):
        """
        Busca un documento en 'invoices' por company_id + invoice_number.
        Devuelve (doc_ref, data) o (None, None).
        """
        if not self._db or not self.active_company_id or not invoice_number:
            return None, None

        try:
            col = self._db.collection("invoices")
            if FieldFilter is None:
                q = (
                    col.where("company_id", "==", int(self.active_company_id))
                    .where("invoice_number", "==", invoice_number)
                    .limit(1)
                )
            else:
                q = (
                    col.where(
                        filter=FieldFilter("company_id", "==", int(self.active_company_id))
                    )
                    .where(filter=FieldFilter("invoice_number", "==", invoice_number))
                    .limit(1)
                )
            docs = list(q.stream())
            if not docs:
                return None, None
            doc = docs[0]
            data = doc.to_dict() or {}
            data["id"] = doc.id
            return doc.reference, data
        except Exception as e:
            print(f"[FIREBASE] Error buscando invoice {invoice_number}: {e}")
            return None, None

    def edit_invoice_by_number(self, invoice_number: str, parent=None):
        """
        Abre la ventana de edición para la factura dada por invoice_number.
        Usa las ventanas clásicas AddInvoiceWindowQt / AddExpenseWindowQt
        y les inyecta los datos luego de crearlas.
        """
        if not self._db or not self.active_company_id:
            raise RuntimeError("Firestore o empresa activa no disponibles.")

        from PyQt6.QtWidgets import QApplication
        from add_invoice_window_qt import AddInvoiceWindowQt
        from add_expense_window_qt import AddExpenseWindowQt

        doc_ref, data = self._find_invoice_doc_by_number(invoice_number)
        if not doc_ref or not data:
            raise RuntimeError("Factura no encontrada en Firebase.")

        tipo = data.get("invoice_type", "")
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("No hay QApplication activa.")
        if parent is None:
            parent = app.activeWindow()

        # Normalizar fechas para los diálogos (datetime.date)
        def _to_date(v):
            if not v:
                return None
            if isinstance(v, datetime.datetime):
                return v.date()
            if isinstance(v, datetime.date):
                return v
            try:
                s = str(v)
                return datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                return None

        data["invoice_date"] = _to_date(data.get("invoice_date"))

        # on_save que actualiza el documento existente
        def on_save(dialog, form_data, invoice_type, invoice_id=None):
            fecha = form_data.get("invoice_date") or form_data.get("fecha")
            invoice_num = (
                form_data.get("invoice_number")
                or form_data.get("número_de_factura")
                or invoice_number
            )
            currency = form_data.get("currency") or form_data.get("moneda")
            rnc = form_data.get("rnc") or form_data.get("rnc_cédula")
            tercero = (
                form_data.get("third_party_name")
                or form_data.get("empresa_a_la_que_se_emitió")
                or form_data.get("empresa")
                or form_data.get("lugar_de_compra_empresa")
            )
            itbis = form_data.get("itbis") or 0.0
            total = (
                form_data.get("total_amount")
                or form_data.get("factura_total")
                or 0.0
            )
            exchange = (
                form_data.get("exchange_rate")
                or form_data.get("tasa_cambio")
                or 1.0
            )
            attach = form_data.get("attachment_path")
            attach_storage = form_data.get("attachment_storage_path")

            try:
                itbis = float(itbis)
            except Exception:
                itbis = 0.0
            try:
                total = float(total)
            except Exception:
                total = 0.0
            try:
                exchange = float(exchange)
            except Exception:
                exchange = 1.0

            update_data = {
                "invoice_date": fecha,
                "imputation_date": fecha,
                "invoice_number": invoice_num,
                "rnc": rnc,
                "third_party_name": tercero,
                "currency": currency,
                "itbis": itbis,
                "total_amount": total,
                "exchange_rate": exchange,
                "attachment_path": attach,
            }
            if attach_storage is not None:
                update_data["attachment_storage_path"] = attach_storage

            ok, msg = True, "Actualizado en Firebase."
            try:
                if isinstance(fecha, datetime.date) and not isinstance(fecha, datetime.datetime):
                    update_data["invoice_date"] = datetime.datetime(
                        fecha.year, fecha.month, fecha.day
                    )
                doc_ref.update(update_data)
            except Exception as e:
                ok, msg = False, f"Error actualizando factura: {e}"
            return ok, msg

        # Crear diálogo sin existing_invoice (tu __init__ no lo acepta)
        if tipo == "emitida":
            dlg = AddInvoiceWindowQt(
                parent=parent,
                controller=self,
                tipo_factura="emitida",
                on_save=on_save,
            )
        else:
            dlg = AddExpenseWindowQt(
                parent=parent,
                controller=self,
                on_save=on_save,
            )

        # Inyectar datos en el formulario si el diálogo lo soporta
        # Probamos varios nombres típicos para no romper nada:
        loaded = False
        for attr in ("load_from_dict", "set_form_data", "set_initial_data"):
            fn = getattr(dlg, attr, None)
            if callable(fn):
                try:
                    fn(data)
                    loaded = True
                    break
                except Exception as e:
                    print(f"[FIREBASE] Error usando {attr} en diálogo de edición: {e}")

        # Si no hay método específico, como mínimo intentamos un setter genérico
        if not loaded and hasattr(dlg, "set_data") and callable(getattr(dlg, "set_data")):
            try:
                dlg.set_data(data)
            except Exception as e:
                print(f"[FIREBASE] Error usando set_data en diálogo de edición: {e}")

        dlg.exec()

    def delete_invoice_by_number(self, invoice_number: str, parent=None):
        """
        Elimina una factura por invoice_number (y empresa activa).
        También intenta borrar el adjunto en Storage si existe attachment_storage_path.
        """
        if not self._db or not self.active_company_id:
            raise RuntimeError("Firestore o empresa activa no disponibles.")

        doc_ref, data = self._find_invoice_doc_by_number(invoice_number)
        if not doc_ref or not data:
            raise RuntimeError("Factura no encontrada en Firebase.")

        # Borrar adjunto en Storage si existe
        try:
            storage_path = data.get("attachment_storage_path") or data.get("storage_path")
            if self._bucket and storage_path:
                sp = str(storage_path).replace("\\", "/")
                blob = self._bucket.blob(sp)
                try:
                    blob.delete()
                except Exception:
                    print(f"[FIREBASE] No se pudo borrar blob {sp}")
        except Exception as e:
            print(f"[FIREBASE] Error al intentar borrar adjunto: {e}")

        # Borrar el doc de Firestore
        try:
            doc_ref.delete()
        except Exception as e:
            raise RuntimeError(f"No se pudo borrar el documento en Firestore: {e}")

    def view_invoice_attachment_by_number(self, invoice_number: str, parent=None):
        """
        Abre el adjunto de la factura:
        - Si tiene attachment_storage_path => bajar de Storage a temp y abrir.
        - Si no, intenta attachment_path local.
        """
        import tempfile
        import webbrowser

        if not self._db:
            raise RuntimeError("Firestore no está inicializado.")

        doc_ref, data = self._find_invoice_doc_by_number(invoice_number)
        if not doc_ref or not data:
            raise RuntimeError("Factura no encontrada en Firebase.")

        # 1) Intentar desde Storage
        storage_path = data.get("attachment_storage_path") or data.get("storage_path")
        if self._bucket and storage_path:
            try:
                sp = str(storage_path).replace("\\", "/")
                blob = self._bucket.blob(sp)
                if not blob.exists():
                    raise RuntimeError("El adjunto en Storage no existe.")
                tmp_dir = tempfile.mkdtemp(prefix="facturas_attach_")
                local_name = os.path.basename(sp) or f"{invoice_number}.bin"
                local_path = os.path.join(tmp_dir, local_name)
                blob.download_to_filename(local_path)
                webbrowser.open(local_path)
                return
            except Exception as e:
                print(f"[FIREBASE] Error obteniendo adjunto desde Storage: {e}")

        # 2) Fallback: ruta local (attachment_path)
        local_path = data.get("attachment_path")
        if local_path and os.path.exists(local_path):
            webbrowser.open(local_path)
            return

        raise RuntimeError("La factura no tiene adjunto disponible.")
    
    # ==================================================================
    #  Reportes PDF para tax_calculations usando report_generator
    # ==================================================================

    def generate_tax_calculation_pdf(self, calc_id, output_path: str) -> tuple[bool, str]:
        """
        Genera un reporte PDF para un cálculo de impuestos (tax_calculation)
        utilizando report_generator.generate_tax_calculation_pdf(report_data, output_path).
        """
        if not self._db:
            return False, "Firestore no está inicializado."

        if calc_id is None:
            return False, "ID de cálculo inválido."

        try:
            import report_generator
        except Exception as e:
            return False, f"No se pudo importar report_generator: {e}"

        # 1) Obtener cálculo y detalles desde Firebase
        details = self.get_tax_calculation_details(calc_id)
        if not details:
            return False, "No se encontraron datos para el cálculo solicitado."

        main = details.get("main") or {}
        det_map = details.get("details") or {}

        company_id = main.get("company_id") or self.active_company_id
        if not company_id:
            return False, "No hay empresa asociada al cálculo."

        # 2) Obtener facturas emitidas para el rango de fechas del cálculo
        start_date = main.get("start_date")
        end_date = main.get("end_date")
        if not (start_date and end_date):
            return False, "El cálculo no tiene rango de fechas definido."

        emitted_invoices = self.get_emitted_invoices_for_period(
            company_id=company_id,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        if not emitted_invoices:
            return False, "No hay facturas emitidas en el periodo del cálculo."

        # 3) Marcar en cada factura si está incluida / retenida según det_map
        for inv in emitted_invoices:
            inv_id = inv.get("id")
            sel_info = det_map.get(inv_id) or det_map.get(str(inv_id)) or {}
            inv["selected_for_calc"] = bool(sel_info.get("selected", False))
            inv["has_retention"] = bool(sel_info.get("retention", False))

        # 4) Preparar datos para report_generator
        try:
            calc_name = main.get("name") or f"Cálculo {calc_id}"
            percent = float(main.get("percent_to_pay", 0.0) or 0.0)
        except Exception:
            calc_name = f"Cálculo {calc_id}"
            percent = 0.0

        report_data = {
            "calculation": {
                "id": main.get("id", calc_id),
                "name": calc_name,
                "company_id": company_id,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "percent_to_pay": percent,
                "created_at": str(main.get("created_at", "")),
                "updated_at": str(main.get("updated_at", "")),
            },
            "invoices": emitted_invoices,
        }

        # 5) Llamar a la función del generador de reportes
        try:
            res = report_generator.generate_tax_calculation_pdf(
                report_data=report_data,
                output_path=output_path,
            )
        except TypeError:
            # Por si tu función no usa kwargs
            try:
                res = report_generator.generate_tax_calculation_pdf(
                    report_data, output_path
                )
            except Exception as e:
                return False, f"Error generando el PDF: {e}"
        except Exception as e:
            return False, f"Error generando el PDF: {e}"

        if isinstance(res, tuple) and len(res) >= 1:
            ok = bool(res[0])
            msg = res[1] if len(res) > 1 else ""
        else:
            ok = bool(res)
            msg = ""

        if not ok:
            return False, msg or "El generador de reportes devolvió error."

        return True, msg or f"Reporte generado en: {output_path}"

    def open_tax_calculation_pdf(self, calc_id, parent=None) -> None:
        """
        Helper para la UI:

        - Genera el PDF en una carpeta temporal.
        - Lo abre con el visor de PDFs del sistema.
        """
        import tempfile
        import webbrowser

        if calc_id is None:
            try:
                from PyQt6.QtWidgets import QMessageBox
                if parent is not None:
                    QMessageBox.warning(parent, "Reporte", "ID de cálculo inválido.")
                else:
                    print("[FIREBASE-TAX] ID de cálculo inválido.")
            except Exception:
                print("[FIREBASE-TAX] ID de cálculo inválido.")
            return

        try:
            tmp_dir = tempfile.mkdtemp(prefix="tax_calc_")
            file_name = f"tax_calculation_{calc_id}.pdf"
            pdf_path = os.path.join(tmp_dir, file_name)

            ok, msg = self.generate_tax_calculation_pdf(
                calc_id=calc_id,
                output_path=pdf_path,
            )
            if not ok:
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    if parent is not None:
                        QMessageBox.critical(
                            parent,
                            "Reporte",
                            msg or "No se pudo generar el reporte.",
                        )
                    else:
                        print("[FIREBASE-TAX] Error:", msg)
                except Exception:
                    print("[FIREBASE-TAX] Error:", msg)
                return

            webbrowser.open(pdf_path)
        except Exception as e:
            try:
                from PyQt6.QtWidgets import QMessageBox
                if parent is not None:
                    QMessageBox.critical(
                        parent,
                        "Reporte",
                        f"No se pudo generar/abrir el PDF: {e}",
                    )
                else:
                    print(f"[FIREBASE-TAX] No se pudo generar/abrir el PDF: {e}")
            except Exception:
                print(f"[FIREBASE-TAX] No se pudo generar/abrir el PDF: {e}")
                
    def open_tax_calculation_pdf(self, calc_id, parent=None) -> None:
        """
        Helper para la UI (TaxCalculationManagementWindowQt):

        - Genera el PDF en una carpeta temporal.
        - Lo abre con el visor de PDFs del sistema.
        """
        import tempfile
        import webbrowser

        success = False
        message = ""

        try:
            tmp_dir = tempfile.mkdtemp(prefix="tax_calc_")
            file_name = f"tax_calculation_{calc_id}.pdf"
            pdf_path = os.path.join(tmp_dir, file_name)

            success, message = self.generate_tax_calculation_pdf(
                calc_id=calc_id,
                output_path=pdf_path,
            )
            if not success:
                QMessageBox = None
                try:
                    from PyQt6.QtWidgets import QMessageBox as _QMB
                    QMessageBox = _QMB
                except Exception:
                    pass
                if QMessageBox is not None and parent is not None:
                    QMessageBox.critical(
                        parent,
                        "Reporte",
                        message or "No se pudo generar el reporte.",
                    )
                else:
                    print("[FIREBASE-TAX] Error:", message)
                return

            webbrowser.open(pdf_path)
        except Exception as e:
            try:
                from PyQt6.QtWidgets import QMessageBox
                if parent is not None:
                    QMessageBox.critical(
                        parent,
                        "Reporte",
                        f"No se pudo generar/abrir el PDF: {e}",
                    )
                else:
                    print(f"[FIREBASE-TAX] No se pudo generar/abrir el PDF: {e}")
            except Exception:
                print(f"[FIREBASE-TAX] No se pudo generar/abrir el PDF: {e}")