from sentence_transformers import SentenceTransformer
import chromadb
from pymongo import MongoClient
import fitz  # pymupdf
import os

from config_vars import MONGO_URI, MONGO_DB_NAME

# Conexiones
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]

chroma_client = chromadb.PersistentClient(path="./chroma_db")
coleccion = chroma_client.get_or_create_collection("apuntes")

modelo = SentenceTransformer("all-MiniLM-L6-v2")

# ─── EXTRAER TEXTO ─────────────────────────────────────────

def extraer_texto_pdf(path):
    texto = ""
    try:
        doc = fitz.open(path)
        for pagina in doc:
            texto += pagina.get_text()
    except Exception as e:
        print(f"Error al leer PDF: {e}")
    return texto

def extraer_texto_codigo(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error al leer archivo: {e}")
        return ""

# ─── INDEXAR APUNTE ────────────────────────────────────────

def indexar_apunte(apunte_id, titulo, descripcion, archivo_path=None):
    texto = f"{titulo}. {descripcion}"

    if archivo_path and os.path.exists(archivo_path):
        extension = archivo_path.split(".")[-1].lower()
        if extension == "pdf":
            texto += " " + extraer_texto_pdf(archivo_path)
        elif extension in ["c", "py", "java", "txt", "md", "h"]:
            texto += " " + extraer_texto_codigo(archivo_path)

    vector = modelo.encode(texto).tolist()

    coleccion.upsert(
        ids=[str(apunte_id)],
        embeddings=[vector],
        metadatas=[{"titulo": titulo, "apunte_id": str(apunte_id)}]
    )
    print(f"Apunte '{titulo}' indexado en ChromaDB")

# ─── BUSQUEDA SEMÁNTICA ────────────────────────────────────

def buscar_semantico(consulta, n_resultados=3):
    vector_consulta = modelo.encode(consulta).tolist()

    resultados = coleccion.query(
        query_embeddings=[vector_consulta],
        n_results=n_resultados
    )

    ids_encontrados = resultados["ids"][0]
    distancias = resultados["distances"][0]

    print(f"\nResultados para: '{consulta}'")
    print("=" * 50)

    apuntes_encontrados = []
    for i, apunte_id in enumerate(ids_encontrados):
        apunte = db.apuntes.find_one({"_id": __import__("bson").ObjectId(apunte_id)})
        if apunte:
            relevancia = round((1 - distancias[i]) * 100, 2)
            print(f"  {i+1}. {apunte['titulo']}")
            print(f"     Materia: {apunte['categoria']['materia']}")
            print(f"     Tipo: {apunte['categoria']['tipo_apunte']}")
            print(f"     Relevancia: {relevancia}%")
            apuntes_encontrados.append(apunte)

    return apuntes_encontrados

# ─── INDEXAR TODOS LOS APUNTES ─────────────────────────────

def indexar_todos():
    apuntes = list(db.apuntes.find())
    print(f"Indexando {len(apuntes)} apunte(s)...")
    for apunte in apuntes:
        indexar_apunte(
            apunte_id=apunte["_id"],
            titulo=apunte["titulo"],
            descripcion=apunte["descripcion"]
        )
    print("Indexación completada.")

