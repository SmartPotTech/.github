# SmartPot environment

## SmartPot - Guía de Ejecución Local

Este repositorio contiene el código para el proyecto **SmartPot**. Puedes ejecutar este proyecto localmente utilizando dos enfoques diferentes:

### Opciones de Ejecución Local

- **Ejecutar con Docker**: Para una ejecución rápida utilizando Docker y Docker Compose, sigue la guía [Docker](docker/README.md).
- **Ejecutar con Kubernetes**: Si prefieres usar Kubernetes, puedes seguir las instrucciones en la guía de [Kubernetes](kubernetes/README.md).

## Estructura del Proyecto

Este proyecto está compuesto por varios servicios:

- **MongoDB**: La base de datos que maneja la información de los cultivos y sensores.
- **API SmartPot**: El backend que interactúa con la base de datos y expone los endpoints REST.
- **Aplicación Web**: El frontend que se comunica con la API para mostrar la información y permitir la interacción con el sistema.
