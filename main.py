import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from dao import registrar_alumno, buscar_alumno, buscar_apuntes, obtener_url_archivo, registrar_descarga, subir_apunte, existe_alumno, buscar_alumnos_por_nombre, buscar_alumno_por_legajo, obtener_escuelas, registrar_alumno_completo, eliminar_apunte
from rag import buscar_semantico, indexar_apunte, indexar_todos, eliminar_apunte_vectorial
from visor import abrir_visor
from datetime import datetime
from pymongo import MongoClient
from config_vars import MONGO_URI, MONGO_DB_NAME
import bson

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]

TIPOS_VALIDOS = ["documento", "codigo_fuente", "diseño_tecnico"]

def input_cancelable(mensaje):
    valor = input(f"{mensaje} (o 'cancelar' para volver al menú): ").strip()
    if valor.lower() == "cancelar":
        print("Operación cancelada.")
        return None
    return valor

def seleccionar_archivos(permitir_multiples=False):
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        if permitir_multiples:
            archivos = filedialog.askopenfilenames(
                title="Seleccioná múltiples archivos para el proyecto técnico",
                filetypes=[
                    ("Todos los archivos", "*.*"),
                    ("PDF", "*.pdf"),
                    ("Código fuente", "*.c *.py *.java *.h *.cpp *.sql"),
                    ("Imágenes", "*.png *.jpg *.jpeg"),
                    ("AutoCAD / Planos", "*.dwg *.dxf *.docx")
                ]
            )
            root.destroy()
            if not archivos:
                return []
            return list(archivos)
        else:
            archivo = filedialog.askopenfilename(
                title="Seleccioná el archivo único (Documento)",
                filetypes=[
                    ("Todos los archivos", "*.*"),
                    ("PDF", "*.pdf"),
                    ("Imágenes", "*.png *.jpg *.jpeg"),
                    ("Documentos", "*.docx *.doc *.txt *.md")
                ]
            )
            root.destroy()
            if not archivo:
                return []
            return [archivo]
    except Exception as e:
        print(f"No se pudo abrir el gestor nativo de archivos: {e}")
        ruta = input_cancelable("Ingresá la ruta manualmente (separe por comas si son varios)")
        if ruta:
            return [r.strip() for r in ruta.split(",")]
        return []

def resolver_recursos_locales(apunte):
    recursos = apunte.get("recursos", [])
    for r in recursos:
        url = r.get("url_storage", "")
        path_local = url.replace("unishare/", "")
        from config_vars import MINIO_ENDPOINT
        base = os.path.expanduser("~/.unishare_cache")
        os.makedirs(base, exist_ok=True)
        local = os.path.join(base, os.path.basename(path_local))
        try:
            from minio import Minio
            from config_vars import MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE
            client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
                          secret_key=MINIO_SECRET_KEY, secure=MINIO_SECURE)
            client.fget_object(MINIO_BUCKET, path_local, local)
            r["_path_local"] = local
        except Exception as e:
            print(f"[DEBUG] Fallo al sincronizar recurso en cache local: {e}")
            r["_path_local"] = ""
    return recursos

def ventana_resultados_semanticos(resultados):
    if not resultados:
        return

    ventana = tk.Tk()
    ventana.title("UniShare — Resultados de Búsqueda")
    ventana.geometry("600x400")

    tk.Label(ventana, text="Resultados encontrados",
             font=("Arial", 13, "bold"), fg="#1F3864").pack(pady=10)

    frame = tk.Frame(ventana)
    frame.pack(fill="both", expand=True, padx=15, pady=5)

    cols = ("Título", "Materia", "Tipo", "Relevancia")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=130 if col != "Título" else 220)

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    for item in resultados:
        apunte = item["apunte"]
        relevancia = item["relevancia"]
        tree.insert("", "end", values=(
            apunte.get("titulo", ""),
            apunte.get("categoria", {}).get("materia", ""),
            apunte.get("categoria", {}).get("tipo_apunte", ""),
            f"{relevancia}%"
        ))

    def abrir_seleccionado():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccioná un resultado primero.")
            return
        idx = tree.index(sel[0])
        apunte = resultados[idx]["apunte"]
        ventana.destroy()
        print("Descargando archivos desde MinIO...")
        recursos = resolver_recursos_locales(apunte)
        abrir_visor(apunte, recursos)

    tk.Button(ventana, text="Ver archivo seleccionado",
              command=abrir_seleccionado, bg="#2E75B6", fg="white",
              font=("Arial", 11, "bold"), pady=6).pack(pady=10)

    ventana.mainloop()

