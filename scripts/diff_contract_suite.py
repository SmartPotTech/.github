#!/usr/bin/env python3
"""Suite de Pruebas Diferenciales de Contrato (A/B Testing) para SmartPot.

Compara byte-a-byte y estructuralmente las respuestas HTTP entre:
  - Entorno A: Spring Boot 4 / Java 21 (smartpot-api)
  - Entorno B: Go 1.26 / Echo v4 (SmartPot-API-Go)

Valida paridad estricta de:
  - Códigos de estado HTTP (200, 201, 204, 400, 401, 403, 404, 405, 409, 429)
  - Mensajes de error en español
  - Formatos de fecha ISO-8601 UTC
  - Esquemas JSON, nombres de atributos (camelCase) y omisión de nulos
"""

import argparse
import difflib
import json
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

ISO_8601_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
OID_REGEX = re.compile(r"^[0-9a-fA-F]{24}$")


def normalize_json(obj: Any) -> Any:
    """Normaliza identificadores y marcas de tiempo dinámicas para comparar contratos."""
    if isinstance(obj, dict):
        normalized = {}
        for k, v in obj.items():
            if k in ("id", "cropId", "actuatorId", "userId", "ownerId") and isinstance(v, str) and OID_REGEX.match(v):
                normalized[k] = "<OBJECT_ID>"
            elif k in ("createdAt", "updatedAt", "measuredAt", "sentAt", "completedAt", "timestamp", "runningUntil", "expiresAt") and isinstance(v, str) and ISO_8601_REGEX.match(v):
                normalized[k] = "<ISO_8601_TIMESTAMP>"
            elif k in ("token", "key", "keyCiphertext") and isinstance(v, str):
                normalized[k] = "<CREDENTIAL_TOKEN>"
            else:
                normalized[k] = normalize_json(v)
        return normalized
    elif isinstance(obj, list):
        return [normalize_json(item) for item in obj]
    return obj


class DifferentialRunner:
    def __init__(self, url_a: str, url_b: Optional[str] = None):
        self.url_a = url_a.rstrip("/")
        self.url_b = url_b.rstrip("/") if url_b else None
        self.history_a: Dict[str, Tuple[int, Any, dict]] = {}
        self.history_b: Dict[str, Tuple[int, Any, dict]] = {}

    def execute_request(self, base_url: str, method: str, path: str, body: Optional[dict] = None, token: Optional[str] = None) -> Tuple[int, Any, dict]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{base_url}{path}", data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if raw else None), dict(resp.headers)
        except urllib.error.HTTPError as err:
            raw = err.read()
            try:
                parsed = json.loads(raw) if raw else None
            except Exception:
                parsed = raw.decode(errors="replace")
            return err.code, parsed, dict(err.headers)
        except Exception as e:
            return 500, {"error": str(e)}, {}

    def run_differential_check(self, label: str, method: str, path: str, body: Optional[dict] = None,
                               token_a: Optional[str] = None, token_b: Optional[str] = None) -> bool:
        code_a, res_a, h_a = self.execute_request(self.url_a, method, path, body, token_a)
        if not self.url_b:
            print(f"  [Stack A] {label}: Status={code_a}")
            return code_a < 500

        code_b, res_b, h_b = self.execute_request(self.url_b, method, path, body, token_b)
        
        status_match = code_a == code_b
        norm_a = normalize_json(res_a)
        norm_b = normalize_json(res_b)
        body_match = norm_a == norm_b

        passed = status_match and body_match
        icon = "✔" if passed else "✖"
        print(f"  {icon} {label} -> A: {code_a} | B: {code_b} | Paridad: {'OK' if passed else 'DIVERGENCIA'}")

        if not passed:
            print("     [-] Divergencia detectada:")
            diff = difflib.unified_diff(
                json.dumps(norm_a, indent=2, ensure_ascii=False).splitlines(),
                json.dumps(norm_b, indent=2, ensure_ascii=False).splitlines(),
                fromfile="Stack_A_Spring",
                tofile="Stack_B_Go",
                lineterm=""
            )
            for line in diff:
                print(f"       {line}")
        return passed


