# Credibility checklist

Every quantitative or checkable claim of the delivered paper, checked on 2026-11-12 against the
aggregated results in [`results/`](../results/) and the code in this repository.

How to read it:
- Claims are quoted in Portuguese, as in the delivered version; line numbers refer to its LaTeX
  source.
- **Status**:
  - `confirmed`: the data support it;
  - `corrected`: the data or the code did not support it, and the revised [`paper.pdf`](paper.pdf)
    now says what was observed. The id in brackets points to [`divergences.md`](divergences.md);
  - `not checkable`: nothing in the CSVs or the code bears on it (external facts, hardware,
    mechanisms that were not measured).
- The raw k6 files were deleted after the analysis, so every check recomputes from the CSVs:
  `summary-table.csv`, `hypothesis-tests.csv`, `normality-tests.csv`, `per-rep-variance.csv`,
  `tail-latency.csv`, `latency-breakdown.csv` and `metrics.csv`.
- Recomputations in the evidence column use Mann-Whitney U and Welch t from the per-run values;
  CPU and memory means use all rows of `metrics.csv` unless a batch is named.

Totals: 23 confirmed, 32 corrected, 11 not checkable.

## Abstract / Resumo (L33-75)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q01 | Resumo L64-65; Abstract L40-42 | "30 repetições por combinação ... totalizando 180 execuções" | confirmed | summary-table: n_baseline = n_observed = 30 in every cell. per-rep-variance, tail-latency and latency-breakdown each have 180 rows (30 × 6). Exception: metrics.csv has 240 rows (see Q40). |
| Q02 | Resumo L66-68; Abstract L42-44 | "testes de normalidade Shapiro-Wilk seguidos de testes t ou Mann-Whitney U" | confirmed | The test choice is consistent with normality-tests.csv. MW is used exactly where an observed sample is non-normal (p50 medium: SW p = 0.0018; p50 high: SW p = 1.6e-5). The t-test is used where all samples are normal. |
| Q03 | Resumo L69-70; Abstract L45-46 | "estatisticamente significativo em todos os níveis de carga ($p < 0{,}001$)" | confirmed | hypothesis-tests.csv: the largest p is 7.1e-9 (p50 medium). All 9 tests have significant = True. |
| Q04 | Resumo L70-71; Abstract L46-47 | "8{,}4\% em p50/carga baixa, 6{,}1\% em p50/carga média e 23{,}1\% em p50/carga alta" | confirmed | CSV gives 8.45 / 6.12 / 23.09. Recomputed from the means: 8.44 / 6.12 / 23.08. |
| Q05 | Resumo L71-72; Abstract L47-48 | "A latência de cauda (p99) cresce de 16{,}9\% em carga baixa para 58{,}5\% em carga alta" | confirmed | CSV gives 16.86 / 58.52. The trend is not monotonic: the medium-load value is 10.12 and is omitted here. |
| Q06 | Resumo L73-74; Abstract L48-49 | "confirmando que o overhead cresce de forma desproporcional sob contenção de recursos" | corrected (D07) | The CSVs show no contention at 100 VUs. Baseline throughput scales ~linearly (88.5 : 444.8 : 900.3 req/s = 1 : 5.03 : 10.17). Baseline p50 falls (6.34 → 4.78 ms). Mean CPU stays ≤ 0.33 %. No test of load × config interaction exists (see the Kruskal-Wallis section). "Confirmando" and "contenção" are not supported. |
| Q07 | Abstract L50-53 | "positioning this work among the first to combine statistical rigor ..." | not checkable | This is a literature claim. Nothing in the CSVs bears on it. |

## Introduction and Related Work (L81-225)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q08 | Intro L133-136 | "quantificar, com intervalo de confiança de 95\%, a degradação de latência ... e o consumo adicional de CPU e memória heap da JVM" | corrected (D06) | The paper reports no confidence interval anywhere. CPU and memory got no test at all. Memory comes from `docker stats`, which measures container memory, not JVM heap. |
| Q09 | Rel. work L174-175 | "reduzem significativamente o custo da instrumentação (até 6,15$\times$)" | not checkable | This is an external figure from Yang 2024. Verify it against the source. |
| Q10 | Method L459-460, L855 | "com 41 microsserviços reais" | not checkable | External fact about TrainTicket. |

