# retention_calculator_window.py
#
# Calculadora clásica de retenciones (Tkinter) integrada con Firebase
# a través de LogicControllerFirebase.get_emitted_invoices_for_period
# y report_generator.generate_retention_pdf.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import datetime
import report_generator


class RetentionCalculatorWindow(tk.Toplevel):
    def __init__(self, parent, controller):
        """
        parent: ventana principal (debe exponer:
                  - root (Tk)
                  - get_current_company_id()
                  - company_selector_var (StringVar) con el nombre de la empresa)
        controller: LogicControllerFirebase (o compatible) que implemente:
                  - get_emitted_invoices_for_period(company_id, start_date, end_date)
        """
        print("[DEBUG-RET] === Abriendo RetentionCalculatorWindow ===")
        super().__init__(parent.root)
        self.parent = parent
        self.controller = controller

        # Comprobación inmediata de company_id al abrir la ventana
        try:
            cid = self.parent.get_current_company_id()
        except Exception as e:
            cid = None
            print(f"[DEBUG-RET] get_current_company_id() lanzó excepción: {e}")
        print(f"[DEBUG-RET] company_id inicial desde parent: {cid!r}")

        self.title("Calculadora de Retenciones")
        self.geometry("800x650")
        self.grab_set()

        # Datos
        self.all_invoices = []            # lista de dicts de facturas
        self.selected_invoice_ids = set() # ids seleccionados

        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # --- Panel de Filtros y Porcentajes ---
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=tk.X)

        filter_frame = ttk.LabelFrame(
            top_frame,
            text="1. Buscar Facturas de Ingreso",
            padding=10,
        )
        filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(filter_frame, text="Desde:").grid(row=0, column=0, sticky="w")
        self.start_date_entry = DateEntry(
            filter_frame,
            date_pattern="yyyy-mm-dd",
            width=12,
        )
        self.start_date_entry.grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Hasta:").grid(row=1, column=0, sticky="w")
        self.end_date_entry = DateEntry(
            filter_frame,
            date_pattern="yyyy-mm-dd",
            width=12,
        )
        self.end_date_entry.grid(row=1, column=1, padx=5)

        ttk.Button(
            filter_frame,
            text="Buscar Facturas",
            command=self._search_invoices,
        ).grid(row=0, column=2, rowspan=2, padx=10, ipady=5)

        percent_frame = ttk.LabelFrame(
            top_frame, text="2. Definir Porcentajes", padding=10
        )
        percent_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        self.itbis_perc_var = tk.StringVar(value="100.0")
        self.total_perc_var = tk.StringVar(value="4.0")

        ttk.Label(percent_frame, text="Retención sobre ITBIS (%):").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(
            percent_frame, textvariable=self.itbis_perc_var, width=8
        ).grid(row=0, column=1)

        ttk.Label(percent_frame, text="Retención sobre Total (%):").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Entry(
            percent_frame, textvariable=self.total_perc_var, width=8
        ).grid(row=1, column=1)

        # --- Panel de Selección de Facturas ---
        tree_frame = ttk.LabelFrame(
            self,
            text="3. Seleccionar Facturas para el Cálculo",
            padding=10,
        )
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("select", "Fecha", "No. Fact.", "Empresa", "Total RD$")
        self.invoice_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings"
        )

        self.invoice_tree.heading("select", text="Sel.")
        self.invoice_tree.column("select", width=40, anchor="center")

        for col in columns[1:]:
            self.invoice_tree.heading(col, text=col)
            anchor = "e" if "Total" in col else "w"
            width = 300 if col == "Empresa" else 120
            self.invoice_tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.invoice_tree.yview
        )
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        self.invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Activar/desactivar selección haciendo clic en la primera columna
        self.invoice_tree.bind("<Button-1>", self._toggle_checkbox)

        # --- Panel de Resultados y Acciones ---
        bottom_frame = ttk.Frame(self, padding=10)
        bottom_frame.pack(fill=tk.X)

        results_frame = ttk.LabelFrame(
            bottom_frame, text="4. Resultados del Cálculo", padding=10
        )
        results_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.result_labels = {}
        results = [
            "Total Seleccionado",
            "ITBIS Retenido",
            "Total Retenido",
            "TOTAL A RETENER",
        ]
        for i, item in enumerate(results):
            font = ("Arial", 11, "bold") if "TOTAL" in item else ("Arial", 10)
            ttk.Label(results_frame, text=f"{item}:", font=font).grid(
                row=i, column=0, sticky="w", padx=5
            )
            lbl = ttk.Label(results_frame, text="RD$ 0.00", font=font)
            lbl.grid(row=i, column=1, sticky="e", padx=5)
            self.result_labels[item] = lbl
        results_frame.columnconfigure(1, weight=1)

        action_frame = ttk.Frame(bottom_frame)
        action_frame.pack(side=tk.LEFT, padx=(20, 0))

        ttk.Button(
            action_frame,
            text="Exportar a PDF",
            command=self._export_pdf,
            style="Accent.TButton",
        ).pack(ipady=10, fill=tk.X)

        print("[DEBUG-RET] UI de RetentionCalculatorWindow construida correctamente.")

    # ------------------------------------------------------------------ #
    # Cargar facturas desde Firebase vía LogicControllerFirebase
    # ------------------------------------------------------------------ #
    def _search_invoices(self):
        start_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        end_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")

        try:
            company_id = self.parent.get_current_company_id()
        except Exception as e:
            print(f"[DEBUG-RET] get_current_company_id() lanzó excepción en _search_invoices: {e}")
            company_id = None

        print(
            f"[DEBUG-RET] _search_invoices company_id={company_id!r}, "
            f"rango={start_date}..{end_date}"
        )

        if company_id is None:
            messagebox.showwarning(
                "Empresa",
                "No hay empresa activa seleccionada.",
                parent=self,
            )
            return

        try:
            self.all_invoices = (
                self.controller.get_emitted_invoices_for_period(
                    company_id, start_date, end_date
                )
                or []
            )
            print(f"[DEBUG-RET] facturas recibidas del controller: {len(self.all_invoices)}")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudieron obtener las facturas desde Firebase:\n{e}",
                parent=self,
            )
            return

        # Normalizar datos mínimos esperados
        normalized = []
        for inv in self.all_invoices:
            try:
                d = dict(inv)
            except Exception:
                continue

            d.setdefault("id", d.get("invoice_id"))
            d.setdefault("invoice_date", "")
            d.setdefault("invoice_number", "")
            d.setdefault("third_party_name", "")
            if "total_amount_rd" not in d:
                try:
                    rate = float(d.get("exchange_rate", 1.0) or 1.0)
                    total = float(d.get("total_amount", 0.0) or 0.0)
                    d["total_amount_rd"] = total * rate
                except Exception:
                    d["total_amount_rd"] = 0.0
            d.setdefault("itbis", 0.0)
            d.setdefault("exchange_rate", 1.0)

            if d.get("id") is None:
                continue
            normalized.append(d)

        print(f"[DEBUG-RET] facturas tras normalizar: {len(normalized)}")
        self.all_invoices = normalized

        # Limpiar tabla y selecciones
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        self.selected_invoice_ids.clear()

        if not self.all_invoices:
            messagebox.showinfo(
                "Sin Datos",
                "No se encontraron facturas de ingreso en el rango de fechas seleccionado.",
                parent=self,
            )
            self._recalculate()
            return

        # Poblar tabla
        for inv in self.all_invoices:
            try:
                row_id = str(inv["id"])
                self.invoice_tree.insert(
                    "",
                    "end",
                    iid=row_id,
                    values=(
                        "☐",
                        str(inv.get("invoice_date", "")),
                        str(inv.get("invoice_number", "")),
                        str(inv.get("third_party_name", "")),
                        f"{float(inv.get('total_amount_rd', 0.0)):,.2f}",
                    ),
                )
            except Exception as e:
                print(f"[DEBUG-RET] Error insertando fila en Treeview: {e}")
                continue

        print(
            f"[DEBUG-RET] filas en Treeview despues de poblar: "
            f"{len(self.invoice_tree.get_children())}"
        )
        self._recalculate()

    # ------------------------------------------------------------------ #
    # Selección / deselección de filas
    # ------------------------------------------------------------------ #
    def _toggle_checkbox(self, event):
        row_id = self.invoice_tree.identify_row(event.y)
        column_id = self.invoice_tree.identify_column(event.x)

        if not row_id or column_id != "#1":
            return

        if row_id in self.selected_invoice_ids:
            self.selected_invoice_ids.remove(row_id)
            self.invoice_tree.set(row_id, "select", "☐")
        else:
            self.selected_invoice_ids.add(row_id)
            self.invoice_tree.set(row_id, "select", "☑")

        self._recalculate()

    # ------------------------------------------------------------------ #
    # Recalcular resultados
    # ------------------------------------------------------------------ #
    def _recalculate(self):
        selected_invoices = [
            inv
            for inv in self.all_invoices
            if str(inv.get("id")) in self.selected_invoice_ids
        ]

        if not selected_invoices:
            for lbl in self.result_labels.values():
                lbl.config(text="RD$ 0.00")
            return

        try:
            p_itb = float(self.itbis_perc_var.get()) / 100.0
            p_tot = float(self.total_perc_var.get()) / 100.0
        except ValueError:
            messagebox.showerror(
                "Error",
                "Los porcentajes deben ser números válidos.",
                parent=self,
            )
            return

        total_general = sum(
            float(inv.get("total_amount_rd", 0.0)) for inv in selected_invoices
        )
        total_itbis = sum(
            float(inv.get("itbis", 0.0))
            * float(inv.get("exchange_rate", 1.0) or 1.0)
            for inv in selected_invoices
        )

        ret_itbis = total_itbis * p_itb
        ret_total = total_general * p_tot
        total_a_retener = ret_itbis + ret_total

        self.result_labels["Total Seleccionado"].config(
            text=f"RD$ {total_general:,.2f}"
        )
        self.result_labels["ITBIS Retenido"].config(text=f"RD$ {ret_itbis:,.2f}")
        self.result_labels["Total Retenido"].config(text=f"RD$ {ret_total:,.2f}")
        self.result_labels["TOTAL A RETENER"].config(
            text=f"RD$ {total_a_retener:,.2f}"
        )

    # ------------------------------------------------------------------ #
    # Exportar PDF usando report_generator
    # ------------------------------------------------------------------ #
    def _export_pdf(self):
        selected_invoices = [
            inv
            for inv in self.all_invoices
            if str(inv.get("id")) in self.selected_invoice_ids
        ]
        if not selected_invoices:
            messagebox.showwarning(
                "Sin Selección",
                "Debes seleccionar al menos una factura para exportar.",
                parent=self,
            )
            return

        try:
            total_general = sum(
                float(inv.get("total_amount_rd", 0.0)) for inv in selected_invoices
            )
            total_itbis = sum(
                float(inv.get("itbis", 0.0))
                * float(inv.get("exchange_rate", 1.0) or 1.0)
                for inv in selected_invoices
            )
            total_subtotal = total_general - total_itbis

            p_itb = float(self.itbis_perc_var.get())
            p_tot = float(self.total_perc_var.get())

            ret_itbis = total_itbis * (p_itb / 100.0)
            ret_total = total_general * (p_tot / 100.0)
            total_a_retener = ret_itbis + ret_total

            results_data = {
                "num_invoices": len(selected_invoices),
                "total_general_rd": total_general,
                "total_itbis_rd": total_itbis,
                "total_subtotal_rd": total_subtotal,
                "p_itb": p_itb,
                "p_tot": p_tot,
                "ret_itbis": ret_itbis,
                "ret_total": ret_total,
                "total_a_retener": total_a_retener,
            }
        except ValueError:
            messagebox.showerror(
                "Error",
                "Los porcentajes deben ser números válidos.",
                parent=self,
            )
            return

        company_name = ""
        try:
            company_name = self.parent.company_selector_var.get()
        except Exception:
            company_name = ""

        default_name = f"Retenciones_{company_name.replace(' ', '_')}.pdf" or "Retenciones.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte de Retenciones",
            initialfile=default_name,
        )
        if not save_path:
            return

        periodo_str = (
            f"{self.start_date_entry.get()} al {self.end_date_entry.get()}"
        )

        success, message = report_generator.generate_retention_pdf(
            save_path,
            company_name,
            periodo_str,
            results_data,
            selected_invoices,
        )
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
        else:
            messagebox.showerror("Error", message, parent=self)