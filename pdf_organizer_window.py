import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import report_generator
import os

class PDFOrganizerWindow(tk.Toplevel):
# En el archivo: pdf_organizer_window.py

    def __init__(self, parent, controller, report_data, company_name, month, year):
        # La única línea que cambia es la siguiente:
        super().__init__(parent)
        
        self.parent = parent
        self.controller = controller
        self.report_data = report_data
        self.company_name = company_name
        self.month = month
        self.year = year
        
        self.attachments_list = [f for f in self.report_data['expense_invoices'] if f.get('attachment_path')]

        self.title("Organizador de Anexos para el Reporte")
        self.geometry("700x500")
        self.grab_set()
        
        self._build_ui()
        self._populate_tree()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Anexos a Incluir (en orden)", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        columns = ('invoice_number', 'third_party', 'file')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.tree.heading('invoice_number', text='No. Factura')
        self.tree.column('invoice_number', width=150)
        self.tree.heading('third_party', text='Proveedor')
        self.tree.column('third_party', width=250)
        self.tree.heading('file', text='Archivo')
        self.tree.pack(fill=tk.BOTH, expand=True)

        buttons_frame = ttk.Frame(main_frame, padding=(10, 0))
        buttons_frame.pack(fill=tk.Y, side=tk.LEFT)
        
        ttk.Button(buttons_frame, text="↑ Subir", command=self._move_up).pack(pady=2, fill=tk.X)
        ttk.Button(buttons_frame, text="↓ Bajar", command=self._move_down).pack(pady=2, fill=tk.X)
        ttk.Button(buttons_frame, text="Excluir", command=self._exclude, style="Accent.TButton").pack(pady=10, fill=tk.X)

        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill=tk.X)
        ttk.Button(action_frame, text="Generar PDF Final", command=self._generate_final_pdf, style="Accent.TButton").pack(side=tk.RIGHT)
        ttk.Button(action_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def _populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for item_data in self.attachments_list:
            file_name = os.path.basename(item_data['attachment_path'])
            self.tree.insert('', 'end', values=(item_data['invoice_number'], item_data['third_party_name'], file_name), iid=str(item_data['id']))

    def _move_up(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        
        index = self.tree.index(selected_item)
        if index > 0:
            self.tree.move(selected_item, '', index - 1)
            item_data = next(item for item in self.attachments_list if str(item['id']) == selected_item)
            self.attachments_list.remove(item_data)
            self.attachments_list.insert(index - 1, item_data)

    def _move_down(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        
        index = self.tree.index(selected_item)
        if index < len(self.attachments_list) - 1:
            self.tree.move(selected_item, '', index + 1)
            item_data = next(item for item in self.attachments_list if str(item['id']) == selected_item)
            self.attachments_list.remove(item_data)
            self.attachments_list.insert(index + 1, item_data)

    def _exclude(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        
        self.tree.delete(selected_item)
        self.attachments_list = [item for item in self.attachments_list if str(item['id']) != selected_item]

    def _generate_final_pdf(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte Final con Anexos",
            initialfile=f"Reporte_{self.company_name.replace(' ', '_')}_{self.month}_{self.year}.pdf"
        )
        if not save_path: return

        self.report_data['ordered_attachments'] = self.attachments_list
        attachment_base_path = self.controller.get_setting('attachment_base_path')
        
        success, message = report_generator.generate_professional_pdf(
            self.report_data, save_path, self.company_name, 
            self.month, self.year, attachment_base_path
        )

        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error", message, parent=self)