def ventana_registrar_alumno():
    escuelas = obtener_escuelas()
    if not escuelas:
        print("Error: no se pudieron cargar las escuelas.")
        return

    ventana = tk.Tk()
    ventana.title("Registrar Alumno — UniShare")
    ventana.geometry("500x620")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Registrar Alumno", font=("Arial", 16, "bold")).pack(pady=10)

    frame = tk.Frame(ventana)
    frame.pack(padx=20, pady=5, fill="both")

    campos = {}

    def agregar_campo(label, key):
        tk.Label(frame, text=label, anchor="w").pack(fill="x")
        entry = tk.Entry(frame, width=50)
        entry.pack(fill="x", pady=2)
        campos[key] = entry

    agregar_campo("Nombre", "nombre")
    agregar_campo("Apellido", "apellido")
    agregar_campo("DNI", "dni")
    agregar_campo("Fecha de nacimiento (DD/MM/AAAA)", "fecha_nacimiento")
    agregar_campo("Email institucional", "email")

    tk.Label(frame, text="Escuela", anchor="w").pack(fill="x")
    escuela_var = tk.StringVar()
    escuela_combo = ttk.Combobox(frame, textvariable=escuela_var, state="readonly", width=47)
    escuela_combo["values"] = [e["nombre"] for e in escuelas]
    escuela_combo.pack(fill="x", pady=2)

    tk.Label(frame, text="Carrera", anchor="w").pack(fill="x")
    carrera_var = tk.StringVar()
    carrera_combo = ttk.Combobox(frame, textvariable=carrera_var, state="readonly", width=47)
    carrera_combo.pack(fill="x", pady=2)

    def actualizar_carreras(event):
        escuela_nombre = escuela_var.get()
        escuela = next((e for e in escuelas if e["nombre"] == escuela_nombre), None)
        if escuela:
            carrera_combo["values"] = escuela["carreras"]
            carrera_combo.set("")

    escuela_combo.bind("<<ComboboxSelected>>", actualizar_carreras)

    error_label = tk.Label(ventana, text="", fg="red", wraplength=460)
    error_label.pack(pady=5)

    def confirmar():
        nombre = campos["nombre"].get().strip()
        apellido = campos["apellido"].get().strip()
        dni_str = campos["dni"].get().strip()
        fecha = campos["fecha_nacimiento"].get().strip()
        email = campos["email"].get().strip()
        escuela_nombre = escuela_var.get()
        carrera = carrera_var.get()

        if not all([nombre, apellido, dni_str, fecha, email, escuela_nombre, carrera]):
            error_label.config(text="Error: todos los campos son obligatorios.")
            return
        if not dni_str.isdigit():
            error_label.config(text="Error: el DNI debe ser numérico.")
            return
        if "@" not in email:
            error_label.config(text="Error: email inválido.")
            return
        try:
            fecha_dt = datetime.strptime(fecha, "%d/%m/%Y")
            edad = (datetime.now() - fecha_dt).days // 365
        except ValueError:
            error_label.config(text="Error: fecha inválida. Usá el formato DD/MM/AAAA.")
            return

        escuela = next((e for e in escuelas if e["nombre"] == escuela_nombre), None)
        inserted_id = registrar_alumno_completo(
            nombre=nombre, apellido=apellido, dni=int(dni_str),
            fecha_nacimiento=fecha, edad=edad, email=email,
            carrera=carrera, escuela_id=str(escuela["_id"])
        )

        if inserted_id:
            messagebox.showinfo("Éxito", "Alumno registrado correctamente.")
            ventana.destroy()
        else:
            error_label.config(text="Error al registrar el alumno.")

    def cancelar():
        ventana.destroy()

    btn_frame = tk.Frame(ventana)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Registrar", command=confirmar,
              bg="#2E75B6", fg="white", width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancelar", command=cancelar, width=15).pack(side="left", padx=5)

    ventana.mainloop()


