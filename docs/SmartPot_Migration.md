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
| Asistente de IA   | `SmartPot-AI`                                              | Python / FastAPI         | **Mejora con componentes en C++**              | Planeado                                 |
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
- **IA con C++.** Componentes nativos para el cálculo numérico pesado (modelos, lógica difusa), manteniendo la capa de
  servicio y los contratos HTTP actuales.

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
- **IA y simulador con componentes en C++**: cálculo numérico nativo detrás de la misma capa de servicio y los mismos
  contratos HTTP.

Cada fase repetirá el mismo patrón: reescritura transparente, validación en la demo beta, corte con aprobación y
depreciación del componente anterior.
