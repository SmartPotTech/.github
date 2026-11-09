<!-- portada
eyebrow: Platform Technical Documentation
titulo: SmartPot Platform: Technical Documentation
acento: SmartPot
subtitulo: Hydroponic Crop Monitoring and Automation Platform
bajada: Architecture, contracts, AI assistant with continuous learning, placement and weather, notification channels, physical and virtual crops, security, deployment, and operations of the platform connecting hydroponic crops with grower applications.
documento: Platform Technical Documentation
version: 1.3 · October 2026
equipo: SmartPotTech
proyecto: smartpot.app
-->

# SmartPot Platform · Plataforma SmartPot

---

## Document Summary

| Field | Value |
|---|---|
| Project | SmartPot · [smartpot.app](https://smartpot.app) |
| Organization | SmartPotTech |
| Document | Platform Technical Documentation |
| Version | 1.3 · October 2026 |
| Scope | SolidJS PWA, Go API, Rust AI inference engine, Python ADBC trainer, crop placement & weather, notification channels, EMQX broker, ESP32 firmware, physical/virtual crops, TimescaleDB storage, infrastructure, and QA |
| Source of Truth | The repository `README.md` files and interactive OpenAPI docs (`/docs`) supersede this document if discrepancies arise |
| Maintenance | Generated from `docs/SmartPot_Technical_Documentation.md`; updated with every architectural or contract change |
| Companion Document | [Project Journey](SmartPot_Project_Journey.md): inception, analysis, design, construction, and testing |

<!-- parte: PART I | Platform Overview -->

## 1. Introduction

### In Plain Words

SmartPot is a complete open-source platform for monitoring, automating, and optimizing hydroponic crops. It connects physical sensors and actuators (or simulated devices) to an intelligent backend and an installable web app (PWA), giving growers total visibility and control over their plants from any device.

### Scope and Architecture Boundaries

The platform provides end-to-end functionality across four operational tiers:
1. **Edge & Device Tier:** MicroPython and Rust Embassy ESP32 firmware publishing telemetry via MQTT with TLS and receiving actuator execution commands.
2. **Broker & Ingestion Tier:** EMQX 5.8.9 enterprise MQTT broker with in-memory HTTP webhook authentication and per-crop dynamic ACL enforcement.
3. **Core Services Tier:** High-throughput Go REST/MQTT API (`SmartPot-API`), TimescaleDB time-series database with continuous aggregates (CAGGs), and Valkey in-memory cache.
4. **Intelligence & Interface Tier:** Standalone Rust AI inference microservice (`SmartPot-AI`), offline Python model trainer (`SmartPot-Trainer`), and responsive SolidJS Progressive Web App (`SmartPot-Web`).

### Supported Plant Species

The system includes preconfigured agronomic profiles for 6 standard hydroponic crops:
- **Lettuce (*Lactuca sativa*):** Fast-growing leafy green with low nutrient density and strict tipburn prevention thresholds.
- **Tomato (*Solanum lycopersicum*):** High-nutrient fruiting crop requiring dynamic photoperiod lighting and high potassium dosing.
- **Strawberry (*Fragaria × ananassa*):** Sensitive root system requiring stable root-zone temperature and strict crown moisture control.
- **Spinach (*Spinacia oleracea*):** Cool-season crop vulnerable to bolting under high ambient temperature or light excess.
- **Bell Pepper (*Capsicum annuum*):** Warm-season crop demanding consistent EC/TDS nutrient levels and moderate humidity.
- **Basil (*Ocimum basilicum*):** Highly aromatic herb requiring intensive light exposure and warm root temperatures.

## 2. System Architecture (Canonical Stack B)

<!-- diagrama: SmartPot_01_Architecture | titulo=SmartPot Platform Architecture (Stack B) | lamina=H -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart LR
  subgraph campo["Reading Sources"]
    maceta["Physical Crop · ESP32<br/>Rust Embassy / MicroPython"]
    wokwi["Physical Crop · Wokwi<br/>Simulated Firmware"]
    sim["Virtual Crops · Rust<br/>SmartPot-DataGenerator"]
  end
  subgraph usuario["Users and Agents"]
    pwa["SolidJS PWA<br/>SmartPot-Web"]
    tg["Telegram"]
    mcp["FastMCP Server<br/>SmartPot-MCP"]
  end
  subgraph plataforma["SmartPot Platform (Stack B)"]
    broker["MQTT Broker EMQX 5.8.9.9.9<br/>SmartPot-Broker"]
    api["REST & MQTT API Go 1.27.3<br/>SmartPot-API"]
    ai["AI Inference · Rust 1.88+<br/>SmartPot-AI"]
    trainer["AI Trainer · Python >=3.13+<br/>SmartPot-Trainer"]
    db[("PostgreSQL 17 + TimescaleDB 2.17.2.2 2.17.2<br/>SmartPot-DB")]
    cache[("Valkey 9.1.3.3.3<br/>SmartPot-Cache")]
    mail["Mailpit v1.33.0 v1.33.0 Mail<br/>SmartPot-Mail"]
  end
  weather["Open-Meteo<br/>Current Weather"]
  maceta <-->|"MQTT TLS 8883<br/>Telemetry · Commands · ACK"| broker
  wokwi <-->|"MQTT TLS"| broker
  sim <-->|"Internal MQTT"| broker
  weather -.->|"Local Weather"| sim
  broker <-->|"Internal MQTT"| api
  broker -.->|"Delegated Authn"| api
  pwa -->|"HTTPS · REST + SSE"| api
  mcp -->|"REST + spt_... token"| api
  api -->|"Simulations & Weather<br/>with Token"| sim
  api -->|"gRPC / REST + Token<br/>Agronomic Inference"| ai
  db -.->|"ADBC Reading"| trainer
  trainer -.->|"JSON Models Ed25519"| ai
  api -->|"Hypertables & Series"| db
  api -->|"Rate Limits & Cache"| cache
  api -->|"SMTP"| mail
  api -->|"Alerts · Digests · Bot"| tg
  classDef device fill:#FBE9E1,stroke:#B85A38,color:#17261F
  classDef edge fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef core fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  classDef data fill:#F2F7F4,stroke:#5B6B63,color:#17261F
  classDef brain fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef app fill:#DDF5EA,stroke:#067A52,color:#17261F
  class maceta,wokwi,sim device
  class broker,weather edge
  class api core
  class db,cache,mail data
  class ai,trainer brain
  class pwa,tg,mcp app
```

### Component Topology

<!-- diagrama: SmartPot_12_Components | titulo=Component Decoupling and Communication Flow -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TB
  subgraph web["SmartPot-Web · SolidJS PWA"]
    w1["Panel general · Cultivos<br/>Control · Acciones"]
    w2["Asistente · Aprendizaje (SSE)"]
    w3["Nuevo cultivo · Ilustración viva<br/>Simulation · Profile & MCP Connections"]
  end
  subgraph api["SmartPot-API · Go (Echo)"]
    a1["security · auth (HttpOnly/CSRF) · users"]
    a2["crops · readings · actuators · commands"]
    a3["mqtt gateway · authn delegada"]
    a4["ai client (gRPC/REST) · agente"]
    a5["notifications · channels · telegram"]
    a6["virtualdevices · overview · connections"]
  end
  subgraph ai["SmartPot-AI · Rust"]
    i1["Inferencia: diagnóstico, 21 reglas,<br/>Sugeno fuzzy logic, native ML models"]
  end
  subgraph trainer["SmartPot-Trainer · Python"]
    t1["Aprendizaje: ADBC Reading TimescaleDB,<br/>entrenamiento offline, firma Ed25519"]
  end
  subgraph sim["SmartPot-DataGenerator · Rust"]
    s1["pots · environment · weather · api Axum"]
  end
  web -->|"REST + SSE"| api
  a3 <-->|"MQTT"| broker["SmartPot-Broker · EMQX"]
  broker -.->|"Delegated Authn"| a3
  s1 <-->|"MQTT"| broker
  a4 -->|"gRPC / REST"| ai
  t1 -.->|"modelos JSON"| ai
  a6 -->|"HTTP + token"| sim
  a5 -->|"Bot API"| tg["Telegram"]
  classDef box fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef ext fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef train fill:#FDF4DD,stroke:#C98D12,color:#17261F
  class w1,w2,w3,a1,a2,a3,a4,a5,a6,i1,s1 box
  class t1 train
  class broker,tg ext
```

The production architecture is completely decoupled into modular microservices running in isolated, rootless Docker containers:

| Service / Container | Technology & Runtime | Primary Architectural Role | Port / Binding |
|---|---|---|---|
| `smartpot-api` | Go 1.27.3 / Echo / pgx v5.12.0 | Core REST API, MQTT gateway, authentication, and command orchestrator | `127.0.0.1:8091` (HTTP) |
| `smartpot-db` | PostgreSQL 17 + TimescaleDB 2.17.2 | Relational metadata, time-series hypertables, continuous aggregates | Internal `5432` |
| `smartpot-cache` | Valkey 9.1.3.3 (Alpine) | Session storage, rate limiting tokens, singleflight cache, and telemetry cache | Internal `6379` |
| `smartpot-broker` | EMQX 5.8.9.9 (Erlang) | MQTT v1 broker with webhook authentication and dynamic per-crop ACLs | `127.0.0.1:1883` / `8083` |
| `smartpot-web` | SolidJS 1.9 / Vite / Tailwind CSS | High-performance reactive PWA served via unprivileged Nginx | `127.0.0.1:5173` |
| `smartpot-ai` | Rust 1.88+ / Tokio / Axum 0.8 | Deterministic inference engine, 21 agronomic rules, and Sugeno fuzzy logic | Internal `50051` (gRPC) / `8002` (REST) |
| `smartpot-trainer` | Python >=3.13 / Arrow ADBC / Scikit | Periodic offline model training with Ed25519 cryptographic signing | Internal worker (no exposed ports) |
| `smartpot-simulator` | Rust 1.88+ / Tokio / Axum 0.8 | Background multi-pot physics simulator with real-time weather integration | Internal `8082` |
| `smartpot-mail` | Mailpit v1.33.0 v1.33.0 (Alpine) | Local SMTP testing server and email recovery inbox | `127.0.0.1:8025` (UI) |

### Key Architectural Decisions

1. **Hexagonal Architecture:** Complete separation of domain entities from external storage, network protocols, and third-party APIs.
2. **Hypertables and Continuous Aggregates:** Telemetry stored in TimescaleDB partitioned chunks with automated 1m, 15m, and 1h CAGGs and 365-day retention.
3. **In-Memory Broker Webhooks:** Device authentication delegated to the API via internal HTTP webhooks cached in Valkey, avoiding disk-based ACL corruption.
4. **Rust Inference Microservice:** High-speed, zero-GC analytical inference delivering sub-millisecond evaluation without JVM overhead.

## 3. Reading Lifecycle (Telemetry Ingestion)

<!-- diagrama: SmartPot_02_Reading_Sequence | titulo=Telemetry Ingestion and Automated Action Sequence -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
sequenceDiagram
  autonumber
  participant M as Device
  participant B as MQTT Broker
  participant A as API
  participant D as PostgreSQL / TimescaleDB
  participant I as AI Assistant
  participant U as PWA
  M->>B: telemetry {temperature, humidity, ph, …}
  B->>A: delivers reading (crop tenant account)
  A->>A: validates physical ranges and rate-limits to 1 per 5s
  A->>D: persists reading to hypertable
  A-)I: evaluates reading + history + actuators + local time
  I-->>A: health, diagnosis, conclusions, predictions & actions
  A->>D: updates crop health index
  alt Automatic mode and actuator off cooldown
    A->>D: creates command (PENDING)
    A->>B: commands {id, actuator, action, durationSeconds}
    B->>M: command QoS 1
    M->>B: commands/ack {id, status: EXECUTED}
    B->>A: confirms
    A->>D: command EXECUTED and updates actuator state
  else Recommendation only
    A->>D: alert to owner on critical findings
  end
  U->>A: GET /api/v1/crops/{id}/insights
  A-->>U: agronomic diagnosis and recommendations
