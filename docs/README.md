# Docs

This benchmark is the experimental part of the final project of the course Avaliação de
Desempenho de Sistemas Computacionais (CKP8555), Mestrado e Doutorado em Ciência da Computação
(MDCC), Universidade Federal do Ceará (UFC), 2026:

> **Avaliação do Overhead de Desempenho Introduzido por Ferramentas de Observabilidade em Sistemas
> de Microsserviços**
> Luiz Matheus Sena Macedo, Arthur Anderson Guimarães Lopes and Lucas Alves Meneses.

The paper plans and runs a 2 × 3 factorial experiment (observability off/on × 10/50/100 virtual
users, 30 repetitions each) following Jain's methodology, and tests every difference at 95 %
confidence.

## Files

| File | What it is |
|---|---|
| [`paper.pdf`](paper.pdf) | The paper, in Portuguese. Revised version, see below. |
| [`credibility-checklist.md`](credibility-checklist.md) | Every checkable claim of the paper, checked against the data in [`results/`](../results/) and the code. |
| [`divergences.md`](divergences.md) | What the delivered text said that the data or the code did not support, and how the revised paper says it. |
| [`architecture.md`](architecture.md) | The system under test, the two configurations, how a run works and why. |

## About the revised paper

`paper.pdf` is the delivered text with these changes and nothing else:

- Two numbers that did not match the CSVs were fixed (D01, D02).
- The CPU and memory tables used two mixed batches for two scenarios; they now use the batch that
  belongs to the latency data (D03).
- Sentences that said more than the data show were rewritten to match the evidence: the role of
  resource contention, the CPU and memory interpretation, the latency breakdown and the
  throughput result (D04–D11, D13).
- Facts about the environment were aligned with the code: JDK 21, no CPU limit, Student t-test
  (D12).

The measured data, the experimental design and the references are unchanged. The LaTeX
source is kept in a private repository.

## Raw data

The 180 raw k6 files were deleted by the authors after the analysis because of their size (0.1 to
1 GB each). The aggregated CSVs in [`results/`](../results/) are what `scripts/analyze.py` produced
from them, and they are the evidence behind every check in this folder.
