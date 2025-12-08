# add_invoice_window_qt.py
#
# Ventana de registro/edición de facturas emitidas con estilo moderno.

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QDateEdit,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate, QPoint
from PyQt6.QtGui import QDoubleValidator, QKeySequence, QShortcut, QFont
import datetime
from attachment_editor_window_qt import AttachmentEditorWindowQt


class AddInvoiceWindowQt(QDialog):
    """
    Ventana de alta/edición de factura emitida (Ingreso) con autocompletado.
    """

    def __init__(
        self,
        parent=None,
        controller=None,
        tipo_factura="emitida",
        on_save=None,
        existing_data=None,
        invoice_id=None,
    ):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.on_save = on_save
        self.existing_data = existing_data or {}
        self.invoice_id = invoice_id or self.existing_data.get("id")
        self.tipo_factura = tipo_factura or "emitida"

        self.setWindowTitle(
            "Registrar Factura Emitida"
            if self.tipo_factura == "emitida"
            else "Registrar Factura de Gasto"
        )
        self.setModal(True)
        self.resize(720, 460)

        # Suggestion widget (hidden until needed)
        self._suggestion_popup = QListWidget(self)
        self._suggestion_popup.setWindowFlags(Qt.WindowType.ToolTip)
        self._suggestion_popup.itemClicked.connect(self._on_suggestion_item_clicked)
        self._suggestion_target = None  # 'rnc' or 'name'

        # History for undo/redo (basic)
        self._history = []
        self._history_index = -1
        self._is_restoring = False

        self._apply_styles()
        self._build_ui()
        self._load_existing()
        self._connect_signals()

        self._push_history()
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self._redo)

    # ------------------------------------------------------------------ #
    # Estilos
    # ------------------------------------------------------------------ #
    def _apply_styles(self):
        self.setObjectName("invoiceDialog")
        self.setStyleSheet("""
        QDialog#invoiceDialog {
            background-color: #E5E7EB;
            font-family: Inter, Segoe UI, Roboto, sans-serif;
            font-size: 13px;
            color: #111827;
        }
        QFrame#dialogCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }
        QLabel#dialogTitle {
            font-size: 16px;
            font-weight: 600;
            color: #0F172A;
        }
        QLabel#dialogSubtitle {
            font-size: 12px;
            color: #6B7280;
        }
        QGroupBox {
            border: none;
            font-weight: 600;
            margin-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 0;
            padding: 0 0 4px 0;
            color: #64748B;
            text-transform: uppercase;
            font-size: 11px;
        }
        QLabel {
            color: #4B5563;
        }
        QLineEdit, QDateEdit, QComboBox {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;
        }
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
            border-color: #3B82F6;
        }
        QPushButton#primaryButton {
            background-color: #1E293B;
            color: #FFFFFF;
            padding: 6px 16px;
            border-radius: 6px;
            font-weight: 500;
            border: none;
        }
        QPushButton#primaryButton:hover {
            background-color: #0F172A;
        }
        QPushButton#secondaryButton {
            background-color: #F9FAFB;
            color: #374151;
            padding: 6px 14px;
            border-radius: 6px;
            border: 1px solid #D1D5DB;
            font-weight: 500;
        }
        QPushButton#secondaryButton:hover {
            background-color: #E5E7EB;
        }
        QPushButton#ghostButton {
            background-color: transparent;
            color: #6B7280;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid #E5E7EB;
            font-weight: 500;
        }
        QPushButton#ghostButton:disabled {
            color: #9CA3AF;
        }
        """)

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        title = QLabel("Registrar Factura Emitida")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Registra una factura de ingreso emitida a un cliente. "
            "Los datos se guardarán en Firebase y actualizarán el dashboard."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("dialogSubtitle")
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(line)

        gb = QGroupBox("Datos de Factura de Ingreso")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        gb.setLayout(form)

        # Fecha
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form.addRow(QLabel("Fecha:"), self.date_edit)

        # Tipo de factura
        self.tipo_cb = QComboBox()
        self.tipo_cb.addItems(["Factura Privada", "Factura Pública", "Otra"])
        form.addRow(QLabel("Tipo de Factura:"), self.tipo_cb)

        # Número de factura
        self.invoice_number_le = QLineEdit()
        self.invoice_number_le.setPlaceholderText("B0100000123 / E3100000123 ...")
        form.addRow(QLabel("Número de Factura:"), self.invoice_number_le)

        # Moneda / Tasa
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
        self.exchange_rate_le.setFixedWidth(120)
        self.exchange_rate_le.setText("1.0")
        hcur.addWidget(self.exchange_rate_le)
        hcur.addStretch()
        form.addRow(QLabel("Moneda / Tasa:"), hcur)

        # RNC
        self.rnc_le = QLineEdit()
        self.rnc_le.setPlaceholderText("RNC o Cédula del tercero")
        form.addRow(QLabel("RNC/Cédula:"), self.rnc_le)

        # Empresa / Cliente tercero
        self.third_party_le = QLineEdit()
        self.third_party_le.setPlaceholderText("Nombre del cliente / proveedor")
        form.addRow(QLabel("Empresa a la que se emitió:"), self.third_party_le)

        # ITBIS + Calc
        self.itbis_le = QLineEdit()
        self.itbis_le.setValidator(QDoubleValidator(0.0, 1e12, 2))
        self.itbis_le.setPlaceholderText("0.00")
        self._calc_itbis_btn = QPushButton("Calc")
        self._calc_itbis_btn.setFixedWidth(70)
        hitbis = QHBoxLayout()
        hitbis.addWidget(self.itbis_le)
        hitbis.addWidget(self._calc_itbis_btn)
        hitbis.addStretch()
        form.addRow(QLabel("ITBIS:"), hitbis)

        # Factura total + Calc
        self.total_le = QLineEdit()
        self.total_le.setValidator(QDoubleValidator(0.0, 1e14, 2))
        self.total_le.setPlaceholderText("0.00")
        self._calc_total_btn = QPushButton("Calc")
        self._calc_total_btn.setFixedWidth(70)
        htotal = QHBoxLayout()
        htotal.addWidget(self.total_le)
        htotal.addWidget(self._calc_total_btn)
        htotal.addStretch()
        form.addRow(QLabel("Factura Total:"), htotal)

        card_layout.addWidget(gb)

        # Botones inferiores (Guardar / Deshacer / Rehacer / Cancelar)
        card_layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")

        self.btn_undo = QPushButton("Deshacer")
        self.btn_undo.setObjectName("ghostButton")
        self.btn_undo.setEnabled(False)

        self.btn_redo = QPushButton("Rehacer")
        self.btn_redo.setObjectName("ghostButton")
        self.btn_redo.setEnabled(False)

        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("primaryButton")

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_undo)
        btn_row.addWidget(self.btn_redo)
        btn_row.addWidget(self.btn_save)

        card_layout.addLayout(btn_row)

        outer.addWidget(card)



    # ------------------------------------------------------------------ #
    # Señales
    # ------------------------------------------------------------------ #
    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save_clicked)

        self.rnc_le.textChanged.connect(lambda txt: self._on_keyup(txt, "rnc"))
        self.third_party_le.textChanged.connect(
            lambda txt: self._on_keyup(txt, "name")
        )

        self.btn_undo.clicked.connect(self._undo)
        self.btn_redo.clicked.connect(self._redo)

        self.invoice_number_le.textChanged.connect(lambda _: self._push_history())
        self.exchange_rate_le.textChanged.connect(lambda _: self._push_history())
        self.rnc_le.textChanged.connect(lambda _: self._push_history())
        self.third_party_le.textChanged.connect(lambda _: self._push_history())
        self.itbis_le.textChanged.connect(lambda _: self._push_history())
        self.total_le.textChanged.connect(lambda _: self._push_history())
        self.currency_cb.currentIndexChanged.connect(lambda _: self._push_history())
        self.tipo_cb.currentIndexChanged.connect(lambda _: self._push_history())
        self.date_edit.dateChanged.connect(lambda _: self._push_history())

        # calc buttons (opcional, siguen como placeholders)
        # self._calc_itbis_btn.clicked.connect(self._calc_itbis)
        # self._calc_total_btn.clicked.connect(self._calc_total)

    # ------------------------------------------------------------------ #
    # Carga de datos existentes
    # ------------------------------------------------------------------ #
    def _load_existing(self):
        d = self.existing_data
        try:
            if not d:
                return
            if d.get("invoice_date"):
                try:
                    y, m, day = map(
                        int, str(d.get("invoice_date")).split("-")[:3]
                    )
                    self.date_edit.setDate(QDate(y, m, day))
                except Exception:
                    pass
            self.invoice_number_le.setText(str(d.get("invoice_number") or ""))
            self.currency_cb.setCurrentText(str(d.get("currency") or "RD$"))
            self.exchange_rate_le.setText(
                str(
                    d.get("exchange_rate")
                    if d.get("exchange_rate") is not None
                    else "1.0"
                )
            )
            self.rnc_le.setText(str(d.get("rnc") or ""))
            self.third_party_le.setText(str(d.get("third_party_name") or ""))
            self.itbis_le.setText(str(d.get("itbis") or "0.00"))
            if d.get("total_amount") is not None:
                self.total_le.setText(str(d.get("total_amount")))
        except Exception as e:
            print("Error cargando datos existentes en AddInvoiceWindowQt:", e)

    # ------------------------------------------------------------------ #
    # Autocompletado
    # ------------------------------------------------------------------ #
    def _on_keyup(self, text: str, search_by: str):
        """Llamado desde textChanged en rnc_le o third_party_le."""
        try:
            q = text.strip()
            if len(q) < 2:
                self._suggestion_popup.hide()
                return
            results = []
            if self.controller and hasattr(self.controller, "search_third_parties"):
                try:
                    results = self.controller.search_third_parties(
                        q, search_by=search_by
                    )
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

            if search_by == "rnc":
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

    # ------------------------------------------------------------------ #
    # Historial (undo/redo)
    # ------------------------------------------------------------------ #
    def _get_state(self):
        return {
            "fecha": self.date_edit.date().toString("yyyy-MM-dd"),
            "tipo": self.tipo_cb.currentText(),
            "invoice_number": self.invoice_number_le.text(),
            "currency": self.currency_cb.currentText(),
            "exchange_rate": self.exchange_rate_le.text(),
            "rnc": self.rnc_le.text(),
            "third_party": self.third_party_le.text(),
            "itbis": self.itbis_le.text(),
            "total": self.total_le.text(),
        }

    def _apply_state(self, state: dict):
        if not state:
            return
        try:
            self._is_restoring = True
            try:
                d = state.get("fecha", "")
                if d:
                    self.date_edit.setDate(QDate.fromString(d, "yyyy-MM-dd"))
            except Exception:
                pass
            self.tipo_cb.setCurrentText(
                state.get("tipo", self.tipo_cb.currentText())
            )
            self.invoice_number_le.setText(
                state.get("invoice_number", self.invoice_number_le.text())
            )
            self.currency_cb.setCurrentText(
                state.get("currency", self.currency_cb.currentText())
            )
            self.exchange_rate_le.setText(
                state.get("exchange_rate", self.exchange_rate_le.text())
            )
            self.rnc_le.setText(state.get("rnc", self.rnc_le.text()))
            self.third_party_le.setText(
                state.get("third_party", self.third_party_le.text())
            )
            self.itbis_le.setText(state.get("itbis", self.itbis_le.text()))
            self.total_le.setText(state.get("total", self.total_le.text()))
        finally:
            self._is_restoring = False
            self._update_undo_redo_buttons()

    def _push_history(self):
        if self._is_restoring:
            return
        state = self._get_state()
        if (
            self._history_index >= 0
            and self._history
            and state == self._history[self._history_index]
        ):
            return
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]
        self._history.append(state)
        self._history_index = len(self._history) - 1
        if len(self._history) > 100:
            self._history.pop(0)
            self._history_index -= 1
        self._update_undo_redo_buttons()

    def _undo(self):
        if self._history_index <= 0:
            return
        try:
            self._is_restoring = True
            self._history_index -= 1
            state = self._history[self._history_index]
            self._apply_state(state)
        finally:
            self._is_restoring = False
            self._update_undo_redo_buttons()

    def _redo(self):
        if self._history_index < 0 or self._history_index >= len(
            self._history
        ) - 1:
            return
        try:
            self._is_restoring = True
            self._history_index += 1
            state = self._history[self._history_index]
            self._apply_state(state)
        finally:
            self._is_restoring = False
            self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(self._history_index > 0)
        self.btn_redo.setEnabled(self._history_index < len(self._history) - 1)

    # ------------------------------------------------------------------ #
    # Wrapper de acceso (_g)
    # ------------------------------------------------------------------ #
    def _g(self, key, default=""):
        """
        Normaliza accesos a valores de la UI para facturas emitidas.
        Incluye alias en español e inglés.
        """
        try:
            fecha = (
                self.date_edit.date().toString("yyyy-MM-dd")
                if hasattr(self, "date_edit")
                else default
            )
            tipo = (
                self.tipo_cb.currentText()
                if hasattr(self, "tipo_cb")
                else "Factura Privada"
            )
            numero = (
                self.invoice_number_le.text().strip()
                if hasattr(self, "invoice_number_le")
                else ""
            )
            moneda = (
                self.currency_cb.currentText()
                if hasattr(self, "currency_cb")
                else ""
            )
            tasa = (
                self.exchange_rate_le.text().strip()
                if hasattr(self, "exchange_rate_le")
                else ""
            )
            rnc = self.rnc_le.text().strip() if hasattr(self, "rnc_le") else ""
            tercero = (
                self.third_party_le.text().strip()
                if hasattr(self, "third_party_le")
                else ""
            )
            itbis = (
                self.itbis_le.text().replace(",", "").strip()
                if hasattr(self, "itbis_le")
                else ""
            )
            total = (
                self.total_le.text().replace(",", "").strip()
                if hasattr(self, "total_le")
                else ""
            )
        except Exception:
            fecha = tipo = numero = moneda = tasa = rnc = tercero = itbis = total = default

        m = {
            # español
            "fecha": fecha,
            "tipo_de_factura": tipo,
            "número_de_factura": numero,
            "moneda": moneda,
            "tasa_cambio": tasa,
            "rnc_cédula": rnc,
            "empresa_a_la_que_se_emitió": tercero,
            "itbis": itbis,
            "factura_total": total,
            # alias
            "empresa": tercero,
            "lugar_de_compra_empresa": tercero,
            # inglés
            "invoice_date": fecha,
            "invoice_type": tipo,
            "invoice_number": numero,
            "currency": moneda,
            "exchange_rate": tasa,
            "rnc": rnc,
            "third_party_name": tercero,
            "total_amount": total,
        }
        return m.get(key, default)

    # ------------------------------------------------------------------ #
    # Guardado
    # ------------------------------------------------------------------ #
    def _on_save_clicked(self):
        """Construye form_data y delega el guardado en on_save/controller."""
        import traceback

        numero = self._g("número_de_factura")
        rnc = self._g("rnc_cédula")
        if not numero:
            QMessageBox.warning(
                self, "Validación", "El número de factura no puede estar vacío."
            )
            return
        if not rnc:
            QMessageBox.warning(
                self, "Validación", "El RNC/Cédula no puede estar vacío."
            )
            return

        def _to_float(s, default=0.0):
            if s is None:
                return float(default)
            if isinstance(s, (int, float)):
                return float(s)
            ss = str(s).replace(",", "").strip()
            if ss == "":
                return float(default)
            try:
                return float(ss)
            except Exception:
                return float(default)

        try:
            fecha_py = (
                self.date_edit.date().toPyDate() if hasattr(self, "date_edit") else None
            )
            invoice_num = numero
            currency = self._g("moneda")
            try:
                exchange_rate = (
                    _to_float(self.exchange_rate_le.text())
                    if hasattr(self, "exchange_rate_le")
                    else _to_float(self._g("tasa_cambio") or 1.0)
                )
            except Exception:
                exchange_rate = 1.0
            rnc_val = rnc
            third_party = (
                self._g("empresa_a_la_que_se_emitió")
                or self._g("empresa")
                or self._g("lugar_de_compra_empresa")
                or ""
            )

            form_data = {
                # Español
                "fecha": fecha_py,
                "tipo_de_factura": self._g("tipo_de_factura"),
                "número_de_factura": invoice_num,
                "moneda": currency,
                "tasa_cambio": exchange_rate,
                "rnc_cédula": rnc_val,
                "empresa_a_la_que_se_emitió": third_party,
                "itbis": _to_float(self._g("itbis")),
                "factura_total": _to_float(self._g("factura_total")),
                # Inglés / moderno
                "invoice_date": fecha_py,
                "invoice_type": "emitida",
                "invoice_number": invoice_num,
                "currency": currency,
                "exchange_rate": exchange_rate,
                "rnc": rnc_val,
                "third_party_name": third_party,
                "total_amount": _to_float(self._g("factura_total")),
                # metadata
                "company_id": (
                    self.parent.get_current_company_id()
                    if self.parent
                    and hasattr(self.parent, "get_current_company_id")
                    else None
                ),
            }
        except Exception as e:
            tb = traceback.format_exc()
            print("Traceback preparing form_data (emitidas):\n", tb)
            QMessageBox.critical(self, "Error", f"Error preparando datos: {e}")
            return

        if callable(self.on_save):
            try:
                try:
                    result = self.on_save(self, form_data, "emitida", self.invoice_id)
                except TypeError:
                    result = self.on_save(self, form_data, "emitida")

                if isinstance(result, tuple) and len(result) >= 1:
                    success = result[0]
                    message = result[1] if len(result) > 1 else ""
                    if success:
                        self.accept()
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            message or "No se pudo guardar la factura.",
                        )
                return
            except Exception as e:
                tb = traceback.format_exc()
                print("Traceback in on_save callback (emitidas):\n", tb)
                QMessageBox.critical(
                    self,
                    "Error al Guardar",
                    f"Ocurrió un error al guardar: {e}",
                )
                return

        # Fallback al controller
        try:
            if self.invoice_id and hasattr(self.controller, "update_invoice"):
                success, message = self.controller.update_invoice(
                    self.invoice_id, form_data
                )
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
                QMessageBox.information(
                    self,
                    "Info",
                    "No hay callback ni métodos del controlador para guardar. Cerrando ventana.",
                )
                self.accept()
                return
        except KeyError as ke:
            tb = traceback.format_exc()
            print("KeyError saving invoice (emitidas):\n", tb)
            QMessageBox.critical(self, "Error", f"Falta clave en los datos: {ke}")
            return
        except Exception as e:
            tb = traceback.format_exc()
            print("Traceback saving invoice (emitidas):\n", tb)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar la factura: {e}",
            )
            return

    # ------------------------------------------------------------------ #
    # Editor de anexos existente (utilizado en otras partes)
    # ------------------------------------------------------------------ #
    def _open_attachment_editor(self, relative_or_absolute_path):
        """
        Abre el editor de anexos. Si se pasa ruta relativa, la intenta resolver
        usando controller.get_setting('attachment_base_path').
        """
        import os

        path = relative_or_absolute_path or ""
        if not os.path.isabs(path):
            try:
                base = self.controller.get_setting("attachment_base_path")
            except Exception:
                base = None
            if base:
                candidate = os.path.join(base, path)
                if os.path.exists(candidate):
                    path = candidate
        if not os.path.exists(path):
            QMessageBox.warning(
                self, "Archivo no encontrado", f"No se encontró el anexo: {path}"
            )
            return
        dlg = AttachmentEditorWindowQt(self, path)
        dlg.exec()