```

1. **Measurement & Publication:** The device (or simulator) samples sensors, applies calibration offsets, and publishes a JSON payload to `smartpot/v1/{cropId}/readings` with QoS 1.
2. **Broker Authorization:** EMQX queries the internal webhook (`/api/v1/mqtt/authn`). If valid, the packet is forwarded; otherwise, the connection is immediately terminated.
3. **Ingestion & Validation:** The API MQTT gateway receives the message, parses the payload without dynamic allocations, and verifies physical range constraints.
4. **Persistence & Caching:** The reading is written to the TimescaleDB `readings` hypertable and cached in Valkey (`crops:{id}:latest`).
5. **Analytical Evaluation:** The API invokes `SmartPot-AI` via gRPC/REST. The engine computes variable diagnostic states, fuzzy health index, and Theil-Sen trend slope.
6. **Closed-Loop Rule Execution:** If automatic mode is enabled and parameters violate safe thresholds, the rule agent checks actuator cooldown and generates an execution command.
7. **Client Delivery:**
<!-- diagrama: SmartPot_13_Control_Activity | titulo=Closed-Loop Telemetry and Command Execution Activity Flow -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TB
  inicio(["Device or Simulator<br/>Publishes Reading"]) --> valida{"Values within<br/>physical bounds?"}
  valida -->|"No"| descarta["Discarded and logged"]
  valida -->|"Sí"| guarda["Persist reading to hypertable<br/>and mark crop online"]
  guarda --> aprende["If real crop, enqueue<br/>for continuous learning"]
  guarda --> evalua{"Evaluation trigger?<br/>30s in auto · 5min in manual"}
  evalua -->|"No"| fin(["Fin"])
  evalua -->|"Sí"| ia["Assistant evaluates:<br/>Diagnosis, forecast, models,<br/>expert system & reactive agent"]
  ia --> critico{"Critical finding?"}
  critico -->|"Sí"| alerta["Notification in PWA<br/>and linked channels"]
  critico -->|"No"| auto
  alerta --> auto{"Automatic mode enabled?"}
  auto -->|"No"| fin
  auto -->|"Sí"| enfria{"Actuator off<br/>cooldown period?"}
  enfria -->|"No"| fin
  enfria -->|"Sí"| comando["Command via MQTT (QoS 1)"]
  comando --> ack{"ACK received within 2 min?"}
  ack -->|"EXECUTED"| ok["Command EXECUTED<br/>and action confirmation recorded"]
  ack -->|"Sin respuesta"| vence["EXPIRED and owner alerted"]
  ok --> fin
  vence --> fin
  classDef start fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  classDef step fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef ask fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef bad fill:#FBE9E1,stroke:#B85A38,color:#17261F
  class inicio,fin start
  class guarda,aprende,ia,alerta,comando,ok step
  class valida,evalua,critico,auto,enfria,ack ask
  class descarta,vence bad
```
 Connected PWA clients receive instant state updates via Server-Sent Events (SSE) or polling.

