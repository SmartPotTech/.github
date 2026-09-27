# Políticas y Procedimientos de Seguridad de SmartPot

Este documento describe los procedimientos de seguridad y las políticas generales para los repositorios de la organización **SmartPotTech**.

- [Versiones soportadas](#versiones-soportadas)
- [Reportar una vulnerabilidad](#reportar-una-vulnerabilidad)
- [Política de divulgación](#política-de-divulgación)
- [Medidas del proyecto](#medidas-del-proyecto)

## Versiones soportadas

Solo la rama `main` de cada repositorio y las imágenes `latest` publicadas en GitHub Container Registry reciben correcciones de seguridad.

| Componente | Imagen | Soportada |
| --- | --- | --- |
| SmartPot-Web | `ghcr.io/smartpottech/smartpot-web:latest` | :white_check_mark: |
| SmartPot-API | `ghcr.io/smartpottech/smartpot-api:latest` | :white_check_mark: |
| SmartPot-AI | `ghcr.io/smartpottech/smartpot-ai:latest` | :white_check_mark: |
| SmartPot-Broker | `ghcr.io/smartpottech/smartpot-broker:latest` | :white_check_mark: |
| SmartPot-DB | `ghcr.io/smartpottech/smartpot-db:latest` | :white_check_mark: |
| SmartPot-Cache | `ghcr.io/smartpottech/smartpot-cache:latest` | :white_check_mark: |
| SmartPot-Mail | `ghcr.io/smartpottech/smartpot-mail:latest` | :white_check_mark: |
| SmartPot-DataGenerator | `ghcr.io/smartpottech/smartpot-datagenerator:latest` | :white_check_mark: |
| SmartPot-IoT | Firmware en `main` | :white_check_mark: |

## Reportar una vulnerabilidad

El equipo de **SmartPot** toma en serio todas las vulnerabilidades. **No abras un issue público.** Repórtala de forma privada:

1. Abre la pestaña **Security** del repositorio afectado y pulsa **Report a vulnerability**, o
2. escribe a `smartpottech@gmail.com`.

Describe el problema, los pasos para reproducirlo, el impacto y, si puedes, una propuesta de corrección. El equipo confirmará la recepción en un plazo de 72 horas y te mantendrá al tanto hasta la corrección y su anuncio.

Para vulnerabilidades en dependencias de terceros, repórtalas también a los mantenedores de esa dependencia.

## Política de divulgación

Al recibir un reporte, el equipo asignará una persona responsable que coordinará la corrección:

* Confirmar el problema y determinar las versiones afectadas.
* Auditar el código en busca de problemas similares.
* Publicar la corrección lo antes posible, junto con nuevas imágenes en GHCR.
* Publicar un aviso de seguridad (GitHub Security Advisory) una vez corregido.

## Medidas del proyecto

| Área | Medida |
| --- | --- |
| Autenticación | JWT HS256 con expiración, contraseñas con BCrypt, límite de peticiones por IP (más estricto en ingreso y registro) |
| Macetas | Una cuenta MQTT por maceta con acceso solo a sus tópicos; clave aleatoria de 192 bits cifrada con AES-GCM en la base y mostrada una sola vez |
| Transporte | HTTPS con HSTS en la web y la API; MQTT sobre TLS 1.2 con CA propia; WebSocket seguro |
| Web | CSP estricta, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` y `Permissions-Policy` |
| Servicios internos | MongoDB, Redis y la IA en una red sin salida a internet; la IA exige un token de servicio |
| Contenedores | Solo lectura, sin capacidades de Linux, `no-new-privileges`, usuarios sin privilegios y límites de recursos |
| Cadena de suministro | Dependabot, revisión de dependencias en cada pull request, CodeQL e imágenes con SBOM y atestación de procedencia |
| Secretos | Solo en GitHub Secrets; el `.env` existe en el servidor únicamente durante el despliegue y la llave del broker queda legible solo para su usuario |
