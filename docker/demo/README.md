# **Demostración de SmartPot con Docker**

La demo levanta SmartPot completo en tu computador con un solo comando: base de datos con datos de ejemplo, caché, correo, broker MQTT, asistente de IA con aprendizaje continuo, API, PWA y el simulador de cultivos, con dos cultivos reales que envían lecturas cada 15 segundos y la opción de encender macetas virtuales con el clima real de cualquier lugar.

> [!WARNING]
> Las contraseñas de [`compose.yaml`](compose.yaml) son públicas. Úsala solo en tu equipo: todos los puertos escuchan únicamente en `127.0.0.1`.

---

## **Requisitos Previos**

* **Docker** con **Docker Compose v2.20 o superior**: [Instrucciones de instalación](https://docs.docker.com/get-docker/)
* Unos 2 GB de memoria libre.

---

## **Ejecución Rápida**

Las imágenes se publican en dos registros con el mismo contenido. Elige uno:

### GitHub Container Registry (recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo/compose.yaml -o compose.yaml
docker compose up -d --wait
```

### Docker Hub

```bash
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/demo/compose.dockerhub.yaml -o compose.dockerhub.yaml
docker compose -f compose.yaml -f compose.dockerhub.yaml up -d --wait
```

| Registro | Imágenes |
| --- | --- |
| GHCR | `ghcr.io/smartpottech/smartpot-<componente>` |
| Docker Hub | `docker.io/sebastian190030/<componente>-smartpot` |

Con Docker Hub, los comandos de detener también llevan `-f compose.yaml -f compose.dockerhub.yaml`.

Abre http://localhost:5173 e ingresa con:

| Correo | Contraseña |
| --- | --- |
| `demo@smartpot.app` | `SmartPot2026` |

Verás dos cultivos en línea: **Lechugas del balcón**, con el modo automático activo (el agente de IA riega, enciende la luz o ventila por su cuenta), y **Tomates cherry**, donde el asistente solo recomienda.

| Servicio | URL |
| --- | --- |
| PWA | http://localhost:5173 |
| API | http://localhost:8091 · documentación en http://localhost:8091/docs |
| Estado de los servicios | http://localhost:8091/health |
| Bandeja de correo | http://localhost:8025 (`admin` / `demo-mailpit-ui`) |
| MQTT | `localhost:1883` · WebSocket `ws://localhost:9001` |

Los correos de recuperación de contraseña llegan a la bandeja de Mailpit.

---

## **Qué Probar**

| Función | Dónde |
| --- | --- |
| **Cultivo en vivo**: las lechugas en tubos NFT y los tomates en maceta de la demo, con cada actuador; enciende la bomba o el ventilador y mira la escena | Detalle de un cultivo › Cultivo en vivo |
| **Cultivo virtual** con el clima real: crea uno virtual, elige su forma y una ciudad, y mira la escena (sol, nubes, lluvia o noche) y las lecturas | Mis cultivos › Nuevo cultivo › Virtual |
| **Medidores manuales**: baja la humedad del sustrato y observa al asistente regar con el modo automático | Cultivo virtual › Cultivo en vivo › Simulación › Manual |
| **Aprendizaje**: lecturas reales por especie, calidad de datos y comparación de modelos (el primer entrenamiento llega tras unas 200 lecturas de la especie, cerca de una hora) | Aprendizaje |
| **Telegram** (opcional): crea un bot con [@BotFather](https://t.me/BotFather) y levanta la demo con `TELEGRAM_BOT_TOKEN=<token> TELEGRAM_BOT_USERNAME=<bot> docker compose up -d --wait`; luego vincúlalo desde Perfil › Notificaciones | Perfil |

---

## **Conectar un Cultivo Propio**

En la PWA crea un cultivo y elige, de una vez, cómo le llegarán las lecturas:

- **Virtual** (lo más simple): SmartPot lo simula con clima real, medidores manuales o día y noche, sin nada más que instalar. Sus controles están en **Cultivo en vivo**.
- **Real con Wokwi o con un ESP32**: la API genera la clave del dispositivo y la muestra **una sola vez** junto con la guía de conexión; la guía y la configuración para el firmware (`config.py`) de [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) siguen en la pestaña **Dispositivo**.
- **Real con el simulador por línea de comandos**, que publica con la clave como lo haría un ESP32:

```bash
docker run --rm --network smartpot-demo_internal \
  -e MQTT_HOST=broker-smartpot \
  -e SIMULATOR_DEVICES=<cropId>:<clave>:LETTUCE \
  ghcr.io/smartpottech/smartpot-datagenerator:latest
```

---

## **Detener**

```bash
docker compose down        # conserva los datos
docker compose down -v     # borra también la base de datos y el broker
```

---

## **Servicios**

| Contenedor | Imagen | Función |
| --- | --- | --- |
| `smartpot-demo-db` | `smartpot-db` | MongoDB 8 con validadores y datos demo |
| `smartpot-demo-cache` | `smartpot-cache` | Redis 8 para el límite de peticiones y la caché de la IA |
| `smartpot-demo-mail` | `smartpot-mail` | Mailpit con SMTP autenticado |
| `smartpot-demo-broker` | `smartpot-broker` | Mosquitto 2.1 con una cuenta MQTT por cultivo |
| `smartpot-demo-ai` | `smartpot-ai` | Sistema experto, lógica difusa, modelos de ML y agente |
| `smartpot-demo-api` | `smartpot-api` | API REST en Spring Boot 4 |
| `smartpot-demo-web` | `smartpot-web` | PWA en React servida por nginx |
| `smartpot-demo-simulator` | `smartpot-datagenerator` | Los dos cultivos demo y los cultivos virtuales que crees desde la PWA |

MongoDB, Redis y la IA viven en una red interna sin salida a internet; solo la API, la PWA, el broker y la bandeja de correo publican puertos, y únicamente en `127.0.0.1`. El simulador sale a internet solo para consultar el clima y no publica puertos. Lo aprendido por la IA se guarda en el volumen `ai_data`.
