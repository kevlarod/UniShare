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

