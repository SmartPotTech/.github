"""Prueba de extremo a extremo sobre el entorno demo de SmartPot.

Recorre el camino completo de un usuario nuevo: registro, cultivo real, telemetría MQTT,
comando con confirmación del dispositivo, switches de los actuadores, evaluación del asistente,
lugar del cultivo con su consejo y su clima, panel general (totales, series comparativas y
análisis de flota), órdenes en bloque, cultivo virtual con su simulación, aprendizaje continuo,
canales de notificación con los avisos por cultivo, recuperación de contraseña por correo,
perfil y cambio de clave, exportación CSV, capacidades del hardware, conexiones spt_ con MCP,
aislamiento entre cuentas y borrado de la cuenta.
Solo usa la biblioteca estándar; publica por MQTT con mosquitto_pub dentro del broker.

    python3 scripts/e2e.py
    SMARTPOT_API_URL=http://localhost:8091 SMARTPOT_BROKER_CONTAINER=smartpot-demo-broker python3 scripts/e2e.py
"""

import base64
import http.cookiejar
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("SMARTPOT_API_URL", "http://localhost:8091").rstrip("/")
BROKER = os.environ.get("SMARTPOT_BROKER_CONTAINER", "smartpot-demo-broker")
MCP = os.environ.get("SMARTPOT_MCP_URL", "http://localhost:8002").rstrip("/")
MAILPIT = os.environ.get("SMARTPOT_MAILPIT_URL", "http://localhost:8025").rstrip("/")
MAILPIT_USERNAME = os.environ.get("SMARTPOT_MAILPIT_USERNAME", "admin")
MAILPIT_PASSWORD = os.environ.get("SMARTPOT_MAILPIT_PASSWORD", "demo-mailpit-ui")
DEMO_EMAIL = os.environ.get("SMARTPOT_DEMO_EMAIL", "demo@smartpot.app")
DEMO_PASSWORD = os.environ.get("SMARTPOT_DEMO_PASSWORD", "SmartPot2026")
MIN_CHECKS = 65

if not os.environ.get("SMARTPOT_BROKER_CONTAINER"):
    check_beta = subprocess.run(["docker", "ps", "--filter", "name=smartpot-demo-beta-broker", "--format", "{{.Names}}"],
                                capture_output=True, text=True)
    if "smartpot-demo-beta-broker" in check_beta.stdout:
        BROKER = "smartpot-demo-beta-broker"

CHECKS = 0
SKIPS = 0


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
    headers: dict | None = None,
) -> tuple[int, dict | list | None]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
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
    global CHECKS
    if not condition:
        raise CheckFailed(message)
    CHECKS += 1
    print(f"  ✔ {message}")


def skip(message: str, reason: str) -> None:
    global SKIPS
    SKIPS += 1
    print(f"  ↷ SKIP {message} ({reason})")


