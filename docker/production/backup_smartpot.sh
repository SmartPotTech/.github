#!/usr/bin/env bash
# Respaldo y restauración de PostgreSQL / TimescaleDB para SmartPot.
#
# Uso:
#   ./backup_smartpot.sh                      # crea backups/smartpot-<UTC>.dump + .manifest + .sha256
#   ./backup_smartpot.sh --restore <archivo>  # restaura limpio: dropdb/createdb + pg_restore --no-owner
#   ./backup_smartpot.sh --help
#
# El respaldo se ejecuta contra el contenedor de la base (PGDUMP dentro del contenedor), no contra el host. No
# necesita el .env: las credenciales y el nombre de la base se leen del propio contenedor. Un flock exclusivo evita
# que dos respaldos o una restauración se solapen y dejen un archivo a medias.
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SMARTPOT_BACKUP_DIR:-${SCRIPT_DIR}/backups}"
CONTAINER="${SMARTPOT_DB_CONTAINER:-smartpot-db}"
RETENTION_DAYS="${SMARTPOT_BACKUP_DAYS:-14}"
LOCK_FILE="${BACKUP_DIR}/.backup.lock"

# Archivos temporales que el trap debe borrar si algo falla antes de publicar el respaldo.
PARTIAL_DUMP=""
PARTIAL_MANIFEST=""
PARTIAL_SHA=""