<!-- parte: PART II | Contracts and Interfaces -->

## 4. MQTT Contract (v1)

### Topic Taxonomy

All MQTT communication follows a strict topic hierarchy:
- **Telemetry Ingestion:** `smartpot/v1/{cropId}/readings` (Publish: Device, Subscribe: API)
- **Device Lifecycle:** `smartpot/v1/{cropId}/status` (Retained Last Will and Testament, `online` / `offline`)
- **Command Dispatch:** `smartpot/v1/{cropId}/actuators/{actuatorType}/command` (Publish: API, Subscribe: Device)
- **Command Acknowledgment:** `smartpot/v1/{cropId}/actuators/{actuatorType}/ack` (Publish: Device, Subscribe: API)

### Payload Structure

```json
{
  "version": 1,
  "cropId": "507f1f77bcf86cd799439011",
  "measuredAt": "2026-10-31T14:30:00Z",
  "measures": {
    "temperature": 21.4,
    "humidity": 64.2,
    "brightness": 1250.0,
    "ph": 6.12,
    "tds": 720.0,
    "atmosphere": 1013.25,
    "soilMoisture": 58.5
  }
}
```

## 5. REST API Specification

### Core Endpoints

| Method | Endpoint | Description | Access Level |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user account | Public (Rate-limited) |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue HttpOnly JWT cookies | Public (10 req/min limit) |
| `POST` | `/api/v1/auth/logout` | Revoke session and clear cookies | Authenticated |
| `GET` | `/api/v1/crops` | List all crops owned by the authenticated user | Authenticated |
| `POST` | `/api/v1/crops` | Create a new crop (real or virtual) | Authenticated (Quota enforced) |
| `GET` | `/api/v1/crops/{id}` | Retrieve detailed crop metadata and health status | Authenticated (Owner only) |
| `PUT` | `/api/v1/crops/{id}` | Update crop settings, mode, and placement | Authenticated (Owner only) |
| `DELETE`| `/api/v1/crops/{id}` | Delete crop, associated readings, and MQTT access | Authenticated (Owner only) |
| `GET` | `/api/v1/crops/{id}/readings/latest` | Retrieve latest telemetry measurement | Authenticated (Owner only) |
| `GET` | `/api/v1/crops/{id}/readings/series` | Query aggregated historical timeseries | Authenticated (Owner only) |
| `POST` | `/api/v1/crops/{id}/commands` | Dispatch actuator execution command | Authenticated (Owner only) |
| `POST` | `/api/v1/crops/{id}/device/key` | Generate or rotate device authentication key | Authenticated (Owner only) |
| `GET` | `/api/v1/overview` | Aggregated dashboard across all user crops | Authenticated |

