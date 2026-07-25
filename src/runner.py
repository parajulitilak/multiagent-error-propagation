"""Run all experimental conditions and log full traces to JSONL.

Usage:
    python -m src.runner --config configs/experiment.yaml [--conditions A B C1]
    python -m src.runner --config configs/experiment.yaml --dry-run   # no API calls
    python -m src.runner --config configs/experiment.yaml --robustness

Each line in results/traces/<condition>.jsonl is one problem's full trace.
Analysis (src/stats.py) reads these files; API runs never need repeating.
Dry runs write to a separate results/traces_dryrun/ so they can never clobber
real traces; real runs refuse to overwrite existing traces without --overwrite.
The robustness mode reruns the conditions at robustness_temperature once per
seed in robustness_seeds, writing to results/traces_robustness/seed_<s>/.
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import pathlib
import random
import re

import yaml
from dotenv import load_dotenv
from tqdm import tqdm

from src.pipeline import Trace, run_pipeline, run_single_agent, extract_final_answer
from src.injection import make_injector


def load_gsm8k(n: int, seed: int, split: str = "test"):
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split=split)
    idx = random.Random(seed).sample(range(len(ds)), n)
    items = []
    for i in idx:
        q = ds[i]["question"]
        gold = ds[i]["answer"].split("####")[-1].strip().replace(",", "")
        items.append({"id": f"gsm8k-{split}-{i}", "question": q, "gold": gold})
    return items


def normalize(ans: str) -> str:
    ans = (ans or "").strip().replace(",", "").replace("$", "")
    # An answer written as an expression ("91 + 182 = 273") states its value
    # as the result of the final computation: the number after the last '='.
    # Models, and the verifier in particular, answer this way; take the
    # result, otherwise fall back to the first number in the text.
    if "=" in ans:
        ans = ans.split("=")[-1]
    m = re.search(r"-?\d+(?:\.\d+)?", ans)
    if not m:
        return ans.lower()
    num = m.group(0)
    if "." in num:  # only decimals have removable trailing zeros
        num = num.rstrip("0").rstrip(".")
    return num


def is_correct(pred: str, gold: str) -> bool:
    return normalize(pred) == normalize(gold)


def run_condition(name: str, spec: dict, items: list, cfg: dict, out_dir: pathlib.Path,
                  dry_run: bool = False, overwrite: bool = False):
    injector = None
    if spec.get("inject_stage"):
        injector = make_injector(cfg["injection"]["types"], cfg["injection"]["seed"],
                                 cfg["injection"].get("severity"))
    rng = random.Random(cfg["injection"]["seed"])

    out_path = out_dir / f"{name}.jsonl"
    if out_path.exists() and out_path.stat().st_size > 0 and not overwrite:
        raise SystemExit(
            f"{out_path} already contains traces; pass --overwrite to replace them"
        )
    n_correct = 0
    with open(out_path, "w") as f:
        for item in tqdm(items, desc=f"condition {name}"):
            if dry_run:
                t = Trace(problem_id=item["id"], condition=name,
                          question=item["question"], gold=item["gold"],
                          final_answer="0")
            elif not spec.get("pipeline"):
                raw, usage = run_single_agent(item["question"], cfg)
                t = Trace(problem_id=item["id"], condition=name,
                          question=item["question"], gold=item["gold"],
                          solution=raw, final_answer=extract_final_answer(raw))
                t.usage["single"] = usage
            else:
                t = run_pipeline(
                    item["question"], cfg,
                    inject_stage=spec.get("inject_stage"),
                    injector=injector, rng=rng,
                    use_verifier=spec.get("verifier", True),
                )
                t.problem_id, t.condition = item["id"], name
                t.gold = item["gold"]
            t.extra["correct"] = is_correct(t.final_answer, t.gold)
            n_correct += t.extra["correct"]
            f.write(json.dumps(dataclasses.asdict(t)) + "\n")

    acc = n_correct / len(items) if items else 0.0
    print(f"[{name}] accuracy = {acc:.3f}  ({n_correct}/{len(items)})  -> {out_path}")
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--conditions", nargs="*", default=None,
                    help="subset, e.g. --conditions A B C1 (default: all)")
    ap.add_argument("--dry-run", action="store_true",
                    help="exercise the harness without API calls")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow replacing existing non-empty trace files")
    ap.add_argument("--robustness", action="store_true",
                    help="replicate at robustness_temperature, once per seed "
                         "in robustness_seeds")
    args = ap.parse_args()

    load_dotenv()
    cfg = yaml.safe_load(open(args.config))

    ds = cfg["dataset"]
    if ds.get("name", "gsm8k") != "gsm8k":
        raise SystemExit(
            f"dataset '{ds['name']}' is not implemented yet (only gsm8k)"
        )
    items = load_gsm8k(ds["n_problems"], ds["sample_seed"], ds["split"])
    print(f"Loaded {len(items)} problems (seed={ds['sample_seed']}); "
          f"same fixed sample for every condition (paired design).")

    base_dir = pathlib.Path(cfg["output_dir"])
    if args.dry_run:
        base_dir = base_dir.with_name(base_dir.name + "_dryrun")

    if args.robustness:
        robust_base = base_dir.with_name(base_dir.name + "_robustness")
        runs = []
        for seed in cfg["robustness_seeds"]:
            rcfg = copy.deepcopy(cfg)
            rcfg["temperature"] = cfg["robustness_temperature"]
            rcfg["injection"]["seed"] = seed
            runs.append((rcfg, robust_base / f"seed_{seed}"))
    else:
        runs = [(cfg, base_dir)]

    conditions = cfg["conditions"]
    selected = args.conditions or list(conditions)
    for run_cfg, out_dir in runs:
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.robustness:
            print(f"\n== robustness run: injection seed "
                  f"{run_cfg['injection']['seed']}, "
                  f"temperature {run_cfg['temperature']} -> {out_dir}")
        summary = {}
        for name in selected:
            summary[name] = run_condition(
                name, conditions[name], items, run_cfg, out_dir,
                dry_run=args.dry_run,
                overwrite=args.overwrite or args.dry_run,
            )
        print("\n=== SUMMARY ===")
        for k, v in summary.items():
            print(f"  {k}: {v:.3f}")


if __name__ == "__main__":
    main()
