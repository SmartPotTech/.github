"""Prueba de extremo a extremo sobre el entorno demo de SmartPot.

Recorre el camino completo de un usuario nuevo: registro, cultivo real, telemetría MQTT,
comando con confirmación del dispositivo, switches de los actuadores, evaluación del asistente,
lugar del cultivo con su consejo y su clima, panel general (totales, series comparativas y
análisis de flota), órdenes en bloque, cultivo virtual con su simulación, aprendizaje continuo,
canales de notificación con los avisos por cultivo y borrado de la cuenta.
Solo usa la biblioteca estándar; publica por MQTT con mosquitto_pub dentro del broker.

    python3 scripts/e2e.py
    SMARTPOT_API_URL=http://localhost:8091 SMARTPOT_BROKER_CONTAINER=smartpot-demo-broker python3 scripts/e2e.py
"""

import http.cookiejar
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
if not os.environ.get("SMARTPOT_BROKER_CONTAINER"):
    check_beta = subprocess.run(["docker", "ps", "--filter", "name=smartpot-demo-beta-broker", "--format", "{{.Names}}"],
                                capture_output=True, text=True)
    if "smartpot-demo-beta-broker" in check_beta.stdout:
        BROKER = "smartpot-demo-beta-broker"


class CheckFailed(Exception):
    pass


class WebSession:
    """Sesión web que conserva las cookies (smartpot_session HttpOnly y smartpot_csrf) y el token CSRF."""

    def __init__(self) -> None:
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.csrf: str | None = None
        self.last_set_cookies: list[str] = []

    def has_http_only_session(self) -> bool:
        has_cookie = any(c.name == "smartpot_session" and bool(c.value) for c in self.cookies)
        has_flag = any(
            header.startswith("smartpot_session=") and "httponly" in header.lower()
            for header in self.last_set_cookies
        )
        return has_cookie and has_flag


def call(
    method: str,
    path: str,
    body: dict | None = None,
    token: WebSession | str | None = None,
    include_csrf: bool = True,
) -> tuple[int, dict | list | None]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    request.add_header("Content-Type", "application/json")
    opener_fn = urllib.request.urlopen
    if isinstance(token, WebSession):
        opener_fn = token.opener.open
        if include_csrf and token.csrf and method not in ("GET", "HEAD", "OPTIONS"):
            request.add_header("X-CSRF-Token", token.csrf)
    elif isinstance(token, str) and token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with opener_fn(request, timeout=20) as response:
            if isinstance(token, WebSession):
                token.last_set_cookies = response.headers.get_all("Set-Cookie") or []
                csrf_hdr = response.headers.get("X-CSRF-Token")
                if csrf_hdr:
                    token.csrf = csrf_hdr
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
    raise CheckFailed(f"Timed out waiting for: {description}")


def publish(username: str, password: str, topic: str, payload: dict) -> bool:
    command = ["docker", "exec", BROKER, "mosquitto_pub", "-h", "127.0.0.1", "-p", "1883",
               "-i", f"e2e-{username}", "-u", username, "-P", password, "-q", "1",
               "-t", topic, "-m", json.dumps(payload)]
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode == 0:
        return True

    network = os.environ.get("SMARTPOT_DOCKER_NETWORK")
    if not network:
        net_inspect = subprocess.run(["docker", "inspect", BROKER, "--format", "{{json .NetworkSettings.Networks}}"],
                                     capture_output=True, text=True)
        if net_inspect.returncode == 0 and "smartpot-demo-beta_internal" in net_inspect.stdout:
            network = "smartpot-demo-beta_internal"
        elif net_inspect.returncode == 0 and "smartpot-demo_internal" in net_inspect.stdout:
            network = "smartpot-demo_internal"
        else:
            network = "smartpot-demo-beta_internal"

    broker_host = os.environ.get("SMARTPOT_BROKER_HOST", "broker-smartpot")
    command_aux = ["docker", "run", "--rm", "--network", network, "eclipse-mosquitto:2.0",
                   "mosquitto_pub", "-h", broker_host, "-p", "1883",
                   "-i", f"e2e-{username}", "-u", username, "-P", password, "-q", "1",
                   "-t", topic, "-m", json.dumps(payload)]
    return subprocess.run(command_aux, capture_output=True, text=True).returncode == 0


