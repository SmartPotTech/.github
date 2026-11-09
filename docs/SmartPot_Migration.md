<!-- portada
eyebrow: Migration Documentation · Documentación de migración
titulo: SmartPot Migration Guide: Stack A to Stack B
acento: SmartPot
subtitulo: From the original stack to the next-generation components · Del stack original a la nueva generación de componentes
bajada: Why and how the platform migrated, component roadmap, the first phase (Go API and PostgreSQL + TimescaleDB), beta demo validation, and the final production cutover with legacy stack deprecation.
documento: Migration Documentation · Documentación de migración
version: 2.0 · November 2026
equipo: SmartPotTech
proyecto: smartpot.app
-->

# SmartPot Migration · Migración de SmartPot

---

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
| API | `SmartPot-API` | Spring Boot 4 / Java 21 | **Go 1.27.3 + Echo**, decoupled ports | **Migrated & Canonical**, in production |
| Database | `SmartPot-DB` | MongoDB 8 | **PostgreSQL 17 + TimescaleDB** | **Migrated & Canonical**, in production |
| Cache | `SmartPot-Cache` | Redis 8 | **Hardened Valkey 9.1.3** | **Migrated & Canonical**, in production |
| MQTT Broker | `SmartPot-Broker` | Eclipse Mosquitto 2.1 | **EMQX 5.8.9** (delegated HTTP auth to API) | **Migrated & Canonical**, in production |
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
- **Valkey (`SmartPot-Cache`) & EMQX (`SmartPot-Broker`).** Valkey 9.1.3 replaces Redis under an open BSD-3-Clause license while preserving protocol compatibility; EMQX 5.8.9 delegates authentication and per-crop ACLs to the API (`POST /internal/mqtt/authn`) without broker file restarts.
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

- **`SmartPot-API`**: Core platform service rewritten in **Go 1.27.3 with Echo**. Replicates all external contracts from the Spring Boot version: REST endpoints, JSON payloads, error handling, MQTT topics and provisioning, cache keys, SMTP, and HTTP calls to AI, simulator, and Telegram.
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
| API | `smartpot-api` (Spring Boot) | `smartpot-api` (Go 1.27.3 + Echo) |
| Database | `smartpot-db` (MongoDB 8) | `smartpot-db` (PostgreSQL 17 + TimescaleDB) |
| Cache | `smartpot-cache` (Redis 8) | `smartpot-cache` (Valkey 9.1.3) |
| Broker | `smartpot-broker` (Mosquitto) | `smartpot-broker` (EMQX 5.8.9) |
| PWA | `smartpot-web` (React 19) | `smartpot-web` (SolidJS 1.9 + SVG) |
| API Connection | `MONGODB_URI` | `DATABASE_URL` |
| Seed Data | `demo@smartpot.app`, 2 crops | **Identical** |

<!-- parte: PART IV | Production Cutover and Upcoming Phases -->

## 12. Execution and Production Cutover

The production cutover was executed on November 4–5, 2026:
1. **Canonical Repository Reorganization**: 21 repositories reorganized; Stack B assumed canonical names (`SmartPot-API`, `SmartPot-DB`, etc.) while legacy repositories received descriptive suffixes.
2. **GHCR Publishing**: Multi-architecture images published to `ghcr.io/smartpottech/*`.
3. **Production Deployment**: Applied with PostgreSQL 17 + TimescaleDB, Valkey 9.1.3, EMQX 5.8.9, Go 1.27.3 API in `scratch`, SolidJS 1.9 PWA, Rust AI, and FastMCP server at `mcp.smartpot.app`.
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
