# **Documentación para Desplegar SmartPot en Minikube**

Esta documentación describe cómo desplegar y ejecutar el proyecto SmartPot en un entorno local utilizando **Minikube** y Kubernetes.

## **Requisitos Previos**

Antes de continuar, asegúrate de tener instalados y configurados los siguientes programas:

1. **Minikube**: [Instrucciones de instalación](https://minikube.sigs.k8s.io/docs/)
2. **Kubectl**: [Instrucciones de instalación](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
3. **Docker** (opcional, pero útil para imágenes locales): [Instrucciones de instalación](https://docs.docker.com/get-docker/)

**Nota:** Si aún no tienes Minikube instalado, puedes hacerlo siguiendo las instrucciones proporcionadas en el sitio oficial.

---

## **Cómo Ejecutar el Proyecto en Minikube**

> [!NOTE]\
> Antes de realizar cualquier paso, asegúrate de haber iniciado Minikube en tu máquina. Si aún no lo has hecho, puedes iniciar Minikube con el siguiente comando:
> 
> ```bash
> minikube start
> ```
> Espera a que Minikube esté completamente iniciado antes de continuar con los siguientes pasos.

### **Opción 1: Ejecución Rápida con un Solo Comando**

Para una forma rápida y sencilla de desplegar el proyecto en Minikube, puedes ejecutar el siguiente comando en tu terminal. Este comando descargará automáticamente el archivo `k8s-deployment.yml` desde el repositorio de GitHub y aplicará los recursos de Kubernetes:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/k8s-deployment.yml -o k8s-deployment.yml && kubectl apply -f k8s-deployment.yml
```

Este comando realiza lo siguiente:
1. **Descarga el archivo `k8s-deployment.yml`** desde el repositorio de GitHub.
2. **Aplica la configuración de Kubernetes** para crear los recursos necesarios, como **Pods**, **Servicios**, **Volúmenes**, y **Deployments**.

Una vez que el comando haya finalizado, podrás acceder a los siguientes servicios:

- **Base de Datos (MongoDB)**: `mongodb://admin:admin@localhost:27018/smartpot/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongo`
- **API SmartPot**: `http://localhost:8091`
- **Aplicación Web**: `http://localhost:5173`

Para obtener las URLs de acceso a los servicios de Minikube:

```bash
minikube service api-smartpot --url
minikube service web-smartpot --url
```

---

### **Opción 2: Despliegue Manual Paso a Paso**

Si prefieres realizar el despliegue manualmente, sigue estos pasos detallados:

#### **Paso 1: Inicializar Minikube**
Primero, asegúrate de tener Minikube en ejecución:

```bash
minikube start
```

Esto inicializa un clúster local de Kubernetes.

#### **Paso 2: Descargar el Archivo de Configuración Kubernetes**

Descarga el archivo de despliegue de Kubernetes para configurar los servicios necesarios:

```bash
curl -L https://raw.githubusercontent.com/SmartPotTech/.github/main/k8s-deployment.yml -o k8s-deployment.yml
```

#### **Paso 3: Aplicar la Configuración de Kubernetes**

Una vez descargado el archivo `k8s-deployment.yml`, aplica la configuración de Kubernetes para crear los recursos en el clúster:

```bash
kubectl apply -f k8s-deployment.yml
```

Este comando creará los **Pods**, **Deployments** y **Servicios** necesarios, y también gestionará el almacenamiento persistente para MongoDB.

#### **Paso 4: Acceder a los Servicios**

Después de que los recursos sean creados, puedes obtener las URLs de acceso a los servicios de Minikube con el siguiente comando:

```bash
minikube service api-smartpot --url
minikube service web-smartpot --url
```

Esto te dará las URLs donde puedes acceder a la API y a la aplicación web localmente.

#### **Paso 5: Detener los Servicios**

Para detener los servicios de Kubernetes, puedes eliminar los recursos creados con el siguiente comando:

```bash
kubectl delete -f k8s-deployment.yml
```

Este comando eliminará todos los recursos definidos en el archivo de despliegue, como **Pods** y **Servicios**.

---

## **Estructura del Proyecto en Kubernetes**

El archivo `k8s-deployment.yml` define varios recursos de Kubernetes que componen la infraestructura del proyecto SmartPot, incluidos los siguientes servicios:

1. **MongoDB (Base de Datos)**: Almacena los datos relacionados con los cultivos y sensores.
2. **API SmartPot (Backend)**: Expondrá los endpoints REST para interactuar con la base de datos.
3. **Web SmartPot (Frontend)**: Aplicación web que interactúa con la API para mostrar información sobre los cultivos.

## **Descripción de los Servicios en `k8s-deployment.yml`**

### **1. PersistentVolume (Volumen Persistente para MongoDB)**

El recurso `PersistentVolume` define la cantidad de almacenamiento que se asigna a la base de datos MongoDB. Asegura que los datos de la base de datos se mantengan entre reinicios del clúster.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mongo-data
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /mnt/data/mongo
```

### **2. PersistentVolumeClaim (Reclamación de Volumen para MongoDB)**

La reclamación de volumen asegura que el contenedor de MongoDB obtenga el almacenamiento persistente necesario.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-data-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### **3. Deployment para la API SmartPot**

El **Deployment** para la API SmartPot define la cantidad de réplicas y la configuración del contenedor, como las variables de entorno necesarias para la conexión a la base de datos.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-smartpot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api-smartpot
  template:
    metadata:
      labels:
        app: api-smartpot
    spec:
      containers:
        - name: api-smartpot
          image: sebastian190030/api-smartpot:latest
          ports:
            - containerPort: 8091
```

### **4. Service para la API SmartPot (Exponer la API)**

El **Service** para la API SmartPot expone el contenedor para que sea accesible desde fuera del clúster de Minikube mediante un puerto específico.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-smartpot
spec:
  selector:
    app: api-smartpot
  ports:
    - protocol: TCP
      port: 8091
      targetPort: 8091
  type: NodePort
```

### **5. Deployment para la Aplicación Web SmartPot (Frontend)**

El **Deployment** para la aplicación web SmartPot configura el frontend de la aplicación.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-smartpot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-smartpot
  template:
    metadata:
      labels:
        app: web-smartpot
    spec:
      containers:
        - name: web-smartpot
          image: sebastian190030/web-smartpot:latest
          ports:
            - containerPort: 5173
```

### **6. Service para la Aplicación Web SmartPot (Exponer el Frontend)**

El **Service** para la aplicación web expone el contenedor para que sea accesible desde fuera del clúster de Minikube.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-smartpot
spec:
  selector:
    app: web-smartpot
  ports:
    - protocol: TCP
      port: 5173
      targetPort: 5173
  type: NodePort
```
