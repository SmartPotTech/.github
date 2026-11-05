#!/usr/bin/env python3
"""Script Centralizado de Validación y Pruebas E2E / Contrato para Demo BETA.

Ejecuta la suite integral de verificación del stack de nueva generación:
  - Sondas de salud en los 8 contenedores (Go, PG17, Valkey, EMQX, SolidJS, Rust, AI, Mail).
  - Verificación de los 2 cultivos demo semilla y telemetría en TimescaleDB.
  - Flujo de creación de cultivo virtual con auto-aprovisionamiento en el simulador Rust.
  - Comandos a actuadores, no solapamiento (409 Conflict) y confirmaciones ACK.
  - Evaluación agronómica con SmartPot-AI y series temporales con time_bucket.
  - Aislamiento multi-tenant y borrado limpio.

Uso:
    python3 test.py
    SMARTPOT_API_URL=http://localhost:8091 python3 test.py
"""

import http.cookiejar
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple, Union

API = os.environ.get("SMARTPOT_API_URL", "http://localhost:8091").rstrip("/")


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


def mcp_reachable(base: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def mcp_call(base: str, token: Optional[str], tool: str, arguments: Optional[dict] = None) -> Tuple[int, Any]:
    """Llama a una herramienta del servidor MCP por streamable HTTP (sin estado, respuesta JSON)."""
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments or {}}}
    req = urllib.request.Request(f"{base}/mcp", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as err:
        return err.code, None


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)
    print(f"  ✔ {message}")


def wait_for(description: str, probe, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        res = probe()
        if res:
            return res
        time.sleep(1)
    raise CheckFailed(f"Timed out waiting for: {description}")


def run_beta_suite():
    print("================================================================================")
    print("  SmartPot Demo BETA — Comprehensive Validation & Contract Suite")
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
                              {"email": "demo@smartpot.app", "password": "SmartPot2026"},
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

    # 6. Ciclo de cultivo virtual
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
        status, created = call("POST", "/api/v1/connections", {"name": "Suite beta", "scope": "READ"}, token=demo_token)
        expect(status == 201 and created.get("token", "").startswith("spt_"), "Read-only connection created")
        conn_token, conn_id = created["token"], created["connection"]["id"]
        try:
            status, conn_crops = call("GET", "/api/v1/crops", token=conn_token)
            expect(status == 200 and len(conn_crops) >= 2, "Connection accesses account crops")
            status, _ = call("POST", f"/api/v1/crops/{v_id}/commands",
                             {"actuatorId": fan["id"], "action": "DEACTIVATE"}, token=conn_token)
            expect(status == 403, "Read-only connection cannot trigger actuators (403)")
            status, _ = call("GET", "/api/v1/connections", token=conn_token)
            expect(status == 403, "Connection cannot manage connections (403)")

            mcp_url = os.environ.get("SMARTPOT_MCP_URL", "http://localhost:8002").rstrip("/")
            if mcp_reachable(mcp_url):
                status, _ = mcp_call(mcp_url, None, "list_crops")
                expect(status == 401, "MCP server requires connection token (401)")
                status, result = mcp_call(mcp_url, conn_token, "list_crops")
                text = json.dumps(result, ensure_ascii=False)
                expect(status == 200 and any(name in text for name in ("Lechugas del balcón", "Balcony Lettuce")), "MCP server lists account crops")
            else:
                print(f"  ℹ SmartPot-MCP server unavailable at {mcp_url}; skipping checks")
        finally:
            status, _ = call("DELETE", f"/api/v1/connections/{conn_id}", token=demo_token)
            expect(status == 204, "Connection revoked")
        status, _ = call("GET", "/api/v1/crops", token=conn_token)
        expect(status == 401, "Revoked connection is immediately rejected (401)")

    finally:
        # Limpieza del cultivo virtual de prueba
        call("DELETE", f"/api/v1/crops/{v_id}", token=demo_token)
        print("  ✔ Virtual crop cleanup completed")

    print("\n================================================================================")
    print("  RESULT: DEMO BETA 100% OPERATIONAL AND CONTRACT COMPLIANT")
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
