# Universidad Nacional de Chilecito

## Equipo de Trabajo
Kevin Paez kevoundec@gmail.com

Lara Brizuela 

Lucas Gonzalez lucas.g44741491@gmail.com

Milagros Osores 

# UniShare
Plataforma de Conocimiento Colaborativo — Base de Datos II 2026

#### Antes de comenzar, necesitás:
* Docker Desktop instalado y corriendo
* Python 3.12
* pip install --upgrade pip

#### Levantar los contenedores
* cp .env.example .env
* docker compose up -d

#### Crear el entorno virtual
* python3 -m venv venv

#### Activar el entorno virtual
* Linux/Mac: source venv/bin/activate
* Windows: venv\Scripts\activate

#### Instalar librerías
* pip install pymongo minio

#### Verificar que las bases de datos funcionan
* python3 test_dao.py

#### Para acceder al panel de MinIO
* http://localhost:9001
* Usuario: minioadmin
* Contraseña: changeme

#### Para conectarse al Mongo Shell
* docker exec -it unishare_mongodb mongo -u admin -p changeme --authenticationDatabase admin

#### Colecciones disponibles en MongoDB
* universidades
* alumnos
* apuntes
* reportes
* transacciones
* anuncios

#### Archivos del proyecto
* config_vars.py — credenciales de conexión a MongoDB y MinIO
* dao.py — funciones para interactuar con ambas bases de datos
* test_dao.py — pruebas que demuestran que todo funciona junto
