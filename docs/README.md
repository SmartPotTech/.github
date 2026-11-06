# SmartPot · Platform Documentation / Documentación de la plataforma

[English](#english) | [Español](#español)

---

<a id="english"></a>

# English

## Overview

| Document | Description | Format |
|---|---|---|
| Technical Platform Documentation | The platform as it runs in production (Stack B): Go/Rust/SolidJS/PostgreSQL architecture, MQTT v1/v2 and REST contracts, AI assistant and continuous learning, Telegram, MCP, real and virtual crops, crop illustrations, data lineage, PWA, firmware, security, deployment, quality, and operations | [Markdown](SmartPot_Technical_Documentation.md) · [DOCX](SmartPot_Technical_Documentation.docx) · [PDF](SmartPot_Technical_Documentation.pdf) |
| Project Journey | Requirement by requirement and diagram by diagram: what was planned during design, what was built, and how it is verified | [Markdown](SmartPot_Project_Journey.md) · [DOCX](SmartPot_Project_Journey.docx) · [PDF](SmartPot_Project_Journey.pdf) |
| Software Lifecycle | Critical analysis of each lifecycle phase: formulation & evaluation, project management, analysis, design, construction, testing, and continuous improvement, with all diagrams | [Markdown](SmartPot_Software_Lifecycle.md) · [DOCX](SmartPot_Software_Lifecycle.docx) · [PDF](SmartPot_Software_Lifecycle.pdf) |
| Quality Audit and A/B Testing | Comprehensive comparative validation of migration: REST and MQTT contract parity, resource footprint, resilience, and production cutover Quality Gates | [Markdown](SmartPot_QA_Audit_AB.md) · [DOCX](SmartPot_QA_Audit_AB.docx) · [PDF](SmartPot_QA_Audit_AB.pdf) |
| Security Scan and A/B Audit | Exhaustive AppSec and DevSecOps audit: SCA scanning with Snyk CLI, SAST, container base image analysis, OWASP API Security Top 10 assessment, IoT network isolation, and prioritized backlog | [Markdown](SmartPot_Security_Scan_AB.md) · [DOCX](SmartPot_Security_Scan_AB.docx) · [PDF](SmartPot_Security_Scan_AB.pdf) |

Markdown files are the single source of truth: GitHub renders them with diagrams, and branded DOCX and PDF documents are generated directly from them.

> [!NOTE]
> **Migration completed.** [SmartPot Migration](SmartPot_Migration.md) documents the transition from the legacy stack to the canonical Stack B (Go, PostgreSQL + TimescaleDB, Valkey, EMQX, SolidJS, Rust, FastMCP). Stack B is formally deployed and active in production at [smartpot.app](https://smartpot.app).

## Component Documentation

This folder brings together the complete platform. Each canonical repository also maintains technical documentation in `docs/` or its `README.md`, sharing the same visual identity, architectural diagrams, and contract specifications:

| Component | What it Covers | Format |
|---|---|---|
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API) | Go 1.26 (Echo), hexagonal architecture, REST endpoints, SSE, `HttpOnly` cookie + CSRF authentication, ports and adapters | [README](https://github.com/SmartPotTech/SmartPot-API/blob/main/README.md) |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) | PostgreSQL 17 + TimescaleDB 2.17, hypertables, continuous compression, real-time continuous aggregates, and read-only roles | [README](https://github.com/SmartPotTech/SmartPot-DB/blob/main/README.md) |
| [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache) | Valkey 9.1, distributed cache, concurrency control, and optional UNIX socket support | [README](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/docs/SmartPot_Cache_Documentation.md) |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker) | EMQX 5.8, MQTT broker with TLS 8883, listeners, and dynamic delegated authentication to the API | [README](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/docs/SmartPot_Broker_Documentation.md) |
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web) | SolidJS 1.9, Bun, Vite, Tailwind CSS, live SSE, deep dark mode, and reactive i18n (`es`/`en`) | [README](https://github.com/SmartPotTech/SmartPot-Web/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Web/blob/main/docs/SmartPot_Web_Documentation.md) |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI) | Rust 1.88+, Axum, Tonic gRPC, expert system, Sugeno fuzzy logic, and native ML models | [README](https://github.com/SmartPotTech/SmartPot-AI/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-AI/blob/main/docs/SmartPot_AI_Documentation.md) |
| [SmartPot-Trainer](https://github.com/SmartPotTech/SmartPot-Trainer) | Python 3.13, FastAPI, Polars, scikit-learn, Apache Arrow ADBC, and Ed25519-signed JSON models | [README](https://github.com/SmartPotTech/SmartPot-Trainer/blob/main/README.md) |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | Rust, Axum, Tokio, rumqttc, physics simulation with JSON and compact v2 binary telemetry | [README](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/docs/SmartPot_DataGenerator_Documentation.md) |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) | Rust (Embassy `no_std`, ESP32), async firmware over TLS 8883 with compact v2 binary packet | [README](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/docs/SmartPot_IoT_Documentation.md) |
| [SmartPot-IoT-Python](https://github.com/SmartPotTech/SmartPot-IoT-Python) | MicroPython 1.23, alternative firmware for rapid prototyping on physical ESP32 or Wokwi simulator | [README](https://github.com/SmartPotTech/SmartPot-IoT-Python/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-IoT-Python/blob/main/docs/SmartPot_IoT_Python_Documentation.md) |
| [SmartPot-MCP](https://github.com/SmartPotTech/SmartPot-MCP) | FastMCP, official tools for AI assistants with connection token authentication (`spt_...`) | [README](https://github.com/SmartPotTech/SmartPot-MCP/blob/main/README.md) |
| [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail) | Mailpit, authenticated SMTP and protected transactional web inbox | [README](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/docs/SmartPot_Mail_Documentation.md) |

### Historical / Legacy Components (Stack A - Deprecated)

The following repositories contain the historical v1.0 implementation (Stack A), archived for architectural reference:

| Repository | Historical Stack | Reason for Archival / Deprecation | Canonical Replacement |
|---|---|---|---|
| [SmartPot-API-Java](https://github.com/SmartPotTech/SmartPot-API-Java) | Java 21, Spring Boot 4.1, Maven | Replaced by Go API with hexagonal architecture | [`SmartPot-API`](https://github.com/SmartPotTech/SmartPot-API) |
| [SmartPot-DB-Mongo](https://github.com/SmartPotTech/SmartPot-DB-Mongo) | MongoDB 8.0/7.0, JavaScript | Replaced by PostgreSQL 17 + TimescaleDB 2.17 | [`SmartPot-DB`](https://github.com/SmartPotTech/SmartPot-DB) |
| [SmartPot-Cache-Redis](https://github.com/SmartPotTech/SmartPot-Cache-Redis) | Redis 8 | Replaced by Valkey 9.1 | [`SmartPot-Cache`](https://github.com/SmartPotTech/SmartPot-Cache) |
| [SmartPot-Broker-Mosquito](https://github.com/SmartPotTech/SmartPot-Broker-Mosquito) | Eclipse Mosquitto 2.1 | Replaced by EMQX 5.8 with delegated authn | [`SmartPot-Broker`](https://github.com/SmartPotTech/SmartPot-Broker) |
| [SmartPot-Web-React](https://github.com/SmartPotTech/SmartPot-Web-React) | React 19, Vite, pnpm | Replaced by SolidJS 1.9 PWA with SSE and Bun | [`SmartPot-Web`](https://github.com/SmartPotTech/SmartPot-Web) |
| [SmartPot-AI-Python](https://github.com/SmartPotTech/SmartPot-AI-Python) | Python, FastAPI, monolithic scikit-learn | Separated into native Rust inference and offline trainer | [`SmartPot-AI`](https://github.com/SmartPotTech/SmartPot-AI) & [`SmartPot-Trainer`](https://github.com/SmartPotTech/SmartPot-Trainer) |
| [SmartPot-DataGenerator-Python](https://github.com/SmartPotTech/SmartPot-DataGenerator-Python) | Python, NumPy | Replaced by Rust simulator with compact v2 packet | [`SmartPot-DataGenerator`](https://github.com/SmartPotTech/SmartPot-DataGenerator) |
| [SmartPot-Proxy](https://github.com/SmartPotTech/SmartPot-Proxy) | Python, FastAPI | Obsolete middleware replaced by broker architecture | [`SmartPot-Broker`](https://github.com/SmartPotTech/SmartPot-Broker) |

## Diagrams

| Diagram | Type | Documents |
|---|---|---|
| 01 Architecture | Flowchart | Technical, Lifecycle |
| 02 Reading Sequence | Sequence | Technical, Lifecycle |
| 03 AI Assistant | Flowchart | Technical, Lifecycle |
| 04 Data Model | Entity-Relationship | Technical, Lifecycle |
| 05 Command States | State Diagram | Technical, Lifecycle |
| 06 Deployment | Flowchart | Technical, Lifecycle |
| 07 Networking | Flowchart | Technical, Lifecycle |
| 08 QA | Flowchart | Technical, Lifecycle |
| 09 Cause and Effect | Flowchart | Journey, Lifecycle |
| 10 Use Cases | Use Case with Actors | Journey, Lifecycle |
| 11 Domain Classes | Class Diagram | Journey, Lifecycle |
| 12 Components | Flowchart | Journey, Lifecycle |
| 13 Automatic Control Activity | Activity | Journey, Lifecycle |
| 14 Telegram Linking | Sequence | All three |
| 15 Virtual Crop with Real Weather | Sequence | All three |
| 16 Continuous Learning | Flowchart | All three |
| 17 Project Phases | Flowchart | Journey, Lifecycle |
| 18 Problem Tree | Flowchart | Lifecycle |
| 19 Objectives Tree | Flowchart | Lifecycle |
| 20 Stakeholder Power & Interest | Quadrant Grid | Lifecycle |
| 21 Work Breakdown Structure | Flowchart | Lifecycle |
| 22 Precedence Network | Flowchart | Lifecycle |
| 23 Critical Path | Gantt | Lifecycle |
| 24 Scrum Cycle | Flowchart | Lifecycle |
| 25 Risks and Outcomes | Flowchart | Lifecycle |
| 26 System Context | C4 Level 1 | Lifecycle |
| 27 Original Design Classes | Class Diagram | Lifecycle |
| 28 Original Design Components | Flowchart | Lifecycle |
| 29 Original Activity: Send Command | Activity | Lifecycle |
| 30 Original Sequence: Historical Data | Sequence | Lifecycle |
| 31 Original Data Model | Entity-Relationship | Lifecycle |
| 32 PWA Sitemap | Flowchart | Lifecycle |
| 33 Testing Pyramid | Flowchart | Lifecycle |
| 34 PDCA Cycle | Flowchart | Lifecycle |
| 35 Improvement Cycles | Flowchart | Lifecycle |
| 36 Research Phases | Flowchart | Lifecycle |
| 37 Crop Notifications | Sequence | Technical |
| 38 Placement Advice | Flowchart | Technical, Journey |
| 39 Actuator as Switch | State Diagram | Technical |
| 40 Original Design Packages | Package Diagram | Lifecycle |
| 41 Original Design Objects | Object Diagram | Lifecycle |
| 42 Original Design Artifacts | Deployment Diagram | Lifecycle |
| 43 Original Activity: Historical Data | Activity | Lifecycle |
| 44 Original Activity: Automatic Control | Activity | Lifecycle |
| 45 Research Schedule | Gantt | Lifecycle |
| 46 A/B Architecture Comparison | Flowchart | A/B Audit |
| 47 A/B Validation Sequence | Sequence | A/B Audit |
| 48 AppSec Security Topology | Flowchart | A/B Audit |
| 49 A/B Security Comparison | Flowchart | Security A/B Audit |

## Global Diagrams

Global, unbounded diagrams showcasing the complete platform in a single image. Rendered without Mermaid character limits and available directly as high-resolution SVGs:

| Global Diagram | Description | Files |
|---|---|---|
| 01 Full Architecture | Actors, devices, network edge (UFW & Nginx), 9 containers with internal modules, ports, networks, volumes, and external services | [MMD](diagrams/SmartPot_Global_01_Architecture.mmd) · [PNG](diagrams/SmartPot_Global_01_Architecture.png) · [SVG](diagrams/SmartPot_Global_01_Architecture.svg) |
| 02 Full Operation | Sequence of 16 scenes and 150+ numbered messages: startup, registration, crop setup, telemetry, automation, AI learning, Telegram, PWA, and lifecycle | [MMD](diagrams/SmartPot_Global_02_Operation_Sequence.mmd) · [PNG](diagrams/SmartPot_Global_02_Operation_Sequence.png) · [SVG](diagrams/SmartPot_Global_02_Operation_Sequence.svg) |
| 03 Continuous Delivery | Commit-to-server lifecycle: CI, E2E QA, container publishing (GHCR & Docker Hub), centralized deployment, secrets, and environments | [MMD](diagrams/SmartPot_Global_03_Delivery.mmd) · [PNG](diagrams/SmartPot_Global_03_Delivery.png) · [SVG](diagrams/SmartPot_Global_03_Delivery.svg) |
| 04 Data Lineage | Ingestion, processing, storage (PostgreSQL/TimescaleDB, Valkey, SQLite, client state), and consumption pathways | [MMD](diagrams/SmartPot_Global_04_Data_Lineage.mmd) · [PNG](diagrams/SmartPot_Global_04_Data_Lineage.png) · [SVG](diagrams/SmartPot_Global_04_Data_Lineage.svg) |
| 05 State Machines | Sessions, MQTT credentials, actuators, health states, automated control, LoRA adaptation, and simulation lifecycle | [MMD](diagrams/SmartPot_Global_05_State_Machines.mmd) · [PNG](diagrams/SmartPot_Global_05_State_Machines.png) · [SVG](diagrams/SmartPot_Global_05_State_Machines.svg) |
| 06 Domain Model | Relational entities, hypertables, continuous aggregates, and DTO contracts | [MMD](diagrams/SmartPot_Global_06_Domain_Model.mmd) · [PNG](diagrams/SmartPot_Global_06_Domain_Model.png) · [SVG](diagrams/SmartPot_Global_06_Domain_Model.svg) |
| 07 PWA User Journey | Screen flows, client routing, API endpoints, and real-time SSE stream consumption | [MMD](diagrams/SmartPot_Global_07_User_Journey.mmd) · [PNG](diagrams/SmartPot_Global_07_User_Journey.png) · [SVG](diagrams/SmartPot_Global_07_User_Journey.svg) |
| 08 AI Decision Making | Telemetry-to-action pipeline: Sugeno fuzzy engine, ML models, 21 agronomic rules, reactive agent, and actuator dispatch | [MMD](diagrams/SmartPot_Global_08_AI_Decision.mmd) · [PNG](diagrams/SmartPot_Global_08_AI_Decision.png) · [SVG](diagrams/SmartPot_Global_08_AI_Decision.svg) |

## Regeneration

Requirements: Python 3.11+, Node.js (with `npx @mermaid-js/mermaid-cli`), Google Chrome, and LibreOffice.

```bash
python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Technical_Documentation.md docs/SmartPot_Project_Journey.md docs/SmartPot_Software_Lifecycle.md
python docs/tools/md_to_docx.py docs/SmartPot_Technical_Documentation.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Project_Journey.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Software_Lifecycle.md --pdf
python docs/tools/render_diagrams.py --global   # global diagrams only
```

---

<a id="español"></a>

# Español

# Documentación de SmartPot

| Documento | Qué cuenta | Formato |
|---|---|---|
| Documentación técnica de la plataforma | La plataforma tal como funciona en producción (Stack B): arquitectura Go/Rust/SolidJS/PostgreSQL, contratos MQTT v1/v2 y REST, asistente de IA y aprendizaje continuo, Telegram, MCP, cultivos reales y virtuales, ilustración de cada cultivo, datos, PWA, firmware, seguridad, despliegue, calidad y operación | [Markdown](SmartPot_Technical_Documentation.md) · [DOCX](SmartPot_Technical_Documentation.docx) · [PDF](SmartPot_Technical_Documentation.pdf) |
| Recorrido del proyecto | Requisito por requisito y diagrama por diagrama: qué se planeó en la fase de diseño, qué quedó construido y cómo se comprueba | [Markdown](SmartPot_Project_Journey.md) · [DOCX](SmartPot_Project_Journey.docx) · [PDF](SmartPot_Project_Journey.pdf) |
| Ciclo de vida del software | La lectura crítica de cada etapa: formulación y evaluación, gestión, análisis, diseño, construcción, pruebas y mejora continua, con todos los diagramas | [Markdown](SmartPot_Software_Lifecycle.md) · [DOCX](SmartPot_Software_Lifecycle.docx) · [PDF](SmartPot_Software_Lifecycle.pdf) |
| Auditoría de Calidad y Pruebas A/B | Validación comparativa completa de la migración: paridad de contratos REST y MQTT, huella de recursos, resiliencia y Quality Gates de corte a producción | [Markdown](SmartPot_QA_Audit_AB.md) · [DOCX](SmartPot_QA_Audit_AB.docx) · [PDF](SmartPot_QA_Audit_AB.pdf) |
| Auditoría de Seguridad A/B | Auditoría exhaustiva de seguridad AppSec y DevSecOps: escaneo SCA con Snyk CLI, SAST, análisis de contenedores, evaluación OWASP Top 10 API, topología de aislamiento IoT y backlog priorizado | [Markdown](SmartPot_Security_Scan_AB.md) · [DOCX](SmartPot_Security_Scan_AB.docx) · [PDF](SmartPot_Security_Scan_AB.pdf) |

Los Markdown son la fuente: GitHub los muestra con sus diagramas y de ellos salen los DOCX y los PDF con la identidad de SmartPot.

> [!NOTE]
> **Migración completada.** [Migración de SmartPot](SmartPot_Migration.md) documenta el proceso y las fases de transición del stack original al nuevo Stack B canónico (Go, PostgreSQL + TimescaleDB, Valkey, EMQX, SolidJS, Rust, FastMCP). El Stack B se encuentra formalmente desplegado y activo en producción en [smartpot.app](https://smartpot.app).

## Documentación de cada componente

Esta carpeta reúne la plataforma completa. Cada repositorio canónico tiene además su propia documentación técnica en `docs/` o en su `README.md`, con la misma identidad visual, diagramas de arquitectura y especificación de contratos:

| Componente | Qué cuenta | Formato |
|---|---|---|
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API) | Go 1.26 (Echo), arquitectura hexagonal, endpoints REST, SSE, autenticación por cookies `HttpOnly` + CSRF, puertos y adaptadores | [README](https://github.com/SmartPotTech/SmartPot-API/blob/main/README.md) |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) | PostgreSQL 17 + TimescaleDB 2.17, hipertablas, compresión continua, agregados en tiempo real y rol de lectura | [README](https://github.com/SmartPotTech/SmartPot-DB/blob/main/README.md) |
| [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache) | Valkey 9.1, caché distribuida, control de concurrencia y soporte de socket UNIX | [README](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Cache/blob/main/docs/SmartPot_Cache_Documentation.md) |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker) | EMQX 5.8, broker MQTT con TLS 8883, listeners y delegación dinámica de autenticación en la API | [README](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Broker/blob/main/docs/SmartPot_Broker_Documentation.md) |
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web) | SolidJS 1.9, Bun, Vite, Tailwind CSS, SSE en vivo, modo oscuro profundo, soporte i18n (`es`/`en`) | [README](https://github.com/SmartPotTech/SmartPot-Web/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Web/blob/main/docs/SmartPot_Web_Documentation.md) |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI) | Rust 1.88+, Axum, Tonic gRPC, sistema experto, lógica difusa Sugeno y modelos ML nativos | [README](https://github.com/SmartPotTech/SmartPot-AI/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-AI/blob/main/docs/SmartPot_AI_Documentation.md) |
| [SmartPot-Trainer](https://github.com/SmartPotTech/SmartPot-Trainer) | Python 3.13, FastAPI, Polars, scikit-learn, Apache Arrow ADBC y modelos firmados con Ed25519 | [README](https://github.com/SmartPotTech/SmartPot-Trainer/blob/main/README.md) |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | Rust, Axum, Tokio, rumqttc, simulación física concurrente con telemetría JSON y v2 compacta | [README](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-DataGenerator/blob/main/docs/SmartPot_DataGenerator_Documentation.md) |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) | Rust (Embassy `no_std`, ESP32), firmware asíncrono sobre TLS con paquete binario compacto v2 | [README](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-IoT/blob/main/docs/SmartPot_IoT_Documentation.md) |
| [SmartPot-IoT-Python](https://github.com/SmartPotTech/SmartPot-IoT-Python) | MicroPython 1.23, firmware alternativo para prototipado rápido en ESP32 o Wokwi | [README](https://github.com/SmartPotTech/SmartPot-IoT-Python/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-IoT-Python/blob/main/docs/SmartPot_IoT_Python_Documentation.md) |
| [SmartPot-MCP](https://github.com/SmartPotTech/SmartPot-MCP) | FastMCP, herramientas oficiales para asistentes de IA y autenticación por tokens de cuenta (`spt_...`) | [README](https://github.com/SmartPotTech/SmartPot-MCP/blob/main/README.md) |
| [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail) | Mailpit, SMTP protegido y bandeja transaccional web | [README](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/README.md) · [Markdown](https://github.com/SmartPotTech/SmartPot-Mail/blob/main/docs/SmartPot_Mail_Documentation.md) |

### Componentes Históricos / Legados (Stack A - Deprecados)

Los siguientes repositorios contienen la implementación histórica original (Stack A, v1.0), conservados como referencia arqueológica de arquitectura:

| Repositorio | Stack histórico | Motivo de archivo / Deprecación | Sustituto canónico |
|---|---|---|---|
| [SmartPot-API-Java](https://github.com/SmartPotTech/SmartPot-API-Java) | Java 21, Spring Boot 4.1, Maven | Reemplazada por la API en Go con arquitectura hexagonal | [`SmartPot-API`](https://github.com/SmartPotTech/SmartPot-API) |
| [SmartPot-DB-Mongo](https://github.com/SmartPotTech/SmartPot-DB-Mongo) | MongoDB 8.0/7.0, JavaScript | Reemplazada por PostgreSQL 17 + TimescaleDB 2.17 | [`SmartPot-DB`](https://github.com/SmartPotTech/SmartPot-DB) |
| [SmartPot-Cache-Redis](https://github.com/SmartPotTech/SmartPot-Cache-Redis) | Redis 8 | Reemplazada por Valkey 9.1 | [`SmartPot-Cache`](https://github.com/SmartPotTech/SmartPot-Cache) |
| [SmartPot-Broker-Mosquito](https://github.com/SmartPotTech/SmartPot-Broker-Mosquito) | Eclipse Mosquitto 2.1 | Reemplazado por EMQX 5.8 con authn delegada | [`SmartPot-Broker`](https://github.com/SmartPotTech/SmartPot-Broker) |
| [SmartPot-Web-React](https://github.com/SmartPotTech/SmartPot-Web-React) | React 19, Vite, pnpm | Reemplazada por la PWA en SolidJS 1.9 con SSE y Bun | [`SmartPot-Web`](https://github.com/SmartPotTech/SmartPot-Web) |
| [SmartPot-AI-Python](https://github.com/SmartPotTech/SmartPot-AI-Python) | Python, FastAPI, scikit-learn monolítico | Separado en inferencia Rust y entrenamiento offline | [`SmartPot-AI`](https://github.com/SmartPotTech/SmartPot-AI) y [`SmartPot-Trainer`](https://github.com/SmartPotTech/SmartPot-Trainer) |
| [SmartPot-DataGenerator-Python](https://github.com/SmartPotTech/SmartPot-DataGenerator-Python) | Python, NumPy | Reemplazado por el simulador en Rust con paquete binario v2 | [`SmartPot-DataGenerator`](https://github.com/SmartPotTech/SmartPot-DataGenerator) |
| [SmartPot-Proxy](https://github.com/SmartPotTech/SmartPot-Proxy) | Python, FastAPI | Middleware previo obsoleto | [`SmartPot-Broker`](https://github.com/SmartPotTech/SmartPot-Broker) |

## Diagramas

| Diagrama | Tipo | Documentos |
|---|---|---|
| 01 Arquitectura | Flujo | Técnica, ciclo de vida |
| 02 Secuencia de una lectura | Secuencia | Técnica, ciclo de vida |
| 03 Asistente de IA | Flujo | Técnica, ciclo de vida |
| 04 Modelo de datos | Entidad-relación | Técnica, ciclo de vida |
| 05 Estados de un comando | Estados | Técnica, ciclo de vida |
| 06 Despliegue | Flujo | Técnica, ciclo de vida |
| 07 Redes | Flujo | Técnica, ciclo de vida |
| 08 QA | Flujo | Técnica, ciclo de vida |
| 09 Causa y efecto | Flujo | Recorrido, ciclo de vida |
| 10 Casos de uso | Flujo con actores | Recorrido, ciclo de vida |
| 11 Clases del dominio | Clases | Recorrido, ciclo de vida |
| 12 Componentes | Flujo | Recorrido, ciclo de vida |
| 13 Actividad del control automático | Actividad | Recorrido, ciclo de vida |
| 14 Vinculación de Telegram | Secuencia | Los tres |
| 15 Cultivo virtual con clima real | Secuencia | Los tres |
| 16 Aprendizaje continuo | Flujo | Los tres |
| 17 Etapas del proyecto | Flujo | Recorrido, ciclo de vida |
| 18 Árbol de problemas | Flujo | Ciclo de vida |
| 19 Árbol de objetivos | Flujo | Ciclo de vida |
| 20 Poder e interés de los interesados | Cuadrantes | Ciclo de vida |
| 21 Estructura de desglose del trabajo | Flujo | Ciclo de vida |
| 22 Red de precedencias | Flujo | Ciclo de vida |
| 23 Ruta crítica | Gantt | Ciclo de vida |
| 24 Ciclo Scrum | Flujo | Ciclo de vida |
| 25 Riesgos y su desenlace | Flujo | Ciclo de vida |
| 26 Contexto del sistema | Flujo (C4, nivel 1) | Ciclo de vida |
| 27 Clases del diseño original | Clases | Ciclo de vida |
| 28 Componentes del diseño original | Flujo | Ciclo de vida |
| 29 Actividad original: enviar un comando | Actividad | Ciclo de vida |
| 30 Secuencia original: datos históricos | Secuencia | Ciclo de vida |
| 31 Modelo de datos original | Entidad-relación | Ciclo de vida |
| 32 Mapa de la PWA | Flujo | Ciclo de vida |
| 33 Pirámide de pruebas | Flujo | Ciclo de vida |
| 34 Ciclo PDCA | Flujo | Ciclo de vida |
| 35 Ciclos de mejora | Flujo | Ciclo de vida |
| 36 Fases de la investigación | Flujo | Ciclo de vida |
| 37 Avisos de un cultivo | Secuencia | Técnica |
| 38 Consejo de lugar | Flujo | Técnica, recorrido |
| 39 Un actuador como switch | Flujo de estados | Técnica |
| 40 Paquetes del diseño original | Paquetes | Ciclo de vida |
| 41 Objetos del diseño original | Objetos | Ciclo de vida |
| 42 Artefactos del diseño original | Despliegue | Ciclo de vida |
| 43 Actividad original: datos históricos | Actividad | Ciclo de vida |
| 44 Actividad original: control automático | Actividad | Ciclo de vida |
| 45 Cronograma de la investigación | Gantt | Ciclo de vida |
| 46 Comparación arquitectónica A/B | Flujo | Auditoría A/B |
| 47 Secuencia de validación A/B | Secuencia | Auditoría A/B |
| 48 Topología de seguridad AppSec | Flujo | Auditoría A/B |
| 49 Comparación de seguridad A/B | Flujo | Auditoría Seguridad A/B |

## Diagramas generales

Diagramas independientes, sin límite de tamaño, que muestran la plataforma completa en una sola imagen. No van en ningún documento: el SVG se abre en el navegador y se amplía tanto como haga falta. Sus nombres empiezan por `SmartPot_Global_`; los demás son específicos y llevan en el nombre lo que muestran.

| Diagrama general | Qué muestra | Archivos |
|---|---|---|
| 01 Arquitectura completa | Personas y dispositivos, borde (UFW y Nginx), los nueve contenedores con sus módulos internos, puertos, redes, volúmenes y servicios externos | [MMD](diagrams/SmartPot_Global_01_Architecture.mmd) · [PNG](diagrams/SmartPot_Global_01_Architecture.png) · [SVG](diagrams/SmartPot_Global_01_Architecture.svg) |
| 02 Operación completa | Secuencia de 16 escenas y más de 150 mensajes numerados: arranque, registro, cultivo real o virtual, conexión, simulación, lectura con automatización, aprendizaje, Telegram, PWA, órdenes, vinculación, desconexión, rotación de la clave, recuperación de la contraseña, borrado y salud | [MMD](diagrams/SmartPot_Global_02_Operation_Sequence.mmd) · [PNG](diagrams/SmartPot_Global_02_Operation_Sequence.png) · [SVG](diagrams/SmartPot_Global_02_Operation_Sequence.svg) |
| 03 Entrega continua | Del commit al servidor: CI, QA con E2E, imágenes en GHCR y Docker Hub, despliegue central, secretos y entornos (demo, desarrollo, producción y Kubernetes) | [MMD](diagrams/SmartPot_Global_03_Delivery.mmd) · [PNG](diagrams/SmartPot_Global_03_Delivery.png) · [SVG](diagrams/SmartPot_Global_03_Delivery.svg) |
| 04 Linaje de los datos | De dónde sale cada dato, por dónde viaja, dónde se guarda (PostgreSQL/TimescaleDB, Valkey, SQLite, modelos y navegador) y quién lo usa | [MMD](diagrams/SmartPot_Global_04_Data_Lineage.mmd) · [PNG](diagrams/SmartPot_Global_04_Data_Lineage.png) · [SVG](diagrams/SmartPot_Global_04_Data_Lineage.svg) |
| 05 Máquinas de estado | Sesión, dispositivo y su cuenta MQTT, comando, evaluación del cultivo, modo automático, aprendizaje por especie, vínculo de Telegram y simulación de un cultivo virtual | [MMD](diagrams/SmartPot_Global_05_State_Machines.mmd) · [PNG](diagrams/SmartPot_Global_05_State_Machines.png) · [SVG](diagrams/SmartPot_Global_05_State_Machines.svg) |
| 06 Modelo de dominio | Entidades relacionales, hipertablas, agregados continuos y contratos con sus relaciones | [MMD](diagrams/SmartPot_Global_06_Domain_Model.mmd) · [PNG](diagrams/SmartPot_Global_06_Domain_Model.png) · [SVG](diagrams/SmartPot_Global_06_Domain_Model.svg) |
| 07 Recorrido de la PWA | Cada pantalla de la PWA SolidJS, las rutas de la API que llama y el servicio que responde | [MMD](diagrams/SmartPot_Global_07_User_Journey.mmd) · [PNG](diagrams/SmartPot_Global_07_User_Journey.png) · [SVG](diagrams/SmartPot_Global_07_User_Journey.svg) |
| 08 Decisión de la IA | De la lectura a la orden: diagnóstico, pronóstico, modelos base y aprendidos, las 21 reglas, índice difuso, agente, consejo de lugar y lo que hace la API | [MMD](diagrams/SmartPot_Global_08_AI_Decision.mmd) · [PNG](diagrams/SmartPot_Global_08_AI_Decision.png) · [SVG](diagrams/SmartPot_Global_08_AI_Decision.svg) |

Los diagramas de flujo usan el motor de diseño ELK, que ordena mejor los grafos grandes; como superan los límites por defecto de Mermaid (50 000 caracteres y 500 aristas), `render_diagrams.py` los reconoce por el nombre y los renderiza sin esos límites, con el PNG a su tamaño natural.

## Estructura

```text
docs/
├── SmartPot_Technical_Documentation.md   # Fuente
├── SmartPot_Project_Journey.md           # Fuente
├── SmartPot_Software_Lifecycle.md        # Fuente
├── *.docx, *.pdf                         # Generados
├── diagrams/                             # Cada diagrama con su fuente (.mmd), su PNG y su SVG
├── assets/                               # Logo, ícono y marca de agua de la portada
└── tools/
    ├── render_diagrams.py                # .mmd → PNG y SVG y sincronización con el Markdown
    └── md_to_docx.py                     # Markdown → DOCX (y PDF con LibreOffice)
```

## Regenerar

Requisitos: Python 3.11+, Node.js (para `npx @mermaid-js/mermaid-cli`), Google Chrome y LibreOffice.

```bash
python docs/tools/render_diagrams.py --sync-md docs/SmartPot_Technical_Documentation.md docs/SmartPot_Project_Journey.md docs/SmartPot_Software_Lifecycle.md
python docs/tools/md_to_docx.py docs/SmartPot_Technical_Documentation.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Project_Journey.md --pdf
python docs/tools/md_to_docx.py docs/SmartPot_Software_Lifecycle.md --pdf
python docs/tools/render_diagrams.py --global   # solo los diagramas generales
```
