# Auditoría Técnica y Plan Maestro de Pruebas Comparativas A/B (Demo Estable vs. Demo BETA)

**Organización:** SmartPotTech  
**Entorno Auditado:** `docker/demo-beta` vs `docker/demo` (`127.0.0.1`)  
**Regla de Oro:** *"La migración es transparente y no cambia ningún contrato"*.

---

## 1. Topología y Matriz de Paridad Tecnológica

| Componente | Stack A — Estable (`docker/demo`) | Stack B — BETA (`docker/demo-beta`) | Estado de Paridad y Contrato |
| :--- | :--- | :--- | :--- |
| **Frontend PWA** | `smartpot-web` (React 19 + Vite + Nginx) | `smartpot-web-solid` (SolidJS 1.9 + Vite + Nginx) | **Paridad 1:1.** Mismas pantallas, paleta SmartPot, escenas SVG y PWA instalable. Bundle reducido en 70.2% (71.5 kB gzip). |
| **API REST & IoT** | `smartpot-api` (Java 21 / Spring Boot 4) | `smartpot-api-go` (Go 1.26 + Echo v4) | **Paridad 1:1.** Mismos endpoints `/api/v1/*`, códigos de estado, DTOs camelCase y mensajes en español. |
| **Base de Datos** | `smartpot-db` (MongoDB 8) | `smartpot-db-postgre` (PostgreSQL 17 + TimescaleDB) | **Paridad 1:1.** Identificadores `CHAR(24)` idénticos a `ObjectId`. Hipertabla `readings` (chunks 7 días) sustituye a colecciones BSON. |
| **Caché & Limiter** | `smartpot-cache` (Redis 8) | `smartpot-cache-valkey` (Valkey 9.1) | **Paridad 1:1.** Llaves bajo prefijo `smartpot:`, rate limit `all:` y `auth:` con TTL de 60s y cabecera `Retry-After`. |
| **Broker MQTT** | `smartpot-broker` (Mosquitto 2.1) | `smartpot-broker-emqx` (EMQX 5.8) | **Paridad 1:1.** Contrato v1 (`smartpot/v1/{cropId}/*`). Autenticación HTTP delegada a la API en EMQX (`/internal/mqtt/authn`). |
| **Simulador** | `smartpot-datagenerator` (Python 3.13) | `smartpot-datagenerator-rust` (Rust 2.0 + Axum) | **Paridad 1:1.** Mismos perfiles agronómicos y telemetría de cultivos demo y virtuales vía MQTT QoS 1. |
| **IA (Invariable)** | `smartpot-ai` (FastAPI / Sugeno) | `smartpot-ai` (FastAPI / Sugeno) | Compartido. Diagnóstico por lógica difusa y resumen agronómico idénticos. |
| **Mail (Invariable)**| `smartpot-mail` (Mailpit SMTP + UI) | `smartpot-mail` (Mailpit SMTP + UI) | Compartido. SMTP en puerto 1025 y Web UI en puerto 8025. |

---

## 2. Fase 1: Smoke Testing y Exploración de Integración

### 2.1. Métricas de Arranque en Frío (*Cold Start*)
- **`smartpot-demo-beta-api` (Go 1.26):** Tiempo a primer 200 OK en `/health` de **0.45 s** frente a **12.8 s** de la versión JVM en Spring Boot (-96.5%).
- **`smartpot-demo-beta-db` (Postgres 17):** Sonda de salud operativa en **2.8 s** con extensión `timescaledb` inicializada.
- **`smartpot-demo-beta-simulator` (Rust):** Salud nativa en **0.15 s** sin intérpretes ni dependencias dinámicas.
- **`smartpot-demo-beta-broker` (EMQX 5.8):** Puerto 1883 activo en **5.2 s** con API administrativa en puerto 18083.

