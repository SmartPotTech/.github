# **Despliegue de SmartPot en Entorno de Producción con Docker**

Este documento describe cómo desplegar el entorno **de producción** del proyecto **SmartPot** utilizando **Docker Compose**.
En este entorno, SmartPot se conecta a servicios externos (base de datos, caché y correo) para garantizar la máxima estabilidad y disponibilidad.

---

## **Requisitos Previos**

Asegúrate de tener instaladas las siguientes herramientas en el servidor de despliegue:

* **Docker**: [Instrucciones de instalación](https://docs.docker.com/get-docker/)
* **Docker Compose**: [Instalación oficial](https://docs.docker.com/compose/install/)

> [!NOTE]
> Se recomienda ejecutar este entorno en un servidor dedicado o una instancia cloud optimizada para producción.

---

## **Arquitectura del Entorno**

En producción, SmartPot utiliza infraestructura distribuida.
Solo se ejecutan los **contenedores esenciales (API y Web)**, mientras que los demás servicios se alojan externamente:

| Servicio     | Tipo             | Ubicación / Proveedor             |
| ------------ | ---------------- | --------------------------------- |
| API SmartPot | Docker Container | Servidor Principal                |
| Web SmartPot | Docker Container | Servidor Principal                |
| MongoDB      | Externo          | MongoDB Atlas                     |
| Redis Cache  | Externo          | Servicio en línea                 |
| SMTP (Email) | Externo          | Gmail (cuenta configurada en API) |

---

## **Archivos Requeridos**

Antes de levantar el entorno, asegúrate de tener los siguientes archivos en el mismo directorio:

* `docker-compose.yml`
* `.env.api`
* `.env.web`

> [!IMPORTANT]
> Cada archivo `.env` debe contener las credenciales y configuraciones de producción,
> incluyendo las URLs de MongoDB Atlas, Redis y Gmail.

---

## **Ejecución del Entorno de Producción**

Puedes levantar el entorno completo con un solo comando:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/production/docker-compose.yml -o docker-compose.yml && docker-compose -p smartpot up -d
```

Este comando:

1. Descarga el archivo `docker-compose.yml` del entorno de producción.
2. Levanta los contenedores en segundo plano (`-d`) bajo el proyecto `smartpot`.

Para detener los contenedores en ejecución:

```bash
docker-compose -p smartpot down
```

---

## **Servicios del Entorno**

### 1. **API SmartPot (Backend)**

Gestiona toda la lógica de negocio, autenticación y comunicación con los servicios externos.
Conecta con **MongoDB Atlas**, **Redis remoto** y **Gmail** según las variables configuradas.

```yaml
api-smartpot:
  image: sebastian190030/api-smartpot:latest
  container_name: smartpot-api
  ports:
    - "8091:8091"
  env_file:
    - .env.api
  networks:
    - network
```

* **Puerto Externo:** `8091`
* **Configuración:** `.env.api`
* **Dependencias externas:** MongoDB Atlas, Redis y Gmail

---

### 2. **Web SmartPot (Frontend)**

Interfaz de usuario desarrollada en React. Consume los endpoints de la API para mostrar datos de sensores, usuarios y cultivos.

```yaml
web-smartpot:
  image: sebastian190030/web-smartpot:latest
  container_name: smartpot-web
  ports:
    - "5173:5173"
  depends_on:
    - api-smartpot
  env_file:
    - .env.web
  networks:
    - network
```

* **Puerto Externo:** `5173`
* **Configuración:** `.env.web`
* **Dependencia:** `api-smartpot`

---

## **Red**

```yaml
networks:
  network:
    driver: bridge
```

* Red interna **bridge** para la comunicación entre la API y la aplicación web.

---

## **Acceso al Entorno**

Una vez desplegado:

* **API SmartPot:** `http://<host>:8091`
* **Web SmartPot:** `http://<host>:5173`

> [!TIP]
> En un despliegue real, se recomienda usar **Nginx o Traefik** como proxy reverso para manejar certificados SSL y redirecciones HTTPS.