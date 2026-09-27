# SmartPot · Entornos, Despliegue y Documentación

[![QA](https://github.com/SmartPotTech/.github/actions/workflows/qa.yml/badge.svg)](https://github.com/SmartPotTech/.github/actions/workflows/qa.yml)
[![Deploy to Production](https://github.com/SmartPotTech/.github/actions/workflows/deploy.yml/badge.svg)](https://github.com/SmartPotTech/.github/actions/workflows/deploy.yml)

Repositorio central de **SmartPot**, la plataforma de monitoreo y automatización de cultivos hidropónicos publicada en [smartpot.app](https://smartpot.app). Reúne lo que no pertenece a un solo servicio: los entornos de Docker y Kubernetes, el despliegue a producción, la batería de QA, la documentación técnica y los archivos de comunidad de la organización.

## Contenido

```text
.github/
├── .github/
│   ├── workflows/
│   │   ├── deploy.yml          # Único despliegue a producción, de a uno (concurrency)
│   │   ├── request-deploy.yml  # Lo llaman los servicios para pedir el despliegue y esperar el resultado
│   │   └── qa.yml              # Pruebas de todos los repositorios y prueba de extremo a extremo
│   ├── ISSUE_TEMPLATE/         # Plantillas de issues de la organización
│   ├── dependabot.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── docker/
│   ├── demo/                   # SmartPot completo con un comando y datos de ejemplo
│   ├── dev/                    # Compila cada servicio desde los repositorios locales
│   └── production/             # Compose, variables, nginx y respaldos del servidor
├── kubernetes/                 # Manifiesto para clústeres locales
├── docs/                       # Documentación técnica, recorrido y ciclo de vida; diagramas específicos y generales
├── scripts/e2e.py              # Prueba de extremo a extremo sobre la demo
├── profile/README.md           # Presentación pública de la organización
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

## Arquitectura

```mermaid
flowchart LR
  M[Cultivo real: ESP32 o Wokwi<br>SmartPot-IoT] -->|MQTT TLS 8883| B[Broker<br>SmartPot-Broker]
  S[Cultivos virtuales<br>SmartPot-DataGenerator] -->|MQTT con la cuenta del cultivo| B
  S -->|clima real| O[Open-Meteo]
  U[PWA<br>SmartPot-Web] -->|HTTPS REST| A[API<br>SmartPot-API]
  A <-->|MQTT| B
  A -->|HTTP + token| S
  A --> D[(MongoDB<br>SmartPot-DB)]
  A --> C[(Redis<br>SmartPot-Cache)]
  A -->|SMTP| E[Mailpit<br>SmartPot-Mail]
  A -->|HTTP + token<br>evaluación y aprendizaje| I[Asistente de IA<br>SmartPot-AI]
  A <-->|avisos y webhook| T[Telegram]
  classDef platform fill:#DDF5EA,stroke:#067A52,color:#17261F
  classDef device fill:#FBE9E1,stroke:#B85A38,color:#17261F
  classDef store fill:#F2F7F4,stroke:#5B6B63,color:#17261F
  classDef external fill:#FDF4DD,stroke:#C98D12,color:#17261F
  classDef core fill:#067A52,stroke:#0B3D2B,color:#FFFFFF
  class A core
  class B,U,I,E,S platform
  class M device
  class D,C store
  class O,T external
```

Cada cultivo es **real** o **virtual**, y eso se elige al crearlo. Uno real publica sus lecturas en `smartpot/v1/{cropId}/telemetry` desde un ESP32 con el firmware, físico o simulado en Wokwi; uno virtual lo simula SmartPot, que sigue el clima de la ciudad, los medidores que mueva la persona o el día y la noche de la especie. Los dos se ven en vivo con su forma (maceta, tubos NFT, torre o balsa) y cada actuador. La API guarda cada lectura, pide al asistente de IA un diagnóstico (sistema experto, lógica difusa, modelos de aprendizaje automático y un agente reactivo) y, si el cultivo tiene el modo automático, envía comandos a los actuadores por `smartpot/v1/{cropId}/commands`. El asistente además **aprende de forma continua** con las lecturas de los cultivos reales de cada especie, seudonimizadas, para anticipar el riego y el calor de la próxima hora. Los avisos llegan a la PWA, que se instala en el teléfono, y a **Telegram** para quien vincula su chat.

Para ver cada pieza por dentro y toda la operación paso a paso están los [diagramas generales](docs/README.md#diagramas-generales).

## Empezar

| Quiero... | Guía |
| --- | --- |
| Ver SmartPot funcionando en mi equipo | [`docker/demo`](docker/README.md) |
| Programar en un servicio | [`docker/dev`](docker/dev/README.md) |
| Desplegar en un servidor | [`docker/production`](docker/production/README.md) |
| Probar en Kubernetes | [`kubernetes`](kubernetes/README.md) |
| Entender el sistema | [`docs`](docs/README.md) |
| Ver toda la plataforma en un solo diagrama | [Diagramas generales](docs/README.md#diagramas-generales) |

## QA

El workflow [`qa.yml`](.github/workflows/qa.yml) se ejecuta en cada cambio de este repositorio, cada lunes y a mano:

| Trabajo | Qué valida |
| --- | --- |
| API | Pruebas unitarias y de controladores con Maven |
| Web | Lint, tipos, pruebas con Vitest y build de producción |
| SmartPot-AI, -DataGenerator, -IoT | Ruff y pytest |
| SmartPot-Broker, -DB, -Cache, -Mail | Imagen endurecida y pruebas de humo (autenticación, ACL por cultivo, TLS, validadores de MongoDB) |
| End-to-End | Compila las ocho imágenes, levanta la demo y recorre registro, cultivo real, telemetría MQTT, comando con confirmación, asistente, panel general, órdenes en bloque, tipo fijo, cultivo virtual con pausa, aprendizaje continuo, canales y borrado de la cuenta |

## Despliegue

Cada servicio publica su imagen en `ghcr.io/smartpottech` (y en Docker Hub como réplica) y pide el despliegue a [`deploy.yml`](.github/workflows/deploy.yml), que actualiza el servidor por SSH con el `compose.yaml` de producción descargando las imágenes de GHCR. Los detalles, los secrets necesarios y la configuración de nginx están en [`docker/production`](docker/production/README.md).

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
