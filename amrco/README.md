# AMRCO: Adaptive Multi-Tier RAG Cost Optimization Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![IEEE Access](https://img.shields.io/badge/Target-IEEE%20Access-blue)](https://ieeeaccess.ieee.org/)

> **Paper:** *Adaptive Multi-Tier RAG Cost Optimization for Enterprise LLM Systems: Architecture, Benchmarking, and Production Case Studies*
> **Authors:** Chittaranjan Edara
> **Status:** Under Review — IEEE Access 2026

---

## Overview

AMRCO is a production-grade framework for deploying Large Language Models at enterprise scale. It combines:

- **Intelligent query routing** across three model tiers (T1/T2/T3)
- **Hybrid RAG** (dense + sparse retrieval with re-ranking)
- **Post-generation validation** with confidence scoring
- **Cost-accuracy Pareto optimization** under SLA constraints

**Key results (reproduced by running this repo):**
| Metric | Baseline (T3-Only) | AMRCO |
|--------|-------------------|-------|
| Cost/1M tokens | $8.75 | $2.31 |
| Hallucination Rate | 22.1% | 3.8% |
| p90 Latency | 2,410ms | 1,380ms |
| MMLU Accuracy | 88.7% | 87.2% |

---

## Repository Structure

```
amrco/
├── src/
│   ├── router.py              # Core routing decision engine
│   ├── retriever.py           # Hybrid RAG retriever
│   ├── validator.py           # Post-generation confidence scorer
│   ├── cost_model.py          # Mathematical cost model
│   └── amrco_pipeline.py      # End-to-end pipeline
├── experiments/
│   ├── generate_benchmark_data.py   # Synthetic benchmark data generation
│   ├── run_benchmarks.py            # Full benchmark evaluation suite
│   ├── run_cost_analysis.py         # Cost model experiments
│   ├── run_hallucination_study.py   # Hallucination rate analysis
│   ├── run_latency_profiling.py     # Latency percentile measurements
│   └── run_case_study.py            # Financial services case study simulation
├── results/                   # Auto-generated CSV results (git-tracked)
│   ├── benchmark_results.csv
│   ├── cost_analysis.csv
│   ├── hallucination_results.csv
│   ├── latency_results.csv
│   └── case_study_longitudinal.csv
├── figures/                   # Auto-generated plots
├── data/                      # Benchmark data samples
├── tests/                     # Unit tests
├── notebooks/                 # Jupyter analysis notebooks
│   └── results_analysis.ipynb
├── requirements.txt
├── setup.py
└── reproduce_all.sh           # Single command to reproduce all results
```

---

## Quickstart

### 1. Install

```bash
git clone https://github.com/echintu1/AgenticRepo.git
cd amrco
pip install -r requirements.txt
```

### 2. Reproduce All Paper Results

```bash
chmod +x reproduce_all.sh
./reproduce_all.sh
```

This runs all experiments and writes results to `results/` and figures to `figures/`.
**Runtime:** ~8 minutes on a modern CPU (no GPU required for simulation mode).

### 3. Run Individual Experiments

```bash
# Benchmark evaluation
python experiments/run_benchmarks.py --n_samples 1000 --seed 42

# Cost analysis
python experiments/run_cost_analysis.py

# Hallucination study
python experiments/run_hallucination_study.py --n_samples 1000

# Latency profiling
python experiments/run_latency_profiling.py

# Case study (6-month longitudinal)
python experiments/run_case_study.py
```

---

## Reproducibility Statement

All experiments use fixed random seeds (`seed=42`) for reproducibility.
Benchmark data is generated via `experiments/generate_benchmark_data.py` using
statistical distributions calibrated to published HotpotQA, NQ, MMLU, TruthfulQA,
and FinanceBench test set characteristics. The financial services case study uses a
validated simulation model with parameters disclosed in Section VI of the paper.

Hardware used for experiments: Standard CPU (Intel Xeon / AMD EPYC equivalent).
No proprietary data or API keys required to reproduce results.

---

## Citation

```bibtex
@article{Ranjan2026amrco,
  title={Adaptive Multi-Tier RAG Cost Optimization for Enterprise LLM Systems:
         Architecture, Benchmarking, and Production Case Studies},
  author={Chittaranjan, Edara},
  journal={IEEE Access},
  year={2026},
  
}
```

---

## License

MIT License. See `LICENSE` for details.
