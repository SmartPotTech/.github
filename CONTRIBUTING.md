# Guía de Contribución

Gracias por aportar a **SmartPot**. Esta guía aplica a todos los repositorios de la organización.

## Repositorios

| Repositorio                                                                      | Contenido                                           | Stack                                          |
|----------------------------------------------------------------------------------|-----------------------------------------------------|------------------------------------------------|
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web)                     | PWA                                                 | React 19, TypeScript, Vite, Tailwind CSS, pnpm |
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API)                     | API REST y puente MQTT                              | Java 21, Spring Boot 4, MongoDB, Paho          |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI)                       | Asistente de IA                                     | Python 3.13, FastAPI, scikit-learn, uv         |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker)               | Broker MQTT                                         | Eclipse Mosquitto 2.1                          |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT)                     | Firmware de la maceta                               | MicroPython en ESP32, Wokwi                    |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | Macetas simuladas                                   | Python 3.13, paho-mqtt, uv                     |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB)                       | Base de datos                                       | MongoDB 8                                      |
| [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache)                 | Caché                                               | Redis 8                                        |
| [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail)                   | Correo                                              | Mailpit                                        |
| [.github](https://github.com/SmartPotTech/.github)                               | Entornos, despliegue, QA, documentación y comunidad | Docker Compose, Kubernetes, GitHub Actions     |

Abre el issue o el pull request en el repositorio del componente que cambias. Si el cambio toca varios componentes, abre
un pull request en cada repositorio y enlázalos entre sí.

## Flujo de trabajo

1. Crea un issue describiendo el problema o la mejora, salvo en cambios triviales.
2. Crea una rama desde `main`:

   | Tipo | Prefijo | Ejemplo |
      | --- | --- | --- |
   | Funcionalidad | `feature/` | `feature/perfil-cilantro` |
   | Corrección | `fix/` | `fix/ack-comandos` |
   | Documentación | `docs/` | `docs/guia-wokwi` |
   | Infraestructura | `ci/` | `ci/cache-uv` |

3. Haz commits pequeños, en inglés y empezando con un verbo en imperativo (`Add`, `Fix`, `Update`, `Remove`...). Cada
   commit cambia una sola cosa.
4. Abre un pull request hacia `main` completando la plantilla.
5. Espera a que pasen los checks (CI, CodeQL, revisión de dependencias) y la revisión de al menos una persona del
   equipo.

## Convenciones

* **Código en inglés; lo que ve el usuario en español.** Nombres de clases, funciones, variables y rutas en inglés.
  Mensajes de error, textos de la interfaz, logs y documentación en español.
* **Comentarios** solo cuando expliquen el porqué de algo que el código no deja claro, en español.
* **Gestores de paquetes:** Maven Wrapper en la API, pnpm en la web y uv en los servicios de Python. Se versionan los
  archivos de bloqueo (`pnpm-lock.yaml`, `uv.lock`).
* **Contrato MQTT** `smartpot/v1/{cropId}/…`: cualquier cambio se refleja a la vez en la API, el firmware, el simulador
  y la documentación.
* **Secretos:** nunca en el repositorio. Los `.env` reales, las claves de las macetas y las llaves privadas de los
  certificados quedan fuera de Git.

## Pruebas

Cada repositorio tiene sus pruebas y su workflow de CI. El workflow [QA](.github/workflows/qa.yml) de este repositorio
las ejecuta todas y, al final, una prueba de extremo a extremo sobre la demo (registro, cultivo, telemetría MQTT,
comandos, asistente y borrado de la cuenta).

```bash
# Prueba de extremo a extremo con la demo local levantada
python3 scripts/e2e.py
```

## Dependencias

Dependabot abre pull requests semanales agrupados. Revisa el changelog, confirma que el CI pasa y fusiona; las
actualizaciones mayores se prueban con el entorno completo antes.
