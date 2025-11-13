# SmartPot - Docker Environments

Este directorio contiene las configuraciones de **Docker Compose** utilizadas para ejecutar **SmartPot** en diferentes entornos del ciclo de vida del proyecto.
Cada entorno define los servicios, variables y redes necesarios según su propósito: demostración, desarrollo o producción.

---

## Estructura General

| Carpeta                               | Entorno      | Propósito                                                                             |
| ------------------------------------- | ------------ | ------------------------------------------------------------------------------------- |
| [`demo/`](demo/README.md)             | Demostración | Ejecutar SmartPot localmente para mostrar funcionalidades o realizar pruebas rápidas. |
| [`dev/`](dev/README.md)               | Desarrollo   | Uso local para programar, probar y depurar cambios activamente.                       |
| [`production/`](production/README.md) | Producción   | Despliegue final en servidores o VPS públicos, con configuración optimizada y segura. |

---

## Demo

**Ruta:** [`/docker/demo`](demo/README.md)
**Propósito:** ejecutar una versión funcional de **SmartPot** con todos los servicios en contenedores locales para demostraciones o validaciones rápidas.

**Servicios incluidos:**

* **MongoDB (`db-smartpot`)** → Base de datos principal para SmartPot.
* **Redis (`cache-smartpot`)** → Caché para optimizar respuestas y reducir carga de consultas.
* **MailPit (`mail-smartpot`)** → Emulador de servidor SMTP para pruebas de correo.
* **API (`api-smartpot`)** → Backend REST construido en Spring Boot.
* **Web (`web-smartpot`)** → Interfaz web en React.

**Características principales:**

* Variables de entorno definidas directamente en el archivo.
* Montaje de volúmenes para persistencia de datos (`mongo_data`).
* Comunicación interna mediante una red compartida Docker (`network`).
* Puertos expuestos localmente:

  * MongoDB → `27018`
  * Redis → `6379`
  * MailPit → `8025 (web) / 1025 (SMTP)`
  * API → `8091`
  * Web → `5173`
* Ideal para **demos**, **pruebas de integración** o **validaciones funcionales rápidas**.

---

## Desarrollo

**Ruta:** [`/docker/dev`](dev/README.md)
**Propósito:** entorno local de desarrollo con configuración completa, usando archivos `.env` separados por servicio.

**Servicios incluidos:**

* **MongoDB (`db-smartpot`)** – Base de datos con credenciales desde `.env.db`.
* **Redis (`cache-smartpot`)** – Caché de datos con configuración desde `.env.cache`.
* **MailPit (`mail-smartpot`)** – Servicio de correo con autenticación de prueba definida en `.env.mail`.
* **API (`api-smartpot`)** – Backend con variables en `.env.api`.
* **Web (`web-smartpot`)** – Frontend React con configuración en `.env.web`.

**Características principales:**

* Cada servicio utiliza su propio archivo `.env`, facilitando ajustes sin modificar el compose.
* Persistencia de MongoDB mediante volumen `mongo_data`.
* Dependencias entre servicios (`depends_on`) definidas explícitamente.
* Red interna `network` para comunicación entre los contenedores.
* Misma exposición de puertos que en demo, pero con configuración modular.
* Permite **recarga en caliente**, **debugging** y **ajustes en tiempo real**.

---

## Producción

**Ruta:** [`/docker/production`](production/README.md)
**Propósito:** entorno optimizado para despliegue final de SmartPot en servidores, VPS o contenedores en la nube.

**Servicios incluidos:**

* **API (`api-smartpot`)** – Backend con variables de entorno seguras cargadas desde `.env.api`.
* **Web (`web-smartpot`)** – Interfaz de usuario en React conectada al backend definido en `.env.web`.

**Características principales:**

* Despliegue **ligero** con solo los servicios necesarios (sin bases locales).
* Conexión a **servicios externos** (MongoDB Atlas, Redis Cloud, SMTP real).
* Variables y credenciales gestionadas mediante archivos `.env`.
* Exposición de puertos:

  * API → `8091`
  * Web → `5173`
* Red interna `network` para comunicación entre frontend y backend.
* Configuración estable para **monitoreo**, **escalabilidad** y **mantenimiento**.

---

## 🧱 Red y Volúmenes

| Elemento     | Demo | Dev | Producción | Descripción                                       |
| ------------ | ---- | --- | ---------- | ------------------------------------------------- |
| `mongo_data` | ✅    | ✅   | ❌          | Volumen persistente para la base de datos local.  |
| `network`    | ✅    | ✅   | ✅          | Red compartida para comunicación entre servicios. |
