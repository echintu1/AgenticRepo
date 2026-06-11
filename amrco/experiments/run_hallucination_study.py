"""
Hallucination Rate Analysis
============================
Measures hallucination rates per model, per retrieval mode, per domain.
Produces: results/hallucination_results.csv
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from scipy import stats
pass  # tqdm

from src.router import MODEL_SPECS, ModelTier, RoutingDecision, RetrievalMode
from src.validator import PostGenerationValidator, RAG_HALLUCINATION_REDUCTION

SEED    = 42
N       = 1000
N_BOOT  = 10_000
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(OUT_DIR, exist_ok=True)
RNG     = np.random.default_rng(SEED)


def make_decision(model_key: str, retrieval_mode: RetrievalMode) -> RoutingDecision:
    spec = MODEL_SPECS[model_key]
    return RoutingDecision(
        model_key            = model_key,
        tier                 = spec.tier,
        retrieval_mode       = retrieval_mode,
        confidence_threshold = 0.80,
        estimated_cost_usd   = 0.005,
        estimated_latency_ms = spec.p50_latency_ms,
        complexity_score     = 0.5,
        reasoning            = "test",
    )


def bootstrap_ci(data, n_boot=N_BOOT):
    boot = [RNG.choice(data, len(data), replace=True).mean() for _ in range(n_boot)]
    return np.mean(data), np.percentile(boot, 2.5), np.percentile(boot, 97.5)


def run_hallucination_study():
    rows = []
    models = ["llama3-8b", "llama3-70b", "claude-haiku",
              "gemini-1-5-pro", "gpt-4o", "claude-3-5-sonnet"]
    ret_modes = [RetrievalMode.NONE, RetrievalMode.DENSE,
                 RetrievalMode.HYBRID]
    domains = {"general": 1.0, "financial": 1.25, "healthcare": 1.18}

    print("\nHallucination Rate Study")
    print("="*60)

    for domain_name, domain_factor in domains.items():
        validator = PostGenerationValidator(rng=RNG, domain_factor=domain_factor)
        print(f"\n  Domain: {domain_name.upper()} (factor={domain_factor})")

        for model_key in models:
            for ret_mode in ret_modes:
                decision = make_decision(model_key, ret_mode)
                halluc_flags = []

                # Simulate retrieval result when needed
                from src.retriever import HybridRetriever, RetrievalResult
                retriever = HybridRetriever(rng=RNG)

                for _ in range(N):
                    if ret_mode != RetrievalMode.NONE:
                        ret_result = retriever.retrieve("test_query", ret_mode)
                    else:
                        ret_result = None
                    vr = validator.validate(decision, ret_result)
                    halluc_flags.append(int(vr.hallucination_flag))

                arr  = np.array(halluc_flags, dtype=float)
                mean, lo, hi = bootstrap_ci(arr)
                spec = MODEL_SPECS[model_key]
                base_hr = spec.hallucination_rate
                rag_red = RAG_HALLUCINATION_REDUCTION[ret_mode]

                rows.append({
                    "domain":          domain_name,
                    "model":           model_key,
                    "retrieval_mode":  ret_mode.value,
                    "n_samples":       N,
                    "hallucination_rate": round(mean, 4),
                    "ci_lower":        round(lo, 4),
                    "ci_upper":        round(hi, 4),
                    "base_rate":       round(base_hr, 4),
                    "rag_reduction_pct": round(rag_red * 100, 1),
                    "tier":            spec.tier.value,
                })
                print(f"    {model_key:<22} {ret_mode.value:<8} "
                      f"HR={mean:.4f} [{lo:.4f},{hi:.4f}]")

    # AMRCO combined hallucination rate (weighted by routing distribution)
    print("\n  AMRCO Combined (financial domain):")
    validator_fin = PostGenerationValidator(rng=RNG, domain_factor=1.25)
    amrco_flags = []
    routing_probs = [("llama3-8b", RetrievalMode.NONE, 0.05),
                     ("llama3-70b", RetrievalMode.DENSE, 0.22),
                     ("claude-3-5-sonnet", RetrievalMode.HYBRID, 0.73)]
    retriever = HybridRetriever(rng=RNG)

    for _ in range(N):
        # Pick tier according to routing distribution
        r = RNG.random()
        cumulative = 0
        for mkey, rmode, prob in routing_probs:
            cumulative += prob
            if r <= cumulative:
                break
        d   = make_decision(mkey, rmode)
        ret = retriever.retrieve("q", rmode) if rmode != RetrievalMode.NONE else None
        vr  = validator_fin.validate(d, ret)
        amrco_flags.append(int(vr.hallucination_flag))

    arr = np.array(amrco_flags, dtype=float)
    mean, lo, hi = bootstrap_ci(arr)
    rows.append({
        "domain": "financial", "model": "amrco",
        "retrieval_mode": "adaptive", "n_samples": N,
        "hallucination_rate": round(mean, 4),
        "ci_lower": round(lo, 4), "ci_upper": round(hi, 4),
        "base_rate": None, "rag_reduction_pct": None, "tier": "adaptive",
    })
    print(f"    AMRCO adaptive            HR={mean:.4f} [{lo:.4f},{hi:.4f}]")

    df = pd.DataFrame(rows)
    out_path = os.path.join(OUT_DIR, "hallucination_results.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  Saved -> {out_path}")
    return df


if __name__ == "__main__":
    df = run_hallucination_study()
