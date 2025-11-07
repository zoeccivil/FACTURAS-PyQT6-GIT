# Migrated ReportWindow -> PyQt6 version (modificada para permitir maximizar y manejo de columnas)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
import report_generator
import datetime
from pathlib import Path
import os


class ReportWindowQt(QDialog):
    """
    Ventana de Reportes (PyQt6).
    - Maximizable y redimensionable.
    - Tablas con columnas ajustables por el usuario y que llenan siempre el ancho disponible.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.report_data = None

        # Título y tamaño inicial
        self.setWindowTitle(f"Reporte Mensual para {self.parent.company_selector.currentText() if hasattr(self.parent, 'company_selector') else ''}")
        self.resize(1000, 700)

        # Habilitar botones de ventana (minimizar/maximizar) y que actúe como ventana normal
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        # Mostrar grip de tamaño en la esquina
        self.setSizeGripEnabled(True)

        self._build_ui()
        # llenar años disponibles y generar reporte inicial
        self._populate_years()
        self._generate_report()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Controls row
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Mes:"))
        self.month_cb = QComboBox()
        self.month_cb.addItems([str(i) for i in range(1, 13)])
        self.month_cb.setCurrentIndex(QDate.currentDate().month() - 1)
        controls.addWidget(self.month_cb)

        controls.addWidget(QLabel("Año:"))
        self.year_cb = QComboBox()
        self.year_cb.setEditable(False)
        controls.addWidget(self.year_cb)

        btn_generate = QPushButton("Generar Reporte")
        btn_generate.clicked.connect(self._generate_report)
        controls.addWidget(btn_generate)

        btn_pdf = QPushButton("Exportar a PDF")
        btn_pdf.clicked.connect(self._export_pdf)
        controls.addWidget(btn_pdf)

        btn_xlsx = QPushButton("Exportar a Excel")
        btn_xlsx.clicked.connect(self._export_excel)
        controls.addWidget(btn_xlsx)

        controls.addStretch()
        main.addLayout(controls)

        # Summary area (group box)
        summary_group = QGroupBox("Resumen General del Mes (RD$)")
        summary_layout = QVBoxLayout()
        self.summary_labels = {}
        items = [
            ("Total Ingresos", "total_ingresos"),
            ("Total Gastos", "total_gastos"),
            ("Total Neto", "total_neto"),
            ("ITBIS Ingresos", "itbis_ingresos"),
            ("ITBIS Gastos", "itbis_gastos"),
            ("ITBIS Neto", "itbis_neto")
        ]
        for label_text, key in items:
            row = QHBoxLayout()
            lbl = QLabel(f"{label_text}:")
            val = QLabel("RD$ 0.00")
            val.setStyleSheet("font-weight: bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            summary_layout.addLayout(row)
            self.summary_labels[key] = val

        summary_group.setLayout(summary_layout)
        main.addWidget(summary_group)

        # Tables area (dos tablas lado a lado que llenan el ancho)
        tables_row = QHBoxLayout()

        # Emitted invoices table
        emitted_group = QGroupBox("Facturas Emitidas (Ingresos)")
        emitted_layout = QVBoxLayout()
        self.emitted_table = QTableWidget(0, 6)
        self.emitted_table.setHorizontalHeaderLabels(['Fecha', 'No. Fact.', 'Empresa', 'Monto Original', 'ITBIS RD$', 'Total RD$'])

        eh = self.emitted_table.horizontalHeader()
        # Permitir que el usuario cambie anchos, mover secciones y que la última columna estire
        eh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh.setStretchLastSection(True)
        eh.setSectionsMovable(True)
        eh.setMinimumSectionSize(50)
        self.emitted_table.setAlternatingRowColors(True)
        self.emitted_table.setSelectionBehavior(self.emitted_table.SelectionBehavior.SelectRows)
        emitted_layout.addWidget(self.emitted_table)
        emitted_group.setLayout(emitted_layout)
        tables_row.addWidget(emitted_group, 1)

        # Expenses table
        expenses_group = QGroupBox("Facturas de Gastos")
        expenses_layout = QVBoxLayout()
        self.expenses_table = QTableWidget(0, 6)
        self.expenses_table.setHorizontalHeaderLabels(['Fecha', 'No. Fact.', 'Empresa', 'Monto Original', 'ITBIS RD$', 'Total RD$'])

        eh2 = self.expenses_table.horizontalHeader()
        eh2.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        eh2.setStretchLastSection(True)
        eh2.setSectionsMovable(True)
        eh2.setMinimumSectionSize(50)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setSelectionBehavior(self.expenses_table.SelectionBehavior.SelectRows)
        expenses_layout.addWidget(self.expenses_table)
        expenses_group.setLayout(expenses_layout)
        tables_row.addWidget(expenses_group, 1)

        main.addLayout(tables_row, 1)

    def _populate_years(self):
        self.year_cb.clear()
        try:
            company_id = self.parent.get_current_company_id()
            years = []
            if company_id and hasattr(self.controller, "get_unique_invoice_years"):
                years = self.controller.get_unique_invoice_years(company_id) or []
            years = sorted({int(y) for y in years if y not in (None, '')}, reverse=True) if years else []
        except Exception:
            years = []

        if years:
            self.year_cb.addItems([str(y) for y in years])
            self.year_cb.setCurrentIndex(0)
        else:
            self.year_cb.addItem(str(datetime.date.today().year))
            self.year_cb.setCurrentIndex(0)

    def _generate_report(self):
        try:
            month = int(self.month_cb.currentText())
            year = int(self.year_cb.currentText())
        except Exception:
            QMessageBox.critical(self, "Error", "Mes y año deben ser números válidos.")
            return

        company_id = None
        try:
            company_id = self.parent.get_current_company_id()
        except Exception:
            company_id = None
        if not company_id:
            QMessageBox.warning(self, "Sin Empresa", "Selecciona una empresa activa.")
            return

        try:
            raw = self.controller.get_monthly_report_data(company_id, month, year) or {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener datos: {e}")
            return

        # Normalizar filas (sqlite3.Row -> dict)
        def _normalize_list(lst):
            normalized = []
            for r in lst or []:
                try:
                    normalized.append(dict(r))
                except Exception:
                    if isinstance(r, dict):
                        normalized.append(r)
                    else:
                        try:
                            normalized.append({k: r[k] for k in r.keys()})
                        except Exception:
                            normalized.append(r)
            return normalized

        self.report_data = {
            "summary": raw.get("summary", {}),
            "emitted_invoices": _normalize_list(raw.get("emitted_invoices", [])),
            "expense_invoices": _normalize_list(raw.get("expense_invoices", []))
        }
        self._populate_report()

    def _populate_report(self):
        # clear tables
        for tbl in (self.emitted_table, self.expenses_table):
            tbl.setRowCount(0)

        # reset summary labels
        for key, lbl in self.summary_labels.items():
            lbl.setText("RD$ 0.00")

        if not self.report_data:
            QMessageBox.information(self, "Sin Datos", "No se encontraron transacciones para el período seleccionado.")
            return

        summary = self.report_data.get("summary", {})
        self.summary_labels.get("total_ingresos").setText(f"RD$ {summary.get('total_ingresos', 0.0):,.2f}")
        self.summary_labels.get("total_gastos").setText(f"RD$ {summary.get('total_gastos', 0.0):,.2f}")
        self.summary_labels.get("total_neto").setText(f"RD$ {summary.get('total_neto', 0.0):,.2f}")
        self.summary_labels.get("itbis_ingresos").setText(f"RD$ {summary.get('itbis_ingresos', 0.0):,.2f}")
        self.summary_labels.get("itbis_gastos").setText(f"RD$ {summary.get('itbis_gastos', 0.0):,.2f}")
        self.summary_labels.get("itbis_neto").setText(f"RD$ {summary.get('itbis_neto', 0.0):,.2f}")

        # populate emitted
        for inv in self.report_data.get("emitted_invoices", []):
            row = self.emitted_table.rowCount()
            self.emitted_table.insertRow(row)
            monto_orig = f"{inv.get('total_amount', 0.0):,.2f} {inv.get('currency', 'RD$')}"
            itbis_rd = float(inv.get('itbis', 0.0)) * float(inv.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(inv.get('total_amount_rd', 0.0))
            self.emitted_table.setItem(row, 0, QTableWidgetItem(str(inv.get('invoice_date', ''))))
            self.emitted_table.setItem(row, 1, QTableWidgetItem(str(inv.get('invoice_number', ''))))
            self.emitted_table.setItem(row, 2, QTableWidgetItem(str(inv.get('third_party_name', ''))))
            item_mo = QTableWidgetItem(monto_orig)
            item_mo.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.emitted_table.setItem(row, 3, item_mo)
            item_it = QTableWidgetItem(f"{itbis_rd:,.2f}")
            item_it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.emitted_table.setItem(row, 4, item_it)
            item_tr = QTableWidgetItem(f"{total_rd:,.2f}")
            item_tr.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.emitted_table.setItem(row, 5, item_tr)

        # populate expenses
        for inv in self.report_data.get("expense_invoices", []):
            row = self.expenses_table.rowCount()
            self.expenses_table.insertRow(row)
            monto_orig = f"{inv.get('total_amount', 0.0):,.2f} {inv.get('currency', 'RD$')}"
            itbis_rd = float(inv.get('itbis', 0.0)) * float(inv.get('exchange_rate', 1.0) or 1.0)
            total_rd = float(inv.get('total_amount_rd', 0.0))
            self.expenses_table.setItem(row, 0, QTableWidgetItem(str(inv.get('invoice_date', ''))))
            self.expenses_table.setItem(row, 1, QTableWidgetItem(str(inv.get('invoice_number', ''))))
            self.expenses_table.setItem(row, 2, QTableWidgetItem(str(inv.get('third_party_name', ''))))
            item_mo = QTableWidgetItem(monto_orig)
            item_mo.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 3, item_mo)
            item_it = QTableWidgetItem(f"{itbis_rd:,.2f}")
            item_it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 4, item_it)
            item_tr = QTableWidgetItem(f"{total_rd:,.2f}")
            item_tr.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 5, item_tr)

    def _export_pdf(self):
        if not self.report_data:
            QMessageBox.warning(self, "Sin Datos", "Primero debes generar un reporte.")
            return

        # pedir nombre de archivo
        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte PDF",
            f"Reporte_{self.parent.company_selector.currentText().replace(' ', '_')}_{self.month_cb.currentText()}_{self.year_cb.currentText()}.pdf",
            "PDF Files (*.pdf)"
        )
        if not fname:
            return

        # Obtener base path para adjuntos (puede ser None)
        attachment_base_path = None
        try:
            # prefer controller helper if available
            if hasattr(self.controller, "get_attachment_base_path"):
                attachment_base_path = self.controller.get_attachment_base_path()
            if not attachment_base_path and hasattr(self.controller, "get_setting"):
                # [LÍNEA CORREGIDA]
                attachment_base_path = self.controller.get_setting("attachments_root")
        except Exception:
            attachment_base_path = None

        # debug print to help troubleshooting
        print("[DBG] attachment_base_path:", attachment_base_path)

        # Normalizar y resolver rutas de adjuntos en report_data
        # Añadimos 'attachment_resolved' a cada invoice dict con ruta absoluta o None
        base_folder = Path(__file__).parent
        missing_attachments = []
        def _resolve_attachment_path(apath):
            if not apath:
                return None
            # normalize slashes and whitespace
            ap_norm = str(apath).strip().replace("\\", os.sep).replace("/", os.sep)
            p = Path(ap_norm)
            if p.is_absolute():
                if p.exists():
                    return str(p)
                # try normpath
                np = Path(os.path.normpath(str(p)))
                if np.exists():
                    return str(np)
                return None
            # relative path: if attachment_base_path provided, join it (normalize)
            if attachment_base_path:
                candidate = Path(os.path.normpath(os.path.join(attachment_base_path, ap_norm)))
                if candidate.exists():
                    return str(candidate)
                # try basename under base path with glob
                bname = os.path.basename(ap_norm)
                pattern = os.path.join(attachment_base_path, "**", bname)
                matches = list(Path(attachment_base_path).glob("**/" + bname))
                if matches:
                    return str(matches[0])
            # try project-relative
            candidate = base_folder / ap_norm
            if candidate.exists():
                return str(candidate)
            # try relative to current working dir
            candidate = Path.cwd() / ap_norm
            if candidate.exists():
                return str(candidate)
            # last resort: case-insensitive search under attachment_base_path (if provided)
            if attachment_base_path:
                for root, dirs, files in os.walk(attachment_base_path):
                    for f in files:
                        if f.lower() == os.path.basename(ap_norm).lower():
                            return os.path.join(root, f)
            return None

        for section in ("emitted_invoices", "expense_invoices"):
            for inv in self.report_data.get(section, []):
                # Keep existing attachment_path if present; resolve to absolute when possible
                ap = inv.get("attachment_path") or inv.get("attachment") or inv.get("anexo") or None
                resolved = _resolve_attachment_path(ap)
                inv["attachment_resolved"] = resolved
                # Debug print per invoice
                print(f"[DBG] invoice {inv.get('invoice_number')} attachment_path='{ap}' resolved='{resolved}'")
                if ap and not resolved:
                    missing_attachments.append({"invoice_number": inv.get("invoice_number"), "attachment": ap})

        # If attachments expected but missing, warn user (non-blocking)
        if missing_attachments:
            missing_list = "\n".join([f"{m['invoice_number']}: {m['attachment']}" for m in missing_attachments[:10]])
            more_note = ""
            if len(missing_attachments) > 10:
                more_note = f"\n... y {len(missing_attachments)-10} más"
            QMessageBox.warning(self, "Adjuntos no encontrados",
                                f"Algunas facturas tienen rutas de adjunto que no se encontraron:\n{missing_list}{more_note}\n\nEl reporte se generará sin esos archivos adjuntos.")
        # buscar la función en report_generator (defensivo)
        func = getattr(report_generator, "generate_professional_pdf", None)
        if func is None:
            for alt in ("generate_professional_report", "generate_pdf_report", "generate_report_pdf"):
                if hasattr(report_generator, alt):
                    func = getattr(report_generator, alt)
                    break

        if func is None:
            available = [n for n in dir(report_generator) if not n.startswith("_")]
            QMessageBox.critical(self, "Error",
                                "La función 'generate_professional_pdf' no existe en report_generator.\n"
                                f"Funciones disponibles: {', '.join(available)}\n"
                                "Revisa report_generator.py y asegúrate de definir generate_professional_pdf(...).")
            return

        # Llamada defensiva: intentamos pasar (report_data, fname, company, month, year, attachment_base_path)
        # pero nos aseguramos que report_data contiene 'attachment_resolved' por invoice.
        try:
            ok, msg = func(self.report_data, fname, self.parent.company_selector.currentText(),
                        self.month_cb.currentText(), self.year_cb.currentText(), attachment_base_path)
        except TypeError:
            # Si la firma es distinta, intentar con menos argumentos
            try:
                ok, msg = func(self.report_data, fname, self.parent.company_selector.currentText(),
                            self.month_cb.currentText(), self.year_cb.currentText())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar el PDF (firma inesperada): {e}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {e}")
            return

        if ok:
            QMessageBox.information(self, "Éxito", msg)
        else:
            QMessageBox.critical(self, "Error", msg)

    def _export_excel(self):
        if not self.report_data:
            QMessageBox.warning(self, "Sin Datos", "Primero debes generar un reporte.")
            return

        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte Excel",
            f"Reporte_{self.parent.company_selector.currentText().replace(' ', '_')}_{self.month_cb.currentText()}_{self.year_cb.currentText()}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not fname:
            return

        try:
            ok, msg = report_generator.generate_excel_report(self.report_data, fname)
            if ok:
                QMessageBox.information(self, "Éxito", msg)
            else:
                QMessageBox.critical(self, "Error", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el Excel: {e}")