### Command Lifecycle

<!-- diagrama: SmartPot_05_Command_States | titulo=Command Lifecycle State Machine -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
stateDiagram-v2
  [*] --> PENDING: Valid order from user or agent
  PENDING --> SENT: Published to commands (QoS 1)
  PENDING --> FAILED: Broker unavailable
  SENT --> EXECUTED: Device ACK EXECUTED
  SENT --> FAILED: Device ACK FAILED
  SENT --> EXPIRED: No ACK within 2 minutes
  EXECUTED --> [*]: Updates actuator state
  FAILED --> [*]
  EXPIRED --> [*]: Alerts owner
```

Commands transition through a deterministic finite-state machine (FSM):
1. **`PENDING`:** Command created in the database and single-in-flight constraint checked.
2. **`SENT`:** Dispatched to the EMQX broker with QoS 1.
3. **`EXECUTED`:** Acknowledged by the device with success confirmation.
4. **`FAILED`:** Rejected by the device due to hardware failure or constraint violation.
5. **`EXPIRED`:** Automatically expired if no acknowledgment arrives within 120 seconds.

<!-- parte: PART III | Intelligence and Operations -->

## 6. AI Assistant & Reasoning Engine

<!-- diagrama: SmartPot_03_AI_Assistant | titulo=AI Assistant Agronomic Decision Pipeline -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TB
  req["Current Reading<br/>+ History (48)<br/>+ Actuators<br/>+ Local Time<br/>+ Outdoor Weather"] --> diag["Per-Variable Diagnosis<br/>LOW · OPTIMAL · HIGH · REST"]
  req --> fc["Theil-Sen Forecast<br/>Trend & Hours to Boundary"]
  req --> lr["Continuous Learning<br/>Models Trained on Real Readings"]
  diag --> norm["Normalization<br/>against Profile"]
  norm --> ml["Base Models<br/>Logistic Regression · MLP · Isolation Forest"]
  diag --> mem["Working Memory<br/>Status & Severity Facts"]
  ml --> mem
  fc --> mem
  lr --> mem
  fc --> ag
  lr --> ag
  req -.->|"lugar · weather"| mem
  mem --> es["Expert System<br/>Forward Chaining"]
  diag --> place["Placement Advice<br/>Species Light Requirements"]
  req --> place
  diag --> fz["Sugeno Fuzzy Logic<br/>Health Index 0–100"]
  es --> ag["Reactive Agent<br/>Per-Actuator Actions"]
  diag --> ag
  ml --> ag
  fz --> out["Response<br/>health · diagnosis · conclusions · predictions<br/>forecasts · learning · placement · actions"]
  es --> out
  ag --> out
  lr --> out
  place --> out
  classDef input fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef step fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef brain fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef result fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  class req input
  class diag,norm,mem step
  class ml,es,fz,ag,fc,lr,place brain
  class out result
```

### Multi-Tier Reasoning Pipeline

1. **Per-Variable Diagnosis:** Immediate evaluation of incoming sensor measurements against the species-specific agronomic tolerance band (`OPTIMAL`, `ACCEPTABLE`, `WARNING`, `CRITICAL`).
2. **21-Rule Expert System:** Heuristic rules covering agronomic conditions (e.g., pH lockouts, photoperiod lighting, high heat alerts, dry substrate warnings).
3. **Sugeno Fuzzy Health Index:** Multi-variable continuous scoring mapping telemetry into a scalar health rating from 0 to 100 across 5 tiers:
   - `90 – 100`: Optimal (Pristine crop conditions)
   - `75 – 89`: Good (Minor parameter variances)
   - `60 – 74`: Fair (Parameters requiring attention)
   - `40 – 59`: Poor (Active physiological stress)
   - `0 – 39`: Critical (Immediate crop mortality risk)
