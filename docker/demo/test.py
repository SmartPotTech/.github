#!/usr/bin/env python3
"""Script Centralizado de Validación y Pruebas E2E / Contrato para Demo BETA.

Ejecuta la suite integral de verificación del stack de nueva generación:
  - Sondas de salud en los 8 contenedores (Go, PG17, Valkey, EMQX, SolidJS, Rust, AI, Mail).
  - Verificación de los 2 cultivos demo semilla y telemetría en TimescaleDB.
  - Resumen estadístico, exportación CSV y capacidades del hardware por MQTT.
  - Flujo de creación de cultivo virtual con auto-aprovisionamiento en el simulador Rust.
  - Comandos a actuadores, no solapamiento (409 Conflict) y confirmaciones ACK.
  - Evaluación agronómica con SmartPot-AI y series temporales con time_bucket.
  - Conexiones spt_ READ/CONTROL y herramientas del servidor MCP.
  - Correo de recuperación en Mailpit y restablecimiento efectivo de la clave demo.
  - Aislamiento multi-tenant y borrado limpio.

Uso:
    python3 test.py
    SMARTPOT_API_URL=http://localhost:8091 python3 test.py
    SMARTPOT_MAILPIT_URL=http://localhost:8025 SMARTPOT_MCP_URL=http://localhost:8002 python3 test.py
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
import urllib.request
from typing import Any, Optional, Tuple, Union

API = os.environ.get("SMARTPOT_API_URL", "http://localhost:8091").rstrip("/")
MCP = os.environ.get("SMARTPOT_MCP_URL", "http://localhost:8002").rstrip("/")
MAILPIT = os.environ.get("SMARTPOT_MAILPIT_URL", "http://localhost:8025").rstrip("/")
MAILPIT_USERNAME = os.environ.get("SMARTPOT_MAILPIT_USERNAME", "admin")
MAILPIT_PASSWORD = os.environ.get("SMARTPOT_MAILPIT_PASSWORD", "demo-mailpit-ui")
DEMO_EMAIL = os.environ.get("SMARTPOT_DEMO_EMAIL", "demo@smartpot.app")
DEMO_PASSWORD = os.environ.get("SMARTPOT_DEMO_PASSWORD", "SmartPot2026")
DEMO_LETTUCE_KEY = os.environ.get("SMARTPOT_DEMO_LETTUCE_KEY", "demo-lettuce-device-key-2026")
BROKER = os.environ.get("SMARTPOT_BROKER_CONTAINER", "smartpot-demo-broker")

CHECKS = 0
SKIPS = 0


class CheckFailed(Exception):
    pass


class WebSession:
    """Sesión web que conserva las cookies (smartpot_session HttpOnly y smartpot_csrf) y el token CSRF."""

    def __init__(self) -> None:
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.csrf: Optional[str] = None
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
    body: Optional[dict] = None,
    token: Optional[Union[WebSession, str]] = None,
    include_csrf: bool = True,
) -> Tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    opener_fn = urllib.request.urlopen
    if isinstance(token, WebSession):
        opener_fn = token.opener.open
        if include_csrf and token.csrf and method not in ("GET", "HEAD", "OPTIONS"):
            req.add_header("X-CSRF-Token", token.csrf)
    elif isinstance(token, str) and token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with opener_fn(req, timeout=20) as resp:
            if isinstance(token, WebSession):
                token.last_set_cookies = resp.headers.get_all("Set-Cookie") or []
                csrf_hdr = resp.headers.get("X-CSRF-Token")
                if csrf_hdr:
                    token.csrf = csrf_hdr
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            parsed = json.loads(raw) if raw else None
        except Exception:
            parsed = raw.decode(errors="replace")
        return err.code, parsed


def request_raw(method: str, path: str, token: Optional[Union[WebSession, str]] = None) -> Tuple[int, Any, str]:
    """Petición sin parseo JSON, para respuestas CSV y otras descargas."""
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Accept", "text/csv, text/plain, */*")
    opener_fn = urllib.request.urlopen
    if isinstance(token, WebSession):
        opener_fn = token.opener.open
        if token.csrf and method not in ("GET", "HEAD", "OPTIONS"):
            req.add_header("X-CSRF-Token", token.csrf)
    elif isinstance(token, str) and token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with opener_fn(req, timeout=20) as resp:
            return resp.status, resp.headers, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.headers, err.read().decode("utf-8", "replace")


def mcp_reachable(base: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def mcp_request(base: str, token: Optional[str], method: str, params: Optional[dict] = None) -> Tuple[int, Any]:
    """Petición JSON-RPC al servidor MCP por streamable HTTP (sin estado, respuesta JSON)."""
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    req = urllib.request.Request(f"{base}/mcp", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, parse_mcp_body(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as err:
        return err.code, parse_mcp_body(err.read().decode("utf-8", "replace"))
    except urllib.error.URLError as err:
        raise CheckFailed(f"MCP server is unreachable at {base}: {err.reason}") from err


def parse_mcp_body(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    events = [line[len("data:"):].strip() for line in text.splitlines() if line.startswith("data:")]
    return json.loads(events[-1]) if events else None


def mcp_result(payload: Any) -> Any:
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


def mcp_failed(payload: Any) -> bool:
    """Indica si MCP devolvió un error de herramienta o JSON-RPC."""
    if not isinstance(payload, dict):
        return True
    if "error" in payload:
        return True
    result = payload.get("result")
    return bool(isinstance(result, dict) and result.get("isError"))


def mcp_call(base: str, token: Optional[str], tool: str, arguments: Optional[dict] = None) -> Tuple[int, Any]:
    """Llama a una herramienta del servidor MCP."""
    return mcp_request(base, token, "tools/call", {"name": tool, "arguments": arguments or {}})


def json_or_text(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8", "replace")


def mailpit_call(method: str, path: str) -> Tuple[int, Any]:
    credentials = base64.b64encode(f"{MAILPIT_USERNAME}:{MAILPIT_PASSWORD}".encode()).decode()
    req = urllib.request.Request(f"{MAILPIT}{path}", method=method)
    req.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json_or_text(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json_or_text(err.read())
    except urllib.error.URLError as err:
        raise CheckFailed(f"Mailpit is unreachable at {MAILPIT}: {err.reason}") from err


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


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
            token = None
            if status_detail == 200:
                pattern = re.compile(r"token=([A-Za-z0-9_-]{20,})")
                for text in iter_strings(detail):
                    match = pattern.search(text)
                    if match:
                        token = match.group(1)
                        break
            if token:
                return {"token": token, "subject": subject, "id": message_id}
        return None

    return wait_for(f"the password recovery email for {email}", probe, timeout)


def publish_broker(username: str, password: str, topic: str, payload: dict) -> bool:
    # La API liga el clientId al cultivo: smartpot-<cropId> para el dispositivo real.
    # La imagen de EMQX no trae mosquitto_pub, así que se publica desde un cliente efímero en la red interna.
    network = os.environ.get("SMARTPOT_DOCKER_NETWORK", "smartpot-demo_internal")
    broker_host = os.environ.get("SMARTPOT_BROKER_HOST", "broker-smartpot")
    command = ["docker", "run", "--rm", "--network", network, "eclipse-mosquitto:2.0",
               "mosquitto_pub", "-h", broker_host, "-p", "1883",
               "-i", f"smartpot-{username}", "-u", username, "-P", password, "-q", "1",
               "-t", topic, "-m", json.dumps(payload)]
    return subprocess.run(command, capture_output=True, text=True).returncode == 0


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
        res = probe()
        if res:
            return res
        time.sleep(1)
    raise CheckFailed(f"Timed out waiting for: {description}")


def check_readings_routes(token: WebSession, crop_id: str) -> None:
    """Resumen estadístico y exportación CSV del cultivo semilla."""
    status, summary = call("GET", f"/api/v1/crops/{crop_id}/readings/summary?hours=24", token=token)
    expect(status == 200 and summary["count"] >= 1, "Readings summary aggregates the live telemetry")
    metrics = summary["metrics"] if status == 200 else {}
    expect("ph" in metrics and metrics.get("ph", {}).get("avg") is not None,
           "Readings summary exposes per-metric statistics")

    status, headers, body = request_raw("GET", f"/api/v1/crops/{crop_id}/readings/export", token=token)
    expect(status == 200 and "text/csv" in (headers.get("Content-Type") or "").lower(),
           "Readings export returns text/csv")
    expect("attachment" in (headers.get("Content-Disposition") or "").lower(),
           "Readings export is served as an attachment")
    lines = [line for line in body.splitlines() if line.strip()]
    expect(bool(lines) and lines[0].startswith("measuredAt,"), "Readings export writes the canonical CSV header")
    expect(len(lines) >= 2, "Readings export includes at least one data row")


def check_capabilities(token: WebSession, crop_id: str) -> None:
    """Publica la declaración canónica del hardware y comprueba su reflejo en la API."""
    capabilities = {
        "schema": 1,
        "device": {
            "firmware": "smartpot-demo/1.0",
            "hardware": "demo-seed",
            "telemetry": {"formats": ["json-v1", "compact-v2"], "compactBytes": 27},
        },
        "sensors": [
            {"key": "temperature", "unit": "C", "resolution": 0.01, "range": [-20, 60]},
            {"key": "ph", "unit": "pH", "resolution": 0.01, "range": [0, 14]},
            {"key": "soilMoisture", "unit": "%", "resolution": 0.1, "range": [0, 100]},
        ],
        "actuators": ["WATER_PUMP", "UV_LIGHT", "FAN"],
    }
    topic = f"smartpot/v1/{crop_id}/capabilities"
    wait_for("the broker to accept the capabilities declaration",
             lambda: publish_broker(crop_id, DEMO_LETTUCE_KEY, topic, capabilities))
    expect(True, "Device publishes its hardware capabilities over MQTT")

    def reflected():
        status, crop = call("GET", f"/api/v1/crops/{crop_id}", token=token)
        stored = ((crop or {}).get("device") or {}).get("capabilities") if status == 200 else None
        if isinstance(stored, dict) and stored.get("device", {}).get("firmware") == "smartpot-demo/1.0":
            return stored
        return None

    stored = wait_for("the API to store the device capabilities", reflected)
    expect(stored["schema"] == 1 and len(stored["sensors"]) == 3,
           "Capabilities are stored as received from the device")
    expect(stored["actuators"] == ["WATER_PUMP", "UV_LIGHT", "FAN"],
           "Capabilities preserve the declared actuators")


def check_password_recovery() -> None:
    """Envía el correo de recuperación, lo lee en Mailpit y restablece la clave demo."""
    status, _ = mailpit_call("DELETE", "/api/v1/messages")
    expect(status in (200, 204), "Mailpit inbox cleared before password recovery")

    status, _ = call("POST", "/api/v1/auth/password/forgot", {"email": DEMO_EMAIL})
    expect(status == 202, "Forgot password accepts the demo email (202)")

    email = wait_for_reset_email(DEMO_EMAIL)
    expect(bool(email.get("token")), "Recovery email arrives in Mailpit with its token")
    token = email["token"]

    replacement = f"Qa{secrets.token_hex(6)}9z"
    status, _ = call("POST", "/api/v1/auth/password/reset", {"token": token, "password": replacement})
    expect(status == 204, "Password reset with the emailed token (204)")
    changed = status == 204

    try:
        status, _ = call("POST", "/api/v1/auth/password/reset", {"token": token, "password": replacement})
        expect(status == 400, "Recovery token cannot be reused (400)")
        status, _ = call("POST", "/api/v1/auth/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        expect(status == 401, "Old demo password stops working after the reset (401)")
        session = WebSession()
        status, _ = call("POST", "/api/v1/auth/login", {"email": DEMO_EMAIL, "password": replacement}, token=session)
        expect(status == 200 and session.has_http_only_session(),
               "New demo password logs in with an HttpOnly session")
    except BaseException:
        if changed:
            restore_demo_password()
        raise

    if changed:
        try:
            mailpit_call("DELETE", "/api/v1/messages")
            call("POST", "/api/v1/auth/password/forgot", {"email": DEMO_EMAIL})
            restored = wait_for_reset_email(DEMO_EMAIL)
            status, _ = call("POST", "/api/v1/auth/password/reset",
                             {"token": restored["token"], "password": DEMO_PASSWORD})
            expect(status == 204, "Demo password restored from a fresh email token")
            status, _ = call("POST", "/api/v1/auth/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
            expect(status == 200, "Demo account logs in with its original password")
        except BaseException:
            restore_demo_password()
            raise


def restore_demo_password() -> None:
    """Restaura la clave demo tras un fallo, sin enmascarar el error original."""
    try:
        mailpit_call("DELETE", "/api/v1/messages")
        status, _ = call("POST", "/api/v1/auth/password/forgot", {"email": DEMO_EMAIL})
        if status == 429:
            time.sleep(60)
            call("POST", "/api/v1/auth/password/forgot", {"email": DEMO_EMAIL})
        email = wait_for_reset_email(DEMO_EMAIL)
        status, _ = call("POST", "/api/v1/auth/password/reset",
                         {"token": email["token"], "password": DEMO_PASSWORD})
        if status == 429:
            time.sleep(60)
            status, _ = call("POST", "/api/v1/auth/password/reset",
                             {"token": email["token"], "password": DEMO_PASSWORD})
        print(f"  ℹ demo password restore returned HTTP {status}")
    except Exception as err:  # noqa: BLE001 - la restauración es best effort
        print(f"  ! could not restore the demo password: {err!r}")


def run_beta_suite():
    print("================================================================================")
    print("  SmartPot Demo Stack — Comprehensive Validation & Contract Suite")
    print(f"  Target API: {API}")
    print("================================================================================\n")

    # 1. Healthcheck de los 8 servicios
    status, health = call("GET", "/health")
    expect(status == 200 and health.get("status") == "UP", "Go API reports global status UP")
    for comp in ("database", "broker", "cache", "ai", "simulator"):
        expect(health.get(comp) == "UP", f"Subsystem '{comp}' connected and UP")

    # 2. Guardia de rutas privadas
    status, body = call("GET", "/api/v1/crops")
    expect(status == 401 and any(msg in body.get("message", "") for msg in ("Please log in", "Inicia sesión")), "Private routes require authentication (401)")

    # 3. Login con cuenta semilla demo (cookie HttpOnly + protección CSRF)
    demo_token = WebSession()
    status, login_body = call("POST", "/api/v1/auth/login",
                              {"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
                              token=demo_token)
    expect(status == 200 and "token" not in (login_body or {}) and demo_token.has_http_only_session() and bool(demo_token.csrf),
           "Successful authentication with seed demo account via HttpOnly cookie and CSRF token")

    status_csrf, _ = call("POST", "/api/v1/crops",
                          {"name": "Sin CSRF", "type": "BASIL", "kind": "VIRTUAL", "form": "TOWER"},
                          token=demo_token, include_csrf=False)
    expect(status_csrf == 403, "CSRF protection rejects mutations missing X-CSRF-Token (403)")

    # 4. Verificación de cultivos demo iniciales
    status, crops = call("GET", "/api/v1/crops", token=demo_token)
    expect(status == 200 and len(crops) >= 2, "Demo account has active seed crops")
    lettuce = next((c for c in crops if c["type"] == "LETTUCE"), None)
    expect(lettuce is not None and lettuce["id"] == "66f5a1000000000000000101", "Seed lettuce crop present")

    # 5. Telemetría en vivo desde el simulador en Rust
    def check_telemetry():
        s, latest = call("GET", f"/api/v1/crops/{lettuce['id']}/readings/latest", token=demo_token)
        return latest if s == 200 and latest and latest.get("measures") else None

    latest_read = wait_for("live telemetry from Rust Simulator", check_telemetry, timeout=30)
    measures = latest_read["measures"]
    expect(all(k in measures for k in ("ph", "temperature", "humidity")), "Sensor readings persisted in TimescaleDB")

    # 6. Rutas secundarias de lectura: resumen estadístico y exportación CSV
    check_readings_routes(demo_token, lettuce["id"])

    # 7. Declaración de capacidades del hardware por MQTT y su reflejo en la API
    check_capabilities(demo_token, lettuce["id"])

    # 8. Ciclo de cultivo virtual
    virt_name = f"Beta-Virtual-{secrets.token_hex(3)}"
    virt_payload = {
        "name": virt_name,
        "type": "BASIL",
        "kind": "VIRTUAL",
        "form": "TOWER",
        "virtual": {
            "mode": "MANUAL",
            "intervalSeconds": 10,
            "manual": {"soilMoisture": 45, "ph": 6.4, "temperature": 22.5}
        }
    }
    status, virt_resp = call("POST", "/api/v1/crops", virt_payload, token=demo_token)
    expect(status == 201 and virt_resp.get("crop", {}).get("kind") == "VIRTUAL", "Virtual crop created")
    expect("device" not in virt_resp, "Virtual crop does not expose credentials to user")
    v_crop = virt_resp["crop"]
    v_id = v_crop["id"]

    try:
        # 7. Actuadores del cultivo virtual
        status, actuators = call("GET", f"/api/v1/crops/{v_id}/actuators", token=demo_token)
        expect(status == 200 and len(actuators) == 6, "Virtual crop initializes all 6 actuators")

        # 8. Envío de comando y rechazo de conflicto / solapamiento (409)
        fan = next(a for a in actuators if a["type"] == "FAN")
        # Rechazo cuando el actuador ya está apagado o hay una orden en curso (409 Conflict)
        status, conflict = call("POST", f"/api/v1/crops/{v_id}/commands",
                                {"actuatorId": fan["id"], "action": "DEACTIVATE"}, token=demo_token)
        expect(status == 409 and any(msg in conflict.get("message", "").lower() for msg in ("already off", "ya está apagado", "in progress", "en curso")),
               "Conflict control prevents redundant or concurrent orders (409)")

        status, cmd = call("POST", f"/api/v1/crops/{v_id}/commands",
                           {"actuatorId": fan["id"], "action": "ACTIVATE", "durationSeconds": 60}, token=demo_token)
        expect(status in (200, 201, 202) and cmd.get("status") in ("PENDING", "SENT"), "Command dispatched to fan")

        # 9. Consulta al Asistente de IA. El simulador publica cada 15 s: mientras el cultivo
        # nuevo no tenga su primera lectura, la API responde 404 y se reintenta.
        deadline = time.monotonic() + 45
        while True:
            status, insight = call("GET", f"/api/v1/crops/{v_id}/insights", token=demo_token)
            if status != 404 or time.monotonic() > deadline:
                break
            time.sleep(3)
        expect(status == 200 and 0 <= insight.get("health", {}).get("index", -1) <= 100, "SmartPot-AI assistant returns valid diagnosis")

        # 10. Agregación de Series Temporales (TimescaleDB time_bucket)
        status, series = call("GET", "/api/v1/overview/series?metric=temperature&hours=1", token=demo_token)
        expect(status == 200 and "series" in series, "Time series aggregated by TimescaleDB")

        # 11. Verificación opcional de SmartPot-Trainer si el puerto está mapeado
        trainer_url = os.environ.get("SMARTPOT_TRAINER_URL", "http://localhost:8001").rstrip("/")
        try:
            req = urllib.request.Request(f"{trainer_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                if resp.status == 200 and data.get("status") == "UP":
                    print("  ✔ Microservice SmartPot-Trainer reports status UP on /health")
        except Exception:
            pass

        # 12. Conexiones personales (tokens spt_) y servidor MCP: cada conexión actúa a nombre de su cuenta con su
        # alcance, nunca administra la cuenta y deja de servir al revocarla.
        status, created = call("POST", "/api/v1/connections", {"name": "Suite demo read", "scope": "READ"}, token=demo_token)
        expect(status == 201 and created.get("token", "").startswith("spt_")
               and created["connection"]["scope"] == "READ", "Read-only connection created")
        conn_token, conn_id = created["token"], created["connection"]["id"]
        status, control = call("POST", "/api/v1/connections", {"name": "Suite demo control", "scope": "CONTROL"}, token=demo_token)
        expect(status == 201 and control["connection"]["scope"] == "CONTROL", "Control connection created")
        control_token, control_id = control["token"], control["connection"]["id"]

        try:
            status, conn_crops = call("GET", "/api/v1/crops", token=conn_token)
            expect(status == 200 and len(conn_crops) >= 2, "Connection accesses account crops")
            status, _ = call("POST", f"/api/v1/crops/{v_id}/commands",
                             {"actuatorId": fan["id"], "action": "DEACTIVATE"}, token=conn_token)
            expect(status == 403, "Read-only connection cannot trigger actuators (403)")
            status, _ = call("GET", "/api/v1/connections", token=conn_token)
            expect(status == 403, "Connection cannot manage connections (403)")

            mcp_url = MCP
            expect(mcp_reachable(mcp_url), f"MCP server is reachable at {mcp_url}")
            status, _ = mcp_request(mcp_url, None, "tools/list")
            expect(status == 401, "MCP server requires a connection token (401)")

            status, listing = mcp_request(mcp_url, conn_token, "tools/list")
            tools = {tool["name"] for tool in (listing or {}).get("result", {}).get("tools", [])
                     if isinstance(tool, dict)} if status == 200 else set()
            expect(status == 200 and {"list_crops", "record_reading"} <= tools,
                   "MCP tools/list exposes the crop and reading tools")

            status, result = mcp_call(mcp_url, conn_token, "list_crops")
            listed = mcp_result(result)
            expect(status == 200 and not mcp_failed(result)
                   and any(crop.get("id") == lettuce["id"] for crop in listed or [] if isinstance(crop, dict)),
                   "MCP server lists the account crops")

            status, blocked = mcp_call(mcp_url, conn_token, "record_reading",
                                       {"crop_id": lettuce["id"], "ph": 6.5})
            expect(status == 200 and mcp_failed(blocked), "Read-only connection cannot write through MCP")

            status, written = mcp_call(mcp_url, control_token, "record_reading",
                                       {"crop_id": lettuce["id"], "ph": 6.5})
            reading = mcp_result(written)
            expect(status == 200 and not mcp_failed(written)
                   and isinstance(reading, dict) and reading.get("measures", {}).get("ph") == 6.5,
                   "Control connection writes through MCP")

            status, _ = call("DELETE", f"/api/v1/connections/{conn_id}", token=demo_token)
            expect(status == 204, "Read-only connection revoked")
            status, _ = mcp_request(mcp_url, conn_token, "tools/list")
            expect(status == 401, "Revoked connection is rejected by MCP (401)")
            status, _ = call("GET", "/api/v1/crops", token=conn_token)
            expect(status == 401, "Revoked connection is immediately rejected by the API (401)")
            status, _ = call("DELETE", f"/api/v1/connections/{control_id}", token=demo_token)
            expect(status == 204, "Control connection revoked")
        finally:
            call("DELETE", f"/api/v1/connections/{conn_id}", token=demo_token)
            call("DELETE", f"/api/v1/connections/{control_id}", token=demo_token)

    finally:
        # Limpieza del cultivo virtual de prueba
        call("DELETE", f"/api/v1/crops/{v_id}", token=demo_token)
        print("  ✔ Virtual crop cleanup completed")

    # 13. Correo de recuperación en Mailpit y restablecimiento efectivo de la clave demo
    check_password_recovery()

    print("\n================================================================================")
    print(f"  RESULT: DEMO STACK OPERATIONAL — {CHECKS} checks passed, {SKIPS} skipped")
    print("================================================================================\n")


if __name__ == "__main__":
    try:
        run_beta_suite()
    except CheckFailed as e:
        print(f"\n[FAILURE] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected exception: {e}")
        sys.exit(1)
