# **Despliegue de SmartPot en Kubernetes**

El manifiesto [`k8s-deployment.yml`](k8s-deployment.yml) levanta SmartPot completo en un clúster local (Docker Desktop,
kind o minikube) con los datos demo y dos macetas simuladas. Está pensado para aprender y probar; para producción se
usa [Docker Compose](../docker/production/README.md).

---

## **Requisitos Previos**

* Un clúster de Kubernetes 1.29 o superior con un `StorageClass` por defecto.
* `kubectl` configurado contra ese clúster.

---

## **Ejecución Rápida**

```bash
kubectl apply -f https://raw.githubusercontent.com/SmartPotTech/.github/main/kubernetes/k8s-deployment.yml
kubectl -n smartpot rollout status deployment/api-smartpot --timeout=5m
```

| Servicio          | URL                                                           |
|-------------------|---------------------------------------------------------------|
| PWA               | http://localhost:30173 (`demo@smartpot.app` / `SmartPot2026`) |
| API               | http://localhost:30091 · http://localhost:30091/docs          |
| MQTT              | `localhost:31883` · WebSocket `ws://localhost:30901`          |
| Bandeja de correo | http://localhost:30825 (`admin` / `k8s-mailpit-ui-local`)     |

En minikube, reemplaza `localhost` por la IP de `minikube ip` y ajusta `WEB_BASE_URL`, `PUBLIC_API_URL`,
`CORS_ALLOWED_ORIGINS`, `API_URL` y `MQTT_*` en el `ConfigMap`.

---

## **Despliegue Paso a Paso**

1. Descarga el manifiesto:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/SmartPotTech/.github/main/kubernetes/k8s-deployment.yml -o k8s-deployment.yml
   ```

2. Cambia los valores del `Secret smartpot-secrets`: son contraseñas de ejemplo solo para clústeres locales.
   `SMARTPOT_AES_KEY` debe ser Base64 de 32 bytes (`openssl rand -base64 32`) y `MONGODB_URI` debe llevar la misma
   `SMARTPOT_DB_PASSWORD`.

3. Aplica y verifica:

   ```bash
   kubectl apply -f k8s-deployment.yml
   kubectl -n smartpot get pods
   curl -fsS http://localhost:30091/health
   ```

4. Elimina todo, incluidos los volúmenes:

   ```bash
   kubectl delete namespace smartpot
   ```

---

## **Recursos del Manifiesto**

| Recurso                  | Nombre                                              | Descripción                                                                                                               |
|--------------------------|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `Namespace`              | `smartpot`                                          | Aplica el perfil `restricted` de Pod Security                                                                             |
| `Secret`                 | `smartpot-secrets`                                  | Contraseñas, secreto JWT, llave AES y tokens de la IA y del simulador                                                     |
| `ConfigMap`              | `smartpot-config`                                   | URLs, usuarios y macetas simuladas                                                                                        |
| `PersistentVolumeClaim`  | `db-data`, `broker-data`, `ai-data`                 | MongoDB (2 Gi), cuentas MQTT (256 Mi) y lo aprendido por la IA (1 Gi)                                                     |
| `Deployment` + `Service` | `db`, `cache`, `mail`, `broker`, `ai`, `api`, `web` | Un pod por servicio                                                                                                       |
| `Deployment` + `Service` | `simulator-smartpot`                                | Macetas fijas de la lechuga y el tomate demo, y las macetas virtuales que pida la API (control interno en el puerto 8081) |

MongoDB, Redis, la IA y el simulador usan `ClusterIP`; la PWA, la API, el broker y la bandeja de correo se publican con
`NodePort`.

---

## **Seguridad de los Pods**

Todos los pods cumplen el perfil `restricted`:

* `runAsNonRoot` con el mismo usuario de la imagen (999 MongoDB, 999 Redis, 1000 Mailpit, 1883 Mosquitto, 1000 IA, API y
  simulador, 101 nginx).
* Sistema de archivos raíz de solo lectura, con `emptyDir` para `/tmp` y para la configuración que nginx genera al
  arrancar.
* Sin capacidades de Linux, sin escalada de privilegios y con `seccompProfile: RuntimeDefault`.
* `automountServiceAccountToken: false`: ningún pod necesita hablar con la API de Kubernetes.
* Límites de CPU y memoria en todos los contenedores, y sondas de arranque, disponibilidad y vida.

---

## **Imágenes Locales**

Para probar imágenes compiladas en tu equipo, etiquétalas como las publicadas antes de aplicar el manifiesto (con
`imagePullPolicy: IfNotPresent` el clúster usa la local):

```bash
docker build -t ghcr.io/smartpottech/smartpot-api:latest ../SmartPot-API
kubectl -n smartpot rollout restart deployment/api-smartpot
```

En kind, carga la imagen con `kind load docker-image ghcr.io/smartpottech/smartpot-api:latest`.
