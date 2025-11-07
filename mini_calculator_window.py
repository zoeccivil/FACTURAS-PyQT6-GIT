# Crea este nuevo archivo: mini_calculator_window.py

import tkinter as tk
from tkinter import ttk

class MiniCalculator(tk.Toplevel):
    def __init__(self, parent, target_entry):
        super().__init__(parent)
        self.target_entry = target_entry

        self.title("Calculadora")
        self.geometry("250x300")
        self.resizable(False, False)
        self.transient(parent) # Mantener por encima de la ventana principal
        self.grab_set()

        self.result_var = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        # Pantalla de resultados
        display = ttk.Entry(self, textvariable=self.result_var, font=("Arial", 16), justify='right')
        display.pack(fill='x', padx=5, pady=5, ipady=5)

        # Frame para los botones
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill='both', expand=True)

        # Definición de botones
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        
        # Crear y posicionar botones en una grilla
        for i, text in enumerate(buttons):
            row, col = divmod(i, 4)
            action = lambda x=text: self._on_press(x)
            ttk.Button(buttons_frame, text=text, command=action).grid(row=row, column=col, sticky="nsew", ipadx=5, ipady=5)
        
        # Botón de Limpiar
        ttk.Button(buttons_frame, text="C", command=self._clear).grid(row=4, column=0, columnspan=2, sticky="nsew")
        ttk.Button(buttons_frame, text="OK", command=self._accept_result).grid(row=4, column=2, columnspan=2, sticky="nsew")

        for i in range(4): buttons_frame.columnconfigure(i, weight=1)
        for i in range(5): buttons_frame.rowconfigure(i, weight=1)

    def _on_press(self, key):
        if key == '=':
            self._calculate()
        else:
            current_text = self.result_var.get()
            self.result_var.set(current_text + key)

    def _calculate(self):
        try:
            result = eval(self.result_var.get())
            self.result_var.set(str(round(result, 2)))
        except:
            self.result_var.set("Error")

    def _clear(self):
        self.result_var.set("")

    def _accept_result(self):
        try:
            # Validar que el resultado sea un número antes de aceptar
            value = float(self.result_var.get())
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(value))
            self.destroy()
        except (ValueError, TypeError):
            # Si hay un error o está vacío, simplemente cerrar
            self.destroy()