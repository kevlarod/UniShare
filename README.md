# Universidad Nacional de Chilecito

## Equipo de Trabajo
Kevin Paez kevoundec@gmail.com

Lara Brizuela 

Lucas Gonzalez lucas.g44741491@gmail.com

Milagros Osores 

# UniShare
Plataforma de Conocimiento Colaborativo — Base de Datos II 2026

UniShare integra un ecosistema de múltiples bases de datos: **MongoDB** para datos estructurados y transaccionales, **MinIO** como Object Storage para los archivos físicos, y **ChromaDB** como base de datos vectorial para habilitar la búsqueda semántica de apuntes mediante RAG (Retrieval-Augmented Generation).

#### Antes de comenzar, necesitás:
* Docker Desktop instalado y corriendo
* Python 3.12
* pip install --upgrade pip

#### Levantar los contenedores (MongoDB y MinIO)
* cp .env.example .env
* docker compose up -d

#### Crear el entorno virtual
* python3 -m venv venv

#### Activar el entorno virtual
* Linux/Mac: source venv/bin/activate
* Windows: venv\Scripts\activate

#### Instalar librerías
* pip install pymongo minio chromadb sentence-transformers pymupdf

#### Verificar que las bases de datos funcionan
1. Probar la conexión transaccional y el storage:
   * python3 test_dao.py
2. Probar la indexación y el motor de búsqueda semántica:
   * python3 test_rag.py

#### Arrancar la aplicación principal
Para usar la plataforma de forma interactiva (menú por consola e interfaz gráfica con Tkinter):
* python3 main.py

#### Accesos a las bases de datos
* **Panel de MinIO:** http://localhost:9001
  * Usuario: minioadmin
  * Contraseña: changeme
* **Mongo Shell:** docker exec -it unishare_mongodb mongo -u admin -p changeme --authenticationDatabase admin
* **ChromaDB:** La base de datos vectorial persiste de forma local en el directorio `./chroma_db` (se crea automáticamente al inicializar).

#### Colecciones disponibles en MongoDB
* universidades
* alumnos
* apuntes
* reportes
* transacciones
* anuncios

#### Archivos del proyecto
* config_vars.py — credenciales de conexión a MongoDB y MinIO
* dao.py — funciones para interactuar con MongoDB y MinIO
* rag.py — lógica de extracción de texto, generación de embeddings (all-MiniLM-L6-v2) e indexación en ChromaDB
* test_dao.py — pruebas de integración para MongoDB y MinIO
* test_rag.py — pruebas del motor de búsqueda vectorial
* main.py — script principal que unifica la carga de datos, registro de usuarios y búsquedas semánticas/tradicionales
