# SmartPot 🌱

**Tu huerto hidropónico, en tu bolsillo.** SmartPot mide la temperatura, la humedad, la luz, el pH, los nutrientes y la humedad del sustrato de tus cultivos, te dice qué necesitan y, si quieres, se encarga de regarlos, iluminarlos y ventilarlos.

[smartpot.app](https://smartpot.app) · [Documentación](https://github.com/SmartPotTech/.github/tree/main/docs) · [Diagramas generales](#la-plataforma-en-diagramas) · [Probar la demo](https://github.com/SmartPotTech/.github/tree/main/docker/demo)

## Cómo funciona

1. **La maceta** (ESP32 con MicroPython) envía sus lecturas por MQTT cifrado cada pocos segundos. ¿No tienes hardware? Enciende una **maceta virtual**: sigue el clima real de tu ciudad, los medidores que muevas o el día y la noche de la especie, y obedece y confirma las órdenes igual que una maceta física.
2. **La API** las guarda y las compara con el rango ideal de la especie: lechuga, tomate, fresa, albahaca, espinaca o pimentón.
3. **El asistente de IA** combina un sistema experto, lógica difusa, modelos de aprendizaje automático y un agente reactivo para diagnosticar el cultivo, calcular su índice de salud y proponer acciones. De noche entiende que la planta descansa. Además **aprende sin parar** de las lecturas reales de cada especie: anticipa cuándo hará falta regar o ventilar en la próxima hora y reconoce lo poco habitual, sin saber de qué cuenta viene cada lectura. Un modelo nuevo solo reemplaza al vigente si lo mejora.
4. **La app** (PWA instalable) muestra todo en tiempo real, envía alertas y permite encender la bomba, la luz o el ventilador, o dejar que el agente lo haga en modo automático.
5. **Telegram** te avisa aunque no tengas la app abierta: vinculas tu chat desde el perfil con un código de un solo uso, eliges qué avisos recibir y consultas cómo van tus cultivos con `/estado`.

## La plataforma en diagramas

Ocho diagramas generales muestran SmartPot completo. Cada uno se abre como SVG y se puede ampliar tanto como haga falta.

| Diagrama general | Qué muestra |
| --- | --- |
| [Arquitectura completa](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_01_Architecture.svg) | Las macetas, el borde, los ocho contenedores con sus módulos, puertos y redes, y los servicios externos |
| [Operación completa](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_02_Operation_Sequence.svg) | Toda la operación paso a paso: del registro a la lectura, la decisión de la IA, la orden a la maceta y el aviso por Telegram |
| [Entrega continua](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_03_Delivery.svg) | Del commit al servidor: pruebas, QA de extremo a extremo, imágenes y despliegue |
| [Linaje de los datos](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_04_Data_Lineage.svg) | De dónde sale cada dato, dónde se guarda y quién lo usa |
| [Máquinas de estado](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_05_State_Machines.svg) | Sesión, maceta, comando, salud, modo automático, aprendizaje, Telegram y maceta virtual |
| [Modelo de dominio](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_06_Domain_Model.svg) | Entidades y contratos con sus relaciones |
| [Recorrido de la app](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_07_User_Journey.svg) | Cada pantalla, qué pide a la API y quién responde |
| [Decisión de la IA](https://github.com/SmartPotTech/.github/blob/main/docs/diagrams/SmartPot_Global_08_AI_Decision.svg) | De la lectura a la orden: diagnóstico, pronóstico, modelos, reglas, índice difuso y agente |

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
