import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from dao import registrar_alumno, buscar_alumno, buscar_apuntes, obtener_url_archivo, registrar_descarga, subir_apunte, existe_alumno, buscar_alumnos_por_nombre, buscar_alumno_por_legajo, obtener_escuelas, registrar_alumno_completo
from rag import buscar_semantico, indexar_apunte, indexar_todos
from datetime import datetime

TIPOS_VALIDOS = ["documento", "codigo_fuente", "diseño_tecnico"]

def input_cancelable(mensaje):
    valor = input(f"{mensaje} (o 'cancelar' para volver al menú): ").strip()
    if valor.lower() == "cancelar":
        print("Operación cancelada.")
        return None
    return valor

def seleccionar_archivo():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        archivo = filedialog.askopenfilename(
            title="Seleccioná el archivo a subir",
            filetypes=[
                ("Todos los archivos", "*.*"),
                ("PDF", "*.pdf"),
                ("Código fuente", "*.c *.py *.java *.h *.cpp"),
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("AutoCAD", "*.dwg *.dxf")
            ]
        )
        root.destroy()
        if not archivo:
            print("No seleccionaste ningún archivo.")
            return None
        print(f"Archivo seleccionado: {archivo}")
        return archivo
    except Exception as e:
        print(f"No se pudo abrir el gestor de archivos: {e}")
        return input_cancelable("Ingresá la ruta del archivo manualmente")

def ventana_registrar_alumno():
    escuelas = obtener_escuelas()
    if not escuelas:
        print("Error: no se pudieron cargar las escuelas.")
        return

    resultado = {"completado": False}

    ventana = tk.Tk()
    ventana.title("Registrar Alumno — UniShare")
    ventana.geometry("500x600")
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
            nombre=nombre,
            apellido=apellido,
            dni=int(dni_str),
            fecha_nacimiento=fecha,
            edad=edad,
            email=email,
            carrera=carrera,
            escuela_id=str(escuela["_id"])
        )

        if inserted_id:
            messagebox.showinfo("Éxito", f"Alumno registrado correctamente.")
            resultado["completado"] = True
            ventana.destroy()
        else:
            error_label.config(text="Error al registrar el alumno.")

    def cancelar():
        ventana.destroy()

    btn_frame = tk.Frame(ventana)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Registrar", command=confirmar, bg="#2E75B6", fg="white", width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancelar", command=cancelar, width=15).pack(side="left", padx=5)

    ventana.mainloop()

def menu():
    print("\n" + "=" * 50)
    print("       UniShare - Plataforma Colaborativa")
    print("=" * 50)
    print("1. Buscar apunte por materia o tipo")
    print("2. Buscar apunte por búsqueda semántica")
    print("3. Consultar alumno")
    print("4. Registrar alumno nuevo")
    print("5. Subir apunte nuevo")
    print("6. Ver URL de archivo")
    print("7. Salir")
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
    buscar_semantico(consulta)

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

def opcion_subir_apunte():
    print("\n-- Subir Apunte --")
    nombre_usuario = input_cancelable("Tu nombre de usuario")
    if nombre_usuario is None:
        return
    if not existe_alumno(nombre_usuario):
        print(f"Error: el usuario '{nombre_usuario}' no existe.")
        return
    titulo = input_cancelable("Título del apunte")
    if titulo is None:
        return
    if not titulo:
        print("Error: el título no puede estar vacío.")
        return
    descripcion = input_cancelable("Descripción")
    if descripcion is None:
        return
    if not descripcion:
        print("Error: la descripción no puede estar vacía.")
        return
    materia = input_cancelable("Materia")
    if materia is None:
        return
    if not materia:
        print("Error: la materia no puede estar vacía.")
        return
    año_str = input_cancelable("Año cursada")
    if año_str is None:
        return
    if not año_str.isdigit():
        print("Error: el año debe ser un número.")
        return
    año = int(año_str)
    tags_str = input_cancelable("Tags (separados por coma)")
    if tags_str is None:
        return
    if not tags_str:
        print("Error: ingresá al menos un tag.")
        return
    tags = [t.strip() for t in tags_str.split(",")]
    tipo = input_cancelable(f"Tipo {TIPOS_VALIDOS}")
    if tipo is None:
        return
    if tipo not in TIPOS_VALIDOS:
        print(f"Error: tipo inválido. Debe ser uno de {TIPOS_VALIDOS}")
        return
    print("Abriendo gestor de archivos...")
    archivo = seleccionar_archivo()
    if archivo is None:
        return
    if not os.path.exists(archivo):
        print(f"Error: el archivo no existe.")
        return
    apunte_id = subir_apunte(
        nombre_usuario=nombre_usuario,
        titulo=titulo,
        descripcion=descripcion,
        materia=materia,
        año_cursada=año,
        tags=tags,
        tipo_apunte=tipo,
        archivo_path=archivo
    )
    if apunte_id:
        indexar_apunte(apunte_id, titulo, descripcion, archivo)

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
                    opcion_subir_apunte()
                elif opcion == "6":
                    opcion_ver_url()
                elif opcion == "7":
                    print("\nHasta luego.")
                    break
                else:
                    print("Opción inválida, intentá de nuevo.")
            except KeyboardInterrupt:
                print("\n\nSaliendo...")
                break
    except Exception as e:
        print(f"\nError inesperado: {e}")