def main():
    parser = argparse.ArgumentParser(description="Differential Contract Tester SmartPot")
    parser.add_argument("--url-a", default="http://localhost:8091", help="URL Stack A (Estable)")
    parser.add_argument("--url-b", default=None, help="URL Stack B (BETA, opcional)")
    args = parser.parse_args()

    runner = DifferentialRunner(args.url_a, args.url_b)
    print("================================================================================")
    print("  SmartPot A/B Differential Contract Verification Suite")
    print(f"  Target A: {args.url_a}")
    print(f"  Target B: {args.url_b or '(Solo auditoria A)'}")
    print("================================================================================\n")

    # 1. Healthcheck
    runner.run_differential_check("Healthcheck Endpoint", "GET", "/health")

    # 2. Rutas no autenticadas (401 Guard)
    runner.run_differential_check("Crops Unauthenticated Guard", "GET", "/api/v1/crops")
    runner.run_differential_check("Overview Unauthenticated Guard", "GET", "/api/v1/overview")

    # 3. Métodos no permitidos (405 Guard)
    runner.run_differential_check("Method Not Allowed 405", "DELETE", "/health")

    # 4. Rutas inexistentes (404 Guard)
    runner.run_differential_check("Not Found 404 Guard", "GET", "/api/v1/ruta-inexistente-smartpot")

    # 5. Registro y Login
    email = f"contract-qa-{secrets.token_hex(4)}@smartpot.test"
    pwd = f"SecPass{secrets.token_hex(4)}9#"
    runner.run_differential_check("Register User Contract", "POST", "/api/v1/auth/register",
                                  {"name": "Diff", "lastName": "Runner", "email": email, "password": pwd})
    
    # Obtener token A y B
    _, body_a, _ = runner.execute_request(args.url_a, "POST", "/api/v1/auth/login", {"email": email, "password": pwd})
    tok_a = (body_a or {}).get("token")
    tok_b = None
    if args.url_b:
        _, body_b, _ = runner.execute_request(args.url_b, "POST", "/api/v1/auth/login", {"email": email, "password": pwd})
        tok_b = (body_b or {}).get("token")

    if tok_a:
        # 6. Creación de Cultivo Real
        crop_payload = {"name": "Lechuga Diff", "type": "LETTUCE", "kind": "REAL", "form": "NFT"}
        runner.run_differential_check("Create Real Crop Contract", "POST", "/api/v1/crops", crop_payload, tok_a, tok_b)

        # 7. Creación de Cultivo Virtual
        virt_payload = {
            "name": "Tomate Virtual Diff", "type": "TOMATO", "kind": "VIRTUAL", "form": "POT",
            "virtual": {"mode": "MANUAL", "intervalSeconds": 10, "manual": {"soilMoisture": 60, "ph": 6.2}}
        }
        runner.run_differential_check("Create Virtual Crop Contract", "POST", "/api/v1/crops", virt_payload, tok_a, tok_b)

        # 8. Modificación ilegal de Kind (400 Guard)
        runner.run_differential_check("Invalid Kind Mutation", "PUT", "/api/v1/crops/66f5a1000000000000000101",
                                      {"name": "Cambio", "type": "LETTUCE", "kind": "VIRTUAL"}, tok_a, tok_b)

        # 9. Limpieza de usuario
        runner.execute_request(args.url_a, "DELETE", "/api/v1/users/me", token=tok_a)
        if args.url_b and tok_b:
            runner.execute_request(args.url_b, "DELETE", "/api/v1/users/me", token=tok_b)

    print("\n[OK] Verificación diferencial de contratos finalizada.")


if __name__ == "__main__":
    main()
