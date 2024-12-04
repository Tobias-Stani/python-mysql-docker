import tkinter as tk
from tkinter import messagebox

# Función para mostrar los valores ingresados
def mostrar_valores():
    valor1 = entrada1.get()
    valor2 = entrada2.get()
    messagebox.showinfo("Valores Ingresados", f"Valor 1: {valor1}\nValor 2: {valor2}")

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Interfaz Gráfica Simple")
ventana.geometry("300x200")

# Etiquetas e inputs
tk.Label(ventana, text="Ingrese el primer valor:").pack(pady=5)
entrada1 = tk.Entry(ventana)
entrada1.pack(pady=5)

tk.Label(ventana, text="Ingrese el segundo valor:").pack(pady=5)
entrada2 = tk.Entry(ventana)
entrada2.pack(pady=5)

# Botón para mostrar valores
boton = tk.Button(ventana, text="Mostrar Valores", command=mostrar_valores)
boton.pack(pady=10)

# Iniciar el bucle de la aplicación
ventana.mainloop()
