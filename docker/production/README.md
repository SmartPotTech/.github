# **Despliegue de SmartPot en Producción con Docker**

Esta guía describe el entorno **de producción** de SmartPot (Stack B): un servidor propio detrás de Nginx con HTTPS, con el broker
MQTT EMQX expuesto por TLS para los dispositivos de los cultivos reales y actualizado automáticamente por GitHub Actions cada
vez que cambia `main` en cualquiera de los servicios.

| Dominio | Servicio |
|---|---|
| `smartpot.app` (y `www`) | PWA en SolidJS 1.9 y Bun |
| `api.smartpot.app` | API REST en Go (Echo) y documentación en `/docs` |
| `mcp.smartpot.app` | Servidor Model Context Protocol (FastMCP) para asistentes de IA |
| `mqtt.smartpot.app:8883` | MQTT sobre TLS (1.2 o superior) para los dispositivos |
| `wss://mqtt.smartpot.app/mqtt` | MQTT sobre WebSocket seguro (EMQX) |
| `mail.smartpot.app` | Bandeja de Mailpit (con usuario y contraseña) |

---

## **Requisitos Previos**

* **Docker Engine** y **Docker Compose v2.20 o superior**: [Instrucciones de instalación](https://docs.docker.com/engine/install/)
* Un usuario SSH con acceso a Docker (`root` o con `sudo` sin contraseña).
* **Nginx** y **Certbot** para publicar los dominios con HTTPS.
* Registros `A` de `smartpot.app`, `api`, `mcp`, `mqtt` y `mail` apuntando al servidor, y `www` como `CNAME` de `smartpot.app`.
* El puerto **8883/tcp** abierto en el firewall para los dispositivos físicos.

---

## **Arquitectura del Entorno**

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

| Servicio | Red | Puerto en el host | Variables que recibe |
|---|---|---|---|
| `db-smartpot` (perfil `db`) | `internal` | Ninguno | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| `cache-smartpot` | `internal` | Ninguno | `VALKEY_PASSWORD`, `VALKEY_SOCKET` |
| `mail-smartpot` (perfil `mail`) | `internal` + `public` | `127.0.0.1:8025` | `MAIL_*`, `MAILPIT_UI_*` |
| `broker-smartpot` | `internal` + `public` | `0.0.0.0:8883`, `127.0.0.1:9001` | `MQTT_ADMIN_*`, certificados en `SMARTPOT_CERTS_DIR`, `MQTT_AUTHN_TOKEN` |
| `ai-smartpot` | `internal` | Ninguno | `SMARTPOT_AI_TOKEN`, `TRUSTED_MODEL_PUBLIC_KEY_HEX`; volumen `ai_data` |
| `trainer-smartpot` | `internal` | Ninguno | `DATABASE_URL`, `SMARTPOT_TRAINER_TOKEN`, `MODEL_SIGNING_KEY_PATH` |
| `api-smartpot` | `internal` + `public` | `127.0.0.1:8091` | `DATABASE_URL`, `CACHE_URL`, JWT, AES, conexiones internas, `SIMULATOR_TOKEN`, `TELEGRAM_*` |
| `web-smartpot` | `public` | `127.0.0.1:5173` | `PUBLIC_API_URL` |
| `mcp-smartpot` | `internal` + `public` | `127.0.0.1:8092` | `PUBLIC_API_URL`, `MCP_ALLOWED_ORIGINS` |
| `simulator-smartpot` | `internal` + `public` (salida al clima) | Ninguno | `SIMULATOR_*`, `MQTT_*` |

Toda la configuración vive en un único `.env`, pero `compose.yaml` entrega a cada contenedor solo sus variables: la PWA no ve el secreto JWT y el servicio de IA solo conoce su token. La red `internal` no tiene salida a internet: PostgreSQL, Valkey y la IA no son alcanzables desde fuera. El simulador de cultivos virtuales solo usa `public` para consultar el clima y no publica puertos; su API de control la usa únicamente la API de SmartPot, con token.

### Endurecimiento aplicado

| Medida | Dónde |
|---|---|
| Sistema de archivos de solo lectura con `tmpfs` para lo temporal | Todos los servicios |
| Sin capacidades de Linux (`cap_drop: ALL`) y `no-new-privileges` | Todos los servicios |
| Usuarios sin privilegios en todas las imágenes | Imágenes de producción |
| Límites de CPU y memoria, `ulimits` y rotación de logs (10 MB × 3) | Todos los servicios |
| Solo el broker escucha fuera de `127.0.0.1`, y solo por TLS | `broker-smartpot` (EMQX) |
| Cada cultivo tiene credenciales únicas y ACL acotada por HTTP en la API | Delegación authn de EMQX en `SmartPot-API` |
| Healthchecks y arranque ordenado (`depends_on: service_healthy`) | Todos los servicios |
| `.env` y certificados solo durante el despliegue | Workflow de despliegue |
| Imágenes públicas firmadas en GHCR con SBOM y procedencia | GHCR |

---

## **Despliegue Automático (GitHub Actions)**

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

* Cuando un servicio (SmartPot-API, -Web, -AI, -Trainer, -MCP, -Broker, -DB, -Cache, -Mail o -DataGenerator) publica su imagen desde `main`: su `deploy.yml` llama a [`request-deploy.yml`](../../.github/workflows/request-deploy.yml), que dispara el despliegue central, muestra el enlace y espera el resultado.
* Con cualquier cambio en `docker/production` de este repositorio.
* A mano, desde **Actions → Deploy to Production → Run workflow**.

**Cola sin duplicados.** `deploy.yml` usa `concurrency: smartpot-production` sin cancelar el que está en curso: mientras un despliegue corre, el siguiente espera, y si llegan varios pedidos a la vez solo queda en espera el más reciente; los intermedios se cancelan porque cada despliegue descarga todas las imágenes y ya incluye sus cambios. El servicio cuya solicitud fue reemplazada lo informa como aviso, no como error. En el servidor, `flock` es una segunda barrera por si algo corre por fuera de GitHub.

Cada ejecución despliega la plataforma completa: descarga las imágenes **desde GHCR** (`ghcr.io/smartpottech/smartpot-*`, públicas) y recrea solo los contenedores cuya imagen o configuración cambió. Docker Hub (`sebastian190030/<componente>-smartpot`) queda como réplica de distribución. Si falta algún secret, el despliegue se omite con un aviso en lugar de fallar.

### Secrets

**En `SmartPotTech/.github`** (el único que se conecta al servidor):

| Secret | Ejemplo | Descripción |
|---|---|---|
| `SERVER_HOST` | `203.0.113.10` | IP o dominio del servidor |
| `SERVER_PORT` | `22` | Puerto SSH |
| `SERVER_USER` | `deploy` | Usuario SSH (`root` o con `sudo` sin contraseña) |
| `SERVER_KEY` | `-----BEGIN … PRIVATE KEY-----` | Llave privada SSH completa |
| `SERVER_KNOWN_HOSTS` | `[203.0.113.10]:22 ssh-ed25519 AAAA…` | Huella del servidor |
| `DEPLOY_PATH` | `/srv/smartpot/production` | Carpeta de despliegue |
| `ENV_FILE` | Contenido de [`.env.example`](.env.example) | `.env` completo de producción |
| `MQTT_CA_CERT` | `-----BEGIN CERTIFICATE-----` | `ca.crt` de la CA de SmartPot (público) |
| `MQTT_SERVER_CERT` | `-----BEGIN CERTIFICATE-----` | `server.crt` para `mqtt.smartpot.app` |
| `MQTT_SERVER_KEY` | `-----BEGIN PRIVATE KEY-----` | `server.key` del broker |

**En cada servicio** (los repositorios con imagen):

| Secret | Descripción |
|---|---|
| `DEPLOY_DISPATCH_TOKEN` | Token *fine-grained* con acceso solo a `SmartPotTech/.github` y permiso **Actions: Read and write**. Sin él, el servicio publica la imagen pero no pide el despliegue |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Opcionales: usuario y token de acceso de Docker Hub para publicar también ahí (`<usuario>/<componente>-smartpot`) |

---

## **Operación**

Los contenedores conservan su configuración aunque el `.env` se borre. Los secretos son obligatorios en `compose.yaml`, así que sin `.env` cualquier comando de `docker compose` se detiene en lugar de recrear los contenedores sin secretos. Para inspeccionar usa `docker` directamente y, para cambiar la configuración, edita `ENV_FILE` y ejecuta **Deploy to Production**.

```bash
docker ps --filter name=smartpot
docker logs -f smartpot-api
docker logs -f smartpot-broker
docker exec -it smartpot-db psql -U smartpot -d smartpot
```

> [!CAUTION]
> `docker compose down -v` borra los volúmenes `db_data`, `broker_data` y `ai_data`: usuarios, cultivos, lecturas, cuentas MQTT y modelos aprendidos por la IA.

---

## **Respaldos**

[`backup_smartpot.sh`](backup_smartpot.sh) genera `backups/smartpot-<fecha>.dump.gz` (`pg_dump` comprimido de PostgreSQL/TimescaleDB, permisos `600`) y elimina los que superan 14 días (`SMARTPOT_BACKUP_DAYS`). Usa las credenciales del propio contenedor.

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production/backup_smartpot.sh -o backup_smartpot.sh
chmod 700 backup_smartpot.sh
./backup_smartpot.sh
```

Restaurar un respaldo:

```bash
docker exec -i smartpot-db sh -c 'gunzip -c | pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < backups/smartpot-<fecha>.dump.gz
```

Las cuentas MQTT no necesitan respaldo: al conectarse, la API atiende la solicitud de autenticación y ACL en `/internal/mqtt/authn` a partir de los registros en PostgreSQL.

---

## **Nginx y HTTPS**

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

`mqtt.smartpot.app` publica `/mqtt` (WebSocket hacia `127.0.0.1:9001`); los dispositivos físicos no pasan por nginx, se conectan directo al puerto 8883 con la CA de SmartPot.

Firewall: además de SSH, 80 y 443, solo hace falta `8883/tcp`.

```bash
ufw allow 8883/tcp comment 'MQTT TLS SmartPot'
```

---

## **Verificación**

```bash
curl -fsS https://api.smartpot.app/health
curl -fsS https://mcp.smartpot.app/health
curl -fsS https://api.smartpot.app/api/v1/crop-profiles | head -c 200
curl -s -o /dev/null -w "%{http_code}\n" https://api.smartpot.app/api/v1/crops
curl -sI https://smartpot.app/ | grep -i content-security-policy
openssl s_client -connect mqtt.smartpot.app:8883 -CAfile ca.crt -brief </dev/null
```

| Comprobación | Resultado esperado |
|---|---|
| `/health` | `{"status":"UP","database":"UP","broker":"UP","cache":"UP","ai":"UP","simulator":"UP"}` |
| `/health` (MCP) | `{"status":"UP","service":"smartpot-mcp","api":"UP"}` |
| `/api/v1/crop-profiles` | Perfiles agronómicos de las seis especies |
| `/api/v1/crops` sin sesión | `401` |
| PWA | `200` con `Content-Security-Policy`, `X-Frame-Options` y `Strict-Transport-Security` |
| Broker EMQX | `Verification: OK` y protocolo `TLSv1.3` (mínimo 1.2) |
