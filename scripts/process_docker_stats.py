#!/usr/bin/env python3
"""
process_docker_stats.py — Parse docker stats time-series CSV and compute
per-container CPU/memory statistics with mean, std, min, max.

Usage: python3 scripts/process_docker_stats.py <dstats_file> <scenario> <rep>

Appends rows to results/dockerstats-summary.csv.
"""

import sys
import os
import numpy as np
from pathlib import Path


def parse_docker_stats_file(filepath):
    """Parse docker stats time-series CSV produced by start_docker_stats_collection."""
    rows = []
    with open(filepath, "r") as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = line.split(",", 7)
            if len(fields) < 7:
                continue
            try:
                ts = fields[0]
                container = fields[1]
                cpu_pct = float(fields[2]) if fields[2] != "N/A" else np.nan
                mem_used = fields[3]
                mem_limit = fields[4]
                mem_pct = float(fields[5]) if fields[5] != "N/A" else np.nan
                rows.append({
                    "timestamp": ts,
                    "container": container,
                    "cpu_pct": cpu_pct,
                    "mem_used_str": mem_used,
                    "mem_limit_str": mem_limit,
                    "mem_pct": mem_pct,
                })
            except (ValueError, IndexError):
                continue
    return rows


def parse_mem_to_mib(mem_str):
    """Parse memory string like '150MiB' to float MiB."""
    if not mem_str or mem_str == "N/A":
        return np.nan
    mem_str = mem_str.strip().replace(",", ".")
    if "GiB" in mem_str:
        return float(mem_str.replace("GiB", "").strip()) * 1024
    elif "MiB" in mem_str:
        return float(mem_str.replace("MiB", "").strip())
    elif "KiB" in mem_str:
        return float(mem_str.replace("KiB", "").strip()) / 1024
    return np.nan


VUS_MAP = {"low": 10, "medium": 50, "high": 100}
SERVICES = ["ts-gateway-service", "ts-order-service", "ts-payment-service", "ts-travel-service"]


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 process_docker_stats.py <dstats_file> <scenario> <rep>")
        sys.exit(1)

    dstats_file = sys.argv[1]
    scenario = sys.argv[2]
    rep = int(sys.argv[3])

    if not os.path.exists(dstats_file):
        print(f"  docker stats file not found: {dstats_file}")
        return

    rows = parse_docker_stats_file(dstats_file)
    if not rows:
        print(f"  No docker stats data in {dstats_file}")
        return

    config = scenario.split("-")[0]
    load = scenario.split("-")[1]
    vus = VUS_MAP.get(load, 0)

    results_dir = Path(dstats_file).parent
    output_file = results_dir / "dockerstats-summary.csv"

    write_header = not output_file.exists()

    with open(output_file, "a") as f:
        if write_header:
            f.write("scenario,rep,vus,config,load,service,"
                    "cpu_mean,cpu_std,cpu_min,cpu_max,cpu_p50,cpu_p95,cpu_p99,"
                    "mem_mean,mem_std,mem_min,mem_max,mem_p50,mem_p95,"
                    "samples\n")

        for svc in SERVICES:
            svc_rows = [r for r in rows if r["container"] == svc]
            if not svc_rows:
                continue

            cpu_vals = np.array([r["cpu_pct"] for r in svc_rows if not np.isnan(r["cpu_pct"])])
            mem_vals = np.array([parse_mem_to_mib(r["mem_used_str"]) for r in svc_rows
                                if not np.isnan(r["mem_pct"])])

            if len(cpu_vals) < 2:
                continue

            row = (
                f"{scenario},{rep},{vus},{config},{load},{svc},"
                f"{np.mean(cpu_vals):.4f},{np.std(cpu_vals):.4f},"
                f"{np.min(cpu_vals):.4f},{np.max(cpu_vals):.4f},"
                f"{np.percentile(cpu_vals, 50):.4f},{np.percentile(cpu_vals, 95):.4f},"
                f"{np.percentile(cpu_vals, 99):.4f},"
                f"{np.mean(mem_vals):.1f},{np.std(mem_vals):.1f},"
                f"{np.min(mem_vals):.1f},{np.max(mem_vals):.1f},"
                f"{np.percentile(mem_vals, 50):.1f},{np.percentile(mem_vals, 95):.1f},"
                f"{len(cpu_vals)}\n"
            )
            f.write(row)

    print(f"  docker stats: processed {len(rows)} rows for {scenario} rep {rep}")


if __name__ == "__main__":
    main()