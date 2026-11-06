# SmartPot 🌱

**Tu huerto hidropónico, en tu bolsillo.** SmartPot mide la temperatura, la humedad, la luz, el pH, los nutrientes y la
humedad del sustrato de tus cultivos, te dice qué necesitan y, si quieres, se encarga de regarlos, iluminarlos y
ventilarlos.

[smartpot.app](https://smartpot.app) · [Documentación](https://github.com/SmartPotTech/.github/tree/main/docs) · [Diagramas generales](#la-plataforma-en-diagramas) · [Probar la demo](https://github.com/SmartPotTech/.github/tree/main/docker/demo)

## Cómo funciona

1. **Tu cultivo**, en maceta, tubos NFT, torre vertical o balsa flotante, envía sus lecturas por MQTT cifrado (TLS 8883) cada pocos
   segundos. Al crearlo eliges, de una vez, si es **real** (un microcontrolador ESP32 con firmware en Rust o MicroPython, físico o
   simulado en Wokwi, con su guía de conexión) o **virtual**: SmartPot lo simula en Rust siguiendo el clima real de tu ciudad,
   los medidores que muevas o el fotoperiodo de la especie, y obedece y confirma las órdenes igual que un dispositivo físico.
2. **La API** (Go / Echo) procesa las lecturas en arquitectura hexagonal, las almacena en **PostgreSQL 17 + TimescaleDB**
   aprovechando hipertablas y agregados en tiempo real, gestiona la caché y límites en **Valkey**, y compara los valores contra
   el rango agronómico ideal de la especie: lechuga, tomate, fresa, albahaca, espinaca o pimentón.
3. **El asistente de IA** (Rust / Axum con interfaz dual gRPC y REST) combina un sistema experto, lógica difusa Sugeno,
   modelos de aprendizaje automático nativos y un agente reactivo para diagnosticar el cultivo, calcular su índice de salud
   y proponer acciones. De noche entiende que la planta descansa. Además, el servicio de entrenamiento (**SmartPot-Trainer** en
   Python / Polars) **aprende sin parar** de las lecturas reales de cada especie mediante consultas ADBC optimizadas: anticipa
   cuándo hará falta regar o ventilar en la próxima hora y reconoce patrones anómalos sin exponer datos de usuario, exportando
   modelos JSON verificados criptográficamente con firmas Ed25519. También analiza **dónde está** cada cultivo: recomienda reubicarlo
   si le falta o sobra luz solar, y suspende el riego exterior ante pronóstico de lluvia.
4. **La app** (PWA reactiva en SolidJS 1.9 y Bun) muestra cada cultivo **en vivo** mediante SSE (Server-Sent Events), dibujado en su
   lugar (bajo techo o al aire libre con el clima exterior), con su forma, su planta y cada actuador encendido o apagado. Cada actuador
   tiene su **switch**: enciendes la bomba, la luz ultravioleta, el ventilador, el humidificador o los dosificadores con un solo toque,
   o dejas que el agente lo haga en modo autónomo. Incluye modo oscuro profundo, soporte bilingüe reactivo (`es`/`en`) y navegación sin parpadeos.
5. **Conexiones para IA y Telegram**: SmartPot expone un servidor **MCP** (Model Context Protocol) oficial (`mcp.smartpot.app`)
   para que asistentes inteligentes interactúen con los cultivos mediante tokens de conexión por cuenta (`spt_...`). Adicionalmente,
   **Telegram** te avisa aunque no tengas la app abierta: vinculas tu chat desde el perfil con un código de un solo uso y cada cultivo
   elige qué avisar, al instante o en resúmenes diarios, con soporte para comandos interactivos (`/estado`).

## La plataforma en diagramas

Ocho diagramas generales muestran SmartPot completo. Cada uno se abre como SVG y se puede ampliar tanto como haga falta.

| Diagrama general | Qué muestra |
|---|---|
| [Arquitectura completa](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_01_Architecture.svg) | Los dispositivos, el borde, los nueve contenedores con sus módulos, puertos y redes, y los servicios externos |
| [Operación completa](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_02_Operation_Sequence.svg) | Toda la operación paso a paso: del registro a la lectura, la decisión de la IA, la orden al dispositivo, la consulta MCP y el aviso por Telegram |
| [Entrega continua](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_03_Delivery.svg) | Del commit al servidor: pruebas de Go, Bun, Rust y Python, QA de extremo a extremo, imágenes GHCR y despliegue |
| [Linaje de los datos](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_04_Data_Lineage.svg) | De dónde sale cada dato, dónde se guarda (Postgres/TimescaleDB, Valkey, SQLite) y quién lo usa |
| [Máquinas de estado](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_05_State_Machines.svg) | Sesión JWT HttpOnly + CSRF, dispositivo, comando, salud, modo automático, aprendizaje, Telegram y simulación de un cultivo virtual |
| [Modelo de dominio](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_06_Domain_Model.svg) | Entidades relacionales, hipertablas, agregados continuos y contratos con sus relaciones |
| [Recorrido de la app](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_07_User_Journey.svg) | Cada pantalla de la PWA SolidJS, qué pide a la API y quién responde |
| [Decisión de la IA](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_08_AI_Decision.svg) | De la lectura a la orden: diagnóstico, pronóstico, modelos Rust/JSON, reglas, índice difuso y agente |

## Repositorios

Los repositorios oficiales que componen la arquitectura canónica de producción de SmartPot:

| Repositorio | Stack / Tecnologías | Rol en la plataforma |
|---|---|---|
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API) | Go 1.26, Echo v4.16, imagen `scratch` | API REST y puente MQTT con arquitectura hexagonal, autenticación por cookies `HttpOnly` + CSRF y soporte gRPC/SSE. |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) | PostgreSQL 17 + TimescaleDB 2.17.2 | Esquema relacional, hipertabla de telemetría, agregados continuos en tiempo real, compresión y rol de lectura. |
| [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache) | Valkey 9.1.2 (C/Lua) | Capa de caché endurecida y broker de estados en memoria (reemplazo abierto de Redis con socket UNIX o TCP). |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker) | EMQX 5.8.9 (Erlang) | Broker MQTT con TLS 8883 y autenticación/ACL delegada dinámicamente en la API (`/internal/mqtt/authn`). |
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web) | SolidJS 1.9, TypeScript, Bun 1.4, Vite, Tailwind CSS | PWA instalable con telemetría en vivo vía SSE, modo oscuro profundo, i18n (`es`/`en`) y runtime nginx sin privilegios. |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI) | Rust 1.88+, Axum 0.8, Tonic (gRPC), Tokio | Inferencia agronómica de alto rendimiento: sistema experto, lógica difusa Sugeno y evaluación nativa de modelos ML. |
| [SmartPot-Trainer](https://github.com/SmartPotTech/SmartPot-Trainer) | Python 3.13, FastAPI, Polars, scikit-learn, ADBC | Aprendizaje continuo fuera del camino crítico: lectura ADBC de TimescaleDB y exportación de modelos firmados con Ed25519. |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | Rust (Axum, Tokio, rumqttc) | Simulador concurrente de cultivos virtuales por MQTT con telemetría JSON y paquete binario compacto v2. |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) | Rust (Embassy `no_std`, ESP32) | Firmware principal para microcontrolador físico con tareas asíncronas, MQTT sobre TLS y telemetría compacta v2. |
| [SmartPot-IoT-Python](https://github.com/SmartPotTech/SmartPot-IoT-Python) | MicroPython 1.23 (ESP32 o Wokwi) | Firmware alternativo para prototipado rápido o simulación en Wokwi con MQTT sobre TLS. |
| [SmartPot-MCP](https://github.com/SmartPotTech/SmartPot-MCP) | Python (SDK `mcp` 2.3, FastMCP) | Servidor Model Context Protocol oficial con herramientas para asistentes de IA y autenticación por tokens de conexión (`spt_...`). |
| [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail) | Mailpit (Go / Docker) | Servidor SMTP protegido y bandeja transaccional web para correos de bienvenida y restablecimiento. |
| [.github](https://github.com/SmartPotTech/.github) | Docker, Kubernetes, GitHub Actions, docs | Orquestación central de entornos (`demo`, `dev`, `production`), manifiestos de clúster, QA E2E y documentación técnica. |

## Tecnologías

Go 1.26 · Echo · SolidJS 1.9 · TypeScript · Bun 1.4 · PostgreSQL 17 · TimescaleDB 2.17 · Valkey 9.1 · EMQX 5.8 · Rust 1.88 · Embassy (`no_std`) · Python 3.13 · Polars · scikit-learn · Apache Arrow ADBC · Model Context Protocol (FastMCP) · Mailpit · Docker Compose · Kubernetes · GitHub Actions

## Contribuir

Lee la [guía de contribución](https://github.com/SmartPotTech/.github/blob/main/CONTRIBUTING.md) y
la [política de seguridad](https://github.com/SmartPotTech/.github/blob/main/SECURITY.md). Todo el código está bajo
licencia MIT.

---

<details>
<summary><strong>Arquitectura histórica (Stack A - v1.0 deprecado)</strong></summary>

> La arquitectura original de la plataforma (Stack A: Spring Boot 4.1, Java 21, MongoDB 8, Redis 8, Mosquitto 2.1, React 19 y simulador en Python) fue reemplazada íntegramente en producción por el Stack canónico moderno (Stack B) tras alcanzar paridad funcional total, mayor eficiencia y verificación de seguridad.
>
> Los repositorios originales fueron renombrados con sufijos tecnológicos descriptivos (`SmartPot-API-Java`, `SmartPot-DB-Mongo`, `SmartPot-Cache-Redis`, `SmartPot-Broker-Mosquito`, `SmartPot-Web-React`, `SmartPot-AI-Python`, `SmartPot-DataGenerator-Python`, `SmartPot-Proxy`) y preservados en estado de archivo como referencia arqueológica e histórica.
</details>
