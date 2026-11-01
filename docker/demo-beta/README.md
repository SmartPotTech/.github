# **Demostración BETA de SmartPot (API en Go + PostgreSQL + Valkey + EMQX + PWA en SolidJS + Simulador en Rust)**

Esta demo levanta SmartPot completo igual que la [demo estable](../demo/README.md), sustituyendo progresivamente los
componentes migrados de nueva generación:
- **API en Go** ([SmartPot-API-Go](https://github.com/SmartPotTech/SmartPot-API-Go)) en lugar de Spring Boot.
- **PostgreSQL 17 + TimescaleDB** ([SmartPot-DB-Postgre](https://github.com/SmartPotTech/SmartPot-DB-Postgre)) en lugar de MongoDB.
- **Valkey 9.1** ([SmartPot-Cache-Valkey](https://github.com/SmartPotTech/SmartPot-Cache-Valkey)) en lugar de Redis.
- **EMQX 5.8** ([SmartPot-Broker-EMQX](https://github.com/SmartPotTech/SmartPot-Broker-EMQX)) en lugar de Mosquitto.
- **PWA en SolidJS** ([SmartPot-Web-Solid](https://github.com/SmartPotTech/SmartPot-Web-Solid)) en lugar de React.
- **Simulador en Rust** ([SmartPot-DataGenerator-Rust](https://github.com/SmartPotTech/SmartPot-DataGenerator-Rust)) en lugar de Python.
- **Entrenador Desacoplado** ([SmartPot-Trainer](https://github.com/SmartPotTech/SmartPot-Trainer)) separando el aprendizaje continuo de la inferencia en caliente de SmartPot-AI.

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

---

## **Ejecución Rápida**

Todas las imágenes son públicas en **GitHub Container Registry (GHCR)** (`ghcr.io/smartpottech/*`). Se levanta el stack completo en un único paso:

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo-beta/compose.yaml | docker compose -f - up -d --wait
```

No hace falta descargar nada más: el `compose.yaml` llega por la tubería y Docker baja las imágenes.

| Componente nuevo | Imagen en GHCR                                     |
|------------------|----------------------------------------------------|
| API (Go)         | `ghcr.io/smartpottech/smartpot-api-go`             |
| Base (Postgre)   | `ghcr.io/smartpottech/smartpot-db-postgre`         |
| Caché (Valkey)   | `ghcr.io/smartpottech/smartpot-cache-valkey`       |
| Broker (EMQX)    | `ghcr.io/smartpottech/smartpot-broker-emqx`        |
| PWA (SolidJS)    | `ghcr.io/smartpottech/smartpot-web-solid`          |
| Simulador (Rust) | `ghcr.io/smartpottech/smartpot-datagenerator-rust` |
| Entrenador (Trainer) | `ghcr.io/smartpottech/smartpot-trainer`       |

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

Desde cualquier carpeta, por el nombre del proyecto:

```bash
docker compose -p smartpot-demo-beta down        # conserva los datos
docker compose -p smartpot-demo-beta down -v     # borra también la base y el broker
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
| `smartpot-demo-beta-simulator` | `smartpot-datagenerator-rust` | Los dos cultivos demo y los cultivos virtuales que crees desde la PWA |
| `smartpot-demo-beta-trainer`   | `smartpot-trainer`       | Aprendizaje continuo fuera del proceso de inferencia; lee la base con el rol de solo lectura |

PostgreSQL, Valkey y la IA viven en una red interna sin salida a internet; solo la API, la PWA, el broker y la bandeja de
correo publican puertos, y únicamente en `127.0.0.1`. El simulador sale a internet solo para consultar el clima.

---

## **Auditoría de Calidad y Pruebas A/B**

La auditoría completa de migración entre la demo estable y la demo beta está documentada en:
- [Auditoría Técnica y Plan de Pruebas A/B (AUDIT_QA_AB.md)](AUDIT_QA_AB.md)

### Ejecución Local de Pruebas Centralizadas

Para verificar el stack de la demo beta en ejecución local:

```bash
# Con el stack levantado en http://localhost:8091:
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo-beta/test.py | python3 -
```

El script comprueba la salud de los servicios, autenticación, cultivos semilla en TimescaleDB, ciclo de cultivo virtual, actuadores, conflicto 409 y consultas a la IA.

### Workflow Automatizado en GitHub Actions

El repositorio incluye el workflow **Demo BETA QA** (`.github/workflows/demo-beta-qa.yml`), que permite evaluar el funcionamiento completo del stack con disparadores manuales (`workflow_dispatch`) o en cambios sobre esta carpeta.
