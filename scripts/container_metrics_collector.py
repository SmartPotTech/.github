#!/usr/bin/env python3
"""Recolección real de métricas de contenedores Docker y evaluación de compuertas QA para SmartPot."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

GATE_THRESHOLDS: dict[str, float] = {
    "max_total_memory_mb": 2048.0,
    "max_api_memory_mb": 256.0,
    "max_web_memory_mb": 64.0,
    "max_avg_cpu_pct": 85.0,
    "max_container_mem_pct": 90.0,
    "min_running_containers": 1.0,
}

_SIZE_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?i?B)\s*$", re.IGNORECASE)
_SIZE_FACTORS_MB: dict[str, float] = {
    "b": 1.0 / (1000.0 * 1000.0),
    "kb": 1.0 / 1000.0,
    "kib": 1024.0 / (1024.0 * 1024.0),
    "mb": 1.0,
    "mib": 1.048576,
    "gb": 1000.0,
    "gib": 1073.741824,
    "tb": 1_000_000.0,
    "tib": 1_099_511.627776,
}


@dataclass(frozen=True)
class ContainerMetric:
    name: str
    cpu_pct: float
    mem_used_mb: float
    mem_limit_mb: float
    mem_pct: float
    pids: int


@dataclass(frozen=True)
class GateResult:
    name: str
    measured: str
    threshold: str
    passed: bool


def parse_size_mb(raw: str) -> float:
    """Convierte tamaños de `docker stats` (ej. '42.5MiB', '1.2GiB') a megabytes."""
    match = _SIZE_RE.match(raw)
    if not match:
        raise ValueError(f"Unrecognized container memory size: {raw!r}")
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value * _SIZE_FACTORS_MB[unit]


def parse_percent(raw: str) -> float:
    """Convierte porcentajes como '12.34%' en flotante."""
    return float(raw.strip().rstrip("%"))


def parse_docker_stats_lines(lines: Iterable[str], prefix: str = "") -> list[ContainerMetric]:
    """Parsea líneas JSON emitidas por `docker stats --no-stream --format '{{json .}}'`."""
    metrics: list[ContainerMetric] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        name = str(payload.get("Name") or payload.get("Container") or "").strip()
        if prefix and not name.startswith(prefix):
            continue
        mem_usage = str(payload.get("MemUsage") or "")
        if "/" in mem_usage:
            used_raw, limit_raw = mem_usage.split("/", 1)
            mem_used_mb = parse_size_mb(used_raw)
            mem_limit_mb = parse_size_mb(limit_raw)
        else:
            mem_used_mb = 0.0
            mem_limit_mb = 0.0
        pids_raw = str(payload.get("PIDs") or "0").strip()
        metrics.append(
            ContainerMetric(
                name=name,
                cpu_pct=parse_percent(str(payload.get("CPUPerc") or "0%")),
                mem_used_mb=mem_used_mb,
                mem_limit_mb=mem_limit_mb,
                mem_pct=parse_percent(str(payload.get("MemPerc") or "0%")),
                pids=int(pids_raw) if pids_raw.isdigit() else 0,
            )
        )
    return sorted(metrics, key=lambda item: item.name)


def collect_docker_stats(prefix: str = "smartpot") -> list[ContainerMetric]:
    """Ejecuta `docker stats --no-stream` sobre contenedores activos."""
    proc = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        raise RuntimeError(f"Failed to execute docker stats: {detail}")
    return parse_docker_stats_lines(proc.stdout.splitlines(), prefix=prefix)


def _find_service_memory(metrics: list[ContainerMetric], token: str) -> float | None:
    matches = [item.mem_used_mb for item in metrics if token in item.name.lower()]
    if not matches:
        return None
    return sum(matches)


def evaluate_quality_gates(
    metrics: list[ContainerMetric],
    thresholds: dict[str, float] | None = None,
) -> list[GateResult]:
    """Evalúa métricas medidas reales contra los umbrales de calidad."""
    limits = thresholds or GATE_THRESHOLDS
    count = len(metrics)
    total_mem_mb = sum(item.mem_used_mb for item in metrics)
    avg_cpu_pct = (sum(item.cpu_pct for item in metrics) / count) if count > 0 else 0.0
    max_mem_pct = max((item.mem_pct for item in metrics), default=0.0)
    api_mem_mb = _find_service_memory(metrics, "api")
    web_mem_mb = _find_service_memory(metrics, "web")

    results: list[GateResult] = [
        GateResult(
            name="running_containers",
            measured=str(count),
            threshold=f">= {int(limits['min_running_containers'])}",
            passed=count >= limits["min_running_containers"],
        ),
        GateResult(
            name="total_memory_mb",
            measured=f"{total_mem_mb:.1f} MB",
            threshold=f"<= {limits['max_total_memory_mb']:.1f} MB",
            passed=count > 0 and total_mem_mb <= limits["max_total_memory_mb"],
        ),
        GateResult(
            name="avg_cpu_pct",
            measured=f"{avg_cpu_pct:.2f}%",
            threshold=f"<= {limits['max_avg_cpu_pct']:.1f}%",
            passed=count > 0 and avg_cpu_pct <= limits["max_avg_cpu_pct"],
        ),
        GateResult(
            name="peak_container_mem_pct",
            measured=f"{max_mem_pct:.2f}%",
            threshold=f"<= {limits['max_container_mem_pct']:.1f}%",
            passed=count > 0 and max_mem_pct <= limits["max_container_mem_pct"],
        ),
    ]
    if api_mem_mb is not None:
        results.append(
            GateResult(
                name="api_memory_mb",
                measured=f"{api_mem_mb:.1f} MB",
                threshold=f"<= {limits['max_api_memory_mb']:.1f} MB",
                passed=api_mem_mb <= limits["max_api_memory_mb"],
            )
        )
    if web_mem_mb is not None:
        results.append(
            GateResult(
                name="web_memory_mb",
                measured=f"{web_mem_mb:.1f} MB",
                threshold=f"<= {limits['max_web_memory_mb']:.1f} MB",
                passed=web_mem_mb <= limits["max_web_memory_mb"],
            )
        )
    return results


def render_report(metrics: list[ContainerMetric], gates: list[GateResult], baseline_total_mb: float | None = None) -> str:
    """Construye el reporte tabular a partir de métricas reales."""
    lines: list[str] = [
        "=== SmartPot Live Container Resource Telemetry ===",
        f"{'Container':<32} {'CPU %':>8} {'Mem (MB)':>12} {'Mem %':>8} {'PIDs':>6}",
        "-" * 72,
    ]
    for item in metrics:
        lines.append(
            f"{item.name:<32} {item.cpu_pct:>7.2f}% {item.mem_used_mb:>11.1f} {item.mem_pct:>7.2f}% {item.pids:>6}"
        )
    total_mem_mb = sum(item.mem_used_mb for item in metrics)
    lines.append("-" * 72)
    summary = f"Total containers: {len(metrics)} | Aggregate memory: {total_mem_mb:.1f} MB"
    if baseline_total_mb is not None and baseline_total_mb > 0:
        delta_pct = ((total_mem_mb - baseline_total_mb) / baseline_total_mb) * 100.0
        summary += f" | Delta vs baseline ({baseline_total_mb:.1f} MB): {delta_pct:+.1f}%"
    lines.append(summary)
    lines.append("")
    lines.append("=== Quality Gate Evaluation ===")
    for gate in gates:
        verdict = "PASS" if gate.passed else "FAIL"
        lines.append(f"  [{verdict}] {gate.name:<26} measured={gate.measured:<12} threshold={gate.threshold}")
    all_ok = all(gate.passed for gate in gates)
    lines.append("")
    lines.append(f"Final Quality Gate Verdict: {'APPROVED' if all_ok else 'FAILED'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect live SmartPot container metrics and evaluate QA gates.")
    parser.add_argument("--prefix", default="smartpot", help="Container name prefix filter (default: smartpot)")
    parser.add_argument("--baseline-json", type=Path, help="Optional baseline metrics JSON generated previously")
    parser.add_argument("--output-json", type=Path, help="Optional path to persist measured metrics JSON")
    args = parser.parse_args(argv)

    try:
        metrics = collect_docker_stats(prefix=args.prefix)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    baseline_total_mb: float | None = None
    if args.baseline_json:
        try:
            baseline_data = json.loads(args.baseline_json.read_text(encoding="utf-8"))
            baseline_total_mb = float(sum(item.get("mem_used_mb", 0.0) for item in baseline_data.get("containers", [])))
        except (OSError, ValueError, TypeError) as exc:
            print(f"ERROR: Invalid baseline JSON {args.baseline_json}: {exc}", file=sys.stderr)
            return 1

    gates = evaluate_quality_gates(metrics)
    print(render_report(metrics, gates, baseline_total_mb=baseline_total_mb))

    if args.output_json:
        payload = {
            "containers": [asdict(item) for item in metrics],
            "gates": [asdict(gate) for gate in gates],
            "approved": all(gate.passed for gate in gates),
        }
        args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return 0 if all(gate.passed for gate in gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