def ventana_subir_apunte():
    ventana = tk.Tk()
    ventana.title("Subir Apunte — Modo Desarrollador")
    ventana.geometry("520x660")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Formulario de Carga Local", font=("Arial", 15, "bold"), fg="#1F3864").pack(pady=12)

    frame = tk.Frame(ventana)
    frame.pack(padx=25, pady=5, fill="both", expand=True)

    campos = {}

    def agregar_campo(label, key):
        tk.Label(frame, text=label, anchor="w", font=("Arial", 9, "bold")).pack(fill="x", pady=(4, 0))
        entry = tk.Entry(frame, width=50)
        entry.pack(fill="x", pady=2)
        campos[key] = entry

    agregar_campo("Título del apunte", "titulo")
    agregar_campo("Descripción Breve", "descripcion")
    agregar_campo("Materia asignada", "materia")
    agregar_campo("Año de cursada", "año_cursada")
    agregar_campo("Tags explicativos (separar por comas)", "tags")

    tk.Label(frame, text="Tipo de Contenido", anchor="w", font=("Arial", 9, "bold")).pack(fill="x", pady=(4, 0))
    tipo_var = tk.StringVar()
    tipo_combo = ttk.Combobox(frame, textvariable=tipo_var, state="readonly", width=47)
    tipo_combo["values"] = TIPOS_VALIDOS
    tipo_combo.set("documento")
    tipo_combo.pack(fill="x", pady=2)

    archivos_seleccionados = []
    
    # Un contenedor de altura fija baja para que el label no rompa el diseño y oculte los botones inferiores
    frame_lbl = tk.Frame(frame, height=75, bd=1, relief="groove")
    frame_lbl.pack(fill="x", pady=8)
    frame_lbl.pack_propagate(False)
    
    lbl_archivos = tk.Label(frame_lbl, text="Ningún archivo seleccionado", fg="gray", wraplength=450, justify="left", font=("Arial", 9))
    lbl_archivos.pack(padx=5, pady=5, fill="both")

    def alternar_modo_seleccion(event):
        nonlocal archivos_seleccionados
        if tipo_var.get() == "documento" and len(archivos_seleccionados) > 1:
            archivos_seleccionados = [archivos_seleccionados[0]]
            lbl_archivos.config(text=f"Ajustado a archivo único por tipo 'documento':\n{os.path.basename(archivos_seleccionados[0])}", fg="orange")

    tipo_combo.bind("<<ComboboxSelected>>", alternar_modo_seleccion)

    def buscar_archivos():
        nonlocal archivos_seleccionados
        tipo_actual = tipo_var.get()
        # Solo permite selección múltiple si es código o ejercicio técnico
        permitir_multiples = (tipo_actual in ["codigo_fuente", "diseño_tecnico"])
        
        archivos_seleccionados = seleccionar_archivos(permitir_multiples=permitir_multiples)
        if archivos_seleccionados:
            nombres = [os.path.basename(p) for p in archivos_seleccionados]
            lbl_archivos.config(text=f"Cola ({len(archivos_seleccionados)}):\n" + ", ".join(nombres), fg="green")
        else:
            lbl_archivos.config(text="Ningún archivo seleccionado", fg="gray")

    btn_buscar = tk.Button(frame, text="📁 Seleccionar Archivos desde Disco", command=buscar_archivos, font=("Arial", 9, "bold"))
    btn_buscar.pack(anchor="w", pady=2)

    error_label = tk.Label(frame, text="", fg="red", wraplength=460, font=("Arial", 9, "bold"))
    error_label.pack(pady=5)

    def confirmar_subida():
        titulo = campos["titulo"].get().strip()
        descripcion = campos["descripcion"].get().strip()
        materia = campos["materia"].get().strip()
        año_str = campos["año_cursada"].get().strip()
        tags_str = campos["tags"].get().strip()
        tipo = tipo_var.get()

        if not all([titulo, descripcion, materia, año_str, tags_str]):
            error_label.config(text="Error: Completá todos los campos de texto.")
            return
        if not año_str.isdigit():
            error_label.config(text="Error: El año de cursada debe ser un número entero.")
            return
        if not archivos_seleccionados:
            error_label.config(text="Error: Tenés que cargar al menos un archivo válido.")
            return

        # ¡Disparador de confirmación definitivo!
        pregunta = messagebox.askyesno(
            "Confirmación de Subida", 
            f"¿Estás seguro de subir el apunte '{titulo}' con {len(archivos_seleccionados)} archivo(s) asociados?"
        )
        if not pregunta:
            return

        tags = [t.strip() for t in tags_str.split(",")]
        usuario_desarrollador = "kevin_paez"

        apunte_id = subir_apunte(
            nombre_usuario=usuario_desarrollador, titulo=titulo,
            descripcion=descripcion, materia=materia,
            año_cursada=int(año_str), tags=tags, tipo_apunte=tipo,
            archivos_paths=archivos_seleccionados
        )

        if apunte_id:
            indexar_apunte(apunte_id, titulo, descripcion, archivos_seleccionados)
            messagebox.showinfo("Proceso Exitoso", f"El apunte '{titulo}' se subió e indexó correctamente.")
            ventana.destroy()
        else:
            error_label.config(text="Error crítico en el backend al procesar la subida.")

    def cancelar():
        ventana.destroy()

    # Contenedor de botones fijo abajo
    btn_frame = tk.Frame(ventana, pady=10)
    btn_frame.pack(fill="x", side="bottom")
    
    # Separador visual estético
    sep = ttk.Separator(ventana, orient="horizontal")
    sep.pack(fill="x", side="bottom", padx=10)

    tk.Button(btn_frame, text="Confirmar Subida", command=confirmar_subida, bg="#2E75B6", fg="white", width=18, font=("Arial", 10, "bold")).pack(side="right", padx=25)
    tk.Button(btn_frame, text="Cancelar", command=cancelar, width=12, font=("Arial", 10)).pack(side="right", padx=5)

    ventana.mainloop()


