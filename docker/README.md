# SmartPot - Docker Environments

Este directorio contiene las configuraciones de **Docker Compose** utilizadas para ejecutar SmartPot en diferentes entornos.  
Cada entorno tiene sus propias variables, puertos y configuraciones adaptadas a su propósito dentro del ciclo de desarrollo y despliegue.

---

## Estructura General

| Carpeta | Entorno | Propósito |
|----------|----------|------------|
| [`demo/`](demo/README.md) | Demostración | Ejecutar una versión ligera para presentaciones o pruebas rápidas. |
| [`dev/`](dev/README.md) | Desarrollo | Uso local para programar y probar cambios. |
| [`staging/`](staging/README.md) | Preproducción | Entorno de pruebas previo al despliegue real. |
| [`production/`](production/README.md) | Producción | Despliegue final en el servidor o entorno público. |

---

## Desarrollo

**Ruta:** [`/docker/dev`](dev/README.md)  
**Propósito:** ejecutar servicios de SmartPot en local para desarrollo activo.

**Características principales:**
- Volúmenes montados para edición en tiempo real.
- Configuración ligera sin optimizaciones de seguridad.
- Recarga automática (hot reload) si aplica.
- Ideal para depurar o integrar nuevas funcionalidades.

---

## Staging

**Ruta:** [`/docker/staging`](staging/README.md)  
**Propósito:** replicar un entorno productivo controlado para validación antes del despliegue real.

**Características principales:**
- Configuración con archivos `.env` separados por servicio.
- Servicios externos simulados o reales (según pruebas).
- Uso de imágenes Docker construidas a partir de versiones estables.
- Permite pruebas de integración completas (API + Web + DB + Cache).

---

## Producción

**Ruta:** [`/docker/production`](production/README.md)  
**Propósito:** entorno optimizado y seguro para ejecutar SmartPot en servidores o VPS públicos.

**Características principales:**
- Despliegue con imágenes finales (sin dependencias de desarrollo).
- Variables y credenciales seguras cargadas desde `.env`.
- Conexión a servicios externos (MongoDB Atlas, Redis, Gmail, etc.).
- Configuración estable para monitoreo, escalabilidad y actualizaciones.