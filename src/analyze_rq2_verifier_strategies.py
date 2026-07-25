"""Comprehensive Analyzer for RQ2 (Verifier Prompt Strategies: Direct vs. CoT vs. Rubric).

Generates markdown reports with side-by-side tables, statistical significance tests,
error fate breakdowns, severity stratification, token costs, and paper-ready LaTeX snippets.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
from collections import Counter
import numpy as np
from scipy import stats as sps
import statsmodels.api as sm

def load_traces(dir_path: pathlib.Path, cond: str) -> dict[str, dict]:
    path = dir_path / f"{cond}.jsonl"
    out = {}
    if not path.exists():
        return out
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        t = json.loads(line)
        out[t["problem_id"]] = t
    return out

def bootstrap_ci(flags: list[int], n_boot: int = 10_000, seed: int = 0):
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    stats_ = sorted(sum(rng.choices(flags, k=n)) / n for _ in range(n_boot))
    return stats_[int(0.025 * n_boot)], stats_[int(0.975 * n_boot)]

def wilson_interval(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return max(0.0, centre - half), min(1.0, centre + half)

def mcnemar_exact(a: dict, b: dict):
    ids = sorted(set(a) & set(b))
    n01 = sum((not a[i]["extra"]["correct"]) and b[i]["extra"]["correct"] for i in ids)
    n10 = sum(a[i]["extra"]["correct"] and (not b[i]["extra"]["correct"]) for i in ids)
    n = n01 + n10
    p = sps.binomtest(min(n01, n10), n, 0.5).pvalue if n > 0 else 1.0
    return {"n_pairs": len(ids), "n01_B_better": n01, "n10_A_better": n10, "p_value": float(p)}

def holm_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj

def compute_error_fate(injected: dict, clean: dict):
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
            
    total = len(ids)
    if has_verifier:
        prop = fates["silently_propagated"] + fates["caught_not_corrected"]
    else:
        prop = fates["propagated"]
        
    plo, phi = wilson_interval(prop, total) if total else (0.0, 0.0)
    
    severity_rates = {}
    for sev in ["mild", "moderate", "severe"]:
        tot_sev = severity_counts[sev]
        if tot_sev > 0:
            pr_sev = severity_propagated[sev]
            severity_rates[sev] = (pr_sev, tot_sev, pr_sev / tot_sev)
            
    out = {
        "n_valid": total,
        "propagation_count": prop,
        "propagation_rate": prop / total if total else 0.0,
        "propagation_ci": (round(plo, 3), round(phi, 3)),
        "absorbed_without_flag": fates.get("absorbed_without_flag", fates.get("absorbed", 0)),
        "caught_and_corrected": fates.get("caught_and_corrected", 0),
        "silently_propagated": fates.get("silently_propagated", fates.get("propagated", 0)),
        "caught_not_corrected": fates.get("caught_not_corrected", 0),
        "severity_rates": severity_rates,
        "type_counts": type_counts
    }
    
    if has_verifier:
        caught = fates["caught_and_corrected"] + fates["caught_not_corrected"]
        clo, chi = wilson_interval(caught, total) if total else (0.0, 0.0)
        out["catch_count"] = caught
        out["catch_rate"] = caught / total if total else 0.0
        out["catch_ci"] = (round(clo, 3), round(chi, 3))
        if caught:
            rlo, rhi = wilson_interval(fates["caught_and_corrected"], caught)
            out["correction_rate"] = fates["caught_and_corrected"] / caught
            out["correction_ci"] = (round(rlo, 3), round(rhi, 3))
        else:
            out["correction_rate"] = 0.0
            out["correction_ci"] = (0.0, 0.0)
            
    return out

def compute_logit(data: dict):
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

def compute_tokens(data: dict):
    out = {}
    for cond, tdict in data.items():
        if not tdict:
            continue
        tot = 0
        ver_tot = 0
        n_solved = 0
        for t in tdict.values():
            usage = t.get("usage") or {}
            c_tot = sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in usage.values() if isinstance(u, dict))
            tot += c_tot
            if "verifier" in usage and isinstance(usage["verifier"], dict):
                ver_tot += usage["verifier"].get("input_tokens", 0) + usage["verifier"].get("output_tokens", 0)
            if t.get("extra", {}).get("correct"):
                n_solved += 1
        out[cond] = {
            "total_tokens": tot,
            "verifier_tokens": ver_tot,
            "avg_per_problem": tot / len(tdict) if tdict else 0,
            "tokens_per_solved": tot / n_solved if n_solved else 0
        }
    return out

def build_model_report(model_name: str, base_dir_map: dict[str, pathlib.Path]):
    conds = ["A", "B", "C1", "C2", "D1", "D2"]
    
    # Load all datasets
    data = {}
    for strat, dpath in base_dir_map.items():
        data[strat] = {}
        for c in conds:
            loaded = load_traces(dpath, c)
            # If fallback needed for non-verifier conditions (A, D1, D2) in CoT / Rubric
            if not loaded and strat in ["cot", "rubric"]:
                loaded = load_traces(base_dir_map["direct"], c)
            data[strat][c] = loaded

    lines = []
    lines.append(f"# RQ2 Comprehensive Report: Verifier Prompt Strategies ({model_name})")
    lines.append(f"\nEvaluating **Direct**, **Chain-of-Thought (CoT)**, and **Rubric** prompting strategies on GSM-Hard (n=200).\n")

    # Section 1: Accuracy Summary
    lines.append("## 1. Accuracy & Performance Breakdown")
    lines.append("| Condition | Description | Direct Strategy (95% CI) | CoT Strategy (95% CI) | Rubric Strategy (95% CI) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: |")
    
    desc_map = {
        "A": "Single Agent Baseline",
        "B": "Clean Multi-Agent Pipeline",
        "C1": "Plan Injected (Verifier ON)",
        "C2": "Solver Injected (Verifier ON)",
        "D1": "Plan Injected (Verifier OFF)",
        "D2": "Solver Injected (Verifier OFF)"
    }
    
    for c in conds:
        row = [f"**{c}**", desc_map[c]]
        for strat in ["direct", "cot", "rubric"]:
            tdict = data[strat][c]
            if tdict:
                flags = [int(t["extra"]["correct"]) for t in tdict.values()]
                acc = sum(flags) / len(flags)
                lo, hi = bootstrap_ci(flags)
                row.append(f"{acc:.3f} [{lo:.3f}, {hi:.3f}]")
            else:
                row.append("N/A")
        lines.append("| " + " | ".join(row) + " |")

    # Section 2: McNemar Statistical Significance
    lines.append("\n## 2. McNemar Exact Paired Significance Tests (Holm-Bonferroni Adjusted)")
    lines.append("| Comparison Contrast | Metric Evaluated | Direct ($p_{holm}$) | CoT ($p_{holm}$) | Rubric ($p_{holm}$) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: |")
    
    contrasts = [
        ("A:B", "Single vs. Clean Pipeline"),
        ("B:C1", "Clean vs. Plan Sabotage"),
        ("C1:D1", "Plan Protection (Verifier Impact)"),
        ("C2:D2", "Solver Protection (Verifier Impact)")
    ]
    
    for pair, pair_desc in contrasts:
        x, y = pair.split(":")
        row = [f"**{pair}**", pair_desc]
        for strat in ["direct", "cot", "rubric"]:
            m_res = mcnemar_exact(data[strat][x], data[strat][y])
            p = m_res["p_value"]
            # We adjust across 4 contrasts per strategy
            all_p = [mcnemar_exact(data[strat][cx], data[strat][cy])["p_value"] for cx, cy in [c[0].split(":") for c in contrasts]]
            adj = holm_adjust(all_p)
            pair_idx = [c[0] for c in contrasts].index(pair)
            p_adj = adj[pair_idx]
            n01 = m_res["n01_B_better"]
            n10 = m_res["n10_A_better"]
            row.append(f"{p_adj:.4f} (+$n_{{01}}$={n01}, -$n_{{10}}$={n10})")
        lines.append("| " + " | ".join(row) + " |")

    # Section 3: Error Fate Metrics
    lines.append("\n## 3. Error Fate & Defense Dynamics")
    lines.append("### A. Plan Injected Condition (C1)")
    lines.append("| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |")
    lines.append("| :--- | :---: | :---: | :---: |")
    
    fate_c1 = {s: compute_error_fate(data[s]["C1"], data[s]["B"]) for s in ["direct", "cot", "rubric"]}
    
    lines.append(f"| Valid Injections ($n$) | {fate_c1['direct']['n_valid']} | {fate_c1['cot']['n_valid']} | {fate_c1['rubric']['n_valid']} |")
    lines.append(f"| **Propagation Rate** | {fate_c1['direct']['propagation_rate']*100:.1f}% | {fate_c1['cot']['propagation_rate']*100:.1f}% | {fate_c1['rubric']['propagation_rate']*100:.1f}% |")
    lines.append(f"| **Catch Rate** | {fate_c1['direct']['catch_rate']*100:.1f}% | {fate_c1['cot']['catch_rate']*100:.1f}% | {fate_c1['rubric']['catch_rate']*100:.1f}% |")
    lines.append(f"| **Correction Rate** | {fate_c1['direct']['correction_rate']*100:.1f}% | {fate_c1['cot']['correction_rate']*100:.1f}% | {fate_c1['rubric']['correction_rate']*100:.1f}% |")
    lines.append(f"| Natural Absorption (No Flag) | {fate_c1['direct']['absorbed_without_flag']} | {fate_c1['cot']['absorbed_without_flag']} | {fate_c1['rubric']['absorbed_without_flag']} |")
    lines.append(f"| Caught & Corrected | {fate_c1['direct']['caught_and_corrected']} | {fate_c1['cot']['caught_and_corrected']} | {fate_c1['rubric']['caught_and_corrected']} |")
    lines.append(f"| Caught but Not Corrected | {fate_c1['direct']['caught_not_corrected']} | {fate_c1['cot']['caught_not_corrected']} | {fate_c1['rubric']['caught_not_corrected']} |")

    lines.append("\n### B. Solver Injected Condition (C2)")
    lines.append("| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |")
    lines.append("| :--- | :---: | :---: | :---: |")
    
    fate_c2 = {s: compute_error_fate(data[s]["C2"], data[s]["B"]) for s in ["direct", "cot", "rubric"]}
    
    lines.append(f"| Valid Injections ($n$) | {fate_c2['direct']['n_valid']} | {fate_c2['cot']['n_valid']} | {fate_c2['rubric']['n_valid']} |")
    lines.append(f"| **Propagation Rate** | {fate_c2['direct']['propagation_rate']*100:.1f}% | {fate_c2['cot']['propagation_rate']*100:.1f}% | {fate_c2['rubric']['propagation_rate']*100:.1f}% |")
    lines.append(f"| **Catch Rate** | {fate_c2['direct']['catch_rate']*100:.1f}% | {fate_c2['cot']['catch_rate']*100:.1f}% | {fate_c2['rubric']['catch_rate']*100:.1f}% |")
    lines.append(f"| **Correction Rate** | {fate_c2['direct']['correction_rate']*100:.1f}% | {fate_c2['cot']['correction_rate']*100:.1f}% | {fate_c2['rubric']['correction_rate']*100:.1f}% |")
    lines.append(f"| Natural Absorption (No Flag) | {fate_c2['direct']['absorbed_without_flag']} | {fate_c2['cot']['absorbed_without_flag']} | {fate_c2['rubric']['absorbed_without_flag']} |")
    lines.append(f"| Caught & Corrected | {fate_c2['direct']['caught_and_corrected']} | {fate_c2['cot']['caught_and_corrected']} | {fate_c2['rubric']['caught_and_corrected']} |")
    lines.append(f"| Caught but Not Corrected | {fate_c2['direct']['caught_not_corrected']} | {fate_c2['cot']['caught_not_corrected']} | {fate_c2['rubric']['caught_not_corrected']} |")

    # Section 4: Severity Breakdown
    lines.append("\n## 4. Severity Propagation Comparison (Number Swaps)")
    lines.append("| Severity Level | Condition | Direct Strategy | CoT Strategy | Rubric Strategy |")
    lines.append("| :--- | :--- | :---: | :---: | :---: |")
    
    for sev in ["mild", "moderate", "severe"]:
        for cond_name, fate_dict in [("C1 (Plan)", fate_c1), ("C2 (Solver)", fate_c2)]:
            row = [f"**{sev.capitalize()}**", cond_name]
            for strat in ["direct", "cot", "rubric"]:
                sdata = fate_dict[strat]["severity_rates"].get(sev)
                if sdata:
                    c_p, c_tot, rate = sdata
                    row.append(f"{c_p}/{c_tot} ({rate*100:.1f}%)")
                else:
                    row.append("N/A")
            lines.append("| " + " | ".join(row) + " |")

    # Section 5: Token Overhead & Cost Analysis
    lines.append("\n## 5. Cost & Token Efficiency Analysis")
    lines.append("| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |")
    lines.append("| :--- | :---: | :---: | :---: |")
    
    tokens_c2 = {s: compute_tokens(data[s])["C2"] for s in ["direct", "cot", "rubric"]}
    lines.append(f"| Total Pipeline Tokens (C2) | {tokens_c2['direct']['total_tokens']:,} | {tokens_c2['cot']['total_tokens']:,} | {tokens_c2['rubric']['total_tokens']:,} |")
    lines.append(f"| Verifier Stage Tokens (C2) | {tokens_c2['direct']['verifier_tokens']:,} | {tokens_c2['cot']['verifier_tokens']:,} | {tokens_c2['rubric']['verifier_tokens']:,} |")
    lines.append(f"| Avg Tokens / Problem | {tokens_c2['direct']['avg_per_problem']:.1f} | {tokens_c2['cot']['avg_per_problem']:.1f} | {tokens_c2['rubric']['avg_per_problem']:.1f} |")
    lines.append(f"| Tokens / Solved Problem | {tokens_c2['direct']['tokens_per_solved']:.1f} | {tokens_c2['cot']['tokens_per_solved']:.1f} | {tokens_c2['rubric']['tokens_per_solved']:.1f} |")

    # Section 6: Logistic Regression Odds Ratios (H2)
    lines.append("\n## 6. Logistic Regression Odds Ratios (H2 Survival Factors)")
    lines.append("| Predictor Variable | Direct OR [95% CI] (p-val) | CoT OR [95% CI] (p-val) | Rubric OR [95% CI] (p-val) |")
    report_logits = {s: compute_logit(data[s]) for s in ["direct", "cot", "rubric"]}
    lines.append("| :--- | :---: | :---: | :---: |")
    
    for var in ["early_stage", "operation_flip", "semantic_logic_error"]:
        row = [f"**{var}**"]
        for strat in ["direct", "cot", "rubric"]:
            l_fit = report_logits[strat]
            if l_fit and var in l_fit:
                or_val = l_fit[var]["OR"]
                lo, hi = l_fit[var]["CI"]
                pval = l_fit[var]["p"]
                row.append(f"{or_val:.2f} [{lo:.2f}, {hi:.2f}] (p={pval:.4f})")
            else:
                row.append("N/A")
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)

def main():
    # Folder mappings
    claude_dirs = {
        "direct": pathlib.Path("results/traces"),
        "cot": pathlib.Path("results/traces_cot"),
        "rubric": pathlib.Path("results/traces_rubric")
    }
    
    qwen_dirs = {
        "direct": pathlib.Path("results/traces_replication_qwen25"),
        "cot": pathlib.Path("results/traces_replication_qwen25_cot"),
        "rubric": pathlib.Path("results/traces_replication_qwen25_rubric")
    }
    
    claude_report = build_model_report("Claude Sonnet 4.6", claude_dirs)
    qwen_report = build_model_report("Qwen 2.5 72B Instruct", qwen_dirs)
    
    full_md = f"# RQ2 Master Report: Verifier Prompting Strategies\n\n{claude_report}\n\n---\n\n{qwen_report}"
    
    # Print directly to terminal for instant viewing & piping
    print("\n" + "="*80)
    print(full_md)
    print("="*80 + "\n")
    
    out_file = pathlib.Path("results/rq2_verifier_strategies_report.md")
    out_file.write_text(full_md, encoding="utf-8")
    txt_file = pathlib.Path("results/rq2_verifier_strategies_report.txt")
    txt_file.write_text(full_md, encoding="utf-8")
    print(f"Success! Master RQ2 report saved to: {out_file.absolute()} and {txt_file.absolute()}")

if __name__ == "__main__":
    main()
