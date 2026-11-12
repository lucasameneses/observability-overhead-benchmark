#!/bin/bash
# run-experiments.sh — Automate 30 repetitions × 6 scenarios (2 configs × 3 loads)
# Usage: bash scripts/run-experiments.sh [--dry-run] [--force]
#
# Features:
#   - Progress bar with ETA
#   - Skip completed runs (checks if JSON output exists)
#   - Resume from where it left off after failures
#   - Collects CPU/memory metrics per service
#
# Scenarios:
#   baseline-low     (no observability, 10 VUs)
#   baseline-medium  (no observability, 50 VUs)
#   baseline-high    (no observability, 100 VUs)
#   observed-low     (with observability, 10 VUs)
#   observed-medium  (with observability, 50 VUs)
#   observed-high    (with observability, 100 VUs)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${PROJECT_DIR}/results"

REPS=30
BASE_URL="http://localhost:18888"
DRY_RUN=false
FORCE=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --force) FORCE=true ;;
    esac
done

mkdir -p "${RESULTS_DIR}"

CONFIGS=("baseline" "observed")
LOADS=("low" "medium" "high")
K6_SCRIPTS=("load/load-low.js" "load/load-medium.js" "load/load-high.js")
K6_VUS=("10" "50" "100")

COMPOSE_BASELINE="${PROJECT_DIR}/docker-compose.baseline.yml"
COMPOSE_OBSERVED="${PROJECT_DIR}/docker-compose.yml"

