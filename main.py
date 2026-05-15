import os
import tkinter as tk
from tkinter import filedialog
from dao import registrar_alumno, buscar_alumno, buscar_apuntes, obtener_url_archivo, registrar_descarga, subir_apunte, existe_alumno, buscar_alumnos_por_nombre, buscar_alumno_por_legajo
from rag import buscar_semantico, indexar_apunte, indexar_todos

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

def opcion_registrar_alumno():
    print("\n-- Registrar Alumno --")

    nombre = input_cancelable("Nombre")
    if nombre is None:
        return
    if not nombre:
        print("Error: el nombre no puede estar vacío.")
        return

    apellido = input_cancelable("Apellido")
    if apellido is None:
        return
    if not apellido:
        print("Error: el apellido no puede estar vacío.")
        return

    nombre_usuario = input_cancelable("Nombre de usuario")
    if nombre_usuario is None:
        return
    if not nombre_usuario:
        print("Error: el nombre de usuario no puede estar vacío.")
        return
    if existe_alumno(nombre_usuario):
        print(f"Error: el usuario '{nombre_usuario}' ya existe.")
        return

    email = input_cancelable("Email institucional")
    if email is None:
        return
    if not email or "@" not in email:
        print("Error: email inválido.")
        return

    carrera = input_cancelable("Carrera")
    if carrera is None:
        return
    if not carrera:
        print("Error: la carrera no puede estar vacía.")
        return

    registrar_alumno(nombre_usuario, email, carrera, nombre=nombre, apellido=apellido)

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
                    opcion_registrar_alumno()
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