4. **Theil-Sen Robust Trend Slope:** Non-parametric linear regression estimating parameter trajectory over a 30-minute sliding window, resistant to transient sensor outliers.
5. **Fleet Cluster Analysis:** K-Means clustering identifying recurring operational states across historical crop cohorts.
6. **Continuous Offline Learning:**
<!-- diagrama: SmartPot_16_Learning | titulo=Continuous Learning and Cryptographic Model Deployment -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TB
  subgraph prep["1 · Datos"]
    direction LR
    lect["Lecturas reales<br/>lotes cada minuto"] --> alm[("SQLite en /data<br/>pseudonymized crop")]
    alm --> cal["Calidad de datos<br/>completitud · validez · IQR"]
    cal --> var["Variables<br/>position in range, circular hour,<br/>tendencia de 30 min"]
  end
  subgraph sup["2 · Supervisado"]
    direction LR
    eti["Etiquetas autosupervisadas<br/>outcome in subsequent hour?"] --> cv["7 modelos con<br/>TimeSeriesSplit<br/>+ baseline"]
    cv --> gs["GridSearchCV<br/>del mejor"]
    gs --> cc{"¿Supera a la baseline<br/>y al vigente en lo<br/>most recent?"}
    cc -->|"Sí"| nuevo["Campeón nuevo<br/>version + joblib artifact"]
    cc -->|"No"| vig["Se conserva<br/>el vigente"]
  end
  subgraph nosup["3 · No supervisado"]
    direction LR
    km["K-Means por silueta<br/>operational states"]
    iso["Isolation Forest<br/>atypical / anomalous readings"]
  end
  var --> eti
  var --> km
  var --> iso
  inf["4 · Cada evaluación: riego y calor en 1 h, sustrato en 1 h, estado y atipicidad"]
  nuevo --> inf
  vig --> inf
  km --> inf
  iso --> inf
  classDef data fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef step fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef ask fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef out fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  class lect,alm data
  class cal,var,eti,cv,gs,km,iso,vig step
  class cc ask
  class nuevo,inf out
```
 Periodic batch training using scikit-learn and Arrow ADBC, outputting signed model artifacts (`.smartpot`) verified with Ed25519 signatures.

## 7. Data Model and Storage

<!-- diagrama: SmartPot_04_Data_Model | titulo=PostgreSQL 17 and TimescaleDB 2.17.2.2 Entity Relationship Model | lamina=H -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
erDiagram
  USERS ||--o{ CROPS : "es owner de"
  USERS ||--o{ NOTIFICATIONS : "recibe"
  USERS ||--o{ PASSWORD_RESET_TOKENS : "solicita"
  USERS ||--o{ CHANNEL_LINKS : "vincula"
  CROPS ||--o{ READINGS : "registra"
  CROPS ||--o{ ACTUATORS : "tiene"
  CROPS ||--o{ COMMANDS : "recibe"
  CROPS ||--o{ NOTIFICATIONS : "genera"
  CROPS ||--o| VIRTUAL_DEVICES : "simula"
  CROPS ||--o{ CROP_CHANNELS : "avisa por"
  ACTUATORS ||--o{ COMMANDS : "ejecuta"
  USERS {
    ObjectId _id
    string name
    string lastName
    string email "single"
    string passwordHash "BCrypt 12"
    string role "USER o ADMIN"
  }
  CROPS {
    ObjectId _id
    ObjectId ownerId
    string name
    string type "LETTUCE, TOMATO, …"
    string kind "REAL o VIRTUAL, fijo"
    string form "POT, NFT, TOWER, RAFT"
    object placement "INDOOR or OUTDOOR, Sun Exposure, Location"
    bool automationEnabled
    object device "keyCiphertext AES-GCM, online, lastSeenAt"
    object health "index, level, label, evaluatedAt"
  }
  READINGS {
    ObjectId _id
    ObjectId cropId
    date measuredAt "TTL 365 days"
    object measures "7 variables"
    string source "MQTT o HTTP"
  }
  ACTUATORS {
    ObjectId _id
    ObjectId cropId
    string type "WATER_PUMP, UV_LIGHT, FAN, …"
    bool active "indefinite activation"
    date runningUntil "si corre por tiempo"
  }
  COMMANDS {
    ObjectId _id
    ObjectId cropId
    ObjectId actuatorId
    string action "ACTIVATE o DEACTIVATE"
    string status "PENDING … EXPIRED"
    string source "USER o AGENT"
  }
  NOTIFICATIONS {
    ObjectId _id
    ObjectId userId
    ObjectId cropId
    string type "INFO, ALERT, COMMAND, DEVICE, AI"
    bool read
  }
  CHANNEL_LINKS {
    ObjectId _id
    ObjectId userId
    string type "TELEGRAM"
    string address "id del chat"
    bool enabled
    array events "tipos elegidos"
  }
  CROP_CHANNELS {
    ObjectId _id
    ObjectId cropId
    string type "TELEGRAM"
    array events "tipos que avisa"
    string delivery "INSTANT o DIGEST"
    int digestHours "1 a 24"
    string dailySummaryAt "HH:mm"
    array recipients "hasta 10 chats"
  }
  VIRTUAL_DEVICES {
    ObjectId _id
    ObjectId cropId "single"
    ObjectId ownerId
    string mode "AUTO, MANUAL, WEATHER"
    object manual "medidores"
    object location "prior to crop location"
    bool active "false en pausa"
  }
  PASSWORD_RESET_TOKENS {
    ObjectId _id
    ObjectId userId
    string tokenHash "SHA-256"
    date expiresAt "TTL"
  }
```

### Schema Design (PostgreSQL / TimescaleDB)

