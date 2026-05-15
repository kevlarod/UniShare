from pymongo import MongoClient
from minio import Minio
from minio.error import S3Error
from bson import ObjectId
import datetime
import os

from config_vars import (
    MONGO_URI, MONGO_DB_NAME,
    MINIO_ENDPOINT, MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE
)

# Conexiones
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

# ─── ALUMNOS ───────────────────────────────────────────────

def registrar_alumno(nombre_usuario, email, carrera, siglas_universidad="UNDEC"):
    universidad = db.universidades.find_one({ "institucion.siglas": siglas_universidad })
    if not universidad:
        return {"error": f"Universidad {siglas_universidad} no encontrada"}

    alumno = {
        "perfil": {
            "nombre_usuario": nombre_usuario,
            "email": email,
            "universidad": {
                "id_universidad": universidad["_id"],
                "siglas": siglas_universidad
            },
            "carrera": carrera
        },
        "seguridad": {
            "password_hash": "$2b$12$placeholder",
            "estado_cuenta": "pendiente",
            "rol": "alumno"
        },
        "economia": {
            "creditos_disponibles": 0.0,
            "total_ganado_historico": 0.0
        },
        "reputacion": {
            "puntos": 0,
            "insignias": [],
            "cantidad_aportes": 0
        }
    }
    resultado = db.alumnos.insert_one(alumno)
    print(f"Alumno '{nombre_usuario}' registrado con ID: {resultado.inserted_id}")
    return resultado.inserted_id

def buscar_alumno(nombre_usuario):
    alumno = db.alumnos.find_one({ "perfil.nombre_usuario": nombre_usuario })
    if alumno:
        print(f"Alumno encontrado: {alumno['perfil']['nombre_usuario']} - {alumno['perfil']['carrera']}")
    else:
        print(f"Alumno '{nombre_usuario}' no encontrado")
    return alumno

# ─── APUNTES ───────────────────────────────────────────────

def subir_apunte(nombre_usuario, titulo, descripcion, materia, año_cursada, tags, tipo_apunte, archivo_path):
    alumno = db.alumnos.find_one({ "perfil.nombre_usuario": nombre_usuario })
    if not alumno:
        return {"error": f"Alumno '{nombre_usuario}' no encontrado"}

    nombre_archivo = os.path.basename(archivo_path)
    extension = nombre_archivo.split(".")[-1]

    if tipo_apunte == "documento":
        carpeta = "apuntes"
        tipo_archivo = "pdf" if extension == "pdf" else "imagen"
    elif tipo_apunte == "codigo_fuente":
        carpeta = "proyectos"
        tipo_archivo = "codigo"
    else:
        carpeta = "apuntes"
        tipo_archivo = "pdf"

    objeto_path = f"{carpeta}/{nombre_archivo}"

    try:
        minio_client.fput_object(MINIO_BUCKET, objeto_path, archivo_path)
        print(f"Archivo '{nombre_archivo}' subido a MinIO en: {objeto_path}")
    except S3Error as e:
        return {"error": f"Error al subir a MinIO: {e}"}

    apunte = {
        "autor_id": alumno["_id"],
        "titulo": titulo,
        "descripcion": descripcion,
        "categoria": {
            "tipo_apunte": tipo_apunte,
            "materia": materia,
            "año_cursada": año_cursada,
            "tags": tags
        },
        "recursos": [{
            "nombre": nombre_archivo,
            "formato": extension,
            "url_storage": f"unishare/{objeto_path}",
            "es_descriptor": True,
            "tipo_archivo": tipo_archivo
        }],
        "estadisticas": {
            "descargas": 0,
            "votos_positivos": 0,
            "votos_negativos": 0,
            "visualizaciones": 0
        }
    }
    resultado = db.apuntes.insert_one(apunte)
    print(f"Apunte '{titulo}' registrado en MongoDB con ID: {resultado.inserted_id}")
    return resultado.inserted_id

def buscar_apuntes(materia=None, tipo_apunte=None, tag=None):
    filtro = {}
    if materia:
        filtro["categoria.materia"] = materia
    if tipo_apunte:
        filtro["categoria.tipo_apunte"] = tipo_apunte
    if tag:
        filtro["categoria.tags"] = tag

    apuntes = list(db.apuntes.find(filtro, {
        "titulo": 1,
        "categoria": 1,
        "estadisticas": 1
    }))

    print(f"\n{len(apuntes)} apunte(s) encontrado(s):")
    for a in apuntes:
        print(f"  - {a['titulo']} | {a['categoria']['tipo_apunte']} | {a['categoria']['materia']}")
    return apuntes

def obtener_url_archivo(titulo_apunte):
    apunte = db.apuntes.find_one({ "titulo": titulo_apunte })
    if not apunte:
        print(f"Apunte '{titulo_apunte}' no encontrado")
        return None

    recursos = apunte.get("recursos", [])
    if not recursos:
        print("El apunte no tiene recursos")
        return None

    url = recursos[0]["url_storage"]
    print(f"URL del archivo: {url}")
    return url

