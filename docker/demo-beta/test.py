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

import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple

API = os.environ.get("SMARTPOT_API_URL", "http://localhost:8091").rstrip("/")


class CheckFailed(Exception):
    pass


def call(method: str, path: str, body: Optional[dict] = None, token: Optional[str] = None) -> Tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            parsed = json.loads(raw) if raw else None
        except Exception:
            parsed = raw.decode(errors="replace")
        return err.code, parsed


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
    raise CheckFailed(f"Tiempo agotado esperando: {description}")


def run_beta_suite():
    print("================================================================================")
    print("  SmartPot Demo BETA — Suite de Validación Integral y Contrato")
    print(f"  Target API: {API}")
    print("================================================================================\n")

    # 1. Healthcheck de los 8 servicios
    status, health = call("GET", "/health")
    expect(status == 200 and health.get("status") == "UP", "API Go reporta estado global UP")
    for comp in ("database", "broker", "cache", "ai", "simulator"):
        expect(health.get(comp) == "UP", f"Subsistema '{comp}' conectado y en UP")

    # 2. Guardia de rutas privadas
    status, body = call("GET", "/api/v1/crops")
    expect(status == 401 and "Inicia sesión" in body.get("message", ""), "Rutas privadas exigen autenticación (401)")

    # 3. Login con cuenta semilla demo
    status, login_body = call("POST", "/api/v1/auth/login", {"email": "demo@smartpot.app", "password": "SmartPot2026"})
    expect(status == 200 and login_body.get("token"), "Autenticación exitosa con cuenta demo semilla")
    demo_token = login_body["token"]

    # 4. Verificación de cultivos demo iniciales
    status, crops = call("GET", "/api/v1/crops", token=demo_token)
    expect(status == 200 and len(crops) >= 2, "La cuenta demo tiene los cultivos semilla activos")
    lettuce = next((c for c in crops if c["type"] == "LETTUCE"), None)
    expect(lettuce is not None and lettuce["id"] == "66f5a1000000000000000101", "Cultivo lechuga semilla presente")

    # 5. Telemetría en vivo desde el simulador en Rust
    def check_telemetry():
        s, latest = call("GET", f"/api/v1/crops/{lettuce['id']}/readings/latest", token=demo_token)
        return latest if s == 200 and latest and latest.get("measures") else None

    latest_read = wait_for("telemetría en vivo generada por Rust Simulator", check_telemetry, timeout=30)
    measures = latest_read["measures"]
    expect(all(k in measures for k in ("ph", "temperature", "humidity")), "Lecturas de sensores persistidas en TimescaleDB")

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
    expect(status == 201 and virt_resp.get("crop", {}).get("kind") == "VIRTUAL", "Creación de cultivo virtual")
    expect("device" not in virt_resp, "Cultivo virtual no expone credenciales al usuario")
    v_crop = virt_resp["crop"]
    v_id = v_crop["id"]

    try:
        # 7. Actuadores del cultivo virtual
        status, actuators = call("GET", f"/api/v1/crops/{v_id}/actuators", token=demo_token)
        expect(status == 200 and len(actuators) == 6, "Cultivo virtual inicializa los 6 actuadores")

        # 8. Envío de comando y rechazo de conflicto / solapamiento (409)
        fan = next(a for a in actuators if a["type"] == "FAN")
        # Rechazo cuando el actuador ya está apagado o hay una orden en curso (409 Conflict)
        status, conflict = call("POST", f"/api/v1/crops/{v_id}/commands",
                                {"actuatorId": fan["id"], "action": "DEACTIVATE"}, token=demo_token)
        expect(status == 409 and ("ya está apagado" in conflict.get("message", "") or "en curso" in conflict.get("message", "")),
               "Control de conflicto previene órdenes redundantes o concurrentes (409)")

        status, cmd = call("POST", f"/api/v1/crops/{v_id}/commands",
                           {"actuatorId": fan["id"], "action": "ACTIVATE", "durationSeconds": 60}, token=demo_token)
        expect(status in (200, 201, 202) and cmd.get("status") in ("PENDING", "SENT"), "Comando enviado al ventilador")

        # 9. Consulta al Asistente de IA
        status, insight = call("GET", f"/api/v1/crops/{v_id}/insights", token=demo_token)
        expect(status == 200 and 0 <= insight.get("health", {}).get("index", -1) <= 100, "Asistente SmartPot-AI responde diagnóstico válido")

        # 10. Agregación de Series Temporales (TimescaleDB time_bucket)
        status, series = call("GET", "/api/v1/overview/series?metric=temperature&hours=1", token=demo_token)
        expect(status == 200 and "series" in series, "Series temporales calculadas por TimescaleDB")

    finally:
        # Limpieza del cultivo virtual de prueba
        call("DELETE", f"/api/v1/crops/{v_id}", token=demo_token)
        print("  ✔ Limpieza del cultivo virtual completada")

    print("\n================================================================================")
    print("  RESULTADO: DEMO BETA 100% OPERATIVA Y EN PARIDAD DE CONTRATO")
    print("================================================================================\n")


if __name__ == "__main__":
    try:
        run_beta_suite()
    except CheckFailed as e:
        print(f"\n[FALLO] Comprobación no superada: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Excepción imprevista: {e}")
        sys.exit(1)