- **`users`:** Identity accounts, Argon2id password hashes, role permissions, and created timestamps.
- **`crops`:** Crop metadata, species type, structural form (Pot, NFT, Tower, Raft), placement, automation flags, and owner foreign key.
- **`devices`:** Device keys encrypted with AES-256-GCM, online heartbeat status, and `last_seen_at` timestamps.
- **`readings`:** TimescaleDB hypertable partitioned by `measured_at` (7-day chunk interval) storing floating-point sensor measures.
- **`actuators`:** Physical/virtual actuator states (Water Pump, UV Light, Fan, Heater, pH Dispenser, Nutrient Dispenser).
- **`commands`:** Command execution log with single-in-flight partial unique index (`commands_one_inflight_per_actuator`).
- **`notifications`:** In-app notification records with read/unread tracking and severity classification.
- **`virtual_devices`:** Simulation configuration, weather coordinates, and manual sensor overrides.

## 8. Web Application (SolidJS PWA)

<!-- diagrama: SmartPot_32_PWA_Sitemap | titulo=SolidJS PWA Sitemap and Route Structure -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart LR
  inicio["/ · Public Landing<br/>Indexable"] --> ingreso["/login · /register<br/>/forgot-password"]
  ingreso --> panel["/app · Overview Dashboard"]
  panel --> cultivos["/app/crops · My Crops"]
  cultivos --> nuevo["New Crop<br/>Real or Virtual · Species · Form"]
  cultivos --> detalle["/app/crops/:id"]
  detalle --> hero["Dynamic Crop Scene<br/>Across All Sub-Tabs"]
  hero --> t1["Summary"] & t2["AI Assistant"] & t3["Control"] & t4["History"] & t5["Device<br/>Physical Only"] & t6["Simulation<br/>Virtual Only"] & t7["Settings"]
  panel --> control["/app/control · Fleet Control"]
  panel --> acciones["/app/actions · Actions"]
  panel --> aprendizaje["/app/learning · Learning"]
  panel --> alertas["/app/notifications · Notifications"]
  panel --> perfil["/app/profile · Profile & Telegram"]
  classDef leaf fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef water fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef sun fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef clay fill:#FBE9E1,stroke:#B85A38,color:#17261F
  classDef core fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  classDef deep fill:#0B3D2B,stroke:#06281C,color:#FFFFFF
  classDef muted fill:#F2F7F4,stroke:#5B6B63,color:#17261F
  class inicio,ingreso water
  class panel core
  class cultivos,control,acciones,aprendizaje,alertas,perfil leaf
  class detalle,nuevo sun
  class hero leaf
  class t1,t2,t3,t4,t5,t6,t7 muted
```

Built with **SolidJS** for high-frequency fine-grained DOM reactivity without virtual DOM reconciliation:
- **PWA Capabilities:** Fully installable across mobile (Android, iOS) and desktop with service worker offline shell.
- **Reactive State Stores:** Telemetry and crop status managed through granular SolidJS signals and stores.
- **Dynamic SVG Crop Visualization:** Custom SVG illustration reflecting plant growth, crop form, weather lighting, and real-time active actuator animations.
- **Accessibility:**
<!-- diagrama: SmartPot_37_Crop_Alerts | titulo=Per-Crop Notification Channel and Telegram Bot Flow -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
sequenceDiagram
  autonumber
  participant P as User
  participant W as PWA
  participant A as API
  participant D as MongoDB
  participant T as Telegram
  participant C as Shared Chat
  P->>W: Settings del cultivo › Avisos por Telegram
  W->>A: PUT /crops/{id}/channels/TELEGRAM (eventos, entrega, resumen diario)
  A->>D: persists crop_channels
  P->>W: Share with another chat
  W->>A: POST /crops/{id}/channels/TELEGRAM/recipients
  A-->>W: link t.me/bot?start=code · single-use · 10 min
  C->>T: opens link and starts bot
  T->>A: /start code (webhook or polling)
  A->>D: adds chat to recipients (up to 10)
  A->>T: "You will now receive alerts for Balcony Lettuce"
  Note over A: Crop notification received
  alt Instant Delivery
    A->>T: alert to owner chat and shared recipients
  else Digest Delivery
    A->>D: queued for digest
    A->>T: digest every 1 to 24h with queued alerts
  end
  A->>T: daily digest at configured hour with health, telemetry & 24h recap
```
 Fully compliant with WCAG 2.1 AA contrast requirements and screen reader labels.

## 9. Real and Virtual Crops

<!-- diagrama: SmartPot_15_Virtual_Crop_Sequence | titulo=Virtual Crop Simulation and Parity Sequence -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
sequenceDiagram
  autonumber
  participant P as User
  participant W as PWA
  participant A as API
  participant S as Simulador
  participant O as Open-Meteo
  participant B as Broker
  P->>W: Nuevo cultivo › Virtual › Balsa flotante › al aire libre · Clima real · Medellín
  W->>A: POST /crops {kind: VIRTUAL, form, placement, virtual}
  A->>A: hasta 5 virtuales · el modo weather exige lugar
  A->>A: cultivo, seis actuadores y cuenta MQTT
  A->>S: PUT /v1/pots/{id} (key, mode, location & exposure)
  A-->>W: 201 sin credenciales: no hay nada que configurar
  S->>O: current weather (10 min cache)
  S->>B: conecta con la cuenta del cultivo
  loop cada intervalo
    S->>B: telemetría con el weather filtrado por el lugar y los actuadores encendidos
    B->>A: reading → assistant → agent (excluded from learning)
  end
  P->>W: Control › switch de la bomba de agua · 15 s
  W->>A: POST /crops/{id}/commands
  A->>B: comando
  B->>S: comando
  S->>B: ACK «Bomba de agua encendida por 15 s»
  S->>B: lectura nueva a los 2 s con el sustrato más húmedo
  W->>A: GET /crops/{id}/virtual-device
  A-->>W: weather, lecturas y actuadores encendidos
  W-->>P: la ilustración muestra la bomba en marcha
  Note over A,S: Pausar conserva la configuración · cada minuto<br/>la API recrea las simulaciones activas que falten
