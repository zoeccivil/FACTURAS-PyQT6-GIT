"""
firebase_controller.py
----------------------

This module provides a simple in-memory controller that mimics the
interface of the existing SQLite-based ``LogicControllerQt``.  The
purpose of this class is to demonstrate how the application could be
adapted to use a non‑SQL backend such as Firebase (Firestore).  Since
the execution environment does not include the Firebase libraries and
credentials, the implementation here stores data in a JSON file
(`firebase_data.json`) located in the working directory.  This file
acts as a stand‑in for Firestore collections.

The controller exposes methods used by the modern GUI such as
``list_companies``, ``set_active_company``, ``add_invoice``,
``update_invoice``, ``_refresh_dashboard``, and
``_populate_transactions_table``.  Additional optional methods like
``create_sql_backup`` are stubbed to maintain compatibility with the
legacy interface.

Because the data is stored in a flat JSON file and loaded into
memory, this controller is not intended for production use.  It is a
lightweight placeholder that satisfies the interface requirements of
the GUI while avoiding any SQL usage during normal operation.

Usage:

    from firebase_controller import FirebaseController
    controller = FirebaseController()
    # pass controller to ModernMainWindow

The JSON structure is simple:

    {
      "companies": [
        {"id": 1, "name": "Acme", "rnc": "001", "address": "", "itbis_adelantado": 0.0},
        ...
      ],
      "invoices": [
        {"id": 1, "company_id": 1, "invoice_type": "emitida", "invoice_date": "2025-10-14", ...},
        ...
      ],
      "third_parties": [
        {"rnc": "123", "name": "Proveedor"},
        ...
      ]
    }
"""

from __future__ import annotations

import json
import os
import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import QMessageBox

try:
    # Attempt to import AddInvoiceWindowQt and AddExpenseWindowQt for use
    from add_invoice_window_qt import AddInvoiceWindowQt
    from add_expense_window_qt import AddExpenseWindowQt
except Exception:
    # Fallback: if these modules are not available, define None placeholders
    AddInvoiceWindowQt = None  # type: ignore
    AddExpenseWindowQt = None  # type: ignore

try:
    # Import the stylesheet from modern_gui so we can apply it to dialogs
    from modern_gui import STYLESHEET
except Exception:
    STYLESHEET = ""


