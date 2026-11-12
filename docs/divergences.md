# Divergences

What the delivered paper said that the experiment data or the code did not support, and how the
revised [`paper.pdf`](paper.pdf) now says it. The text was changed to match the evidence, never the
other way round. Claim ids (Qnn) point to the [credibility checklist](credibility-checklist.md).

The evidence is the aggregated data in [`results/`](../results/) and the code in this repository.
The raw k6 files of the 180 runs were deleted after the analysis (about 0.1 to 1 GB each), so
nothing below was re-measured: every number was recomputed from the CSVs.

## Numbers

### D01 — p95 overhead at 50 VUs (Q21)

- **Delivered**: "+8,9%" (latency table and hypothesis table).
- **Data**: `summary-table.csv` gives 8.82 %.
- **Revised**: 8,8 %.

### D02 — growth of requests above 20 ms (Q32)

- **Delivered**: "3,0% [...] contra apenas 0,7% no baseline -- um aumento de 4×".
- **Data**: `tail-latency.csv` gives 3.008 % vs 0.655 %, a ratio of 4.6.
- **Revised**: "um aumento de cerca de 4,6×".

### D03 — CPU and memory tables mixed two batches (Q38–Q40, Q49)

- **Delivered**: the tables say "Média de 30 repetições", but for observed-low and
  observed-medium they average 60 rows. `metrics.csv` holds two batches of 30 for those two
  scenarios, because `run-experiments.sh` appends to the file and those scenarios were run twice.
- **Data**: the two batches disagree, mostly in memory at 50 VUs (older batch 1349–1427 MiB, newer
  batch 1552–1644 MiB). The newer batch sits right before observed-high in the file, so it belongs
  to the same run as the k6 files behind the latency results.
- **Revised**: the tables use the newer batch. The 50 VUs memory overhead changes from
  "−3 % a +1 %" to +5.5 % to +7.0 %, so the paragraph about the GC recovering memory at medium load
  was removed. `analyze.py` now keeps the newest 30 rows per scenario, and the resource figures
  in `results/figures/` were regenerated.

| Observed, newest batch | GW | Order | Pay | Travel |
|---|---|---|---|---|
| CPU 10 VUs (%) | 0.30 | 0.35 | 0.33 | 0.38 |
| CPU 50 VUs (%) | 0.46 | 0.33 | 0.58 | 0.38 |
| Memory 10 VUs (MiB) | 1507 | 1591 | 1589 | 1410 |
| Memory 50 VUs (MiB) | 1552 | 1644 | 1634 | 1623 |

## CPU

### D04 — "consistently higher", "below 1 % without spikes", "statistically significant" (Q41, Q60, Q61)

- **Delivered**: CPU with instrumentation is "consistentemente superior ao baseline"; CPU stays
  "consistentemente abaixo de 1% em todos os cenários, sem picos significativos", so one sample
  per run is representative; the CPU overhead is "estatisticamente significativo".
- **Data**: no CPU test had been run. A Mann-Whitney U per cell (newest batch) is significant for
  all four services at 100 VUs, but only for the order service at 10 VUs and only for the payment
  service at 50 VUs. 25 of the 720 samples exceed 1 % of a core, up to 4.75 %.
- **Revised**: mean CPU is higher in every cell but low and spike-sensitive; the test result per
  load is stated; a single sample per run is listed as a limitation and the CPU results are
  called indicative.

## Memory

### D05 — "fixed cost amortized under load" and "5–7 %" (Q48, Q58)

- **Delivered**: the instrumentation memory is a fixed cost "amortizado sob carga moderada e
  alta"; elsewhere the high-load overhead is "5--7%".
- **Data**: the overhead grows with load: 4.6–5.4 % at 10 VUs (travel excluded), 5.5–7.0 % at
  50 VUs, 6.2–6.8 % at 100 VUs, significant in every cell (Mann-Whitney U, p < 0.001).
- **Revised**: those ranges, with no amortization claim; "6--7%" in the practical implications.

### D06 — "heap" vs container memory, and the travel service (Q08, Q15, Q47)

- **Delivered**: memory is called "memória heap da JVM" and explained by a smaller initial heap
  in the travel service.
- **Code**: memory comes from `docker stats`, which reports container memory. Every service starts
  with a fixed 2 GB heap (`-Xms2g -Xmx2g`), so no service has a smaller initial heap.
- **Revised**: "memória do contêiner" throughout (unit MiB); the travel-service difference at
  10 VUs (853–1011 MiB per run) is reported without a cause.

## Latency interpretation

### D07 — "overhead grows under resource contention" (Q06, Q14, Q24, Q65, Q30)

- **Delivered**: abstract, methodology, results and conclusion say the overhead at 100 VUs grows
  "sob contenção de recursos" and that the instrumentation "amplifica a contenção"; 100 VUs is
  described as close to saturation; the high-load overhead is "dominado por outliers".
