# **Demostración BETA de SmartPot (API en Go + PostgreSQL + Valkey + EMQX + PWA en SolidJS + Simulador en Rust)**

Esta demo levanta SmartPot completo igual que la [demo estable](../demo/README.md), sustituyendo progresivamente los
componentes migrados de nueva generación:
- **API en Go** ([SmartPot-API-Go](https://github.com/SmartPotTech/SmartPot-API-Go)) en lugar de Spring Boot.
- **PostgreSQL 17 + TimescaleDB** ([SmartPot-DB-Postgre](https://github.com/SmartPotTech/SmartPot-DB-Postgre)) en lugar de MongoDB.
- **Valkey 9.1** ([SmartPot-Cache-Valkey](https://github.com/SmartPotTech/SmartPot-Cache-Valkey)) en lugar de Redis.
- **EMQX 5.8** ([SmartPot-Broker-EMQX](https://github.com/SmartPotTech/SmartPot-Broker-EMQX)) en lugar de Mosquitto.
- **PWA en SolidJS** ([SmartPot-Web-Solid](https://github.com/SmartPotTech/SmartPot-Web-Solid)) en lugar de React.
- **Simulador en Rust** ([SmartPot-DataGenerator-Rust](https://github.com/SmartPotTech/SmartPot-DataGenerator-Rust)) en lugar de Python.

El resto de componentes (correo y asistente de IA) son **los mismos de siempre**: la migración es
transparente y no cambia ningún contrato.

> [!WARNING]
> **Versión beta.** Este stack **no es producción**: es la vista previa del stack nuevo mientras se valida antes del
> corte. Hoy producción sigue en Spring Boot + MongoDB. Las contraseñas de los `compose` son públicas; úsalo solo en tu
> equipo (todos los puertos escuchan en `127.0.0.1`). Para el plan completo, lee la
> [documentación de migración](../../docs/SmartPot_Migration.md).

---

## **Requisitos Previos**

* **Docker** con **Docker Compose v2.20 o superior**: [instrucciones](https://docs.docker.com/get-docker/)
* Unos 2 GB de memoria libre.
* Para construir localmente (ver abajo): los repositorios `SmartPot-API-Go`, `SmartPot-DB-Postgre`,
  `SmartPot-Cache-Valkey`, `SmartPot-Broker-EMQX`, `SmartPot-Web-Solid` y `SmartPot-DataGenerator-Rust` clonados junto a `.github/`.

---

## **Ejecución Rápida**

Hay dos formas, según de dónde salgan las imágenes nuevas (API en Go y base PostgreSQL):

### A. Construir desde los repositorios locales (disponible hoy)

Mientras las imágenes nuevas terminan de publicarse en GHCR, construye la API y la base desde los repos clonados junto a
`.github/` (el resto se descarga de GHCR). Desde esta carpeta:

```bash
docker compose -f compose.yaml -f compose.build.yaml up -d --wait --build
```

### B. Solo con imágenes de GHCR (cuando estén publicadas)

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo-beta/compose.yaml -o compose.yaml
docker compose up -d --wait
```

| Componente nuevo | Imagen en GHCR                                     |
|------------------|----------------------------------------------------|
| API (Go)         | `ghcr.io/smartpottech/smartpot-api-go`             |
| Base (Postgre)   | `ghcr.io/smartpottech/smartpot-db-postgre`         |
| Caché (Valkey)   | `ghcr.io/smartpottech/smartpot-cache-valkey`       |
| Broker (EMQX)    | `ghcr.io/smartpottech/smartpot-broker-emqx`        |
| PWA (SolidJS)    | `ghcr.io/smartpottech/smartpot-web-solid`          |
| Simulador (Rust) | `ghcr.io/smartpottech/smartpot-datagenerator-rust` |

Abre http://localhost:5173 e ingresa con la **misma cuenta de la demo** (el seed de PostgreSQL replica el de MongoDB):

| Correo              | Contraseña     |
|---------------------|----------------|
| `demo@smartpot.app` | `SmartPot2026` |

Verás los mismos dos cultivos en línea: **Lechugas del balcón** (NFT, automático) y **Tomates cherry** (maceta, solo
recomienda), alimentados por el simulador como si fueran su ESP32.

| Servicio                | URL                                                                 |
|-------------------------|---------------------------------------------------------------------|
| PWA                     | http://localhost:5173                                               |
| API                     | http://localhost:8091 · documentación en http://localhost:8091/docs |
| Estado de los servicios | http://localhost:8091/health                                        |
| Bandeja de correo       | http://localhost:8025 (`admin` / `demo-mailpit-ui`)                 |
| MQTT                    | `localhost:1883` · WebSocket `ws://localhost:9001`                  |

---

## **Qué Cambia y Qué No**

| Pieza                  | Demo estable                 | Demo beta                                  |
|------------------------|------------------------------|--------------------------------------------|
| API                    | `smartpot-api` (Spring Boot) | `smartpot-api-go` (Go 1.26 + Echo)         |
| Base de datos          | `smartpot-db` (MongoDB 8)    | `smartpot-db-postgre` (PostgreSQL 17 + TimescaleDB) |
| Caché                  | `smartpot-cache` (Redis 8)   | `smartpot-cache-valkey` (Valkey 9.1)       |
| Broker MQTT            | `smartpot-broker` (Mosquitto)| `smartpot-broker-emqx` (EMQX 5.8)          |
| PWA                    | `smartpot-web` (React 19)    | `smartpot-web-solid` (SolidJS + SVG nativo)|
| Simulador              | `smartpot-datagenerator` (Python 3.13) | `smartpot-datagenerator-rust` (Rust 1.85 + Tokio) |
| Conexión de la API     | `MONGODB_URI`                | `DATABASE_URL` (URL de PostgreSQL)         |
| Correo e IA            | Sin cambios                  | **Idénticos**                              |
| Contratos (REST, MQTT, JWT, claves de dispositivo, cuentas) | — | **Idénticos**: mismos secretos, mismo contrato |

La telemetría vive en una **hipertabla de TimescaleDB** (fragmentos de 7 días y retención de 1 año, el equivalente al
índice TTL anterior). Los identificadores siguen siendo ObjectId hexadecimales de 24 caracteres, así que los tokens y
las claves de dispositivo ya emitidos siguen siendo válidos.

---

## **Detener**

Según cómo lo hayas levantado:

```bash
# Si usaste el override de construcción local (A):
docker compose -f compose.yaml -f compose.build.yaml down        # conserva los datos
docker compose -f compose.yaml -f compose.build.yaml down -v     # borra también la base y el broker

# Si usaste solo GHCR (B):
docker compose down
docker compose down -v
```

---

## **Servicios**

| Contenedor                     | Imagen                   | Función                                                               |
|--------------------------------|--------------------------|-----------------------------------------------------------------------|
| `smartpot-demo-beta-db`        | `smartpot-db-postgre`    | **PostgreSQL 17 + TimescaleDB** con esquema, usuario de app y datos demo |
| `smartpot-demo-beta-cache`     | `smartpot-cache-valkey`  | Valkey 9.1 (reemplazo libre de Redis) para el límite de peticiones y la caché de la IA |
| `smartpot-demo-beta-mail`      | `smartpot-mail`          | Mailpit con SMTP autenticado                                          |
| `smartpot-demo-beta-broker`    | `smartpot-broker-emqx`   | EMQX 5.8 con autenticación por cultivo delegada en la API            |
| `smartpot-demo-beta-ai`        | `smartpot-ai`            | Sistema experto, lógica difusa, modelos de ML y agente                |
| `smartpot-demo-beta-api`       | `smartpot-api-go`        | **API REST en Go 1.26 + Echo** (base de datos desacoplada)           |
| `smartpot-demo-beta-web`       | `smartpot-web-solid`     | **PWA en SolidJS** servida por nginx endurecido sin privilegios      |
| `smartpot-demo-beta-simulator` | `smartpot-datagenerator` | Los dos cultivos demo y los cultivos virtuales que crees desde la PWA |

PostgreSQL, Valkey y la IA viven en una red interna sin salida a internet; solo la API, la PWA, el broker y la bandeja de
correo publican puertos, y únicamente en `127.0.0.1`. El simulador sale a internet solo para consultar el clima.
