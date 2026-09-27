# SmartPot 🌱

**Tu huerto hidropónico, en tu bolsillo.** SmartPot mide la temperatura, la humedad, la luz, el pH, los nutrientes y la humedad del sustrato de tus cultivos, te dice qué necesitan y, si quieres, se encarga de regarlos, iluminarlos y ventilarlos.

[smartpot.app](https://smartpot.app) · [Documentación](https://github.com/SmartPotTech/.github/tree/main/docs) · [Probar la demo](https://github.com/SmartPotTech/.github/tree/main/docker/demo)

## Cómo funciona

1. **La maceta** (ESP32 con MicroPython) envía sus lecturas por MQTT cifrado cada pocos segundos.
2. **La API** las guarda y las compara con el rango ideal de la especie: lechuga, tomate, fresa, albahaca, espinaca o pimentón.
3. **El asistente de IA** combina un sistema experto, lógica difusa, modelos de aprendizaje automático y un agente reactivo para diagnosticar el cultivo, calcular su índice de salud y proponer acciones. De noche entiende que la planta descansa.
4. **La app** (PWA instalable) muestra todo en tiempo real, envía alertas y permite encender la bomba, la luz o el ventilador, o dejar que el agente lo haga en modo automático.

## Repositorios

| Repositorio | Qué hace |
| --- | --- |
| [SmartPot-Web](https://github.com/SmartPotTech/SmartPot-Web) | Aplicación web progresiva en React |
| [SmartPot-API](https://github.com/SmartPotTech/SmartPot-API) | API REST y puente MQTT en Spring Boot |
| [SmartPot-AI](https://github.com/SmartPotTech/SmartPot-AI) | Asistente de IA en FastAPI y scikit-learn |
| [SmartPot-Broker](https://github.com/SmartPotTech/SmartPot-Broker) | Broker MQTT Mosquitto con una cuenta por maceta |
| [SmartPot-IoT](https://github.com/SmartPotTech/SmartPot-IoT) | Firmware de la maceta y simulación en Wokwi |
| [SmartPot-DataGenerator](https://github.com/SmartPotTech/SmartPot-DataGenerator) | Macetas simuladas para pruebas y demos |
| [SmartPot-DB](https://github.com/SmartPotTech/SmartPot-DB) · [SmartPot-Cache](https://github.com/SmartPotTech/SmartPot-Cache) · [SmartPot-Mail](https://github.com/SmartPotTech/SmartPot-Mail) | MongoDB, Redis y Mailpit endurecidos |
| [.github](https://github.com/SmartPotTech/.github) | Entornos, despliegue, QA y documentación |

## Tecnologías

React 19 · TypeScript · Tailwind CSS · Java 21 · Spring Boot 4 · Python 3.13 · FastAPI · scikit-learn · MicroPython · Eclipse Mosquitto · MongoDB · Redis · Docker · Kubernetes · GitHub Actions

## Contribuir

Lee la [guía de contribución](https://github.com/SmartPotTech/.github/blob/main/CONTRIBUTING.md) y la [política de seguridad](https://github.com/SmartPotTech/.github/blob/main/SECURITY.md). Todo el código está bajo licencia MIT.
