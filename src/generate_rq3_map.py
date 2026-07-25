"""Generator for RQ3 (The Master Error Map).

Synthesizes data across Injection Stages (Decomposer vs. Solver), Verifier Presence
(Active vs. Ablated), Error Types (number_swap, operation_flip, semantic_logic_error),
Severities (mild, moderate, severe), and Strategies (Direct, CoT, Rubric).

Outputs formatted tables directly to terminal and saves to results/rq3_map_report.txt (and .md).
"""
from __future__ import annotations

import json
import math
import pathlib

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

def build_rq3_map(model_name: str, base_dir_map: dict[str, pathlib.Path]):
    conds = ["A", "B", "C1", "C2", "D1", "D2"]
    data = {}
    for strat, dpath in base_dir_map.items():
        data[strat] = {}
        for c in conds:
            loaded = load_traces(dpath, c)
            if not loaded and strat in ["cot", "rubric"]:
                loaded = load_traces(base_dir_map["direct"], c)
            data[strat][c] = loaded

    lines = []
    lines.append(f"# RQ3 Master Causal Error Map ({model_name})")
    lines.append("\nSynthesizing interaction between Injection Stage, Verifier Ablation, Error Type, Severity, and Verifier Strategy.\n")

    # Section 1: Error Type Matrix
    lines.append("## 1. Causal Error Defense Matrix by Error Type")
    lines.append("| Error Type | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % (No Verifier) | Causal Verifier Defense ($\Delta_{Direct}$) | Causal Verifier Defense ($\Delta_{CoT}$) | Causal Verifier Defense ($\Delta_{Rubric}$) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    error_types = ["number_swap", "operation_flip", "semantic_logic_error"]
    
    for etype in error_types:
        for stage, c_cond, d_cond in [("Decomposer (Plan)", "C1", "D1"), ("Solver (Execution)", "C2", "D2")]:
            row = [f"**{etype}**", stage]
            
            # Baseline ablated rate (D1 or D2)
            d_tdict = data["direct"][d_cond]
            b_tdict = data["direct"]["B"]
            valid_d = [i for i in d_tdict if d_tdict[i].get("injection_meta", {}).get("type") == etype and i in b_tdict and b_tdict[i]["extra"]["correct"]]
            d_prop = sum(1 for i in valid_d if not d_tdict[i]["extra"]["correct"])
            d_rate = d_prop / len(valid_d) if valid_d else 0.0
            
            strat_rates = {}
            for strat in ["direct", "cot", "rubric"]:
                c_tdict = data[strat][c_cond]
                cb_tdict = data[strat]["B"]
                valid_c = [i for i in c_tdict if c_tdict[i].get("injection_meta", {}).get("type") == etype and i in cb_tdict and cb_tdict[i]["extra"]["correct"]]
                c_prop = sum(1 for i in valid_c if not c_tdict[i]["extra"]["correct"])
                c_rate = c_prop / len(valid_c) if valid_c else 0.0
                strat_rates[strat] = c_rate
                row.append(f"{c_rate*100:.1f}% ({c_prop}/{len(valid_c)})")
                
            row.append(f"{d_rate*100:.1f}% ({d_prop}/{len(valid_d)})")
            
            # Causal deltas
            for strat in ["direct", "cot", "rubric"]:
                delta = d_rate - strat_rates[strat]
                row.append(f"**+{delta*100:.1f}%**" if delta > 0 else f"{delta*100:.1f}%")
                
            lines.append("| " + " | ".join(row) + " |")

    # Section 2: Severity Map
    lines.append("\n## 2. Severity-Stratified Causal Defense Map (Number Swaps)")
    lines.append("| Severity Level | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % | Causal Defense ($\Delta_{CoT}$) | Causal Defense ($\Delta_{Rubric}$) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for sev in ["mild", "moderate", "severe"]:
        for stage, c_cond, d_cond in [("Decomposer (Plan)", "C1", "D1"), ("Solver (Execution)", "C2", "D2")]:
            row = [f"**{sev.capitalize()}**", stage]
            
            d_tdict = data["direct"][d_cond]
            b_tdict = data["direct"]["B"]
            valid_d = [i for i in d_tdict if d_tdict[i].get("injection_meta", {}).get("type") == "number_swap" and d_tdict[i].get("injection_meta", {}).get("severity") == sev and i in b_tdict and b_tdict[i]["extra"]["correct"]]
            d_prop = sum(1 for i in valid_d if not d_tdict[i]["extra"]["correct"])
            d_rate = d_prop / len(valid_d) if valid_d else 0.0
            
            strat_rates = {}
            for strat in ["direct", "cot", "rubric"]:
                c_tdict = data[strat][c_cond]
                cb_tdict = data[strat]["B"]
                valid_c = [i for i in c_tdict if c_tdict[i].get("injection_meta", {}).get("type") == "number_swap" and c_tdict[i].get("injection_meta", {}).get("severity") == sev and i in cb_tdict and cb_tdict[i]["extra"]["correct"]]
                c_prop = sum(1 for i in valid_c if not c_tdict[i]["extra"]["correct"])
                c_rate = c_prop / len(valid_c) if valid_c else 0.0
                strat_rates[strat] = c_rate
                row.append(f"{c_rate*100:.1f}% ({c_prop}/{len(valid_c)})")
                
            row.append(f"{d_rate*100:.1f}% ({d_prop}/{len(valid_d)})")
            
            for strat in ["cot", "rubric"]:
                delta = d_rate - strat_rates[strat]
                row.append(f"**+{delta*100:.1f}%**" if delta > 0 else f"{delta*100:.1f}%")
                
            lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)

def main():
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
    
    c_map = build_rq3_map("Claude Sonnet 4.6", claude_dirs)
    q_map = build_rq3_map("Qwen 2.5 72B Instruct", qwen_dirs)
    
    full_md = f"# RQ3 Master Error Map Report\n\n{c_map}\n\n---\n\n{q_map}"
    
    # Print to terminal
    print("\n" + "="*80)
    print(full_md)
    print("="*80 + "\n")
    
    # Save to file (overwriting old text file)
    txt_file = pathlib.Path("results/rq3_map_report.txt")
    txt_file.write_text(full_md, encoding="utf-8")
    md_file = pathlib.Path("results/rq3_map_report.md")
    md_file.write_text(full_md, encoding="utf-8")
    print(f"Success! Master RQ3 map report saved to: {txt_file.absolute()} and {md_file.absolute()}")

if __name__ == "__main__":
    main()
