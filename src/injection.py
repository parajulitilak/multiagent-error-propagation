"""Controlled fault injection.

We corrupt ONE intermediate output with a known, scripted perturbation, then
let the rest of the pipeline run untouched. Because the fault is planted by
us, ground truth about where the failure started is known; this is what
turns 'agents sometimes fail' into a causal measurement.

Each injector returns (corrupted_text, meta) where meta records exactly what
changed, so every downstream error can be attributed.

Number swaps are graded into three pre-registered severity levels by the
relative size of the change they introduce:
  mild      under a 15% change
  moderate  a 30-60% change
  severe    more than a 200% change, or a sign flip
A candidate replacement is accepted only if its realized relative change
falls inside the target band. If no number in the text can express the
target band (small integers cannot change by under 15%), the injector
escalates to the next level; the meta records both the target and the
realized level so any escalation is visible in the traces.
"""
from __future__ import annotations

import random
import re

# Word-level arithmetic flips: applied to plans/solutions in math tasks.
_OP_FLIPS = {
    "add": "subtract", "subtract": "add",
    "plus": "minus", "minus": "plus",
    "multiply": "divide", "divide": "multiply",
    "more": "fewer", "fewer": "more",
    "increase": "decrease", "decrease": "increase",
    "sum": "difference", "difference": "sum",
    "total": "difference",
}

# Quantities: plain integers/decimals plus comma-grouped forms like 1,234.
# The trailing guard rejects word characters and decimal continuations but
# allows a sentence-final period ('the total is 6.').
_NUM_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?!\w)(?!\.\d)")

# Severity bands on the realized relative change |new - old| / |old|.
# A sign flip is severe regardless of magnitude.
SEVERITY_BANDS = {
    "mild": (0.0, 0.15),             # 0 < rel < 0.15
    "moderate": (0.30, 0.60),        # 0.30 <= rel <= 0.60
    "severe": (2.00, float("inf")),  # rel > 2.00, or sign flip
}
SEVERITY_ORDER = ["mild", "moderate", "severe"]

# Multiplier sets per level; 'negate' flips the sign. Overridable from the
# experiment config so the released YAML pins the exact perturbations.
DEFAULT_MULTIPLIERS = {
    "mild": [0.9, 1.1],
    "moderate": [0.4, 0.6, 1.4, 1.6],
    "severe": [3.5, 4.0, "negate"],
}


def _is_label(text: str, m: re.Match) -> bool:
    """True for list/step labels: 'Step 1:', 'Part 3)', or a line-start '2.'.

    Only labels are excluded; a real quantity that happens to end a sentence
    ('the total is 6.') stays eligible.
    """
    before = text[: m.start()]
    if re.search(r"(?:step|part|stage|question|q)\s*$", before, flags=re.IGNORECASE):
        return True
    nxt = text[m.end(): m.end() + 1]
    line_prefix = before.rsplit("\n", 1)[-1]
    return bool(re.fullmatch(r"\s*", line_prefix)) and bool(re.match(r"[.):]", nxt or ""))


def _grade(old: float, new: float):
    """Realized (level, relative_change, sign_flip) for a candidate swap.

    Level is None when the change lands between bands (rejected during the
    candidate search; reported as 'off_band' only by the last-resort path).
    """
    sign_flip = (old > 0 > new) or (old < 0 < new)
    # Relative change is undefined at old==0 (division by zero); any move off
    # zero is an unbounded relative change, so it grades as severe rather than
    # being dropped or crashing. rel is left None since no ratio is meaningful.
    if old == 0:
        return ("severe" if new != 0 else None), None, sign_flip
    rel = abs(new - old) / abs(old)
    if sign_flip or rel > SEVERITY_BANDS["severe"][0]:
        return "severe", round(rel, 4), sign_flip
    if SEVERITY_BANDS["moderate"][0] <= rel <= SEVERITY_BANDS["moderate"][1]:
        return "moderate", round(rel, 4), sign_flip
    if 0 < rel < SEVERITY_BANDS["mild"][1]:
        return "mild", round(rel, 4), sign_flip
    return None, round(rel, 4), sign_flip


def _candidate(old: float, raw: str, factor):
    """Candidate value for one multiplier, rounded to the original's
    precision; None when the perturbation cannot change the value."""
    if factor == "negate":
        return -old if old != 0 else None
    val = old * float(factor)
    if "." in raw:
        val = round(val, len(raw.split(".")[1]))
    else:
        val = float(round(val))
    return val if val != old else None