## Methodology (L228-515)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q11 | Workload L359-362 | "duração total de 5 minutos e 30~segundos ... 30~segundos de \textit{warm-up} ... e 5~minutos em carga constante" | corrected (D12) | The throughput table equals mean count / 330 s exactly (Q29), so k6 counts cover the full 330 s. Minor: procedure step 3 (L501-503) describes a separate 30 s warm-up before k6, which reads like a second warm-up. Clarify. |
| Q12 | Workload L364 | "pausa de 100~ms entre requisições consecutivas de um mesmo VU" | not checkable | No sleep data in the CSVs. It is consistent with closed-loop arithmetic: 100 / (0.1 + 0.00538 s) ≈ 949 req/s ceiling vs 900 req/s measured over 330 s including ramp. |
| Q13 | Fatores L401-409 | "\textit{heap} máximo da JVM em 2~GB ... limite de CPU dos contêineres em 2~vCPUs ... intervalo de coleta do Prometheus em 15~segundos ... Intel Core i5-12450H ... 16~GB" | corrected (D12) | Configuration and hardware. No data in the CSVs. |
| Q14 | Fatores L386-388, L396-399 | "A carga alta (100~VUs) tensiona o sistema próximo à saturação, revelando o custo marginal da observabilidade sob contenção de CPU e memória" | corrected (D07) | The data show no saturation (see Q06). Mean container CPU at 100 VUs in baseline is 0.28-0.33 %. Memory is ~1.5 GiB of a 2 GB heap limit, but no GC data exists. |
| Q15 | Métricas Tab. L436; L449-450 | "Memória heap por serviço & docker stats & MB" / "reportada em MiB" | corrected (D06) | `docker stats` reports container memory, not heap. The table header says MB while the text and data are MiB/GiB. |
| Q16 | Métricas L445-446 | "medido em requisições por segundo bem-sucedidas (HTTP~2xx)" | not checkable | The `count` column has no status-code breakdown. |
| Q17 | Métricas Tab. L437; L450-451 | "Erros HTTP & k6 & \%" / "A taxa de erros HTTP agrega todas as respostas com código diferente de 2xx" | not checkable | No error data in any CSV. The paper never reports an error rate either: a declared metric that has no result. |
| Q18 | Métricas L446-449 | "O uso de CPU é amostrado via \texttt{docker stats} ao final de cada execução ... reportado como utilização percentual do limite alocado ao contêiner" | not checkable | metrics.csv holds one value per run, which fits a single sample. Whether the value is a percentage of the limit or of a host core cannot be told from the CSV. |
| Q19 | Justificativa L488-489 | "O \textit{script} \texttt{analyze.py} implementa essa sequência ... utilizando \texttt{scipy.stats}" | confirmed | [`scripts/analyze.py`](../scripts/analyze.py) runs `stats.shapiro`, then `stats.ttest_ind` or `stats.mannwhitneyu`; its outputs match the paper (Q27). |

