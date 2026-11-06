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
- **Microservicio desacoplado de entrenamiento y aprendizaje continuo** (`SmartPot-Trainer`): separación estricta entre plano de servicio (inferencia pura sub-milisegundo en `SmartPot-AI`) y plano de entrenamiento pesado (`SmartPot-Trainer`). Gestiona SQLite WAL con seudonimización SHA-256, torneos de modelos con `TimeSeriesSplit(cv=4)` y `GridSearchCV`, estados operacionales con K-Means y silueta ($k \in [2, 6]$), detección de anomalías con `IsolationForest` y adaptadores LoRA, disparando recarga en memoria caliente (`POST /v1/learning/reload`) en $< 5\text{ ms}$ en `SmartPot-AI` tras cada promoción de modelo sin reinicio de contenedor. Integrado en todos los stacks de despliegue (`demo-beta`, `demo`, `dev`, `production`) compartiendo el volumen `/data` (`ai_data`).
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
dispositivos, ExHook gRPC de EMQX, inferencia sin pickle (los modelos se cargan con `joblib`) y firma de modelos con una
clave de confianza distribuida (hoy se verifica solo si se define `TRUSTED_MODEL_PUBLIC_KEY_HEX`).