def main() -> None:
    print(f"SmartPot E2E against {API}")

    status, health = call("GET", "/health")
    expect(status == 200 and health["status"] == "UP", "API and its dependencies are UP")
    expect(all(health[key] == "UP" for key in ("database", "broker", "cache", "ai", "simulator")),
           "base de datos, broker, caché, IA y simulador responden")

    status, body = call("GET", "/api/v1/crops")
    expect(status == 401 and "message" in body, "private routes require active session")

    email = f"qa-{secrets.token_hex(4)}@smartpot.test"
    password = f"Qa{secrets.token_hex(6)}9z"
    reg_session = WebSession()
    status, body = call("POST", "/api/v1/auth/register",
                        {"name": "Prueba", "lastName": "Automática", "email": email, "password": password},
                        reg_session)
    expect(status == 201 and "token" not in (body or {}) and reg_session.has_http_only_session(),
           "registration of new user with HttpOnly cookie without exposing JWT in JSON")

    token = WebSession()
    status, body = call("POST", "/api/v1/auth/login", {"email": email, "password": password}, token)
    expect(status == 200 and "token" not in (body or {}) and token.has_http_only_session() and bool(token.csrf),
           "login with new credentials via HttpOnly cookie and CSRF token")

    status_csrf, _ = call("POST", "/api/v1/crops",
                          {"name": "Sin CSRF", "type": "LETTUCE", "kind": "REAL", "form": "NFT"},
                          token, include_csrf=False)
    expect(status_csrf == 403, "mutations without X-CSRF-Token are rejected (403)")

    try:
        run_flow(token)
    finally:
        status, _ = call("DELETE", "/api/v1/users/me", token=token)
        expect(status == 204, "test account deletion")

    print("E2E completed successfully.")


