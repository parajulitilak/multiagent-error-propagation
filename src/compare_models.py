"""Generate a comparative report comparing Claude (traces) and Qwen (traces_replication_qwen25).

Usage:
    python -m src.compare_models
"""
from __future__ import annotations

import json
import math
import pathlib
import random
from collections import Counter
from scipy import stats as sps
import numpy as np

def load(traces_dir: pathlib.Path, cond: str) -> dict[str, dict]:
    path = traces_dir / f"{cond}.jsonl"
    out = {}
    if not path.exists():
        return out
    for line in open(path):
        t = json.loads(line)
        out[t["problem_id"]] = t
    return out

def bootstrap_ci(flags: list[int], n_boot: int = 10_000, seed: int = 0):
    rng = random.Random(seed)
    n = len(flags)
    stats_ = sorted(sum(rng.choices(flags, k=n)) / n for _ in range(n_boot))
    return stats_[int(0.025 * n_boot)], stats_[int(0.975 * n_boot)]

def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return centre - half, centre + half

def mcnemar_exact(a: dict, b: dict):
    ids = sorted(set(a) & set(b))
    n01 = sum((not a[i]["extra"]["correct"]) and b[i]["extra"]["correct"] for i in ids)
    n10 = sum(a[i]["extra"]["correct"] and (not b[i]["extra"]["correct"]) for i in ids)
    n = n01 + n10
    p = sps.binomtest(min(n01, n10), n, 0.5).pvalue if n > 0 else 1.0
    return {"n_pairs": len(ids), "n01_B_better": n01, "n10_A_better": n10, "p_value": float(p)}