```

- **Physical Microcontroller (ESP32):** Real hardware running MicroPython or Rust Embassy connected over Wi-Fi with TLS.
- **Wokwi Cloud Simulation:** In-browser simulation environment executing identical firmware binary against the live platform.
- **Built-in Virtual Crops:** High-efficiency Rust background simulator modeling multi-pot physics, solar cycles, and real-world outdoor weather via Open-Meteo API.

## 10. Security Architecture

<!-- diagrama: SmartPot_07_Networks | titulo=Network Isolation and Port Ingress Topology -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart LR
  internet(("Internet"))
  subgraph host["Host Server"]
    nginx["Nginx :443"]
    subgraph public["Public Network"]
      web["web-smartpot<br/>127.0.0.1:5173"]
      api["api-smartpot<br/>127.0.0.1:8091"]
      broker["broker-smartpot<br/>0.0.0.0:8883 TLS · 127.0.0.1:9001 WS"]
      mail["mail-smartpot<br/>127.0.0.1:8025"]
      sim["simulator-smartpot<br/>No Ingress · Egress Only"]
    end
    subgraph internal["Internal Network · No Internet Egress"]
      db[("db-smartpot :27017")]
      cache[("cache-smartpot :6379")]
      ai["ai-smartpot :8000<br/>volumen ai_data"]
    end
  end
  internet -->|"HTTPS"| nginx
  internet -->|"MQTT TLS 8883"| broker
  nginx --> web
  nginx --> api
  nginx -->|"wss /mqtt"| broker
  nginx --> mail
  api --> db
  api --> cache
  api --> ai
  api -->|"8081 con token"| sim
  sim -->|"1883"| broker
  sim -.->|"weather"| internet
  api -.->|"Telegram Bot API"| internet
  api -->|"1883"| broker
  api -->|"SMTP 1025"| mail
  classDef pub fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef priv fill:#F2F7F4,stroke:#5B6B63,color:#17261F
  classDef gate fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  classDef world fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  class web,api,broker,mail,sim pub
  class db,cache,ai priv
  class nginx gate
  class internet world
```

- **Zero-Trust BOLA Protection:** All API endpoints strictly validate that requested resources belong to the authenticated caller.
- **Constant-Time Cryptography:** Token comparisons and device key verifications execute via `subtle.ConstantTimeCompare` to defeat timing side-channel attacks.
- **Ephemeral JWT Sessions:** Signed HS256 tokens transported in HttpOnly, SameSite=Strict cookies with CSRF validation.
- **Container Isolation:** Core backend running inside an empty `scratch` container with zero OS packages, shells, or network tools.
- **Strict Network Ingress:** Production ports bound exclusively to `127.0.0.1`, fronted by Nginx with TLS termination and security headers.

## 11. Deployment and Infrastructure

<!-- diagrama: SmartPot_06_Deployment | titulo=Production Docker Compose Deployment Topology -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart TB
  subgraph github["GitHub · SmartPotTech"]
    repo["Push a main<br/>en un servicio"] --> ci["CI del repo<br/>tests · CodeQL static analysis"]
    repo --> pkg["packaging.yml<br/>imagen + SBOM + procedencia"]
    pkg --> ghcr[("GHCR<br/>registro de despliegue")]
    pkg --> hub[("Docker Hub<br/>distribution replica")]
    pkg --> dep["deploy.yml del repo<br/>request-deploy.yml"]
    dep -->|"workflow_dispatch<br/>DEPLOY_DISPATCH_TOKEN"| queue["Cola smartpot-production<br/>one executing · newest pending queued"]
    queue --> central["deploy.yml central<br/>(.github)"]
    central -.->|"resultado"| dep
    secrets["Secrets solo en .github<br/>ENV_FILE · SERVER_KEY · MQTT_*"] -.-> central
  end
  subgraph servidor["Host Server"]
    stage[".deploy-{id}<br/>compose.yaml · .env · certificados"]
    certs["SMARTPOT_CERTS_DIR<br/>certificados TLS del broker"]
    compose["docker compose -p smartpot<br/>pull + up --wait<br/>database schema migration"]
    nginx["Nginx + Let's Encrypt"]
  end
  central -->|"SSH + flock"| stage
  stage --> certs
  stage --> compose
  ghcr -->|"pull"| compose
  hub -.->|"demo a elección"| demo["Demo local<br/>compose.dockerhub.yaml"]
  central -->|"GET /health"| nginx
  classDef gh fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef key fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef srv fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef core fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  class repo,ci,pkg,dep,demo gh
  class central core
  class secrets,certs,queue key
  class stage,compose,nginx srv
