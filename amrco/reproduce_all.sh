#!/bin/bash
# reproduce_all.sh
# Reproduces all paper results from scratch.
# Runtime: ~8 minutes on standard CPU.

set -e
echo "=============================================="
echo "  AMRCO — Reproducing All Paper Results"
echo "=============================================="

cd "$(dirname "$0")"

echo ""
echo "[1/6] Generating benchmark data..."
python experiments/generate_benchmark_data.py

echo ""
echo "[2/6] Running benchmark evaluations (n=1000, 10k bootstrap)..."
python experiments/run_benchmarks.py --n_samples 1000 --seed 42

echo ""
echo "[3/6] Running hallucination study..."
python experiments/run_hallucination_study.py

echo ""
echo "[4/6] Running cost analysis..."
python experiments/run_cost_analysis.py

echo ""
echo "[5/6] Running latency profiling..."
python experiments/run_latency_profiling.py

echo ""
echo "[6/6] Running case study simulation..."
python experiments/run_case_study.py

echo ""
echo "[Figures] Generating all paper figures..."
python experiments/generate_figures.py

echo ""
echo "=============================================="
echo "  All results saved to results/ and figures/"
echo "=============================================="
echo ""
echo "Run unit tests with:"
echo "  python -m pytest tests/ -v"
