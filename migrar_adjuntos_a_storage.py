import sys
import os
import datetime
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from logic_firebase import LogicControllerFirebase


def norm_company_folder_name(name: str) -> str:
    """Normaliza el nombre de empresa para carpeta local (igual que en AddExpenseWindowQt)."""
    safe = (
        "".join(c for c in name if c.isalnum() or c in (" ", "-", "_"))
        .strip()
        .replace(" ", "_")
    )
    return safe or "company"


class MigrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Migración de adjuntos locales -> Firebase Storage")
        self.resize(900, 600)

        self.controller = LogicControllerFirebase(config_path="config.json")

        self._build_ui()
        self._load_companies()

        self.base_local_folder: Optional[Path] = None

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1) Selección de carpeta base local
        row_local = QHBoxLayout()
        row_local.addWidget(QLabel("Carpeta BASE local (empresas):"))
        self.lbl_local_folder = QLabel("No seleccionada")
        self.lbl_local_folder.setStyleSheet("color: #1D4ED8;")
        btn_select_folder = QPushButton("Elegir carpeta...")
        btn_select_folder.clicked.connect(self._choose_local_folder)
        row_local.addWidget(self.lbl_local_folder, 1)
        row_local.addWidget(btn_select_folder)
        layout.addLayout(row_local)

        # 2) Empresa Firebase (company_id)
        row_company = QHBoxLayout()
        row_company.addWidget(QLabel("Empresa en Firebase:"))
        self.cb_company = QComboBox()
        row_company.addWidget(self.cb_company, 1)
        layout.addLayout(row_company)

        # 3) Año / Mes
        row_period = QHBoxLayout()
        row_period.addWidget(QLabel("Año:"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(2000, 2100)
        self.spin_year.setValue(datetime.date.today().year)
        row_period.addWidget(self.spin_year)

        row_period.addWidget(QLabel("Mes:"))
        self.cb_month = QComboBox()
        for m in range(1, 13):
            self.cb_month.addItem(f"{m:02d}", m)
        self.cb_month.setCurrentIndex(datetime.date.today().month - 1)
        row_period.addWidget(self.cb_month)

        row_period.addStretch()
        layout.addLayout(row_period)

        # 4) Botón de migración
        btn_migrate = QPushButton("Migrar adjuntos de este periodo")
        btn_migrate.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        btn_migrate.clicked.connect(self._on_migrate_clicked)
        layout.addWidget(btn_migrate, alignment=Qt.AlignmentFlag.AlignLeft)

        # 5) Log
        layout.addWidget(QLabel("Log de migración:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.txt_log, 1)

    def _log(self, text: str):
        self.txt_log.append(text)
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )
        print(text)

    def _choose_local_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona la carpeta BASE donde están las empresas locales",
            "",
        )
        if not folder:
            return
        self.base_local_folder = Path(folder)
        self.lbl_local_folder.setText(str(self.base_local_folder))

    def _load_companies(self):
        self.cb_company.clear()
        companies = self.controller.get_companies() or []
        for c in companies:
            name = c.get("name", "")
            cid = c.get("id")
            self.cb_company.addItem(f"{cid} - {name}", cid)
        if not companies:
            self.cb_company.addItem("Sin empresas (revisa Firestore)", None)

    # ---------------- Lógica de migración ----------------
    def _on_migrate_clicked(self):
        if self.base_local_folder is None:
            QMessageBox.warning(
                self,
                "Carpeta no seleccionada",
                "Primero selecciona la carpeta BASE local de empresas.",
            )
            return

        cid = self.cb_company.currentData()
        if cid is None:
            QMessageBox.warning(
                self,
                "Empresa no válida",
                "Selecciona una empresa válida en Firebase.",
            )
            return

        year = int(self.spin_year.value())
        month = int(self.cb_month.currentData())
        month_str = f"{month:02d}"

        # Confirmación
        reply = QMessageBox.question(
            self,
            "Confirmar migración",
            (
                "¿Migrar adjuntos locales a Storage para:\n\n"
                f"  Empresa Firebase ID: {cid}\n"
                f"  Año: {year}, Mes: {month_str}\n"
                f"  Carpeta BASE local: {self.base_local_folder}\n\n"
                "Se subirán archivos encontrados localmente y se actualizarán "
                "los documentos de 'invoices' con 'attachment_storage_path'."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._run_migration_for_period(company_id=cid, year=year, month=month)

    def _run_migration_for_period(self, company_id: int, year: int, month: int):
        db = self.controller._db
        bucket = self.controller._bucket
        if db is None or bucket is None:
            QMessageBox.critical(
                self,
                "Firebase no inicializado",
                "Firestore o Storage no están inicializados. Revisa config.json.",
            )
            return

        # 1) Encontrar el nombre de empresa para mapear con carpeta local
        comp_name = None
        for i in range(self.cb_company.count()):
            if self.cb_company.itemData(i) == company_id:
                text = self.cb_company.itemText(i)
                # texto tipo "7 - CARVAJAL_DIAZ_SRL"
                parts = text.split("-", 1)
                if len(parts) == 2:
                    comp_name = parts[1].strip()
                else:
                    comp_name = text.strip()
                break
        comp_name = comp_name or str(company_id)
        local_company_folder = norm_company_folder_name(comp_name)

        base = self.base_local_folder
        # Estructura esperada: BASE / <Empresa> / <Año> / <Mes>
        local_period_folder = base / local_company_folder / str(year) / f"{month:02d}"
        self._log(
            f"[INFO] Carpeta local objetivo: {local_period_folder} "
            f"(empresa='{comp_name}')"
        )

        if not local_period_folder.exists():
            self._log(
                f"[WARN] La carpeta local {local_period_folder} no existe. "
                "Probablemente no haya adjuntos para este periodo."
            )

        # 2) Traer facturas de ese periodo y empresa
        self._log(
            f"[INFO] Obteniendo facturas company_id={company_id}, "
            f"año={year}, mes={month:02d} desde Firestore..."
        )

        invoices = self.controller._query_invoices(
            company_id=company_id,
            month_str=f"{month:02d}",
            year_int=year,
            tx_type=None,
        )
        self._log(f"[INFO] Facturas encontradas: {len(invoices)}")

        total_processed = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for inv in invoices:
            total_processed += 1
            doc_id = inv.get("id")
            invoice_number = inv.get("invoice_number")
            rnc = inv.get("rnc") or inv.get("client_rnc") or ""

            attach_storage = (
                inv.get("attachment_storage_path")
                or inv.get("storage_path")
                or None
            )

            if attach_storage:
                self._log(
                    f"[SKIP] doc_id={doc_id}, fact={invoice_number}: "
                    "ya tiene attachment_storage_path."
                )
                total_skipped += 1
                continue

            # Buscamos el archivo local. Como la estructura te la organizabas tú,
            # intentamos distintas variantes basadas en invoice_number y RNC.
            candidate_files: List[Path] = []

            if local_period_folder.exists():
                try:
                    # Patrón más habitual: NUMEROFACTURA_RNC*.*
                    if invoice_number:
                        pattern_main = f"{invoice_number}_*"
                        candidate_files.extend(local_period_folder.glob(pattern_main))

                    # Fallback: cualquier archivo que contenga el número de factura
                    if invoice_number:
                        pattern_any = f"*{invoice_number}*"
                        candidate_files.extend(local_period_folder.glob(pattern_any))

                except Exception as e:
                    self._log(
                        f"[ERR] Error buscando archivos para "
                        f"doc_id={doc_id}, fact={invoice_number}: {e}"
                    )

            # De-duplicar
            seen = set()
            candidate_files = [
                p for p in candidate_files if not (str(p) in seen or seen.add(str(p)))
            ]

            if not candidate_files:
                self._log(
                    f"[WARN] No se encontró archivo local para "
                    f"doc_id={doc_id}, fact={invoice_number} en {local_period_folder}"
                )
                total_skipped += 1
                continue

            # Por simplicidad, tomamos el primero
            local_path = candidate_files[0]
            self._log(
                f"[INFO] doc_id={doc_id}, fact={invoice_number}: "
                f"usando archivo local '{local_path.name}'"
            )

            # Convertir invoice_date a date para subir a Storage
            inv_date_raw = inv.get("invoice_date") or inv.get("fecha")
            inv_date_py = None
            try:
                if isinstance(inv_date_raw, datetime.date):
                    inv_date_py = inv_date_raw
                elif isinstance(inv_date_raw, datetime.datetime):
                    inv_date_py = inv_date_raw.date()
                elif inv_date_raw:
                    s = str(inv_date_raw)
                    inv_date_py = datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
            except Exception:
                inv_date_py = None

            try:
                sp = self.controller.upload_attachment_to_storage(
                    local_path=str(local_path),
                    company_id=company_id,
                    invoice_number=str(invoice_number or doc_id),
                    invoice_date=inv_date_py,
                    rnc=str(rnc or ""),
                )
                if not sp:
                    self._log(
                        f"[ERR] No se pudo subir a Storage para "
                        f"doc_id={doc_id}, fact={invoice_number}"
                    )
                    total_errors += 1
                    continue

                # Actualizar el documento
                try:
                    col = self.controller._db.collection("invoices")
                    col.document(str(doc_id)).update({"attachment_storage_path": sp})
                    total_updated += 1
                    self._log(
                        f"[OK] doc_id={doc_id}, fact={invoice_number}: "
                        f"attachment_storage_path='{sp}'"
                    )
                except Exception as e:
                    self._log(
                        f"[ERR] No se pudo actualizar doc_id={doc_id}: {e}"
                    )
                    total_errors += 1
                    continue

            except Exception as e:
                self._log(
                    f"[EXC] Excepción migrando doc_id={doc_id}, "
                    f"fact={invoice_number}: {e}"
                )
                total_errors += 1
                continue

        self._log("\n=== RESUMEN MIGRACIÓN ===")
        self._log(f"  Procesados  : {total_processed}")
        self._log(f"  Actualizados: {total_updated}")
        self._log(f"  Saltados    : {total_skipped}")
        self._log(f"  Errores     : {total_errors}")
        self._log("=== FIN ===")


def main():
    app = QApplication(sys.argv)
    win = MigrationWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()