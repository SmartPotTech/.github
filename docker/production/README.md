# **Despliegue de SmartPot en Producción con Docker**

Esta guía describe el entorno **de producción** de SmartPot: un servidor propio detrás de Nginx con HTTPS, con el broker
MQTT expuesto por TLS para los dispositivos de los cultivos reales y actualizado automáticamente por GitHub Actions cada
vez que cambia `main` en cualquiera de los servicios.

| Dominio                        | Servicio                                              |
|--------------------------------|-------------------------------------------------------|
| `smartpot.app` (y `www`)       | PWA                                                   |
| `api.smartpot.app`             | API REST y documentación en `/docs`                   |
| `mqtt.smartpot.app:8883`       | MQTT sobre TLS (1.2 o superior) para los dispositivos |
| `wss://mqtt.smartpot.app/mqtt` | MQTT sobre WebSocket seguro                           |
| `mail.smartpot.app`            | Bandeja de Mailpit (con usuario y contraseña)         |

---

## **Requisitos Previos**

* **Docker Engine** y **Docker Compose v2.20 o superior
  **: [Instrucciones de instalación](https://docs.docker.com/engine/install/)
* Un usuario SSH con acceso a Docker (`root` o con `sudo` sin contraseña).
* **Nginx** y **Certbot** para publicar los dominios con HTTPS.
* Registros `A` de `smartpot.app`, `api`, `mqtt` y `mail` apuntando al servidor, y `www` como `CNAME` de `smartpot.app`.
* El puerto **8883/tcp** abierto en el firewall para los dispositivos.

---

## **Arquitectura del Entorno**

```mermaid
flowchart LR
  B[Navegador] -->|HTTPS 443| N[Nginx + Let's Encrypt]
  M[ESP32 de un cultivo real] -->|MQTT TLS 8883| K[broker-smartpot]
  N -->|127.0.0.1:5173| W[web-smartpot]
  N -->|127.0.0.1:8091| A[api-smartpot]
  N -->|127.0.0.1:9001 wss| K
  N -->|127.0.0.1:8025| E[mail-smartpot]
  A -->|red interna| D[(db-smartpot)]
  A -->|red interna| C[(cache-smartpot)]
  A -->|red interna| I[ai-smartpot]
  A -->|red interna| V[simulator-smartpot]
  V -->|MQTT 1883 interno| K
  V -.->|clima| O[Open-Meteo]
  A -->|MQTT 1883 interno| K
  A -->|SMTP 1025 interno| E
  A -.->|alertas| T[Telegram Bot API]
  T -.->|webhook firmado| N
```

| Servicio                        | Red                                                | Puerto en el host                | Variables que recibe                                                          |
|---------------------------------|----------------------------------------------------|----------------------------------|-------------------------------------------------------------------------------|
| `db-smartpot` (perfil `db`)     | `internal`                                         | Ninguno                          | `MONGO_ROOT_*`, `SMARTPOT_DB_*`, `SMARTPOT_SEED_DEMO`                         |
| `cache-smartpot`                | `internal`                                         | Ninguno                          | `REDIS_PASSWORD`                                                              |
| `mail-smartpot` (perfil `mail`) | `internal` + `public`                              | `127.0.0.1:8025`                 | `MAIL_*`, `MAILPIT_UI_*`                                                      |
| `broker-smartpot`               | `internal` + `public`                              | `0.0.0.0:8883`, `127.0.0.1:9001` | `MQTT_ADMIN_*`, certificados en `SMARTPOT_CERTS_DIR`                          |
| `ai-smartpot`                   | `internal`                                         | Ninguno                          | `SMARTPOT_AI_TOKEN`, `LEARNING_*`; volumen `ai_data` con lo aprendido         |
| `api-smartpot`                  | `internal` + `public`                              | `127.0.0.1:8091`                 | JWT, AES, conexiones internas, URLs públicas, `SIMULATOR_TOKEN`, `TELEGRAM_*` |
| `web-smartpot`                  | `public`                                           | `127.0.0.1:5173`                 | `PUBLIC_API_URL`                                                              |
| `simulator-smartpot`            | `internal` + `public` (solo salida, para el clima) | Ninguno                          | `SIMULATOR_*`                                                                 |

Toda la configuración vive en un único `.env`, pero `compose.yaml` entrega a cada contenedor solo sus variables: la PWA
no ve el secreto JWT y el servicio de IA solo conoce su token. La red `internal` no tiene salida a internet: MongoDB,
Redis y la IA no son alcanzables desde fuera. El simulador de cultivos virtuales solo usa `public` para consultar el
clima y no publica puertos; su API de control la usa únicamente la API de SmartPot, con token.

### Endurecimiento aplicado

| Medida                                                               | Dónde                           |
|----------------------------------------------------------------------|---------------------------------|
| Sistema de archivos de solo lectura con `tmpfs` para lo temporal     | Todos los servicios             |
| Sin capacidades de Linux (`cap_drop: ALL`) y `no-new-privileges`     | Todos los servicios             |
| Usuarios sin privilegios en todas las imágenes                       | Imágenes                        |
| Límites de CPU y memoria, `ulimits` y rotación de logs (10 MB × 3)   | Todos los servicios             |
| Solo el broker escucha fuera de `127.0.0.1`, y solo por TLS          | `broker-smartpot`               |
| Cada cultivo tiene su propia cuenta MQTT y solo accede a sus tópicos | Seguridad dinámica de Mosquitto |
| Healthchecks y arranque ordenado (`depends_on: service_healthy`)     | Todos los servicios             |
| `.env` y certificados solo durante el despliegue                     | Workflow de despliegue          |
| Imágenes con SBOM y atestación de procedencia                        | GHCR                            |

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
  S->>S: instala certificados en SMARTPOT_CERTS_DIR (usuario 1883)
  S->>G: docker compose pull
  S->>S: up -d --wait
  S->>S: migración de los esquemas de la base (idempotente)
  S->>S: borra .env
  D->>S: GET /health público
  Q-->>R: resultado del despliegue central
```

Solo este repositorio despliega. El workflow [`deploy.yml`](../../.github/workflows/deploy.yml) se ejecuta:

* Cuando un servicio (SmartPot-API, -Web, -AI, -Broker, -DB, -Cache, -Mail o -DataGenerator) publica su imagen desde
  `main`: su `deploy.yml` llama a [`request-deploy.yml`](../../.github/workflows/request-deploy.yml), que dispara el
  despliegue central, muestra el enlace y espera el resultado.
* Con cualquier cambio en `docker/production` de este repositorio.
* A mano, desde **Actions → Deploy to Production → Run workflow**.

**Cola sin duplicados.** `deploy.yml` usa `concurrency: smartpot-production` sin cancelar el que está en curso: mientras
un despliegue corre, el siguiente espera, y si llegan varios pedidos a la vez (por ejemplo, push simultáneos en tres
servicios) solo queda en espera el más reciente; los intermedios se cancelan porque cada despliegue descarga todas las
imágenes y ya incluye sus cambios. El servicio cuya solicitud fue reemplazada lo informa como aviso, no como error. En
el servidor, `flock` es una segunda barrera por si algo corre por fuera de GitHub.

Cada ejecución despliega la plataforma completa: descarga las imágenes **desde GHCR** (
`ghcr.io/smartpottech/smartpot-*`, públicas) y recrea solo los contenedores cuya imagen o configuración cambió. Docker
Hub (`sebastian190030/<componente>-smartpot`) queda como réplica de distribución para quien prefiera ese registro, por
ejemplo en la [demo](../demo/README.md). Si falta algún secret, el despliegue se omite con un aviso en lugar de fallar.

**Migración de la base.** Los scripts de inicio de MongoDB solo corren con el volumen vacío, así que después de levantar
los contenedores el despliegue aplica los esquemas de [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) a la
base existente con su migración (`/opt/smartpot/migrate.js`). Es idempotente: crea las colecciones que falten, pone o
actualiza cada validador y no toca los documentos. Si falla, el despliegue falla; si la imagen de la base es anterior y
no la trae, se omite con un aviso.

### Secrets

**En `SmartPotTech/.github`** (el único que se conecta al servidor):

| Secret               | Ejemplo                                     | Descripción                                      |
|----------------------|---------------------------------------------|--------------------------------------------------|
| `SERVER_HOST`        | `203.0.113.10`                              | IP o dominio del servidor                        |
| `SERVER_PORT`        | `22`                                        | Puerto SSH                                       |
| `SERVER_USER`        | `deploy`                                    | Usuario SSH (`root` o con `sudo` sin contraseña) |
| `SERVER_KEY`         | `-----BEGIN … PRIVATE KEY-----`             | Llave privada SSH completa                       |
| `SERVER_KNOWN_HOSTS` | `[203.0.113.10]:22 ssh-ed25519 AAAA…`       | Huella del servidor                              |
| `DEPLOY_PATH`        | `/srv/smartpot/production`                  | Carpeta de despliegue                            |
| `ENV_FILE`           | Contenido de [`.env.example`](.env.example) | `.env` completo de producción                    |
| `MQTT_CA_CERT`       | `-----BEGIN CERTIFICATE-----`               | `ca.crt` de la CA de SmartPot (público)          |
| `MQTT_SERVER_CERT`   | `-----BEGIN CERTIFICATE-----`               | `server.crt` para `mqtt.smartpot.app`            |
| `MQTT_SERVER_KEY`    | `-----BEGIN PRIVATE KEY-----`               | `server.key` del broker                          |

**En cada servicio** (los ocho repositorios con imagen):

| Secret                                | Descripción                                                                                                                                                           |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DEPLOY_DISPATCH_TOKEN`               | Token *fine-grained* con acceso solo a `SmartPotTech/.github` y permiso **Actions: Read and write**. Sin él, el servicio publica la imagen pero no pide el despliegue |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Opcionales: usuario y token de acceso de Docker Hub para publicar también ahí (`<usuario>/<componente>-smartpot`)                                                     |

Los tres secrets `MQTT_*` son opcionales: si no existen, el broker usa los certificados que ya estén en el servidor.
Cuando existen, el workflow comprueba que el certificado esté firmado por la CA y que la llave le corresponda, y los
instala en `SMARTPOT_CERTS_DIR` con dueño `1883` (el usuario del broker) y la llave en modo `600`. `ca.key` nunca se
sube: con ella se firman certificados nuevos.

Los certificados se generan con [
`generate-certs.sh`](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/scripts/generate-certs.sh) del broker:

```bash
CLIENT_NAME=smartpot-device sh scripts/generate-certs.sh certs mqtt.smartpot.app
```

> [!IMPORTANT]
> Usa una llave SSH dedicada al despliegue y genera secretos propios. `SMARTPOT_AES_KEY` cifra las claves de los
> dispositivos: si cambia, hay que rotar la clave de cada cultivo real. Nunca actives `SMARTPOT_SEED_DEMO` en producción.

### Variables de `ENV_FILE`

| Variable                                                                      | Valor                                                                                                                               |
|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `COMPOSE_PROFILES`                                                            | `db,mail` en un servidor único; quita `db` si MongoDB es externo (define `MONGODB_URI`)                                             |
| `SMARTPOT_*_PORT`                                                             | Puertos del host; todos en `127.0.0.1` salvo `SMARTPOT_MQTT_TLS_PORT`                                                               |
| `SMARTPOT_CERTS_DIR`                                                          | Carpeta de los certificados del broker, por defecto `/etc/mosquitto/certs`                                                          |
| `SMARTPOT_*_TAG`                                                              | `latest`, `sha-<commit>` o `X.Y.Z`                                                                                                  |
| `MONGO_ROOT_PASSWORD` / `SMARTPOT_DB_PASSWORD`                                | Contraseñas de MongoDB (administrador y aplicación)                                                                                 |
| `REDIS_PASSWORD`                                                              | Contraseña de Redis                                                                                                                 |
| `MAIL_PASSWORD` / `MAILPIT_UI_PASSWORD`                                       | SMTP interno y bandeja web, al menos 12 caracteres                                                                                  |
| `MQTT_ADMIN_PASSWORD`                                                         | Cuenta con la que la API administra el broker, al menos 16 caracteres                                                               |
| `SMARTPOT_JWT_SECRET`                                                         | Al menos 32 caracteres                                                                                                              |
| `SMARTPOT_AES_KEY`                                                            | Base64 de 32 bytes aleatorios                                                                                                       |
| `SMARTPOT_AI_TOKEN`                                                           | Token interno entre la API y la IA, al menos 24 caracteres                                                                          |
| `WEB_BASE_URL` / `PUBLIC_API_URL` / `CORS_ALLOWED_ORIGINS`                    | Dominios públicos de la PWA y la API                                                                                                |
| `MQTT_PUBLIC_*` / `MQTT_WEBSOCKET_URL`                                        | Lo que la PWA muestra en la guía para conectar el dispositivo                                                                       |
| `AI_TIMEZONE`                                                                 | Zona horaria del descanso nocturno del asistente, `America/Bogota`                                                                  |
| `LEARNING_MIN_SAMPLES` / `LEARNING_RETRAIN_EVERY` / `LEARNING_RETENTION_DAYS` | Aprendizaje continuo: lecturas para el primer entrenamiento (200), lecturas nuevas para reentrenar (300) y días que se guardan (60) |
| `SIMULATOR_TOKEN`                                                             | Token entre la API y el simulador, al menos 24 caracteres; sin él no se pueden crear cultivos virtuales                             |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_BOT_USERNAME`                                | Bot creado con [@BotFather](https://t.me/BotFather); vacíos, el canal no se ofrece                                                  |
| `TELEGRAM_MODE` / `TELEGRAM_WEBHOOK_SECRET`                                   | `webhook` en producción: la API registra `PUBLIC_API_URL/api/v1/channels/telegram/webhook` y exige el secreto en cada llamada       |

### Operación

Los contenedores conservan su configuración aunque el `.env` se borre. Los secretos son obligatorios en `compose.yaml`,
así que sin `.env` cualquier comando de `docker compose` se detiene en lugar de recrear los contenedores sin secretos.
Para inspeccionar usa `docker` directamente y, para cambiar la configuración, edita `ENV_FILE` y ejecuta **Deploy to
Production**.

```bash
docker ps --filter name=smartpot
docker logs -f smartpot-api
docker logs -f smartpot-broker
docker exec smartpot-db mongosh --quiet /opt/smartpot/migrate.js   # migración a mano
```

Los despliegues simultáneos no se pisan: cada uno sube su configuración a una carpeta temporal propia (`.deploy-<id>`,
permisos `700`) y espera su turno con `flock`.

> [!CAUTION]
> `docker compose down -v` borra los volúmenes `db_data`, `broker_data` y `ai_data`: usuarios, cultivos, lecturas,
> cuentas MQTT y lo aprendido por la IA.

---

## **Despliegue Manual**

```bash
mkdir -p smartpot/production && cd smartpot/production
base=https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production
curl -fsSL $base/compose.yaml -o compose.yaml
curl -fsSL $base/.env.example -o .env
chmod 600 .env
docker compose -p smartpot up -d --wait
docker exec smartpot-db mongosh --quiet /opt/smartpot/migrate.js
```

---

## **Respaldos**

[`backup_smartpot.sh`](backup_smartpot.sh) genera `backups/smartpot-<fecha>.archive.gz` (`mongodump` comprimido,
permisos `600`) y elimina los que superan 14 días (`SMARTPOT_BACKUP_DAYS`). Usa las credenciales del propio contenedor.

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production/backup_smartpot.sh -o backup_smartpot.sh
chmod 700 backup_smartpot.sh
./backup_smartpot.sh
```

Restaurar un respaldo:

```bash
docker exec -i smartpot-db sh -c 'mongorestore --drop --archive --gzip \
  -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin' \
  < backups/smartpot-<fecha>.archive.gz
```

Las cuentas MQTT no necesitan respaldo: al conectarse, la API vuelve a crear en el broker la cuenta de cada cultivo a
partir de la base de datos.

---

## **Nginx y HTTPS**

La carpeta [`nginx/`](nginx) tiene un archivo por dominio para `/etc/nginx/sites-available/`. Todos usan el certificado
`smartpot.app` de Let's Encrypt, que debe cubrir los cinco nombres:

```bash
certbot certonly --nginx --cert-name smartpot.app \
  -d smartpot.app -d www.smartpot.app -d api.smartpot.app -d mqtt.smartpot.app -d mail.smartpot.app
for site in smartpot.app api.smartpot.app mqtt.smartpot.app mail.smartpot.app; do
  cp nginx/$site.conf /etc/nginx/sites-available/$site
  ln -sf /etc/nginx/sites-available/$site /etc/nginx/sites-enabled/$site
done
nginx -t && systemctl reload nginx
```

`mqtt.smartpot.app` solo publica `/mqtt` (WebSocket hacia `127.0.0.1:9001`); los dispositivos no pasan por nginx, se
conectan directo al puerto 8883 con la CA de SmartPot. La PWA necesita HTTPS para registrar el service worker e
instalarse.

Firewall: además de SSH, 80 y 443, solo hace falta `8883/tcp`.

```bash
ufw allow 8883/tcp comment 'MQTT TLS SmartPot'
```

---

## **Verificación**

```bash
curl -fsS https://api.smartpot.app/health
curl -fsS https://api.smartpot.app/api/v1/crop-profiles | head -c 200
curl -s -o /dev/null -w "%{http_code}\n" https://api.smartpot.app/api/v1/crops
curl -sI https://smartpot.app/ | grep -i content-security-policy
openssl s_client -connect mqtt.smartpot.app:8883 -CAfile ca.crt -brief </dev/null
```

| Comprobación              | Resultado esperado                                                                      |
|---------------------------|-----------------------------------------------------------------------------------------|
| `/health`                 | `{"status":"UP","database":"UP","broker":"UP","cache":"UP","ai":"UP","simulator":"UP"}` |
| `/api/v1/crop-profiles`   | Perfiles de las seis especies                                                           |
| `/api/v1/crops` sin token | `401`                                                                                   |
| PWA                       | `200` con `Content-Security-Policy`, `X-Frame-Options` y `Strict-Transport-Security`    |
| Broker                    | `Verification: OK` y protocolo `TLSv1.3` (el mínimo aceptado es 1.2)                    |
