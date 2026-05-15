#!/bin/bash
echo "Iniciando importación de colecciones..."

mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=universidades --file=/docker-entrypoint-initdb.d/universidades.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=escuelas --file=/docker-entrypoint-initdb.d/escuelas.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=alumnos --file=/docker-entrypoint-initdb.d/alumnos.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=apuntes --file=/docker-entrypoint-initdb.d/apuntes.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=reportes --file=/docker-entrypoint-initdb.d/reportes.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=transacciones --file=/docker-entrypoint-initdb.d/transacciones.json
mongoimport --uri="mongodb://admin:changeme@localhost:27017/unishare_db?authSource=admin" --collection=anuncios --file=/docker-entrypoint-initdb.d/anuncios.json

echo "Importación completada."