log() {
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

die() {
    log "ERROR: $*" >&2
    exit 1
}

cleanup() {
    [ -z "$PARTIAL_DUMP" ] || rm -f "$PARTIAL_DUMP"
    [ -z "$PARTIAL_MANIFEST" ] || rm -f "$PARTIAL_MANIFEST"
    [ -z "$PARTIAL_SHA" ] || rm -f "$PARTIAL_SHA"
}
trap cleanup EXIT

usage() {
    cat <<'USAGE'
Usage: backup_smartpot.sh [--restore <archive>] [--help]

Without arguments it creates a verified custom-format backup:
  smartpot-<UTC timestamp>.dump        pg_dump -Fc
  smartpot-<UTC timestamp>.manifest    database metadata and readings range
  smartpot-<UTC timestamp>.dump.sha256 SHA-256 checksum

--restore <archive>  Drops and recreates the database, restores the archive with
                     pg_restore --no-owner, refreshes continuous aggregates and
                     runs ANALYZE. This destroys the current database.

Environment:
  SMARTPOT_DB_CONTAINER  Database container name (default: smartpot-db)
  SMARTPOT_BACKUP_DIR    Destination directory (default: <script dir>/backups)
  SMARTPOT_BACKUP_DAYS   Retention in days (default: 14)
USAGE
}

require_tools() {
    command -v docker >/dev/null 2>&1 || die "docker is required"
    command -v flock >/dev/null 2>&1 || die "flock is required"
    command -v sha256sum >/dev/null 2>&1 || die "sha256sum is required"
    command -v find >/dev/null 2>&1 || die "find is required"
}

require_container() {
    local running
    running="$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || true)"
    [ "$running" = "true" ] || die "container '${CONTAINER}' is not running"
}

# Lee una variable del entorno del contenedor con un valor de respaldo, para no depender del .env del host.
container_env() {
    local name="$1" fallback="$2" value
    value="$(docker exec "$CONTAINER" printenv "$name" 2>/dev/null || true)"
    printf '%s' "${value:-$fallback}"
}

acquire_lock() {
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR" 2>/dev/null || true
    exec 9>"$LOCK_FILE"
    flock -n 9 || die "another backup or restore is already running (lock: ${LOCK_FILE})"
}

# Devuelve las métricas que acompañan al dump. Se consultan después del pg_dump; el manifiesto deja constancia del
# estado observado y permite comparar el conteo tras una restauración.
database_metrics() {
    local user="$1" database="$2"
    docker exec "$CONTAINER" psql -qtAX -F '=' -U "$user" -d "$database" -c "
SELECT * FROM (VALUES
    ('database_size', pg_size_pretty(pg_database_size(current_database()))),
    ('server_version', current_setting('server_version')),
    ('readings_count', (SELECT count(*)::text FROM readings)),
    ('readings_min', (SELECT COALESCE(min(measured_at)::text, '') FROM readings)),
    ('readings_max', (SELECT COALESCE(max(measured_at)::text, '') FROM readings))
) AS metrics(key, value);"
}

backup() {
    local user database stamp base final_dump manifest sha_file toc_entries metrics
    user="$(container_env POSTGRES_USER smartpot-root)"
    database="$(container_env POSTGRES_DB smartpot)"
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    base="smartpot-${stamp}"
    final_dump="${BACKUP_DIR}/${base}.dump"
    manifest="${BACKUP_DIR}/${base}.manifest"
    sha_file="${final_dump}.sha256"

    log "starting backup of database '${database}' from container '${CONTAINER}'"
    PARTIAL_DUMP="${final_dump}.partial"
    PARTIAL_MANIFEST="${manifest}.partial"
    PARTIAL_SHA="${sha_file}.partial"

    # -Fc ya comprime: no se envuelve otra vez en gzip. --lock-wait-timeout evita bloquear la base indefinidamente
    # si una transacción larga mantiene un lock incompatible.
    docker exec "$CONTAINER" pg_dump -U "$user" -d "$database" -Fc --lock-wait-timeout=30s >"$PARTIAL_DUMP" ||
        die "pg_dump failed"

    # Un dump truncado o corrupto se detecta antes de publicarlo: pg_restore --list recorre el TOC completo.
    docker exec -i "$CONTAINER" pg_restore --list <"$PARTIAL_DUMP" >/dev/null ||
        die "archive TOC validation failed"
    toc_entries="$(docker exec -i "$CONTAINER" pg_restore --list <"$PARTIAL_DUMP" | grep -cE '^[0-9]+;' || true)"

    metrics="$(database_metrics "$user" "$database")" || die "could not read database metrics"
    {
        echo "database=${database}"
        echo "container=${CONTAINER}"
        echo "created_at=${stamp}"
        echo "dump_format=custom"
        echo "toc_entries=${toc_entries}"
        echo "sha256_algorithm=sha256"
        printf '%s\n' "$metrics"
    } >"$PARTIAL_MANIFEST"

    # Publicación atómica: el nombre definitivo solo aparece cuando dump, TOC y manifiesto están completos.
    mv -f "$PARTIAL_DUMP" "$final_dump"
    PARTIAL_DUMP=""
    mv -f "$PARTIAL_MANIFEST" "$manifest"
    PARTIAL_MANIFEST=""

    # El checksum se calcula sobre el nombre relativo para que `sha256sum -c` funcione desde el directorio.
    (cd "$BACKUP_DIR" && sha256sum "$(basename "$final_dump")" >"$PARTIAL_SHA")
    mv -f "$PARTIAL_SHA" "$sha_file"
    PARTIAL_SHA=""

    log "backup ready: ${final_dump}"
    log "manifest: ${manifest}"
    log "checksum: ${sha_file}"

    # Retención: se borra el dump y sus dos archivos satélite. El respaldo recién creado nunca entra porque su
    # mtime es de ahora y RETENTION_DAYS es al menos 1.
    find "$BACKUP_DIR" -maxdepth 1 -type f -name 'smartpot-*.dump' -mtime +"$RETENTION_DAYS" -print0 |
        while IFS= read -r -d '' old_dump; do
            old_base="${old_dump%.dump}"
            rm -f "$old_dump" "${old_base}.manifest" "${old_dump}.sha256"
            log "removed expired backup: $(basename "$old_dump")"
        done

    log "backup completed successfully"
}

restore() {
    local archive="$1" user database manifest expected actual
    [ -f "$archive" ] || die "archive not found: ${archive}"
    user="$(container_env POSTGRES_USER smartpot-root)"
    database="$(container_env POSTGRES_DB smartpot)"

    if [ -f "${archive}.sha256" ]; then
        (cd "$(dirname "$archive")" && sha256sum -c "$(basename "${archive}").sha256") ||
            die "checksum verification failed for ${archive}"
    else
        log "WARNING: no SHA-256 sidecar found for ${archive}; continuing without checksum"
    fi

    docker exec -i "$CONTAINER" pg_restore --list <"$archive" >/dev/null ||
        die "archive TOC validation failed"

    log "WARNING: dropping and recreating database '${database}' in container '${CONTAINER}'"
    # dropdb --force cierra las sesiones abiertas; nunca se usa pg_restore --clean porque TimescaleDB no puede
    # recrear limpiamente sus vistas continuas ni las políticas sobre una base existente.
    docker exec "$CONTAINER" dropdb -U "$user" --force --if-exists "$database"
    docker exec "$CONTAINER" createdb -U "$user" -O "$user" "$database"

    docker exec "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$user" -d "$database" \
        -c "CREATE EXTENSION IF NOT EXISTS timescaledb"
    docker exec "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$user" -d "$database" \
        -c "SELECT timescaledb_pre_restore()"

    # --no-owner deja los objetos a nombre del usuario de la conexión (la cuenta administradora del contenedor);
    # los GRANT del dump se conservan porque no se usa --no-privileges.
    docker exec -i "$CONTAINER" pg_restore -U "$user" -d "$database" --exit-on-error --no-owner <"$archive"

    docker exec "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$user" -d "$database" \
        -c "SELECT timescaledb_post_restore()"

    # Refresco completo de los agregados continuos: tras una restauración limpia el catálogo de TimescaleDB existe,
    # pero los datos materializados deben recalcularse desde la hipertabla base. Se usa \gexec y no un bloque DO
    # porque cada refresh abre su propio portal y TimescaleDB rechaza varios CALL en la misma transacción.
    docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$user" -d "$database" <<'SQL'
SELECT format('CALL refresh_continuous_aggregate(%L, NULL, NULL);', view_name)
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;
\gexec
SQL

    docker exec "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$user" -d "$database" -c "ANALYZE"

    # El manifiesto es la prueba de que el archivo restaurado es el que se creó: si el conteo no coincide, la
    # restauración se considera fallida aunque pg_restore haya terminado con código 0.
    if [ -f "${archive%.dump}.manifest" ]; then
        manifest="${archive%.dump}.manifest"
    elif [ -f "${archive}.manifest" ]; then
        manifest="${archive}.manifest"
    else
        manifest=""
    fi
    if [ -n "$manifest" ]; then
        expected="$(sed -n 's/^readings_count=//p' "$manifest" | head -n 1)"
        actual="$(docker exec "$CONTAINER" psql -qtAX -U "$user" -d "$database" -c 'SELECT count(*) FROM readings')"
        [ -n "$expected" ] || die "manifest has no readings_count: ${manifest}"
        [ "$expected" = "$actual" ] ||
            die "readings count mismatch after restore (manifest=${expected}, database=${actual})"
        log "readings count verified: ${actual}"
    else
        log "WARNING: no manifest found next to ${archive}; row count was not verified"
    fi

    log "restore completed successfully"
}

case "${1:-}" in
    "")
        require_tools
        acquire_lock
        require_container
        backup
        ;;
    --restore)
        [ "$#" -eq 2 ] || {
            usage >&2
            exit 2
        }
        require_tools
        acquire_lock
        require_container
        restore "$2"
        ;;
    --help | -h)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
