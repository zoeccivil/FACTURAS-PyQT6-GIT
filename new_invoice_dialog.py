"""
Diálogo moderno para registrar una nueva factura en Firebase.

Usa el mismo estilo visual que modern_gui (card blanca, botones primario/secundario).
"""

from __future__ import annotations

import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QFrame, QMessageBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont


class NewInvoiceDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Nueva factura")
        self.resize(640, 420)
        self._init_ui()
        self._apply_styles()
        self._populate_defaults()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("invoiceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)

        # Header
        title = QLabel("Registrar nueva factura")
        title.setObjectName("dialogTitle")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)

        subtitle = QLabel(
            "Completa los datos básicos de la factura. "
            "Se guardará directamente en Firebase."
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(line)

        # Empresa (solo lectura, empresa activa)
        row_company = QHBoxLayout()
        lbl_company = QLabel("Empresa:")
        self.company_edit = QLineEdit()
        self.company_edit.setReadOnly(True)
        row_company.addWidget(lbl_company)
        row_company.addWidget(self.company_edit, 1)
        card_layout.addLayout(row_company)

        # Fecha + tipo
        row_date_type = QHBoxLayout()
        lbl_date = QLabel("Fecha:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        row_date_type.addWidget(lbl_date)
        row_date_type.addWidget(self.date_edit)

        lbl_type = QLabel("Tipo:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("Ingreso (emitida)", "emitida")
        self.type_combo.addItem("Gasto", "gasto")

        row_date_type.addSpacing(12)
        row_date_type.addWidget(lbl_type)
        row_date_type.addWidget(self.type_combo)

        card_layout.addLayout(row_date_type)

        # Número + categoría
        row_number_cat = QHBoxLayout()
        lbl_number = QLabel("No. factura:")
        self.number_edit = QLineEdit()
        row_number_cat.addWidget(lbl_number)
        row_number_cat.addWidget(self.number_edit, 1)

        lbl_cat = QLabel("Categoría:")
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Factura Privada / Consumidor final / etc.")
        row_number_cat.addSpacing(12)
        row_number_cat.addWidget(lbl_cat)
        row_number_cat.addWidget(self.category_edit, 1)

        card_layout.addLayout(row_number_cat)

        # RNC + Tercero
        row_rnc_third = QHBoxLayout()
        lbl_rnc = QLabel("RNC / Cédula:")
        self.rnc_edit = QLineEdit()
        row_rnc_third.addWidget(lbl_rnc)
        row_rnc_third.addWidget(self.rnc_edit, 1)

        lbl_third = QLabel("Cliente / Proveedor:")
        self.third_party_edit = QLineEdit()
        row_rnc_third.addSpacing(12)
        row_rnc_third.addWidget(lbl_third)
        row_rnc_third.addWidget(self.third_party_edit, 1)

        card_layout.addLayout(row_rnc_third)

        # Moneda + montos
        row_money = QHBoxLayout()

        lbl_currency = QLabel("Moneda:")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["RD$", "USD"])
        row_money.addWidget(lbl_currency)
        row_money.addWidget(self.currency_combo)

        lbl_amount = QLabel("Total:")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(1_000_000_000)
        self.amount_spin.setDecimals(2)
        row_money.addSpacing(12)
        row_money.addWidget(lbl_amount)
        row_money.addWidget(self.amount_spin)

        lbl_itbis = QLabel("ITBIS:")
        self.itbis_spin = QDoubleSpinBox()
        self.itbis_spin.setMaximum(1_000_000_000)
        self.itbis_spin.setDecimals(2)
        row_money.addSpacing(12)
        row_money.addWidget(lbl_itbis)
        row_money.addWidget(self.itbis_spin)

        card_layout.addLayout(row_money)

        # Tasa + total RD$
        row_rate_rd = QHBoxLayout()
        lbl_rate = QLabel("Tasa cambio:")
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMaximum(1_000_000)
        self.rate_spin.setDecimals(4)
        self.rate_spin.setValue(1.0)

        row_rate_rd.addWidget(lbl_rate)
        row_rate_rd.addWidget(self.rate_spin)

        lbl_total_rd = QLabel("Total RD$:")
        self.total_rd_spin = QDoubleSpinBox()
        self.total_rd_spin.setMaximum(1_000_000_000)
        self.total_rd_spin.setDecimals(2)
        row_rate_rd.addSpacing(12)
        row_rate_rd.addWidget(lbl_total_rd)
        row_rate_rd.addWidget(self.total_rd_spin)

        card_layout.addLayout(row_rate_rd)

        # Botones
        card_layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save_clicked)
        btn_row.addWidget(save_btn)

        card_layout.addLayout(btn_row)

        root.addWidget(card)

    def _apply_styles(self):
        self.setObjectName("newInvoiceDialog")
        self.setStyleSheet("""
        QDialog#newInvoiceDialog {
            background-color: #E5E7EB;
        }
        QFrame#invoiceCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }
        QLabel#dialogTitle {
            color: #0F172A;
        }
        QLabel#dialogSubtitle {
            color: #6B7280;
            font-size: 12px;
        }
        QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;
        }
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
            border-color: #3B82F6;
        }
        QPushButton#primaryButton {
            background-color: #1E293B;
            color: #FFFFFF;
            padding: 6px 14px;
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
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid #D1D5DB;
            font-weight: 500;
        }
        QPushButton#secondaryButton:hover {
            background-color: #E5E7EB;
        }
        """)

    def _populate_defaults(self):
        # Empresa activa desde el controller
        try:
            name = getattr(self.controller, "active_company_name", None)
            if not name and hasattr(self.controller, "list_companies"):
                companies = self.controller.list_companies() or []
                name = companies[0] if companies else ""
            self.company_edit.setText(name or "")
        except Exception:
            self.company_edit.setText("")

    def _on_save_clicked(self):
        # Validaciones mínimas
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        invoice_type = self.type_combo.currentData()
        number = self.number_edit.text().strip()
        rnc = self.rnc_edit.text().strip()
        third = self.third_party_edit.text().strip()
        currency = self.currency_combo.currentText()

        if not number:
            QMessageBox.warning(self, "Validación", "Debe indicar un número de factura.")
            return
        if not rnc or not third:
            QMessageBox.warning(self, "Validación", "Debe indicar RNC y nombre del cliente/proveedor.")
            return

        amount = float(self.amount_spin.value())
        itbis = float(self.itbis_spin.value())
        rate = float(self.rate_spin.value()) or 1.0
        total_rd = float(self.total_rd_spin.value()) or amount * rate

        data = {
            "company_id": self.controller.active_company_id,
            "invoice_type": invoice_type,
            "invoice_date": date_str,
            "imputation_date": date_str,  # de momento igual a fecha
            "invoice_number": number,
            "invoice_category": self.category_edit.text().strip() or None,
            "rnc": rnc,
            "third_party_name": third,
            "currency": currency,
            "itbis": itbis,
            "total_amount": amount,
            "exchange_rate": rate,
            "total_amount_rd": total_rd,
            "attachment_path": None,
            "client_name": None,
            "client_rnc": None,
            "excel_path": None,
            "pdf_path": None,
            "due_date": None,
        }

        ok, msg = self.controller.add_invoice(data)
        if not ok:
            QMessageBox.critical(self, "Error", msg)
            return

        QMessageBox.information(self, "Factura", msg)
        self.accept()