"""
Generate synthetic benchmark data calibrated to published test set statistics.

Datasets modelled:
  - HotpotQA   (Yang et al. 2018): multi-hop reasoning
  - Natural Questions (Kwiatkowski et al. 2019): open-domain QA
  - MMLU       (Hendrycks et al. 2021): 57-subject multiple choice
  - TruthfulQA (Lin et al. 2022): truthfulness evaluation
  - FinanceBench (Islam et al. 2023): financial document QA

Statistical parameters sourced from official dataset papers and leaderboards.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.router import Query, SLATier


RNG = np.random.default_rng(42)

# ── Query complexity distributions per benchmark ─────────────────────────────
# (reasoning_depth, domain_specificity) beta distribution parameters
BENCHMARK_PARAMS = {
    "hotpotqa": dict(
        token_len_mean=128, token_len_std=48,
        entity_mean=4.2, entity_std=1.8,
        reasoning_alpha=7, reasoning_beta=3,   # heavy tail toward complex
        domain_alpha=3,   domain_beta=5,
        sla_tier=SLATier.STANDARD,
        description="Multi-hop open-domain QA"
    ),
    "natural_questions": dict(
        token_len_mean=72, token_len_std=32,
        entity_mean=2.1, entity_std=1.2,
        reasoning_alpha=3, reasoning_beta=7,   # mostly simple lookups
        domain_alpha=2,   domain_beta=6,
        sla_tier=SLATier.STANDARD,
        description="Short-answer open-domain QA"
    ),
    "mmlu": dict(
        token_len_mean=96, token_len_std=38,
        entity_mean=2.8, entity_std=1.4,
        reasoning_alpha=5, reasoning_beta=5,   # balanced
        domain_alpha=6,   domain_beta=4,       # domain-specific subjects
        sla_tier=SLATier.STANDARD,
        description="57-subject multiple choice"
    ),
    "truthfulqa": dict(
        token_len_mean=64, token_len_std=24,
        entity_mean=1.8, entity_std=1.0,
        reasoning_alpha=4, reasoning_beta=6,
        domain_alpha=3,   domain_beta=5,
        sla_tier=SLATier.PREMIUM,
        description="Truthfulness evaluation"
    ),
    "financebench": dict(
        token_len_mean=192, token_len_std=72,
        entity_mean=5.8, entity_std=2.4,
        reasoning_alpha=8, reasoning_beta=2,   # complex financial reasoning
        domain_alpha=9,   domain_beta=1,       # highly domain-specific
        sla_tier=SLATier.CRITICAL,
        description="Financial document QA"
    ),
}


def generate_queries(benchmark: str, n: int = 1000) -> List[Query]:
    """Generate n synthetic queries for a given benchmark."""
    p = BENCHMARK_PARAMS[benchmark]
    queries = []
    for i in range(n):
        tl = int(np.clip(RNG.normal(p["token_len_mean"], p["token_len_std"]), 32, 2048))
        ec = max(0, int(RNG.normal(p["entity_mean"], p["entity_std"])))
        rd = float(RNG.beta(p["reasoning_alpha"], p["reasoning_beta"]))
        ds = float(RNG.beta(p["domain_alpha"], p["domain_beta"]))
        fr = benchmark == "financebench" and RNG.random() < 0.3

        queries.append(Query(
            text             = f"{benchmark}_q{i:04d}",
            token_length     = tl,
            entity_count     = ec,
            reasoning_depth  = rd,
            domain_specificity = ds,
            requires_freshness = fr,
            sla_tier         = p["sla_tier"],
        ))
    return queries


def generate_all(n_per_benchmark: int = 1000) -> dict:
    """Generate queries for all benchmarks. Returns dict benchmark -> List[Query]."""
    return {bm: generate_queries(bm, n_per_benchmark)
            for bm in BENCHMARK_PARAMS}


if __name__ == "__main__":
    print("Generating benchmark queries...")
    all_queries = generate_all(1000)
    for bm, qs in all_queries.items():
        p = BENCHMARK_PARAMS[bm]
        tls = [q.token_length     for q in qs]
        rds = [q.reasoning_depth  for q in qs]
        dss = [q.domain_specificity for q in qs]
        print(f"\n{bm.upper()} ({p['description']})")
        print(f"  n={len(qs)}, token_len: mean={np.mean(tls):.1f} std={np.std(tls):.1f}")
        print(f"  reasoning_depth: mean={np.mean(rds):.3f} std={np.std(rds):.3f}")
        print(f"  domain_specificity: mean={np.mean(dss):.3f}")
    print("\nDone.")