def opcion_eliminar_apunte():
    print("\n-- Eliminar Apunte --")
    titulo = input_cancelable("Ingresá el título exacto del apunte a eliminar")
    if not titulo:
        return

    confirmar = input(f"¿Estás completamente seguro de eliminar permanentemente '{titulo}'? (s/n): ").strip().lower()
    if confirmar != 's':
        print("Operación cancelada.")
        return

    apunte_id = eliminar_apunte(titulo)
    if apunte_id:
        eliminar_apunte_vectorial(apunte_id)
        print(f"¡Éxito! El apunte '{titulo}' fue borrado de MongoDB, MinIO y ChromaDB.")
    else:
        print("No se encontró el apunte o no se pudo eliminar.")


def menu():
    print("\n" + "=" * 50)
    print("       UniShare - Plataforma Colaborativa")
    print("=" * 50)
    print("1. Buscar apunte por materia o tipo")
    print("2. Buscar apunte por búsqueda semántica")
    print("3. Consultar alumno")
    print("4. Registrar alumno nuevo")
    print("5. Subir apunte nuevo (GUI)")
    print("6. Eliminar un apunte")
    print("7. Ver URL de archivo")
    print("8. Salir")
    print("=" * 50)
    return input("Elegí una opción: ").strip()

def opcion_buscar_apunte():
    print("\n-- Buscar apunte --")
    materia = input_cancelable("Materia (Enter para omitir)")
    if materia is None:
        return
    materia = materia or None
    tipo = input_cancelable(f"Tipo {TIPOS_VALIDOS} (Enter para omitir)")
    if tipo is None:
        return
    if tipo and tipo not in TIPOS_VALIDOS:
        print(f"Error: tipo inválido. Debe ser uno de {TIPOS_VALIDOS}")
        return
    tipo = tipo or None
    buscar_apuntes(materia=materia, tipo_apunte=tipo)

def opcion_buscar_semantico():
    print("\n-- Búsqueda Semántica --")
    consulta = input_cancelable("¿Qué estás buscando?")
    if consulta is None:
        return
    if not consulta:
        print("Error: la consulta no puede estar vacía.")
        return

    from rag import buscar_semantico_con_apuntes
    resultados = buscar_semantico_con_apuntes(consulta)
    if resultados:
        ventana_resultados_semanticos(resultados)

def opcion_consultar_alumno():
    print("\n-- Consultar Alumno --")
    texto = input_cancelable("Ingresá nombre, apellido o parte del nombre")
    if texto is None:
        return
    if not texto:
        print("Error: el campo no puede estar vacío.")
        return
    resultados = buscar_alumnos_por_nombre(texto)
    if not resultados:
        return
    if len(resultados) == 1:
        legajo = resultados[0]["perfil"].get("legajo")
        buscar_alumno_por_legajo(legajo)
        return
    legajo_str = input_cancelable("Ingresá el legajo para ver los datos completos")
    if legajo_str is None:
        return
    if not legajo_str.isdigit():
        print("Error: el legajo debe ser un número.")
        return
    buscar_alumno_por_legajo(int(legajo_str))

def opcion_ver_url():
    print("\n-- Ver URL de archivo --")
    titulo = input_cancelable("Título del apunte")
    if titulo is None:
        return
    if not titulo:
        print("Error: el título no puede estar vacío.")
        return
    url = obtener_url_archivo(titulo)
    if url:
        registrar_descarga(titulo)

if __name__ == "__main__":
    try:
        print("Inicializando índice semántico...")
        indexar_todos()
        while True:
            try:
                opcion = menu()
                if opcion == "1":
                    opcion_buscar_apunte()
                elif opcion == "2":
                    opcion_buscar_semantico()
                elif opcion == "3":
                    opcion_consultar_alumno()
                elif opcion == "4":
                    ventana_registrar_alumno()
                elif opcion == "5":
                    ventana_subir_apunte()
                elif opcion == "6":
                    opcion_eliminar_apunte()
                elif opcion == "7":
                    opcion_ver_url()
                elif opcion == "8":
                    print("\nHasta luego.")
                    break
                else:
                    print("Opción inválida, intentá de nuevo.")
            except KeyboardInterrupt:
                print("\n\nSaliendo...")
                break
    except Exception as e:
        print(f"\nError inesperado: {e}")