def run_flow(token: WebSession | str) -> None:
    status, body = call("POST", "/api/v1/crops",
                        {"name": "Lechuga de prueba", "type": "LETTUCE", "kind": "REAL", "form": "NFT"}, token)
    expect(status == 201 and body["device"]["key"], "real crop creation with device credentials")
    expect(body["crop"]["kind"] == "REAL" and body["crop"]["form"] == "NFT", "crop preserves kind and form")
    crop, device = body["crop"], body["device"]
    crop_id, username, key, topics = crop["id"], device["username"], device["key"], device["topics"]

    reading = {"temperature": 19.5, "humidity": 62, "brightness": 850, "ph": 6.0, "tds": 700,
               "atmosphere": 1012, "soilMoisture": 71}
    wait_for("que el broker acepte la clave del dispositivo",
             lambda: publish(username, key, topics["telemetry"], reading))
    expect(True, "device publishes telemetry with key")
    expect(not publish(username, "clave-incorrecta", topics["telemetry"], reading),
           "broker rejects incorrect key")

    latest = wait_for("la lectura en la API",
                      lambda: (lambda r: r[1] if r[0] == 200 else None)(
                          call("GET", f"/api/v1/crops/{crop_id}/readings/latest", token=token)))
    expect(latest["measures"]["ph"] == 6.0, "API persists reading received via MQTT")

    status, actuators = call("GET", f"/api/v1/crops/{crop_id}/actuators", token=token)
    pump = next(a for a in actuators if a["type"] == "WATER_PUMP")
    fan = next(a for a in actuators if a["type"] == "FAN")
    status, command = call("POST", f"/api/v1/crops/{crop_id}/commands",
                           {"actuatorId": pump["id"], "action": "ACTIVATE", "durationSeconds": 60}, token)
    expect(status in (200, 201, 202) and command["status"] in ("PENDING", "SENT"), "command dispatch to pump")

    status, body = call("POST", f"/api/v1/crops/{crop_id}/commands",
                        {"actuatorId": pump["id"], "action": "DEACTIVATE"}, token)
    expect(status == 409 and any(m in body["message"].lower() for m in ("in progress", "en curso")), "no overlapping orders to same actuator")

    publish(username, key, topics["commandAck"], {"id": command["id"], "status": "EXECUTED", "message": "E2E"})

    def executed():
        _, commands = call("GET", f"/api/v1/crops/{crop_id}/commands", token=token)
        return any(c["id"] == command["id"] and c["status"] == "EXECUTED" for c in commands or [])

    wait_for("la confirmación del comando", executed)
    expect(True, "device ACK marks command as executed")

    status, actuators = call("GET", f"/api/v1/crops/{crop_id}/actuators", token=token)
    pump = next(a for a in actuators if a["type"] == "WATER_PUMP")
    expect(pump["running"] and not pump["active"] and pump.get("runningUntil"),
           "pump switch remains on until duration expires")

    status, body = call("POST", f"/api/v1/crops/{crop_id}/commands",
                        {"actuatorId": fan["id"], "action": "DEACTIVATE"}, token)
    expect(status == 409 and any(m in body["message"].lower() for m in ("already off", "ya está apagado")),
           "redundant order is rejected (409)")

    status, insight = call("GET", f"/api/v1/crops/{crop_id}/insights", token=token)
    expect(status == 200 and 0 <= insight["health"]["index"] <= 100, "assistant evaluates crop")
    expect(bool(insight["summary"]), "assistant provides diagnostic summary")
    expect(insight.get("learning", {}).get("source") in ("BASE", "LEARNED"), "evaluation reports continual learning state")
    expect(insight["placement"]["level"] == "UNKNOWN", "without location, assistant queries crop placement")

    check_placement(token, crop_id)

    status, overview = call("GET", "/api/v1/overview", token=token)
    expect(status == 200 and overview["totals"]["crops"] == 1, "overview summarizes account")

    status, series = call("GET", "/api/v1/overview/series?metric=ph&hours=1", token=token)
    points = series["series"][0]["points"] if status == 200 and series["series"] else []
    expect(len(points) >= 1 and points[0]["value"] == 6.0, "comparative series aggregates crop readings")

    status, fleet = call("GET", "/api/v1/overview/fleet", token=token)
    expect(status == 200 and fleet["crops"][0]["id"] == crop_id, "assistant evaluates all crops in fleet")

    status, bulk = call("POST", "/api/v1/commands/bulk", {"actuatorType": "FAN", "action": "DEACTIVATE"}, token)
    expect(status == 202 and bulk["skipped"] == 1 and any(m in bulk["results"][0]["message"].lower() for m in ("already off", "ya está apagado")),
           "redundant bulk command is skipped (409)")

    status, bulk = call("POST", "/api/v1/commands/bulk",
                        {"actuatorType": "FAN", "action": "ACTIVATE", "durationSeconds": 60}, token)
    expect(status == 202 and bulk["sent"] == 1, "bulk command to all crops")

    status, history = call("GET", "/api/v1/commands?limit=10", token=token)
    expect(status == 200 and len(history) == 2, "command history gathers all crop commands")

    status, crops = call("PUT", "/api/v1/crops/automation", {"enabled": True}, token)
    expect(status == 200 and crops[0]["automationEnabled"], "bulk automation mode")

    check_kinds(token, crop_id)
    check_virtual_crop(token)
    check_learning(token)

    check_channels(token, crop_id)

    status, _ = call("DELETE", f"/api/v1/crops/{crop_id}", token=token)
    expect(status == 204, "crop deletion")


def check_placement(token: str, crop_id: str) -> None:
    status, _ = call("GET", f"/api/v1/crops/{crop_id}/weather", token=token)
    expect(status == 204, "without location no weather is available")

    placement = {"setting": "OUTDOOR", "exposure": "PARTIAL_SUN",
                 "location": {"name": "Medellín, Antioquia", "latitude": 6.25, "longitude": -75.56}}
    status, crop = call("PUT", f"/api/v1/crops/{crop_id}",
                        {"name": "Lechuga de prueba", "type": "LETTUCE", "placement": placement}, token)
    expect(status == 200 and crop["placement"]["setting"] == "OUTDOOR"
           and crop["placement"]["location"]["name"] == "Medellín, Antioquia", "crop preserves placement")

    status, weather = call("GET", f"/api/v1/crops/{crop_id}/weather", token=token)
    expect(status == 204 or (status == 200 and "temperature" in weather),
           "location weather returned or reported unavailable")

    status, insight = call("GET", f"/api/v1/crops/{crop_id}/insights", token=token)
    advice = insight["placement"]
    expect(advice["level"] == "OK" and advice["idealExposure"] == "PARTIAL_SUN",
           "assistant approves partial sun for lettuce")