## Results: latency and hypothesis tests (L521-591)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q20 | Tab. latencia L541-548 | Absolute ms values: "6,34 & 11,58 & 20,29" ... "5,88 (+23,1\%) & 17,23 (+56,6\%) & 27,73 (+58,5\%)" | confirmed | All 18 ms values match the summary-table means to 2 dp. Every per-rep mean also matches. Overheads match except Q21. |
| Q21 | Tab. latencia L545; Tab. hipotese L584 | "13,10 (+8,9\%)" / "p95 & 50 VUs & t-test & ... & 8,9\%" | corrected (D01) | CSV gives 8.82 % (recomputed 8.83), which rounds to **8.8 %**. The same 8.9 is hardcoded in the figure scripts (fig2, fig8 v2, fig9). |
| Q22 | Latência L553-556 | "($p < 0{,}001$, teste t de Welch ou Mann-Whitney U conforme normalidade)" | corrected (D12) | The CSV says only "t-test". With n = 30 per group, Student and Welch give the identical t statistic (recomputed: −79.30, −18.15, −43.07 ... matching the CSV). Only df differs, and every p is ≪ 0.001 either way. |
| Q23 | Latência L556-559 | "8,4\% em p50 e 16,9\% em p99 ... 6,1\% em p50 e 10,1\% em p99 ... 23,1\% em p50 e 58,5\% em p99" | confirmed | CSV: 8.45 / 16.86, 6.12 / 10.12, 23.09 / 58.52. |
| Q24 | Latência L559-561 | "o overhead cresce de forma desproporcional ... indicando que a instrumentação amplifica a latência de cauda sob contenção de recursos" | corrected (D07) | The increase is real in absolute terms for p95 and p99. Δp95 is 1.52 / 1.06 / 6.23 ms and Δp99 is 3.42 / 2.10 / 10.24 ms. But "sob contenção" is not shown (Q06), and no interaction test exists. |
| Q25 | Latência L561-563 | "a latência absoluta do baseline diminui com o aumento da carga (de 6,34~ms a 10~VUs para 4,78~ms a 100~VUs em p50)" | confirmed | CSV gives 6.336 → 4.778 ms. Per-rep SDs are 0.023 and 0.093, so the drop is not noise. Baseline p95 (11.58 → 11.01) and p99 (20.29 → 17.49) also fall. |
| Q26 | Latência L563-565 | "possivelmente devido a efeitos de cache \textit{warm} e otimizações da JVM sob carga sustentada" | not checkable | No cache, JIT or GC data. The hedge "possivelmente" is appropriate. See the p50 section for what the data do show. |
| Q27 | Tab. hipotese L572-588 | Test per row ("t-test" / "Mann-Whitney U"), "$<$0{,}001", caption "Todos significativos a $\alpha = 0{,}05$" | confirmed | The test names match hypothesis-tests.csv row for row. Recomputation from per-rep-variance: MW U = 58 (p50 medium) and 22 (p50 high), identical to the CSV, and all t statistics match. |

## Results: throughput (L593-617)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q28 | Tab. throughput L606-608 | "88,5 & 88,0 & 0,6\%" / "444,8 & 442,9 & 0,4\%" / "900,3 & 884,5 & 1,8\%" | confirmed | Mean count / 330 s gives 88.51 / 87.95, 444.84 / 442.92, 900.28 / 884.51. Reductions are 0.63 / 0.43 / 1.75 %. Note: the 330 s denominator includes the 30 s ramp, so steady-state req/s is understated by a few %. The ratios are unaffected. |
| Q29 | Throughput L613-617 | "a redução atinge 1,8\%, valor relativamente modesto que reflete o aumento de latência" | corrected (D11) | It is consistent with closed-loop arithmetic: 100/(0.1+0.007281) vs 100/(0.1+0.005379) predicts −1.77 %, and −1.75 % was measured. Throughput loss is a mechanical consequence of the latency increase plus 100 ms think time. |

## Results: tail latency (L619-652)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q30 | Cauda L621-622 | "o overhead em carga alta é dominado por \textit{outliers} de cauda longa" | corrected (D07) | The p50 itself rises 23 % at 100 VUs, which is a bulk shift. Only 3.0 % of requests exceed 20 ms. Observed-high per-rep p50 is **bimodal**: 8 reps at 4.82-5.14 ms (≈ baseline 4.78) and 21 reps at 5.91-6.46 ms. |
| Q31 | Tab. cauda L636-643 | ">20 ms: 1,1 / 1,7 / 1,1 / 1,4 / 0,7 / 3,0 \%; >50 ms: 0,0 except observed 100 VUs 0,1 \%; >100 ms: all 0,0 \%" | confirmed | Mean of 30 reps for >20 ms: 1.055 / 1.659 / 1.149 / 1.435 / 0.655 / 3.008. For >50 ms the observed 100 VUs value is 0.071; all others round to 0.0. For >100 ms the largest value is 0.011. |
| Q32 | Cauda L648-649; Discussão L792-794 | "3,0\% ... contra apenas 0,7\% no baseline -- um aumento de 4$\times$" | corrected (D02) | 3.008 / 0.655 = **4.6×** (4.3× from the rounded values). It should say "≈4,6×" or "mais de 4×". |
| Q33 | Cauda L650-652 | "a proporção de requisições com latência elevada é suficiente para inflacionar significativamente os percentis p95 e p99" | corrected (D08) | Observed p95 at 100 VUs is 17.23 ms, below 20 ms. The p95 rise (11.0 → 17.2 ms) cannot come from requests above 20 ms; it is a shift of the body of the distribution. The claim is plausible for p99 only. |

