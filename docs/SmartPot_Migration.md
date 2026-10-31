<!-- portada
eyebrow: Documentación de migración
titulo: Migración de SmartPot
acento: SmartPot
subtitulo: Del stack original a la nueva generación de componentes
bajada: Por qué y cómo migra la plataforma, la hoja de ruta por componente, la primera fase ya construida (API en Go y PostgreSQL + TimescaleDB), la versión demo beta para probarla y el camino al corte de producción con la depreciación del stack anterior.
documento: Documentación de migración
version: 1.0 · octubre 2026
equipo: SmartPotTech
proyecto: smartpot.app
-->

# Migración de SmartPot

## Ficha del documento

| Campo             | Valor                                                                                                                                                 |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Proyecto          | SmartPot · [smartpot.app](https://smartpot.app)                                                                                                       |
| Organización      | SmartPotTech                                                                                                                                           |
| Documento         | Documentación de migración de la plataforma                                                                                                           |
| Versión           | 1.1 · octubre 2026                                                                                                                                    |
| Estado            | En curso. La API, la base de datos, el broker MQTT, la caché, la PWA y el simulador están migrados en código y validados en la demo beta; el resto está en curso    |
| Alcance           | La estrategia de migración, la hoja de ruta por componente, los componentes migrados (Go, PostgreSQL + TimescaleDB, Valkey, EMQX, SolidJS y Rust) y el corte|
| Fuente de verdad  | Los README de cada repositorio y la [documentación técnica](SmartPot_Technical_Documentation.md) describen la plataforma **como funciona hoy**        |
| Documento hermano | [Documentación técnica](SmartPot_Technical_Documentation.md): la plataforma tal como está en producción                                               |

> [!IMPORTANT]
> **Qué es producción hoy.** La plataforma en producción sigue corriendo con la API en **Spring Boot** y la base en
> **MongoDB**. La migración que describe este documento está construida y probada, pero **aún no se ha desplegado**: el
> corte a producción es un paso pendiente, sujeto a aprobación. Hasta entonces, el stack nuevo vive en la versión demo
> beta.

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
| Simulador         | `SmartPot-DataGenerator` → `SmartPot-DataGenerator-Rust`   | Python 3.13 / FastAPI    | **Rust 1.85 + Tokio + Axum 0.8 + rumqttc**     | **Migrado (código)**, en la demo beta    |
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

Dos formas, según de dónde salgan las imágenes nuevas:

```bash
# A. Construyendo la API y la base desde los repos locales (disponible hoy):
cd .github/docker/demo-beta
docker compose -f compose.yaml -f compose.build.yaml up -d --wait --build

# B. Solo con imágenes de GHCR (cuando estén publicadas):
docker compose up -d --wait
```

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

## 12. Qué falta para el corte

El código está listo; el corte a producción es operativo y requiere aprobación:

1. **Publicar las imágenes nuevas en GHCR** (`smartpot-api-go` y `smartpot-db-postgre`), igual que el resto.
2. **Actualizar el entorno de producción** de la organización para que use la imagen de la API en Go y la base
   PostgreSQL (con `DATABASE_URL` en vez de `MONGODB_URI`), tanto en Docker Compose como en Kubernetes y en el workflow
   central de despliegue.
3. **Respaldar la base actual** y planear la **migración de los datos** de MongoDB a PostgreSQL (o partir de una base
   nueva, según se decida).
4. **Hacer el corte** en una ventana de bajo uso, verificar `/health` y las rutas críticas, y dejar el stack anterior
   disponible como respaldo durante un periodo de observación.

> [!WARNING]
> **No ejecutar sin aprobación.** El corte toca producción. Los pasos anteriores (publicación, actualización del
> entorno, respaldo y despliegue) se realizan solo con el visto bueno explícito del responsable.

## 13. Depreciación del stack anterior

Cuando el stack nuevo esté estable en producción, los componentes anteriores se **deprecan**: `SmartPot-API` (Spring
Boot) y `SmartPot-DB` (MongoDB) dejan de recibir cambios y sus imágenes se marcan como obsoletas, pero se conservan como
respaldo durante el periodo de observación. Lo mismo aplicará, a su turno, a cada componente que vaya migrando: el
anterior queda deprecado solo después de que el nuevo lo reemplace en producción.

## 14. Próximas fases

Tras la API en Go, PostgreSQL + TimescaleDB, Valkey, EMQX y la PWA en SolidJS (`SmartPot-Web-Solid`), la hoja de ruta
continúa (ver la [sección 2](#2-hoja-de-ruta-por-componente)):

- **Firmware en Rust** (`SmartPot-IoT-Rust`): firmware de alto rendimiento migrado y optimizado en Rust 2024 `no_std` con Embassy dual-core, canales libres de bloqueos, banco de actuadores temporizados y soporte para simulación completa en Wokwi (`diagram.json`, `wokwi.toml`, `start.py`) o placa física ESP32. No forma parte del despliegue Docker de `demo-beta` (los cultivos en el servidor los simula `SmartPot-DataGenerator-Rust`), pero su contrato MQTT v1 fue probado y validado de extremo a extremo contra EMQX y la API Go de `demo-beta`. Convive con el firmware en MicroPython hasta el corte definitivo.
- **IA optimizada con motor nativo C++20, Cython, Polars y LoRA** (`SmartPot-AI`): motor numérico de alto rendimiento en C++20 con estimador Theil-Sen lineal en $O(M)$, inferencia difusa Sugeno branchless con latencia sub-milisegundo ($47.2\text{ µs}$), puente Cython nogil con Memoryviews zero-copy, eliminación de cold-start (57 ms vs 5,500 ms) con artefacto binario estático, pipeline de telemetría DQS acelerado con Polars LazyFrame (20,000 filas en 36 ms) y adaptación analítica en caliente por especie mediante Low-Rank Adaptation (LoRA) en $< 0.19\text{ ms}$, preservando el 100% de paridad funcional, agronómica y de contratos REST de la IA.
- **Microservicio desacoplado de entrenamiento y aprendizaje continuo** (`SmartPot-Trainer`): separación estricta entre plano de servicio (inferencia pura sub-milisegundo en `SmartPot-AI`) y plano de entrenamiento pesado (`SmartPot-Trainer`). Gestiona SQLite WAL con seudonimización SHA-256, torneos de modelos con `TimeSeriesSplit(cv=4)` y `GridSearchCV`, estados operacionales con K-Means y silueta ($k \in [2, 6]$), detección de anomalías con `IsolationForest` y adaptadores LoRA, disparando recarga en memoria caliente (`POST /v1/learning/reload`) en $< 5\text{ ms}$ en `SmartPot-AI` tras cada promoción de modelo sin reinicio de contenedor. Integrado en todos los stacks de despliegue (`demo-beta`, `demo`, `dev`, `production`) compartiendo el volumen `/data` (`ai_data`).
- **Simulador en Rust** (`SmartPot-DataGenerator-Rust`): completamente migrado a Rust 2.0 / Axum 0.8 / Tokio / rumqttc con huella < 15 MB e integrado en demo beta.

Cada fase repetirá el mismo patrón: reescritura transparente, validación en la demo beta, corte con aprobación y
depreciación del componente anterior.

<!-- parte: PARTE V | Plan Maestro de Maximización y Endurecimiento Industrial del Stack B (demo-beta) -->

## 15. Plan Maestro de Maximización y Endurecimiento Industrial del Stack B (demo-beta)

### 15.1. Directiva Arquitectónica Central: Evolución In-Place sin Proliferación de Stacks

> [!IMPORTANT]
> **No existe un "Stack C" ni repositorios paralelos.** El **Stack B (`demo-beta`)** es el stack definitivo de producción de SmartPot. Cualquier modernización técnica, cambio de protocolo o reemplazo de runtime se ejecuta **in-place** dentro de los repositorios existentes de la organización (`SmartPot-AI`, `SmartPot-Trainer`, `SmartPot-API-Go`, `SmartPot-DB-Postgre`, `SmartPot-Cache-Valkey`, `SmartPot-Broker-EMQX`, `SmartPot-Web-Solid`, `SmartPot-IoT-Rust`, `SmartPot-DataGenerator-Rust` y `.github`).

La evolución a escala industrial masiva resuelve las siguientes premisas críticas:
1. **Transporte Dual Adaptativo**: Queda superado el acoplamiento rígido a Unix Domain Sockets (UDS). Los servicios implementan autodetección: UDS (`/var/run/smartpot/*.sock`) en despliegues mononodo de latencia ultra-baja (como `demo-beta`), con conmutación transparente a **gRPC sobre HTTP/2 (con soporte eBPF Socket Bypass / Cilium)** o **TCP/TLS 1.3** en entornos multi-nodo distribuidos.
2. **Inferencia Segura Zero-Copy**: Erradicación total de `dlopen` de bibliotecas `.so` dinámicas (Treelite C) y deserialización `pickle`/`joblib` entre servicios. La inferencia en Rust opera exclusivamente con grafos estáticos **ONNX-ML (`tract-onnx`)** y tensores mapeados en memoria mediante **`rkyv`** (`memmap2`), con integridad verificada por hash **BLAKE3** y firma asimétrica **Ed25519**.
3. **Cero SQLite en `SmartPot-Trainer`**: Eliminada la redundancia de almacenamiento y re-ingesta local. `SmartPot-Trainer` lee las series temporales directamente desde TimescaleDB mediante **ADBC (`adbc-driver-postgresql`)**, transfiriendo bloques binarios **Apache Arrow** directo a `Polars LazyFrame` con cero copias en memoria.
4. **Separación Builder vs. Runner en Frontend**: **Bun 1.4** se confina a la fase de construcción y empaquetado (`builder`), generando activos estáticos pre-comprimidos con Zstandard (`.zst`, nivel 19) y Brotli (`.br`, nivel 11). El **runner** de producción en `SmartPot-Web-Solid` es un servidor estático ultraligero en **Caddy 2.9 (HTTP/3 QUIC + kTLS)** sin runtime de JavaScript en producción.

### 15.2. Arquitectura Industrial Definitiva

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ARQUITECTURA INDUSTRIAL DEFINITIVA - SMARTPOT STACK B                                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  [ SmartPot-IoT-Rust (ESP32) ] ──┐ (mTLS X.509 Ed25519 + MQTT v5 Topic Aliases + Payload Postcard/Protobuf 22 Bytes)
  [ SmartPot-DataGenerator-Rust ] ┘ (Filtro Mediana + EKF Q16.16 en el borde / TLS Session Tickets < 15ms)
                 │
                 ▼
  [ SmartPot-Broker-EMQX 5.8 (OTP 27) ]
    • Autenticación mTLS en handshake (CN == device_id ACL criptográfico)
    • Stream persistente bidireccional vía EMQX gRPC ExHook (Protobuf binario, cero webhooks HTTP)
                 │
                 ▼
  [ SmartPot-API-Go (Go 1.26 + PGO + Distroless) ] ◄───(HTTP/3 QUIC + SSE Binary/SIMD Stream)───► [ SmartPot-Web-Solid ]
    │ • Lock-Free Ring Buffer de Ingesta (Disruptor pattern)                                        • Builder: Bun 1.4 (.zst/.br)
    │ • Caché L1 in-memory + L2 Valkey (Agronomic Deadband Filter)                                  • Runner: Caddy HTTP/3 QUIC
    │ • Auth Stateless PASETO v4 / JWT EdDSA (Ed25519 en memoria < 15µs)                            • Web Workers + Signals 60FPS
    │
    ├───────────────────────────────┬─────────────────────────────────────────┐
    │ (Dual: UDS / RESP3 Pipelined) │ (Dual: UDS / gRPC HTTP/2 Protobuf v3)   │ (pgx Binary COPY FROM STDIN cada 25ms/500 msgs)
    ▼                               ▼                                         ▼
[ SmartPot-Cache-Valkey 9.1 ]   [ SmartPot-AI (Migrado In-Place a Rust) ] [ SmartPot-DB-Postgre (PG 17 + TimescaleDB 2.18) ]
  • io-threads 4 + Jemalloc purge • Axum 0.8 (REST) + Tonic (gRPC)          • Rol Ingesta: synchronous_commit = off (150k ins/s)
  • Funciones Lua Deadband        • SIMD f64x4: Theil-Sen, VPD, EKF, Sugeno • Rol Transaccional: synchronous_commit = on + RLS
  • Pub/Sub de Hot-Reload IA      • Sistema Experto en Bitsets (u64 < 200ns)• Chunks 1d + Compresión Columnar Zstd a las 12h
                                  • Inferencia tract-onnx + rkyv mmap       • Continuous Aggregates: 1m, 15m, 1h (< 1.5ms query)
                                  • Hot-Reload lock-free vía ArcSwap (<500ns)
                                  • Verificación BLAKE3 + Firma Ed25519
                                                ▲
                                                │ (Exporta ONNX-ML + rkyv firmados con Ed25519 + Señal Valkey Pub/Sub)
                                                │
                                  [ SmartPot-Trainer (Python 3.13 + uv) ]
                                    • Cero SQLite: Lectura directa Arrow vía ADBC Postgres desde TimescaleDB
                                    • Procesamiento paralelo en Rust con Polars LazyFrame (IQR, Rolling, Lead/Shift)
                                    • Ruta Rápida: Adaptadores NumPy LoRA (W = W0 + α·B·A) actualizados en < 1ms
                                    • Ruta Profunda: Torneo Champion-Challenger Scikit-Learn exportado con skl2onnx
```

### 15.3. Comparativa de Protocolos y Estándar Builder/Runner

| Capa / Flujo | Protocolo Anterior | Protocolo Definitivo Industrial | Ganancia Arquitectónica |
| :--- | :--- | :--- | :--- |
| **Borde IoT → Broker** | MQTT v3.1.1 JSON (~180 B) | **MQTT v5 Postcard (22 B) + Topic Aliases** | Reducción de ancho de banda del 88%, eliminación de parsing JSON en microcontrolador. |
| **Broker → Gateway API** | Webhook HTTP POST JSON | **gRPC ExHook persistente (Protobuf binario)** | Eliminación de handshakes HTTP/1.1 por mensaje, multiplexación en un solo stream TCP. |
| **Gateway → Persistencia** | Inserciones SQL micro-batching | **`pgx.CopyFrom` binario masivo STDIN** | Supera 150,000 inserciones/s sin saturar buffer pool ni bloquear fsync de disco. |
| **Gateway → IA / Caché** | HTTP/1.1 REST JSON + TCP Redis | **Dual UDS (`.sock`) / gRPC HTTP/2 + RESP3** | Latencia sub-milisegundo (< 200 µs UDS) y bypass de pila TCP en mononodo. |
| **Gateway → PWA Web** | Polling condicional ETag 304 | **HTTP/3 QUIC + SSE (Server-Sent Events)** | Cero latencia de sondeo, actualización reactiva empujada en tiempo real por el servidor. |

| Componente | Builder / Entorno de Compilación | Runner / Imagen de Producción | Estrategia de Contención |
| :--- | :--- | :--- | :--- |
| **SmartPot-AI** | `rust:1.85-bookworm` (cargo-chef, target x86_64-unknown-linux-musl, `target-cpu=x86-64-v3`, LTO fat) | `gcr.io/distroless/static-debian12:nonroot` | Binario estático puro, 0 vulnerabilidades de SO, sin shell ni herramientas. |
| **SmartPot-Trainer** | `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (`uv sync --frozen --compile-bytecode`) | `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (usuario sin privilegios UID 65532) | Ingesta analítica directa por ADBC Arrow, aislamiento de procesos, sin SQLite. |
| **SmartPot-API-Go** | `golang:1.26-alpine` (`CGO_ENABLED=0`, `-pgo=default.pgo`, `-trimpath`, `-ldflags="-s -w"`) | `gcr.io/distroless/static-debian12:nonroot` | Imagen `scratch`/distroless, memoria < 15 MB, PGO habilitado. |
| **SmartPot-Web-Solid** | `oven/bun:1.4-alpine` (`bun run build`, pre-compresión Zstandard y Brotli) | `caddy:2.9-alpine` (servidor nativo HTTP/3 QUIC + kTLS) | Cero runtime JavaScript en producción; servicio de activos estáticos desde caché kernel. |
| **SmartPot-DataGenerator-Rust** | `rust:1.85-bookworm` (musl static builder) | `gcr.io/distroless/static-debian12:nonroot` | Simulador nativo en Rust con huella < 2 MB RAM. |

### 15.4. Especificación Técnica por Componente

#### A. SmartPot-AI (Migración In-Place a Rust 2024 Edition)
* **Stack**: `axum 0.8` (compatibilidad REST v1 completa) + `tonic` (gRPC sobre `/var/run/smartpot/ai.sock` y TCP interno) + `tokio` multi-hilo con `mimalloc` como `#[global_allocator]`.
* **Núcleo SIMD (`core::simd` / `wide`)**:
  * Cálculo de **Déficit de Presión de Vapor (VPD) foliar psicrométrico** mediante la ecuación de Tetens/Buck con offset térmico radiativo:
    $$e_s(T) = 0.61078 \exp\left(\frac{17.27 \cdot T}{T + 237.3}\right), \quad \text{VPD} = e_s(T_{\text{air}} - 1.5) - \left(e_s(T_{\text{air}}) \cdot \frac{\text{RH}}{100}\right)$$
  * **Filtro de Kalman Extendido (EKF 1D)**: pre-filtrado de ruido electromagnético en lecturas de pH, conductividad (TDS/EC) y humedad de sustrato.
  * **Regresión Robusta Theil-Sen $O(M)$** y **Lógica Difusa Sugeno Branchless** vectorizadas en registros `f64x4`.
* **Sistema Experto en Bitsets `u64`**: Hechos agronómicos codificados como máscaras de bits individuales (`TempHigh`, `VpdCritical`, `PhAcidicDrift`, `MoistureDepleting`). Evaluación atómica bit a bit de las 21 reglas en $< 200\text{ ns}$.
* **Motor ML Zero-Copy**: Inferencia de árboles con `tract-onnx` (`TreeEnsembleClassifier`) y tensores LoRA mapeados con `rkyv`/`memmap2`.
* **Hot-Reload Atómico**: Sustitución de modelos mediante `arc_swap::ArcSwap<ModelBundle>` sin contención de cerrojos, verificando hash BLAKE3 y firma Ed25519 del artefacto.

#### B. SmartPot-Trainer (Python 3.13 + uv + ADBC Arrow + Polars + ONNX)
* **Ingesta Analítica Directa**: Cero SQLite. Conexión de alto rendimiento mediante `adbc-driver-postgresql` transfiriendo flujos binarios Arrow directo a `Polars LazyFrame`.
* **Pipeline Vectorizado**: Filtrado IQR, métricas DQS, medias/desviaciones móviles y generación de etiquetas autosupervisadas en el motor multihilo de Polars.
* **Entrenamiento en Dos Velocidades**:
  * *Ruta Rápida (LoRA)*: Actualización analítica de matrices $B_s \in \mathbb{R}^{d \times r}$ y $A_s \in \mathbb{R}^{r \times k}$ ($r=2$) en $< 1\text{ ms}$.
  * *Ruta Profunda*: Torneo Champion-Challenger con `TimeSeriesSplit(4)` sobre Scikit-Learn paralelizado con joblib en `/dev/shm`.
* **Exportación y Firma**: Generación de `.onnx` (`skl2onnx`), firma criptográfica Ed25519 y notificación mediante Valkey Pub/Sub (`smartpot:ai:reload`).

#### C. SmartPot-API-Go (Go 1.26 + PGO + Disruptor + CopyFrom + Deadband)
* **Ingesta Masiva**: Cola Ring Buffer lock-free (Disruptor) con vaciado cada 25 ms o 500 registros ejecutando `pgxPoolIngest.CopyFrom` directo a PostgreSQL.
* **Filtro de Banda Muerta Agronómico**: Caché L1 en memoria de Go respaldada por Valkey L2. Bypass de hasta el 80% de consultas a la IA si $|\Delta T| < 0.1^\circ\text{C}$, $|\Delta RH| < 0.4\%$, $|\Delta pH| < 0.03$ y $|\Delta EC| < 15\,\mu\text{S/cm}$ dentro del TTL de 60s.
* **Transporte Dual**: Conexión adaptativa hacia IA y Valkey por socket UNIX o gRPC HTTP/2 / RESP3.
* **Seguridad Stateless**: Verificación en memoria de tokens PASETO v4.public / JWT EdDSA (curva Ed25519) en $< 15\text{ µs}$.

#### D. SmartPot-DB-Postgre (PostgreSQL 17 + TimescaleDB 2.18 Ultra-Tuned)
* **Separación de Roles**:
  * `smartpot_ingest`: `synchronous_commit = off` y `commit_delay = 10000`, optimizado para ingesta continua masiva (> 150k ins/s).
  * `smartpot_app`: `synchronous_commit = on` con políticas RLS (`ENABLE ROW LEVEL SECURITY`) aisladas por `app.current_tenant_id`.
* **Hipertablas y Vistas Continuas**: Fragmentos de 1 día, compresión columnar Zstandard a las 12 horas y continuous aggregates (`readings_1m`, `readings_15m`, `readings_1h`) para consultas históricas sub-milisegundo.

#### E. SmartPot-Cache-Valkey (Valkey 9.1 Multi-IO + UDS + Lua)
* Listener dual en puerto 6379 y `/var/run/smartpot/valkey.sock`.
* `io-threads 4`, purga asíncrona de memoria Jemalloc (`lazyfree`, `activedefrag`).
* Funciones Lua atómicas para evaluación de Deadband, deduplicación de paquetes MQTT y rate limiting GCRA.

#### F. SmartPot-Broker-EMQX (EMQX 5.8 + MQTT v5 + mTLS X.509 + gRPC ExHook)
* MQTT v5 con Topic Aliases (`topic_alias_maximum = 64`).
* Autenticación mTLS en handshake (certificados cliente Ed25519 / P-256) con TLS Session Resumption y validación ACL `peer_cert_cn == clientid`.
* Integración gRPC ExHook persistente hacia la API sin sobrecarga de webhooks HTTP.

#### G. SmartPot-IoT-Rust y DataGenerator-Rust (Borde Ciberfísico)
* Filtro de mediana de 5 muestras + EKF unidimensional en aritmética de punto fijo Q16.16 en el ESP32.
* Serialización binaria Postcard/Protobuf en 22 bytes (`timestamp_delta`, `temp_centi`, `rh_centi`, `soil_moisture_centi`, `ph_milli`, `tds_ppm`, `light_lux`, `battery_mv`, `status_flags`, `crc8`).

#### H. SmartPot-Web-Solid (Frontend Reactivo HTTP/3)
* Builder con Bun 1.4 y pre-compresión dual Zstandard y Brotli.
* Runner en Caddy 2.9 sobre HTTP/3 (QUIC) con kTLS.
* Conexión reactiva continua vía Server-Sent Events (SSE) y procesamiento de telemetría en Web Worker con `Float64Array` transferibles (`SharedArrayBuffer`) a 60 FPS.
