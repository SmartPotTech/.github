# SmartPot Production Deployment with Docker

[English](#english) | [Español](#español)

---

<a id="english"></a>

## English

This guide describes the SmartPot **production** environment: a dedicated server behind Nginx with HTTPS, the EMQX MQTT broker exposed over TLS for real crop devices, and automatic updates through GitHub Actions whenever `main` changes in any service.

| Domain                         | Service                                                 |
| ------------------------------ | ------------------------------------------------------- |
| `smartpot.app` (and `www`)     | PWA built with SolidJS 1.9 and Bun                      |
| `api.smartpot.app`             | Go REST API (Echo), documentation at `/docs`            |
| `mcp.smartpot.app`             | Model Context Protocol server (FastMCP) for MCP clients |
| `mqtt.smartpot.app:8883`       | MQTT over TLS (1.2 or later) for devices                |
| `wss://mqtt.smartpot.app/mqtt` | MQTT over secure WebSocket (EMQX)                       |
| `mail.smartpot.app`            | Mailpit inbox with username and password                |

---

### Requirements

- **Docker Engine** and **Docker Compose v2.20 or later**: [installation instructions](https://docs.docker.com/engine/install/)
- An SSH user with Docker access (`root` or passwordless `sudo`).
- **Nginx** and **Certbot** to publish the domains over HTTPS.
- `A` records for `smartpot.app`, `api`, `mcp`, `mqtt`, and `mail` pointing to the server, and `www` as a `CNAME` for `smartpot.app`.
- Port **8883/tcp** open in the firewall for physical devices.

---

### Environment Architecture

```mermaid
flowchart LR
  B[Navegador] -->|HTTPS 443| N[Nginx + Let's Encrypt]
  M[ESP32 de un cultivo real] -->|MQTT TLS 8883| K[broker-smartpot: EMQX]
  N -->|127.0.0.1:5173| W[web-smartpot: SolidJS]
  N -->|127.0.0.1:8091| A[api-smartpot: Go]
  N -->|127.0.0.1:8092| P[mcp-smartpot: FastMCP]
  N -->|127.0.0.1:9001 wss| K
  N -->|127.0.0.1:8025| E[mail-smartpot: Mailpit]
  A -->|red interna| D[(db-smartpot: TimescaleDB)]
  A -->|red interna o socket| C[(cache-smartpot: Valkey)]
  A -->|gRPC / REST interno| I[ai-smartpot: Rust]
  D -.->|ADBC lectura continua| R[trainer-smartpot: Python]
  R -.->|modelos JSON firmados| I
  A -->|red interna| V[simulator-smartpot: Rust]
  V -->|MQTT interno| K
  V -.->|clima| O[Open-Meteo]
  A <-->|MQTT interno| K
  K -.->|POST /internal/mqtt/authn| A
  A -->|SMTP 1025 interno| E
  P -->|REST + spt_... token| A
  A -.->|alertas| T[Telegram Bot API]
  T -.->|webhook firmado| N
```

| Service                          | Network                                | Host port                        | Variables received                                                                                                                                    |
| -------------------------------- | -------------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `db-smartpot` (profile `db`)     | `internal`                             | None                             | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SMARTPOT_DB_USERNAME`, `SMARTPOT_DB_PASSWORD`, `SMARTPOT_READER_PASSWORD`, `SMARTPOT_SEED_DEMO` |
| `cache-smartpot`                 | `internal`                             | None                             | `VALKEY_PASSWORD`, `VALKEY_SOCKET`                                                                                                                    |
| `mail-smartpot` (profile `mail`) | `internal` + `public`                  | `127.0.0.1:8025`                 | `MAIL_*`, `MAILPIT_UI_*`                                                                                                                              |
| `broker-smartpot`                | `internal` + `public`                  | `0.0.0.0:8883`, `127.0.0.1:9001` | `MQTT_ADMIN_*`, certificates in `SMARTPOT_CERTS_DIR`, `MQTT_AUTHN_TOKEN`                                                                              |
| `ai-smartpot`                    | `internal`                             | None                             | `SMARTPOT_AI_TOKEN`, `TRUSTED_MODEL_PUBLIC_KEY_HEX`; volume `ai_data`                                                                                 |
| `trainer-smartpot`               | `internal`                             | None                             | `DATABASE_URL` (read-only role), `SMARTPOT_TRAINER_TOKEN`, `MODEL_SIGNING_KEY_PATH`, `SMARTPOT_AI_TOKEN`, `SMARTPOT_AI_URL`                           |
| `api-smartpot`                   | `internal` + `public`                  | `127.0.0.1:8091`                 | `DATABASE_URL` (writable role), `CACHE_URL`, JWT, AES, internal connections, `SIMULATOR_TOKEN`, `TELEGRAM_*`                                          |
| `web-smartpot`                   | `public`                               | `127.0.0.1:5173`                 | `PUBLIC_API_URL`                                                                                                                                      |
| `mcp-smartpot`                   | `internal` + `public`                  | `127.0.0.1:8092`                 | `PUBLIC_API_URL`, `MCP_ALLOWED_ORIGINS`                                                                                                               |
| `simulator-smartpot`             | `internal` + `public` (weather egress) | None                             | `SIMULATOR_*`, `MQTT_*`                                                                                                                               |

All configuration lives in a single `.env`, but `compose.yaml` gives each container only its own variables: the PWA never sees the JWT secret and the AI service only knows its token. The `internal` network has no internet egress: PostgreSQL, Valkey, and the AI service are not reachable from outside. The virtual crop simulator uses `public` only to query the weather and publishes no ports. Its control API is used only by the SmartPot API, with a token.

**Model signing custody.** The AI mounts `ai_data:/data:ro`; it only reads `{SPECIES}_inference.json` and `{SPECIES}_manifest.json`. The Trainer writes models to `ai_data` and keeps the Ed25519 private key in a separate `trainer_keys` volume mounted at `/data/keys` (mode `0600`), never readable by the AI. Set `MODEL_SIGNING_KEY_PATH=/data/keys/ed25519_private.pem` and `TRUSTED_MODEL_PUBLIC_KEY_HEX=<32-byte hex>` so the AI authenticates every learned package; without the trust anchor it only checks the BLAKE2b hash. The MCP server validates each `spt_` token against the API and caches the verdict for 30 seconds (`MCP_TOKEN_CACHE_SECONDS`), including `tools/list`.

### Database Roles

Production separates database roles. The API connects with the writable `DATABASE_URL` and the `smartpot` role. The trainer connects with a URL built from `smartpot_reader` and `SMARTPOT_READER_PASSWORD`, so it can never write through the API role. Development uses the same split. Kubernetes mounts the `TRAINER_DATABASE_URL` secret key as the trainer's `DATABASE_URL`, while the API keeps `DATABASE_URL`.

The reader role can read `readings`, the `trainer_readings` security-barrier view, and only `id`, `type`, and `kind` from `crops`. It has no access to users, device credentials, or tokens.

### Hardening

| Control                                                                          | Where                                   |
| -------------------------------------------------------------------------------- | --------------------------------------- |
| Read-only filesystem with `tmpfs` for temporary data                             | All services                            |
| No Linux capabilities (`cap_drop: ALL`) and `no-new-privileges`                  | All services                            |
| Unprivileged users in every image                                                | Production images                       |
| CPU and memory limits, `ulimits`, and log rotation (10 MB x 3)                   | All services                            |
| Only the broker listens outside `127.0.0.1`, and only over TLS                   | `broker-smartpot` (EMQX)                |
| Every crop has unique credentials and a narrow ACL enforced over HTTP in the API | EMQX authn delegation in `SmartPot-API` |
| Healthchecks and ordered startup (`depends_on: service_healthy`)                 | All services                            |
| `.env` and certificates only during deployment                                   | Deployment workflow                     |
| Public images signed in GHCR with SBOM and provenance                            | GHCR                                    |

---

### Automatic Deployment (GitHub Actions)

```mermaid
sequenceDiagram
  participant R as Repo de un servicio
  participant G as GHCR y Docker Hub
  participant Q as request-deploy.yml
  participant D as deploy.yml (.github)
  participant S as Servidor
  R->>G: packaging.yml publica la imagen
  R->>Q: deploy.yml del repo pide el despliegue
  Q->>D: workflow_dispatch (origen, commit, id de solicitud)
  Note over D: concurrency smartpot-production: uno en curso y uno en espera
  D->>D: genera .env desde ENV_FILE, valida secretos y certificados
  D->>S: SSH: compose.yaml, .env (600) y certificados
  S->>S: instala certificados en SMARTPOT_CERTS_DIR
  S->>G: docker compose pull
  S->>S: up -d --wait
  S->>S: borra .env
  D->>S: GET /health público
  Q-->>R: resultado del despliegue central
```

Only this repository deploys. The [`deploy.yml`](../../.github/workflows/deploy.yml) workflow runs:

- When a service (SmartPot-API, -Web, -AI, -Trainer, -MCP, -Broker, -DB, -Cache, -Mail, or -DataGenerator) publishes its image from `main`: its `deploy.yml` calls [`request-deploy.yml`](../../.github/workflows/request-deploy.yml), which triggers the central deployment, shows the link, and waits for the result.
- On any change under `docker/production` in this repository.
- Manually, from **Actions -> Deploy to Production -> Run workflow**.

**Queue without duplicates.** `deploy.yml` uses `concurrency: smartpot-production` without canceling the running job. While one deployment runs, the next one waits. If several requests arrive at once, only the most recent one remains queued. Intermediate requests are canceled because every deployment pulls all images and already includes their changes. A service whose request was replaced reports it as a warning, not an error. On the server, `flock` is a second barrier in case something runs outside GitHub.

Each run deploys the full platform: it pulls the images **from GHCR** (`ghcr.io/smartpottech/smartpot-*`, public) and recreates only the containers whose image or configuration changed. Docker Hub (`sebastian190030/<component>-smartpot`) remains a distribution mirror. If a secret is missing, the deployment is skipped with a warning instead of failing.

### Secrets

**In `SmartPotTech/.github`** (the only repository that connects to the server):

| Secret               | Example                                    | Description                              |
| -------------------- | ------------------------------------------ | ---------------------------------------- |
| `SERVER_HOST`        | `203.0.113.10`                             | Server IP or domain                      |
| `SERVER_PORT`        | `22`                                       | SSH port                                 |
| `SERVER_USER`        | `deploy`                                   | SSH user (`root` or passwordless `sudo`) |
| `SERVER_KEY`         | `-----BEGIN ... PRIVATE KEY-----`          | Complete SSH private key                 |
| `SERVER_KNOWN_HOSTS` | `[203.0.113.10]:22 ssh-ed25519 AAAA...`    | Server fingerprint                       |
| `DEPLOY_PATH`        | `/srv/smartpot/production`                 | Deployment directory                     |
| `ENV_FILE`           | Contents of [`.env.example`](.env.example) | Complete production `.env`               |
| `MQTT_CA_CERT`       | `-----BEGIN CERTIFICATE-----`              | SmartPot CA `ca.crt` (public)            |
| `MQTT_SERVER_CERT`   | `-----BEGIN CERTIFICATE-----`              | `server.crt` for `mqtt.smartpot.app`     |
| `MQTT_SERVER_KEY`    | `-----BEGIN PRIVATE KEY-----`              | Broker `server.key`                      |

`ENV_FILE` must define `SMARTPOT_READER_PASSWORD`. The database creates `smartpot_reader` with that password and the trainer uses it in its read-only URL. `DATABASE_URL` remains the writable URL for the API.

**In each service** (the repositories with images):

| Secret                                | Description                                                                                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEPLOY_DISPATCH_TOKEN`               | *Fine-grained* token with access only to `SmartPotTech/.github` and the **Actions: Read and write** permission. Without it, the service publishes the image but does not request deployment |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Optional: Docker Hub username and access token to publish there too (`<user>/<component>-smartpot`)                                                                                         |

---

### Operations

Containers keep their configuration even if the `.env` is deleted. Secrets are mandatory in `compose.yaml`, so without `.env` any `docker compose` command stops instead of recreating containers without secrets. To inspect, use `docker` directly. To change configuration, edit `ENV_FILE` and run **Deploy to Production**.

```bash
docker ps --filter name=smartpot
docker logs -f smartpot-api
docker logs -f smartpot-broker
docker exec -it smartpot-db psql -U smartpot -d smartpot
```

> [!CAUTION]
> `docker compose down -v` deletes the `db_data`, `broker_data`, and `ai_data` volumes: users, crops, readings, MQTT accounts, and models learned by the AI service.

---

### Backups

[`backup_smartpot.sh`](backup_smartpot.sh) creates three artifacts per run in `backups/`:

- `smartpot-<UTC timestamp>.dump`: custom-format `pg_dump -Fc` archive. It is already compressed and is not gzipped.
- `smartpot-<UTC timestamp>.manifest`: database name, container, UTC timestamp, TOC entries, `readings_count`, readings range, and database size.
- `smartpot-<UTC timestamp>.dump.sha256`: SHA-256 checksum sidecar.

The script uses `set -Eeuo pipefail`, `umask 077`, and an exclusive `flock`. It reads credentials from the container, uses `SMARTPOT_DB_CONTAINER` (default `smartpot-db`), writes `pg_dump -Fc --lock-wait-timeout=30s` to a `.partial` file, validates the archive TOC with `pg_restore --list`, writes the manifest and checksum, and publishes the files with an atomic rename. Retention is controlled by `SMARTPOT_BACKUP_DAYS` (default 14) and removes each expired dump with its manifest and checksum. `SMARTPOT_BACKUP_DIR` changes the destination directory.

Exact backup command:

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production/backup_smartpot.sh -o backup_smartpot.sh
chmod 700 backup_smartpot.sh
./backup_smartpot.sh
```

Exact restore command:

```bash
./backup_smartpot.sh --restore backups/smartpot-<timestamp>.dump
```

> [!WARNING]
> `--restore` destroys the current database. The script runs `dropdb --force --if-exists` and `createdb` before restoring. Stop all writers and take a fresh backup first.

The restore path verifies the checksum, validates the archive TOC, drops and recreates the database, runs `CREATE EXTENSION IF NOT EXISTS timescaledb`, calls `timescaledb_pre_restore()`, runs `pg_restore --exit-on-error --no-owner`, calls `timescaledb_post_restore()`, refreshes each continuous aggregate with one `CALL` per transaction through `\gexec`, runs `ANALYZE`, and compares the readings count with the manifest.

Do not use `pg_restore --clean` with TimescaleDB continuous aggregates. It cannot rebuild the aggregates and their policies safely over an existing database. This archive is custom format and is not gzipped, so restore only through `--restore`.

MQTT accounts need no backup: when a device connects, the API handles the authentication and ACL request at `/internal/mqtt/authn` from the rows in PostgreSQL.

---

### Nginx and HTTPS

The [`nginx/`](nginx) directory has one file per domain for `/etc/nginx/sites-available/`. All of them use the Let's Encrypt `smartpot.app` certificate, which covers the active domains:

```bash
certbot certonly --nginx --cert-name smartpot.app \
  -d smartpot.app -d www.smartpot.app -d api.smartpot.app -d mcp.smartpot.app -d mqtt.smartpot.app -d mail.smartpot.app
for site in smartpot.app api.smartpot.app mcp.smartpot.app mqtt.smartpot.app mail.smartpot.app; do
  cp nginx/$site.conf /etc/nginx/sites-available/$site
  ln -sf /etc/nginx/sites-available/$site /etc/nginx/sites-enabled/$site
done
nginx -t && systemctl reload nginx
```

`mqtt.smartpot.app` publishes `/mqtt` (WebSocket to `127.0.0.1:9001`). Physical devices do not go through nginx. They connect directly to port 8883 with the SmartPot CA.

Firewall: besides SSH, 80, and 443, only `8883/tcp` is required.

```bash
ufw allow 8883/tcp comment 'MQTT TLS SmartPot'
```

---

### Verification

```bash
curl -fsS https://api.smartpot.app/health
curl -fsS https://mcp.smartpot.app/health
curl -fsS https://api.smartpot.app/api/v1/crop-profiles | head -c 200
curl -s -o /dev/null -w "%{http_code}\n" https://api.smartpot.app/api/v1/crops
curl -sI https://smartpot.app/ | grep -i content-security-policy
openssl s_client -connect mqtt.smartpot.app:8883 -CAfile ca.crt -brief </dev/null
```

| Check                             | Expected result                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| `/health`                         | `{"status":"UP","database":"UP","broker":"UP","cache":"UP","ai":"UP","simulator":"UP"}`  |
| `/health` (MCP)                   | `{"status":"UP","service":"smartpot-mcp","api":"UP"}`                                    |
| `/api/v1/crop-profiles`           | Agronomic profiles for the six species                                                   |
| `/api/v1/crops` without a session | `401`                                                                                    |
| PWA                               | `200` with `Content-Security-Policy`, `X-Frame-Options`, and `Strict-Transport-Security` |
| EMQX broker                       | `Verification: OK` and `TLSv1.3` protocol (minimum 1.2)                                  |

---

<a id="español"></a>

## Español

Esta guía describe el entorno **de producción** de SmartPot: un servidor propio detrás de Nginx con HTTPS, el broker MQTT EMQX expuesto por TLS para los dispositivos de los cultivos reales y actualizado automáticamente por GitHub Actions cada vez que cambia `main` en cualquiera de los servicios.

| Dominio                        | Servicio                                                    |
| ------------------------------ | ----------------------------------------------------------- |
| `smartpot.app` (y `www`)       | PWA en SolidJS 1.9 y Bun                                    |
| `api.smartpot.app`             | API REST en Go (Echo) y documentación en `/docs`            |
| `mcp.smartpot.app`             | Servidor Model Context Protocol (FastMCP) para clientes MCP |
| `mqtt.smartpot.app:8883`       | MQTT sobre TLS (1.2 o superior) para los dispositivos       |
| `wss://mqtt.smartpot.app/mqtt` | MQTT sobre WebSocket seguro (EMQX)                          |
| `mail.smartpot.app`            | Bandeja de Mailpit (con usuario y contraseña)               |

---

### Requisitos previos

- **Docker Engine** y **Docker Compose v2.20 o superior**: [instrucciones de instalación](https://docs.docker.com/engine/install/)
- Un usuario SSH con acceso a Docker (`root` o con `sudo` sin contraseña).
- **Nginx** y **Certbot** para publicar los dominios con HTTPS.
- Registros `A` de `smartpot.app`, `api`, `mcp`, `mqtt` y `mail` apuntando al servidor, y `www` como `CNAME` de `smartpot.app`.
- El puerto **8883/tcp** abierto en el firewall para los dispositivos físicos.

---

### Arquitectura del entorno

```mermaid
flowchart LR
  B[Navegador] -->|HTTPS 443| N[Nginx + Let's Encrypt]
  M[ESP32 de un cultivo real] -->|MQTT TLS 8883| K[broker-smartpot: EMQX]
  N -->|127.0.0.1:5173| W[web-smartpot: SolidJS]
  N -->|127.0.0.1:8091| A[api-smartpot: Go]
  N -->|127.0.0.1:8092| P[mcp-smartpot: FastMCP]
  N -->|127.0.0.1:9001 wss| K
  N -->|127.0.0.1:8025| E[mail-smartpot: Mailpit]
  A -->|red interna| D[(db-smartpot: TimescaleDB)]
  A -->|red interna o socket| C[(cache-smartpot: Valkey)]
  A -->|gRPC / REST interno| I[ai-smartpot: Rust]
  D -.->|ADBC lectura continua| R[trainer-smartpot: Python]
  R -.->|modelos JSON firmados| I
  A -->|red interna| V[simulator-smartpot: Rust]
  V -->|MQTT interno| K
  V -.->|clima| O[Open-Meteo]
  A <-->|MQTT interno| K
  K -.->|POST /internal/mqtt/authn| A
  A -->|SMTP 1025 interno| E
  P -->|REST + spt_... token| A
  A -.->|alertas| T[Telegram Bot API]
  T -.->|webhook firmado| N
```

| Servicio                        | Red                                     | Puerto en el host                | Variables que recibe                                                                                                                                  |
| ------------------------------- | --------------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `db-smartpot` (perfil `db`)     | `internal`                              | Ninguno                          | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SMARTPOT_DB_USERNAME`, `SMARTPOT_DB_PASSWORD`, `SMARTPOT_READER_PASSWORD`, `SMARTPOT_SEED_DEMO` |
| `cache-smartpot`                | `internal`                              | Ninguno                          | `VALKEY_PASSWORD`, `VALKEY_SOCKET`                                                                                                                    |
| `mail-smartpot` (perfil `mail`) | `internal` + `public`                   | `127.0.0.1:8025`                 | `MAIL_*`, `MAILPIT_UI_*`                                                                                                                              |
| `broker-smartpot`               | `internal` + `public`                   | `0.0.0.0:8883`, `127.0.0.1:9001` | `MQTT_ADMIN_*`, certificados en `SMARTPOT_CERTS_DIR`, `MQTT_AUTHN_TOKEN`                                                                              |
| `ai-smartpot`                   | `internal`                              | Ninguno                          | `SMARTPOT_AI_TOKEN`, `TRUSTED_MODEL_PUBLIC_KEY_HEX`; volumen `ai_data`                                                                                |
| `trainer-smartpot`              | `internal`                              | Ninguno                          | `DATABASE_URL` (rol de solo lectura), `SMARTPOT_TRAINER_TOKEN`, `MODEL_SIGNING_KEY_PATH`, `SMARTPOT_AI_TOKEN`, `SMARTPOT_AI_URL`                      |
| `api-smartpot`                  | `internal` + `public`                   | `127.0.0.1:8091`                 | `DATABASE_URL` (rol escritor), `CACHE_URL`, JWT, AES, conexiones internas, `SIMULATOR_TOKEN`, `TELEGRAM_*`                                            |
| `web-smartpot`                  | `public`                                | `127.0.0.1:5173`                 | `PUBLIC_API_URL`                                                                                                                                      |
| `mcp-smartpot`                  | `internal` + `public`                   | `127.0.0.1:8092`                 | `PUBLIC_API_URL`, `MCP_ALLOWED_ORIGINS`                                                                                                               |
| `simulator-smartpot`            | `internal` + `public` (salida al clima) | Ninguno                          | `SIMULATOR_*`, `MQTT_*`                                                                                                                               |

Toda la configuración vive en un único `.env`, pero `compose.yaml` entrega a cada contenedor solo sus variables: la PWA no ve el secreto JWT y el servicio de IA solo conoce su token. La red `internal` no tiene salida a internet: PostgreSQL, Valkey y la IA no son alcanzables desde fuera. El simulador de cultivos virtuales solo usa `public` para consultar el clima y no publica puertos. Su API de control la usa únicamente la API de SmartPot, con token.

**Custodia de la firma de modelos.** La IA monta `ai_data:/data:ro` y solo lee `{SPECIES}_inference.json` y `{SPECIES}_manifest.json`. El Trainer escribe los modelos en `ai_data` y guarda la clave privada Ed25519 en el volumen separado `trainer_keys`, montado en `/data/keys` (modo `0600`), nunca legible por la IA. Define `MODEL_SIGNING_KEY_PATH=/data/keys/ed25519_private.pem` y `TRUSTED_MODEL_PUBLIC_KEY_HEX=<hex de 32 bytes>` para que la IA autentique cada paquete aprendido; sin el ancla de confianza solo comprueba el hash BLAKE2b. El servidor MCP valida cada token `spt_` contra la API y cachea el veredicto 30 segundos (`MCP_TOKEN_CACHE_SECONDS`), incluido `tools/list`.

### Roles de base de datos

Producción separa los roles de base de datos. La API se conecta con el `DATABASE_URL` escribible y el rol `smartpot`. El entrenador se conecta con una URL construida con `smartpot_reader` y `SMARTPOT_READER_PASSWORD`, así nunca puede escribir con el rol de la API. Desarrollo usa la misma separación. Kubernetes monta la clave `TRAINER_DATABASE_URL` del secreto como `DATABASE_URL` del entrenador, mientras la API conserva `DATABASE_URL`.

El rol de lectura puede leer `readings`, la vista `trainer_readings` con `security_barrier` y solo `id`, `type` y `kind` de `crops`. No tiene acceso a usuarios, credenciales de dispositivo ni tokens.

### Endurecimiento aplicado

| Medida                                                                  | Dónde                                      |
| ----------------------------------------------------------------------- | ------------------------------------------ |
| Sistema de archivos de solo lectura con `tmpfs` para lo temporal        | Todos los servicios                        |
| Sin capacidades de Linux (`cap_drop: ALL`) y `no-new-privileges`        | Todos los servicios                        |
| Usuarios sin privilegios en todas las imágenes                          | Imágenes de producción                     |
| Límites de CPU y memoria, `ulimits` y rotación de logs (10 MB x 3)      | Todos los servicios                        |
| Solo el broker escucha fuera de `127.0.0.1`, y solo por TLS             | `broker-smartpot` (EMQX)                   |
| Cada cultivo tiene credenciales únicas y ACL acotada por HTTP en la API | Delegación authn de EMQX en `SmartPot-API` |
| Healthchecks y arranque ordenado (`depends_on: service_healthy`)        | Todos los servicios                        |
| `.env` y certificados solo durante el despliegue                        | Workflow de despliegue                     |
| Imágenes públicas firmadas en GHCR con SBOM y procedencia               | GHCR                                       |

---

### Despliegue automático (GitHub Actions)

```mermaid
sequenceDiagram
  participant R as Repo de un servicio
  participant G as GHCR y Docker Hub
  participant Q as request-deploy.yml
  participant D as deploy.yml (.github)
  participant S as Servidor
  R->>G: packaging.yml publica la imagen
  R->>Q: deploy.yml del repo pide el despliegue
  Q->>D: workflow_dispatch (origen, commit, id de solicitud)
  Note over D: concurrency smartpot-production: uno en curso y uno en espera
  D->>D: genera .env desde ENV_FILE, valida secretos y certificados
  D->>S: SSH: compose.yaml, .env (600) y certificados
  S->>S: instala certificados en SMARTPOT_CERTS_DIR
  S->>G: docker compose pull
  S->>S: up -d --wait
  S->>S: borra .env
  D->>S: GET /health público
  Q-->>R: resultado del despliegue central
```

Solo este repositorio despliega. El workflow [`deploy.yml`](../../.github/workflows/deploy.yml) se ejecuta:

- Cuando un servicio (SmartPot-API, -Web, -AI, -Trainer, -MCP, -Broker, -DB, -Cache, -Mail o -DataGenerator) publica su imagen desde `main`: su `deploy.yml` llama a [`request-deploy.yml`](../../.github/workflows/request-deploy.yml), que dispara el despliegue central, muestra el enlace y espera el resultado.
- Con cualquier cambio en `docker/production` de este repositorio.
- A mano, desde **Actions -> Deploy to Production -> Run workflow**.

**Cola sin duplicados.** `deploy.yml` usa `concurrency: smartpot-production` sin cancelar el que está en curso. Mientras un despliegue corre, el siguiente espera. Si llegan varios pedidos a la vez, solo queda en espera el más reciente. Los intermedios se cancelan porque cada despliegue descarga todas las imágenes y ya incluye sus cambios. El servicio cuya solicitud fue reemplazada lo informa como aviso, no como error. En el servidor, `flock` es una segunda barrera por si algo corre por fuera de GitHub.

Cada ejecución despliega la plataforma completa: descarga las imágenes **desde GHCR** (`ghcr.io/smartpottech/smartpot-*`, públicas) y recrea solo los contenedores cuya imagen o configuración cambió. Docker Hub (`sebastian190030/<componente>-smartpot`) queda como réplica de distribución. Si falta algún secret, el despliegue se omite con un aviso en lugar de fallar.

### Secretos

**En `SmartPotTech/.github`** (el único que se conecta al servidor):

| Secret               | Ejemplo                                     | Descripción                                      |
| -------------------- | ------------------------------------------- | ------------------------------------------------ |
| `SERVER_HOST`        | `203.0.113.10`                              | IP o dominio del servidor                        |
| `SERVER_PORT`        | `22`                                        | Puerto SSH                                       |
| `SERVER_USER`        | `deploy`                                    | Usuario SSH (`root` o con `sudo` sin contraseña) |
| `SERVER_KEY`         | `-----BEGIN ... PRIVATE KEY-----`           | Llave privada SSH completa                       |
| `SERVER_KNOWN_HOSTS` | `[203.0.113.10]:22 ssh-ed25519 AAAA...`     | Huella del servidor                              |
| `DEPLOY_PATH`        | `/srv/smartpot/production`                  | Carpeta de despliegue                            |
| `ENV_FILE`           | Contenido de [`.env.example`](.env.example) | `.env` completo de producción                    |
| `MQTT_CA_CERT`       | `-----BEGIN CERTIFICATE-----`               | `ca.crt` de la CA de SmartPot (público)          |
| `MQTT_SERVER_CERT`   | `-----BEGIN CERTIFICATE-----`               | `server.crt` para `mqtt.smartpot.app`            |
| `MQTT_SERVER_KEY`    | `-----BEGIN PRIVATE KEY-----`               | `server.key` del broker                          |

`ENV_FILE` debe definir `SMARTPOT_READER_PASSWORD`. La base crea `smartpot_reader` con esa contraseña y el entrenador la usa en su URL de solo lectura. `DATABASE_URL` sigue siendo la URL escribible de la API.

**En cada servicio** (los repositorios con imagen):

| Secret                                | Descripción                                                                                                                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DEPLOY_DISPATCH_TOKEN`               | Token *fine-grained* con acceso solo a `SmartPotTech/.github` y permiso **Actions: Read and write**. Sin él, el servicio publica la imagen pero no pide el despliegue |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Opcionales: usuario y token de acceso de Docker Hub para publicar también ahí (`<usuario>/<componente>-smartpot`)                                                     |

---

### Operación

Los contenedores conservan su configuración aunque el `.env` se borre. Los secretos son obligatorios en `compose.yaml`, así que sin `.env` cualquier comando de `docker compose` se detiene en lugar de recrear los contenedores sin secretos. Para inspeccionar, usa `docker` directamente. Para cambiar la configuración, edita `ENV_FILE` y ejecuta **Deploy to Production**.

```bash
docker ps --filter name=smartpot
docker logs -f smartpot-api
docker logs -f smartpot-broker
docker exec -it smartpot-db psql -U smartpot -d smartpot
```

> [!CAUTION]
> `docker compose down -v` borra los volúmenes `db_data`, `broker_data` y `ai_data`: usuarios, cultivos, lecturas, cuentas MQTT y modelos aprendidos por la IA.

---

### Respaldos

[`backup_smartpot.sh`](backup_smartpot.sh) genera tres artefactos por ejecución en `backups/`:

- `smartpot-<fecha UTC>.dump`: archivo de formato personalizado `pg_dump -Fc`. Ya está comprimido y no se envuelve en gzip.
- `smartpot-<fecha UTC>.manifest`: nombre de la base, contenedor, fecha UTC, entradas del TOC, `readings_count`, rango de lecturas y tamaño de la base.
- `smartpot-<fecha UTC>.dump.sha256`: archivo lateral con el checksum SHA-256.

El script usa `set -Eeuo pipefail`, `umask 077` y un `flock` exclusivo. Lee las credenciales del contenedor y usa `SMARTPOT_DB_CONTAINER` (por defecto `smartpot-db`). Escribe `pg_dump -Fc --lock-wait-timeout=30s` en un archivo `.partial`. Valida el TOC con `pg_restore --list`. Crea el manifiesto y el checksum. Publica los archivos con un renombrado atómico. La retención se controla con `SMARTPOT_BACKUP_DAYS` (por defecto 14) y borra cada respaldo vencido con su manifiesto y su checksum. `SMARTPOT_BACKUP_DIR` cambia el directorio de destino.

Comando exacto de respaldo:

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production/backup_smartpot.sh -o backup_smartpot.sh
chmod 700 backup_smartpot.sh
./backup_smartpot.sh
```

Comando exacto de restauración:

```bash
./backup_smartpot.sh --restore backups/smartpot-<fecha>.dump
```

> [!WARNING]
> `--restore` destruye la base actual. El script ejecuta `dropdb --force --if-exists` y `createdb` antes de restaurar. Detén a todos los escritores y toma un respaldo nuevo primero.

La restauración verifica el checksum. Valida el TOC del archivo. Borra y recrea la base. Ejecuta `CREATE EXTENSION IF NOT EXISTS timescaledb` y llama a `timescaledb_pre_restore()`. Ejecuta `pg_restore --exit-on-error --no-owner` y llama a `timescaledb_post_restore()`. Refresca cada agregado continuo con un `CALL` por transacción mediante `\gexec`. Ejecuta `ANALYZE` y compara el conteo de lecturas con el manifiesto.

No uses `pg_restore --clean` con agregados continuos de TimescaleDB. No puede reconstruir los agregados ni sus políticas de forma segura sobre una base existente. Este archivo es de formato personalizado y no está comprimido con gzip, así que restaura solo con `--restore`.

Las cuentas MQTT no necesitan respaldo: al conectarse, la API atiende la solicitud de autenticación y ACL en `/internal/mqtt/authn` a partir de los registros en PostgreSQL.

---

### Nginx y HTTPS

La carpeta [`nginx/`](nginx) tiene un archivo por dominio para `/etc/nginx/sites-available/`. Todos usan el certificado `smartpot.app` de Let's Encrypt, que cubre los dominios activos:

```bash
certbot certonly --nginx --cert-name smartpot.app \
  -d smartpot.app -d www.smartpot.app -d api.smartpot.app -d mcp.smartpot.app -d mqtt.smartpot.app -d mail.smartpot.app
for site in smartpot.app api.smartpot.app mcp.smartpot.app mqtt.smartpot.app mail.smartpot.app; do
  cp nginx/$site.conf /etc/nginx/sites-available/$site
  ln -sf /etc/nginx/sites-available/$site /etc/nginx/sites-enabled/$site
done
nginx -t && systemctl reload nginx
```

`mqtt.smartpot.app` publica `/mqtt` (WebSocket hacia `127.0.0.1:9001`). Los dispositivos físicos no pasan por nginx. Se conectan directo al puerto 8883 con la CA de SmartPot.

Firewall: además de SSH, 80 y 443, solo hace falta `8883/tcp`.

```bash
ufw allow 8883/tcp comment 'MQTT TLS SmartPot'
```

---

### Verificación

```bash
curl -fsS https://api.smartpot.app/health
curl -fsS https://mcp.smartpot.app/health
curl -fsS https://api.smartpot.app/api/v1/crop-profiles | head -c 200
curl -s -o /dev/null -w "%{http_code}\n" https://api.smartpot.app/api/v1/crops
curl -sI https://smartpot.app/ | grep -i content-security-policy
openssl s_client -connect mqtt.smartpot.app:8883 -CAfile ca.crt -brief </dev/null
```

| Comprobación               | Resultado esperado                                                                      |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `/health`                  | `{"status":"UP","database":"UP","broker":"UP","cache":"UP","ai":"UP","simulator":"UP"}` |
| `/health` (MCP)            | `{"status":"UP","service":"smartpot-mcp","api":"UP"}`                                   |
| `/api/v1/crop-profiles`    | Perfiles agronómicos de las seis especies                                               |
| `/api/v1/crops` sin sesión | `401`                                                                                   |
| PWA                        | `200` con `Content-Security-Policy`, `X-Frame-Options` y `Strict-Transport-Security`    |
| Broker EMQX                | `Verification: OK` y protocolo `TLSv1.3` (mínimo 1.2)                                   |
