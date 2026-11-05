#!/usr/bin/env bash
# Respaldo de PostgreSQL / TimescaleDB: backups/smartpot-<fecha>.dump.gz (pg_dump comprimido, permisos 600).
# Usa las credenciales del propio contenedor, así que no necesita el .env.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

RETENTION_DAYS="${SMARTPOT_BACKUP_DAYS:-14}"
umask 077
mkdir -p backups
file="backups/smartpot-$(date +%Y%m%d-%H%M%S).dump.gz"

echo "Creando respaldo de la base de datos..."
docker exec smartpot-db sh -c 'pg_dump -U "${POSTGRES_USER:-smartpot-root}" -d "${POSTGRES_DB:-smartpot}" -Fc' | gzip -c > "$file.partial"
mv "$file.partial" "$file"
find backups -name 'smartpot-*.dump.gz' -mtime +"$RETENTION_DAYS" -delete

echo "Respaldo creado: $file ($(du -h "$file" | cut -f1))"
