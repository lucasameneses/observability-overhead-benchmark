#!/usr/bin/env python3
"""
analyze.py — Statistical analysis of observability overhead experiments.

Methodology (Jain, 1991):
  1. Shapiro-Wilk normality test per group
  2. If normal: paired t-test (2 groups) or ANOVA + Tukey (3+ groups)
  3. If non-normal: Mann-Whitney U (2 groups) or Kruskal-Wallis (3+ groups)
  All tests at 95% confidence level (alpha = 0.05).

Usage:
  python3 scripts/analyze.py [--results-dir DIR] [--output-dir DIR]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ALPHA = 0.05
REPS = 30

CONFIGS = ["baseline", "observed"]
LOADS = ["low", "medium", "high"]
VUS = {"low": 10, "medium": 50, "high": 100}
SERVICES = ["gateway", "order", "payment", "travel"]


def parse_k6_json(filepath):
    """Parse k6 JSON output and extract summary metrics."""
    http_reqs = []

    with open(filepath, 'r') as f:
        for line in f:
            try:
                point = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            if point.get("type") == "Point" and point.get("metric") == "http_req_duration":
                data = point.get("data", {})
                if data.get("value") is not None:
                    http_reqs.append(data.get("value"))

    if not http_reqs:
        return None

    return {
        "p50": np.percentile(http_reqs, 50),
        "p95": np.percentile(http_reqs, 95),
        "p99": np.percentile(http_reqs, 99),
        "mean": np.mean(http_reqs),
        "std": np.std(http_reqs),
        "min": np.min(http_reqs),
        "max": np.max(http_reqs),
        "count": len(http_reqs),
    }


def parse_k6_json_detailed(filepath):
    """Parse k6 JSON output and extract ALL metrics as dict of lists."""
    result = {}

    with open(filepath, 'r') as f:
        for line in f:
            try:
                point = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            if point.get("type") != "Point":
                continue

            metric = point.get("metric")
            value = point.get("data", {}).get("value")
            if value is None:
                continue

            if metric not in result:
                result[metric] = []
            result[metric].append(value)

    return result


def load_all_k6_detailed(results_dir):
    """Load all k6 JSON results with detailed metrics, keyed by (config, load, rep)."""
    cache = {}

    for config in CONFIGS:
        for load in LOADS:
            for rep in range(1, 100):
                scenario = f"{config}-{load}"
                rep_padded = f"{rep:02d}"
                filepath = Path(results_dir) / f"{scenario}_rep{rep_padded}.json"

                if not filepath.exists():
                    continue

                detailed = parse_k6_json_detailed(str(filepath))
                cache[(config, load, rep)] = detailed

    return cache


def load_k6_results(results_dir):
    """Load all k6 JSON results into a DataFrame."""
    rows = []

    for config in CONFIGS:
        for load in LOADS:
            for rep in range(1, 100):
                scenario = f"{config}-{load}"
                rep_padded = f"{rep:02d}"
                filepath = Path(results_dir) / f"{scenario}_rep{rep_padded}.json"

                if not filepath.exists():
                    continue

                metrics = parse_k6_json(str(filepath))
                if metrics is None:
                    continue

                rows.append({
                    "config": config,
                    "load": load,
                    "vus": VUS[load],
                    "rep": rep,
                    "scenario": scenario,
                    **metrics,
                })

    return pd.DataFrame(rows)


def load_metrics_csv(results_dir):
    """Load metrics.csv with CPU/memory data."""
    filepath = Path(results_dir) / "metrics.csv"
    if not filepath.exists():
        return None
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(how="all")
    # run-experiments.sh appends to metrics.csv, so a re-run scenario has
    # older batches above the newest one. Keep the newest REPS rows, which
    # belong to the same run as the k6 JSON files.
    df = df.groupby("scenario", sort=False).tail(REPS)
    df["load"] = df["scenario"].str.split("-").str[-1]
    df["config"] = df["scenario"].str.split("-").str[0]
    for svc in SERVICES:
        mem_col = f"mem_{svc}"
        if mem_col in df.columns:
            df[mem_col] = df[mem_col].apply(parse_memory_mb)
    return df


def parse_memory_mb(mem_str):
    """Parse memory string like '150MiB' or '256.5MiB' to float MB."""
    if pd.isna(mem_str) or mem_str == "N/A":
        return np.nan
    mem_str = str(mem_str).strip().replace(",", ".")
    if "GiB" in mem_str:
        return float(mem_str.replace("GiB", "").strip()) * 1024
    elif "MiB" in mem_str:
        return float(mem_str.replace("MiB", "").strip())
    elif "KiB" in mem_str:
        return float(mem_str.replace("KiB", "").strip()) / 1024
    elif "B" in mem_str:
        return float(mem_str.replace("B", "").strip()) / 1024 / 1024
    return np.nan


def shapiro_wilk_test(df, metric_col, group_col):
    """Run Shapiro-Wilk normality test for each group."""
    results = []
    for name, group in df.groupby(group_col):
        values = group[metric_col].dropna()
        if len(values) < 3:
            continue
        stat, p = stats.shapiro(values)
        results.append({
            group_col: name,
            "metric": metric_col,
            "statistic": stat,
            "p_value": p,
            "normal": p > ALPHA,
        })
    return pd.DataFrame(results)


def compare_two_groups(baseline, observed, metric_name):
    """Compare two groups using t-test or Mann-Whitney U."""
    b = baseline.dropna()
    o = observed.dropna()

    if len(b) < 3 or len(o) < 3:
        return None

    _, p_norm_b = stats.shapiro(b)
    _, p_norm_o = stats.shapiro(o)

    both_normal = (p_norm_b > ALPHA) and (p_norm_o > ALPHA)

    if both_normal:
        stat, p = stats.ttest_ind(b, o)
        test = "t-test"
    else:
        stat, p = stats.mannwhitneyu(b, o, alternative='two-sided')
        test = "Mann-Whitney U"

    return {
        "metric": metric_name,
        "test": test,
        "statistic": stat,
        "p_value": p,
        "significant": p < ALPHA,
        "baseline_mean": round(b.mean(), 3),
        "observed_mean": round(o.mean(), 3),
        "baseline_std": round(b.std(), 3),
        "observed_std": round(o.std(), 3),
        "overhead_pct": round(((o.mean() - b.mean()) / b.mean() * 100), 2) if b.mean() != 0 else float('inf'),
    }


def anova_or_kruskal(df, metric_col, group_col):
    """Run ANOVA or Kruskal-Wallis across multiple groups."""
    groups = []
    names = []
    for name, group in df.groupby(group_col):
        vals = group[metric_col].dropna()
        if len(vals) >= 3:
            groups.append(vals)
            names.append(name)

    if len(groups) < 2:
        return None

    _, p_norms = zip(*[stats.shapiro(g) for g in groups])
    all_normal = all(p > ALPHA for p in p_norms)

    if all_normal:
        stat, p = stats.f_oneway(*groups)
        test = "ANOVA"
    else:
        stat, p = stats.kruskal(*groups)
        test = "Kruskal-Wallis"

    return {
        "metric": metric_col,
        "test": test,
        "statistic": stat,
        "p_value": p,
        "significant": p < ALPHA,
        "groups": str(names),
    }


def plot_latency_comparison(df, output_dir):
    """Generate boxplots comparing baseline vs observed for each load level."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    metrics = [("p50", "Latency p50 (ms)"), ("p95", "Latency p95 (ms)"), ("p99", "Latency p99 (ms)")]

    for ax, (metric, title) in zip(axes, metrics):
        sns.boxplot(data=df, x="load", y=metric, hue="config", ax=ax, order=LOADS)
        ax.set_title(title)
        ax.set_xlabel("Load Level")
        ax.set_ylabel("Latency (ms)")

    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "latency_comparison.png", dpi=150)
    plt.close()


