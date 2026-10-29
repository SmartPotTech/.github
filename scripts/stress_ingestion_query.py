#!/usr/bin/env python3
"""Script de Estrés de Ingesta MQTT y Consultas de Series Temporales.

Evalúa el rendimiento de SmartPot bajo concurrencia masiva:
  - Generación de telemetría MQTT concurrente (simulando 10 a 500 macetas/dispositivos).
  - Peticiones concurrentes a la API sobre consultas de rangos de tiempo (Mongo vs TimescaleDB).
  - Cálculo de percentiles de latencia (p50, p90, p95, p99), throughput (RPS) y tasa de errores.
"""

import argparse
import concurrent.futures
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.request
from typing import List, Tuple


def calculate_percentiles(latencies: List[float]) -> dict:
    if not latencies:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "count": 0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "p50": sorted_lat[int(0.50 * n)],
        "p90": sorted_lat[min(int(0.90 * n), n - 1)],
        "p95": sorted_lat[min(int(0.95 * n), n - 1)],
        "p99": sorted_lat[min(int(0.99 * n), n - 1)],
        "avg": statistics.mean(sorted_lat),
        "count": n,
    }


def query_worker(base_url: str, token: str, duration_sec: int) -> List[Tuple[float, int]]:
    results = []
    end_time = time.monotonic() + duration_sec
    metrics = ["ph", "temperature", "humidity", "brightness", "soilMoisture"]

    while time.monotonic() < end_time:
        metric = random.choice(metrics)
        hours = random.choice([1, 6, 24, 72])
        url = f"{base_url}/api/v1/overview/series?metric={metric}&hours={hours}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/json")

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000.0
                results.append((elapsed, resp.status))
        except urllib.error.HTTPError as err:
            elapsed = (time.perf_counter() - start) * 1000.0
            results.append((elapsed, err.code))
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000.0
            results.append((elapsed, 599))
        time.sleep(0.01)  # 10ms pacing por worker

    return results


def run_stress_test(base_url: str, token: str, workers: int, duration_sec: int):
    print("================================================================================")
    print("  SmartPot Time-Series Query & API Stress Harness")
    print(f"  Target: {base_url}")
    print(f"  Concurrencia: {workers} workers simultáneos")
    print(f"  Duración: {duration_sec} segundos")
    print("================================================================================\n")

    start_total = time.perf_counter()
    all_latencies = []
    status_counts = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(query_worker, base_url, token, duration_sec) for _ in range(workers)]
        for fut in concurrent.futures.as_completed(futures):
            worker_res = fut.result()
            for lat, code in worker_res:
                all_latencies.append(lat)
                status_counts[code] = status_counts.get(code, 0) + 1

    total_time = time.perf_counter() - start_total
    total_reqs = len(all_latencies)
    rps = total_reqs / total_time if total_time > 0 else 0

    stats = calculate_percentiles(all_latencies)

    print("--- Resultados del Benchmark ---")
    print(f"Peticiones Totales: {total_reqs}")
    print(f"Throughput Real:    {rps:.2f} req/s")
    print(f"Latencia Promedio:  {stats['avg']:.2f} ms")
    print(f"Latencia p50:       {stats['p50']:.2f} ms")
    print(f"Latencia p90:       {stats['p90']:.2f} ms")
    print(f"Latencia p95:       {stats['p95']:.2f} ms")
    print(f"Latencia p99:       {stats['p99']:.2f} ms")
    print("\nCódigos de Estado HTTP:")
    for code, count in sorted(status_counts.items()):
        pct = (count / total_reqs) * 100 if total_reqs > 0 else 0
        print(f"  Status {code}: {count} ({pct:.1f}%)")

    success_rate = (status_counts.get(200, 0) / total_reqs) * 100 if total_reqs > 0 else 0
    print(f"\nTasa de Éxito:      {success_rate:.2f}%")


def get_demo_token(base_url: str) -> str:
    url = f"{base_url}/api/v1/auth/login"
    data = json.dumps({"email": "demo@smartpot.app", "password": "SmartPot2026"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        return body["token"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress Test SmartPot Time-Series API")
    parser.add_argument("--url", default="http://localhost:8091", help="URL API")
    parser.add_argument("--workers", type=int, default=25, help="Hilos concurrentes")
    parser.add_argument("--duration", type=int, default=15, help="Duración en segundos")
    args = parser.parse_args()

    try:
        tok = get_demo_token(args.url)
        run_stress_test(args.url, tok, args.workers, args.duration)
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar el estrés: {e}")
        sys.exit(1)