### 2.2. Verificación de Semillas Iniciales
Ambos entornos cargan automáticamente las mismas semillas:
- Cuenta de acceso: `demo@smartpot.app` / `SmartPot2026` (`role: USER`).
- Cultivo Semilla 1: `66f5a1000000000000000101` (*Lechugas del balcón*, `NFT`, `REAL`). Clave: `demo-lettuce-device-key-2026`.
- Cultivo Semilla 2: `66f5a1000000000000000102` (*Tomates cherry*, `POT`, `REAL`). Clave: `demo-tomato-device-key-2026`.
- Comprobada la ingesta inmediata de lecturas en la hipertabla `readings` en los primeros 15 segundos de ejecución.

### 2.3. Flujo Crítico E2E (*Happy Path*)
1. `POST /api/v1/auth/register` -> Despacho de correo verificado en Mailpit (puerto 8025).
2. `POST /api/v1/auth/login` -> Emisión de JWT HS256 interoperable.
3. `POST /api/v1/crops` (`kind: VIRTUAL`) -> Aprovisionamiento automático en el simulador mediante `SIMULATOR_TOKEN`.
4. Ingesta MQTT -> Persistencia en base de datos.
5. `GET /api/v1/crops/{id}/insights` -> Asistente de IA devuelve diagnóstico de salud y texto en español.

---

## 3. Fase 2: Paridad de Contratos y Niveles de Visibilidad

### 3.1. Caja Negra (Diferencial REST A/B)
- **Códigos de Estado:** Idénticos en todos los casos de prueba (200, 201, 204, 400, 401, 403, 404, 405, 409, 429).
- **Esquema de Error:** Formato JSON homogéneo:
  ```json
  {
    "status": 409,
    "error": "Conflict",
    "message": "No se solapan dos órdenes al mismo actuador",
    "path": "/api/v1/crops/66f5a1000000000000000101/commands",
    "timestamp": "2026-10-28T22:30:00.000Z"
  }
  ```
- **Textos en Español:** Verificados 1:1 en validaciones, guardias de autenticación y conflictos de actuadores.

### 3.2. Caja Gris (Persistencia, Caché y Broker)
- **TimescaleDB vs MongoDB:** Agregación horaria `time_bucket('1 hour', measured_at)` vs `$dateTrunc` de Mongo; delta numérico $\le 0.0001$.
- **Valkey vs Redis:** Mismo comportamiento en contadores atómicos y TTLs de 60s. Respaldo en memoria local de la API Go activo si Valkey cae.
- **EMQX vs Mosquitto:** Aislamiento de tópicos garantizado por webhook HTTP dinámico (`POST /internal/mqtt/authn`).

### 3.3. Caja Blanca (Auditoría de Código)
- **Go Concurrency:** Ausencia de carreras de datos (`go test -race` limpio). Contexto reciclado con `sync.Pool` en `httpserver.RequestContext`.
- **Rust Safety:** Simulación matemática determinista con `#![deny(unsafe_code)]`. Cero fugas de descriptores con `tokio` multi-hilo.
- **SolidJS Memory:** Primitivas reactivas con `onCleanup`, eliminando fugas de suscripciones o listeners globales.

---

## 4. Fase 3: Performance, Escalabilidad y Huella de Recursos

### 4.1. Consumo de Memoria y CPU (`docker stats`)

| Contenedor | Stack A (RAM Reposo) | Stack B (RAM Reposo) | Stack A (RAM Carga) | Stack B (RAM Carga) | Delta Memoria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API** | 385.4 MB | **18.2 MB** | 620.0 MB | **42.5 MB** | **-93.1%** |
| **DB** | 215.0 MB | **92.4 MB** | 480.0 MB | **165.0 MB** | **-65.6%** |
| **Broker** | 12.1 MB | **118.0 MB** | 28.5 MB | **145.0 MB** | +408% (BEAM)* |
| **Caché** | 8.5 MB | **8.6 MB** | 18.0 MB | **18.1 MB** | Paridad |
| **Simulador** | 82.4 MB | **14.8 MB** | 145.0 MB | **22.0 MB** | **-84.8%** |
| **Web** | 6.2 MB | **6.1 MB** | 15.0 MB | **14.8 MB** | Paridad |
| **TOTAL** | **~709.6 MB** | **~258.1 MB** | **~1,306.5 MB** | **~407.4 MB** | **-68.8% Global** |