## Results: latency decomposition (L654-687)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q34 | Tab. decomposicao L672-679 | "Waiting 6,25 / 6,78; 6,00 / 6,36; 4,64 / 5,73; Sending 0,02 ... 0,01; Receiving 0,05 / 0,05; 0,08 / 0,09; 0,08 / 0,07" | confirmed | latency-breakdown means: waiting_p50 6.253 / 6.785 / 5.998 / 6.359 / 4.643 / 5.727. sending_p50 0.020 / 0.021 / 0.018 / 0.020 / 0.016 / 0.015. receiving_p50 0.045 / 0.048 / 0.082 / 0.094 / 0.079 / 0.071. |
| Q35 | Decomp. L656-660 | "o overhead é quase integralmente atribuível ao tempo de processamento no servidor (\textit{server waiting time})" | confirmed | The waiting_p50 increase as a share of the http_req_duration p50 increase is 99 % / 96 % / 98 % (low / medium / high). |
| Q36 | Decomp. L684-685 | "Os tempos de envio ... e recebimento ... são desprezíveis em todas as configurações ($<$0,1~ms)" | confirmed | The largest p50 value is 0.094 ms. Means reach 0.144 ms and receiving_p99 reaches 0.97 ms, but the claim is about p50. |
| Q37 | Decomp. L685-687; Discussão L794-796 | "confirmando que o overhead não é causado por saturação de rede, mas sim pelo custo computacional da instrumentação dentro da JVM" | corrected (D09) | k6 "waiting" covers everything after the gateway: the inter-container hops gateway→order→payment→travel→DB/Redis, plus host contention from the collector, Jaeger, Loki and Promtail containers on the same machine. It rules out only the client↔gateway transfer. It cannot locate the cost "dentro da JVM". |

