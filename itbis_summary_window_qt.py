from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QComboBox,QMessageBox,
)
from PyQt6.QtCore import Qt, QDate


class ItbisSummaryWindowQt(QDialog):
    """
    Resumen ITBIS para una empresa, con filtro propio de mes/año.

    Requiere que el controller implemente:

      - get_itbis_month_summary(company_id, month_str, year_int) -> dict
      - get_itbis_adelantado_period(company_id, month_str, year_int) -> float
      - update_itbis_adelantado_period(company_id, month_str, year_int, value) -> bool
    """

    MONTHS_MAP = {
        "Enero": "01",
        "Febrero": "02",
        "Marzo": "03",
        "Abril": "04",
        "Mayo": "05",
        "Junio": "06",
        "Julio": "07",
        "Agosto": "08",
        "Septiembre": "09",
        "Octubre": "10",
        "Noviembre": "11",
        "Diciembre": "12",
    }

    def __init__(
        self,
        parent,
        controller,
        company_id,
        company_name: str,
        month_str: str,
        year_int: int,
    ):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.company_id = company_id
        self.company_name = company_name
        # estado interno
        self.current_month_str = month_str
        self.current_year_int = year_int
        self.current_itbis_neto: float = 0.0

        self.setWindowTitle("Resumen ITBIS - Mes Actual")
        self.resize(780, 280)
        self.setModal(True)

        self._build_ui()
        self._load_period_into_filters(month_str, year_int)
        self._load_data()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        # Card principal
        card = QFrame()
        card.setObjectName("itbisCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        # Fila superior: título + filtros de mes/año
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        title = QLabel("Resumen Financiero Actual")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #0F172A;")
        top_row.addWidget(title)
        self.subtitle_label = QLabel(f"Empresa: {self.company_name}")
        self.subtitle_label.setStyleSheet("font-size: 11px; color: #6B7280;")
        top_row.addWidget(self.subtitle_label)
        top_row.addStretch()

        # Selectores propios de mes/año
        self.month_selector = QComboBox()
        for m in self.MONTHS_MAP.keys():
            self.month_selector.addItem(m)
        self.month_selector.currentIndexChanged.connect(self._on_period_changed)

        self.year_selector = QComboBox()
        self.year_selector.currentIndexChanged.connect(self._on_period_changed)

        top_row.addWidget(QLabel("Mes:"))
        top_row.addWidget(self.month_selector)
        top_row.addSpacing(6)
        top_row.addWidget(QLabel("Año:"))
        top_row.addWidget(self.year_selector)

        card_layout.addLayout(top_row)

        # Línea separadora fina
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        card_layout.addWidget(sep)

        # 1) Totales ingresos / gastos
        tot_layout = QHBoxLayout()
        tot_layout.setSpacing(40)

        # Columna izquierda
        left_col = QVBoxLayout()
        left_col.setSpacing(4)

        lbl_ingresos_text = QLabel("Total Ingresos:")
        lbl_ingresos_text.setStyleSheet("color: #4B5563;")
        self.label_total_ingresos = QLabel("RD$ 0.00")
        self.label_total_ingresos.setStyleSheet(
            "color: #15803D; font-weight: 700; font-size: 16px;"
        )

        lbl_it_ing = QLabel("ITBIS Ingresos:")
        lbl_it_ing.setStyleSheet("color: #4B5563;")
        self.label_itbis_ingresos = QLabel("RD$ 0.00")
        self.label_itbis_ingresos.setStyleSheet(
            "color: #15803D; font-weight: 700; font-size: 14px;"
        )

        left_col.addWidget(lbl_ingresos_text)
        left_col.addWidget(self.label_total_ingresos)
        left_col.addSpacing(4)
        left_col.addWidget(lbl_it_ing)
        left_col.addWidget(self.label_itbis_ingresos)

        # Columna derecha
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        lbl_gastos_text = QLabel("Total Gastos:")
        lbl_gastos_text.setStyleSheet("color: #4B5563;")
        self.label_total_gastos = QLabel("RD$ 0.00")
        self.label_total_gastos.setStyleSheet(
            "color: #B91C1C; font-weight: 700; font-size: 16px;"
        )

        lbl_it_gas = QLabel("ITBIS Gastos:")
        lbl_it_gas.setStyleSheet("color: #4B5563;")
        self.label_itbis_gastos = QLabel("RD$ 0.00")
        self.label_itbis_gastos.setStyleSheet(
            "color: #B91C1C; font-weight: 700; font-size: 14px;"
        )

        right_col.addWidget(lbl_gastos_text)
        right_col.addWidget(self.label_total_gastos)
        right_col.addSpacing(4)
        right_col.addWidget(lbl_it_gas)
        right_col.addWidget(self.label_itbis_gastos)

        tot_layout.addLayout(left_col, 1)
        tot_layout.addLayout(right_col, 1)
        card_layout.addLayout(tot_layout)

        # 2) ITBIS adelantado + botón Calcular
        adel_layout = QHBoxLayout()
        adel_layout.setSpacing(12)

        lbl_adel = QLabel("ITBIS Adelantado (Mes Ant.):")
        lbl_adel.setStyleSheet("color: #4B5563;")
        self.edit_itbis_adelantado = QLineEdit("0.00")
        self.edit_itbis_adelantado.setMaximumWidth(140)
        self.edit_itbis_adelantado.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.edit_itbis_adelantado.setPlaceholderText("0.00")

        self.btn_calcular = QPushButton("Calcular")
        self.btn_calcular.setObjectName("primaryButton")
        self.btn_calcular.setMinimumWidth(120)
        self.btn_calcular.clicked.connect(self._on_calculate_clicked)

        adel_layout.addWidget(lbl_adel)
        adel_layout.addWidget(self.edit_itbis_adelantado)
        adel_layout.addSpacing(24)
        adel_layout.addWidget(self.btn_calcular)
        adel_layout.addStretch()
        card_layout.addLayout(adel_layout)

        # 3) ITBIS a pagar
        pagar_layout = QHBoxLayout()
        pagar_layout.setSpacing(10)

        lbl_pagar = QLabel("ITBIS a Pagar (Restante):")
        lbl_pagar.setStyleSheet("color: #4B5563;")
        self.label_itbis_a_pagar = QLabel("RD$ 0.00")
        self.label_itbis_a_pagar.setStyleSheet(
            "color: #B91C1C; font-weight: 700; font-size: 16px;"
        )

        pagar_layout.addWidget(lbl_pagar)
        pagar_layout.addWidget(self.label_itbis_a_pagar)
        pagar_layout.addStretch()
        card_layout.addLayout(pagar_layout)

        # 4) ITBIS neto y total neto
        neto_layout = QHBoxLayout()
        neto_layout.setSpacing(40)

        lbl_neto = QLabel("ITBIS Neto:")
        lbl_neto.setStyleSheet("color: #4B5563;")
        self.label_itbis_neto = QLabel("RD$ 0.00")
        self.label_itbis_neto.setStyleSheet(
            "color: #1D4ED8; font-size: 16px; font-weight: bold; text-decoration: underline;"
        )

        lbl_total_neto = QLabel("Total Neto:")
        lbl_total_neto.setStyleSheet("color: #4B5563;")
        self.label_total_neto = QLabel("RD$ 0.00")
        self.label_total_neto.setStyleSheet(
            "color: #1D4ED8; font-size: 16px; font-weight: bold; text-decoration: underline;"
        )

        neto_layout.addWidget(lbl_neto)
        neto_layout.addWidget(self.label_itbis_neto)
        neto_layout.addSpacing(40)
        neto_layout.addWidget(lbl_total_neto)
        neto_layout.addWidget(self.label_total_neto)
        neto_layout.addStretch()
        card_layout.addLayout(neto_layout)

        root.addWidget(card)

        # estilos
        self.setStyleSheet(
            self.styleSheet()
            + """
        QFrame#itbisCard {
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
        }
        QLineEdit {
            background-color: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 4px 6px;
            color: #111827;
        }
        QLineEdit:focus {
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
        """
        )

    # ------------------------------------------------------------------
    # Carga filtros de periodo
    # ------------------------------------------------------------------
    def _load_period_into_filters(self, month_str: str, year_int: int):
        # Mes
        month_name = None
        for name, code in self.MONTHS_MAP.items():
            if code == month_str:
                month_name = name
                break
        if month_name is None:
            # por si acaso, usar mes actual
            current_month_index = QDate.currentDate().month() - 1
            self.month_selector.setCurrentIndex(max(0, current_month_index))
        else:
            idx = list(self.MONTHS_MAP.keys()).index(month_name)
            self.month_selector.setCurrentIndex(idx)

        # Años: ponemos el actual y +/- 3 como opciones rápidas
        self.year_selector.clear()
        base_year = year_int or QDate.currentDate().year()
        years = sorted({base_year - 1, base_year, base_year + 1})
        for y in years:
            self.year_selector.addItem(str(y))
        # seleccionar el año recibido
        try:
            idx_y = years.index(base_year)
            self.year_selector.setCurrentIndex(idx_y)
        except ValueError:
            self.year_selector.setCurrentIndex(1 if len(years) > 1 else 0)
                # Actualizar subtítulo "Empresa: X – Periodo: YYYY-MM"
        month_name = self.month_selector.currentText()
        month_code = self.MONTHS_MAP.get(month_name, "--")
        period_str = f"{base_year}-{month_code}"
        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(
                f"Empresa: {self.company_name} – Periodo: {period_str}"
            )

    # ------------------------------------------------------------------
    # Carga de datos desde controller
    # ------------------------------------------------------------------
    def _load_data(self):
        # actualizar estado mes/año desde filtros
        month_name = self.month_selector.currentText()
        self.current_month_str = self.MONTHS_MAP.get(month_name)
        try:
            self.current_year_int = int(self.year_selector.currentText())
        except Exception:
            self.current_year_int = None

        # 1) Resumen del mes
        summary = {}
        try:
            if hasattr(self.controller, "get_itbis_month_summary"):
                summary = (
                    self.controller.get_itbis_month_summary(
                        self.company_id, self.current_month_str, self.current_year_int
                    )
                    or {}
                )
        except Exception:
            summary = {}

        total_income = float(summary.get("total_income", 0.0))
        total_expense = float(summary.get("total_expense", 0.0))
        itbis_income = float(summary.get("itbis_income", 0.0))
        itbis_expense = float(summary.get("itbis_expense", 0.0))
        itbis_neto = float(summary.get("itbis_neto", itbis_income - itbis_expense))
        total_neto = float(summary.get("total_neto", total_income - total_expense))

        self.current_itbis_neto = itbis_neto

        self.label_total_ingresos.setText(f"RD$ {total_income:,.2f}")
        self.label_total_gastos.setText(f"RD$ {total_expense:,.2f}")
        self.label_itbis_ingresos.setText(f"RD$ {itbis_income:,.2f}")
        self.label_itbis_gastos.setText(f"RD$ {itbis_expense:,.2f}")
        self.label_itbis_neto.setText(f"RD$ {itbis_neto:,.2f}")
        self.label_total_neto.setText(f"RD$ {total_neto:,.2f}")

        # 2) ITBIS adelantado guardado para este periodo
        try:
            adelantado = 0.0
            if hasattr(self.controller, "get_itbis_adelantado_period"):
                adelantado = float(
                    self.controller.get_itbis_adelantado_period(
                        self.company_id, self.current_month_str, self.current_year_int
                    )
                    or 0.0
                )
            self.edit_itbis_adelantado.setText(f"{adelantado:,.2f}")
        except Exception:
            self.edit_itbis_adelantado.setText("0.00")

        # calcula inicial sin guardar
        self._recalculate_itbis_restante(save=False)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _on_period_changed(self):
        self._load_data()
        # Actualizar subtítulo con nuevo periodo
        month_name = self.month_selector.currentText()
        month_code = self.MONTHS_MAP.get(month_name, "--")
        try:
            year_val = int(self.year_selector.currentText())
        except Exception:
            year_val = self.current_year_int or QDate.currentDate().year()
        period_str = f"{year_val}-{month_code}"
        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(
                f"Empresa: {self.company_name} – Periodo: {period_str}"
            )

    def _on_calculate_clicked(self):
        ok, msg = self._recalculate_itbis_restante(save=True)
        # Mostrar feedback al usuario
        if ok:
            QMessageBox.information(self, "ITBIS", msg)
        else:
            QMessageBox.warning(self, "ITBIS", msg)

    # ------------------------------------------------------------------
    # Cálculo de ITBIS restante
    # ------------------------------------------------------------------
    def _recalculate_itbis_restante(self, save: bool = True) -> tuple[bool, str]:
        """Calcula y muestra el ITBIS a pagar. Devuelve (ok, mensaje)."""
        try:
            adelantado_str = self.edit_itbis_adelantado.text().replace(",", "")
            itbis_adelantado = float(adelantado_str or 0.0)

            itbis_neto = getattr(self, "current_itbis_neto", 0.0)
            itbis_a_pagar = itbis_neto - itbis_adelantado

            color = "#B91C1C" if itbis_a_pagar >= 0 else "#15803D"
            self.label_itbis_a_pagar.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 16px;"
            )
            self.label_itbis_a_pagar.setText(f"RD$ {itbis_a_pagar:,.2f}")

            if save and hasattr(self.controller, "update_itbis_adelantado_period"):
                try:
                    ok = self.controller.update_itbis_adelantado_period(
                        self.company_id,
                        self.current_month_str,
                        self.current_year_int,
                        itbis_adelantado,
                    )
                    if ok:
                        return True, "ITBIS adelantado calculado y guardado correctamente."
                    else:
                        return False, "No se pudo guardar el ITBIS adelantado en Firebase."
                except Exception as e:
                    return False, f"Error al guardar el ITBIS adelantado: {e}"

            # Si no hay save (modo solo cálculo inicial)
            return True, "Cálculo realizado."

        except (ValueError, TypeError):
            self.label_itbis_a_pagar.setStyleSheet(
                "color: red; font-weight: bold; font-size: 16px;"
            )
            self.label_itbis_a_pagar.setText("Error de formato")
            return False, "Error de formato en el ITBIS adelantado. Usa solo números."