"""Statistical analysis for the paper. Reads JSONL traces, prints paper-ready numbers.

Usage:
    python -m src.stats --traces results/traces [--pairs A:B B:C1 C1:D1 C2:D2]
    python -m src.stats --robustness results/traces_robustness

Implements the paper's pre-registered plan:
  * accuracy per condition with 95% bootstrap CI (10k resamples)
  * McNemar's exact test for paired condition comparisons, with
    Holm-Bonferroni correction across the tested contrasts
  * Wilson score intervals for rates
  * error-fate breakdown; verifier catch rate and correction rate
  * logistic regression of fault survival on injection stage and operator,
    reported as odds ratios (H2)
  * token cost per condition and per solved problem
  * robustness replication summary (mean accuracy and 95% t-interval per seed)
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
from collections import Counter

from scipy import stats as sps


def load(traces_dir: pathlib.Path, cond: str) -> dict[str, dict]:
    path = traces_dir / f"{cond}.jsonl"
    out = {}
    for line in open(path):
        t = json.loads(line)
        out[t["problem_id"]] = t
    return out


def bootstrap_ci(flags: list[int], n_boot: int = 10_000, seed: int = 0):
    """95% percentile bootstrap CI for a proportion."""
    rng = random.Random(seed)
    n = len(flags)
    stats_ = sorted(sum(rng.choices(flags, k=n)) / n for _ in range(n_boot))
    return stats_[int(0.025 * n_boot)], stats_[int(0.975 * n_boot)]


def wilson(k: int, n: int, z: float = 1.96):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return centre - half, centre + half


def mcnemar_exact(a: dict, b: dict):
    """Exact McNemar on paired binary outcomes (correct/incorrect per problem).

    Uses only the disagreement cells:
      n01 = A wrong, B right;  n10 = A right, B wrong.
    Two-sided exact binomial test on (min(n01,n10); n01+n10; p=0.5).
    """
    ids = sorted(set(a) & set(b))
    n01 = sum((not a[i]["extra"]["correct"]) and b[i]["extra"]["correct"] for i in ids)
    n10 = sum(a[i]["extra"]["correct"] and (not b[i]["extra"]["correct"]) for i in ids)
    n = n01 + n10
    p = sps.binomtest(min(n01, n10), n, 0.5).pvalue if n > 0 else 1.0
    return {"n_pairs": len(ids), "n01_B_better": n01, "n10_A_better": n10, "p_value": p}


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (step-down, monotone, capped at 1)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def error_fate(injected: dict, clean: dict):
    """For injected runs: was the planted fault caught, corrected, or propagated?

    Restricted to problems the clean pipeline solved correctly, so any new
    error is attributable to the injection. With the verifier ablated (D
    conditions) there is no accept/reject, so only propagated/absorbed are
    reported; catch and correction rates exist only for verifier conditions.
    """
    has_verifier = any(t.get("verifier_output") for t in injected.values())
    fates = Counter()
    type_counts = Counter()
    severity_counts = Counter()
    severity_propagated = Counter()
    ids = [i for i in injected
           if injected[i].get("injection_meta", {}) and
              injected[i]["injection_meta"].get("applied") and
              i in clean and clean[i]["extra"]["correct"]]
    for i in ids:
        t = injected[i]
        meta = t.get("injection_meta") or {}
        type_counts[meta.get("type", "unknown")] += 1
        
        # Track severity outcomes for number swaps
        if meta.get("type") == "number_swap" and "severity" in meta:
            sev = meta["severity"]
            severity_counts[sev] += 1
            if not t["extra"]["correct"]:
                severity_propagated[sev] += 1
                
        correct = t["extra"]["correct"]
        if not has_verifier:
            fates["propagated" if not correct else "absorbed"] += 1
            continue
        caught = t.get("verifier_verdict") == "REJECT"
        if caught and correct:
            fates["caught_and_corrected"] += 1
        elif caught and not correct:
            fates["caught_not_corrected"] += 1
        elif not caught and not correct:
            fates["silently_propagated"] += 1
        else:
            fates["absorbed_without_flag"] += 1
    total = sum(fates.values())
    if has_verifier:
        prop = fates["silently_propagated"] + fates["caught_not_corrected"]
    else:
        prop = fates["propagated"]
    lo, hi = wilson(prop, total) if total else (0, 0)
    
    type_freq = {k: f"{v}/{total} ({v/total*100:.1f}%)" for k, v in type_counts.items()}
    
    severity_rates = {}
    for sev in ["mild", "moderate", "severe"]:
        total_sev = severity_counts[sev]
        if total_sev > 0:
            prop_sev = severity_propagated[sev]
            severity_rates[sev] = f"{prop_sev}/{total_sev} ({prop_sev/total_sev*100:.1f}%)"
            
    out = {"n_valid_injections": total, **fates,
           "propagation_rate": prop / total if total else None,
           "propagation_wilson95": (round(lo, 3), round(hi, 3)),
           "injection_types": type_freq}
    if severity_rates:
        out["severity_propagation"] = severity_rates
        
    if has_verifier:
        caught = fates["caught_and_corrected"] + fates["caught_not_corrected"]
        clo, chi = wilson(caught, total) if total else (0, 0)
        out["catch_rate"] = caught / total if total else None
        out["catch_wilson95"] = (round(clo, 3), round(chi, 3))
        if caught:
            rlo, rhi = wilson(fates["caught_and_corrected"], caught)
            out["correction_rate"] = fates["caught_and_corrected"] / caught
            out["correction_wilson95"] = (round(rlo, 3), round(rhi, 3))
        else:
            out["correction_rate"] = None
    return out


def survival_logit(data: dict):
    """Logistic regression of fault survival on injection stage and operator.

    Rows: C1/C2 problems where the injection applied and clean B was correct.
    survived=1 when the final answer is wrong. Odds ratios with 95% CIs; the
    early_stage coefficient is the pre-registered test for H2.
    """
    import numpy as np
    import statsmodels.api as sm

    rows = []
    for cond, early in (("C1", 1), ("C2", 0)):
        if cond not in data or "B" not in data:
            continue
        for pid, t in data[cond].items():
            meta = t.get("injection_meta") or {}
            if not meta.get("applied"):
                continue
            b = data["B"].get(pid)
            if not (b and b["extra"]["correct"]):
                continue
            rows.append((0 if t["extra"]["correct"] else 1,
                         early,
                         1 if meta.get("type") == "operation_flip" else 0,
                         1 if meta.get("type") == "semantic_logic_error" else 0))
    if len(rows) < 20:
        print(f"  skipped: only {len(rows)} usable injections")
        return
    y = np.array([r[0] for r in rows], dtype=float)
    X = sm.add_constant(np.array([r[1:] for r in rows], dtype=float))
    try:
        fit = sm.Logit(y, X).fit(disp=0)
    except Exception as e:
        print(f"  logit failed ({e}); report raw rates instead")
        return
    names = ["intercept", "early_stage", "operation_flip", "semantic_logic_error"]
    ors = np.exp(fit.params)
    cis = np.exp(fit.conf_int())
    for name, o, (lo, hi), p in zip(names, ors, cis, fit.pvalues):
        print(f"  {name}: OR={o:.2f} [{lo:.2f}, {hi:.2f}]  p={p:.4f}  (n={len(rows)})")


def token_cost(cond_data: dict) -> int:
    """Total tokens (input + output, all stages) across a condition's traces."""
    total = 0
    for t in cond_data.values():
        for stage in (t.get("usage") or {}).values():
            total += stage.get("input_tokens", 0) + stage.get("output_tokens", 0)
    return total