```

- **Environment Profiles:** Pre-configured Docker Compose setups for `demo` (local all-in-one), `dev` (hot-reloading), and `production` (hardened multi-container).
- **CI/CD Automation:** Centralized GitHub Actions pipelines running linting, unit tests, integration tests, Snyk security scans, and container image generation with SBOM attestations.
- **Kubernetes Ready:** Declarative Kubernetes manifests (`k8s-deployment.yml`) with immutable image pull policies and strict resource quotas.

## 12. Quality Assurance and Testing

<!-- diagrama: SmartPot_08_QA | titulo=Automated QA Verification Pipeline -->

```mermaid
%%{init: {"theme": "base", "fontFamily": "Segoe UI, Arial, sans-serif", "themeVariables": {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "15px", "primaryColor": "#DDF5EA", "primaryTextColor": "#17261F", "primaryBorderColor": "#067A52", "secondaryColor": "#E3F2FB", "secondaryTextColor": "#17261F", "secondaryBorderColor": "#1F6FA0", "tertiaryColor": "#F2F7F4", "tertiaryTextColor": "#17261F", "tertiaryBorderColor": "#D5E3DC", "lineColor": "#5B6B63", "textColor": "#17261F", "mainBkg": "#DDF5EA", "nodeBorder": "#067A52", "clusterBkg": "#F7FAF8", "clusterBorder": "#D5E3DC", "edgeLabelBackground": "#FFFFFF", "actorBkg": "#067A52", "actorBorder": "#0B3D2B", "actorTextColor": "#FFFFFF", "actorLineColor": "#5B6B63", "signalColor": "#17261F", "signalTextColor": "#17261F", "labelBoxBkgColor": "#0B3D2B", "labelBoxBorderColor": "#0B3D2B", "labelTextColor": "#FFFFFF", "loopTextColor": "#0B3D2B", "noteBkgColor": "#FDF4DD", "noteBorderColor": "#C98D12", "noteTextColor": "#17261F", "activationBkgColor": "#DDF5EA", "activationBorderColor": "#067A52", "attributeBackgroundColorOdd": "#FFFFFF", "attributeBackgroundColorEven": "#F2F7F4"}}}%%
flowchart LR
  trigger["Push · Pull Request<br/>· Scheduled · Manual"] --> api["API<br/>Go Test & Echo Verify"]
  trigger --> web["Web<br/>Lint · Types · Vitest · Build"]
  trigger --> py["AI · DataGenerator · IoT<br/>Cargo Test · Pytest · Ruff"]
  trigger --> ct["Broker · DB · Cache · Mail<br/>Image + Smoke Tests"]
  api --> e2e["End-to-End<br/>8 Containers + Full Demo"]
  web --> e2e
  py --> e2e
  ct --> e2e
  e2e --> flow["registro → cultivo → telemetría MQTT → comando con ACK → switches<br/>→ assistant → location & weather → overview dashboard<br/>→ bulk commands → virtual crop → continuous learning<br/>→ canales and per-crop notifications → borrado"]
  classDef start fill:#E3F2FB,stroke:#1F6FA0,color:#17261F
  classDef job fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef final fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  classDef detail fill:#FDF4DD,stroke:#C98D12,color:#17261F
  class trigger start
  class api,web,py,ct job
  class e2e final
  class flow detail
```

Comprehensive multi-tiered testing certifies the integrity of all 13 Stack B repositories:
- Unit test coverage exceeding 85% across all core business logic.
- Automated end-to-end (E2E) integration harness executing 101 multi-service operational scenarios.
- Forensic zero-trust compliance verification certifying zero dead code, zero false positives, and 100% real test execution.

## 13. System Operations

- **Healthchecks:** Deep multi-service health probes verifying database connectivity, cache response times, and broker reachability.
- **Observability:** Structured JSON logging (`slog` in Go, `tracing` in Rust) with correlation request IDs.
- **Disaster Recovery:** Automated backup script (`backup_smartpot.sh`) with file locks, partial staging, SHA-256 manifests, and tested restore runbooks.

## 14. Technical Glossary

- **BOLA (Broken Object Level Authorization):** Vulnerability where an authenticated user accesses another user's objects; completely mitigated in SmartPot.
- **CAGG (Continuous Aggregate):** TimescaleDB pre-aggregated materialized views refreshing on a sliding window for high-performance charting.
- **EC / TDS:** Electrical Conductivity and Total Dissolved Solids, measuring nutrient density in the hydroponic water reservoir.
- **Hypertable:** TimescaleDB partitioned time-series table behaving like a single PostgreSQL table while optimizing chunk storage.
- **QoS (Quality of Service):** MQTT delivery guarantee level; SmartPot utilizes QoS 1 (at least once) for telemetry and actuator commands.

<!-- parte: PART IV | Industrial Hardening Master Plan -->

## 15. Master Plan for Maximization and Industrial Hardening of Stack B

### 15.1 Architectural Directive: In-Place Evolution
The canonical Stack B represents the definitive industrial standard for SmartPot. All future development strictly evolves within Stack B repositories without introducing auxiliary runtimes or parallel monolithic stacks.

### 15.2 Definitively Certified Component Matrix
- Core Backend: `SmartPot-API` (Go 1.27.3 / Echo / pgx v5.12.0)
- Telemetry Database: `SmartPot-DB` (PostgreSQL 17 / TimescaleDB 2.17.2)
- Memory Cache: `SmartPot-Cache` (Valkey 9.1.3.3 Alpine)
- Message Broker: `SmartPot-Broker` (EMQX 5.8.9.9)
- Web PWA: `SmartPot-Web` (SolidJS 1.9 / Vite / Tailwind CSS)
- AI Reasoning: `SmartPot-AI` (Rust 1.88+ / Tokio / Axum 0.8)
- Model Training: `SmartPot-Trainer` (Python >=3.13 / Arrow ADBC / Scikit)
- Virtual Simulation: `SmartPot-DataGenerator` (Rust 1.88+ / Tokio / Axum 0.8)
- Edge Firmware: `SmartPot-IoT` (MicroPython & Rust Embassy ESP32)

---

<a id="español"></a>
