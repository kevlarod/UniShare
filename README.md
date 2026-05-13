# UniShare - Plataforma de Conocimiento Colaborativo

Repositorio académico colaborativo para estudiantes universitarios.
Proyecto Integrador — Base de Datos II — UNDEC 2026.

## Integrantes
Paez Kevin
Brizuela Lara
Gonzalez Lucas
Osores Milagros

## Stack Tecnológico
- **Base de datos**: MongoDB 4.4
- **Object Storage**: MinIO
- **Infraestructura**: Docker + Docker Compose

## Requisitos Previos
- Docker Desktop instalado y corriendo
- Git configurado

## Levantar el entorno

1. Clonar el repositorio:
   git clone https://github.com/kevlarod/UniShare.git
   cd UniShare

2. Crear el archivo de variables de entorno:
   cp .env.example .env

3. Levantar los contenedores:
   docker compose up -d

4. Verificar que estén corriendo:
   docker compose ps

## Base de Datos MongoDB

Las colecciones se encuentran en docker/mongo-seed/.

### Colecciones
- universidades
- alumnos
- apuntes
- reportes
- transacciones
- anuncios

## Estado del Proyecto
- [x] Infraestructura Docker
- [x] Base de datos MongoDB con colecciones e índices
- [ ] Object Storage MinIO
- [ ] Backend Python
- [ ] Frontend