def _finish(text: str, m: re.Match, raw: str, new: float,
            target: str, realized: str, rel, sign_flip: bool):
    new_str = str(int(new)) if float(new).is_integer() else str(new)
    if "," in raw and float(new).is_integer():
        new_str = f"{int(new):,}"
    corrupted = text[: m.start(1)] + new_str + text[m.end(1):]
    meta = {
        "type": "number_swap", "applied": True,
        "old": raw.replace(",", ""), "new": new_str.replace(",", ""),
        "pos": m.start(1),
        "severity_target": target, "severity": realized,
        "relative_change": rel, "sign_flip": sign_flip,
    }
    return corrupted, meta


def number_swap(text: str, rng: random.Random, severity: str = "moderate",
                multipliers: dict | None = None):
    """Replace one quantity with a plausible wrong value inside the target
    severity band.

    Comma-grouped quantities ('$1,234') are treated as one number and the
    grouping is preserved in the corrupted text. List/step labels are
    excluded: corrupting them changes no quantity, which would dilute the
    injection with harmless perturbations and bias propagation rates
    downward. The value is guaranteed to change whenever any quantity is
    eligible.
    """
    mults = multipliers or DEFAULT_MULTIPLIERS
    nums = [m for m in _NUM_RE.finditer(text) if not _is_label(text, m)]
    if not nums:
        return text, {"type": "number_swap", "applied": False}

    for level in SEVERITY_ORDER[SEVERITY_ORDER.index(severity):]:
        picks = nums[:]
        rng.shuffle(picks)
        for m in picks:
            raw = m.group(1)
            old = float(raw.replace(",", ""))
            factors = list(mults[level])
            rng.shuffle(factors)
            for f in factors:
                new = _candidate(old, raw, f)
                if new is None:
                    continue
                realized, rel, flip = _grade(old, new)
                if realized != level:
                    continue
                return _finish(text, m, raw, new, severity, realized, rel, flip)

    # Last resort (only zeros eligible, or no band fits any number): still
    # guarantee a changed value and report the realized grade honestly.
    m = rng.choice(nums)
    raw = m.group(1)
    old = float(raw.replace(",", ""))
    new = old + rng.choice([1, 2, 3])
    realized, rel, flip = _grade(old, new)
    return _finish(text, m, raw, new, severity, realized or "off_band", rel, flip)


def operation_flip(text: str, rng: random.Random):
    """Flip one arithmetic operation word to its opposite."""
    candidates = []
    for word, repl in _OP_FLIPS.items():
        for m in re.finditer(rf"\b{word}\b", text, flags=re.IGNORECASE):
            candidates.append((m, repl))
    if not candidates:
        return text, {"type": "operation_flip", "applied": False}
    m, repl = rng.choice(candidates)
    corrupted = text[: m.start()] + repl + text[m.end():]
    meta = {
        "type": "operation_flip", "applied": True,
        "old": m.group(0), "new": repl, "pos": m.start(),
    }
    return corrupted, meta


INJECTORS = {"number_swap": number_swap, "operation_flip": operation_flip}


def make_injector(types: list[str], seed: int,
                  severity_multipliers: dict | None = None):
    """Return injector fn cycling over requested types; falls back if one
    perturbation type finds nothing to corrupt in a given text.

    Number-swap severity targets cycle mild -> moderate -> severe in
    application order, so the three levels stay balanced across the fixed,
    ordered problem sample; the counter advances only when a swap is
    actually applied.

    Balance is guaranteed on the TARGET (severity_target in the meta), not on
    the realized level: when a text cannot express the target band (e.g. a
    small integer that cannot change by <15% for a mild target), number_swap
    escalates and records the realized level in 'severity'. The meta keeps
    both, so downstream analysis can stratify on either. Realized levels may
    therefore be mildly imbalanced; the stats use Wilson intervals and a
    logistic model, neither of which requires equal cell sizes.
    """
    base_rng = random.Random(seed)
    applied_swaps = 0

    def injector(text: str, rng: random.Random | None = None):
        nonlocal applied_swaps
        r = rng or base_rng
        order = types[:]
        r.shuffle(order)
        for t in order:
            if t == "number_swap":
                target = SEVERITY_ORDER[applied_swaps % len(SEVERITY_ORDER)]
                corrupted, meta = number_swap(text, r, target, severity_multipliers)
                if meta.get("applied"):
                    applied_swaps += 1
                    return corrupted, meta
            else:
                corrupted, meta = INJECTORS[t](text, r)
                if meta.get("applied"):
                    return corrupted, meta
        return text, {"type": "none_applicable", "applied": False}

    return injector
