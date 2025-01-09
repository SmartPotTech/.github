# **Demostración Local de SmartPot con Docker**

Esta documentación describe cómo levantar y ejecutar el proyecto SmartPot en tu entorno local utilizando Docker Compose. Se describen los servicios involucrados, sus configuraciones y cómo ejecutar los contenedores.

## **Requisitos Previos**
Asegúrate de tener instalados los siguientes programas:
- **Docker**: [Instrucciones de instalación](https://docs.docker.com/get-docker/)
- **Docker Compose**: Viene integrado con Docker Desktop, pero si usas Linux o configuraciones personalizadas, asegúrate de tener Docker Compose instalado. [Instrucciones de instalación](https://docs.docker.com/compose/install/)

## **Cómo Ejecutar el Proyecto**

> [!NOTE]\
>  Antes de realizar cualquier paso, asegúrate de tener Docker en ejecución en tu máquina. Si estás utilizando Docker Desktop, abre la aplicación y espera a que esté completamente iniciado antes de continuar con los siguientes pasos.

### **Opción 1: Ejecución Rápida con un Solo Comando**

Si prefieres una forma más rápida de poner en marcha el proyecto, puedes utilizar el siguiente comando en la terminal. Este comando descargará automáticamente el archivo `docker-compose.yml` y levantará los contenedores en un solo paso:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/docker/docker-compose.yml -o docker-compose.yml && docker-compose -p smartpot up -d
```

Este comando realiza las siguientes acciones:
1. **Descarga el archivo `docker-compose.yml`** desde el repositorio de GitHub.
2. **Levanta los contenedores** en modo "detached" usando Docker Compose.

Una vez que los contenedores estén en funcionamiento, puedes acceder a los siguientes servicios:

- **Base de Datos (MongoDB)**: `mongodb://admin:admin@localhost:27018/smartpot/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongo`
- **API SmartPot**: `http://localhost:8091`
- **Aplicación Web**: `http://localhost:5173`

Para detener todos los servicios, ejecuta el siguiente comando:

```bash
docker-compose -p smartpot down
```

---

### **Opción 2: Ejecución Paso a Paso (Versión Extensa)**

Si prefieres realizar los pasos de manera más detallada, sigue estas instrucciones:

#### **Paso 1: Clonar o Descargar el Proyecto**
Asegúrate de tener todos los archivos necesarios en tu máquina local, incluyendo el archivo `docker-compose.yml`. Si no lo tienes, puedes descargarlo directamente desde el repositorio ejecutando el siguiente comando:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/docker-compose.yml -o docker-compose.yml
```

Este comando descargará el archivo `docker-compose.yml` necesario para continuar con la configuración del proyecto.

#### **Paso 2: Realizar el Pull de las Imágenes Docker**
Descarga las imágenes de los contenedores necesarios para el proyecto. Ejecuta los siguientes comandos en la terminal para obtener las imágenes más recientes:

```bash
docker pull sebastian190030/db-smartpot:latest
docker pull sebastian190030/api-smartpot:latest
docker pull sebastian190030/web-smartpot:latest
```

#### **Paso 3: Iniciar los Servicios con Docker Compose**

Desde el directorio donde se encuentra tu archivo `docker-compose.yml`, ejecuta el siguiente comando para iniciar los contenedores:

```bash
docker-compose -p smartpot up -d
```

Este comando:
- **`-p smartpot`**: Le da el nombre `smartpot` al proyecto, lo que afecta los nombres de los contenedores, redes y volúmenes.
- **`up -d`**: Levanta los contenedores en segundo plano (modo "detached").

#### **Paso 4: Acceder a los Servicios**

Una vez que los contenedores estén en funcionamiento, puedes acceder a los siguientes servicios:

- **Base de Datos (MongoDB)**: Accede a la base de datos usando la URI de conexión `mongodb://admin:admin@localhost:27018/smartpot/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongo`.
- **API SmartPot**: Accede a la API en `http://localhost:8091`.
- **Aplicación Web**: Accede a la aplicación frontend en `http://localhost:5173`.

#### **Paso 5: Detener los Servicios**

Para detener todos los servicios y eliminar los contenedores, ejecuta el siguiente comando:

```bash
docker-compose -p smartpot down
```

Este comando:
- Detiene y elimina todos los contenedores, redes y volúmenes definidos en el archivo `docker-compose.yml`.

---

Con esta organización, la documentación ahora tiene:

1. **Opción Rápida** primero, para quienes desean una puesta en marcha más veloz.
2. **Opción Extensa** después, para quienes prefieren un enfoque más detallado.
3. **Comando común** para detener los servicios al final.

¡Espero que ahora esté todo en el orden que necesitabas!



## **Estructura del Proyecto**
El archivo `docker-compose.yml` define los servicios que componen la infraestructura del proyecto:
- **MongoDB**: La base de datos que maneja toda la información relacionada con los cultivos y sensores.
- **API SmartPot**: El backend de la aplicación que interactúa con la base de datos y expone los endpoints REST.
- **Web SmartPot**: La aplicación frontend que se comunica con la API para mostrar información de los cultivos y permitir la interacción con el sistema.

## **Descripción de Servicios en `docker-compose.yml`**

### 1. **Servicio para la Base de Datos (MongoDB)**
Este servicio ejecuta un contenedor MongoDB, con la configuración necesaria para iniciar la base de datos `smartpot`.

```yaml
  db-smartpot:
    image: sebastian190030/db-smartpot:latest
    container_name: smartpot-db
    ports:
      - "27018:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - smartpot-network
```
**Configuración clave:**
- **Imagen**: Usa la imagen de Docker `sebastian190030/db-smartpot:latest`.
- **Puertos**: Expone el puerto 27017 del contenedor a 27018 en el host para acceder a la base de datos localmente.
- **Volúmenes**: Se utiliza un volumen (`mongo_data`) para persistir los datos de la base de datos.
- **Redes**: El contenedor se conecta a la red `smartpot-network` para comunicarse con otros servicios.

### 2. **Servicio para la API (Backend)**
Este servicio ejecuta el contenedor de la API de SmartPot, configurando las variables de entorno necesarias para conectarse a la base de datos MongoDB y manejar la lógica de autenticación y operaciones de la API.

```yaml
api-smartpot:
  image: sebastian190030/api-smartpot:latest
  container_name: smartpot-api
  environment:
      - APP_NAME=SmartPot-API
      - PORT=8091
      - TITLE=SmartPot API
      - DESCRIPTION=Documentación de la API REST de SmartPot
      - VERSION=1.0.0
      - AUTHOR=SmartPot Developers
      - DATA_CONNECTION_METHOD=mongodb
      - DATA_SOURCE_USERNAME=admin
      - DATA_SOURCE_PASSWORD=admin
      - DATA_SOURCE_DOMAIN=db-smartpot:27017
      - DATA_SOURCE_DB=smartpot
      - DATA_PARAMS=directConnection=true&serverSelectionTimeoutMS=100000&socketTimeoutMS=10000&appName=mongo
      - SECURITY_JWT_SECRET_KEY=c8e9b6803afbcfa6edd9569c94c75ff4b144622b0a0570a636dffd62c24a3476
      - SECURITY_JWT_EXPIRATION=86400000
      - SECURITY_PUBLIC_ROUTES=/auth/login,/auth/verify
      - HEADER_CORS_ALLOWED_ORIGINS=http://localhost:5173
      - SERVER_TOMCAT_TIMEOUT=600000
      - DEBUGGER_MODE=INFO
  ports:
    - "8091:8091"
  depends_on:
    - db-smartpot
  networks:
    - smartpot-network
```
**Configuración clave:**
- **Imagen**: Usa la imagen de Docker `sebastian190030/api-smartpot:latest`.
- **Variables de entorno**: Incluye detalles sobre el nombre de la API, configuración JWT, detalles de conexión a la base de datos MongoDB (`localhost:27018`), y CORS para la aplicación frontend.
- **Dependencias**: El servicio depende de `db-smartpot` para asegurar que la base de datos esté lista antes de iniciar la API.
- **Puertos**: Expone el puerto 8091 para que la API sea accesible desde el navegador.

### 3. **Servicio para la Aplicación Web (Frontend)**
Este servicio ejecuta el contenedor de la aplicación web, configurando la URL base de la API para que el frontend se comunique con el backend.

```yaml
web-smartpot:
  image: sebastian190030/web-smartpot:latest
  container_name: smartpot-web
  environment:
    - VITE_API_BASE_URL=http://localhost:8091
  ports:
    - "5173:5173"
  networks:
    - smartpot-network
```
**Configuración clave:**
- **Imagen**: Usa la imagen de Docker `sebastian190030/web-smartpot:latest`.
- **Variables de entorno**: Configura la variable `VITE_API_BASE_URL` para que el frontend se comunique con la API de SmartPot a través de `http://localhost:8091`.
- **Puertos**: Expone el puerto 5173 para acceder a la aplicación web.

### 4. **Volúmenes**
Para garantizar la persistencia de los datos de la base de datos MongoDB, se define un volumen:
```yaml
volumes:
  mongo_data:
```
El volumen `mongo_data` se utiliza para almacenar los datos de MongoDB en el sistema local.

### 5. **Redes**
Se define una red llamada `smartpot-network` para que los contenedores puedan comunicarse entre sí.

```yaml
networks:
  smartpot-network:
    driver: bridge
```
