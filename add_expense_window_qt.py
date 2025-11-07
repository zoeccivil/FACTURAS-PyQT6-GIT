# add_expense_window_qt.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QDateEdit,
    QComboBox, QLineEdit, QPushButton, QGroupBox, QSpacerItem, QSizePolicy,
    QMessageBox, QFileDialog, QDialogButtonBox, QFrame, QListWidget, QListWidgetItem,
    QInputDialog
)
from PyQt6.QtCore import Qt, QDate, QPoint, QSize
from PyQt6.QtGui import QDoubleValidator, QPixmap
import os
import shutil
import datetime
import subprocess
import platform
import tempfile
from pathlib import Path

from attachment_editor_window_qt import AttachmentEditorWindowQt


class AddExpenseWindowQt(QDialog):
    def __init__(self, parent=None, controller=None, on_save=None, existing_data=None, invoice_id=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.on_save = on_save
        self.existing_data = existing_data or {}
        self.invoice_id = invoice_id or self.existing_data.get("id")
        self.invoice_type = "gasto"
        
        # <-- 1. AÑADIR REFERENCIA PARA EL EDITOR NO MODAL
        self.editor_instance = None

        self.attachment_relative_path = ""
        self._pending_temp_attachment = None

        self._suggestion_popup = QListWidget(self)
        self._suggestion_popup.setWindowFlags(Qt.WindowType.ToolTip)
        self._suggestion_popup.itemClicked.connect(self._on_suggestion_item_clicked)
        self._suggestion_target = None

        self.setWindowTitle("Registrar Factura de Gasto")
        self.setModal(True)
        self.setMinimumWidth(640)

        self._build_ui()
        self._load_existing()
        self._connect_signals()

    # (El método _build_ui no necesita cambios)
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        gb = QGroupBox("Datos Factura de Gastos")
        form = QFormLayout()
        gb.setLayout(form)

        # Botón cargar y ver anexo (arriba)
        self.btn_load_and_show = QPushButton("Cargar y Ver Anexo para Imputar Datos...")
        form.addRow(self.btn_load_and_show)

        # Fecha
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form.addRow(QLabel("Fecha:"), self.date_edit)

        # Número de factura
        self.invoice_number_le = QLineEdit()
        self.invoice_number_le.setPlaceholderText("B0100000123 / E3100000123 ...")
        form.addRow(QLabel("Número de Factura:"), self.invoice_number_le)

        # Moneda y tasa
        hcur = QHBoxLayout()
        self.currency_cb = QComboBox()
        if self.controller and hasattr(self.controller, "get_all_currencies"):
            try:
                self.currency_cb.addItems(self.controller.get_all_currencies())
            except Exception:
                self.currency_cb.addItems(["RD$", "USD", "EUR"])
        else:
            self.currency_cb.addItems(["RD$", "USD", "EUR"])
        self.currency_cb.setFixedWidth(120)
        hcur.addWidget(self.currency_cb)

        self.exchange_rate_le = QLineEdit()
        self.exchange_rate_le.setValidator(QDoubleValidator(0.0, 1e9, 6))
        self.exchange_rate_le.setFixedWidth(100)
        self.exchange_rate_le.setText("1.0")
        hcur.addWidget(self.exchange_rate_le)
        hcur.addStretch()
        form.addRow(QLabel("Moneda / Tasa:"), hcur)

        # RNC
        self.rnc_le = QLineEdit()
        self.rnc_le.setPlaceholderText("RNC o Cédula del tercero")
        form.addRow(QLabel("RNC/Cédula:"), self.rnc_le)

        # Lugar de compra / Empresa
        self.third_party_le = QLineEdit()
        self.third_party_le.setPlaceholderText("Lugar de Compra / Nombre del proveedor")
        form.addRow(QLabel("Lugar de Compra/Empresa:"), self.third_party_le)

        # ITBIS + Calc
        hitbis = QHBoxLayout()
        self.itbis_le = QLineEdit()
        self.itbis_le.setValidator(QDoubleValidator(0.0, 1e12, 2))
        self.itbis_le.setPlaceholderText("0.00")
        hitbis.addWidget(self.itbis_le)
        self.btn_calc_itbis = QPushButton("Calc")
        self.btn_calc_itbis.setFixedWidth(60)
        hitbis.addWidget(self.btn_calc_itbis)
        hitbis.addStretch()
        form.addRow(QLabel("ITBIS:"), hitbis)

        # Factura total + Calc
        htotal = QHBoxLayout()
        self.total_le = QLineEdit()
        self.total_le.setValidator(QDoubleValidator(0.0, 1e14, 2))
        self.total_le.setPlaceholderText("0.00")
        htotal.addWidget(self.total_le)
        self.btn_calc_total = QPushButton("Calc")
        self.btn_calc_total.setFixedWidth(60)
        htotal.addWidget(self.btn_calc_total)
        htotal.addStretch()
        form.addRow(QLabel("Factura Total:"), htotal)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(gb)
        main_layout.addWidget(sep)

        # Comprobante Adjunto section
        adj_layout = QVBoxLayout()
        lbl = QLabel("Comprobante Adjunto:")
        adj_layout.addWidget(lbl)

        h_attach = QHBoxLayout()
        self.attachment_display = QLabel("")  # muestra ruta relativa
        self.attachment_display.setWordWrap(True)
        self.attachment_display.setStyleSheet("color: blue; font-style: italic;")
        h_attach.addWidget(self.attachment_display, 1)

        btns = QHBoxLayout()
        self.btn_attach_file = QPushButton("Adjuntar sin ver...")
        self.btn_remove_attach = QPushButton("Quitar")
        self.btn_preview_attach = QPushButton("Ver")
        btns.addWidget(self.btn_attach_file)
        btns.addWidget(self.btn_remove_attach)
        btns.addWidget(self.btn_preview_attach)
        h_attach.addLayout(btns)

        adj_layout.addLayout(h_attach)
        main_layout.addLayout(adj_layout)

        # Spacer + buttons
        main_layout.addItem(QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        bb = QDialogButtonBox()
        self.btn_save = QPushButton("Guardar")
        self.btn_cancel = QPushButton("Cancelar")
        bb.addButton(self.btn_save, QDialogButtonBox.ButtonRole.AcceptRole)
        bb.addButton(self.btn_cancel, QDialogButtonBox.ButtonRole.RejectRole)
        main_layout.addWidget(bb)

    # (El resto de los métodos hasta llegar a los manejadores de anexos no cambian)
    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.btn_attach_file.clicked.connect(self._attach_file)
        self.btn_remove_attach.clicked.connect(self._remove_attachment)
        self.btn_preview_attach.clicked.connect(self._load_and_show_attachment)
        self.btn_load_and_show.clicked.connect(self._on_load_and_show_clicked)
        self.rnc_le.textChanged.connect(lambda txt: self._on_keyup(txt, 'rnc'))
        self.third_party_le.textChanged.connect(lambda txt: self._on_keyup(txt, 'name'))
        self.btn_calc_itbis.clicked.connect(self._calc_itbis_from_total)
        self.btn_calc_total.clicked.connect(self._calc_total_from_itbis)
    
    def _load_existing(self):
        d = self.existing_data
        try:
            if not d:
                return
            if d.get("invoice_date"):
                try:
                    y, m, day = map(int, str(d.get("invoice_date")).split("-")[:3])
                    self.date_edit.setDate(QDate(y, m, day))
                except Exception:
                    pass
            self.invoice_number_le.setText(str(d.get("invoice_number") or ""))
            self.currency_cb.setCurrentText(str(d.get("currency") or "RD$"))
            self.exchange_rate_le.setText(str(d.get("exchange_rate") if d.get("exchange_rate") is not None else "1.0"))
            self.rnc_le.setText(str(d.get("rnc") or ""))
            self.third_party_le.setText(str(d.get("third_party_name") or ""))
            self.itbis_le.setText(str(d.get("itbis") or "0.00"))
            if d.get("total_amount") is not None:
                self.total_le.setText(str(d.get("total_amount")))
            ap = d.get("attachment_path")
            if ap:
                self.attachment_relative_path = ap
                self.attachment_display.setText(ap)
        except Exception as e:
            print("Error cargando datos existentes en AddExpenseWindowQt:", e)
    
    def _on_keyup(self, text: str, search_by: str):
        try:
            q = text.strip()
            if len(q) < 2:
                self._suggestion_popup.hide()
                return
            results = []
            if self.controller and hasattr(self.controller, "search_third_parties"):
                try:
                    results = self.controller.search_third_parties(q, search_by=search_by)
                except Exception:
                    results = []
            if not results:
                self._suggestion_popup.hide()
                return

            self._suggestion_popup.clear()
            for r in results:
                display = f"{r.get('rnc','')} - {r.get('name','')}"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, r)
                self._suggestion_popup.addItem(item)

            if search_by == 'rnc':
                widget = self.rnc_le
            else:
                widget = self.third_party_le
            self._suggestion_target = search_by
            pos = widget.mapToGlobal(widget.rect().bottomLeft())
            self._suggestion_popup.move(pos + QPoint(0, 2))
            self._suggestion_popup.setFixedWidth(widget.width() + 150)
            self._suggestion_popup.show()
        except Exception as e:
            print("Error en _on_keyup suggestions:", e)
            self._suggestion_popup.hide()

    def _on_suggestion_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        self._apply_suggestion(data)

    def _apply_suggestion(self, data: dict):
        if not data:
            return
        try:
            rnc = data.get("rnc") or data.get("rnc_cedula") or ""
            name = data.get("name") or data.get("third_party_name") or ""
            self.rnc_le.setText(str(rnc))
            self.third_party_le.setText(str(name))
        finally:
            self._suggestion_popup.hide()
    
    def _get_attachment_base(self) -> str:
        try:
            if self.controller and hasattr(self.controller, "get_attachment_base_path"):
                base = self.controller.get_attachment_base_path()
                if base:
                    return str(Path(base))
            if self.controller and hasattr(self.controller, "get_setting"):
                base = self.controller.get_setting("attachments_root", "")
                if base:
                    return str(Path(base))
        except Exception:
            pass
        default = Path.cwd() / "attachments"
        default.mkdir(parents=True, exist_ok=True)
        return str(default)

    def _store_attachment(self, source_path: str) -> str | None:
        try:
            if not source_path or not os.path.exists(source_path):
                QMessageBox.critical(self, "Error", "El archivo seleccionado no existe.")
                return None
            base_path = self._get_attachment_base()
            company_name = None
            try:
                if self.parent and hasattr(self.parent, "company_selector"):
                    company_name = self.parent.company_selector.currentText()
                elif self.controller and hasattr(self.controller, "get_active_company_name"):
                    company_name = self.controller.get_active_company_name()
            except Exception:
                company_name = None
            company_name = company_name or "company"
            safe_company = "".join(c for c in company_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
            try:
                invoice_date = self.date_edit.date().toPyDate()
            except Exception:
                invoice_date = datetime.date.today()
            year = invoice_date.strftime("%Y")
            month = invoice_date.strftime("%m")
            dest_folder = Path(base_path) / safe_company / year / month
            dest_folder.mkdir(parents=True, exist_ok=True)
            invoice_part = "".join(c for c in (self.invoice_number_le.text().strip() or "") if (c.isalnum() or c in ("-", "_"))).strip() or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            rnc_part = "".join(c for c in (self.rnc_le.text().strip() or "") if (c.isalnum() or c in ("-", "_"))).strip() or "noRNC"
            orig_name = Path(source_path).name
            ext = Path(orig_name).suffix.lower() or ""
            dest_name = f"{invoice_part}_{rnc_part}{ext}"
            dest_path = dest_folder / dest_name
            if dest_path.exists():
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_name = f"{invoice_part}_{rnc_part}_{ts}{ext}"
                dest_path = dest_folder / dest_name
            shutil.copy2(source_path, str(dest_path))
            try:
                relative = os.path.relpath(str(dest_path), base_path)
            except Exception:
                relative = str(dest_path)
            return relative
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar anexo", f"No se pudo guardar el anexo:\n{e}")
            return None

    def _attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar anexo (imágenes o PDF)", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff *.tif *.svg);;PDF (*.pdf);;Todos los archivos (*.*)")
        if not file_path:
            return
        rel = self._store_attachment(file_path)
        if rel:
            self.attachment_relative_path = rel
            self.attachment_display.setText(rel)
            QMessageBox.information(self, "Adjunto guardado", f"El anexo se guardó en:\n{rel}")

    # <-- 2. MODIFICAR _on_load_and_show_clicked
    def _on_load_and_show_clicked(self):
        # Si ya hay una instancia del editor abierta, solo tráela al frente.
        if self.editor_instance and self.editor_instance.isVisible():
            self.editor_instance.activateWindow()
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar anexo (imágenes o PDF)", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff *.tif *.svg);;PDF (*.pdf);;Todos los archivos (*.*)")
        if not file_path:
            return

        try:
            ext = Path(file_path).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tf:
                temp_path = tf.name
            shutil.copy2(file_path, temp_path)
            
            if ext.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".svg"):
                # Crear la instancia del editor
                self.editor_instance = AttachmentEditorWindowQt(self, temp_path)
                # Conectar la señal 'saved' al nuevo manejador
                self.editor_instance.saved.connect(self._on_editor_saved)
                # Mostrar la ventana de forma no modal
                self.editor_instance.show()
            else:
                # El comportamiento para otros archivos no cambia
                if platform.system() == "Windows": os.startfile(temp_path)
                elif platform.system() == "Darwin": subprocess.run(["open", temp_path], check=False)
                else: subprocess.run(["xdg-open", temp_path], check=False)
                # Para archivos no editables, se considera pendiente inmediatamente
                self._pending_temp_attachment = temp_path
                self.attachment_display.setText(f"(temp) {Path(temp_path).name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo preparar el anexo temporal: {e}")

    # <-- 3. CREAR NUEVO MÉTODO MANEJADOR (SLOT)
    def _on_editor_saved(self, saved_temp_path):
        """
        Este método se activa cuando el editor emite la señal 'saved'.
        """
        self._pending_temp_attachment = saved_temp_path
        display_name = f"(temp) {Path(saved_temp_path).name}"
        self.attachment_display.setText(display_name)
        self._prompt_attachment_metadata_if_missing()

    # (El resto del archivo AddExpenseWindowQt no necesita cambios)
    def _load_and_show_attachment(self):
        rel = getattr(self, "attachment_relative_path", "") or ""
        if not rel:
            if getattr(self, "_pending_temp_attachment", None):
                full = self._pending_temp_attachment
                if os.path.exists(full):
                    # Usar la misma lógica no modal aquí también
                    if self.editor_instance and self.editor_instance.isVisible():
                        self.editor_instance.activateWindow()
                    else:
                        self.editor_instance = AttachmentEditorWindowQt(self, full)
                        self.editor_instance.saved.connect(self._on_editor_saved)
                        self.editor_instance.show()
                    return
            resp = QMessageBox.question(self, "Adjuntar", "No hay anexo asociado. ¿Deseas seleccionar uno ahora?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp == QMessageBox.StandardButton.Yes:
                self._on_load_and_show_clicked()
            return
        
        base = self._get_attachment_base()
        full = str(Path(base) / rel) if not os.path.isabs(rel) else rel
        if not os.path.exists(full):
            QMessageBox.critical(self, "No Existe", f"No se encontró el archivo en la ruta esperada:\n{full}")
            return
        
        if any(full.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".svg")):
            if self.editor_instance and self.editor_instance.isVisible():
                self.editor_instance.activateWindow()
            else:
                self.editor_instance = AttachmentEditorWindowQt(self, full)
                self.editor_instance.saved.connect(self._on_editor_saved)
                self.editor_instance.show()
            return
            
        try:
            if platform.system() == "Windows": os.startfile(full)
            elif platform.system() == "Darwin": subprocess.run(["open", full], check=False)
            else: subprocess.run(["xdg-open", full], check=False)
        except Exception as e:
            QMessageBox.critical(self, "Error Abrir Archivo", f"No se pudo abrir el archivo:\n{e}")

    def _prompt_attachment_metadata_if_missing(self):
        try:
            need_rnc = not self.rnc_le.text().strip()
            need_name = not self.third_party_le.text().strip()
            if not (need_rnc or need_name):
                return
            suggested = os.path.splitext(os.path.basename(self._pending_temp_attachment or self.attachment_relative_path or ""))[0]
            if need_name:
                text, ok = QInputDialog.getText(self, "Nombre de Empresa", "Introduce el nombre de la empresa para este anexo:", text=suggested)
                if ok and text.strip():
                    self.third_party_le.setText(text.strip())
            if need_rnc:
                text2, ok2 = QInputDialog.getText(self, "RNC / Cédula", "Introduce el RNC o cédula (opcional):", text="")
                if ok2 and text2.strip():
                    self.rnc_le.setText(text2.strip())
        except Exception as e:
            print("Error prompting metadata:", e)
    
    def _finalize_temp_attachment(self, temp_path: str) -> str | None:
        if not temp_path or not os.path.exists(temp_path):
            return None
        try:
            base_path = self._get_attachment_base()
            company_name = None
            try:
                if self.parent and hasattr(self.parent, "company_selector"):
                    company_name = self.parent.company_selector.currentText()
                elif self.controller and hasattr(self.controller, "get_active_company_name"):
                    company_name = self.controller.get_active_company_name()
            except Exception:
                company_name = None
            company_name = company_name or "company"
            safe_company = "".join(c for c in company_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
            try:
                invoice_date = self.date_edit.date().toPyDate()
            except Exception:
                invoice_date = datetime.date.today()
            year = invoice_date.strftime("%Y")
            month = invoice_date.strftime("%m")
            dest_folder = Path(base_path) / safe_company / year / month
            dest_folder.mkdir(parents=True, exist_ok=True)
            invoice_part = "".join(c for c in (self.invoice_number_le.text().strip() or "") if (c.isalnum() or c in ("-", "_"))).strip() or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            rnc_part = "".join(c for c in (self.rnc_le.text().strip() or "") if (c.isalnum() or c in ("-", "_"))).strip() or "noRNC"
            ext = Path(temp_path).suffix.lower()
            dest_name = f"{invoice_part}_{rnc_part}{ext}"
            dest_path = dest_folder / dest_name
            if dest_path.exists():
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_name = f"{invoice_part}_{rnc_part}_{ts}{ext}"
                dest_path = dest_folder / dest_name
            shutil.copy2(temp_path, str(dest_path))
            try:
                relative = os.path.relpath(str(dest_path), base_path)
            except Exception:
                relative = str(dest_path)
            # optionally remove temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return relative
        except Exception as e:
            QMessageBox.critical(self, "Error al finalizar anexo", f"No se pudo mover el anexo temporal:\n{e}")
            return None

    def _calc_itbis_from_total(self):
        try:
            total = float(str(self.total_le.text()).replace(",", "") or 0.0)
            rate_percent = 18.0
            itbis = (total * rate_percent) / (100.0 + rate_percent)
            self.itbis_le.setText(f"{itbis:,.2f}")
        except Exception:
            QMessageBox.warning(self, "Cálculo", "No se pudo calcular ITBIS desde el total. Verifica el valor ingresado.")

    def _calc_total_from_itbis(self):
        try:
            itbis = float(str(self.itbis_le.text()).replace(",", "") or 0.0)
            rate_percent = 18.0
            total = itbis * (100.0 + rate_percent) / rate_percent if rate_percent else itbis
            self.total_le.setText(f"{total:,.2f}")
        except Exception:
            QMessageBox.warning(self, "Cálculo", "No se pudo calcular Total desde ITBIS. Verifica el valor ingresado.")

    def _g(self, key, default=""):
        m = {
            "fecha": self.date_edit.date().toString("yyyy-MM-dd"),
            "tipo_de_factura": "Factura de Gasto",
            "número_de_factura": self.invoice_number_le.text().strip(),
            "moneda": self.currency_cb.currentText(),
            "tasa_cambio": self.exchange_rate_le.text().strip(),
            "rnc_cédula": self.rnc_le.text().strip(),
            "empresa_a_la_que_se_emitió": self.third_party_le.text().strip(),
            "lugar_de_compra_empresa": self.third_party_le.text().strip(),
            "itbis": self.itbis_le.text().replace(",", "").strip(),
            "factura_total": self.total_le.text().replace(",", "").strip()
        }
        return m.get(key, default)

    def _on_save_clicked(self):
        import traceback
        try:
            pending = getattr(self, "_pending_temp_attachment", None)
            if pending:
                rel_final = self._finalize_temp_attachment(pending)
                if rel_final:
                    self.attachment_relative_path = rel_final
                    self.attachment_display.setText(rel_final)
                    self._pending_temp_attachment = None
                else:
                    QMessageBox.critical(self, "Error", "No se pudo finalizar el anexo temporal. Revisa el anexo o intenta adjuntarlo nuevamente.")
                    return
        except Exception as e:
            tb = traceback.format_exc()
            print("Error finalizando anexo temporal:\n", tb)
            QMessageBox.critical(self, "Error", f"Error finalizando anexo temporal: {e}")
            return
        
        if not self._g("número_de_factura"):
            QMessageBox.warning(self, "Validación", "El número de factura no puede estar vacío.")
            return
        if not self._g("rnc_cédula"):
            QMessageBox.warning(self, "Validación", "El RNC/Cédula no puede estar vacío.")
            return

        attachment_val = getattr(self, "attachment_relative_path", "") or None

        def _to_float(s, default=0.0):
            if s is None: return float(default)
            if isinstance(s, (int, float)): return float(s)
            ss = str(s).replace(",", "").strip()
            if ss == "": return float(default)
            try: return float(ss)
            except Exception: return float(default)

        try:
            fecha_py = self.date_edit.date().toPyDate()
            invoice_num = self.invoice_number_le.text().strip()
            currency = self.currency_cb.currentText()
            try:
                exchange_rate = _to_float(self.exchange_rate_le.text(), default=1.0)
            except Exception:
                exchange_rate = 1.0
            rnc = self.rnc_le.text().strip()
            third_party = self.third_party_le.text().strip()

            form_data = {
                "fecha": fecha_py, "tipo_de_factura": "Factura de Gasto", "número_de_factura": invoice_num,
                "moneda": currency, "tasa_cambio": exchange_rate, "rnc_cédula": rnc,
                "empresa_a_la_que_se_emitió": third_party, "lugar_de_compra_empresa": third_party,
                "itbis": _to_float(self.itbis_le.text(), default=0.0), "factura_total": _to_float(self.total_le.text(), default=0.0),
                "invoice_type": "gasto", "invoice_date": fecha_py, "invoice_number": invoice_num,
                "currency": currency, "exchange_rate": exchange_rate, "rnc": rnc, "third_party_name": third_party,
                "itbis": _to_float(self.itbis_le.text(), default=0.0), "total_amount": _to_float(self.total_le.text(), default=0.0),
                "attachment_path": attachment_val,
                "company_id": (self.parent.get_current_company_id() if self.parent and hasattr(self.parent, "get_current_company_id") else None)
            }
        except Exception as e:
            tb = traceback.format_exc()
            print("Traceback preparing form_data:\n", tb)
            QMessageBox.critical(self, "Error", f"Error preparando datos: {e}")
            return
        
        if callable(self.on_save):
            try:
                try: result = self.on_save(self, form_data, self.invoice_type, self.invoice_id)
                except TypeError: result = self.on_save(self, form_data, self.invoice_type)

                if isinstance(result, tuple) and len(result) >= 1:
                    success, message = result[0], (result[1] if len(result) > 1 else "")
                    if success: self.accept()
                    else: QMessageBox.warning(self, "Error", message or "No se pudo guardar la factura.")
                else: pass
            except Exception as e:
                tb = traceback.format_exc()
                print("Traceback in on_save callback:\n", tb)
                QMessageBox.critical(self, "Error al Guardar", f"Ocurrió un error al guardar: {e}")
            return

        try:
            if self.invoice_id and hasattr(self.controller, "update_invoice"):
                success, message = self.controller.update_invoice(self.invoice_id, form_data)
                if success:
                    QMessageBox.information(self, "Éxito", message)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", message)
                return
            elif not self.invoice_id and hasattr(self.controller, "add_invoice"):
                success, message = self.controller.add_invoice(form_data)
                if success:
                    QMessageBox.information(self, "Éxito", message)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", message)
                return
            else:
                QMessageBox.information(self, "Info", "No hay callback ni métodos del controlador para guardar. Cerrando.")
                self.accept()
                return
        except KeyError as ke:
            tb = traceback.format_exc()
            print("KeyError saving invoice:\n", tb)
            QMessageBox.critical(self, "Error", f"Falta clave en los datos: {ke}")
            return
        except Exception as e:
            tb = traceback.format_exc()
            print("Traceback saving invoice:\n", tb)
            QMessageBox.critical(self, "Error", f"No se pudo guardar la factura: {e}")
            return
        
    def _to_float(self, s, default=0.0):
        if s is None: return float(default)
        if isinstance(s, (int, float)): return float(s)
        ss = str(s).replace(",", "").strip()
        if ss == "": return float(default)
        return float(ss)

    def _remove_attachment(self):
        try:
            rel = getattr(self, "attachment_relative_path", "") or ""
            if not rel:
                self.attachment_relative_path = ""
                if hasattr(self, "attachment_display"): self.attachment_display.setText("")
                return

            try: base = self._get_attachment_base()
            except Exception: base = None

            full_path = str(Path(base) / rel) if base and not os.path.isabs(rel) else rel

            if full_path and os.path.exists(full_path):
                resp = QMessageBox.question(
                    self,
                    "Eliminar anexo",
                    "¿Deseas eliminar también el archivo físico del anexo?\n\n(Si no, sólo se quitará la referencia en la ventana)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp == QMessageBox.StandardButton.Yes:
                    try:
                        os.remove(full_path)
                        QMessageBox.information(self, "Archivo eliminado", "El archivo del anexo fue eliminado correctamente.")
                    except Exception as e:
                        QMessageBox.warning(self, "No se pudo eliminar", f"No fue posible eliminar el archivo:\n{e}")
            
            self.attachment_relative_path = ""
            if hasattr(self, "attachment_display"):
                self.attachment_display.setText("")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al quitar el anexo: {e}")