def plot_latency_per_load(df, output_dir):
    """Generate bar charts with error bars for each load level."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    metrics = [("p50", "p50"), ("p95", "p95"), ("p99", "p99")]

    for ax, (metric, label) in zip(axes, metrics):
        summary = df.groupby(["config", "load"])[metric].agg(["mean", "std"]).reset_index()
        x = np.arange(len(LOADS))
        width = 0.35
        for i, config in enumerate(CONFIGS):
            subset = summary[summary["config"] == config]
            ax.bar(
                x=x + (i - 0.5) * width,
                height=subset["mean"].values,
                yerr=subset["std"].values,
                width=width,
                label=config,
                capsize=5,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(LOADS)
        ax.set_title(f"Latency {label} by Load Level")
        ax.set_xlabel("Load Level")
        ax.set_ylabel("Latency (ms)")
        ax.legend()

    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "latency_per_load.png", dpi=150)
    plt.close()


def plot_throughput_comparison(df, output_dir):
    """Generate throughput comparison chart."""
    df = df.copy()
    df["throughput"] = df["count"] / 330

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x="load", y="throughput", hue="config", ax=ax, order=LOADS)
    ax.set_title("Throughput by Load Level")
    ax.set_xlabel("Load Level")
    ax.set_ylabel("Throughput (req/s)")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "throughput_comparison.png", dpi=150)
    plt.close()


def plot_overhead_percentage(df, output_dir):
    """Generate overhead percentage chart."""
    rows = []
    for metric in ["p50", "p95", "p99"]:
        for load in LOADS:
            b = df[(df["config"] == "baseline") & (df["load"] == load)][metric]
            o = df[(df["config"] == "observed") & (df["load"] == load)][metric]
            if len(b) > 0 and len(o) > 0 and b.mean() > 0:
                overhead = (o.mean() - b.mean()) / b.mean() * 100
                rows.append({"metric": metric, "load": load, "overhead_pct": overhead})

    overhead_df = pd.DataFrame(rows)
    if overhead_df.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=overhead_df, x="load", y="overhead_pct", hue="metric", ax=ax, order=LOADS)
    ax.set_title("Observability Overhead (%) by Load Level")
    ax.set_xlabel("Load Level")
    ax.set_ylabel("Overhead (%)")
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "overhead_percentage.png", dpi=150)
    plt.close()


def plot_resource_comparison(metrics_df, output_dir):
    """Generate CPU and memory comparison charts."""
    if metrics_df is None or metrics_df.empty:
        return

    services = ["gateway", "order", "payment", "travel"]
    service_labels = ["Gateway", "Order", "Payment", "Travel"]

    for resource, unit, col_template, fname in [
        ("CPU", "%", "cpu_{}", "cpu_comparison.png"),
        ("Memory", "MiB", "mem_{}", "memory_comparison.png"),
    ]:
        fig, axes = plt.subplots(1, len(services), figsize=(20, 5), sharey=False)

        for i, (svc, label) in enumerate(zip(services, service_labels)):
            ax = axes[i]
            col = col_template.format(svc)
            if col not in metrics_df.columns:
                ax.set_title(f"{resource} — {label}\n(no data)")
                continue

            data = metrics_df.dropna(subset=[col]).copy()

            sns.boxplot(data=data, x="load", y=col, hue="config", ax=ax, order=LOADS)
            ax.set_title(f"{resource} — {label}")
            ax.set_xlabel("Load Level")
            ax.set_ylabel(f"{resource} ({unit})")

        plt.tight_layout()
        plt.savefig(Path(output_dir) / "figures" / fname, dpi=150)
        plt.close()


def plot_resource_heatmap(metrics_df, output_dir):
    """Generate heatmap of resource usage overhead per service per load."""
    if metrics_df is None or metrics_df.empty:
        return

    services = ["gateway", "order", "payment", "travel"]

    for resource, col_template, fname in [
        ("CPU", "cpu_{}", "cpu_overhead_heatmap.png"),
        ("Memory", "mem_{}", "memory_overhead_heatmap.png"),
    ]:
        overhead_rows = []

        for svc in services:
            col = col_template.format(svc)
            if col not in metrics_df.columns:
                continue

            for load in LOADS:
                b = metrics_df[(metrics_df["config"] == "baseline") & (metrics_df["load"] == load)][col].dropna()
                o = metrics_df[(metrics_df["config"] == "observed") & (metrics_df["load"] == load)][col].dropna()
                if len(b) > 0 and len(o) > 0 and b.mean() > 0:
                    overhead_rows.append({
                        "service": svc,
                        "load": load,
                        "overhead_pct": (o.mean() - b.mean()) / b.mean() * 100,
                    })

        if not overhead_rows:
            continue

        overhead_df = pd.DataFrame(overhead_rows)
        pivot = overhead_df.pivot_table(index="service", columns="load", values="overhead_pct")

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="RdYlGn_r", center=0, ax=ax)
        ax.set_title(f"{resource} Overhead (%) — Observed vs Baseline")
        ax.set_xlabel("Load Level")
        ax.set_ylabel("Service")
        plt.tight_layout()
        plt.savefig(Path(output_dir) / "figures" / fname, dpi=150)
        plt.close()


def generate_summary_table(df, metrics_df, output_dir):
    """Generate a comprehensive summary table as CSV."""
    rows = []

    for metric in ["p50", "p95", "p99", "mean", "count"]:
        for load in LOADS:
            b = df[(df["config"] == "baseline") & (df["load"] == load)][metric]
            o = df[(df["config"] == "observed") & (df["load"] == load)][metric]

            if len(b) == 0 or len(o) == 0:
                continue

            row = {
                "metric": metric,
                "load": load,
                "vus": VUS[load],
                "baseline_mean": round(b.mean(), 3),
                "baseline_std": round(b.std(), 3),
                "observed_mean": round(o.mean(), 3),
                "observed_std": round(o.std(), 3),
                "overhead_pct": round(((o.mean() - b.mean()) / b.mean() * 100), 2) if b.mean() != 0 else float('inf'),
                "n_baseline": len(b),
                "n_observed": len(o),
            }
            rows.append(row)

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(Path(output_dir) / "summary-table.csv", index=False)
    return summary_df


def load_mpstat_summary(results_dir):
    """Load mpstat-summary.csv with per-run CPU time-series statistics."""
    filepath = Path(results_dir) / "mpstat-summary.csv"
    if not filepath.exists():
        return None
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def load_dockerstats_summary(results_dir):
    """Load dockerstats-summary.csv with per-container CPU/memory time-series statistics."""
    filepath = Path(results_dir) / "dockerstats-summary.csv"
    if not filepath.exists():
        return None
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def generate_mpstat_table(mpstat_df, output_dir):
    """Generate mpstat summary table for the article."""
    if mpstat_df is None or mpstat_df.empty:
        return None

    rows = []
    for load in LOADS:
        for config in CONFIGS:
            subset = mpstat_df[(mpstat_df["config"] == config) & (mpstat_df["load"] == load)]
            if subset.empty:
                continue
            rows.append({
                "load": load,
                "vus": VUS[load],
                "config": config,
                "cpu_used_mean_pct": round(subset["cpu_used_mean"].mean(), 2),
                "cpu_used_std_pct": round(subset["cpu_used_mean"].std(), 2),
                "cpu_usr_mean_pct": round(subset["cpu_usr_mean"].mean(), 2),
                "cpu_sys_mean_pct": round(subset["cpu_sys_mean"].mean(), 2),
                "cpu_iowait_mean_pct": round(subset["cpu_iowait_mean"].mean(), 2),
                "cpu_used_min_pct": round(subset["cpu_used_min"].mean(), 2),
                "cpu_used_max_pct": round(subset["cpu_used_max"].mean(), 2),
                "n_reps": len(subset),
            })

    summary = pd.DataFrame(rows)
    summary.to_csv(Path(output_dir) / "mpstat-table.csv", index=False)
    return summary


def generate_dockerstats_table(dstats_df, output_dir):
    """Generate docker stats time-series summary table for the article."""
    if dstats_df is None or dstats_df.empty:
        return None

    rows = []
    for load in LOADS:
        for config in CONFIGS:
            for svc in SERVICES:
                svc_label = svc.replace("ts-", "").replace("-service", "")
                subset = dstats_df[
                    (dstats_df["config"] == config) &
                    (dstats_df["load"] == load) &
                    (dstats_df["service"] == svc)
                ]
                if subset.empty:
                    continue
                rows.append({
                    "load": load,
                    "vus": VUS[load],
                    "config": config,
                    "service": svc,
                    "service_label": svc_label,
                    "cpu_mean_pct": round(subset["cpu_mean"].mean(), 4),
                    "cpu_std_pct": round(subset["cpu_std"].mean(), 4),
                    "cpu_p50_pct": round(subset["cpu_p50"].mean(), 4),
                    "cpu_p95_pct": round(subset["cpu_p95"].mean(), 4),
                    "cpu_p99_pct": round(subset["cpu_p99"].mean(), 4),
                    "cpu_min_pct": round(subset["cpu_min"].mean(), 4),
                    "cpu_max_pct": round(subset["cpu_max"].mean(), 4),
                    "mem_mean_mib": round(subset["mem_mean"].mean(), 1),
                    "mem_std_mib": round(subset["mem_std"].mean(), 1),
                    "n_reps": len(subset),
                })

    summary = pd.DataFrame(rows)
    summary.to_csv(Path(output_dir) / "dockerstats-table.csv", index=False)
    return summary


def plot_mpstat_comparison(mpstat_df, output_dir):
    """Generate CPU utilization comparison plot from mpstat data."""
    if mpstat_df is None or mpstat_df.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax, metric, ylabel in zip(axes,
                                     ["cpu_used_mean", "cpu_usr_mean", "cpu_sys_mean"],
                                     ["Total CPU Used (%)", "User CPU (%)", "System CPU (%)"]):
        sns.boxplot(data=mpstat_df, x="load", y=metric, hue="config",
                    ax=ax, order=LOADS)
        ax.set_title(f"Host {ylabel} (mpstat)")
        ax.set_xlabel("Load Level")
        ax.set_ylabel(ylabel)

    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "mpstat_cpu_comparison.png", dpi=150)
    plt.close()


def plot_dockerstats_comparison(dstats_df, output_dir):
    """Generate per-container CPU comparison from docker stats time-series."""
    if dstats_df is None or dstats_df.empty:
        return

    svc_labels = {
        "ts-gateway-service": "Gateway",
        "ts-order-service": "Order",
        "ts-payment-service": "Payment",
        "ts-travel-service": "Travel",
    }

    fig, axes = plt.subplots(1, 4, figsize=(20, 5), sharey=True)

    for i, (svc, label) in enumerate(svc_labels.items()):
        ax = axes[i]
        subset = dstats_df[dstats_df["service"] == svc]
        if subset.empty:
            ax.set_title(f"{label} (no data)")
            continue

        sns.boxplot(data=subset, x="load", y="cpu_mean", hue="config",
                    ax=ax, order=LOADS)
        ax.set_title(f"{label} CPU (docker stats)")
        ax.set_xlabel("Load Level")
        ax.set_ylabel("CPU %")

    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "dockerstats_cpu_comparison.png", dpi=150)
    plt.close()


def run_analysis(results_dir, output_dir):
    """Run full statistical analysis pipeline."""
    print("=" * 60)
    print("  Observability Overhead Analysis")
    print("  Methodology: Jain (1991)")
    print("=" * 60)

    figures_dir = Path(output_dir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load k6 results
    print("\n[1/7] Loading k6 latency results...")
    df = load_k6_results(results_dir)
    if df.empty:
        print("ERROR: No k6 results found. Run experiments first.")
        sys.exit(1)
    print(f"  Loaded {len(df)} data points across {df['scenario'].nunique()} scenarios")

    # 2. Load CPU/memory metrics
    print("\n[2/7] Loading CPU/memory metrics...")
    metrics_df = load_metrics_csv(results_dir)
    if metrics_df is not None:
        print(f"  Loaded {len(metrics_df)} metric rows")
    else:
        print("  No metrics.csv found, skipping resource analysis")

    # 3. Normality tests
    print("\n[3/7] Running Shapiro-Wilk normality tests...")
    normality_results = []
    for metric in ["p50", "p95", "p99", "mean"]:
        df["scenario"] = df["config"] + "-" + df["load"]
        sw = shapiro_wilk_test(df, metric, "scenario")
        if not sw.empty:
            normality_results.append(sw)
        for load in LOADS:
            subset = df[df["load"] == load]
            sw2 = shapiro_wilk_test(subset, metric, "config")
            if not sw2.empty:
                normality_results.append(sw2)

    if normality_results:
        normality_df = pd.concat(normality_results, ignore_index=True).drop_duplicates()
        normality_df.to_csv(Path(output_dir) / "normality-tests.csv", index=False)
        print(f"  Normality tests: {len(normality_df)}")
        print(f"  Normal: {normality_df['normal'].sum()}/{len(normality_df)}")

    # 4. Hypothesis tests (baseline vs observed per load level)
    print("\n[4/7] Running hypothesis tests (baseline vs observed)...")
    hypothesis_results = []
    for metric in ["p50", "p95", "p99"]:
        for load in LOADS:
            b = df[(df["config"] == "baseline") & (df["load"] == load)][metric]
            o = df[(df["config"] == "observed") & (df["load"] == load)][metric]
            result = compare_two_groups(b, o, f"{metric}_{load}")
            if result:
                hypothesis_results.append(result)

    if hypothesis_results:
        hyp_df = pd.DataFrame(hypothesis_results)
        hyp_df.to_csv(Path(output_dir) / "hypothesis-tests.csv", index=False)
        print(f"  Hypothesis tests: {len(hyp_df)}")
        sig_count = hyp_df["significant"].sum()
        print(f"  Significant (p < {ALPHA}): {sig_count}/{len(hyp_df)}")

    # 5. ANOVA across load levels
    print("\n[5/7] Running ANOVA/Kruskal-Wallis across load levels...")
    anova_results = []
    for metric in ["p50", "p95", "p99"]:
        result = anova_or_kruskal(df, metric, "load")
        if result:
            anova_results.append(result)

    if anova_results:
        anova_df = pd.DataFrame(anova_results)
        anova_df.to_csv(Path(output_dir) / "anova-table.csv", index=False)
        print(f"  ANOVA/Kruskal-Wallis results: {len(anova_df)}")

    # 7. Summary table
    print("\n[6/8] Generating summary table...")
    summary_df = generate_summary_table(df, metrics_df, output_dir)
    print(f"  Summary table: {len(summary_df)} rows")

    # 7.5. Load and analyze mpstat data
    print("\n[6.5/8] Loading mpstat CPU time-series data...")
    mpstat_df = load_mpstat_summary(results_dir)
    if mpstat_df is not None and not mpstat_df.empty:
        print(f"  Loaded {len(mpstat_df)} mpstat rows")
        mpstat_summary = generate_mpstat_table(mpstat_df, output_dir)
        if mpstat_summary is not None:
            print(f"  Saved: mpstat-table.csv")
            print(f"  mpstat summary:")
            for _, row in mpstat_summary.iterrows():
                print(f"    {row['config']}-{row['load']}: "
                      f"CPU used {row['cpu_used_mean_pct']:.2f}% "
                      f"(+/- {row['cpu_used_std_pct']:.2f}%)")
    else:
        print("  No mpstat-summary.csv found, skipping mpstat analysis")

    # 7.6. Load and analyze docker stats time-series data
    print("\n[6.6/8] Loading docker stats time-series data...")
    dstats_df = load_dockerstats_summary(results_dir)
    if dstats_df is not None and not dstats_df.empty:
        print(f"  Loaded {len(dstats_df)} docker stats rows")
        dstats_summary = generate_dockerstats_table(dstats_df, output_dir)
        if dstats_summary is not None:
            print(f"  Saved: dockerstats-table.csv")
            print(f"  docker stats summary (CPU mean per service per scenario):")
            for _, row in dstats_summary.iterrows():
                print(f"    {row['config']}-{row['load']} {row['service']}: "
                      f"CPU {row['cpu_mean_pct']:.4f}% +/- {row['cpu_std_pct']:.4f}% "
                      f"(p50={row['cpu_p50_pct']:.4f}%, p99={row['cpu_p99_pct']:.4f}%)")
    else:
        print("  No dockerstats-summary.csv found, skipping docker stats analysis")

    # 7. Load detailed k6 cache for advanced analyses
    print("\n[7/10] Loading detailed k6 metrics for advanced analysis...")
    k6_cache = load_all_k6_detailed(results_dir)
    print(f"  Loaded detailed metrics for {len(k6_cache)} runs")

    # 8. Generate plots
    print("\n[8/10] Generating plots...")
    try:
        plot_latency_comparison(df, output_dir)
        print("  Saved: latency_comparison.png")
        plot_latency_per_load(df, output_dir)
        print("  Saved: latency_per_load.png")
        plot_throughput_comparison(df, output_dir)
        print("  Saved: throughput_comparison.png")
        plot_overhead_percentage(df, output_dir)
        print("  Saved: overhead_percentage.png")

        if metrics_df is not None:
            plot_resource_comparison(metrics_df, output_dir)
            print("  Saved: cpu_comparison.png, memory_comparison.png")
            plot_resource_heatmap(metrics_df, output_dir)
            print("  Saved: cpu_overhead_heatmap.png, memory_overhead_heatmap.png")

        if mpstat_df is not None and not mpstat_df.empty:
            plot_mpstat_comparison(mpstat_df, output_dir)
            print("  Saved: mpstat_cpu_comparison.png")

        if dstats_df is not None and not dstats_df.empty:
            plot_dockerstats_comparison(dstats_df, output_dir)
            print("  Saved: dockerstats_cpu_comparison.png")
    except Exception as e:
        print(f"  Warning: some plots failed: {e}")

    # 9. Latency breakdown analysis
    print("\n[9/10] Analyzing latency breakdown (waiting/sending/receiving)...")
    breakdown_df = analyze_latency_breakdown(k6_cache, output_dir)
    if not breakdown_df.empty:
        print(f"  Saved: latency-breakdown.csv, latency_breakdown.png, latency_breakdown_p99.png")

    # 10. Tail latency analysis
    print("\n[10/10] Analyzing tail latency distribution...")
    tail_df = analyze_tail_latency(k6_cache, output_dir)
    if not tail_df.empty:
        print(f"  Saved: tail-latency.csv, tail_latency plots")

    # Per-rep variance
    variance_df = analyze_per_rep_variance(k6_cache, output_dir)
    if not variance_df.empty:
        print(f"  Saved: per-rep-variance.csv, per_rep_variance.png")

    # Print summary
    print("\n" + "=" * 60)
    print("  Analysis Complete")
    print("=" * 60)
    print(f"  Results saved to: {output_dir}/")
    print(f"  - normality-tests.csv")
    print(f"  - hypothesis-tests.csv")
    print(f"  - anova-table.csv")
    print(f"  - summary-table.csv")
    print(f"  - latency-breakdown.csv")
    print(f"  - tail-latency.csv")
    print(f"  - per-rep-variance.csv")
    print(f"  - figures/")

    if hypothesis_results:
        print("\n  Key findings:")
        for r in hypothesis_results:
            sig = "SIGNIFICANT" if r["significant"] else "not significant"
            print(f"    {r['metric']}: overhead={r['overhead_pct']}% ({sig}, {r['test']})")


def analyze_latency_breakdown(k6_cache, output_dir):
    """Analyze latency breakdown: waiting (server), sending, receiving."""
    phase_map = {
        "http_req_waiting": "waiting",
        "http_req_sending": "sending",
        "http_req_receiving": "receiving",
        "http_req_connecting": "connecting",
    }
    rows = []

    for (config, load, rep), metrics in sorted(k6_cache.items()):
        row = {"config": config, "load": load, "rep": rep, "vus": VUS[load]}
        for k6_metric, phase_name in phase_map.items():
            values = metrics.get(k6_metric)
            if values:
                arr = np.array(values)
                row[f"{phase_name}_p50"] = np.percentile(arr, 50)
                row[f"{phase_name}_p95"] = np.percentile(arr, 95)
                row[f"{phase_name}_p99"] = np.percentile(arr, 99)
                row[f"{phase_name}_mean"] = np.mean(arr)
            else:
                row[f"{phase_name}_p50"] = np.nan
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(Path(output_dir) / "latency-breakdown.csv", index=False)

    if df.empty:
        return df

    phases = [("waiting_p50", "Server Processing (waiting)"), ("sending_p50", "Sending"), ("receiving_p50", "Receiving")]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (col, label) in zip(axes, phases):
        if col in df.columns:
            sns.boxplot(data=df, x="load", y=col, hue="config", ax=ax, order=LOADS)
            ax.set_title(f"p50 Latency — {label}")
            ax.set_xlabel("Load Level")
            ax.set_ylabel("Latency (ms)")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "latency_breakdown.png", dpi=150)
    plt.close()

    phases_p99 = [("waiting_p99", "Server Processing (waiting)"), ("sending_p99", "Sending"), ("receiving_p99", "Receiving")]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (col, label) in zip(axes, phases_p99):
        if col in df.columns:
            sns.boxplot(data=df, x="load", y=col, hue="config", ax=ax, order=LOADS)
            ax.set_title(f"p99 Latency — {label}")
            ax.set_xlabel("Load Level")
            ax.set_ylabel("Latency (ms)")
    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "latency_breakdown_p99.png", dpi=150)
    plt.close()

    return df


def analyze_tail_latency(k6_cache, output_dir):
    """Analyze tail latency: distribution of long-running requests."""
    rows = []

    for (config, load, rep), metrics in sorted(k6_cache.items()):
        durations = metrics.get("http_req_duration")
        if not durations:
            continue

        arr = np.array(durations)
        rows.append({
            "config": config,
            "load": load,
            "rep": rep,
            "vus": VUS[load],
            "count": len(arr),
            "p50": np.percentile(arr, 50),
            "p90": np.percentile(arr, 90),
            "p95": np.percentile(arr, 95),
            "p99": np.percentile(arr, 99),
            "mean": np.mean(arr),
            "std": np.std(arr),
            "max": np.max(arr),
            "pct_over_20ms": float((arr > 20).sum() / len(arr) * 100),
            "pct_over_50ms": float((arr > 50).sum() / len(arr) * 100),
            "pct_over_100ms": float((arr > 100).sum() / len(arr) * 100),
        })

    df = pd.DataFrame(rows)
    df.to_csv(Path(output_dir) / "tail-latency.csv", index=False)

    if df.empty:
        return df

    for threshold, label in [(20, "20"), (50, "50"), (100, "100")]:
        fig, ax = plt.subplots(figsize=(8, 5))
        col = f"pct_over_{threshold}ms"
        if col in df.columns:
            sns.barplot(data=df, x="load", y=col, hue="config", ax=ax, order=LOADS)
            ax.set_title(f"% Requests > {threshold}ms by Load Level")
            ax.set_xlabel("Load Level")
            ax.set_ylabel(f"% Requests > {threshold}ms")
        plt.tight_layout()
        plt.savefig(Path(output_dir) / "figures" / f"tail_latency_pct_over_{threshold}ms.png", dpi=150)
        plt.close()

    return df


def analyze_per_rep_variance(k6_cache, output_dir):
    """Analyze per-rep variance to identify stability of measurements."""
    rows = []

    for (config, load, rep), metrics in sorted(k6_cache.items()):
        durations = metrics.get("http_req_duration")
        if not durations:
            continue

        arr = np.array(durations)
        rows.append({
            "config": config,
            "load": load,
            "rep": rep,
            "vus": VUS[load],
            "count": len(arr),
            "p50": np.percentile(arr, 50),
            "p95": np.percentile(arr, 95),
            "p99": np.percentile(arr, 99),
            "mean": np.mean(arr),
            "std": np.std(arr),
        })

    df = pd.DataFrame(rows)
    df.to_csv(Path(output_dir) / "per-rep-variance.csv", index=False)

    if df.empty:
        return df

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    for col_idx, metric in enumerate(["p50", "p99"]):
        for row_idx, load in enumerate(LOADS):
            ax = axes[col_idx][row_idx]
            subset = df[df["load"] == load]
            for c, marker in [("baseline", "o"), ("observed", "s")]:
                cdata = subset[subset["config"] == c]
                ax.plot(cdata["rep"], cdata[metric], marker=marker, label=c)
            ax.set_title(f"{metric} — {load} load ({VUS[load]} VUs)")
            ax.set_xlabel("Repetition")
            ax.set_ylabel(f"{metric} latency (ms)")
            ax.legend()

    plt.tight_layout()
    plt.savefig(Path(output_dir) / "figures" / "per_rep_variance.png", dpi=150)
    plt.close()

    return df


def main():
    parser = argparse.ArgumentParser(description="Statistical analysis of observability overhead experiments")
    parser.add_argument("--results-dir", default="results", help="Directory with experiment results (default: results)")
    parser.add_argument("--output-dir", default=None, help="Directory for analysis output (default: same as results-dir)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    results_dir = project_dir / args.results_dir
    output_dir = project_dir / (args.output_dir if args.output_dir else args.results_dir)

    run_analysis(str(results_dir), str(output_dir))


if __name__ == "__main__":
    main()