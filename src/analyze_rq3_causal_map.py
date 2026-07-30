"""RQ3 analyzer: causal verifier map.

Research Question 3 (The Map):
How do injection stage (Decomposer vs Solver) and the presence of a verifier
(ablation) interact with error type, severity, and verifier strategy to
determine catch rates? A full map is produced identifying which verifier
catches which error, where it was injected, how severe it was, and isolating
the causal contribution of the verification stage.

This script generates:
1. Error-type x stage x strategy map
2. Number-swap severity x stage x strategy map
3. Best-verifier summary (who catches what best)
4. Causal verifier defense deltas from ablation
5. Separate Claude and Qwen sections

Outputs:
- results/rq3_map_report.md
- results/rq3_map_report.txt
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.runner import normalize


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONDS = ["A", "B", "C1", "C2", "D1", "D2"]
STRATEGIES = ["direct", "cot", "rubric"]
ERROR_TYPES = ["number_swap", "operation_flip", "semantic_logic_error"]
SEVERITIES = ["mild", "moderate", "severe"]

STAGE_MAP = {
    "C1": "Decomposer (Plan)",
    "D1": "Decomposer (Plan)",
    "C2": "Solver (Execution)",
    "D2": "Solver (Execution)",
}

VERIFIER_ON_OFF = {
    "C1": "D1",
    "C2": "D2",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SubgroupMetrics:
    n: int
    propagation_count: int
    propagation_rate: Optional[float]
    catch_count: Optional[int]
    catch_rate: Optional[float]
    correction_count: Optional[int]
    correction_rate: Optional[float]
    absorbed_count: int
    caught_not_corrected: Optional[int]

    def propagation_str(self) -> str:
        if self.n == 0 or self.propagation_rate is None:
            return "N/A"
        return f"{self.propagation_rate * 100:.1f}% ({self.propagation_count}/{self.n})"

    def catch_str(self) -> str:
        if self.n == 0 or self.catch_rate is None or self.catch_count is None:
            return "N/A"
        return f"{self.catch_rate * 100:.1f}% ({self.catch_count}/{self.n})"

    def correction_str(self) -> str:
        if self.correction_rate is None or self.correction_count is None or self.catch_count is None:
            return "N/A"
        if self.catch_count == 0:
            return "0.0% (0/0)"
        return f"{self.correction_rate * 100:.1f}% ({self.correction_count}/{self.catch_count})"


# ---------------------------------------------------------------------------
# Loading / scoring helpers
# ---------------------------------------------------------------------------

def load_traces(dir_path: pathlib.Path, cond: str) -> dict[str, dict]:
    """Load one condition file and re-score correctness with the canonical scorer."""
    path = dir_path / f"{cond}.jsonl"
    out: dict[str, dict] = {}
    if not path.exists():
        return out

    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        t = json.loads(line)
        t.setdefault("extra", {})["correct"] = (
            normalize(t.get("final_answer")) == normalize(t.get("gold"))
        )
        out[t["problem_id"]] = t
    return out


def load_strategy_bundle(base_dir_map: dict[str, pathlib.Path]) -> dict[str, dict[str, dict]]:
    """Load direct / cot / rubric traces.

    For non-verifier conditions A/D1/D2, CoT and Rubric folders may not contain
    separate copies. In that case, fall back to the direct folder, matching the
    current repo pattern already used for RQ2.
    """
    data: dict[str, dict[str, dict]] = {}
    for strategy, dpath in base_dir_map.items():
        data[strategy] = {}
        for cond in CONDS:
            loaded = load_traces(dpath, cond)
            if not loaded and strategy in {"cot", "rubric"} and cond in {"A", "D1", "D2"}:
                loaded = load_traces(base_dir_map["direct"], cond)
            data[strategy][cond] = loaded
    return data


# ---------------------------------------------------------------------------
# Subgroup selection
# ---------------------------------------------------------------------------

def valid_ids(injected: dict[str, dict], clean_b: dict[str, dict]) -> list[str]:
    """Injected problems where the injection actually applied and clean B was correct."""
    ids = []
    for pid, t in injected.items():
        meta = t.get("injection_meta") or {}
        clean_t = clean_b.get(pid)
        if meta.get("applied") and clean_t and clean_t.get("extra", {}).get("correct"):
            ids.append(pid)
    return ids


def subgroup_ids(
    injected: dict[str, dict],
    clean_b: dict[str, dict],
    error_type: str | None = None,
    severity: str | None = None,
) -> list[str]:
    ids = valid_ids(injected, clean_b)
    out = []
    for pid in ids:
        meta = injected[pid].get("injection_meta") or {}

        if error_type is not None and meta.get("type") != error_type:
            continue
        if severity is not None and meta.get("severity") != severity:
            continue

        out.append(pid)
    return out


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def compute_metrics_for_ids(
    traces: dict[str, dict],
    ids: list[str],
    has_verifier: bool,
) -> SubgroupMetrics:
    """Compute propagation / catch / correction for a fixed subgroup."""
    n = len(ids)
    if n == 0:
        return SubgroupMetrics(
            n=0,
            propagation_count=0,
            propagation_rate=None,
            catch_count=None if not has_verifier else 0,
            catch_rate=None,
            correction_count=None if not has_verifier else 0,
            correction_rate=None,
            absorbed_count=0,
            caught_not_corrected=None if not has_verifier else 0,
        )

    propagation_count = 0
    catch_count = 0
    correction_count = 0
    absorbed_count = 0
    caught_not_corrected = 0

    for pid in ids:
        t = traces[pid]
        correct = bool(t.get("extra", {}).get("correct"))

        if not has_verifier:
            if correct:
                absorbed_count += 1
            else:
                propagation_count += 1
            continue

        caught = t.get("verifier_verdict") == "REJECT"

        if caught:
            catch_count += 1
            if correct:
                correction_count += 1
            else:
                propagation_count += 1
                caught_not_corrected += 1
        else:
            if correct:
                absorbed_count += 1
            else:
                propagation_count += 1

    return SubgroupMetrics(
        n=n,
        propagation_count=propagation_count,
        propagation_rate=(propagation_count / n),
        catch_count=catch_count if has_verifier else None,
        catch_rate=(catch_count / n) if has_verifier else None,
        correction_count=correction_count if has_verifier else None,
        correction_rate=((correction_count / catch_count) if has_verifier and catch_count else 0.0) if has_verifier else None,
        absorbed_count=absorbed_count,
        caught_not_corrected=caught_not_corrected if has_verifier else None,
    )


def defense_delta_str(ablation_metrics: SubgroupMetrics, verifier_metrics: SubgroupMetrics) -> str:
    """Positive means verifier reduced propagation relative to ablation."""
    if ablation_metrics.propagation_rate is None or verifier_metrics.propagation_rate is None:
        return "N/A"
    delta = ablation_metrics.propagation_rate - verifier_metrics.propagation_rate
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta * 100:.1f}%"


# ---------------------------------------------------------------------------
# RQ3 maps
# ---------------------------------------------------------------------------

def compute_error_type_stage_map(strategy_data: dict[str, dict[str, dict]]) -> list[dict]:
    rows = []

    for error_type in ERROR_TYPES:
        for on_cond, off_cond in VERIFIER_ON_OFF.items():
            stage = STAGE_MAP[on_cond]
            per_strategy = {}

            for strategy in STRATEGIES:
                clean_b = strategy_data[strategy]["B"]

                on_ids = subgroup_ids(
                    strategy_data[strategy][on_cond],
                    clean_b,
                    error_type=error_type,
                )
                off_ids = subgroup_ids(
                    strategy_data[strategy][off_cond],
                    clean_b,
                    error_type=error_type,
                )

                on_metrics = compute_metrics_for_ids(strategy_data[strategy][on_cond], on_ids, has_verifier=True)
                off_metrics = compute_metrics_for_ids(strategy_data[strategy][off_cond], off_ids, has_verifier=False)

                per_strategy[strategy] = {
                    "on": on_metrics,
                    "off": off_metrics,
                }

            rows.append({
                "kind": "type",
                "label": error_type,
                "stage": stage,
                "per_strategy": per_strategy,
            })

    return rows


def compute_severity_stage_map(strategy_data: dict[str, dict[str, dict]]) -> list[dict]:
    rows = []

    for severity in SEVERITIES:
        for on_cond, off_cond in VERIFIER_ON_OFF.items():
            stage = STAGE_MAP[on_cond]
            per_strategy = {}

            for strategy in STRATEGIES:
                clean_b = strategy_data[strategy]["B"]

                on_ids = subgroup_ids(
                    strategy_data[strategy][on_cond],
                    clean_b,
                    error_type="number_swap",
                    severity=severity,
                )
                off_ids = subgroup_ids(
                    strategy_data[strategy][off_cond],
                    clean_b,
                    error_type="number_swap",
                    severity=severity,
                )

                on_metrics = compute_metrics_for_ids(strategy_data[strategy][on_cond], on_ids, has_verifier=True)
                off_metrics = compute_metrics_for_ids(strategy_data[strategy][off_cond], off_ids, has_verifier=False)

                per_strategy[strategy] = {
                    "on": on_metrics,
                    "off": off_metrics,
                }

            rows.append({
                "kind": "severity",
                "label": severity,
                "stage": stage,
                "per_strategy": per_strategy,
            })

    return rows


# ---------------------------------------------------------------------------
# Strategy ranking helpers
# ---------------------------------------------------------------------------

def best_strategy_for_metric(row: dict, metric: str) -> str:
    """Choose best verifier strategy for a row.

    metric:
    - 'catch_rate' -> higher is better
    - 'correction_rate' -> higher is better
    - 'propagation_rate' -> lower is better
    """
    candidates = []
    for strategy in STRATEGIES:
        metrics = row["per_strategy"][strategy]["on"]
        value = getattr(metrics, metric)
        if value is None:
            continue
        candidates.append((strategy, value))

    if not candidates:
        return "N/A"

    if metric == "propagation_rate":
        return min(candidates, key=lambda x: x[1])[0]
    return max(candidates, key=lambda x: x[1])[0]


def build_winner_summary(rows: list[dict]) -> Counter:
    wins = Counter()
    for row in rows:
        wins[f"catch::{best_strategy_for_metric(row, 'catch_rate')}"] += 1
        wins[f"correction::{best_strategy_for_metric(row, 'correction_rate')}"] += 1
        wins[f"lowest_propagation::{best_strategy_for_metric(row, 'propagation_rate')}"] += 1
    return wins


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_error_type_stage_table(rows: list[dict]) -> list[str]:
    lines = []
    lines.append("## 1. Causal Error Defense Matrix by Error Type")
    lines.append("| Error Type | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for row in rows:
        d_on = row["per_strategy"]["direct"]["on"]
        c_on = row["per_strategy"]["cot"]["on"]
        r_on = row["per_strategy"]["rubric"]["on"]

        # Ablation should be identical across strategies in principle, but keep
        # direct as canonical for display.
        d_off = row["per_strategy"]["direct"]["off"]

        lines.append(
            "| "
            + " | ".join([
                f"**{row['label']}**",
                row["stage"],
                d_on.catch_str(),
                d_on.correction_str(),
                d_on.propagation_str(),
                c_on.catch_str(),
                c_on.correction_str(),
                c_on.propagation_str(),
                r_on.catch_str(),
                r_on.correction_str(),
                r_on.propagation_str(),
                d_off.propagation_str(),
                f"**{defense_delta_str(d_off, d_on)}**",
                f"**{defense_delta_str(d_off, c_on)}**",
                f"**{defense_delta_str(d_off, r_on)}**",
            ])
            + " |"
        )

    return lines


def format_severity_stage_table(rows: list[dict]) -> list[str]:
    lines = []
    lines.append("## 2. Severity-Stratified Causal Defense Map (Number Swaps)")
    lines.append("| Severity Level | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for row in rows:
        d_on = row["per_strategy"]["direct"]["on"]
        c_on = row["per_strategy"]["cot"]["on"]
        r_on = row["per_strategy"]["rubric"]["on"]
        d_off = row["per_strategy"]["direct"]["off"]

        lines.append(
            "| "
            + " | ".join([
                f"**{row['label'].capitalize()}**",
                row["stage"],
                d_on.catch_str(),
                d_on.correction_str(),
                d_on.propagation_str(),
                c_on.catch_str(),
                c_on.correction_str(),
                c_on.propagation_str(),
                r_on.catch_str(),
                r_on.correction_str(),
                r_on.propagation_str(),
                d_off.propagation_str(),
                f"**{defense_delta_str(d_off, d_on)}**",
                f"**{defense_delta_str(d_off, c_on)}**",
                f"**{defense_delta_str(d_off, r_on)}**",
            ])
            + " |"
        )

    return lines


def format_best_verifier_map(rows: list[dict], title: str) -> list[str]:
    lines = []
    lines.append(title)
    lines.append("| Subgroup | Stage | Best Catch Strategy | Best Correction Strategy | Lowest Propagation Strategy |")
    lines.append("| :--- | :--- | :---: | :---: | :---: |")

    for row in rows:
        lines.append(
            "| "
            + " | ".join([
                f"**{row['label'].capitalize() if row['kind'] == 'severity' else row['label']}**",
                row["stage"],
                best_strategy_for_metric(row, "catch_rate"),
                best_strategy_for_metric(row, "correction_rate"),
                best_strategy_for_metric(row, "propagation_rate"),
            ])
            + " |"
        )

    return lines


def format_global_summary(type_rows: list[dict], severity_rows: list[dict]) -> list[str]:
    lines = []
    lines.append("## 5. Global Strategy Win Summary")
    lines.append("These counts summarize how often each verifier strategy wins across subgroups.")
    lines.append("")

    type_wins = build_winner_summary(type_rows)
    sev_wins = build_winner_summary(severity_rows)

    lines.append("### Error-Type Map Wins")
    lines.append(f"- Direct best catch wins: **{type_wins['catch::direct']}**")
    lines.append(f"- CoT best catch wins: **{type_wins['catch::cot']}**")
    lines.append(f"- Rubric best catch wins: **{type_wins['catch::rubric']}**")
    lines.append(f"- Direct best correction wins: **{type_wins['correction::direct']}**")
    lines.append(f"- CoT best correction wins: **{type_wins['correction::cot']}**")
    lines.append(f"- Rubric best correction wins: **{type_wins['correction::rubric']}**")
    lines.append(f"- Direct lowest propagation wins: **{type_wins['lowest_propagation::direct']}**")
    lines.append(f"- CoT lowest propagation wins: **{type_wins['lowest_propagation::cot']}**")
    lines.append(f"- Rubric lowest propagation wins: **{type_wins['lowest_propagation::rubric']}**")
    lines.append("")

    lines.append("### Severity Map Wins")
    lines.append(f"- Direct best catch wins: **{sev_wins['catch::direct']}**")
    lines.append(f"- CoT best catch wins: **{sev_wins['catch::cot']}**")
    lines.append(f"- Rubric best catch wins: **{sev_wins['catch::rubric']}**")
    lines.append(f"- Direct best correction wins: **{sev_wins['correction::direct']}**")
    lines.append(f"- CoT best correction wins: **{sev_wins['correction::cot']}**")
    lines.append(f"- Rubric best correction wins: **{sev_wins['correction::rubric']}**")
    lines.append(f"- Direct lowest propagation wins: **{sev_wins['lowest_propagation::direct']}**")
    lines.append(f"- CoT lowest propagation wins: **{sev_wins['lowest_propagation::cot']}**")
    lines.append(f"- Rubric lowest propagation wins: **{sev_wins['lowest_propagation::rubric']}**")

    return lines


# ---------------------------------------------------------------------------
# Per-model report builder
# ---------------------------------------------------------------------------

def build_model_report(model_name: str, base_dir_map: dict[str, pathlib.Path]) -> str:
    strategy_data = load_strategy_bundle(base_dir_map)

    type_rows = compute_error_type_stage_map(strategy_data)
    severity_rows = compute_severity_stage_map(strategy_data)

    lines = []
    lines.append(f"# RQ3 Master Causal Error Map ({model_name})")
    lines.append("")
    lines.append("Synthesizing the interaction between injection stage, verifier ablation, error type, severity, and verifier strategy.")
    lines.append("")

    lines.extend(format_error_type_stage_table(type_rows))
    lines.append("")
    lines.extend(format_severity_stage_table(severity_rows))
    lines.append("")
    lines.extend(format_best_verifier_map(type_rows, "## 3. Best Verifier by Error Type and Stage"))
    lines.append("")
    lines.extend(format_best_verifier_map(severity_rows, "## 4. Best Verifier by Severity and Stage"))
    lines.append("")
    lines.extend(format_global_summary(type_rows, severity_rows))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    claude_dirs = {
        "direct": pathlib.Path("results/traces"),
        "cot": pathlib.Path("results/traces_cot"),
        "rubric": pathlib.Path("results/traces_rubric"),
    }

    qwen_dirs = {
        "direct": pathlib.Path("results/traces_replication_qwen25"),
        "cot": pathlib.Path("results/traces_replication_qwen25_cot"),
        "rubric": pathlib.Path("results/traces_replication_qwen25_rubric"),
    }

    claude_report = build_model_report("Claude Sonnet 4.6", claude_dirs)
    qwen_report = build_model_report("Qwen 2.5 72B Instruct", qwen_dirs)

    full_md = "\n\n---\n\n".join([
        "# RQ3 Master Error Map Report",
        claude_report,
        qwen_report,
    ])

    print("\n" + "=" * 100)
    print(full_md)
    print("=" * 100 + "\n")

    md_path = pathlib.Path("results/rq3_map_report.md")
    txt_path = pathlib.Path("results/rq3_map_report.txt")

    md_path.write_text(full_md, encoding="utf-8")
    txt_path.write_text(full_md, encoding="utf-8")

    print(f"Saved:\n- {md_path.absolute()}\n- {txt_path.absolute()}")


if __name__ == "__main__":
    main()