# ─── ESTADÍSTICAS ──────────────────────────────────────────

def registrar_descarga(titulo_apunte):
    resultado = db.apuntes.update_one(
        { "titulo": titulo_apunte },
        { "$inc": { "estadisticas.descargas": 1 } }
    )
    if resultado.modified_count:
        print(f"Descarga registrada para: '{titulo_apunte}'")
    return resultado.modified_count


def existe_alumno(nombre_usuario):
    return db.alumnos.find_one({ "perfil.nombre_usuario": nombre_usuario }) is not None

def buscar_alumnos_por_nombre(texto):
    import re
    regex = re.compile(texto, re.IGNORECASE)
    resultados = list(db.alumnos.find({
        "$or": [
            { "perfil.nombre": regex },
            { "perfil.apellido": regex },
            { "perfil.nombre_usuario": regex }
        ]
    }))

    if not resultados:
        print(f"No se encontraron alumnos con '{texto}'")
        return []

    print(f"\n{len(resultados)} alumno(s) encontrado(s):")
    for a in resultados:
        print(f"  - {a['perfil'].get('nombre', '')} {a['perfil'].get('apellido', '')} | Legajo: {a['perfil'].get('legajo', 'N/A')}")
    return resultados

def buscar_alumno_por_legajo(legajo):
    alumno = db.alumnos.find_one({ "perfil.legajo": legajo })
    if not alumno:
        print(f"No se encontró ningún alumno con legajo {legajo}")
        return None

    p = alumno["perfil"]
    s = alumno["seguridad"]
    e = alumno.get("economia", {})
    r = alumno.get("reputacion", {})

    print(f"\n{'=' * 40}")
    print(f"  Nombre:    {p.get('nombre', '')} {p.get('apellido', '')}")
    print(f"  Usuario:   {p.get('nombre_usuario', '')}")
    print(f"  Legajo:    {p.get('legajo', '')}")
    print(f"  Email:     {p.get('email', '')}")
    print(f"  Carrera:   {p.get('carrera', '')}")
    print(f"  Rol:       {s.get('rol', '')}")
    print(f"  Estado:    {s.get('estado_cuenta', '')}")
    print(f"  Créditos:  {e.get('creditos_disponibles', 0)}")
    print(f"  Puntos:    {r.get('puntos', 0)}")
    print(f"  Aportes:   {r.get('cantidad_aportes', 0)}")
    print(f"  Insignias: {r.get('insignias', [])}")
    print(f"{'=' * 40}")
    return alumno

def obtener_escuelas():
    return list(db.escuelas.find())

def generar_nombre_usuario(nombre, apellido, dni, edad):
    base = nombre[:2].lower() + apellido[:2].lower() + str(dni)[-2:] + str(edad)
    if db.alumnos.find_one({ "perfil.nombre_usuario": base }):
        base = base + "_2"
    return base

def generar_legajo():
    import random
    while True:
        legajo = random.randint(10000, 99999)
        if not db.alumnos.find_one({ "perfil.legajo": legajo }):
            return legajo

def registrar_alumno_completo(nombre, apellido, dni, fecha_nacimiento, edad, email, carrera, escuela_id, siglas_universidad="UNDEC"):
    from datetime import datetime
    import bson

    universidad = db.universidades.find_one({ "institucion.siglas": siglas_universidad })
    if not universidad:
        return {"error": f"Universidad {siglas_universidad} no encontrada"}

    nombre_usuario = generar_nombre_usuario(nombre, apellido, dni, edad)
    legajo = generar_legajo()

    alumno = {
        "perfil": {
            "nombre_usuario": nombre_usuario,
            "nombre": nombre,
            "apellido": apellido,
            "legajo": legajo,
            "dni": dni,
            "fecha_nacimiento": datetime.strptime(fecha_nacimiento, "%d/%m/%Y"),
            "edad": edad,
            "email": email,
            "escuela_id": bson.ObjectId(escuela_id),
            "carrera": carrera,
            "universidad": {
                "id_universidad": universidad["_id"],
                "siglas": siglas_universidad
            }
        },
        "seguridad": {
            "password_hash": "$2b$12$placeholder",
            "estado_cuenta": "pendiente",
            "rol": "alumno"
        },
        "economia": {
            "creditos_disponibles": 0.0,
            "total_ganado_historico": 0.0
        },
        "reputacion": {
            "puntos": 0,
            "insignias": [],
            "cantidad_aportes": 0
        }
    }

    resultado = db.alumnos.insert_one(alumno)
    print(f"Alumno '{nombre_usuario}' registrado con legajo {legajo}")
    return resultado.inserted_id
