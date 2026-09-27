"""Prueba de extremo a extremo sobre el entorno demo de SmartPot.

Recorre el camino completo de un usuario nuevo: registro, cultivo, telemetría MQTT,
comando con confirmación de la maceta, evaluación del asistente, panel general (totales,
series comparativas y análisis de flota), órdenes en bloque y borrado de la cuenta.
Solo usa la biblioteca estándar; publica por MQTT con mosquitto_pub dentro del broker.

    python3 scripts/e2e.py
    SMARTPOT_API_URL=http://localhost:8091 SMARTPOT_BROKER_CONTAINER=smartpot-demo-broker python3 scripts/e2e.py
"""

import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("SMARTPOT_API_URL", "http://localhost:8091").rstrip("/")
BROKER = os.environ.get("SMARTPOT_BROKER_CONTAINER", "smartpot-demo-broker")


class CheckFailed(Exception):
    pass


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | list | None]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)
    print(f"  ✔ {message}")


def wait_for(description: str, probe, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = probe()
        if result:
            return result
        time.sleep(1)
    raise CheckFailed(f"Tiempo agotado esperando: {description}")


def publish(username: str, password: str, topic: str, payload: dict) -> bool:
    command = ["docker", "exec", BROKER, "mosquitto_pub", "-h", "127.0.0.1", "-p", "1883",
               "-i", f"e2e-{username}", "-u", username, "-P", password, "-q", "1",
               "-t", topic, "-m", json.dumps(payload)]
    return subprocess.run(command, capture_output=True, text=True).returncode == 0


def main() -> None:
    print(f"SmartPot E2E contra {API}")

    status, health = call("GET", "/health")
    expect(status == 200 and health["status"] == "UP", "la API y sus dependencias están arriba")
    expect(all(health[key] == "UP" for key in ("database", "broker", "cache", "ai")),
           "base de datos, broker, caché e IA responden")

    status, body = call("GET", "/api/v1/crops")
    expect(status == 401 and "message" in body, "las rutas privadas exigen sesión")

    email = f"qa-{secrets.token_hex(4)}@smartpot.test"
    password = f"Qa{secrets.token_hex(6)}9z"
    status, body = call("POST", "/api/v1/auth/register",
                        {"name": "Prueba", "lastName": "Automática", "email": email, "password": password})
    expect(status == 201, "registro de un usuario nuevo")

    status, body = call("POST", "/api/v1/auth/login", {"email": email, "password": password})
    expect(status == 200 and body.get("token"), "ingreso con las credenciales nuevas")
    token = body["token"]

    try:
        run_flow(token)
    finally:
        status, _ = call("DELETE", "/api/v1/users/me", token=token)
        expect(status == 204, "borrado de la cuenta de prueba")

    print("E2E completado.")


def run_flow(token: str) -> None:
    status, body = call("POST", "/api/v1/crops", {"name": "Lechuga de prueba", "type": "LETTUCE"}, token)
    expect(status == 201 and body["device"]["key"], "creación del cultivo con credenciales de la maceta")
    crop, device = body["crop"], body["device"]
    crop_id, username, key, topics = crop["id"], device["username"], device["key"], device["topics"]

    reading = {"temperature": 19.5, "humidity": 62, "brightness": 850, "ph": 6.0, "tds": 700,
               "atmosphere": 1012, "soilMoisture": 71}
    wait_for("que el broker acepte la clave de la maceta",
             lambda: publish(username, key, topics["telemetry"], reading))
    expect(True, "la maceta publica telemetría con su clave")
    expect(not publish(username, "clave-incorrecta", topics["telemetry"], reading),
           "el broker rechaza una clave incorrecta")

    latest = wait_for("la lectura en la API",
                      lambda: (lambda r: r[1] if r[0] == 200 else None)(
                          call("GET", f"/api/v1/crops/{crop_id}/readings/latest", token=token)))
    expect(latest["measures"]["ph"] == 6.0, "la API guarda la lectura recibida por MQTT")

    status, actuators = call("GET", f"/api/v1/crops/{crop_id}/actuators", token=token)
    pump = next(a for a in actuators if a["type"] == "WATER_PUMP")
    status, command = call("POST", f"/api/v1/crops/{crop_id}/commands",
                           {"actuatorId": pump["id"], "action": "ACTIVATE", "durationSeconds": 5}, token)
    expect(status in (200, 201, 202) and command["status"] in ("PENDING", "SENT"), "envío de un comando a la bomba")

    publish(username, key, topics["commandAck"], {"id": command["id"], "status": "EXECUTED", "message": "E2E"})

    def executed():
        _, commands = call("GET", f"/api/v1/crops/{crop_id}/commands", token=token)
        return any(c["id"] == command["id"] and c["status"] == "EXECUTED" for c in commands or [])

    wait_for("la confirmación del comando", executed)
    expect(True, "la confirmación de la maceta marca el comando como ejecutado")

    status, insight = call("GET", f"/api/v1/crops/{crop_id}/insights", token=token)
    expect(status == 200 and 0 <= insight["health"]["index"] <= 100, "el asistente evalúa el cultivo")
    expect(bool(insight["summary"]), "el asistente entrega un resumen en español")

    status, overview = call("GET", "/api/v1/overview", token=token)
    expect(status == 200 and overview["totals"]["crops"] == 1, "el panel general resume la cuenta")

    status, series = call("GET", "/api/v1/overview/series?metric=ph&hours=1", token=token)
    points = series["series"][0]["points"] if status == 200 and series["series"] else []
    expect(len(points) >= 1 and points[0]["value"] == 6.0, "la serie comparativa agrega las lecturas del cultivo")

    status, fleet = call("GET", "/api/v1/overview/fleet", token=token)
    expect(status == 200 and fleet["crops"][0]["id"] == crop_id, "el asistente analiza todos los cultivos")

    status, bulk = call("POST", "/api/v1/commands/bulk", {"actuatorType": "FAN", "action": "DEACTIVATE"}, token)
    expect(status == 202 and bulk["sent"] == 1, "orden en bloque a todos los cultivos")

    status, history = call("GET", "/api/v1/commands?limit=10", token=token)
    expect(status == 200 and len(history) == 2, "el historial reúne los comandos de todos los cultivos")

    status, crops = call("PUT", "/api/v1/crops/automation", {"enabled": True}, token)
    expect(status == 200 and crops[0]["automationEnabled"], "modo automático en bloque")

    status, _ = call("DELETE", f"/api/v1/crops/{crop_id}", token=token)
    expect(status == 204, "borrado del cultivo")


if __name__ == "__main__":
    try:
        main()
    except (CheckFailed, KeyError, StopIteration, urllib.error.URLError) as error:
        print(f"  ✘ {error!r}")
        sys.exit(1)