class FirebaseController:
    """
    A lightweight controller that emulates a Firestore backend using a
    JSON file.  It maintains a list of companies, invoices and third
    parties in memory.  Methods mirror those in ``LogicControllerQt``
    where possible.
    """

    def __init__(self, data_path: str = "firebase_data.json") -> None:
        self.data_path = data_path
        self._load_data()
        self.active_company_id: Optional[int] = None
        self.current_tx_filter: Optional[str] = None  # 'emitida' or 'gasto' or None

    def _load_data(self) -> None:
        """Load data from JSON file into memory.  If the file does not
        exist, initialise with an empty structure."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}
        self.data: Dict[str, Any] = {
            "companies": data.get("companies", []),
            "invoices": data.get("invoices", []),
            "third_parties": data.get("third_parties", []),
        }
        # Assign incremental IDs if not present
        self._next_company_id = (
            max((c.get("id", 0) for c in self.data["companies"]), default=0) + 1
        )
        self._next_invoice_id = (
            max((i.get("id", 0) for i in self.data["invoices"]), default=0) + 1
        )

    def _save_data(self) -> None:
        """Persist the current in‑memory data back to the JSON file."""
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Company management
    # ------------------------------------------------------------------
    def list_companies(self) -> List[str]:
        """Return a list of company names."""
        return [c.get("name", "") for c in self.data["companies"]]

    def set_active_company(self, name: str) -> None:
        """Set the active company by its name.  If not found, active
        company becomes None."""
        self.active_company_id = None
        for c in self.data["companies"]:
            if c.get("name") == name:
                self.active_company_id = c.get("id")
                break

    def add_company(self, name: str, rnc: str) -> tuple[bool, str]:
        """Add a new company.  Returns success flag and message."""
        # Check duplicates
        for c in self.data["companies"]:
            if c.get("name") == name or c.get("rnc") == rnc:
                return False, "Ya existe una empresa con ese nombre o RNC."
        new_company = {
            "id": self._next_company_id,
            "name": name,
            "rnc": rnc,
            "address": "",
            "itbis_adelantado": 0.0,
        }
        self._next_company_id += 1
        self.data["companies"].append(new_company)
        self._save_data()
        return True, "Empresa añadida exitosamente."

    def get_unique_invoice_years(self, company_id: Optional[int] = None) -> List[str]:
        """Return a list of unique years (as strings) for the active
        company.  If company_id is provided, it overrides the active
        company."""
        cid = company_id or self.active_company_id
        if cid is None:
            return []
        years: set[str] = set()
        for inv in self.data["invoices"]:
            if inv.get("company_id") == cid and inv.get("invoice_date"):
                try:
                    y = str(inv["invoice_date"])[:4]
                    if y:
                        years.add(y)
                except Exception:
                    pass
        return list(years)

    # ------------------------------------------------------------------
    # Transaction filter
    # ------------------------------------------------------------------
    def set_transaction_filter(self, tx_type: Optional[str]) -> None:
        """Set the current transaction type filter (e.g. 'emitida', 'gasto' or None)."""
        self.current_tx_filter = tx_type

    # ------------------------------------------------------------------
    # Dashboard and table data
    # ------------------------------------------------------------------
    def _refresh_dashboard(self, month: Optional[str], year: Optional[int]) -> Optional[Dict[str, float]]:
        """Compute summary totals for the dashboard based on the current
        filters.  Returns a dict with keys 'income', 'income_itbis',
        'expense', 'expense_itbis', 'net_itbis', 'payable'."""
        if self.active_company_id is None:
            return None
        income = expense = income_itbis = expense_itbis = 0.0
        for inv in self.data["invoices"]:
            if inv.get("company_id") != self.active_company_id:
                continue
            # Filter by month/year if provided
            date_str = inv.get("invoice_date")
            if not date_str:
                continue
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue
            if year and dt.year != year:
                continue
            if month and dt.strftime("%m") != str(month).zfill(2):
                continue
            itbis = float(inv.get("itbis", 0.0)) * float(inv.get("exchange_rate", 1.0))
            total_rd = float(inv.get("total_amount_rd", inv.get("total_amount", 0.0))) * float(inv.get("exchange_rate", 1.0))
            if inv.get("invoice_type") == "emitida":
                income += total_rd
                income_itbis += itbis
            elif inv.get("invoice_type") == "gasto":
                expense += total_rd
                expense_itbis += itbis
        return {
            "income": income,
            "income_itbis": income_itbis,
            "expense": expense,
            "expense_itbis": expense_itbis,
            "net_itbis": income_itbis - expense_itbis,
            "payable": income_itbis - expense_itbis,
        }

    def _populate_transactions_table(
        self, month: Optional[str], year: Optional[int], tx_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Return a list of transactions for the table.  Each entry is a
        dict with keys 'date', 'type', 'number', 'party', 'itbis', and
        'total'.  Filters are applied for month, year and tx_type."""
        if self.active_company_id is None:
            return []
        rows: List[Dict[str, Any]] = []
        for inv in self.data["invoices"]:
            if inv.get("company_id") != self.active_company_id:
                continue
            # Filter by type
            if tx_type and inv.get("invoice_type") != tx_type:
                continue
            # Filter by month/year
            date_str = inv.get("invoice_date")
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue
            if year and dt.year != year:
                continue
            if month and dt.strftime("%m") != str(month).zfill(2):
                continue
            rows.append(
                {
                    "date": date_str,
                    "type": inv.get("invoice_type"),
                    "number": inv.get("invoice_number"),
                    "party": inv.get("third_party_name"),
                    "itbis": inv.get("itbis", 0.0),
                    "total": inv.get("total_amount_rd", inv.get("total_amount", 0.0)),
                    "id": inv.get("id"),
                }
            )
        # Sort by date descending
        return sorted(rows, key=lambda r: r.get("date"), reverse=True)

    # ------------------------------------------------------------------
    # Invoice management
    # ------------------------------------------------------------------
    def add_invoice(self, invoice_data: Dict[str, Any]) -> tuple[bool, str]:
        """Add a new invoice.  The invoice_data should contain the
        required keys such as company_id, invoice_date, invoice_type,
        invoice_number, rnc, third_party_name, itbis and total_amount.
        Returns (success, message)."""
        cid = invoice_data.get("company_id")
        if cid is None:
            cid = self.active_company_id
            invoice_data["company_id"] = cid
        if cid is None:
            return False, "No hay empresa activa seleccionada."
        # Simple duplicate check on invoice_number and rnc within company
        for inv in self.data["invoices"]:
            if (
                inv.get("company_id") == cid
                and inv.get("rnc") == invoice_data.get("rnc")
                and inv.get("invoice_number") == invoice_data.get("invoice_number")
            ):
                return False, "Ya existe una factura con el mismo número para este RNC."
        new_inv = invoice_data.copy()
        new_inv["id"] = self._next_invoice_id
        self._next_invoice_id += 1
        # Convert date to string if it's a date object
        date_val = invoice_data.get("invoice_date")
        if isinstance(date_val, datetime.date):
            new_inv["invoice_date"] = date_val.strftime("%Y-%m-%d")
        elif isinstance(date_val, str):
            new_inv["invoice_date"] = date_val
        else:
            new_inv["invoice_date"] = datetime.date.today().strftime("%Y-%m-%d")
        # Ensure exchange_rate numeric
        try:
            new_inv["exchange_rate"] = float(invoice_data.get("exchange_rate", 1.0) or 1.0)
        except Exception:
            new_inv["exchange_rate"] = 1.0
        # Derive total_amount_rd if not provided
        total = invoice_data.get("total_amount")
        if total is not None:
            try:
                total_rd = float(total) * new_inv["exchange_rate"]
            except Exception:
                total_rd = 0.0
        else:
            total_rd = 0.0
        new_inv["total_amount_rd"] = total_rd
        self.data["invoices"].append(new_inv)
        # Update third party directory
        self.add_or_update_third_party(invoice_data.get("rnc"), invoice_data.get("third_party_name"))
        self._save_data()
        return True, "Factura registrada exitosamente."

    def update_invoice(self, invoice_id: int, invoice_data: Dict[str, Any]) -> tuple[bool, str]:
        """Update an existing invoice by id.  Returns (success, message)."""
        # Find invoice
        target = None
        for inv in self.data["invoices"]:
            if inv.get("id") == invoice_id:
                target = inv
                break
        if not target:
            return False, "No se encontró la factura."
        # Duplicate check: other invoice with same number and rnc
        cid = target.get("company_id")
        new_num = invoice_data.get("invoice_number")
        new_rnc = invoice_data.get("rnc")
        for inv in self.data["invoices"]:
            if (
                inv.get("company_id") == cid
                and inv.get("id") != invoice_id
                and inv.get("invoice_number") == new_num
                and inv.get("rnc") == new_rnc
            ):
                return False, "Ya existe otra factura con el mismo número para este RNC."
        # Update fields
        for key, val in invoice_data.items():
            if key == "invoice_date" and isinstance(val, datetime.date):
                target[key] = val.strftime("%Y-%m-%d")
            else:
                target[key] = val
        # Update total_amount_rd
        try:
            rate = float(invoice_data.get("exchange_rate", target.get("exchange_rate", 1.0)) or 1.0)
            total = float(invoice_data.get("total_amount", target.get("total_amount", 0.0)) or 0.0)
            target["total_amount_rd"] = total * rate
        except Exception:
            pass
        # Update third party directory
        self.add_or_update_third_party(new_rnc, invoice_data.get("third_party_name"))
        self._save_data()
        return True, "Factura actualizada exitosamente."

    def delete_invoice(self, invoice_id: int) -> tuple[bool, str]:
        """Delete an invoice by id.  Returns (success, message)."""
        for idx, inv in enumerate(self.data["invoices"]):
            if inv.get("id") == invoice_id:
                del self.data["invoices"][idx]
                self._save_data()
                return True, "Factura eliminada."
        return False, "Factura no encontrada."

    # ------------------------------------------------------------------
    # Third party management
    # ------------------------------------------------------------------
    def search_third_parties(self, query: str, search_by: str = "name") -> List[Dict[str, str]]:
        """Return a list of third parties matching the query.  The search
        can be by 'name' or 'rnc'."""
        if len(query) < 2:
            return []
        results: List[Dict[str, str]] = []
        for tp in self.data.get("third_parties", []):
            val = tp.get(search_by, "").lower()
            if val.startswith(query.lower()):
                results.append({"rnc": tp.get("rnc", ""), "name": tp.get("name", "")})
            if len(results) >= 10:
                break
        return results

    def add_or_update_third_party(self, rnc: Optional[str], name: Optional[str]) -> None:
        """Add a new third party or update the name if the RNC exists."""
        if not rnc or not name:
            return
        # Normalize
        rnc = rnc.strip()
        name = name.strip()
        for tp in self.data.setdefault("third_parties", []):
            if tp.get("rnc") == rnc:
                tp["name"] = name
                self._save_data()
                return
        # Not found, append
        self.data.setdefault("third_parties", []).append({"rnc": rnc, "name": name})
        self._save_data()

    # ------------------------------------------------------------------
    # Currency management
    # ------------------------------------------------------------------
    def get_all_currencies(self) -> List[str]:
        """Return a list of supported currencies.  Firestore backend
        always returns a default set."""
        return ["RD$", "USD", "EUR"]

    # ------------------------------------------------------------------
    # Dialog actions
    # ------------------------------------------------------------------
    def open_add_invoice_window(self) -> None:
        """Open the add invoice dialog.  Applies the global stylesheet if
        available and hooks the save callback to add the invoice into the
        internal data store."""
        if AddInvoiceWindowQt is None:
            QMessageBox.information(None, "Nueva Factura", "El módulo AddInvoiceWindowQt no está disponible.")
            return
        # Callback to save the invoice
        def on_save(_dlg, form_data: Dict[str, Any], tipo: str, invoice_id: Optional[int] = None):
            if invoice_id:
                return self.update_invoice(invoice_id, form_data)
            else:
                return self.add_invoice(form_data)
        try:
            dlg = AddInvoiceWindowQt(parent=None, controller=self, tipo_factura="emitida", on_save=on_save)
            # Apply modern theme
            if STYLESHEET:
                dlg.setStyleSheet(STYLESHEET)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(None, "Nueva Factura", f"No se pudo abrir la ventana de factura: {exc}")

    def open_add_expense_window(self) -> None:
        """Open the add expense dialog (for 'gasto' type)."""
        if AddExpenseWindowQt is None:
            QMessageBox.information(None, "Nueva Gasto", "El módulo AddExpenseWindowQt no está disponible.")
            return
        def on_save(_dlg, form_data: Dict[str, Any], tipo: str, invoice_id: Optional[int] = None):
            form_data["invoice_type"] = "gasto"
            if invoice_id:
                return self.update_invoice(invoice_id, form_data)
            else:
                return self.add_invoice(form_data)
        try:
            dlg = AddExpenseWindowQt(parent=None, controller=self, tipo_factura="gasto", on_save=on_save)
            if STYLESHEET:
                dlg.setStyleSheet(STYLESHEET)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(None, "Nuevo Gasto", f"No se pudo abrir la ventana de gasto: {exc}")

    # ------------------------------------------------------------------
    # Placeholder methods for compatibility
    # ------------------------------------------------------------------
    def _open_tax_calculation_manager(self) -> None:
        QMessageBox.information(None, "Impuestos", "Gestor de impuestos no implementado en FirebaseController.")

    def _open_itbis_summary(self) -> None:
        QMessageBox.information(None, "Resumen ITBIS", "Resumen ITBIS no implementado en FirebaseController.")

    def _open_report_window(self) -> None:
        QMessageBox.information(None, "Reportes", "Reportes no implementados en FirebaseController.")

    def diagnose_row(self, number: Any) -> None:
        # In a real implementation, this could show details about the invoice.
        QMessageBox.information(None, "Diagnóstico", f"Número de factura: {number}")

    def get_sqlite_db_path(self) -> str:
        """Return empty string since FirebaseController does not use SQLite."""
        return ""

    def create_sql_backup(self, retention_days: int = 30) -> str:
        """Create a backup of the SQLite database.  Since we are not
        using SQLite, return a message indicating no action."""
        return ""

    def on_firebase_config_updated(self) -> None:
        """Hook called after Firebase configuration is updated.  Can be
        used to reload credentials or perform other setup."""
        # Currently nothing to do
        pass
