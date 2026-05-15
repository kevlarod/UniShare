#!/bin/bash

echo "Iniciando la carga de datos (Seeding)..."

COLLECTIONS=("alumnos" "anuncios" "apuntes" "escuelas" "reportes" "transacciones" "universidades")

for col in "${COLLECTIONS[@]}"; do
    echo "Importando colección: $col..."
    mongoimport --username "$MONGO_INITDB_ROOT_USERNAME" \
                --password "$MONGO_INITDB_ROOT_PASSWORD" \
                --authenticationDatabase admin \
                --db "$MONGO_INITDB_DATABASE" \
                --collection "$col" \
                --type json \
                --file "/docker-entrypoint-initdb.d/${col}.json"
done

echo "Carga de datos finalizada exitosamente."
