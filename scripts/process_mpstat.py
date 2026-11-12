#!/usr/bin/env python3
"""
process_mpstat.py — Parse mpstat output and compute per-run CPU statistics.

Usage: python3 scripts/process_mpstat.py <mpstat_file> <scenario> <rep>

Appends a row to results/mpstat-summary.csv with mean/std of CPU utilization.
Also keeps the raw mpstat file for reference.
"""

import sys
import os
import re
from pathlib import Path


def parse_mpstat_file(filepath):
    """Parse mpstat output file and return list of CPU utilization samples.

    Returns a list of dicts with keys: timestamp, cpu_id, usr, sys, idle, etc.
    The 'all' row is the aggregate across all CPUs.
    """
    rows = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Linux"):
                continue

            fields = line.split()
            if len(fields) < 11:
                continue

            try:
                timestamp = fields[0]
                cpu_id = fields[1]
                if cpu_id == "CPU":
                    continue

                usr = float(fields[2].replace(",", "."))
                nice = float(fields[3].replace(",", "."))
                sys_val = float(fields[4].replace(",", "."))
                iowait = float(fields[5].replace(",", "."))
                irq = float(fields[6].replace(",", "."))
                soft = float(fields[7].replace(",", "."))
                steal = float(fields[8].replace(",", "."))
                guest = float(fields[9].replace(",", "."))
                gnice = float(fields[10].replace(",", "."))
                idle = float(fields[11].replace(",", ".")) if len(fields) > 11 else 0.0

                used = 100.0 - idle

                rows.append({
                    "timestamp": timestamp,
                    "cpu_id": cpu_id,
                    "usr": usr,
                    "nice": nice,
                    "sys": sys_val,
                    "iowait": iowait,
                    "irq": irq,
                    "soft": soft,
                    "steal": steal,
                    "guest": guest,
                    "gnice": gnice,
                    "idle": idle,
                    "used": used,
                })
            except (ValueError, IndexError):
                continue

    return rows


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 process_mpstat.py <mpstat_file> <scenario> <rep>")
        sys.exit(1)

    mpstat_file = sys.argv[1]
    scenario = sys.argv[2]
    rep = int(sys.argv[3])

    if not os.path.exists(mpstat_file):
        print(f"  mpstat file not found: {mpstat_file}")
        return

    rows = parse_mpstat_file(mpstat_file)
    if not rows:
        print(f"  No mpstat data in {mpstat_file}")
        return

    all_rows = [r for r in rows if r["cpu_id"] == "all"]
    if not all_rows:
        all_rows = rows

    import numpy as np

    used_values = [r["used"] for r in all_rows]
    usr_values = [r["usr"] for r in all_rows]
    sys_values = [r["sys"] for r in all_rows]
    iowait_values = [r["iowait"] for r in all_rows]

    config = scenario.split("-")[0]
    load = scenario.split("-")[1]

    vus_map = {"low": 10, "medium": 50, "high": 100}
    vus = vus_map.get(load, 0)

    results_dir = Path(mpstat_file).parent
    output_file = results_dir / "mpstat-summary.csv"

    write_header = not output_file.exists()

    row_str = (
        f"{scenario},{rep},{vus},{config},{load},"
        f"{np.mean(used_values):.2f},{np.std(used_values):.2f},"
        f"{np.mean(usr_values):.2f},{np.std(usr_values):.2f},"
        f"{np.mean(sys_values):.2f},{np.std(sys_values):.2f},"
        f"{np.mean(iowait_values):.2f},{np.std(iowait_values):.2f},"
        f"{np.min(used_values):.2f},{np.max(used_values):.2f},"
        f"{len(used_values)}"
    )

    with open(output_file, "a") as f:
        if write_header:
            f.write("scenario,rep,vus,config,load,"
                    "cpu_used_mean,cpu_used_std,"
                    "cpu_usr_mean,cpu_usr_std,"
                    "cpu_sys_mean,cpu_sys_std,"
                    "cpu_iowait_mean,cpu_iowait_std,"
                    "cpu_used_min,cpu_used_max,"
                    "samples\n")
        f.write(row_str + "\n")

    print(f"  mpstat: used={np.mean(used_values):.2f}% +/- {np.std(used_values):.2f}% "
          f"(n={len(used_values)}, min={np.min(used_values):.2f}, max={np.max(used_values):.2f})")


if __name__ == "__main__":
    main()