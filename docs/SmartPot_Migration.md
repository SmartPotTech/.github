<!-- portada
eyebrow: Migration Documentation · Documentación de migración
titulo: SmartPot Migration · Migración de SmartPot
acento: SmartPot
subtitulo: From the original stack to the next-generation components · Del stack original a la nueva generación de componentes
bajada: Why and how the platform migrated, component roadmap, the first phase (Go API and PostgreSQL + TimescaleDB), beta demo validation, and the final production cutover with legacy stack deprecation.
documento: Migration Documentation · Documentación de migración
version: 2.0 · November 2026
equipo: SmartPotTech
proyecto: smartpot.app
-->

# SmartPot Migration · Migración de SmartPot

[English](#english) | [Español](#español)

---

<a id="english"></a>

# English

## Document Summary

| Field | Value |
|---|---|
| Project | SmartPot · [smartpot.app](https://smartpot.app) |
| Organization | SmartPotTech |
| Document | Platform Migration Documentation |
| Version | 2.0 · November 2026 |
| Status | **Successfully Completed**. Canonical Stack B is 100% active and verified in production (`smartpot.app`, `api.smartpot.app`, `mcp.smartpot.app`) |
| Scope | Migration strategy, component roadmap, migrated services (Go, PostgreSQL + TimescaleDB, Valkey, EMQX, SolidJS, Rust, FastMCP), and final production cutover |
| Source of Truth | Individual repository README files and [Technical Documentation](SmartPot_Technical_Documentation.md) describe the canonical production platform |
| Companion Document | [Technical Documentation](SmartPot_Technical_Documentation.md): the platform as deployed in production |

> [!NOTE]
> **Active Production.** The production cutover to Stack B was completed successfully: the platform runs on Go (Echo), PostgreSQL 17 + TimescaleDB, Valkey, EMQX, SolidJS, and Rust, with the MCP server at `mcp.smartpot.app`. Legacy Stack A components were archived as historical reference.

<!-- parte: PART I | Migration Vision -->

## 1. Why Migrate

SmartPot was operational and in production. The migration was not aimed at fixing a broken system, but at **renewing the technical foundation** of every component toward more efficient, secure, and purpose-built engines and languages, without changing platform functionality or visual design:

- **Performance and Footprint.** Native compiled binaries (Go, Rust, C++) replace virtual machines and interpreters: instant startup, lower memory consumption, and minimal container images.
- **Security.** Distroless and `scratch` images without shells or package managers, strong typing, and hardened database engines significantly minimize attack surfaces.
- **The Right Tool for the Job.** A specialized time-series hypertable for telemetry, fine-grained reactivity in the PWA, numerical computation in native engines for AI, and low-level control in embedded firmware.
- **Transparency.** Every migration preserves **identical external contracts** (REST routes, MQTT topics, JSON schemas, keys), enabling components to be swapped individually without impacting dependent services or end users.

> [!NOTE]
> **Guiding Principle.** Components are migrated **one by one** while preserving contracts. Until a new component is verified and deployed, the previous one continues serving traffic. There is no risky "big-bang" cutover.

## 2. Component Roadmap

The migration encompassed the entire platform. Each component progressed at its own pace:

| Component | Repository | Original (Legacy Stack A) | Destination (Stack B) | Status |
|---|---|---|---|---|
| API | `SmartPot-API` | Spring Boot 4 / Java 21 | **Go 1.26 + Echo**, decoupled ports | **Migrated & Canonical**, in production |
| Database | `SmartPot-DB` | MongoDB 8 | **PostgreSQL 17 + TimescaleDB** | **Migrated & Canonical**, in production |
| Cache | `SmartPot-Cache` | Redis 8 | **Hardened Valkey 9.1** | **Migrated & Canonical**, in production |
| MQTT Broker | `SmartPot-Broker` | Eclipse Mosquitto 2.1 | **EMQX 5.8** (delegated HTTP auth to API) | **Migrated & Canonical**, in production |
| Web PWA | `SmartPot-Web` | React 19 + Vite | **SolidJS 1.9 + Vite (native SVG)** | **Migrated & Canonical**, in production |
| IoT Firmware | `SmartPot-IoT` | MicroPython | **Rust 2024 no_std + Embassy** (ESP32) | **Migrated & Canonical**, host tests passing |
| AI Inference | `SmartPot-AI` | Python / FastAPI | **Rust 1.88+ / Axum / Tonic (gRPC)** | **Migrated & Canonical**, in production |
| AI Trainer | `SmartPot-Trainer` | Monolithic in AI | **Python / FastAPI / Polars / ADBC** | **Migrated & Canonical**, decoupled plane |
| Simulator | `SmartPot-DataGenerator` | Python 3.13 / FastAPI | **Rust (Tokio + Axum 0.8 + rumqttc)** | **Migrated & Canonical**, in production |
| Mail Server | `SmartPot-Mail` | Mailpit | Unchanged | Canonical production container |

### Why Each Destination Was Chosen

- **Go API.** A single static binary with goroutine concurrency (MQTT client, Telegram bot, background workers, and event bus run in parallel without thread pools or external cron), packaged into a `scratch` image. Powered by **Echo**, using a strongly-typed `RequestContext` (recycled via `sync.Pool`), centralized error handlers, zero-allocation Radix tree routing, and hexagonal architecture.
- **PostgreSQL + TimescaleDB.** Relational schema with `CHECK` constraints, `JSONB` for optional structured subdocuments, and an optimized **hypertable** for telemetry ingestion with 7-day chunks and 1-year retention.
- **Rust Firmware.** Zero-cost abstractions, memory safety without garbage collection, async tasks and channels decoupling data acquisition from network communication, custom sensor drivers, and MQTT over TLS 8883.
- **SolidJS PWA (`SmartPot-Web`).** Fine-grained reactivity without Virtual DOM overhead (`createSignal`, `createMemo`, `createEffect`), native SVG charts without heavy external graphing libraries, conditional revalidation via `ETag` (`If-None-Match` / `304 Not Modified`), instant cross-tab session synchronization, and an unprivileged Nginx container with Brotli compression.
- **Valkey (`SmartPot-Cache`) & EMQX (`SmartPot-Broker`).** Valkey 9.1 replaces Redis under an open BSD-3-Clause license while preserving protocol compatibility; EMQX 5.8 delegates authentication and per-crop ACLs to the API (`POST /internal/mqtt/authn`) without broker file restarts.
- **Rust Simulator (`SmartPot-DataGenerator`).** Full rewrite with Tokio runtime, Axum 0.8 HTTP server, `rumqttc`, constant-time token verification (`subtle`), `#![deny(unsafe_code)]`, and memory usage below 15 MB RAM.
- **Native AI Inference (`SmartPot-AI`).** High-performance Rust reasoning engine with Axum REST and Tonic gRPC, Sugeno fuzzy logic, ML models, and Ed25519-signed JSON model loading.

## 3. Migration Strategy

1. **One Component at a Time.** Each piece is rewritten, thoroughly tested, and only then integrated into the stack.
2. **Identical Contracts.** Transparent migration: REST endpoints, JSON formats, status codes, MQTT topics, cache keys, and inter-service HTTP contracts remain unchanged.
3. **Beta Demo Validation.** The new stack was validated end-to-end locally with the organizational E2E test suite before production deployment.
4. **Rollback Points.** Until the final cutover, rolling back simply meant keeping the previous container active. After cutover, the legacy stack was archived but retained as a fallback reference.

<!-- parte: PART II | First Phase: Go API and PostgreSQL -->

## 4. What Changed in the First Phase

The first phase updated two foundational components simultaneously:

- **`SmartPot-API`**: Core platform service rewritten in **Go 1.26 with Echo**. Replicates all external contracts from the Spring Boot version: REST endpoints, JSON payloads, error handling, MQTT topics and provisioning, cache keys, SMTP, and HTTP calls to AI, simulator, and Telegram.
- **`SmartPot-DB`**: Relational database on **PostgreSQL 17 + TimescaleDB**, replacing MongoDB while maintaining data contract parity for all dependent services.

## 5. Architecture: The Database as an Implementation Detail

The key to seamless database migration was **Dependency Inversion** (ports and adapters). In `SmartPot-API`, each domain package (`users`, `crops`, `readings`, `actuators`, `commands`, `notifications`, `channels`, `virtualdevices`, `auth`) defines the `Repository` interface it requires—its *port*—while PostgreSQL implementations—the *adapters*—live separately in `internal/storage/postgres`:

```text
internal/
├── crops/            port.go  → Repository interface (what the domain needs)
├── readings/         port.go
├── ...               (one port per domain)
└── storage/postgres/ pgx adapters implementing each port (pool and SQL)
```

## 6. The New Data Model

Ten relational tables, all utilizing `CHAR(24)` identifiers (preserving hexadecimal ObjectId strings) so existing tokens and device keys remain valid:

| Table | Contents |
|---|---|
| `users` | User accounts (unique email, BCrypt hash, role). |
| `crops` | Real or virtual crops. `placement`, `device`, and `health` stored as `JSONB`. |
| `readings` | TimescaleDB **hypertable**: telemetry readings, one typed column per sensor variable. |
| `actuators` | Crop actuators (water pump, UV light, fan, humidifier, dosers) and active state. |
| `commands` | Actuator commands and lifecycle states. |
| `notifications` | In-app alerts and notifications. |
| `password_reset_tokens` | SHA-256 hash of password reset tokens. |
| `channel_links` | Account links to external notification channels (Telegram). |
| `crop_channels` | Per-crop notification routing; `recipients` as `JSONB`. |
| `virtual_devices` | Simulation parameters for virtual crops. |

- **Relational schema** with `CHECK` constraints and unique indexes replaces MongoDB `$jsonSchema` validators.
- **`JSONB`** preserves document flexibility for optional subdocuments (placement, device state, health metrics, events).
- **TimescaleDB** partitions `readings` into 7-day chunks with a **365-day retention policy**. Continuous aggregates provide real-time 1m, 15m, and 1h rollups.

## 7. Transparency and Compatibility

| Dimension | Guarantee |
|---|---|
| REST Endpoints & Payloads | Identical, under `/api/v1`; same status codes, JSON keys, and diagnostic structures. |
| Security | Same JWT specification (HS256, shared secret, issuer, and claims), cost-12 BCrypt, and AES-256-GCM. |
| Identifiers | 24-character hexadecimal ObjectIds; issued tokens and device keys remain fully valid. |
| MQTT Protocol | Same `smartpot/v1/{cropId}/...` topics and dynamic authentication flow. |
| Cache, Mail, AI, Simulator | Same Valkey keys (`smartpot:` prefix), SMTP configuration, and internal HTTP endpoints. |

## 8. Status and Validation

The migration followed a disciplined six-stage implementation plan:
- Full test coverage passing with `go test ./...` across all 19 packages.
- Docker image validates schema, hypertables, retention, application role permissions, `CHECK` constraints, and idempotent migration scripts.
- **Central E2E suite passes 46/46 checks**, verifying authentication, crops, MQTT, telemetry, AI reasoning, commands, and notification channels.

<!-- parte: PART III | Beta Demo Version -->

## 9. What the Demo Beta Is

The **demo beta** (`docker/demo/`) packages the complete canonical stack in a reproducible local environment: Go API, PostgreSQL + TimescaleDB, Valkey, EMQX, Mailpit, Rust AI, SolidJS PWA, and simulator. It seeds demo account data (`demo@smartpot.app` / `SmartPot2026`) and two simulated crops (lettuce and tomato).

## 10. How to Run It

All images are published to GitHub Container Registry (GHCR) and run with a single command without downloading source code:

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo/compose.yaml | docker compose -f - up -d --wait
```

To stop:
```bash
docker compose -p smartpot-demo down -v
```

PWA URL: `http://localhost:5173` | API Healthcheck: `http://localhost:8091/health`

## 11. Equivalence with Stable Demo

| Component | Stable Demo (Legacy Stack A) | Canonical Demo (Stack B) |
|---|---|---|
| API | `smartpot-api` (Spring Boot) | `smartpot-api` (Go 1.26 + Echo) |
| Database | `smartpot-db` (MongoDB 8) | `smartpot-db` (PostgreSQL 17 + TimescaleDB) |
| Cache | `smartpot-cache` (Redis 8) | `smartpot-cache` (Valkey 9.1) |
| Broker | `smartpot-broker` (Mosquitto) | `smartpot-broker` (EMQX 5.8) |
| PWA | `smartpot-web` (React 19) | `smartpot-web` (SolidJS 1.9 + SVG) |
| API Connection | `MONGODB_URI` | `DATABASE_URL` |
| Seed Data | `demo@smartpot.app`, 2 crops | **Identical** |

<!-- parte: PART IV | Production Cutover and Upcoming Phases -->

## 12. Execution and Production Cutover

The production cutover was executed on November 4–5, 2026:
1. **Canonical Repository Reorganization**: 21 repositories reorganized; Stack B assumed canonical names (`SmartPot-API`, `SmartPot-DB`, etc.) while legacy repositories received descriptive suffixes.
2. **GHCR Publishing**: Multi-architecture images published to `ghcr.io/smartpottech/*`.
3. **Production Deployment**: Applied with PostgreSQL 17 + TimescaleDB, Valkey 9.1, EMQX 5.8, Go 1.26 API in `scratch`, SolidJS 1.9 PWA, Rust AI, and FastMCP server at `mcp.smartpot.app`.
4. **Live Verification**: `https://api.smartpot.app/health` reports `UP` across all subsystems.

## 13. Deprecation of the Legacy Stack

With Stack B active in production:
- Stack A repositories (`SmartPot-API-Java`, `SmartPot-DB-Mongo`, `SmartPot-Cache-Redis`, etc.) are formally **deprecated and archived**.
- Readmes and documentation include deprecation banners redirecting to canonical successors.
- Historical code remains available on GitHub for architectural auditability.

## 14. Upcoming Phases

- **Embedded Rust Firmware** (`SmartPot-IoT`): High-performance async firmware in Rust 2024 `no_std` with Embassy, dual-core tasking, timed actuator banks, and Wokwi simulation.
- **Optimized AI Engine** (`SmartPot-AI`): Native Rust inference engine with sub-millisecond Sugeno fuzzy evaluation, SIMD optimizations, and LoRA adaptation.
- **Decoupled Training Plane** (`SmartPot-Trainer`): Separation between real-time inference and analytical training, managing TimescaleDB reading ingestion, tournament evaluation, and Ed25519-signed model exports.
- **Rust Simulator** (`SmartPot-DataGenerator`): Rust simulator with Tokio and Axum 0.8, memory footprint < 15 MB.

<!-- parte: PART V | Transport and Protocols -->

## 15. Transport and Protocols of the New Stack

| Link | Fast Transport | Fallback | Status |
|---|---|---|---|
| API → AI | gRPC (HTTP/2) via UNIX socket or TCP with token | REST HTTP/1.1 | Tested in demo beta, zero fallbacks |
| API → Valkey | UNIX socket in shared volume | TCP 6379 | Tested |
| Device → API | Compact v2 binary packet (27 bytes) over MQTT | v1 JSON payload on same topic | Simulator and firmware supported |
| API → PWA | Server-Sent Events (`/api/v1/crops/{id}/stream`) | 30s polling with `If-None-Match` (304) | Tested with HTTP/1.1 and HTTP/1.0 |
| DB → Trainer | ADBC (Apache Arrow) with read-only `smartpot_reader` | Local SQLite cache fed by API | Tested |

**Compact v2 Binary Packet** (big-endian): `[0]` 'P' (0x50) · `[1]` version 2 · `[2-3]` sequence · `[4-7]` epoch in seconds · `[8-9]` presence bitmask (bit 0 temp, 1 humidity, 2 light, 3 pH, 4 TDS, 5 pressure, 6 soil) · `[10-11]` temp i16 ×100 · `[12-13]` humidity ×100 · `[14-17]` light u32 lux · `[18-19]` pH ×100 · `[20-21]` TDS · `[22-23]` pressure ×10 hPa · `[24-25]` soil ×100 · `[26]` CRC-8.

---

<a id="español"></a>

# Español

# Migración de SmartPot

## Ficha del documento

| Campo             | Valor                                                                                                                                                 |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Proyecto          | SmartPot · [smartpot.app](https://smartpot.app)                                                                                                       |
| Organización      | SmartPotTech                                                                                                                                           |
| Documento         | Documentación de migración de la plataforma                                                                                                           |
| Versión           | 2.0 · noviembre 2026                                                                                                                                  |
| Estado            | **Completada con éxito**. El Stack B canónico está 100% activo y verificado en producción (smartpot.app, api.smartpot.app, mcp.smartpot.app)          |
| Alcance           | La estrategia de migración, la hoja de ruta por componente, los componentes migrados (Go, PostgreSQL + TimescaleDB, Valkey, EMQX, SolidJS, Rust, FastMCP) y el corte definitivo a producción |
| Fuente de verdad  | Los README de cada repositorio y la [documentación técnica](SmartPot_Technical_Documentation.md) describen la plataforma canónica en producción       |
| Documento hermano | [Documentación técnica](SmartPot_Technical_Documentation.md): la plataforma tal como está en producción                                               |

> [!NOTE]
> **Producción activa.** El corte a producción del Stack B fue completado exitosamente: la plataforma opera sobre Go (Echo), PostgreSQL 17 + TimescaleDB, Valkey, EMQX, SolidJS y Rust, con el servidor MCP en `mcp.smartpot.app`. Los componentes legados del Stack A fueron archivados como referencia histórica.

<!-- parte: PARTE I | Visión de la migración -->

## 1. Por qué migrar

SmartPot funciona y está en producción. La migración no busca arreglar algo roto, sino **renovar la base técnica** de
cada componente hacia lenguajes y motores más eficientes, seguros y adecuados a su trabajo, sin cambiar lo que la
plataforma hace ni cómo se ve. Los motivos, componente a componente:

- **Rendimiento y huella.** Binarios compilados y nativos (Go, Rust, C++) en lugar de máquinas virtuales e intérpretes:
  arranque inmediato, menos memoria e imágenes mínimas.
- **Seguridad.** Imágenes sin shell ni gestor de paquetes (`scratch`), tipado fuerte y motores endurecidos reducen la
  superficie de ataque.
- **Herramienta adecuada a cada trabajo.** Una base de series temporales para la telemetría, reactividad fina en la PWA,
  cálculo numérico en C++ para la IA y el simulador, y control de bajo nivel en el dispositivo.
- **Transparencia.** Cada migración conserva **idénticos los contratos externos** (REST, MQTT, formas JSON, claves),
  así que las piezas se cambian una por una sin tocar al resto ni a los usuarios.

> [!NOTE]
> **Principio rector.** Se migra **componente por componente**, manteniendo los contratos. Mientras una pieza nueva no
> esté validada y desplegada, la anterior sigue sirviendo producción. No hay un "gran cambio" de todo a la vez.

## 2. Hoja de ruta por componente

La migración abarca toda la plataforma. Cada componente avanza a su ritmo; la primera fase (API y base de datos) es la
que ya está construida.

| Componente        | Repositorio                                                | Hoy (producción)         | Destino                                        | Estado                                   |
|-------------------|------------------------------------------------------------|--------------------------|------------------------------------------------|------------------------------------------|
| API               | `SmartPot-API` → `SmartPot-API-Go`                         | Spring Boot 4 / Java 21  | **Go 1.26 + Echo**, base desacoplada           | **Migrada (código)**, en la demo beta    |
| Base de datos     | `SmartPot-DB` → `SmartPot-DB-Postgre`                      | MongoDB 8                | **PostgreSQL 17 + TimescaleDB**                | **Migrada (código)**, en la demo beta    |
| Caché             | `SmartPot-Cache` → `SmartPot-Cache-Valkey`                 | Redis 8                  | **Valkey 9.1** endurecido                      | **Migrada (código)**, en la demo beta    |
| Broker MQTT       | `SmartPot-Broker` → `SmartPot-Broker-EMQX`                 | Mosquitto 2.1            | **EMQX 5.8** (Apache-2.0, auth HTTP en la API) | **Migrado (código)**, en la demo beta    |
| Web (PWA)         | `SmartPot-Web` → `SmartPot-Web-Solid`                      | React 19 + Vite          | **SolidJS + TypeScript + Vite (SVG nativo)**   | **Migrada (código)**, en la demo beta    |
| Firmware IoT      | `SmartPot-IoT` → `SmartPot-IoT-Rust`                       | MicroPython              | **Rust 2024 no_std + Embassy** (ESP32 físico o en Wokwi)      | **Migrado (código y Wokwi)**, probado con EMQX y API Go  |
| Asistente de IA (Inferencia) | `SmartPot-AI`                                              | Python / FastAPI         | **Aceleración nativa C++20, Cython nogil, Polars y LoRA** (Theil-Sen $O(M)$, Sugeno SIMD, pre-baked models, recarga en caliente < 5 ms) | **Optimizado (código y benchmarks)**, integrado en main |
| Entrenador de IA (Training Plane) | `SmartPot-Trainer`                                         | Python / FastAPI / Scikit-Learn | **Plano de entrenamiento desacoplado** (Champion-Challenger, TimeSeriesSplit, GridSearchCV, K-Means silueta, Isolation Forest, LoRA) | **Construido e integrado**, en todos los stacks |
| Simulador         | `SmartPot-DataGenerator` → `SmartPot-DataGenerator-Rust`   | Python 3.13 / FastAPI    | **Rust (edición 2024) + Tokio + Axum 0.8 + rumqttc**     | **Migrado (código)**, en la demo beta    |
| Correo            | `SmartPot-Mail`                                            | Mailpit                  | Sin cambio en el plan                          | —                                        |

### Por qué cada destino

- **API en Go.** Un solo binario estático, concurrencia con goroutines (el cliente MQTT, el bot, los trabajos
  periódicos y el bus de eventos corren en paralelo sin hilos ni cron), e imagen final `scratch`. Sobre **Echo**, la
  capa HTTP aprovecha que `echo.Context` es una interfaz desacoplada para inyectar un contexto propio con tipado
  estricto en tiempo de compilación (`*httpserver.RequestContext`, reciclado con `sync.Pool`) que transporta la
  identidad del usuario, las credenciales JWT y la traza de telemetría sin mapas de cadenas ni conversiones inseguras;
  combina manejadores con retorno explícito de error (`func(echo.Context) error`) conectados a un `HTTPErrorHandler`
  centralizado, middlewares por composición funcional lineal, enrutamiento en árbol Radix *zero-allocation* y una
  interfaz `echo.Validator` intercambiable. Reemplaza al tiempo de ejecución de la JVM sin perder ninguna función.
- **Base en PostgreSQL + TimescaleDB.** Relacional tipado con restricciones `CHECK` (en lugar de validadores
  `$jsonSchema`), `JSONB` para los subdocumentos ricos y opcionales, y una **hipertabla** para la telemetría, pensada
  para la ingesta continua de lecturas de sensores.
- **Firmware en Rust.** Seguridad de memoria sin recolector de basura, tareas asíncronas y canales para desacoplar la
  adquisición de datos, la conectividad y los comandos, con drivers embebidos propios y MQTT sobre TLS.
- **PWA en SolidJS (`SmartPot-Web-Solid`).** Reactividad de grano fino sin Virtual DOM (`createSignal`, `createMemo`,
  `createEffect`), gráficos de series temporales renderizados en SVG nativo sin bibliotecas externas pesadas,
  revalidación condicional por `ETag` (`If-None-Match` / `304 Not Modified`) coordinada con `SmartPot-API-Go` para no
  transferir ni volver a parsear JSON cuando las lecturas no cambian, sincronización instantánea de sesión entre
  pestañas y cabecera `Cross-Origin-Resource-Policy: same-origin` en el contenedor Nginx sin privilegios.
- **Caché en Valkey (`SmartPot-Cache-Valkey`) y Broker en EMQX (`SmartPot-Broker-EMQX`).** Valkey 9.1 sustituye a Redis
  con licencia libre manteniendo el protocolo y las claves; EMQX 5.8 delega la autenticación y las ACL por cultivo en la
  API (`POST /internal/mqtt/authn`) sin reiniciar ni sincronizar archivos.
- **Simulador en Rust (`SmartPot-DataGenerator-Rust`).** Reescritura completa en Rust 1.85 con el runtime Tokio,
  servidor HTTP Axum 0.8, cliente MQTT `rumqttc`, validación de tokens en tiempo constante (`subtle`), `#![deny(unsafe_code)]`
  y huella de memoria < 15 MB RAM, con healthcheck nativo embebido en el binario (`--healthcheck`).
- **IA con C++.** Motor numérico nativo en C++20 (`src/native/`) con enlace C ABI directo (`ctypes`) para las
  tareas intensivas: estimador de Theil-Sen lineal en $O(M)$ mediante `std::nth_element` (3.6x–50x de aceleración frente
  a `np.triu_indices`), lógica difusa Sugeno branchless con constantes `constexpr`, control de calidad de datos (IQR) y
  transformaciones vectoriales continuas, con fallback transparente a Python y telemetría en `/v1/engine`. Preserva
  100% idéntica la capa de servicio FastAPI y los contratos HTTP.

## 3. Estrategia de migración

1. **Un componente a la vez.** Cada pieza se reescribe en su propio repositorio, se prueba y solo entonces entra al
   stack nuevo. La anterior no se toca hasta que la nueva esté desplegada y estable.
2. **Contratos idénticos.** La migración es transparente: las rutas REST, las formas JSON, los códigos y mensajes, los
   tópicos MQTT, las claves de Redis y las llamadas HTTP entre servicios no cambian. Los componentes vecinos no notan la
   diferencia.
3. **Validación en una demo beta.** Antes del corte, el stack nuevo se levanta completo en local con la suite de
   extremo a extremo de la organización. Solo pasa a producción con todo en verde.
4. **Puntos de reversa.** Mientras no se haga el corte, volver atrás es simplemente no desplegar. Tras el corte, el
   stack anterior queda deprecado pero disponible como respaldo durante un periodo de observación.

<!-- parte: PARTE II | Primera fase: API en Go y PostgreSQL -->

## 4. Qué cambió en la primera fase

La primera fase reescribe **dos** componentes a la vez, porque van de la mano:

- **`SmartPot-API-Go`**: el núcleo de la plataforma reescrito en **Go 1.26 con Echo**. Reproduce idénticos todos los
  contratos externos de la versión en Spring Boot: rutas REST, formas JSON, códigos y mensajes en español, tópicos MQTT
  y aprovisionamiento en Mosquitto, claves de Redis, SMTP y las llamadas HTTP a la IA, al simulador y a Telegram.
- **`SmartPot-DB-Postgre`**: la base de datos sobre **PostgreSQL 17 + TimescaleDB**, que sustituye a MongoDB
  manteniendo el mismo contrato de datos de cara al resto de la plataforma.

Para los demás componentes —broker, caché, correo, IA, PWA, firmware y simulador— **no cambia nada**: la API es el único
servicio que habla con la base de datos, así que el motor es un detalle interno.

## 5. Arquitectura: la base de datos como detalle

La clave de que el motor sea intercambiable es la **inversión de dependencias** (puertos y adaptadores). En
`SmartPot-API-Go`, cada dominio (users, crops, readings, actuators, commands, notifications, channels, virtualdevices,
auth) declara la **interfaz** `Repository` que necesita de la capa de datos —su *puerto*—, y las implementaciones sobre
PostgreSQL —los *adaptadores*— viven aparte, en `internal/storage/postgres`. El dominio no conoce el motor: depende de
la interfaz, no de la implementación.

```text
internal/
├── crops/            port.go  → interfaz Repository (lo que el dominio necesita)
├── readings/         port.go
├── ...               (un puerto por dominio)
└── storage/postgres/ adaptadores pgx que implementan cada puerto (pool y SQL)
```

El resultado: cambiar de MongoDB a PostgreSQL fue **implementar los adaptadores nuevos y cablearlos en `cmd/api`**, sin
tocar la lógica de negocio. El mismo diseño permitiría, en el futuro, otro motor sin reescribir el dominio.

## 6. El modelo de datos nuevo

Diez tablas, todas con identificadores `CHAR(24)` (los mismos ObjectId hexadecimales que generaba la API), para que
los tokens y las claves de dispositivo ya emitidos sigan siendo válidos:

| Tabla                   | Contenido                                                                   |
|-------------------------|-----------------------------------------------------------------------------|
| `users`                 | Cuentas (correo único, hash BCrypt, rol).                                   |
| `crops`                 | Cultivos reales o virtuales. `placement`, `device` y `health` como `JSONB`. |
| `readings`              | **Hipertabla** de TimescaleDB: telemetría, una columna tipada por variable. |
| `actuators`             | Salidas de cada cultivo (bomba, luz UV, ventilador, etc.) y su estado.      |
| `commands`              | Órdenes a los actuadores y su ciclo de vida.                                |
| `notifications`         | Alertas de la PWA (cuenta y cultivo).                                       |
| `password_reset_tokens` | Solo el SHA-256 del token de recuperación.                                  |
| `channel_links`         | Vínculo de una cuenta con un canal externo (Telegram).                      |
| `crop_channels`         | Avisos de un cultivo por un canal; `recipients` como `JSONB`.               |
| `virtual_devices`       | Configuración de simulación de un cultivo virtual.                          |

- **Relacional tipado** con `CHECK` e índices únicos (correo, cultivo + tipo de actuador) reemplaza a los validadores
  `$jsonSchema`.
- **`JSONB`** conserva la flexibilidad del modelo documental para los subdocumentos opcionales (lugar, dispositivo,
  salud, destinatarios, eventos).
- **TimescaleDB** particiona `readings` por tiempo en fragmentos de 7 días y una **política de retención de 1 año**
  descarta los antiguos (equivale al índice TTL de MongoDB). Las series temporales usan `time_bucket`, el equivalente
  nativo de `$dateTrunc`. Los demás vencimientos (tokens, comandos, notificaciones) los hace un **barrido en proceso**
  de la API, sin cron.

La cuenta administradora de PostgreSQL es la dueña del esquema y **no la usa la API**; la API entra con un usuario que
solo tiene permisos de DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) sobre su base. La imagen corre endurecida
(`read_only`, `no-new-privileges`, capacidades de Linux mínimas).

## 7. Transparencia y compatibilidad

| Aspecto                      | Garantía                                                                                      |
|------------------------------|-----------------------------------------------------------------------------------------------|
| Rutas y formas REST          | Idénticas, bajo `/api/v1`; mismos códigos y mensajes en español.                              |
| Seguridad                    | Mismo JWT (HS256, mismo secreto, emisor y *claims*), BCrypt de costo 12 y AES-256-GCM.        |
| Identificadores              | ObjectId hexadecimales de 24 caracteres; los tokens y claves ya emitidos siguen válidos.      |
| MQTT                         | Mismos tópicos `smartpot/v1/{cropId}/...` y mismo aprovisionamiento en Mosquitto.             |
| Caché, correo, IA, simulador | Mismas claves de Redis (prefijo `smartpot:`), SMTP y llamadas HTTP; sin cambios de contrato.  |

## 8. Estado y validación

La primera fase se construyó en un **plan de seis etapas** (esquema de la base, configuración de Go, puertos y
adaptadores por dominio, limpieza del código de MongoDB, validación de extremo a extremo y documentación), con un
*commit* por dominio para mantener la compilación en verde en cada paso.

- **Código completo y commiteado** en `SmartPot-API-Go` y `SmartPot-DB-Postgre`.
- `go build`, `go vet` y `go test ./...` en verde; cubren el cifrado (incluido descifrar un texto cifrado por la
  versión en Java), JWT, contraseñas, rangos de medida, tópicos y telemetría, aprovisionamiento, comandos y expiración,
  reglas de cultivo y clima, agente, canales y el bot de Telegram.
- La imagen de la base valida en CI el esquema, la hipertabla, la retención, los permisos del usuario de la aplicación,
  las restricciones `CHECK` y la migración idempotente, con y sin datos demo.
- **Suite central de extremo a extremo en verde (46/46)** contra la API en Go y PostgreSQL + TimescaleDB, cubriendo
  autenticación, cultivos, MQTT, lecturas, IA, comandos y canales.

<!-- parte: PARTE III | La versión demo beta -->

## 9. Qué es la demo beta

La **demo beta** ([`docker/demo-beta/`](../docker/demo-beta/README.md)) es el stack nuevo completo en tu computador: la
API en Go y PostgreSQL + TimescaleDB, más el broker, la caché, el correo, el asistente de IA, la PWA y el simulador **sin
cambios**. Sirve para probar la migración de punta a punta antes del corte, con los mismos datos de ejemplo que la demo
estable: la cuenta `demo@smartpot.app` y los dos cultivos (lechugas y tomates) que el simulador alimenta como si fueran
su ESP32. El *seed* de PostgreSQL replica exactamente al de MongoDB (misma cuenta, mismos cultivos, mismas claves de
dispositivo cifradas con la clave AES de demostración).

## 10. Cómo ejecutarla

Todas las imágenes son públicas en GitHub Container Registry (GHCR) y la demo beta se levanta con un solo comando,
sin descargar el código:

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo-beta/compose.yaml | docker compose -f - up -d --wait
```

Se detiene con `docker compose -p smartpot-demo-beta down` (con `-v` borra también los datos).

Luego abre http://localhost:5173 (cuenta `demo@smartpot.app` / `SmartPot2026`) y revisa el estado en
http://localhost:8091/health. El [README de la demo beta](../docker/demo-beta/README.md) tiene el detalle.

## 11. Equivalencia con la demo estable

| Pieza                         | Demo estable (`docker/demo/`) | Demo beta (`docker/demo-beta/`)            |
|-------------------------------|-------------------------------|--------------------------------------------|
| API                           | `smartpot-api` (Spring Boot)  | `smartpot-api-go` (Go 1.26 + Echo)         |
| Base de datos                 | `smartpot-db` (MongoDB 8)     | `smartpot-db-postgre` (PostgreSQL + TimescaleDB) |
| Caché                         | `smartpot-cache` (Redis 8)    | `smartpot-cache-valkey` (Valkey 9.1)       |
| Broker MQTT                   | `smartpot-broker` (Mosquitto) | `smartpot-broker-emqx` (EMQX 5.8)          |
| PWA                           | `smartpot-web` (React 19)     | `smartpot-web-solid` (SolidJS + SVG nativo)|
| Conexión de la API            | `MONGODB_URI`                 | `DATABASE_URL`                             |
| Correo, IA y simulador        | Las mismas imágenes           | **Las mismas imágenes**                    |
| Cuenta y cultivos demo        | `demo@smartpot.app`, 2 cultivos | **Idénticos**                            |

<!-- parte: PARTE IV | Camino a producción y próximas fases -->

## 12. Ejecución y corte definitivo a producción

El corte a producción se ejecutó exitosamente el 4 y 5 de noviembre de 2026, culminando el plan de modernización:

1. **Reorganización y renombramiento canónico de repositorios**: Los 21 repositorios de la organización fueron ordenados. El Stack B asumió los nombres canónicos oficiales (`SmartPot-API`, `SmartPot-DB`, `SmartPot-Cache`, `SmartPot-Broker`, `SmartPot-Web`, `SmartPot-AI`, `SmartPot-DataGenerator`, `SmartPot-IoT`), mientras que los componentes legados del Stack A fueron renombrados con sufijos de tecnología descriptivos (`-Java`, `-Mongo`, `-Redis`, `-Mosquito`, `-React`, `-Python`).
2. **Publicación universal de imágenes en GHCR**: Se generaron y publicaron las imágenes públicas bajo el namespace oficial `ghcr.io/smartpottech/*`.
3. **Despliegue a producción con GitHub Actions**: Se aplicó la configuración de producción con PostgreSQL 17 + TimescaleDB (`DATABASE_URL`), Valkey (`VALKEY_PASSWORD`), EMQX 5.8, API Go 1.26 en imagen `scratch`, PWA en SolidJS 1.9, motor de IA en Rust y servidor MCP en `mcp.smartpot.app` (puerto 8092).
4. **Verificación en vivo**: `https://api.smartpot.app/health` respondió `UP` en todos los subsistemas (database, broker, cache, ai, simulator), `https://smartpot.app/` sirve la PWA reactiva y `https://mcp.smartpot.app/health` reporta disponibilidad para asistentes inteligentes.

## 13. Depreciación del stack anterior

Con el Stack B consolidado en producción:
- Los componentes anteriores del **Stack A** (`SmartPot-API-Java`, `SmartPot-DB-Mongo`, `SmartPot-Cache-Redis`, `SmartPot-Broker-Mosquito`, `SmartPot-Web-React`, `SmartPot-AI-Python`, `SmartPot-DataGenerator-Python`, `SmartPot-Proxy`) quedan formalmente **deprecados y archivados**.
- Su documentación fue actualizada con advertencias explícitas de deprecación y enlaces de redirección a sus contrapartes canónicas.
- Quedan preservados en GitHub como evidencia histórica de la evolución arquitectónica de la plataforma.

## 14. Próximas fases

Tras la API en Go, PostgreSQL + TimescaleDB, Valkey, EMQX y la PWA en SolidJS (`SmartPot-Web-Solid`), la hoja de ruta
continúa (ver la [sección 2](#2-hoja-de-ruta-por-componente)):

- **Firmware en Rust** (`SmartPot-IoT-Rust`): firmware de alto rendimiento migrado y optimizado en Rust 2024 `no_std` con Embassy dual-core, canales libres de bloqueos, banco de actuadores temporizados y soporte para simulación completa en Wokwi (`diagram.json`, `wokwi.toml`, `start.py`) o placa física ESP32. No forma parte del despliegue Docker de `demo-beta` (los cultivos en el servidor los simula `SmartPot-DataGenerator-Rust`), pero su contrato MQTT v1 fue probado y validado de extremo a extremo contra EMQX y la API Go de `demo-beta`. Convive con el firmware en MicroPython hasta el corte definitivo.
- **IA optimizada con motor nativo C++20, Cython, Polars y LoRA** (`SmartPot-AI`): motor numérico de alto rendimiento en C++20 con estimador Theil-Sen lineal en $O(M)$, inferencia difusa Sugeno branchless con latencia sub-milisegundo ($47.2\text{ µs}$), puente Cython nogil con Memoryviews zero-copy, eliminación de cold-start (57 ms vs 5,500 ms) con artefacto binario estático, pipeline de telemetría DQS acelerado con Polars LazyFrame (20,000 filas en 36 ms) y adaptación analítica en caliente por especie mediante Low-Rank Adaptation (LoRA) en $< 0.19\text{ ms}$, preservando el 100% de paridad funcional, agronómica y de contratos REST de la IA.
- **Microservicio desacoplado de entrenamiento y aprendizaje continuo** (`SmartPot-Trainer`): separación estricta entre plano de servicio (inferencia pura sub-milisegundo en `SmartPot-AI`) y plano de entrenamiento pesado (`SmartPot-Trainer`). Gestiona SQLite WAL con seudonimización SHA-256, torneos de modelos con `TimeSeriesSplit(cv=4)` y `GridSearchCV`, estados operacionales con K-Means y silueta ($k \in [2, 6]$), detección de anomalías con `IsolationForest` y adaptadores LoRA, disparando recarga en memoria caliente (`POST /v1/learning/reload`) en $< 5\text{ ms}$ en `SmartPot-AI` tras cada promoción de modelo sin reinicio de contenedor. Integrado en todos los stacks de despliegue (`demo`, `dev`, `production`) con `ai_data` de solo lectura para la IA y la clave privada de firma en el volumen separado `trainer_keys` (nunca legible por la IA).
- **Simulador en Rust** (`SmartPot-DataGenerator-Rust`): migrado a Rust (edición 2024) con Axum 0.8, Tokio y rumqttc con huella < 15 MB e integrado en demo beta.

Cada fase repetirá el mismo patrón: reescritura transparente, validación en la demo beta, corte con aprobación y
depreciación del componente anterior.

<!-- parte: PARTE V | Transporte y protocolos del stack nuevo -->

## 15. Transporte y protocolos del stack nuevo

El stack nuevo evoluciona en sus propios repositorios (no hay un tercer stack). Cada protocolo rápido tiene un
respaldo compatible con cualquier nginx, incluso HTTP/1.0, porque los servidores de desarrollo son compartidos.

| Tramo | Transporte rápido | Respaldo | Estado (2026-10-31) |
|-------|-------------------|----------|---------------------|
| API → IA | gRPC (HTTP/2) por socket UNIX (`AI_GRPC_SOCKET`) o TCP interno (`AI_GRPC_ADDR`), con el mismo JSON del contrato REST y el token en los metadatos | REST por HTTP/1.1 | Probado en la demo beta, sin caídas al respaldo |
| API → Valkey | Socket UNIX (`VALKEY_SOCKET`) en un volumen compartido | TCP 6379 | Probado |
| Dispositivo → API | Paquete compacto v2 de 27 bytes por MQTT (máscara de presencia, presión y luz de 32 bits) | JSON del contrato v1, en el mismo tópico | El simulador lo usa en la demo beta; el firmware, si se compila con `COMPACT_TELEMETRY` |
| API → PWA | Server-Sent Events (`/api/v1/crops/{id}/stream`), con chunked o hasta el cierre en HTTP/1.0 | Consulta cada 30 s con `If-None-Match` (304) | Probado con HTTP/1.1 y HTTP/1.0 |
| Base → Entrenador | ADBC (Apache Arrow) con el rol de solo lectura `smartpot_reader`, solo cultivos reales | SQLite local alimentado por la API | Probado |

**Paquete compacto v2** (big-endian): `[0]` 'P' (0x50) · `[1]` versión 2 · `[2-3]` secuencia · `[4-7]` época en
segundos (0 = sin hora) · `[8-9]` máscara de presencia (bit 0 temperatura, 1 humedad, 2 luz, 3 pH, 4 TDS, 5 presión,
6 sustrato) · `[10-11]` temperatura i16 ×100 · `[12-13]` humedad ×100 · `[14-17]` luz u32 en lux · `[18-19]` pH ×100 ·
`[20-21]` TDS · `[22-23]` presión ×10 hPa · `[24-25]` sustrato ×100 · `[26]` CRC-8 (polinomio 0x07). Un sensor sin su
bit está ausente, como si se omitiera en el JSON; la API acepta también la versión 1 de 22 bytes.

Otras piezas de rendimiento ya en el código: ingesta por lotes con `COPY` binario (100 lecturas o 10 ms), agregados
continuos de TimescaleDB con datos en tiempo real, banda muerta del agente antes de consultar a la IA, núcleo nativo
C++/Cython de la IA y compresión estática Brotli y Gzip de la PWA. Quedan como trabajo futuro, sin código: mTLS de los
dispositivos y ExHook gRPC de EMQX. La inferencia ya es sin pickle: el Trainer publica `smartpot.learned-models/1`
firmado con Ed25519/BLAKE2b y la IA lo evalúa nativamente; `TRUSTED_MODEL_PUBLIC_KEY_HEX` fija la clave de confianza.