## Results: resources (L689-762)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q38 | Tab. cpu L704-711 | CPU means "0,23 & 0,24 & 0,22 & 0,30" ... "0,57 & 0,66 & 0,70 & 0,38" | corrected (D03) | All 24 values match the metrics.csv means **if observed-low and observed-medium use all 60 rows**. The 30-row batches differ. Observed-low: batch A 0.235 / 0.573 / 0.367 / 0.404, batch B 0.300 / 0.351 / 0.332 / 0.380. Observed-medium: batch A 0.422 / 0.508 / 0.652 / 0.401, batch B 0.457 / 0.326 / 0.583 / 0.380. |
| Q39 | Tab. memoria L725-732 | Memory means "1442 & 1510 & 1508 & 948" ... "1592 & 1664 & 1656 & 1645" | corrected (D03) | All 24 values match GiB×1024 + MiB parsing with 60 rows for observed-low and observed-medium. The mixed-unit parse is correct, for example baseline-low travel = 947.5 MiB. |
| Q40 | Tab. cpu L697 and Tab. memoria L718 captions; Ameaças L877-878 | "Média de 30 repetições" | corrected (D03) | observed-low and observed-medium have 60 rows (two batches, both rep 1-30) and the tables average all 60. The memory batches disagree strongly in observed-medium: batch A 1406 / 1411 / 1427 / 1349 MiB vs batch B 1552 / 1644 / 1634 / 1623 MiB. |
| Q41 | Recursos L737-739 | "o consumo de CPU dos serviços instrumentados é consistentemente superior ao baseline em todos os níveis de carga" | corrected (D04) | The means are inflated by spikes: 43 of 960 samples exceed 1 %, max 4.75 %. Medians: gateway low 0.23 vs 0.23; gateway medium 0.27 vs 0.24 (lower); travel medium 0.295 vs 0.305. A Mann-Whitney (60-row observed) is n.s. for gateway low (p = 0.33), travel low (p = 0.14) and travel medium (p = 0.42). Gateway medium is significant in the **opposite** direction by ranks (p = 0.024). |
| Q42 | Recursos L739-745 | "O \textit{gateway} apresenta overhead de 17--104\%" / "\textit{order-service} (+83--106\%) e \textit{payment-service} (+59--130\%)" / "\textit{travel-service} ... (+19--30\%)" | corrected (D04) | These ranges reproduce only from the **rounded** table values. Unrounded means give GW 16-101 %, order 77-106 %, payment 55-127 %, travel 20-30 %. Because the means are driven by spikes, the ranges are fragile (Q41). |
| Q43 | Recursos L741-746; Discussão L796-799 | "que processam \textit{spans} de tracing propagados pela cadeia. O \textit{travel-service}, que não realiza chamadas downstream, apresenta overhead menor" | corrected (D13) | The CSVs hold no per-span or per-component CPU breakdown. This is a mechanism hypothesis and should be stated as one. |
| Q44 | Recursos L745-747 | "\textit{order} e \textit{payment} atingem 0,66\% e 0,70\% de CPU, contra 0,32\% no baseline" | confirmed | Observed: 0.658 / 0.699. Baseline: 0.320 / 0.325. |
| Q45 | Recursos L749-751 | "A memória dos serviços instrumentados apresenta overhead de 6--7\% em carga alta" | confirmed | GW +6.8 %, order +6.8 %, payment +6.6 %, travel +6.2 %. |
| Q46 | Recursos L752-754 | "\textit{travel-service} apresenta overhead de memória mais elevado (+49\%) ... (948~MiB no baseline, contra 1442--1510~MiB nos demais serviços)" | confirmed | 1416.1 / 947.5 = +49.4 %. Other baseline-low services: 1441.6-1509.9 MiB. |
| Q47 | Recursos L752-754 | "possivelmente porque o serviço parte de um \textit{heap} inicial menor" | corrected (D06) | The metric is container memory, not heap. The baseline-low travel samples range 853-1011 MiB while the other loads sit at ~1.5 GiB. No data explains why. |
| Q48 | Recursos L755-757 | "Esse custo fixo é amortizado sob carga moderada e alta" | corrected (D05) | For the non-travel services the memory overhead is **larger** at high load (+6.6 to +6.8 %) than at low load (+4.6 to +5.4 %). Nothing is amortized. |
| Q49 | Recursos L757-762 | "Em carga média, o overhead de memória é desprezível ($-$3\% a $+$1\%) ... sugerindo que o GC consegue recuperar a memória adicional" | corrected (D03) | The arithmetic matches the 60-row means (−3.4 % to +0.9 %). But that figure averages two inconsistent batches: batch A −12.3 % to −4.0 %, batch B +5.4 % to +7.0 %. Batch B alone matches the high-load pattern. The GC interpretation rests on mixed batches, and no GC data exists. |