- **Data**: the baseline shows no saturation at 100 VUs. Throughput is linear in the VU count
  (88.5 : 444.8 : 900.3 req/s), baseline latency falls (p50 6.34 to 4.78 ms) and mean CPU stays
  under 1 % of a core. The p50 rise at 100 VUs (+23.1 %) is +1.10 ms, partly a lower baseline;
  8 of the 30 observed runs, the first eight in order, have a p50 of 4.82–5.14 ms, close to the
  baseline (see `results/figures/per_rep_variance.png`). p95 and p99 rise in absolute terms too
  (+6.2 and +10.2 ms) while the baseline falls.
- **Revised**: the overhead percentage is the largest at 100 VUs, given with absolute ms; the
  bimodal p50 is reported; the baseline shows no saturation; the mechanism was not isolated. The
  high-load overhead is described as a shift of the median plus a wider tail.

### D08 — p95 inflated by requests above 20 ms (Q33)

- **Delivered**: the share of requests above 20 ms "inflaciona significativamente os percentis p95
  e p99".
- **Data**: observed p95 at 100 VUs is 17.2 ms, below 20 ms.
- **Revised**: the 20 ms share affects p99; the p95 rise is a shift of the body of the distribution.

### D09 — overhead "integralmente" in the server, "dentro da JVM" (Q35, Q37, Q66)

- **Delivered**: the latency breakdown shows the overhead is "integralmente atribuível ao
  processamento no servidor" and is the "custo computacional da instrumentação dentro da JVM".
- **Data**: 96–99 % of the p50 increase is in k6's `waiting` phase, which covers everything after
  the request leaves the client: the four services, the internal network hops and host contention
  from the observability containers on the same machine.
- **Revised**: 96–99 % of the increase is in the client's waiting time, which rules out the
  client–gateway transfer and nothing more. The table caption was changed the same way.

### D10 — "uniform" overhead and "fixed cost" at low load (Q50, Q64)

- **Delivered**: at 10 VUs the overhead is "relativamente uniforme entre percentis", "consistente
  com o custo fixo da instrumentação".
- **Data**: p99 overhead (16.9 %) is twice the p50 overhead (8.4 %), and one load level cannot
  separate fixed from variable cost.
- **Revised**: the likely sources (agent, Micrometer, Promtail) are listed without the "uniform" or
  "fixed cost" conclusions.

## Throughput

### D11 — "throughput is not significantly affected" (Q54, Q29)

- **Delivered**: throughput "é preservado" and "não é significativamente afetado".
- **Data**: the loss is small (0.6 %, 0.4 %, 1.8 %) but significant at every load (Mann-Whitney U
  on requests per run, p < 0.001). With a closed loop and 100 ms think time, it follows from the
  latency increase: the predicted loss at 100 VUs is 1.77 %, the measured one 1.75 %.
- **Revised**: small but statistically detectable, a consequence of the latency increase; the
  experiment does not measure maximum capacity.

## Setup facts

### D12 — what the paper said about the environment (Q11, Q22, plus code checks)

| Delivered | Code | Revised |
|---|---|---|
| "JDK 17 com heap máxima de 2 GB" | Dockerfiles use `eclipse-temurin:21` and `-Xms2g -Xmx2g` | JDK 21, fixed 2 GB heap |
| "limite de CPU dos contêineres em 2 vCPUs"; CPU as "percentual do limite alocado" | No CPU limit in either compose file; `docker stats` reports % of one core | No CPU limit; CPU in % of one host core |
| "teste t de Welch" | `analyze.py` calls `scipy.stats.ttest_ind` with the default `equal_var=True` | Student t-test |
| A 30 s warm-up "period" before k6 | 30 single requests, one per second; k6's 30 s ramp is inside the measured window | Both stated |
| "com intervalo de confiança de 95%"; "poder estatístico adequado" | No interval and no power analysis in the outputs | "testes estatísticos a 95 % de confiança"; no power claim |

### D13 — span-processing explanation for CPU (Q43)

- **Delivered**: order and payment have higher CPU overhead because they "processam spans de
  tracing propagados pela cadeia".
- **Data**: no per-component CPU data exists.
- **Revised**: stated as a hypothesis that needs per-component measurement.

## Not changed

- Literature figures (Yang et al. 5–15 % and 6.15×, TrainTicket's 41 services) were not checked
  against the sources here.
- Hardware and OS described in the paper (Intel Core i5-12450H, 16 GB, Ubuntu 24.04) are as
  reported by the authors.
- The Kruskal-Wallis table in `results/anova-table.csv` pools both configurations, so it tests
  the load effect on raw latency, not on the overhead. The paper never cited it, and it was left
  out of the revision.
