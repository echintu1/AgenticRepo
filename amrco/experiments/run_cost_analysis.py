"""
Cost Analysis Experiment
=========================
Computes cost savings of AMRCO vs. T3-only baselines across workload volumes.
Produces: results/cost_analysis.csv
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd

from src.router import AMRCORouter, RouterConfig, Query, SLATier, MODEL_SPECS
from src.cost_model import (query_cost, workload_cost_summary,
                            savings_vs_t3_only, cost_per_million_tokens)
from experiments.generate_benchmark_data import generate_all

SEED    = 42
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(OUT_DIR, exist_ok=True)
RNG     = np.random.default_rng(SEED)


def run_cost_analysis():
    router = AMRCORouter()
    all_queries = generate_all(1000)
    # flatten all benchmark queries
    all_q = [q for qs in all_queries.values() for q in qs]

    rows = []

    # ── 1. Per-model cost/1M tokens ───────────────────────────────────────────
    print("\nCost per 1M tokens (3:1 input:output ratio):")
    print("-"*45)
    model_costs = {}
    for mk, spec in MODEL_SPECS.items():
        c1m = cost_per_million_tokens(mk, input_ratio=0.75)
        model_costs[mk] = c1m
        print(f"  {mk:<24} ${c1m:.2f}")

    # AMRCO weighted average
    routing_mix = {"llama3-8b": 0.60, "llama3-70b": 0.25, "claude-3-5-sonnet": 0.15}
    amrco_c1m = sum(cost_per_million_tokens(m, 0.75) * w for m, w in routing_mix.items())
    print(f"  {'amrco (adaptive)':<24} ${amrco_c1m:.2f}")

    for mk, c in {**model_costs, "amrco": amrco_c1m}.items():
        rows.append({"experiment": "cost_per_1m", "model": mk,
                     "cost_usd": round(c, 4), "metric": "cost_per_1m_tokens"})

    # ── 2. AMRCO savings vs. baselines ───────────────────────────────────────
    print("\nAMRCO savings vs. T3-only baseline:")
    print("-"*45)
    decisions = [router.route(q) for q in all_q]

    for baseline_model in ["gpt-4o", "claude-3-5-sonnet", "gemini-1-5-pro"]:
        sv = savings_vs_t3_only(decisions, t3_model=baseline_model)
        print(f"  vs. {baseline_model:<20}: {sv['savings_pct']:.1f}% savings "
              f"(${sv['savings_usd']:.2f} saved on {sv['n_queries']} queries)")
        rows.append({
            "experiment":     "savings_vs_baseline",
            "model":          f"amrco_vs_{baseline_model}",
            "savings_pct":    round(sv["savings_pct"], 2),
            "amrco_usd":      round(sv["amrco_total_usd"], 4),
            "baseline_usd":   round(sv["t3_baseline_usd"], 4),
            "n_queries":      sv["n_queries"],
            "metric":         "cost_savings",
        })

    # ── 3. Routing distribution ───────────────────────────────────────────────
    print("\nRouting distribution:")
    tier_counts = {}
    for d in decisions:
        tier_counts[d.tier.value] = tier_counts.get(d.tier.value, 0) + 1
    total = len(decisions)
    for tier, cnt in sorted(tier_counts.items()):
        pct = cnt / total * 100
        print(f"  {tier}: {cnt} ({pct:.1f}%)")
        rows.append({"experiment": "routing_dist", "model": tier,
                     "count": cnt, "pct": round(pct, 2), "metric": "routing"})

    # ── 4. Monthly cost projection (enterprise scale) ─────────────────────────
    print("\nMonthly cost projection (enterprise: 1M queries/month):")
    print("-"*55)
    monthly_queries = 1_000_000
    scale = monthly_queries / len(all_q)
    for mk in ["gpt-4o", "claude-3-5-sonnet", "gemini-1-5-pro", "llama3-70b"]:
        spec   = MODEL_SPECS[mk]
        c_per_q = ((512 * spec.price_in_per_1m + 256 * spec.price_out_per_1m)
                   / 1_000_000)
        monthly = c_per_q * monthly_queries
        print(f"  {mk:<22}: ${monthly:>10,.0f}/month")
        rows.append({"experiment": "monthly_projection", "model": mk,
                     "monthly_usd": round(monthly, 2), "metric": "monthly_cost"})

    amrco_per_q = sv["amrco_total_usd"] / len(all_q)   # reuse from last sv calc
    amrco_monthly = amrco_per_q * monthly_queries * (sv["amrco_total_usd"]/sv["t3_baseline_usd"])
    # Recompute cleanly
    amrco_per_q_clean = sum(query_cost(d, 512, 256).inference_usd
                            for d in decisions) / len(decisions)
    amrco_monthly_clean = amrco_per_q_clean * monthly_queries
    print(f"  {'amrco (adaptive)':<22}: ${amrco_monthly_clean:>10,.0f}/month")
    rows.append({"experiment": "monthly_projection", "model": "amrco",
                 "monthly_usd": round(amrco_monthly_clean, 2), "metric": "monthly_cost"})

    df = pd.DataFrame(rows)
    out_path = os.path.join(OUT_DIR, "cost_analysis.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  Saved -> {out_path}")
    return df


if __name__ == "__main__":
    run_cost_analysis()