def wait_for(description: str, probe, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = probe()
        if result:
            return result
        time.sleep(1)
    raise CheckFailed(f"Timed out waiting for: {description}")


def request_raw(method: str, path: str, token: WebSession | str | None = None) -> tuple[int, object, str]:
    """Petición sin parseo JSON, para respuestas CSV y otras descargas."""
    request = urllib.request.Request(f"{API}{path}", method=method)
    request.add_header("Accept", "text/csv, text/plain, */*")
    opener_fn = urllib.request.urlopen
    if isinstance(token, WebSession):
        opener_fn = token.opener.open
        if token.csrf and method not in ("GET", "HEAD", "OPTIONS"):
            request.add_header("X-CSRF-Token", token.csrf)
    elif isinstance(token, str) and token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with opener_fn(request, timeout=20) as response:
            return response.status, response.headers, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read().decode("utf-8", "replace")


def mcp_request(method: str, params: dict | None = None,
                token: str | None = None) -> tuple[int, dict | list | None]:
    """Petición JSON-RPC al servidor MCP por streamable HTTP (respuesta JSON sin estado)."""
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    request = urllib.request.Request(f"{MCP}/mcp", data=json.dumps(body).encode(), method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json, text/event-stream")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, parse_mcp_body(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as error:
        return error.code, parse_mcp_body(error.read().decode("utf-8", "replace"))
    except urllib.error.URLError as error:
        raise CheckFailed(f"MCP server is unreachable at {MCP}: {error.reason}") from error


def parse_mcp_body(raw: str) -> dict | list | None:
    text = raw.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    # Algunos transportes responden text/event-stream: se toma el último evento data.
    events = [line[len("data:"):].strip() for line in text.splitlines() if line.startswith("data:")]
    return json.loads(events[-1]) if events else None


def mcp_result(payload: dict | list | None):
    """Extrae el resultado útil de una respuesta MCP, sea JSON estructurado o texto."""
    if not isinstance(payload, dict):
        return payload
    result = payload.get("result")
    if not isinstance(result, dict):
        return result
    if isinstance(result.get("structuredContent"), (dict, list)):
        structured = result["structuredContent"]
        if isinstance(structured, dict) and set(structured) == {"result"}:
            return structured["result"]
        return structured
    for item in result.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return result


def mcp_failed(payload: dict | list | None) -> bool:
    """Indica si MCP devolvió un error de herramienta o JSON-RPC."""
    if not isinstance(payload, dict):
        return True
    if "error" in payload:
        return True
    result = payload.get("result")
    return bool(isinstance(result, dict) and result.get("isError"))


def json_or_text(raw: bytes):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8", "replace")


def mailpit_call(method: str, path: str) -> tuple[int, object]:
    credentials = base64.b64encode(f"{MAILPIT_USERNAME}:{MAILPIT_PASSWORD}".encode()).decode()
    request = urllib.request.Request(f"{MAILPIT}{path}", method=method)
    request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json_or_text(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json_or_text(error.read())
    except urllib.error.URLError as error:
        raise CheckFailed(f"Mailpit is unreachable at {MAILPIT}: {error.reason}") from error


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def extract_reset_token(message: dict | list | None) -> str | None:
    # El enlace del correo es {WEB_BASE_URL}/reset-password?token=...; el token es base64url.
    pattern = re.compile(r"token=([A-Za-z0-9_-]{20,})")
    for text in iter_strings(message):
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def wait_for_reset_email(email: str, timeout: float = 25.0) -> dict:
    def probe():
        status, inbox = mailpit_call("GET", "/api/v1/messages?limit=50")
        if status != 200 or not isinstance(inbox, dict):
            return None
        for message in inbox.get("messages") or []:
            if not isinstance(message, dict):
                continue
            recipients = [str(item.get("Address", "")).lower()
                          for item in message.get("To") or [] if isinstance(item, dict)]
            subject = str(message.get("Subject", ""))
            if email.lower() not in recipients or "password" not in subject.lower():
                continue
            message_id = message.get("ID") or message.get("Id") or message.get("id")
            if not message_id:
                continue
            status_detail, detail = mailpit_call("GET", f"/api/v1/message/{message_id}")
            token = extract_reset_token(detail) if status_detail == 200 else None
            if token:
                return {"token": token, "subject": subject, "id": message_id}
        return None

    return wait_for(f"el correo de recuperación para {email}", probe, timeout)


def clear_recipient_inbox(email: str) -> int:
    """Borra en Mailpit solo los mensajes dirigidos al destinatario indicado."""
    search_query = urllib.parse.urlencode({"query": f'to:"{email}"', "limit": 50})
    status, inbox = mailpit_call("GET", f"/api/v1/search?{search_query}")
    if status != 200:
        return status
    if isinstance(inbox, dict) and inbox.get("messages_count", 0) == 0:
        return 200
    delete_query = urllib.parse.urlencode({"query": f'to:"{email}"'})
    del_status, _ = mailpit_call("DELETE", f"/api/v1/search?{delete_query}")
    return del_status


def publish(username: str, password: str, topic: str, payload: dict) -> bool:
    # La API liga el clientId al cultivo: smartpot-<cropId> para el dispositivo real.
    command = ["docker", "exec", BROKER, "mosquitto_pub", "-h", "127.0.0.1", "-p", "1883",
               "-i", f"smartpot-{username}", "-u", username, "-P", password, "-q", "1",
               "-t", topic, "-m", json.dumps(payload)]
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode == 0:
        return True

    network = os.environ.get("SMARTPOT_DOCKER_NETWORK")
    if not network:
        net_inspect = subprocess.run(["docker", "inspect", BROKER, "--format", "{{json .NetworkSettings.Networks}}"],
                                     capture_output=True, text=True)
        if net_inspect.returncode == 0:
            try:
                networks = json.loads(net_inspect.stdout or "{}")
            except json.JSONDecodeError:
                networks = {}
            # Cualquier proyecto de compose usa una red <proyecto>_internal.
            network = next((name for name in networks if name.endswith("_internal")), None)
        else:
            network = None
        if not network:
            network = "smartpot-demo-beta_internal"

    broker_host = os.environ.get("SMARTPOT_BROKER_HOST", "broker-smartpot")
    command_aux = ["docker", "run", "--rm", "--network", network, "eclipse-mosquitto:2.0",
                   "mosquitto_pub", "-h", broker_host, "-p", "1883",
                   "-i", f"smartpot-{username}", "-u", username, "-P", password, "-q", "1",
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
        check_account_security()
        check_password_recovery()
    finally:
        status, _ = call("DELETE", "/api/v1/users/me", token=token)
        expect(status == 204, "test account deletion")

    if CHECKS < MIN_CHECKS:
        raise CheckFailed(f"expected at least {MIN_CHECKS} checks, got {CHECKS}")
    print(f"E2E completed successfully: {CHECKS} checks passed, {SKIPS} skipped.")


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

    check_readings_exports(token, crop_id)
    check_capabilities(token, crop_id, username, key, topics)

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
    check_connections_mcp(token, crop_id)
    check_isolation(token)
    check_validation(token)

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
    expect(status == 200 and (telegram["available"] or "TELEGRAM_BOT_TOKEN" in telegram["requirements"]),
           "notification channels report Telegram availability and requirements")

    status, settings = call("GET", f"/api/v1/crops/{crop_id}/channels", token=token)
    crop_telegram = next(channel for channel in settings if channel["type"] == "TELEGRAM")
    expect(status == 200 and crop_telegram["available"] == telegram["available"] and not crop_telegram["linked"],
           "crop alerts report channel availability and link state")

    if telegram["available"]:
        status, link = call("POST", "/api/v1/channels/TELEGRAM/link", token=token)
        expect(status == 200 and bool(link["code"]) and bool(link["expiresAt"]),
               "Telegram link code generated for the account")
        expect(link["url"].startswith("https://t.me/") and link["code"] in link["url"],
               "link code embedded in the Telegram deep link")
    else:
        status, body = call("PUT", f"/api/v1/crops/{crop_id}/channels/TELEGRAM", {"delivery": "DIGEST"}, token)
        expect(status == 503 and any(m in body["message"].lower() for m in ("not configured", "no está configurado")),
               "unconfigured Telegram channel returns 503")
        skip("Telegram link code generation", "TELEGRAM_BOT_TOKEN is not configured")

    status, _ = call("POST", "/api/v1/channels/telegram/webhook", {"update_id": 1})
    expect(status in (401, 403, 404), "Telegram webhook rejects updates without a secret (401/403/404)")

    status, _ = call("POST", "/api/v1/channels/telegram/webhook", {"update_id": 1},
                     headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"})
    expect(status in (401, 403, 404), "Telegram webhook rejects a wrong secret (401/403/404)")


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


def check_readings_exports(token: str, crop_id: str) -> None:
    status, summary = call("GET", f"/api/v1/crops/{crop_id}/readings/summary?hours=24", token=token)
    expect(status == 200 and summary["count"] >= 1, "readings summary counts the MQTT reading")
    metrics = summary["metrics"] if status == 200 else {}
    expect(all(key in metrics for key in ("temperature", "humidity", "ph", "soilMoisture"))
           and metrics.get("ph", {}).get("avg") == 6.0,
           "readings summary returns per-metric statistics (min/avg/max)")

    status, headers, body = request_raw("GET", f"/api/v1/crops/{crop_id}/readings/export", token=token)
    content_type = (headers.get("Content-Type") or "").lower()
    expect(status == 200 and content_type.startswith("text/csv"), "readings export returns text/csv")
    disposition = headers.get("Content-Disposition") or ""
    expect(f'attachment; filename="smartpot-{crop_id}.csv"' == disposition,
           "readings export sets the attachment filename")
    lines = [line for line in body.splitlines() if line.strip()]
    header = "measuredAt,temperature,humidity,brightness,ph,tds,atmosphere,soilMoisture"
    expect(bool(lines) and lines[0] == header, "readings export writes the canonical CSV header")
    expect(len(lines) >= 2 and lines[1].startswith("20"), "readings export includes at least one data row")


def check_capabilities(token: str, crop_id: str, username: str, key: str, topics: dict) -> None:
    topic = topics["telemetry"].rsplit("/", 1)[0] + "/capabilities"
    capabilities = {
        "schema": 1,
        "device": {
            "firmware": "smartpot-e2e/1.0",
            "hardware": "esp32-e2e",
            "telemetry": {"formats": ["json-v1", "compact-v2"], "compactBytes": 27},
        },
        "sensors": [
            {"key": "temperature", "unit": "C", "resolution": 0.01, "range": [-20, 60]},
            {"key": "ph", "unit": "pH", "resolution": 0.01, "range": [0, 14]},
            {"key": "soilMoisture", "unit": "%", "resolution": 0.1, "range": [0, 100]},
        ],
        "actuators": ["WATER_PUMP", "UV_LIGHT", "FAN"],
    }
    wait_for("que el broker acepte la declaración de capacidades",
             lambda: publish(username, key, topic, capabilities))
    expect(True, "device publishes its hardware capabilities over MQTT")

    def reflected():
        status, crop = call("GET", f"/api/v1/crops/{crop_id}", token=token)
        stored = ((crop or {}).get("device") or {}).get("capabilities") if status == 200 else None
        if isinstance(stored, dict) and stored.get("device", {}).get("firmware") == "smartpot-e2e/1.0":
            return crop
        return None

    crop = wait_for("que la API guarde las capacidades del dispositivo", reflected)
    stored = crop["device"]["capabilities"]
    expect(stored["schema"] == 1 and len(stored["sensors"]) == 3,
           "capabilities are stored as received from the device")
    expect(stored["actuators"] == ["WATER_PUMP", "UV_LIGHT", "FAN"],
           "capabilities preserve the declared actuators")
    expect(crop["device"].get("capabilitiesUpdatedAt") and not crop["device"].get("capabilitiesStale"),
           "capabilities are timestamped and marked fresh")


def check_connections_mcp(token: str, crop_id: str) -> None:
    status, created = call("POST", "/api/v1/connections",
                           {"name": "E2E read", "scope": "READ"}, token)
    expect(status == 201 and created["token"].startswith("spt_") and created["connection"]["scope"] == "READ",
           "read-only connection token created")
    read_token, read_id = created["token"], created["connection"]["id"]

    status, crops = call("GET", "/api/v1/crops", token=read_token)
    expect(status == 200 and any(crop["id"] == crop_id for crop in crops),
           "read-only connection lists the account crops")
    status, _ = call("POST", f"/api/v1/crops/{crop_id}/readings", {"ph": 6.1}, token=read_token)
    expect(status == 403, "read-only connection cannot write readings (403)")

    status, control = call("POST", "/api/v1/connections",
                           {"name": "E2E control", "scope": "CONTROL"}, token)
    expect(status == 201 and control["connection"]["scope"] == "CONTROL",
           "control connection token created")
    control_token, control_id = control["token"], control["connection"]["id"]

    status, _ = mcp_request("tools/list")
    expect(status == 401, "MCP tools/list requires a connection token (401)")

    status, listing = mcp_request("tools/list", token=read_token)
    tools = {tool["name"] for tool in (listing or {}).get("result", {}).get("tools", [])
             if isinstance(tool, dict)} if status == 200 else set()
    expect(status == 200 and {"list_crops", "record_reading"} <= tools,
           "MCP tools/list exposes crop and reading tools")

    status, listing = mcp_request("tools/call", {"name": "list_crops", "arguments": {}}, read_token)
    listed = mcp_result(listing)
    expect(status == 200 and not mcp_failed(listing)
           and any(crop.get("id") == crop_id for crop in listed or [] if isinstance(crop, dict)),
           "MCP list_crops returns the account crops")

    status, blocked = mcp_request("tools/call",
                                  {"name": "record_reading",
                                   "arguments": {"crop_id": crop_id, "ph": 6.6}}, read_token)
    expect(status == 200 and mcp_failed(blocked), "MCP write with a READ connection is blocked")

    status, written = mcp_request("tools/call",
                                  {"name": "record_reading",
                                   "arguments": {"crop_id": crop_id, "ph": 6.6}}, control_token)
    reading = mcp_result(written)
    expect(status == 200 and not mcp_failed(written)
           and isinstance(reading, dict) and reading.get("measures", {}).get("ph") == 6.6,
           "MCP write with a CONTROL connection is allowed")

    status, latest = call("GET", f"/api/v1/crops/{crop_id}/readings/latest", token=token)
    expect(status == 200 and latest["measures"]["ph"] == 6.6, "MCP write is persisted in the API")

    status, _ = call("DELETE", f"/api/v1/connections/{read_id}", token=token)
    expect(status == 204, "read-only connection revoked")

    status, _ = mcp_request("tools/list", token=read_token)
    expect(status == 401, "revoked connection token is rejected by MCP (401)")

    status, _ = call("GET", "/api/v1/crops", token=read_token)
    expect(status == 401, "revoked connection token is rejected by the API (401)")

    status, _ = call("DELETE", f"/api/v1/connections/{control_id}", token=token)
    expect(status == 204, "control connection revoked")


def check_isolation(token: str) -> None:
    email = f"qa-isolation-{secrets.token_hex(4)}@smartpot.test"
    password = f"Qa{secrets.token_hex(6)}9z"
    other = WebSession()
    status, _ = call("POST", "/api/v1/auth/register",
                     {"name": "Otra", "lastName": "Cuenta", "email": email, "password": password}, other)
    expect(status == 201 and other.has_http_only_session(), "second account created for isolation checks")

    status, body = call("POST", "/api/v1/crops",
                        {"name": "Cultivo ajeno", "type": "BASIL", "kind": "REAL", "form": "POT"}, other)
    expect(status == 201 and body["crop"]["id"], "second account crop created")
    other_crop = body["crop"]["id"]

    try:
        status, _ = call("GET", f"/api/v1/crops/{other_crop}", token=token)
        expect(status == 404, "another account's crop is not visible (404)")
        status, _ = call("GET", f"/api/v1/crops/{other_crop}/readings/latest", token=token)
        expect(status == 404, "another account's readings are not visible (404)")
        status, _ = call("PUT", f"/api/v1/crops/{other_crop}",
                         {"name": "Intruso", "type": "BASIL"}, token=token)
        expect(status == 404, "another account's crop cannot be modified (404)")
        status, _ = call("GET", f"/api/v1/crops/{other_crop}/readings/export", token=token)
        expect(status == 404, "another account's CSV export is denied (404)")
    except BaseException:
        call("DELETE", f"/api/v1/crops/{other_crop}", token=other)
        call("DELETE", "/api/v1/users/me", token=other)
        raise

    status, _ = call("DELETE", f"/api/v1/crops/{other_crop}", token=other)
    status_after, _ = call("DELETE", "/api/v1/users/me", token=other)
    expect(status == 204 and status_after == 204, "second account and its crop cleaned up")


def check_validation(token: str) -> None:
    status, body = call("POST", "/api/v1/crops",
                        {"name": "A", "type": "LETTUCE", "kind": "REAL"}, token)
    fields = (body or {}).get("fields") or {}
    expect(status in (400, 422) and "name" in fields,
           "invalid crop name is rejected with field validation (400/422)")

    status, body = call("PUT", "/api/v1/users/me", {"name": "A", "lastName": "B"}, token)
    fields = (body or {}).get("fields") or {}
    expect(status in (400, 422) and "name" in fields,
           "invalid profile name is rejected with field validation (400/422)")


def check_account_security() -> None:
    email = f"qa-profile-{secrets.token_hex(4)}@smartpot.test"
    password = f"Qa{secrets.token_hex(6)}9z"
    new_password = f"Qa{secrets.token_hex(6)}9z"
    session = WebSession()
    new_session: WebSession | None = None

    try:
        status, _ = call("POST", "/api/v1/auth/register",
                         {"name": "Perfil", "lastName": "Prueba", "email": email, "password": password}, session)
        expect(status == 201 and session.has_http_only_session(),
               "profile test account registered with an HttpOnly session")

        status, body = call("PUT", "/api/v1/users/me",
                            {"name": "Perfil", "lastName": "Actualizado"}, session)
        expect(status == 200 and body["name"] == "Perfil" and body["lastName"] == "Actualizado",
               "profile update persists the name and last name")

        status, body = call("GET", "/api/v1/users/me", token=session)
        expect(status == 200 and body["lastName"] == "Actualizado",
               "profile update is visible in the current session")

        status, body = call("PUT", "/api/v1/users/me/password",
                            {"currentPassword": "wrong-current-password", "newPassword": new_password}, session)
        expect(status == 400 and "current password" in body["message"].lower(),
               "wrong current password is rejected (400)")

        status, _ = call("PUT", "/api/v1/users/me/password",
                         {"currentPassword": password, "newPassword": new_password}, session)
        expect(status == 204, "password change accepted (204)")

        status, _ = call("GET", "/api/v1/crops", token=session)
        expect(status == 401, "password change invalidates the previous session (401)")

        status, _ = call("POST", "/api/v1/auth/login", {"email": email, "password": password})
        expect(status == 401, "old password no longer works (401)")

        new_session = WebSession()
        status, _ = call("POST", "/api/v1/auth/login",
                         {"email": email, "password": new_password}, new_session)
        expect(status == 200 and new_session.has_http_only_session(),
               "new password logs in with a fresh HttpOnly session")

        status, _ = call("DELETE", "/api/v1/users/me", token=new_session)
        expect(status == 204, "profile test account deletion")
        new_session = None
    finally:
        for active in (new_session, session):
            if active is not None:
                call("DELETE", "/api/v1/users/me", token=active)


def check_password_recovery() -> None:
    email = f"qa-recovery-{secrets.token_hex(4)}@smartpot.test"
    password = f"Qa{secrets.token_hex(6)}9z"
    replacement = f"Qa{secrets.token_hex(6)}9z"
    reg_session: WebSession | None = WebSession()
    session: WebSession | None = None

    try:
        status, _ = call("POST", "/api/v1/auth/register",
                         {"name": "Recuperacion", "lastName": "Prueba", "email": email, "password": password},
                         reg_session)
        expect(status == 201 and reg_session.has_http_only_session(),
               "recovery test account registered with an HttpOnly session")

        inbox_status = clear_recipient_inbox(email)
        expect(inbox_status in (200, 204), "Mailpit recipient inbox cleared before password recovery")

        status, _ = call("POST", "/api/v1/auth/password/forgot", {"email": email})
        expect(status == 202, "forgot password accepts the test account email (202)")

        reset_mail = wait_for_reset_email(email)
        expect(bool(reset_mail.get("token")), "recovery email arrives in Mailpit with its token")
        token = reset_mail["token"]

        status, _ = call("POST", "/api/v1/auth/password/reset",
                         {"token": token, "password": replacement})
        expect(status == 204, "password reset with the emailed token (204)")

        status, _ = call("POST", "/api/v1/auth/password/reset",
                         {"token": token, "password": replacement})
        expect(status == 400, "recovery token cannot be reused (400)")

        status, _ = call("POST", "/api/v1/auth/login", {"email": email, "password": password})
        expect(status == 401, "old password stops working after the reset (401)")

        session = WebSession()
        status, _ = call("POST", "/api/v1/auth/login", {"email": email, "password": replacement}, session)
        expect(status == 200 and session.has_http_only_session(),
               "new password logs in with an HttpOnly session")

        status, _ = call("DELETE", "/api/v1/users/me", token=session)
        expect(status == 204, "recovery test account deletion")
        session = None
        reg_session = None
    finally:
        for active in (session, reg_session):
            if active is not None:
                call("DELETE", "/api/v1/users/me", token=active)
        clear_recipient_inbox(email)


if __name__ == "__main__":
    try:
        main()
    except (CheckFailed, KeyError, StopIteration, urllib.error.URLError) as error:
        print(f"  ✘ {error!r}")
        sys.exit(1)
