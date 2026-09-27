# **SmartPot con Docker**

Tres entornos de Docker Compose, todos con los mismos contenedores endurecidos (solo lectura, sin capacidades de Linux, usuarios sin privilegios y healthchecks):

| Carpeta | Entorno | Imágenes | Para qué sirve |
| --- | --- | --- | --- |
| [`demo/`](demo/README.md) | Demostración | Publicadas en GHCR | Probar SmartPot completo con un comando y datos de ejemplo |
| [`dev/`](dev/README.md) | Desarrollo | Compiladas desde los repositorios locales | Programar y probar cambios con toda la plataforma |
| [`production/`](production/README.md) | Producción | Publicadas en GHCR, con etiqueta configurable | Servidor con Nginx, HTTPS y despliegue automático |

## Servicios

| Servicio | Repositorio | Imagen |
| --- | --- | --- |
| `db-smartpot` | [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) | `ghcr.io/smartpottech/smartpot-db` |
| `cache-smartpot` | [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache) | `ghcr.io/smartpottech/smartpot-cache` |
| `mail-smartpot` | [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail) | `ghcr.io/smartpottech/smartpot-mail` |
| `broker-smartpot` | [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker) | `ghcr.io/smartpottech/smartpot-broker` |
| `ai-smartpot` | [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI) | `ghcr.io/smartpottech/smartpot-ai` |
| `api-smartpot` | [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API) | `ghcr.io/smartpottech/smartpot-api` |
| `web-smartpot` | [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web) | `ghcr.io/smartpottech/smartpot-web` |
| `simulator-smartpot` | [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | `ghcr.io/smartpottech/smartpot-datagenerator` |

La maceta física corre el firmware de [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) y se conecta al broker.

## Puertos

| Puerto | Servicio | Demo y desarrollo | Producción |
| --- | --- | --- | --- |
| 5173 | PWA | `127.0.0.1` | `127.0.0.1`, detrás de Nginx |
| 8091 | API | `127.0.0.1` | `127.0.0.1`, detrás de Nginx |
| 1883 | MQTT | `127.0.0.1` | Solo red interna |
| 8883 | MQTT sobre TLS | `127.0.0.1` (desarrollo, con certificados) | Público |
| 9001 | MQTT sobre WebSocket | `127.0.0.1` | `127.0.0.1`, detrás de Nginx (`wss`) |
| 8025 | Bandeja de correo | `127.0.0.1` | `127.0.0.1`, detrás de Nginx |
| 27017, 6379, 8000, 1025 | MongoDB, Redis, IA, SMTP | Solo en desarrollo | Solo red interna |
