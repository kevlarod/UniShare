from dao import (
    registrar_alumno,
    buscar_alumno,
    buscar_apuntes,
    obtener_url_archivo,
    registrar_descarga
)

print("=" * 50)
print("TEST 1: Buscar alumno existente")
print("=" * 50)
buscar_alumno("kevin_paez")

print("\n" + "=" * 50)
print("TEST 2: Registrar alumno nuevo")
print("=" * 50)
registrar_alumno(
    nombre_usuario="osores_milagros",
    email="milagros@alumno.undec.edu.ar",
    carrera="Ingeniería en Sistemas"
)

print("\n" + "=" * 50)
print("TEST 3: Buscar apuntes por materia")
print("=" * 50)
buscar_apuntes(materia="Estructura de Datos")

print("\n" + "=" * 50)
print("TEST 4: Obtener URL de archivo desde MongoDB")
print("=" * 50)
obtener_url_archivo("Parcial 1 - La Encriptación de Argus")

print("\n" + "=" * 50)
print("TEST 5: Registrar una descarga")
print("=" * 50)
registrar_descarga("Parcial 1 - La Encriptación de Argus")

print("\n" + "=" * 50)
print("TEST 6: Buscar apuntes por tipo")
print("=" * 50)
buscar_apuntes(tipo_apunte="codigo_fuente")

print("\nTodos los tests completados.")