TOTAL_RUNS=$(( ${#CONFIGS[@]} * ${#LOADS[@]} * REPS ))

# The paper's runs used a local k6. Without one, fall back to the k6 image on
# the host network, so the load still reaches the gateway through localhost.
K6_IMAGE="grafana/k6:0.54.0"
run_k6() {
    local output_file="$1" k6_script="$2"
    if command -v k6 > /dev/null; then
        k6 run --out "json=${output_file}" --env "BASE_URL=${BASE_URL}" "${PROJECT_DIR}/${k6_script}"
    else
        docker run --rm --network host -u "$(id -u)" \
            -v "${PROJECT_DIR}:/work" -w /work "${K6_IMAGE}" \
            run --out "json=/work/${output_file#"${PROJECT_DIR}/"}" --env "BASE_URL=${BASE_URL}" "/work/${k6_script}"
    fi
}

progress_bar() {
    local current=$1
    local total=$2
    local start_time=$3
    local width=40
    
    local pct=$(( current * 100 / total ))
    local filled=$(( current * width / total ))
    local empty=$(( width - filled ))
    
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="#"; done
    for ((i=0; i<empty; i++)); do bar+="-"; done
    
    local elapsed=$(($(date +%s) - start_time))
    local remaining=0
    if [[ $current -gt 0 ]]; then
        remaining=$(( elapsed * (total - current) / current ))
    fi
    local eta_h=$(( remaining / 3600 ))
    local eta_min=$(( (remaining % 3600) / 60 ))
    
    if [[ $eta_h -gt 0 ]]; then
        printf "\r  [%s] %3d%% (%d/%d) ETA: %dh%02dm" "$bar" "$pct" "$current" "$total" "$eta_h" "$eta_min"
    else
        printf "\r  [%s] %3d%% (%d/%d) ETA: %dm" "$bar" "$pct" "$current" "$total" "$eta_min"
    fi
}

wait_for_healthy() {
    local url="$1"
    local max_wait=180
    local elapsed=0
    while ! curl -sf "${url}" > /dev/null 2>&1; do
        sleep 5
        elapsed=$((elapsed + 5))
        if [[ $elapsed -ge $max_wait ]]; then
            echo "FAILED (${max_wait}s)"
            return 1
        fi
    done
    echo "OK (${elapsed}s)"
}

collect_metrics() {
    local scenario="$1"
    local rep="$2"
    local vus="$3"
    local metrics_line="${scenario},${rep},${vus}"
    
    for svc in ts-gateway-service ts-order-service ts-payment-service ts-travel-service; do
        local cpu_mem
        cpu_mem=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "${svc}" 2>/dev/null || echo "N/A,N/A")
        local cpu mem
        cpu=$(echo "$cpu_mem" | cut -d',' -f1 | tr -d '%')
        mem=$(echo "$cpu_mem" | cut -d',' -f2 | cut -d'/' -f1 | tr -d ' ')
        metrics_line="${metrics_line},${cpu},${mem}"
    done
    
    echo "$metrics_line" >> "${RESULTS_DIR}/metrics.csv"
}

# --- Docker stats time-series collection (0.5s interval) ---
# Collects per-container CPU/memory every 0.5s during k6 execution.
# Produces per-run CSV files for statistical analysis.

start_docker_stats_collection() {
    local scenario="$1"
    local rep="$2"
    local output_file="${RESULTS_DIR}/dockerstats_${scenario}_rep$(printf '%02d' $rep).csv"
    
    echo "timestamp,container,cpu_pct,mem_usage,mem_limit,mem_pct,net_io,block_io" > "${output_file}"
    
    while true; do
        local ts
        ts=$(date +%s%3N 2>/dev/null || date +%s)
        for svc in ts-gateway-service ts-order-service ts-payment-service ts-travel-service; do
            local line
            line=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}" "${svc}" 2>/dev/null || echo "N/A,N/A,N/A,N/A,N/A")
            local cpu mem_used mem_limit mem_pct net block
            cpu=$(echo "$line" | cut -d',' -f1 | tr -d '% ' )
            local mem_full
            mem_full=$(echo "$line" | cut -d',' -f2)
            mem_pct=$(echo "$line" | cut -d',' -f3 | tr -d '% ')
            net=$(echo "$line" | cut -d',' -f4)
            block=$(echo "$line" | cut -d',' -f5)
            mem_used=$(echo "$mem_full" | cut -d'/' -f1 | tr -d ' ')
            mem_limit=$(echo "$mem_full" | cut -d'/' -f2 | tr -d ' ')
            echo "${ts},${svc},${cpu},${mem_used},${mem_limit},${mem_pct},${net},${block}" >> "${output_file}"
        done
        sleep 0.5
    done &
    DOCKER_STATS_PID=$!
}

stop_docker_stats_collection() {
    if [[ -n "${DOCKER_STATS_PID:-}" ]] && kill -0 "${DOCKER_STATS_PID}" 2>/dev/null; then
        kill "${DOCKER_STATS_PID}" 2>/dev/null || true
        wait "${DOCKER_STATS_PID}" 2>/dev/null || true
    fi
}

# --- mpstat host-level CPU collection (1s interval) ---
# mpstat minimum interval is 1s. Used for host-level CPU utilization.

start_mpstat() {
    local scenario="$1"
    local rep="$2"
    local mpstat_file="${RESULTS_DIR}/mpstat_${scenario}_rep$(printf '%02d' $rep).csv"
    mpstat -P ALL 1 > "${mpstat_file}" &
    MPSTAT_PID=$!
}

stop_mpstat() {
    if [[ -n "${MPSTAT_PID:-}" ]] && kill -0 "${MPSTAT_PID}" 2>/dev/null; then
        kill "${MPSTAT_PID}" 2>/dev/null || true
        wait "${MPSTAT_PID}" 2>/dev/null || true
    fi
}

process_mpstat() {
    local scenario="$1"
    local rep="$2"
    local mpstat_file="${RESULTS_DIR}/mpstat_${scenario}_rep$(printf '%02d' $rep).csv"
    
    if [[ ! -f "${mpstat_file}" ]]; then
        return
    fi
    
    python3 "${SCRIPT_DIR}/process_mpstat.py" "${mpstat_file}" "${scenario}" "${rep}"
}

process_docker_stats() {
    local scenario="$1"
    local rep="$2"
    local dstats_file="${RESULTS_DIR}/dockerstats_${scenario}_rep$(printf '%02d' $rep).csv"
    
    if [[ ! -f "${dstats_file}" ]]; then
        return
    fi
    
    python3 "${SCRIPT_DIR}/process_docker_stats.py" "${dstats_file}" "${scenario}" "${rep}"
}

# Dry run mode
if $DRY_RUN; then
    echo "=== DRY RUN MODE ==="
    echo "Would run ${TOTAL_RUNS} experiments"
    echo ""
    current=0
    for config in "${CONFIGS[@]}"; do
        compose_file=$( [[ "$config" == "baseline" ]] && echo "$COMPOSE_BASELINE" || echo "$COMPOSE_OBSERVED" )
        for load_idx in "${!LOADS[@]}"; do
            load="${LOADS[$load_idx]}"
            k6_script="${K6_SCRIPTS[$load_idx]}"
            vus="${K6_VUS[$load_idx]}"
            scenario="${config}-${load}"
            for rep in $(seq 1 "$REPS"); do
                current=$((current + 1))
                echo "[${current}/${TOTAL_RUNS}] ${scenario} rep ${rep}/${REPS} (VUs: ${vus})"
                echo "  docker compose -f ${compose_file} up -d --build"
                echo "  k6 run --out json=${RESULTS_DIR}/${scenario}_rep$(printf '%02d' $rep).json ${k6_script}"
                echo "  docker compose -f ${compose_file} down -v"
            done
        done
    done
    exit 0
fi

START_TIME=$(date +%s)

echo "============================================"
echo "  Experiment Runner — 30 reps × 6 scenarios"
echo "  Total runs: ${TOTAL_RUNS}"
echo "  Estimated time: ~21 hours"
echo "  Resume: skips completed runs automatically"
echo "  Use --force to redo completed runs"
echo "============================================"

# Initialize metrics CSV if needed
if [[ ! -f "${RESULTS_DIR}/metrics.csv" ]] || $FORCE; then
    echo "scenario,rep,vus,cpu_gateway,mem_gateway,cpu_order,mem_order,cpu_payment,mem_payment,cpu_travel,mem_travel" > "${RESULTS_DIR}/metrics.csv"
fi

current=0
passed=0
failed=0
skipped=0

for config in "${CONFIGS[@]}"; do
    if [[ "$config" == "baseline" ]]; then
        compose_file="$COMPOSE_BASELINE"
    else
        compose_file="$COMPOSE_OBSERVED"
    fi

    for load_idx in "${!LOADS[@]}"; do
        load="${LOADS[$load_idx]}"
        k6_script="${K6_SCRIPTS[$load_idx]}"
        vus="${K6_VUS[$load_idx]}"
        scenario="${config}-${load}"

        for rep in $(seq 1 "$REPS"); do
            current=$((current + 1))
            rep_padded=$(printf "%02d" "$rep")
            output_file="${RESULTS_DIR}/${scenario}_rep${rep_padded}.json"

            # Skip if already completed
            if [[ -f "$output_file" ]] && ! $FORCE; then
                skipped=$((skipped + 1))
                progress_bar $current $TOTAL_RUNS $START_TIME
                continue
            fi

            echo ""
            echo "=== [${current}/${TOTAL_RUNS}] ${scenario} rep ${rep}/${REPS} (VUs: ${vus}) ==="

            # Clean up
            echo -n "  Stopping previous env... "
            docker compose -f "${compose_file}" down -v --remove-orphans 2>/dev/null || true
            echo "done"

            # Start environment
            echo -n "  Starting ${config} env... "
            docker compose -f "${compose_file}" up -d --build 2>&1 | tail -1

            echo -n "  Health check: "
            sleep 10
            if ! wait_for_healthy "${BASE_URL}/api/v1/orderservice/welcome"; then
                echo "  FAILED: services not healthy, skipping rep"
                docker compose -f "${compose_file}" down -v 2>/dev/null || true
                failed=$((failed + 1))
                progress_bar $current $TOTAL_RUNS $START_TIME
                continue
            fi

            echo -n "  Waiting for all services... "
            sleep 5
            echo "done"

            # Warm-up
            echo -n "  Warm-up (30s)... "
            for i in $(seq 1 30); do
                curl -sf "${BASE_URL}/api/v1/orderservice/order" > /dev/null 2>&1 || true
                sleep 1
            done
            echo "done"

            # Start mpstat (host-level, 1s) and docker stats (per-container, 0.5s)
            echo -n "  Starting resource collection... "
            start_mpstat "$scenario" "$rep"
            start_docker_stats_collection "$scenario" "$rep"
            echo "done"

            # Run k6
            echo -n "  Running k6 (${load}, 5m30s)... "
            if run_k6 "${output_file}" "${k6_script}" > /dev/null 2>&1; then
                echo "OK"
                passed=$((passed + 1))
            else
                echo "FAILED"
                failed=$((failed + 1))
            fi

            # Stop resource collection
            echo -n "  Stopping resource collection... "
            stop_mpstat
            stop_docker_stats_collection
            echo "done"

            # Process mpstat and docker stats data
            echo -n "  Processing mpstat data... "
            process_mpstat "$scenario" "$rep"
            echo -n "  Processing docker stats data... "
            process_docker_stats "$scenario" "$rep"
            echo "done"

            # Collect final snapshot metrics
            echo -n "  Collecting metrics... "
            collect_metrics "$scenario" "$rep" "$vus"
            echo "done"

            # Stop environment
            echo -n "  Stopping env... "
            docker compose -f "${compose_file}" down -v 2>&1 | tail -1
            echo "done"

            progress_bar $current $TOTAL_RUNS $START_TIME
        done
    done
done

ELAPSED=$(($(date +%s) - START_TIME))
ELAPSED_H=$((ELAPSED / 3600))
ELAPSED_MIN=$(( (ELAPSED % 3600) / 60 ))

echo ""
echo ""
echo "============================================"
echo "  Experiments Complete!"
echo "  Time: ${ELAPSED_H}h${ELAPSED_MIN}m"
echo "  Passed: ${passed}, Failed: ${failed}, Skipped: ${skipped}"
echo "  Results in: ${RESULTS_DIR}/"
echo ""
echo "  Run analysis:"
echo "    python3 scripts/analyze.py"
echo "============================================"