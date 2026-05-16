import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # pymupdf
from PIL import Image, ImageTk
import io
import os
import shutil

def abrir_visor(apunte, recursos):
    ventana = tk.Tk()
    ventana.title(f"UniShare — {apunte.get('titulo', 'Visor')}")
    ventana.geometry("1000x700")

    tipo = apunte.get("categoria", {}).get("tipo_apunte", "documento")

    # Header
    header = tk.Frame(ventana, bg="#1F3864", pady=10)
    header.pack(fill="x")
    tk.Label(header, text=apunte.get("titulo", ""), font=("Arial", 14, "bold"),
             bg="#1F3864", fg="white").pack(side="left", padx=15)
    tk.Label(header, text=f"Materia: {apunte.get('categoria', {}).get('materia', '')}",
             font=("Arial", 10), bg="#1F3864", fg="#a0b8d8").pack(side="left", padx=10)

    # Si contiene más de un archivo o es desarrollo técnico, abrimos el panel multiarchivo
    if len(recursos) > 1 or tipo in ["codigo_fuente", "diseño_tecnico"]:
        _visor_multiarchivo(ventana, recursos)
    else:
        _visor_documento(ventana, recursos)

    ventana.mainloop()

def _visor_documento(ventana, recursos):
    if not recursos:
        tk.Label(ventana, text="No hay archivos disponibles.", font=("Arial", 12)).pack(pady=20)
        return

    recurso = recursos[0]
    path = recurso.get("_path_local", "")
    nombre = recurso.get("nombre", "")
    ext = nombre.split(".")[-1].lower() if nombre else ""

    frame_botones = tk.Frame(ventana, pady=5)
    frame_botones.pack(fill="x", padx=10)

    def descargar():
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Archivo no disponible para descarga.")
            return
        destino = filedialog.asksaveasfilename(defaultextension=f".{ext}", initialfile=nombre)
        if destino:
            shutil.copy2(path, destino)
            messagebox.showinfo("Descarga completa", f"Archivo guardado en:\n{destino}")

    tk.Button(frame_botones, text="⬇ Descargar", command=descargar,
              bg="#2E75B6", fg="white", font=("Arial", 10, "bold"),
              padx=10, pady=4).pack(side="right")

    frame_visor = tk.Frame(ventana)
    frame_visor.pack(fill="both", expand=True, padx=10, pady=5)

    _desplegar_vista_previa(frame_visor, ext, path)

