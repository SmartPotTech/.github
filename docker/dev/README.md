# **Despliegue de SmartPot en Dev con Docker**

Esta documentación describe cómo levantar y ejecutar el entorno **Dev** del proyecto **SmartPot** utilizando Docker Compose.
Este entorno sirve como punto de desarrollo, ideal para pruebas previas al despliegue final.

---

## **Requisitos Previos**

Asegúrate de tener instalados los siguientes programas en el servidor donde se desplegará el entorno:

* **Docker**: [Instrucciones de instalación](https://docs.docker.com/get-docker/)
* **Docker Compose**: Si no viene incluido con tu versión de Docker, puedes instalarlo siguiendo las [instrucciones oficiales](https://docs.docker.com/compose/install/).

---

## **Archivos Necesarios**

Antes de ejecutar el entorno, debes tener en el servidor los siguientes archivos dentro del mismo directorio:

* `docker-compose.yml`
* `.env.db`
* `.env.cache`
* `.env.api`
* `.env.web`

> [!IMPORTANT]
> Los archivos `.env` deben contener las configuraciones específicas de cada servicio.
> No es necesario detallar su contenido aquí, pero deben estar correctamente referenciados en el `docker-compose.yml`.

---

## **Ejecución Rápida del Entorno**

Puedes iniciar el entorno dev de **SmartPot** en un solo paso con el siguiente comando:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/dev/docker-compose.yml -o docker-compose.yml && docker-compose -p smartpot up -d
```

Este comando realiza las siguientes acciones:

1. **Descarga** el archivo `docker-compose.yml` correspondiente al entorno dev desde el repositorio.
2. **Levanta los contenedores** definidos en el archivo en segundo plano (`-d`).

Asegúrate de que los archivos `.env` se encuentren en el mismo directorio antes de ejecutar el comando.

Para detener el entorno:

```bash
docker-compose -p smartpot down
```

---

## **Estructura del Entorno**

El archivo `docker-compose.yml` de dev define una infraestructura compuesta por cuatro servicios principales:

* **MongoDB**: Base de datos del sistema SmartPot.
* **Redis**: Servicio de caché para optimizar el rendimiento.
* **API SmartPot**: Backend que gestiona la lógica de negocio y expone los endpoints REST.
* **Web SmartPot**: Interfaz de usuario (frontend) construida con React.

> [!NOTE]
> El servicio de correo (Mail Service) **no se utiliza** en este entorno, ya que SmartPot usa el **servicio de Gmail** configurado en la API para el envío de correos.

---

## **Descripción de Servicios**

### 1. **Base de Datos (MongoDB)**

Encargada de almacenar toda la información relacionada con usuarios, cultivos y sensores.

```yaml
db-smartpot:
  image: sebastian190030/db-smartpot:latest
  container_name: smartpot-db
  ports:
    - "27018:27017"
  volumes:
    - mongo_data:/data/db
  env_file:
    - .env.db
```

* **Puerto Externo:** `27018`
* **Datos Persistentes:** Volumen `mongo_data`
* **Configuración:** Variables desde `.env.db`

---

### 2. **Cache (Redis)**

Proporciona almacenamiento en memoria para mejorar la respuesta del sistema y reducir la carga en la base de datos.

```yaml
cache-smartpot:
  image: sebastian190030/cache-smartpot:latest
  container_name: smartpot-cache
  ports:
    - "6379:6379"
  env_file:
    - .env.cache
```

* **Puerto Externo:** `6379`
* **Configuración:** Variables desde `.env.cache`

---

### 3. **API SmartPot (Backend)**

Gestiona la lógica principal del sistema, la autenticación y la comunicación con la base de datos y Redis.

```yaml
api-smartpot:
  image: sebastian190030/api-smartpot:latest
  container_name: smartpot-api
  ports:
    - "8091:8091"
  depends_on:
    - db-smartpot
    - cache-smartpot
  env_file:
    - .env.api
```

* **Puerto Externo:** `8091`
* **Depende de:** `db-smartpot`, `cache-smartpot`
* **Configuración:** Variables desde `.env.api`

---

### 4. **Web SmartPot (Frontend)**

Aplicación web de interfaz de usuario, que consume la API para mostrar datos y controlar los dispositivos.

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
```

* **Puerto Externo:** `5173`
* **Depende de:** `api-smartpot`
* **Configuración:** Variables desde `.env.web`

---

## **Volúmenes y Red**

```yaml
volumes:
  mongo_data:

networks:
  network:
    driver: bridge
```

* **Volumen `mongo_data`**: Mantiene los datos de MongoDB de forma persistente.
* **Red `network`**: Permite la comunicación interna entre los servicios de SmartPot.

---

## **Acceso a los Servicios**

Una vez desplegado el entorno, podrás acceder a:

* **MongoDB** → `mongodb://user:passoword@<host>:27018/smartpot`
* **API SmartPot** → `http://<host>:8091`
* **Web SmartPot** → `http://<host>:5173`