## Discussion (L765-878)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q50 | Interpretação L773-777 | "O overhead é moderado e relativamente uniforme entre percentis (8,4\% em p50, 16,9\% em p99), consistente com o custo fixo da instrumentação" | corrected (D10) | The p99 overhead is twice the p50 overhead, which is not uniform. "Custo fixo" is an interpretation; a single load level cannot separate fixed from variable cost, and the overhead is not monotonic in load. |
| Q51 | Interpretação L778-781 | "alinhado com os 5--15\% reportados por Yang et al." / "o overhead em p99 (16,9\%) exceda essa faixa" | not checkable | The 5-15 % range is external and should be verified in Yang 2024. The 16.9 % is confirmed (Q05). |
| Q52 | Interpretação L783-786 | "O overhead em p50 é o menor entre os três níveis (6,1\%)" / "O overhead em p99 (10,1\%)" | confirmed | 6.12 < 8.45 < 23.09. p99 is 10.12. |
| Q53 | Interpretação L786-788 | "possivelmente porque o \textit{batching} de spans do OTEL amortiza o custo por requisição sob carga moderada" | not checkable | No collector or batching data. |
| Q54 | Interpretação L801-806; Implicações L828-830; Conclusão L903-905 | "o \textit{throughput} é preservado em todos os níveis de carga ... a queda máxima é de 1,8\%" / "O \textit{throughput} não é significativamente afetado pela instrumentação" | corrected (D11) | 1.8 % is confirmed (Q28). But no throughput test was run, and a Welch t from summary-table at 100 VUs gives t ≈ 22.7 (Δ 5,203 req/run, SDs 196 / 1241), so the loss is statistically significant. Say "small (≤1,8 %)", not "não significativamente". The near-zero loss is largely a property of the closed-loop design with 100 ms think time (Q29), not evidence of preserved capacity. |
| Q55 | Implicações L814-816 | "Em ambientes com carga baixa a moderada (até 50~VUs), o overhead ... é aceitável (6--17\% entre p50 e p99)" | confirmed | The range across p50, p95 and p99 at 10 and 50 VUs is 6.12-16.86 %. "Aceitável" is a judgement. |
| Q56 | Implicações L817-819 | "particularmente na latência de cauda (+58\% em p99)" | confirmed | 58.52 %. |
| Q57 | Implicações L822-824 | "A latência p99 é a métrica mais sensível ao overhead" | confirmed | p99 > p95 > p50 overhead at every load. At 100 VUs the p95/p99 gap is small (56.6 vs 58.5 %). |
| Q58 | Implicações L825-827 | "O custo de memória da instrumentação (5--7\% adicional em carga alta)" | corrected (D05) | The data give 6.2-6.8 %. The Results section itself says 6-7 % (L749-750). |
| Q59 | Ameaças L835-837 | "30 repetições por combinação, conferindo poder estatístico adequado" | corrected (D12) | No power analysis. Sample size suffices for the observed effects, since all p < 1e-8. |
| Q60 | Ameaças L861-865 | "a utilização de CPU permaneça consistentemente abaixo de 1\% em todos os cenários, sem picos significativos" | corrected (D04) | 43 of 960 per-service samples exceed 1 %. Max 4.75 % (observed-high order), 4.62 % (observed-low order), 3.47 % (observed-medium gateway). Baseline-low order has a 1.02 % sample. This undercuts "a amostragem pontual é representativa". |
| Q61 | Ameaças L866-868 | "O overhead relativo ... é consistente e estatisticamente significativo, preservando a validade da comparação" (CPU) | corrected (D04) | No CPU test exists in the CSVs. A Mann-Whitney finds several cells n.s. and one reversed (Q41). |
| Q62 | Ameaças L871-872 | "os serviços não apresentam pressão significativa de GC sob os níveis de carga avaliados" | not checkable | No GC data. |

## Conclusion (L881-915)

| Id | Section (line) | Claim (delivered text) | Status | Data / evidence |
|---|---|---|---|---|
| Q63 | Conclusão L892-895 | "O overhead de observabilidade é \textbf{estatisticamente significativo} em todos os níveis de carga e percentis de latência ($p < 0{,}001$)" | confirmed | Same as Q03: largest p = 7.1e-9. |
| Q64 | Conclusão L896-898 | "o overhead é moderado (6--17\% entre p50 e p99), consistente com o custo fixo da instrumentação e alinhado com a literatura" | corrected (D10) | The numbers are confirmed (Q55). "Custo fixo" is not shown (Q50), and literature alignment is not checkable (Q51). |
| Q65 | Conclusão L899-902 | "23\% em p50 e 58\% em p99, indicando que a instrumentação amplifica a contenção de recursos sob alta concorrência" | corrected (D07) | The numbers are confirmed. The mechanism is not supported (Q06, Q14, and the p50 section below). |
| Q66 | Conclusão L906-908 | "A decomposição de latência confirma que o overhead é integralmente atribuível ao processamento no servidor, excluindo saturação de rede como causa" | corrected (D09) | The data give 96-99 %, and Results itself says "quase integralmente". "Server" includes the inter-service network and host contention (Q37). |
