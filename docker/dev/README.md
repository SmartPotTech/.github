# **Desarrollo de SmartPot con Docker**

El entorno de desarrollo compila cada servicio desde los repositorios clonados en tu máquina, así cualquier cambio local se prueba con la plataforma completa: base de datos, caché, correo, broker MQTT, IA, API, PWA y cultivos simulados.

---

## **Requisitos Previos**

* **Docker** con **Docker Compose v2.20 o superior**: [Instrucciones de instalación](https://docs.docker.com/get-docker/)
* Los repositorios clonados uno junto al otro:

```text
SmartPot/
├── .github/            # este repositorio
├── SmartPot-AI/
├── SmartPot-API/
├── SmartPot-Broker/
├── SmartPot-Cache/
├── SmartPot-DataGenerator/
├── SmartPot-DB/
├── SmartPot-Mail/
└── SmartPot-Web/
```

```bash
mkdir SmartPot && cd SmartPot
for repo in .github SmartPot-AI SmartPot-API SmartPot-Broker SmartPot-Cache SmartPot-DataGenerator SmartPot-DB SmartPot-Mail SmartPot-Web; do
  git clone https://github.com/SmartPotTech/$repo.git
done
```

---

## **Ejecución**

```bash
cd .github/docker/dev
cp .env.example .env
docker compose up -d --build --wait
```

| Servicio | URL local |
| --- | --- |
| PWA | http://localhost:5173 |
| API y documentación | http://localhost:8091 · http://localhost:8091/docs |
| IA y documentación | http://localhost:8000/docs (token en `SMARTPOT_AI_TOKEN`) |
| Bandeja de correo | http://localhost:8025 (`admin` / `MAILPIT_UI_PASSWORD`) |
| MQTT | `localhost:1883` · WebSocket `ws://localhost:9001` |
| MongoDB | `mongodb://smartpot:<SMARTPOT_DB_PASSWORD>@localhost:27017/smartpot?authSource=smartpot` |
| Redis | `localhost:6379` con `REDIS_PASSWORD` |

La base arranca con datos demo: `demo@smartpot.app` / `SmartPot2026`, con una lechuga en tubos NFT y un tomate en maceta, cultivos reales que publica el simulador (perfil `simulator`).

Para recompilar un solo servicio después de un cambio:

```bash
docker compose up -d --build api-smartpot
```

Para detener el entorno (`-v` borra también los datos):

```bash
docker compose down
```

---

## **TLS del Broker en Local**

El listener `8883` se activa solo si hay certificados en `./certs`:

```bash
sh ../../../SmartPot-Broker/scripts/generate-certs.sh certs localhost
docker compose restart broker-smartpot
```

---

## **Variables**

Todas están en [`.env.example`](.env.example) con valores de desarrollo. `SMARTPOT_REPOS` cambia la carpeta donde se buscan los repositorios y los `SMARTPOT_*_PORT` permiten mover los puertos si ya están ocupados.