def report_robustness(base: pathlib.Path):
    """Accuracy per condition across seed_*/ replicates: mean and 95% t-interval."""
    seed_dirs = sorted(base.glob("seed_*"))
    if not seed_dirs:
        raise SystemExit(f"no seed_*/ directories under {base}")
    conds = sorted({p.stem for d in seed_dirs for p in d.glob("*.jsonl")})
    print(f"=== Robustness replication ({len(seed_dirs)} seeds) ===")
    for c in conds:
        accs = []
        for d in seed_dirs:
            if not (d / f"{c}.jsonl").exists():
                continue
            flags = [int(t["extra"]["correct"]) for t in load(d, c).values()]
            accs.append(sum(flags) / len(flags))
        mean = sum(accs) / len(accs)
        if len(accs) > 1:
            sd = (sum((a - mean) ** 2 for a in accs) / (len(accs) - 1)) ** 0.5
            half = sps.t.ppf(0.975, len(accs) - 1) * sd / len(accs) ** 0.5
            per_seed = ", ".join(f"{a:.3f}" for a in accs)
            print(f"  {c}: mean={mean:.3f} +/- {half:.3f}  (seeds: {per_seed})")
        else:
            print(f"  {c}: {mean:.3f} (single replicate)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", default="results/traces")
    ap.add_argument("--pairs", nargs="*",
                    default=["A:B", "B:C1", "C1:D1", "C2:D2"],
                    help="paired McNemar comparisons (default: the paper's contrasts)")
    ap.add_argument("--robustness", default=None, metavar="DIR",
                    help="summarise robustness replicates under DIR instead")
    args = ap.parse_args()

    lines = []
    def log(msg=""):
        lines.append(msg)

    if args.robustness:
        report_robustness(pathlib.Path(args.robustness))
        return

    d = pathlib.Path(args.traces)
    conds = sorted(p.stem for p in d.glob("*.jsonl"))
    data = {c: load(d, c) for c in conds}

    log("=== Accuracy with 95% bootstrap CI ===")
    for c in conds:
        flags = [int(t["extra"]["correct"]) for t in data[c].values()]
        acc = sum(flags) / len(flags)
        lo, hi = bootstrap_ci(flags)
        log(f"  {c}: {acc:.3f}  [{lo:.3f}, {hi:.3f}]  n={len(flags)}")

    log("\n=== McNemar exact (paired), Holm-Bonferroni corrected ===")
    tested = [(pair, mcnemar_exact(data[x], data[y]))
              for pair in args.pairs
              for x, y in [pair.split(":")]
              if x in data and y in data]
    adj = holm([r["p_value"] for _, r in tested])
    for (pair, r), p_adj in zip(tested, adj):
        log(f"  {pair}: {r}  p_holm={p_adj:.4f}")

    log("\n=== Error fate (injected conditions vs clean B) ===")
    if "B" in data:
        for c in conds:
            if c.startswith(("C", "D")):
                log(f"  {c}: {error_fate(data[c], data['B'])}")

    log("\n=== Fault survival logit (H2): odds ratios ===")
    # Capture survival logit output
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        survival_logit(data)
    log(f.getvalue().strip())

    log("\n=== Token cost ===")
    for c in conds:
        total = token_cost(data[c])
        solved = sum(t["extra"]["correct"] for t in data[c].values())
        per_solved = f"{total / solved:.0f}" if solved else "n/a"
        log(f"  {c}: {total} tokens total, {per_solved} per solved problem")

    full_report = "\n".join(lines)
    print(full_report)

    # Save report to results/rq1_report.txt (overwriting)
    out_file = pathlib.Path("results/rq1_report.txt")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_report, encoding="utf-8")
    print(f"\n[Saved RQ1 report to {out_file.absolute()}]")


if __name__ == "__main__":
    main()