def check_channels(token: str, crop_id: str) -> None:
    status, channels = call("GET", "/api/v1/channels", token=token)
    telegram = next(channel for channel in channels if channel["type"] == "TELEGRAM")
    expect(status == 200 and not telegram["available"] and "TELEGRAM_BOT_TOKEN" in telegram["requirements"],
           "without bot, Telegram appears unavailable reporting requirements")

    status, settings = call("GET", f"/api/v1/crops/{crop_id}/channels", token=token)
    telegram = next(channel for channel in settings if channel["type"] == "TELEGRAM")
    expect(status == 200 and not telegram["available"] and not telegram["linked"],
           "crop alerts report if channel is available and linked")

    status, body = call("PUT", f"/api/v1/crops/{crop_id}/channels/TELEGRAM", {"delivery": "DIGEST"}, token)
    expect(status == 503 and any(m in body["message"].lower() for m in ("not configured", "no está configurado")),
           "unconfigured channel returns 503")


def check_kinds(token: str, crop_id: str) -> None:
    status, _ = call("PUT", f"/api/v1/crops/{crop_id}/virtual-device", {"mode": "AUTO"}, token)
    expect(status == 400, "real crop cannot be simulated")
    status, _ = call("PUT", f"/api/v1/crops/{crop_id}",
                     {"name": "Lechuga de prueba", "type": "LETTUCE", "kind": "VIRTUAL"}, token)
    expect(status == 400, "real crop cannot transition to virtual")


def check_virtual_crop(token: str) -> None:
    status, _ = call("POST", "/api/v1/crops", {"name": "Clima sin lugar", "type": "BASIL", "kind": "VIRTUAL",
                                               "virtual": {"mode": "WEATHER"}}, token)
    expect(status == 400, "weather mode requires location")

    status, body = call("POST", "/api/v1/crops", {
        "name": "Lechuga virtual", "type": "LETTUCE", "kind": "VIRTUAL", "form": "TOWER",
        "virtual": {"mode": "MANUAL", "intervalSeconds": 10,
                    "manual": {"soilMoisture": 42, "ph": 6.8, "temperature": 21}}}, token)
    expect(status == 201 and body["crop"]["kind"] == "VIRTUAL" and not body.get("device"),
           "virtual crop created without device credentials")
    crop_id = body["crop"]["id"]
    path = f"/api/v1/crops/{crop_id}/virtual-device"

    status, actuators = call("GET", f"/api/v1/crops/{crop_id}/actuators", token=token)
    expect(status == 200 and len(actuators) == 6, "virtual crop initializes all six actuators")
    status, _ = call("GET", f"/api/v1/crops/{crop_id}/device", token=token)
    expect(status == 400, "virtual crop does not return device key")

    def virtual_reading():
        _, latest = call("GET", f"/api/v1/crops/{crop_id}/readings/latest", token=token)
        soil = (latest or {}).get("measures", {}).get("soilMoisture")
        return soil is not None and abs(soil - 42) <= 4

    wait_for("la lectura del cultivo virtual", virtual_reading, timeout=60)
    expect(True, "simulation publishes via MQTT with virtual crop credentials")

    status, body = call("GET", path, token=token)
    expect(status == 200 and body["active"] and body["connected"] and body["mode"] == "MANUAL",
           "simulation reports live state")

    status, _ = call("DELETE", path, token=token)
    status_after, body = call("GET", path, token=token)
    expect(status == 204 and status_after == 200 and not body["active"], "simulation paused")

    status, _ = call("DELETE", f"/api/v1/crops/{crop_id}", token=token)
    expect(status == 204, "virtual crop deleted")


def check_learning(token: str) -> None:
    def learned():
        status, body = call("GET", "/api/v1/ai/learning", token=token)
        return body if status == 200 and body["storedReadings"] > 0 else None

    body = wait_for("que la IA reciba lecturas para aprender", learned, timeout=90)
    expect(any(item["cropType"] == "LETTUCE" for item in body["cropTypes"]),
           "AI stores real readings for continual learning")


if __name__ == "__main__":
    try:
        main()
    except (CheckFailed, KeyError, StopIteration, urllib.error.URLError) as error:
        print(f"  ✘ {error!r}")
        sys.exit(1)
