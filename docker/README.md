# **SmartPot con Docker**

Tres entornos de Docker Compose, todos con los mismos contenedores endurecidos (solo lectura, sin capacidades de Linux,
usuarios sin privilegios y healthchecks):

| Carpeta                               | Entorno      | Imágenes                                      | Para qué sirve                                             |
|---------------------------------------|--------------|-----------------------------------------------|------------------------------------------------------------|
| [`demo/`](demo/README.md)             | Demostración | GHCR (principal) o Docker Hub, a elección     | Probar SmartPot completo con un comando y datos de ejemplo |
| [`dev/`](dev/README.md)               | Desarrollo   | Compiladas desde los repositorios locales     | Programar y probar cambios con toda la plataforma          |
| [`production/`](production/README.md) | Producción   | Publicadas en GHCR, con etiqueta configurable | Servidor con Nginx, HTTPS y despliegue automático          |

## Servicios

| Servicio             | Repositorio                                                                      | GHCR                                          | Docker Hub                               |
|----------------------|----------------------------------------------------------------------------------|-----------------------------------------------|------------------------------------------|
| `db-smartpot`        | [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB)                       | `ghcr.io/smartpottech/smartpot-db`            | `sebastian190030/db-smartpot`            |
| `cache-smartpot`     | [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache)                 | `ghcr.io/smartpottech/smartpot-cache`         | `sebastian190030/cache-smartpot`         |
| `mail-smartpot`      | [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail)                   | `ghcr.io/smartpottech/smartpot-mail`          | `sebastian190030/mail-smartpot`          |
| `broker-smartpot`    | [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker)               | `ghcr.io/smartpottech/smartpot-broker`        | `sebastian190030/broker-smartpot`        |
| `ai-smartpot`        | [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI)                       | `ghcr.io/smartpottech/smartpot-ai`            | `sebastian190030/ai-smartpot`            |
| `api-smartpot`       | [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API)                     | `ghcr.io/smartpottech/smartpot-api`           | `sebastian190030/api-smartpot`           |
| `web-smartpot`       | [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web)                     | `ghcr.io/smartpottech/smartpot-web`           | `sebastian190030/web-smartpot`           |
| `simulator-smartpot` | [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | `ghcr.io/smartpottech/smartpot-datagenerator` | `sebastian190030/datagenerator-smartpot` |

Los despliegues descargan de **GHCR**; Docker Hub es una réplica para distribución. Cada repositorio publica en Docker
Hub cuando tiene los secrets `DOCKER_USERNAME` y `DOCKER_PASSWORD`.

Las lecturas llegan de tres fuentes: la maceta física con el firmware
de [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT), el mismo firmware en Wokwi (a mano, en el navegador) y
las macetas virtuales del simulador, siempre encendidas y controladas desde la PWA.

## Puertos

| Puerto                  | Servicio                     | Demo y desarrollo                          | Producción                           |
|-------------------------|------------------------------|--------------------------------------------|--------------------------------------|
| 5173                    | PWA                          | `127.0.0.1`                                | `127.0.0.1`, detrás de Nginx         |
| 8091                    | API                          | `127.0.0.1`                                | `127.0.0.1`, detrás de Nginx         |
| 1883                    | MQTT                         | `127.0.0.1`                                | Solo red interna                     |
| 8883                    | MQTT sobre TLS               | `127.0.0.1` (desarrollo, con certificados) | Público                              |
| 9001                    | MQTT sobre WebSocket         | `127.0.0.1`                                | `127.0.0.1`, detrás de Nginx (`wss`) |
| 8025                    | Bandeja de correo            | `127.0.0.1`                                | `127.0.0.1`, detrás de Nginx         |
| 27017, 6379, 8000, 1025 | MongoDB, Redis, IA, SMTP     | Solo en desarrollo                         | Solo red interna                     |
| 8081                    | API de control del simulador | Solo en desarrollo                         | Solo red interna                     |
