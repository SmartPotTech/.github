#!/usr/bin/env bash
# Respaldo de MongoDB: backups/smartpot-<fecha>.archive.gz (mongodump comprimido, permisos 600).
# Usa las credenciales del propio contenedor, así que no necesita el .env.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

RETENTION_DAYS="${SMARTPOT_BACKUP_DAYS:-14}"
umask 077
mkdir -p backups
file="backups/smartpot-$(date +%Y%m%d-%H%M%S).archive.gz"

echo "Creando respaldo de la base de datos..."
docker exec smartpot-db sh -c 'mongodump --quiet --archive --gzip \
  --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin --db "${SMARTPOT_DB_NAME:-smartpot}"' > "$file.partial"
mv "$file.partial" "$file"
find backups -name 'smartpot-*.archive.gz' -mtime +"$RETENTION_DAYS" -delete

echo "Respaldo creado: $file ($(du -h "$file" | cut -f1))"