def _visor_multiarchivo(ventana, recursos):
    frame_principal = tk.Frame(ventana)
    frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

    # Panel izquierdo — lista de todos los archivos
    frame_lista = tk.Frame(frame_principal, width=250, bg="#f0f0f0", relief="sunken", bd=1)
    frame_lista.pack(side="left", fill="y", padx=(0, 5))
    frame_lista.pack_propagate(False)

    tk.Label(frame_lista, text="Archivos del Aporte", font=("Arial", 11, "bold"),
             bg="#1F3864", fg="white", pady=6).pack(fill="x")

    listbox = tk.Listbox(frame_lista, font=("Courier New", 10), selectbackground="#2E75B6",
                         activestyle="none", bd=0, highlightthickness=0)
    listbox.pack(fill="both", expand=True, padx=5, pady=5)

    # Panel derecho — visor dinámico reactivo
    frame_visor_dinamico = tk.Frame(frame_principal)
    frame_visor_dinamico.pack(side="left", fill="both", expand=True)

    frame_header_codigo = tk.Frame(frame_visor_dinamico, bg="#2d2d2d", pady=4)
    frame_header_codigo.pack(fill="x")

    nombre_archivo_var = tk.StringVar(value="Seleccioná un archivo")
    tk.Label(frame_header_codigo, textvariable=nombre_archivo_var,
             font=("Courier New", 10), bg="#2d2d2d", fg="#a0a0a0").pack(side="left", padx=10)

    frame_contenido = tk.Frame(frame_visor_dinamico)
    frame_contenido.pack(fill="both", expand=True)

    def descargar_actual():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccioná un archivo primero.")
            return
        recurso = recursos[sel[0]]
        path = recurso.get("_path_local", "")
        nombre = recurso.get("nombre", "")
        ext = nombre.split(".")[-1] if nombre else "txt"
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Archivo no disponible.")
            return
        destino = filedialog.asksaveasfilename(defaultextension=f".{ext}", initialfile=nombre)
        if destino:
            shutil.copy2(path, destino)
            messagebox.showinfo("Descarga completa", f"Archivo guardado en:\n{destino}")

    tk.Button(frame_header_codigo, text="⬇ Descargar", command=descargar_actual,
              bg="#2E75B6", fg="white", font=("Arial", 9), padx=8).pack(side="right", padx=5)

    def mostrar_archivo(event):
        sel = listbox.curselection()
        if not sel:
            return
        recurso = recursos[sel[0]]
        path = recurso.get("_path_local", "")
        nombre = recurso.get("nombre", "")
        nombre_archivo_var.set(nombre)

        # Limpiamos el contenedor dinámico anterior
        for widget in frame_contenido.winfo_children():
            widget.destroy()

        ext = nombre.split(".")[-1].lower() if nombre else ""
        _desplegar_vista_previa(frame_contenido, ext, path)

    listbox.bind("<<ListboxSelect>>", mostrar_archivo)

    # Listar todos de forma natural asignando iconos visuales simples
    for recurso in recursos:
        nombre = recurso.get("nombre", "")
        ext = nombre.split(".")[-1].lower()
        if ext == "pdf":
            prefijo = "📕 "
        elif ext in ["png", "jpg", "jpeg", "gif"]:
            prefijo = "🖼️ "
        elif ext in ["c", "py", "java", "h", "cpp"]:
            prefijo = "💻 "
        else:
            prefijo = "📄 "
        listbox.insert("end", prefijo + nombre)

    if recursos:
        listbox.selection_set(0)
        mostrar_archivo(None)

def _desplegar_vista_previa(frame, ext, path):
    if not path or not os.path.exists(path):
        tk.Label(frame, text="Archivo no disponible localmente.", font=("Arial", 11), fg="red").pack(pady=20)
        return

    # Extensiones de código o texto plano nativas
    if ext in ["c", "py", "java", "txt", "md", "h", "cpp", "json", "html", "css", "sql"]:
        text_frame = tk.Frame(frame)
        text_frame.pack(fill="both", expand=True)

        text_widget = tk.Text(text_frame, font=("Courier New", 10), bg="#1e1e1e", fg="#d4d4d4", wrap="none", bd=0)
        scroll_y = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scroll_x = tk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        text_widget.pack(side="left", fill="both", expand=True)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text_widget.insert("1.0", f.read())
        except Exception as e:
            text_widget.insert("1.0", f"Error de lectura: {e}")
        text_widget.configure(state="disabled")

    elif ext == "pdf":
        _renderizar_pdf(frame, path)

    elif ext in ["png", "jpg", "jpeg", "gif", "bmp"]:
        _renderizar_imagen(frame, path)

    else:
        # Formatos opcionales no previsualizables (ej: docx, dwg)
        tk.Label(frame,
                 text=f"Vista previa no disponible para archivos .{ext}\nUtilizá el botón de descarga superior para abrirlo.",
                 font=("Arial", 11), fg="#595959", justify="center").pack(pady=60)

def _renderizar_pdf(frame, path):
    try:
        doc = fitz.open(path)
        canvas_frame = tk.Frame(frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg="gray")
        scrollbar_y = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        images = []
        y_offset = 10
        for page in doc:
            mat = fitz.Matrix(1.3, 1.3)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            photo = ImageTk.PhotoImage(img)
            images.append(photo)
            canvas.create_image(10, y_offset, anchor="nw", image=photo)
            y_offset += img.height + 10

        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.images = images
    except Exception as e:
        tk.Label(frame, text=f"Error al renderizar PDF: {e}", fg="red").pack(pady=20)

def _renderizar_imagen(frame, path):
    try:
        img = Image.open(path)
        img.thumbnail((700, 500))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(frame, image=photo)
        label.image = photo
        label.pack(pady=15)
    except Exception as e:
        tk.Label(frame, text=f"Error al cargar imagen: {e}", fg="red").pack(pady=20)