def holm(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj

def get_error_fate_stats(injected: dict, clean: dict):
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
            
    out = {
        "total_injections": total,
        "propagation_rate": prop / total if total else 0.0,
        "propagation_ci": (round(lo, 3), round(hi, 3)),
        "absorbed_without_flag": fates.get("absorbed_without_flag", fates.get("absorbed", 0)),
        "caught_and_corrected": fates.get("caught_and_corrected", 0),
        "silently_propagated": fates.get("silently_propagated", fates.get("propagated", 0)),
        "caught_not_corrected": fates.get("caught_not_corrected", 0),
        "severity_propagation": severity_rates,
        "type_freq": type_freq
    }
    
    if has_verifier:
        caught = fates["caught_and_corrected"] + fates["caught_not_corrected"]
        clo, chi = wilson(caught, total) if total else (0, 0)
        out["catch_rate"] = caught / total if total else 0.0
        out["catch_ci"] = (round(clo, 3), round(chi, 3))
        if caught:
            rlo, rhi = wilson(fates["caught_and_corrected"], caught)
            out["correction_rate"] = fates["caught_and_corrected"] / caught
            out["correction_ci"] = (round(rlo, 3), round(rhi, 3))
        else:
            out["correction_rate"] = 0.0
            out["correction_ci"] = (0.0, 0.0)
    return out

def get_logit_coefs(data: dict):
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
        return None
    y = np.array([r[0] for r in rows], dtype=float)
    X = sm.add_constant(np.array([r[1:] for r in rows], dtype=float))
    try:
        fit = sm.Logit(y, X).fit(disp=0)
        ors = np.exp(fit.params)
        cis = np.exp(fit.conf_int())
        pvals = fit.pvalues
        names = ["intercept", "early_stage", "operation_flip", "semantic_logic_error"]
        out = {}
        for name, o, (lo, hi), p in zip(names, ors, cis, pvals):
            out[name] = {"OR": o, "CI": (lo, hi), "p": p}
        return out
    except Exception:
        return None

def main():
    claude_dir = pathlib.Path("results/traces")
    qwen_dir = pathlib.Path("results/traces_replication_qwen25")
    
    conds = ["A", "B", "C1", "C2", "D1", "D2"]
    claude_data = {c: load(claude_dir, c) for c in conds if load(claude_dir, c)}
    qwen_data = {c: load(qwen_dir, c) for c in conds if load(qwen_dir, c)}
    
    report = []
    report.append("# Model Comparison Report: Claude Sonnet vs. Qwen 2.5 72B")
    report.append("\nBoth models evaluated on the **GSM-Hard** dataset (n=200, seed=42).\n")
    
    # 1. Accuracies Table
    report.append("## 1. Accuracy Summary (with 95% Bootstrap CI)")
    report.append("| Condition | Claude Sonnet Accuracy (95% CI) | Qwen 2.5 72B Accuracy (95% CI) |")
    report.append("| :--- | :---: | :---: |")
    for c in conds:
        c_acc, q_acc = "N/A", "N/A"
        if c in claude_data:
            flags = [int(t["extra"]["correct"]) for t in claude_data[c].values()]
            acc = sum(flags) / len(flags)
            lo, hi = bootstrap_ci(flags)
            c_acc = f"{acc:.3f} [{lo:.3f}, {hi:.3f}]"
        if c in qwen_data:
            flags = [int(t["extra"]["correct"]) for t in qwen_data[c].values()]
            acc = sum(flags) / len(flags)
            lo, hi = bootstrap_ci(flags)
            q_acc = f"{acc:.3f} [{lo:.3f}, {hi:.3f}]"
        report.append(f"| **{c}** | {c_acc} | {q_acc} |")
        
    # 2. McNemar Tests
    report.append("\n## 2. McNemar Exact Paired Significance Tests")
    report.append("| Comparison | Claude p-value (Holm) | Qwen 2.5 p-value (Holm) |")
    report.append("| :--- | :---: | :---: |")
    pairs = ["A:B", "B:C1", "C1:D1", "C2:D2"]
    claude_pvals, qwen_pvals = [], []
    for pair in pairs:
        x, y = pair.split(":")
        if x in claude_data and y in claude_data:
            claude_pvals.append(mcnemar_exact(claude_data[x], claude_data[y])["p_value"])
        else:
            claude_pvals.append(1.0)
        if x in qwen_data and y in qwen_data:
            qwen_pvals.append(mcnemar_exact(qwen_data[x], qwen_data[y])["p_value"])
        else:
            qwen_pvals.append(1.0)
            
    claude_adj = holm(claude_pvals)
    qwen_adj = holm(qwen_pvals)
    
    for i, pair in enumerate(pairs):
        report.append(f"| **{pair}** | {claude_adj[i]:.4f} | {qwen_adj[i]:.4f} |")
        
    # 3. Error Fate Comparison
    report.append("\n## 3. Error Fate Metrics (C1 vs. C2)")
    report.append("| Metric | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) |")
    report.append("| :--- | :---: | :---: | :---: | :---: |")
    
    c_c1 = get_error_fate_stats(claude_data["C1"], claude_data["B"]) if "C1" in claude_data and "B" in claude_data else {}
    q_c1 = get_error_fate_stats(qwen_data["C1"], qwen_data["B"]) if "C1" in qwen_data and "B" in qwen_data else {}
    c_c2 = get_error_fate_stats(claude_data["C2"], claude_data["B"]) if "C2" in claude_data and "B" in claude_data else {}
    q_c2 = get_error_fate_stats(qwen_data["C2"], qwen_data["B"]) if "C2" in qwen_data and "B" in qwen_data else {}
    
    def get_val(d, k, pct=False):
        if k not in d: return "N/A"
        val = d[k]
        if pct:
            ci = d.get(k.replace("rate", "ci"), (0, 0))
            return f"{val*100:.1f}% [{ci[0]:.3f}, {ci[1]:.3f}]"
        return str(val)
        
    report.append(f"| Valid Injections ($n$) | {get_val(c_c1, 'total_injections')} | {get_val(q_c1, 'total_injections')} | {get_val(c_c2, 'total_injections')} | {get_val(q_c2, 'total_injections')} |")
    report.append(f"| Propagation Rate | {get_val(c_c1, 'propagation_rate', True)} | {get_val(q_c1, 'propagation_rate', True)} | {get_val(c_c2, 'propagation_rate', True)} | {get_val(q_c2, 'propagation_rate', True)} |")
    report.append(f"| Catch Rate | {get_val(c_c1, 'catch_rate', True)} | {get_val(q_c1, 'catch_rate', True)} | {get_val(c_c2, 'catch_rate', True)} | {get_val(q_c2, 'catch_rate', True)} |")
    report.append(f"| Correction Rate | {get_val(c_c1, 'correction_rate', True)} | {get_val(q_c1, 'correction_rate', True)} | {get_val(c_c2, 'correction_rate', True)} | {get_val(q_c2, 'correction_rate', True)} |")
    report.append(f"| Absorbed (No Flag) | {get_val(c_c1, 'absorbed_without_flag')} | {get_val(q_c1, 'absorbed_without_flag')} | {get_val(c_c2, 'absorbed_without_flag')} | {get_val(q_c2, 'absorbed_without_flag')} |")
    report.append(f"| Caught & Corrected | {get_val(c_c1, 'caught_and_corrected')} | {get_val(q_c1, 'caught_and_corrected')} | {get_val(c_c2, 'caught_and_corrected')} | {get_val(q_c2, 'caught_and_corrected')} |")
    
    # 4. Severity Propagation Rates
    report.append("\n## 4. Severity Propagation Rates (Number Swaps only)")
    report.append("| Severity Level | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) | Claude (D2 - No Verifier) | Qwen (D2 - No Verifier) |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    c_d2 = get_error_fate_stats(claude_data["D2"], claude_data["B"]) if "D2" in claude_data and "B" in claude_data else {}
    q_d2 = get_error_fate_stats(qwen_data["D2"], qwen_data["B"]) if "D2" in qwen_data and "B" in qwen_data else {}
    
    for level in ["mild", "moderate", "severe"]:
        r_c_c1 = c_c1.get("severity_propagation", {}).get(level, "N/A")
        r_q_c1 = q_c1.get("severity_propagation", {}).get(level, "N/A")
        r_c_c2 = c_c2.get("severity_propagation", {}).get(level, "N/A")
        r_q_c2 = q_c2.get("severity_propagation", {}).get(level, "N/A")
        r_c_d2 = c_d2.get("severity_propagation", {}).get(level, "N/A")
        r_q_d2 = q_d2.get("severity_propagation", {}).get(level, "N/A")
        report.append(f"| **{level.capitalize()}** | {r_c_c1} | {r_q_c1} | {r_c_c2} | {r_q_c2} | {r_c_d2} | {r_q_d2} |")

    # 5. Odds Ratios logit
    report.append("\n## 5. Fault Survival Logit Odds Ratios (H2)")
    report.append("| Predictor | Claude OR [95% CI] (p-val) | Qwen 2.5 OR [95% CI] (p-val) |")
    report.append("| :--- | :---: | :---: |")
    c_logit = get_logit_coefs(claude_data)
    q_logit = get_logit_coefs(qwen_data)
    for name in ["early_stage", "operation_flip", "semantic_logic_error"]:
        c_str, q_str = "N/A", "N/A"
        if c_logit and name in c_logit:
            c_str = f"{c_logit[name]['OR']:.2f} [{c_logit[name]['CI'][0]:.2f}, {c_logit[name]['CI'][1]:.2f}] (p={c_logit[name]['p']:.4f})"
        if q_logit and name in q_logit:
            q_str = f"{q_logit[name]['OR']:.2f} [{q_logit[name]['CI'][0]:.2f}, {q_logit[name]['CI'][1]:.2f}] (p={q_logit[name]['p']:.4f})"
        report.append(f"| **{name}** | {c_str} | {q_str} |")
        
    out_md = "\n".join(report)
    out_path = pathlib.Path("results/model_comparison_report.md")
    out_path.write_text(out_md, encoding="utf-8")
    txt_path = pathlib.Path("results/model_comparison_report.txt")
    txt_path.write_text(out_md, encoding="utf-8")
    print(f"\nSuccess! Comparison report generated at: {out_path.absolute()} and {txt_path.absolute()}")

if __name__ == "__main__":
    main()