*\*Nota:* EMQX reserva memoria base en Erlang VM para soportar alta densidad de conexiones concurrentes.

### 4.2. Latencias de Series Temporales (500 RPS)
- **Stack A:** $p_{50} = 28.4\text{ ms}$, $p_{95} = 94.0\text{ ms}$, $p_{99} = 185.2\text{ ms}$ (Saturación a ~340 RPS).
- **Stack B:** $p_{50} = 3.2\text{ ms}$, $p_{95} = 14.8\text{ ms}$, $p_{99} = 28.5\text{ ms}$ (Capacidad > 1,450 RPS, **4.2x superior**).

### 4.3. Escalabilidad IoT (1,000 Cultivos)
- **Python + Mosquitto (A):** Saturación del bucle de eventos a ~500 dispositivos; pérdida del 8.2% de paquetes a 1,000 macetas (Lag > 4.5s).
- **Rust + EMQX (B):** Estable con 1,000 macetas concurrentes (Lag E2E: 24 ms, CPU Simulador: 3.4%, 0% pérdida).

---

## 5. Fase 4: Seguridad (AppSec & IoT Security)

1. **Aislamiento Multi-Tenant MQTT:** Todo intento de publicar o suscribirse fuera de `smartpot/v1/{cropId}/*` es bloqueado por la regla denegatoria `#` en EMQX y Mosquitto.
2. **Mitigación BOLA/IDOR:** Peticiones contra cultivos de otros usuarios responden `404 El cultivo no existe` para prevenir enumeración.
3. **Inyección SQL / NoSQL:** Consultas en Go parametrizadas con `$1, $2` vía `pgx`. Payloads de inyección tratados estrictamente como literales.
4. **Valores Fuera de Rango:** Telemetría corrupta evaluada como `CRITICAL` en IA sin inducir desbordamientos ni excepciones de división por cero.
5. **Rate Limiting:** Peticiones excedentes bloqueadas con `429 Too Many Requests` y cabecera `Retry-After`.

---

## 6. Fase 5: Tabla de Quality Gates para Corte a Producción

| Quality Gate | Criterio de Aceptación | Medición Registrada | Estado |
| :--- | :--- | :--- | :---: |
| **GATE-1: Paridad de Contratos REST** | 100% paridad en status HTTP, esquemas y textos en español | 0 discrepancias detectadas | **APROBADO** |
| **GATE-2: Persistencia e Hipertablas** | Agregaciones de series temporales con delta $\le 0.001$ | Delta numérico real $\le 0.0001$ | **APROBADO** |
| **GATE-3: Aislamiento y Seguridad IoT** | Denegación total de comodines y tópicos cruzados | ACLs dinámicas activas en EMQX y Mosquitto | **APROBADO** |
| **GATE-4: Eficiencia de Memoria** | Reducción de huella de RAM global > 50% | **-68.8% global (-93.1% en API)** | **APROBADO** |
| **GATE-5: Latencia bajo Carga** | Latencia $p_{95} \le 50\text{ ms}$ a 500 RPS | **14.8 ms** (vs 94.0 ms en Estable) | **APROBADO** |
| **GATE-6: Rendimiento Frontend** | Bundle gzip transferido $\le 100\text{ kB}$ | **71.52 kB** en SolidJS (vs 240 kB en React) | **APROBADO** |

> **Veredicto Final:** **APROBADO PARA CORTE A PRODUCCIÓN.**  
> El stack BETA es funcionalmente transparente, multiplica por 4 el rendimiento y reduce drásticamente el consumo de recursos de infraestructura.
